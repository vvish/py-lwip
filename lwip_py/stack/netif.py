"""lwip netif python wrapper"""
import ctypes

from lwip_py.stack.ip_address import IpAddr, IpV4Addr
from lwip_py.stack.pbuf import PBuf
from lwip_py.utility import address_helpers, ctypes_helper


class NetIf(object):
    """
    The class wraps lwip netif struct.

    The class represents single network interface.
    """

    flag_up = 0x1
    flag_broadcast = 0x2
    flag_link_up = 0x4
    flag_etharp = 0x8
    flag_ethernet = 0x10
    flag_igmp = 0x20

    class _LwipNetIf(ctypes.Structure):
        pass

    netif_init_fn_type = ctypes.CFUNCTYPE(
        ctypes.c_int8, ctypes.POINTER(_LwipNetIf),
    )
    netif_input_fn_type = ctypes.CFUNCTYPE(
        ctypes.c_int8, ctypes.POINTER(PBuf), ctypes.POINTER(_LwipNetIf),
    )

    netif_linkoutput_fn = ctypes.CFUNCTYPE(
        ctypes.c_int8, ctypes.POINTER(_LwipNetIf), ctypes.POINTER(PBuf),
    )

    netif_output_fn = ctypes.CFUNCTYPE(
        ctypes.c_int8,
        ctypes.POINTER(_LwipNetIf),
        ctypes.POINTER(PBuf),
        ctypes.POINTER(IpV4Addr),
    )

    netif_status_cbk_fn = ctypes.CFUNCTYPE(
        None, ctypes.POINTER(_LwipNetIf),
    )

    hwaddr_arr = ctypes.c_uint8 * 6
    name_arr = ctypes.c_char * 2

    _LwipNetIf._fields_ = [
        ('next', ctypes.POINTER(_LwipNetIf)),
        ('ip_addr', IpV4Addr),
        ('netmask', IpV4Addr),
        ('gw', IpV4Addr),
        ('input', netif_input_fn_type),
        ('output', netif_output_fn),
        ('linkoutput', netif_linkoutput_fn),
        ('status_callback', netif_status_cbk_fn),
        ('link_callback', netif_status_cbk_fn),
        ('state', ctypes.c_void_p),
        ('mtu', ctypes.c_uint16),
        ('hwaddr', hwaddr_arr),
        ('hwaddr_len', ctypes.c_uint8),
        ('flags', ctypes.c_uint8),
        ('name', name_arr),
        ('num', ctypes.c_uint8),
    ]

    def __init__(self, name, lwip, stack):
        """
        Initialize new object.

        Parameters
        ----------
        name : string
            human readable interface name
        lwip : ctype lib
            instance of the lwip lib
        stack : Stack
            stack that will service the interface
        """
        self._name = name
        self._lwip = lwip
        self._stack = stack

        self._netif_add = ctypes_helper.wrap_function(
            self._lwip,
            'netif_add',
            ctypes.POINTER(self._LwipNetIf),
            [
                ctypes.POINTER(self._LwipNetIf),
                ctypes.POINTER(IpV4Addr),
                ctypes.POINTER(IpV4Addr),
                ctypes.POINTER(IpV4Addr),
                ctypes.c_void_p,
                self.netif_init_fn_type,
                self.netif_input_fn_type,
            ],
        )

        self._etharp_output = ctypes_helper.wrap_function(
            self._lwip,
            'etharp_output',
            ctypes.c_int8,
            [
                ctypes.POINTER(self._LwipNetIf),
                ctypes.POINTER(PBuf),
                ctypes.POINTER(IpV4Addr),
            ],
        )

        self._ip_input = ctypes_helper.wrap_function(
            self._lwip,
            'ethernet_input',
            ctypes.c_int8,
            [
                ctypes.POINTER(PBuf),
                ctypes.POINTER(self._LwipNetIf),
            ],
        )

        self._interface = self._LwipNetIf()

        self._netif_input = self.netif_input_fn_type()
        self._netif_output = self.netif_output_fn()

        self._netif_link_output = self.netif_linkoutput_fn(
            self._link_output_wrapper,
        )
        self._netif_user_link_output = None

        self._netif_status = self.netif_status_cbk_fn()
        self._netif_link_status = self.netif_status_cbk_fn()

        self._ping_callback = None

    def __str__(self):
        """
        Reflect object info as human-readable string.

        The output mimics ifconfig output to some extent.

        Returns
        -------
        string
            readable object info
        """
        flags = [
            (self.flag_up, 'UP'),
            (self.flag_broadcast, 'BROADCAST'),
            (self.flag_etharp, 'ETH_ARP'),
            (self.flag_ethernet, 'ETH'),
            (self.flag_link_up, 'LINK'),
            (self.flag_igmp, 'IGMP'),
        ]

        flags_str = ', '.join(
            [
                fl[1] for fl in flags if self._interface.flags & fl[0]
            ],
        )

        return '{0}: flags={1}<{2}> inet {3} netmask {4} gw {5}'.format(
            self._name,
            self._interface.flags,
            flags_str,
            address_helpers.int_ip_to_string(self._interface.ip_addr.addr),
            address_helpers.int_ip_to_string(self._interface.netmask.addr),
            address_helpers.int_ip_to_string(self._interface.gw.addr),
        )

    def get_stack(self):
        """
        Return the stack that services the interface.

        Returns
        -------
        Stack
            stack associated with the interface
        """
        return self._stack

    def set_output_callbacks(self, link_output, output=None):
        """
        Set the callback invoked for outgoing data.

        Parameters
        ----------
        link_output : callable
            callable to be invoked when link-layer data should be sent
        output : callable, optional
            callable to forward network-layer data, by default None
        """
        if output is not None:
            self._netif_output = self.netif_output_fn(output)
        else:
            self._netif_output = self.netif_output_fn(self._etharp_output)

        self._interface.output = self._netif_output

        self._netif_user_link_output = link_output
        self._interface.linkoutput = self._netif_link_output

    def set_status_callbacks(self, status_callback, link_callback):
        """
        Set interface status callbacks.

        Parameters
        ----------
        status_callback : callable
            callable to invoke on interface status change
        link_callback : callable
            callable to invoke when link status changes
        """
        self._netif_status = self.netif_status_cbk_fn(
            self._status_callback_internal,
        )
        self._status_callback = status_callback
        self._interface.status_callback = self._netif_status

        self._netif_link_status = self.netif_status_cbk_fn(
            self._link_status_callback_internal,
        )
        self._link_status = link_callback
        self._interface.link_callback = self._netif_link_status

    def set_name(self, name):
        """
        Set the low level interface name.

        The name is two symbols array used to identify the interface in
        lwip logs.

        Parameters
        ----------
        name : two symbol array
            symbols used to identify interface
        """
        self._interface.name = name

    def add(self, ip_address, netmask, gateway):
        self._py_object = ctypes.py_object(self)
        self._netif_input = self.netif_input_fn_type(self._ip_input)
        self._netif_add(
            self._interface,
            ip_address,
            netmask,
            gateway,
            ctypes.cast(ctypes.pointer(self._py_object), ctypes.c_void_p),
            self.netif_init_fn_type(self._report_netif_init),
            self._netif_input,
        )

        self._interface.hwaddr = (0xA, 0xB, 0xC, 0xD, 0xE, 0xF)
        self._interface.hwaddr_len = 6
        self._interface.flags = 8

    def set_up(self):
        netif_set_up = ctypes_helper.wrap_function(
            self._lwip,
            'netif_set_up',
            None,
            [ctypes.POINTER(self._LwipNetIf)],
        )
        netif_set_up(ctypes.byref(self._interface))

    def set_down(self):
        netif_set_down = ctypes_helper.wrap_function(
            self._lwip,
            'netif_set_down',
            None,
            [ctypes.POINTER(self._LwipNetIf)],
        )
        netif_set_down(ctypes.byref(self._interface))

    def set_link_up(self):
        netif_set_link_up = ctypes_helper.wrap_function(
            self._lwip,
            'netif_set_link_up',
            None,
            [ctypes.POINTER(self._LwipNetIf)],
        )
        netif_set_link_up(ctypes.byref(self._interface))

    def set_link_down(self):
        netif_set_link_down = ctypes_helper.wrap_function(
            self._lwip,
            'netif_set_link_down',
            None,
            [ctypes.POINTER(self._LwipNetIf)],
        )
        netif_set_link_down(ctypes.byref(self._interface))

    def set_default(self):
        netif_set_default = ctypes_helper.wrap_function(
            self._lwip,
            'netif_set_default',
            None,
            [ctypes.POINTER(self._LwipNetIf)],
        )
        netif_set_default(ctypes.byref(self._interface))

    def set_etharp_flag(self):
        etherarp_flag = 8
        self._interface.flags = self._interface.flags | etherarp_flag

    def input(self, incoming_pbuf):
        self._interface.input(incoming_pbuf, self._interface)

    def input_data(self, incoming_data):
        array = ctypes.c_uint8 * len(incoming_data)
        # p = self.get_stack().allocate_raw_pbuf_from_data(
        #     ctypes.cast(data, ctypes.c_void_p), ctypes.sizeof(data))

        allocator = self.get_stack().make_allocator()
        incoming_pbuf = allocator.allocate_raw_pbuf_from_data(
            array.from_buffer(incoming_data), len(incoming_data),
        )

        self._interface.input(incoming_pbuf, self._interface)

    def get_address(self):
        return address_helpers.int_ip_to_string(self._interface.ip_addr.addr)

    def _report_netif_init(self, netif):
        return 0

    def _link_output_wrapper(self, netif, outgoing_pbuf):
        if self._netif_user_link_output is not None:

            payload = ctypes.cast(
                outgoing_pbuf.contents.payload, ctypes.POINTER(
                    ctypes.c_uint8 * outgoing_pbuf.contents.len,
                ),
            )

            payload_to_send = bytearray(payload.contents)

            netif = ctypes.cast(
                netif.contents.state, ctypes.POINTER(
                    ctypes.py_object,
                ),
            ).contents.value

            # return self._netif_user_link_output(netif, payload_to_send)
            self._netif_user_link_output(netif, payload_to_send)
            return 0

    def _status_callback_internal(self, ni):
        if self._status_callback:
            self._status_callback(self)

    def _link_status_callback_internal(self, ni):
        if self._link_status:
            self._link_status(self)