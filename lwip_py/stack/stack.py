"""lwip stack python wrapper."""
from lwip_py.stack import udp_socket
from lwip_py.stack.memory_allocator import Allocator
from lwip_py.stack.netif import NetIf
from lwip_py.stack.ping_client import PingClient
from lwip_py.utility import ctypes_helper


class SocketTypes(object):
    """Types of socket to create."""

    sock_stream = 1
    sock_dgram = 2
    sock_raw = 3


class Stack(object):
    """Wrapper around lwip stack instance."""

    def __init__(self, library_loader):
        """
        Initialize new object.

        Parameters
        ----------
        library_loader : callable
            callable returning new instance of the lwip lib
        """
        self._library_loader = library_loader
        self._interfaces = {}

    def init(self):
        """
        Initialize stack.

        The new instance of the stack library will be loaded.
        """
        self._lwip = self._library_loader()

        self._sys_check_timeouts = ctypes_helper.wrap_function(
            self._lwip, 'sys_check_timeouts', None, None,
        )

        self._lwip.lwip_init()

    def make_interface(self, name):
        """
        Make new network interface serviced by the stack.

        Parameters
        ----------
        name : string
            human readable name of the inteface

        Returns
        -------
        NetIf
            new interface
        """
        netif = NetIf(name, self._lwip, self)
        self._interfaces[name] = netif
        return netif

    def make_allocator(self):
        """
        Make new memory allocator associated with the stack.

        Allocation will be happening from the pools and memory areas
        reserved in the stack lib.

        Returns
        -------
        MemoryAllocator
            new allocator
        """
        return Allocator(self._lwip)

    def make_socket(self, socket_type):
        """
        Make socket instance.

        Parameters
        ----------
        socket_type : int
            type of the socket to be created

        Returns
        -------
        Socket
            socket object

        Raises
        ------
        ValueError
            only SOCK_DGRAM is currently supported
        """
        if socket_type == SocketTypes.sock_dgram:
            return udp_socket.UdpSocket(self._lwip, self.make_allocator())

        raise ValueError()

    def make_ping_client(self):
        """
        Make new ping client.

        Returns
        -------
        PingClient
            new ping client
        """
        return PingClient(self._lwip)

    def get_interfaces(self):
        """
        Return interfaces associated with the stack.

        Returns
        -------
        Dictionary(string, NetIf)
            interfaces indexed by their names
        """
        return self._interfaces

    def service_timeouts(self):
        """
        Service stack timeouts.

        lwip requires periodic call of this function to handle
        timing-dependant logic.
        """
        self._sys_check_timeouts()
