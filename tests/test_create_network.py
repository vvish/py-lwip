"""Minimum tests to check imports and basic functionality."""

from unittest.mock import Mock

from lwip_py.emulation import EthernetNetwork

LWIP_LIB_PATH = 'lwip_lib/build/liblwip.so'


def test_create_minimum_network():
    """Test elementary network creation."""
    network = EthernetNetwork(LWIP_LIB_PATH)
    network.add_host(
        'peer_one', ('p1.eth1', '127.3.2.1', '255.255.255.0', '127.0.0.0'),
    )

    status_cbk_mock = Mock()
    network.set_status_callbacks(status_cbk_mock, status_cbk_mock)

    bus_cbk_mock = Mock()
    network.get_ethernet_bus().add_observer(bus_cbk_mock)

    network.start()
    network.set_up_interfaces()
    network.stop()

    assert status_cbk_mock.call_count == 2, 'Callback should be called twice'
    bus_cbk_mock.assert_called_once()
