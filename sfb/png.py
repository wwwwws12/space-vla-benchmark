"""Minimal RGB8 PNG writer using only Python's standard library."""

import struct
import zlib


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_rgb8(path, pixels) -> None:
    """Write an HxWx3 uint8-like array as PNG, preserving RGB channel order."""
    if getattr(pixels, "ndim", None) != 3 or pixels.shape[2] != 3:
        raise ValueError("expected an HxWx3 RGB array")
    height, width, _ = pixels.shape
    rows = pixels.tobytes()
    stride = width * 3
    scanlines = b"".join(b"\x00" + rows[y * stride:(y + 1) * stride] for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header) + _chunk(b"IDAT", zlib.compress(scanlines, 6)) + _chunk(b"IEND", b"")
    with open(path, "wb") as stream:
        stream.write(payload)
