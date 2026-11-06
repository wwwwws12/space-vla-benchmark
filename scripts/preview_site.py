"""Loopback-only website preview with opt-in access to prepared dataset archives."""
import argparse
import errno
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import unquote, urlsplit
import webbrowser


ZIP_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.zip\Z')
FLAT_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*\Z')
SHA_LINE = re.compile(r'([a-fA-F0-9]{64})[ \t]+\*?([A-Za-z0-9][A-Za-z0-9_.-]*)\Z')
GROUPS = {
    'mars-baseline', 'mars-second', 'moon-baseline', 'moon-second',
    'cabin-baseline', 'cabin-second',
}


def disconnected(exc):
    return (
        isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError))
        or getattr(exc, 'errno', None) in {errno.EPIPE, errno.ECONNRESET, errno.ECONNABORTED}
        or getattr(exc, 'winerror', None) in {10053, 10054}
    )


class DatasetFiles:
    """Read-only allowlist; no dataset route is mapped through generic path translation."""

    def __init__(self, directory):
        self.directory = directory.resolve()
        self.complete = self.directory.parent / 'COMPLETE.json'
        self.lock = threading.RLock()
        self.signature = None
        self.allowed = None

    def flat_file(self, filename):
        if not FLAT_NAME.fullmatch(filename):
            raise ValueError('Non-flat filename')
        path = self.directory / filename
        if path.is_symlink() or not path.is_file() or path.resolve().parent != self.directory:
            raise ValueError('Package file unavailable')
        return path

    @staticmethod
    def identity(path):
        stat = path.stat()
        return stat.st_size, stat.st_mtime_ns

    def snapshot(self):
        """Return filename -> expected bytes only when the entire six-group release is ready."""
        with self.lock:
            try:
                if self.complete.is_symlink() or not self.complete.is_file():
                    return None
                manifest_path = self.flat_file('dataset_manifest.json')
                checksum_path = self.flat_file('SHA256SUMS')
                signature = (
                    self.identity(self.complete), self.identity(manifest_path),
                    self.identity(checksum_path),
                )
                if signature != self.signature or self.allowed is None:
                    complete = json.loads(self.complete.read_text(encoding='utf-8'))
                    if (
                        complete.get('status') != 'LOCAL_DATASET_ARCHIVES_COMPLETE'
                        or complete.get('groups') != 6
                        or complete.get('unique_routes') != 900
                        or complete.get('route_conditions') != 1800
                        or complete.get('frames') != 65600
                    ):
                        return None
                    checksums = {}
                    for line in checksum_path.read_text(encoding='utf-8').splitlines():
                        if not line.strip():
                            continue
                        match = SHA_LINE.fullmatch(line)
                        if not match or match[2] in checksums:
                            return None
                        checksums[match[2]] = match[1].lower()
                    manifest_bytes = manifest_path.read_bytes()
                    if hashlib.sha256(manifest_bytes).hexdigest() != checksums.get('dataset_manifest.json'):
                        return None
                    manifest = json.loads(manifest_bytes)
                    groups = manifest.get('groups')
                    if not isinstance(groups, list) or len(groups) != 6:
                        return None
                    if {group.get('id') for group in groups} != GROUPS:
                        return None
                    allowed = {}
                    casefolded_names = set()
                    for group in groups:
                        archives = group.get('archives')
                        if not isinstance(archives, list) or not archives:
                            return None
                        for archive in archives:
                            filename = archive.get('filename')
                            size = archive.get('bytes')
                            digest = archive.get('sha256')
                            if (
                                not isinstance(filename, str) or not ZIP_NAME.fullmatch(filename)
                                or filename.casefold() in casefolded_names
                                or type(size) is not int or size <= 0
                                or not isinstance(digest, str)
                                or checksums.get(filename) != digest.lower()
                            ):
                                return None
                            casefolded_names.add(filename.casefold())
                            allowed[filename] = size
                    if complete.get('archives') != len(allowed) or complete.get('archive_bytes') != sum(allowed.values()):
                        return None
                    allowed['dataset_manifest.json'] = len(manifest_bytes)
                    allowed['SHA256SUMS'] = checksum_path.stat().st_size
                    self.allowed = allowed
                    self.signature = signature
                # Check every ZIP on every request, without rereading multi-GB payloads.
                # COMPLETE.json is written last; a removed/truncated archive disables download.
                for filename, size in self.allowed.items():
                    if self.flat_file(filename).stat().st_size != size:
                        return None
                return dict(self.allowed)
            except (OSError, ValueError, TypeError, AttributeError, KeyError):
                return None


