"""Model of a primitive ethernet network."""
from lwip_py.emulation.ethernet_bus import EthernetBus
from lwip_py.emulation.host import Host
from lwip_py.stack import Stack
from lwip_py.utility import MultiInstanceLibraryLoader


class EthernetNetwork(object):
    """
    Class facilitates creation of the emulated network.

    Class aggregates ethernet bus and multiple hosts providing methods
    to configure them.
    """

    def __init__(self, path_to_lwip_lib):
        self._path_to_lwip_lib = path_to_lwip_lib
        self._ethernet_bus = EthernetBus()
        self._hosts = {}
        self._status_callback = None
        self._link_callback = None

    def add_host(self, host_name, *host_interfaces):
        """
        Add new network interface.

        Parameters
        ----------
        host_name : string
            interface name
        host_interfaces : enumerable(name, address, mask, gateway)
            interface parameters
        """
        stack = Stack(MultiInstanceLibraryLoader(self._path_to_lwip_lib))
        host = Host(stack)

        for interface in host_interfaces:
            new_interface = host.add_network_interface(*interface)
            new_interface.set_status_callbacks(
                self._internal_status_callback,
                self._internal_link_callback,
            )
            self._ethernet_bus.add_interface(
                new_interface, host.on_incoming_data,
            )

        self._hosts[host_name] = host

    def get_host(self, host_name):
        return self._hosts[host_name]

    def get_ethernet_bus(self):
        return self._ethernet_bus

    def set_status_callbacks(self, status_callback, link_callback):
        self._status_callback = status_callback
        self._link_callback = link_callback

    def start(self):
        self._ethernet_bus.start()
        for host in self._hosts.values():
            host.start()

    def stop(self):
        self._ethernet_bus.stop()
        for host in self._hosts.values():
            host.stop()

    def set_up_interfaces(self):
        for host in self._hosts.values():
            host.set_up_interfaces(True)

    def _internal_status_callback(self, net_if):
        if self._status_callback:
            self._status_callback(net_if)

    def _internal_link_callback(self, net_if):
        if self._link_callback:
            self._link_callback(net_if)
