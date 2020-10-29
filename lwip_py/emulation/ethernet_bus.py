import threading

from lwip_py.utility import SingleThreadExecutor


class EthernetBus(object):
    """
    Class emulates a bus distributing data to all subscribed interfaces.

    The class provides possibility to register observers that will be
    triggered if data is forwarded via bus.

    """

    def __init__(self, *interfaces):
        """
        Initialize a new object.

        Parameters
        ----------
        interfaces : array_like
            arbitrary set of interfaces that should be added to bus
        """
        self._interfaces = list(interfaces)

        for iface in self._interfaces:
            iface[0].set_output_callbacks(self.get_output_callback())

        self._observers = []
        self._filters = []

        self._task_queue = SingleThreadExecutor()
        self._task_thread = threading.Thread(target=self._task_queue.run)

    def add_observer(self, observer_to_add):
        """
        Add observer to react on data transmission.

        Observer is an executable that receives two parameters:
            source network interface of type NetIf
            data that is forwarded

        Parameters
        ----------
        observer : executable
            executable that wil be invoked when the bus forwards data
        """
        self._observers.append(observer_to_add)

    def add_filter(self, filter_to_add):
        """
        Add filter to control if data should be forwarded.

        Filter is an executable that receives two parameters:
            source network interface of type NetIf
            data that is forwarded

        and returns True if data should be forwarded, False otherwise

        Parameters
        ----------
        filter_to_add : executable
            executable that wil be invoked when the bus has data to
            forward
        """
        self._filters.append(filter_to_add)

    def add_interface(self, interface, on_data_callback):
        """
        Connect interface to the bus.

        Parameters
        ----------
        interface : NetIF
            [description]
        on_data_callback : [type]
            [description]
        """
        self._interfaces.append((interface, on_data_callback))
        interface.set_output_callbacks(self.get_output_callback())

    def broadcast(self, netif_from, data_to_broadcast):
        """
        Forward data to all interfaces connected to the bus.

        Parameters
        ----------
        netif_from : NetIf
            source network interface
        data_to_broadcast : array_like
            data that will be forwarded
        """
        self._task_queue.schedule_delayed(
            0, 0, self._broadcast, netif_from, data_to_broadcast,
        )

    def get_output_callback(self):
        """
        Return output callback that should be used by interfaces.

        The interface should be used to forward data via the bus

        Returns
        -------
        callable
            The callback to forward data via the bus
        """
        return lambda iface, data_to_send: self.broadcast(iface, data_to_send)

    def start(self):
        """
        Activate the bus.

        The bus starts processing data
        """
        self._task_thread.start()

    def stop(self):
        """
        Stop the bus.

        After the call no data should be forwarded to the bus
        """
        self._task_queue.stop(sync=True)
        self._task_thread.join()

    def _broadcast(self, netif_from, data_to_broadcast):
        should_forward = all(
            map(lambda fi: fi(netif_from, data_to_broadcast), self._filters),
        ) if self._filters else True

        for observer in self._observers:
            observer(netif_from, data_to_broadcast, should_forward)

        if should_forward:
            for interface, callback in self._interfaces:
                if interface != netif_from:
                    callback(interface, data_to_broadcast)
