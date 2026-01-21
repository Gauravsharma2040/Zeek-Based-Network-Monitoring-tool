# parser.py
import struct
import socket
STRUCT_FMT = "!QIIHB"
STRUCT_SIZE = struct.calcsize(STRUCT_FMT)
def parse_event(data: bytes) -> dict:
    ts, src, dst, port, proto = struct.unpack(STRUCT_FMT, data)

    return {
        "ts": ts,
        "src": socket.inet_ntoa(struct.pack("!I", src)),
        "dst": socket.inet_ntoa(struct.pack("!I", dst)),
        "port": port,
        "proto": proto,
    }

def parse_batch(data: bytes):
    for i in range(0, len(data), STRUCT_SIZE):
        chunk = data[i:i + STRUCT_SIZE]
        if len(chunk) == STRUCT_SIZE:
            yield parse_event(chunk)
