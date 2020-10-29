# lwIP python bindings

## Summary
The project provides python bindings for lwIP portable
network stack along with the environment to deploy the stack in the user
space.

The project status is 'Proof of concept/Work in progress'.

It was originally intended to be a study case for ctypes workshop but the outcome
can be potentially used for several side purposes:
- to be os-independent test-bed for lwIP stack;
- deploy the stack in user space and use it on top of Api for unconventional link-layers/hardware;
- experiment with and learn about lwIP stack and stack integration.

Currently the following features are available:
- loading of several instances of lwIP stack emulating separate network hosts;
- emulated user space ethernet bus providing communication between lwIP ethernet network interfaces;
- async Udp socket implementation on top of lwIP core api;
- ping (ICMP echo) functionality.

## lwIP

lwIP is a portable network stack developed to be used in embedded systems.
The stack itself is added into the source tree as a submodule and can be found
in the folder `lwip`. To be used via ctypes it is built as a shared library.
The build environment for the library is located in the folder `lwip-lib`.

## Repository

The repository has submodules so it should be cloned accordingly:

```bash
git clone https://github.com/vvish/py-lwip.git
git submodule update --init --recursive
```

or shorter

```bash
git clone --recurse-submodules https://github.com/vvish/py-lwip.git
```

## lwIP shared library

The `Makefile` in the root of the source tree has target to
build the library:

```bash
make lwip-lib
```

## Makefile

The `Makefile` also contains other targets that simplify installation of project
dependencies and tooling.

To install prerequisites, recommended tools and the package itself in the editable
mode the following command can be used:

```bash
make init
```

## Example code

The file `lwip_py/examples/examples.py` contains some reference code for the framework.
For example:
```bash
python3 lwip_py/examples/examples.py -tw -l lwip_lib/build/liblwip.so udp-ping-pong
```
will run script implementing UDP-datagram exchange and forward recorded traffic
to wireshark via scapy (wireshark should be available in the system).

## Contribution

As the project was originally intended as a reference everyone who is
interested to learn more about ctypes and python in general or experiment with
lwIP and network protocols is welcomed to use it and contribute.

Feedback in the form of change requests, defect tickets and PR-s is appreciated.

Please consider that the code is under development, provided 'as is' and no warranty is given.
