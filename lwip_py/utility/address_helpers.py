"""Facilities for networking addresses conversion/processing."""

import functools


def int_ip_from_string(ip_string):
    """
    Convert ip4 address from string representation into int (4 bytes).

    Parameters
    ----------
    ip_string : string
        ip4 address as string (dot-separated)

    Returns
    -------
    int
        4-byte integer ip4 address representation
    """
    addr_segments = map(int, reversed(ip_string.split('.')))
    return functools.reduce(lambda hi, lo: (hi << 8) | lo, addr_segments, 0)


def int_ip_to_string(ip_int):
    """
    Convert ip4 address from integer into string representation.

    Parameters
    ----------
    ip_int : int
        4-byte ip4 integer representation

    Returns
    -------
    string
        ip4 string representation
    """
    byte_mask = 0xFF
    return '.'.join(
        [str((ip_int >> shift) & byte_mask) for shift in (0, 8, 16, 24)],
    )
