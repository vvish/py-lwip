import ctypes

from lwip_py.utility import address_helpers


class IpV4Addr(ctypes.Structure):
    _fields_ = [('addr', ctypes.c_uint32)]

    def __init__(self, ip_str='0.0.0.0'):
        self.addr = address_helpers.int_ip_from_string(ip_str)


class IpV6Addr(ctypes.Structure):
    _fields_ = [('addr', ctypes.c_uint32 * 4), ('zone', ctypes.c_uint8)]


class _AddressUnion(ctypes.Union):
    _fields_ = [('ip6', IpV6Addr), ('ip4', IpV4Addr)]


class IpAddr(ctypes.Structure):
    def __init__(self, addr):
        address_type_ipv4 = 0
        address_type_ipv6 = 6

        if isinstance(addr, IpV4Addr):
            self.u_addr.ip4 = addr
            self.type = address_type_ipv4
        elif isinstance(addr, IpV4Addr):
            self.u_addr.ip6 = addr
            self.type = address_type_ipv6
        else:
            raise ValueError()

    _fields_ = [('u_addr', _AddressUnion), ('type', ctypes.c_uint8)]
