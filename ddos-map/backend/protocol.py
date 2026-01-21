import struct
STRUCT_FMT = "!QIIHB"   # ts, src, dst, port, proto
STRUCT_SIZE = struct.calcsize(STRUCT_FMT)
