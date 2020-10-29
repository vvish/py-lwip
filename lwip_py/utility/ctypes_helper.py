"""
Helper to initialize ctypes function wrappers.

The code for this function is mostly taken from
https://dbader.org/blog/python-ctypes-tutorial-part-2
"""


def wrap_function(lib, func_name, res_type, arg_types):
    """
    Make ctypes function wrapper.

    Parameters
    ----------
    lib : library object
        library loaded via ctypes
    func_name : string
        name of the function
    res_type : ctypes type object
        function return type
    arg_types : array_like of ctypes type objects
        array of ctypes type objects corresponding to function arguments

    Returns
    -------
    ctypes function wrapper
        created function wrapper
    """
    function_wrapper = lib.__getattr__(func_name)
    function_wrapper.restype = res_type
    function_wrapper.argtypes = arg_types
    return function_wrapper
