import ctypes
import shutil
import tempfile


class MultiInstanceLibraryLoader(object):
    """
    Loads the same library multiple times.

    ctypes will load another instance of the same
    library only if the file will have a different name
    """

    def __init__(self, path_to_lib):
        self._path_to_lib = path_to_lib

    def __call__(self):
        self._tmp_lib_copy = self._make_tmp_lib_copy()
        return ctypes.CDLL(self._tmp_lib_copy.name)

    def _make_tmp_lib_copy(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=True)
        shutil.copy2(self._path_to_lib, tmp_file.name)
        return tmp_file
