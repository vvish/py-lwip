"""Implementation of the lwip based Udp socket."""

import ctypes

from lwip_py.stack import PBuf, exceptions
from lwip_py.stack.ip_address import IpV4Addr
from lwip_py.utility import ctypes_helper

_IP_PCB_FIELDS = (
    ('local_ip', IpV4Addr),
    ('remote_ip', IpV4Addr),
    ('netif_idx', ctypes.c_uint8),
    ('so_options', ctypes.c_uint8),
    ('tos', ctypes.c_uint8),
    ('ttl', ctypes.c_uint8),
)


class _UdpPcb(ctypes.Structure):
    pass


udp_recv_fn_func_type = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.POINTER(_UdpPcb),
    ctypes.POINTER(PBuf),
    ctypes.POINTER(IpV4Addr),
    ctypes.c_uint16,
)


_UdpPcb._fields_ = [
    *_IP_PCB_FIELDS,
    ('next', ctypes.POINTER(_UdpPcb)),
    ('flags', ctypes.c_uint8),
    ('local_port', ctypes.c_uint16),
    ('remote_port', ctypes.c_uint16),
    ('recv', udp_recv_fn_func_type),
    ('recv_arg', ctypes.c_void_p),
]

err_t = ctypes.c_int8


class UdpSocket(object):
    """
    Class that implements Udp socket (not fully posix like).

    The class wraps lwip low level socket representation udp_pcb.
    It allows to bind to the address/port, send data to the arbitrary
    address/port and receive data. The received data is not stored in
    the socket buffer, but forwarded via client specified callback.
    The callback is invoked from the stack context.
    """

    def __init__(self, lwip, allocator):
        """
        Initialize new UdpSocket object.

        Parameters
        ----------
        lwip : lib instance
            the instance of the lwip library, loaded via ctypes
        allocator : Allocator
            stack memory allocator
        """
        self._lwip = lwip
        self._allocator = allocator
        self._pcb = None
        self._rx_callback = None

        self._udp_new_ip_type = ctypes_helper.wrap_function(
            self._lwip,
            'udp_new_ip_type',
            ctypes.POINTER(_UdpPcb),
            [ctypes.c_uint8],
        )
        self._udp_bind = ctypes_helper.wrap_function(
            self._lwip,
            'udp_bind',
            err_t,
            [
                ctypes.POINTER(_UdpPcb),
                ctypes.POINTER(IpV4Addr),
                ctypes.c_uint16,
            ],
        )
        self._udp_recv = ctypes_helper.wrap_function(
            self._lwip,
            'udp_recv',
            None,
            [ctypes.POINTER(_UdpPcb), udp_recv_fn_func_type, ctypes.c_void_p],
        )
        self._udp_send_to = ctypes_helper.wrap_function(
            self._lwip,
            'udp_sendto',
            err_t,
            [
                ctypes.POINTER(_UdpPcb),
                ctypes.POINTER(PBuf),
                ctypes.POINTER(IpV4Addr),
                ctypes.c_uint16,
            ],
        )

    def bind(self, end_point):
        """
        Bind socket to the ip_address/port pair.

        Parameters
        ----------
        end_point : tuple(ip address string, port)
            ip address and port to bind to

        Raises
        ------
        AllocationError
            if the low-level socket allocation can not be done
        StackException
            if the low-level stack error occures
        """
        ip_type_v4 = 0
        self._pcb = self._udp_new_ip_type(ip_type_v4).contents

        if not self._pcb:
            raise exceptions.AllocationError()

        ip_address_str, port = end_point
        ip_address = IpV4Addr(ip_address_str) if ip_address_str else None

        bind_result = self._udp_bind(self._pcb, ip_address, port)
        if bind_result:
            raise exceptions.StackException(bind_result)

        self._internal_callback = udp_recv_fn_func_type(self._recv_callback)
        self._udp_recv(
            self._pcb, self._internal_callback, None,
        )

    def send_to(self, data_to_send, ip_address, port):
        """
        Send data to remote host.

        Parameters
        ----------
        data_to_send : bytearray
            data that should be sent
        ip_address : IpV4Address
            address of the remote host
        port : int
            remote port

        Raises
        ------
        StackException
            indicates that the internal lwip error occured
        AllocationError
            is raised if pbuf to place outgoing data can not be allocated
        """
        pbuf_to_send = self._allocator.allocate_transport_pbuf_from_data(
            data_to_send,
        )

        if pbuf_to_send:
            send_result = self._udp_send_to(
                self._pcb, pbuf_to_send, ip_address, port,
            )
            if send_result:
                raise exceptions.StackException(send_result)
        else:
            raise exceptions.AllocationError()

    def set_recv_callback(self, callback):
        """
        Set callback to be invoked on incoming data.

        Callack function should accept as a single parameter a 
        tuple(bytearray, IpV4Address, int) holding data, source address,
        sorce port respectively.

        Parameters
        ----------
        callback : function
            the callback function
        """
        self._rx_callback = callback

    def _recv_callback(self, arg, pcb, pbuf, addr, port):
        payload = ctypes.cast(
            pbuf.contents.payload, ctypes.POINTER(
                ctypes.c_uint8 * pbuf.contents.len,
            ),
        )

        addr_copy = IpV4Addr()
        addr_copy.addr = addr.contents.addr
        new_chunk = (bytearray(payload.contents), addr_copy, port)

        self._allocator.free_pbuf(pbuf)

        if self._rx_callback:
            self._rx_callback(self, *new_chunk)
