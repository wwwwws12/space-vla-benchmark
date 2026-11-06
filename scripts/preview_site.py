"""Serve only the local static project page; optionally open its browser tab."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    directory = Path(__file__).resolve().parents[1] / 'site' / 'dist'
    class Handler(SimpleHTTPRequestHandler):
        extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.mp4':'video/mp4', '.webm':'video/webm', '.js':'text/javascript', '.css':'text/css'}
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()
    url = f'http://127.0.0.1:{args.port}/index.zh-CN.html'
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(directory)))
    except OSError:
        raise SystemExit(f'Cannot bind port {args.port}; use a different --port. No existing process was stopped.')
    print(f'LOCAL PREVIEW: {url}', flush=True)
    print('Keep this window open. Ctrl+C stops the preview. No upload or model calls.', flush=True)
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
