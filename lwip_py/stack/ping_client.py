"""Ping client implementation."""
import ctypes

from lwip_py.stack.ip_address import IpAddr
from lwip_py.utility import ctypes_helper


class PingClient(object):
    """Wrapper around ping application from lwip contribs."""

    def __init__(self, lwip):
        """
        Initialize new object.

        Parameters
        ----------
        lwip : ctypes wrapper for lib
            lwip library instance
        """
        self._lwip = lwip

        self._ping_init = ctypes_helper.wrap_function(
            self._lwip, 'ping_init', None, [ctypes.POINTER(IpAddr)],
        )

        self._ping_send_now = ctypes_helper.wrap_function(
            self._lwip, 'ping_send_now', None, None,
        )

        self._ping_callback_fn = ctypes.CFUNCTYPE(
            None, ctypes.c_uint8,
        )

        self._set_ping_callback = ctypes_helper.wrap_function(
            self._lwip, 'set_ping_callback', None, [self._ping_callback_fn],
        )

    def ping(self, target_ip, callback):
        """
        Ping (send ICMP echo and expect response) remote host.

        Parameters
        ----------
        target_ip : IpAddress
            ip address to ping
        callback : function
            callback to forward ping result
        """
        self._ping_callback = callback
        self._ping_ctypes_callback = self._ping_callback_fn(
            self._ping_callback_internal,
        )

        self._set_ping_callback(self._ping_ctypes_callback)
        self._ping_init(ctypes.byref(target_ip))
        self._ping_send_now()

    def _ping_callback_internal(self, ping_result):
        self._set_ping_callback(self._ping_callback_fn())
        if self._ping_callback:
            tmp_callback = self._ping_callback
            self._ping_callback = None
            tmp_callback(ping_result != 0)
