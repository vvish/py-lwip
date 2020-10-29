"""
Examples of lwip-python bindings application.

The following scenarious are currently included:
1. ICMP ping;
2. UDP ping-pong (exchange by datagrams between peers).

To run example lwip lib should be built first.

To get information about cmd arguments the script can be excuted
with --help parameter.
"""
import argparse
import threading

import scapy.all as scapy
from lwip_py.emulation import EthernetNetwork
from lwip_py.output import EthernetRecorder
from lwip_py.stack import IpAddr, IpV4Addr, SocketTypes


class _PingApp(object):
    def __init__(self, address_to_ping):
        self._completion = threading.Event()
        self._address_to_ping = address_to_ping

    def ping(self, host):
        self._ping_client = host.get_stack().make_ping_client()
        self._ping_client.ping(self._address_to_ping, self._on_ping_result)

    def wait_for_completion(self):
        self._completion.wait()

    def _on_ping_result(self, ping_result):
        self._completion.set()


class _UdpPingPongApp(object):
    def __init__(self, source_peer, max_counter):
        self._source_peer = source_peer
        self._max_counter = max_counter

        self.completion = threading.Event()

    def start(self, host):
        self._host = host
        self._socket = host.get_stack().make_socket(SocketTypes.sock_dgram)
        self._socket.bind(self._source_peer)
        self._socket.set_recv_callback(self._receive_data)

    def start_and_send_ping(self, host, target):
        self.start(host)
        self._send_ping(target, 1)

    def _receive_data(self, socket, received_data, addres_from, port_from):
        counter = int.from_bytes(received_data, 'big')
        if counter < self._max_counter:
            new_counter = counter + 1
            self._host.execute(
                lambda _: self._send_ping(
                    (addres_from, port_from), new_counter,
                ),
            )
            if new_counter == self._max_counter:
                self.completion.set()
        else:
            self.completion.set()

    def _send_ping(self, destination, counter):
        self._socket.send_to(
            counter.to_bytes(4, 'big'), *destination,
        )


def _ethernet_logger(printer, netif, frame, was_forwarded):
    incoming_data = bytearray(frame)
    eth_frame = scapy.Ether(scapy.raw(incoming_data))

    ip_format_str = (
        '{Ether:%Ether.src% > %Ether.dst%} ' +
        '{ARP:ARP %ARP.op%} ' +
        '{IP:IP %IP.src% > %IP.dst%} ' +
        '{ICMP:ICMP %ICMP.type% %ICMP.code%} ' +
        '{UDP:UDP %UDP.sport% > %UDP.dport%} '
    )

    printer(eth_frame.sprintf(ip_format_str))


def _parse_args(program_description, available_scenarious):
    arg_parser = argparse.ArgumentParser(
        description=program_description,
    )
    arg_parser.add_argument(
        'scenario', help='scenario to execute', choices=available_scenarious,
    )

    arg_parser.add_argument(
        '-w',
        '--wireshark',
        help='forward trafic to wireshark',
        action='store_true',
    )

    arg_parser.add_argument(
        '-t',
        '--traffic_trace',
        help='output text traffic log',
        action='store_true',
    )

    arg_parser.add_argument(
        '-l',
        '--lwip_lib',
        help='path to lwip shared library',
        default=None,
    )

    arg_parser.add_argument(
        '-i',
        '--interface_logs',
        help='verbose logging of the network interfaces statuses',
        action='store_true',
    )

    return arg_parser.parse_args()


def _run_example():
    examples = ['udp-ping-pong', 'icmp-ping']
    args = _parse_args('lwip-python examples', examples)

    network = EthernetNetwork(args.lwip_lib)
    network.add_host(
        'peer_one', ('p1.eth1', '127.3.2.1', '255.255.255.0', '127.0.0.0'),
    )
    network.add_host(
        'peer_two', ('p2.eth1', '127.3.2.2', '255.255.255.0', '127.0.0.0'),
    )

    if args.interface_logs:
        network.set_status_callbacks(print, print)

    if args.traffic_trace:
        network.get_ethernet_bus().add_observer(
            lambda *args: _ethernet_logger(print, *args),
        )

    if args.wireshark:
        ethernet_recorder = EthernetRecorder()
        network.get_ethernet_bus().add_observer(ethernet_recorder)

    network.start()
    network.set_up_interfaces()

    if args.scenario == 'udp-ping-pong':
        peer_one_app = _UdpPingPongApp(('', 1000), 10)
        network.get_host('peer_one').execute(peer_one_app.start).result()

        peer_two_app = _UdpPingPongApp(('', 2000), 10)
        network.get_host('peer_two').execute(
            lambda host: peer_two_app.start_and_send_ping(
                host, (IpV4Addr('127.3.2.1'), 1000),
            ),
        ).result()

        peer_one_app.completion.wait()
        peer_two_app.completion.wait()

    elif args.scenario == 'icmp-ping':
        ping_app = _PingApp(IpAddr(IpV4Addr('127.3.2.2')))
        network.get_host('peer_one').execute(ping_app.ping).result()
        ping_app.wait_for_completion()

    network.stop()

    if args.wireshark:
        frames = (
            scapy.Ether(
                scapy.raw(rd),
            ) for rd in ethernet_recorder.recorded_frames
        )
        scapy.wireshark(frames)


if __name__ == '__main__':
    _run_example()
