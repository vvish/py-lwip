import ctypes


class PBuf(ctypes.Structure):
    """lwip pbuf wrapper."""


PBuf._fields_ = [
    ('next', ctypes.POINTER(PBuf)),
    ('payload', ctypes.c_void_p),
    ('tot_len', ctypes.c_uint16),
    ('len', ctypes.c_uint16),
    ('type_internal', ctypes.c_uint8),
    ('flags', ctypes.c_uint8),
    ('ref', ctypes.c_uint8),
    ('if_idx', ctypes.c_uint8),
]
