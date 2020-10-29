import ctypes

from lwip_py.stack.pbuf import PBuf
from lwip_py.utility import ctypes_helper


class Allocator(object):
    def __init__(self, lwip):
        """
        Initialize new object.

        Parameters
        ----------
        lwip : lib instance (loaded via ctypes)
            lwip library instance
        """
        self._pbuf_alloc = ctypes_helper.wrap_function(
            lwip,
            'pbuf_alloc',
            ctypes.POINTER(PBuf),
            [ctypes.c_int64, ctypes.c_uint16, ctypes.c_int64],
        )

        self._pbuf_take = ctypes_helper.wrap_function(
            lwip,
            'pbuf_take',
            ctypes.c_int8,
            [ctypes.POINTER(PBuf), ctypes.c_void_p, ctypes.c_uint16],
        )

        self._pbuf_free = ctypes_helper.wrap_function(
            lwip, 'pbuf_free', ctypes.c_uint8, [ctypes.POINTER(PBuf)],
        )

    def allocate_raw_pbuf(self, size):
        """
        Allocate raw memory buffer via lwip stack facilities.

        To forward data into the stack it has to be placed in the
        memory managed by the stack

        Parameters
        ----------
        size : integer
            size of the block to allocate

        Returns
        -------
        PBuf
            object representing allocated buffer
        """
        pbuf_raw = 1
        pbuf_pool = 386

        new_pbuf = self._pbuf_alloc(pbuf_raw, size, pbuf_pool)
        return new_pbuf.contents

    def allocate_raw_pbuf_from_data(self, data_to_place, size=None):
        """
        Allocate raw buffer and place data there.

        Parameters
        ----------
        data_to_place : array_like
            data to place into pbuf
        size : integer, optional
            size of the block to allocate

        Returns
        -------
        PBuf
            object representing allocated buffer
        """
        size = size or len(data_to_place)

        new_pbuf = self.allocate_raw_pbuf(size)
        self._pbuf_take(new_pbuf, data_to_place, size)
        return new_pbuf

    def allocate_transport_pbuf_from_data(self, data_to_place, size=None):
        """
        Allocate pbuf for transport layer payload.

        Parameters
        ----------
        data_to_place : array_like
            data to place into pbuf
        size : integer
            size of the block to allocate

        Returns
        -------
        PBuf
            object representing allocated buffer
        """
        pbuf_transport = 74
        pbuf_ram = 640

        size = size or len(data_to_place)

        new_pbuf = self._pbuf_alloc(pbuf_transport, size, pbuf_ram)
        self._pbuf_take(new_pbuf, data_to_place, size)
        return new_pbuf.contents

    def free_pbuf(self, pbuf):
        """
        Free previously allocated PBuf.

        Parameters
        ----------
        pbuf : PBuf
            pbuf representing chain to deallocate

        Returns
        -------
        int
            number of pbuf-s released
        """
        return int(self._pbuf_free(pbuf))