def single_range(value, size):
    """Return inclusive start/end; reject malformed, multi-range and unsatisfiable requests."""
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', value.strip())
    if not match or not any(match.groups()) or size <= 0:
        raise ValueError('Invalid range')
    first, last = match.groups()
    if not first:
        suffix = int(last)
        if suffix <= 0:
            raise ValueError('Invalid suffix range')
        return max(0, size - suffix), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError('Unsatisfiable range')
    return start, end


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--dataset-directory', type=Path, help='Prepared packages directory; files are never copied into the website.')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    repository = Path(__file__).resolve().parents[1]
    directory = repository / 'site' / 'dist'
    dataset_directory = args.dataset_directory or (
        repository.parents[2] / 'dataset_downloads' / 'space_vla_20261106_01' / 'packages'
    )
    dataset = DatasetFiles(dataset_directory)

    class Handler(SimpleHTTPRequestHandler):
        extensions_map = {
            **SimpleHTTPRequestHandler.extensions_map,
            '.mp4': 'video/mp4', '.webm': 'video/webm',
            '.js': 'text/javascript', '.css': 'text/css',
        }

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

        def handle(self):
            try:
                super().handle()
            except OSError as exc:
                if not disconnected(exc):
                    raise

        def finish(self):
            try:
                super().finish()
            except OSError as exc:
                if not disconnected(exc):
                    raise

        def do_GET(self):
            if not self.dataset_request(head_only=False):
                super().do_GET()

        def do_HEAD(self):
            if not self.dataset_request(head_only=True):
                super().do_HEAD()

        def dataset_request(self, head_only):
            try:
                path = unquote(urlsplit(self.path).path, errors='strict')
            except (ValueError, UnicodeError):
                self.send_error(400, 'Invalid request path')
                return True
            if path != '/dataset-downloads' and not path.startswith('/dataset-downloads/'):
                return False
            allowed = dataset.snapshot()
            if path == '/dataset-downloads/status.json':
                body = json.dumps({'available': allowed is not None}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                if not head_only:
                    self.wfile.write(body)
                return True
            filename = path.removeprefix('/dataset-downloads/')
            if not FLAT_NAME.fullmatch(filename) or allowed is None or filename not in allowed:
                self.send_error(404, 'Dataset file unavailable')
                return True
            try:
                filepath = dataset.flat_file(filename)
                source = filepath.open('rb')
            except (OSError, ValueError):
                self.send_error(404, 'Dataset file unavailable')
                return True
            with source:
                size = os.fstat(source.fileno()).st_size
                if size != allowed[filename]:
                    self.send_error(409, 'Dataset file changed; reload the download list')
                    return True
                start, end, partial = 0, size - 1, False
                range_headers = self.headers.get_all('Range') or []
                if range_headers:
                    try:
                        if len(range_headers) != 1:
                            raise ValueError('Multiple Range headers')
                        start, end = single_range(range_headers[0], size)
                        partial = True
                    except ValueError:
                        self.send_response(416)
                        self.send_header('Content-Range', f'bytes */{size}')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Content-Length', '0')
                        self.end_headers()
                        return True
                length = max(0, end - start + 1)
                self.send_response(206 if partial else 200)
                self.send_header('Content-Type', 'application/zip' if filename.endswith('.zip') else (
                    'application/json; charset=utf-8' if filename.endswith('.json') else 'text/plain; charset=utf-8'
                ))
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Length', str(length))
                if partial:
                    self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                self.end_headers()
                if not head_only:
                    source.seek(start)
                    remaining = length
                    while remaining:
                        chunk = source.read(min(1024 * 1024, remaining))
                        if not chunk:
                            self.close_connection = True
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            return True

    url = f'http://127.0.0.1:{args.port}/index.zh-CN.html'
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(directory)))
    except OSError:
        raise SystemExit(f'Cannot bind port {args.port}; use a different --port. No existing process was stopped.')
    print(f'LOCAL PREVIEW: {url}', flush=True)
    print('DATASET DOWNLOADS: ' + ('ready' if dataset.snapshot() is not None else 'not ready; website preview remains available'), flush=True)
    print('Keep this window open. Ctrl+C stops the preview. No upload or model calls.', flush=True)
    if not args.no_browser:
        browser_timer = threading.Timer(0.4, lambda: webbrowser.open(url))
        browser_timer.daemon = True
        browser_timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
