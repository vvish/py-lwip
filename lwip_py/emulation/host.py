"""
Emulation of the host on which the lwIP stack is deployed.

Provides single threaded execution context in which accesses to stack
should be done.

Emulates deployment model intended for no-OS integration, where single
processing thread is used.
"""
import threading

from lwip_py.stack.ip_address import IpV4Addr
from lwip_py.utility import scheduler


class Host(object):
    """
    Class represents the host in network emulation.

    The Host class aggregates the properties belonging to single
    emulated host. It owns the instance of the stack 'deployed' on the
    host.
    """

    def __init__(self, stack):
        """
        Initialize new Host object.

        Parameters
        ----------
        stack : Stack
            network stack instance
        """
        self._stack = stack
        self._task_queue = scheduler.SingleThreadExecutor()
        self._working_thread = threading.Thread(target=self._task_queue.run)

        self._stack.init()

    def add_network_interface(self, name, address, mask=None, gateway=None):
        """
        Create new network interface for the host.

        Parameters
        ----------
        name : string
            name of the interface
        address : string
            ip address of the new interface
        mask : string, optional
            network mask, by default None
        gateway : string, optional
            ip address of the default gateway, by default None

        Returns
        -------
        NetIf
            new network interface
        """
        interface_ip = IpV4Addr(address)
        network_mask = IpV4Addr(mask) if mask else None
        gateway = IpV4Addr(gateway) if gateway else None

        interface = self._stack.make_interface(name)
        interface.set_name(b'In')
        interface.add(interface_ip, network_mask, gateway)

        interface.set_etharp_flag()

        return interface

    def set_up_interfaces(self, sync=False):
        """
        Activate the host interfaces.

        The network interfaces belonging to the host will be
        activated (interface and link will be set up) in the host
        execution context

        Parameters
        ----------
        sync : bool, optional
            should operation be syncronized, by default False
        """
        task = self._task_queue.schedule_delayed(
            scheduler.IMMEDIATE, scheduler.TOP_PRIO, self._set_up_interfaces,
        )
        if sync:
            task.result()

    def start(self):
        """
        Start handling of the stack activities on the host.

        The thread responsible for execution in the host context
        will be started
        """
        self._working_thread.start()

    def stop(self):
        """Stop handling of the networking activities on the host."""
        self._task_queue.stop(sync=True)
        self._working_thread.join()

    def get_stack(self):
        return self._stack

    def get_interface(self, name):
        """
        Return interface by name.

        Parameters
        ----------
        name : string
            interface name

        Returns
        -------
        NetIf
            requested network interface
        """
        return self._stack.get_interfaces()[name]

    def on_incoming_data(self, interface, incoming_data):
        """
        Forward data to the host.

        Parameters
        ----------
        interface : NetIf
            interface for which the data is addressed
        incoming_data : arraylike
            data to forward
        """
        self._task_queue.schedule_delayed(
            scheduler.IMMEDIATE,
            scheduler.TOP_PRIO,
            interface.input_data,
            incoming_data,
        )

    def execute(self, action, delay=0):
        """
        Execute action in the context of the host thread.

        Parameters
        ----------
        action : executable
            action to execute

        Returns
        -------
        future
            future for the scheduled task
        """
        return self._task_queue.schedule_delayed(
            delay, scheduler.TOP_PRIO, action, self,
        )

    def _set_up_interfaces(self):
        for inf in self._stack.get_interfaces().values():
            inf.set_link_up()
            inf.set_up()
