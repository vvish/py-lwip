class StackException(Exception):
    """Base class for stack-related exceptions."""


class LwipError(StackException):
    """Class representing lwip error codes."""

    _mapping = {
        -1: 'Out of memory',
        -2: 'Buffer error',
        -3: 'Timeout',
        -4: 'Routing problem',
        -5: 'Operation in progress',
        -6: 'Illegal value',
        -7: 'Operation would block',
        -8: 'Address in use',
        -9: 'Already connecting',
        -10: 'Connection already established',
        -11: 'Not connected',
        -12: 'Low level interface error',
        -13: 'Connection aborted',
        -14: 'Connection reset',
        -15: 'Connection closed',
        -16: 'Illegal argument',
    }

    def __init__(self, code):
        self._code = code

    def __str__(self):
        return self._mapping[self._code]

    def get_code(self):
        return self._code


class AllocationError(StackException):
    """Class representing error in stack memory allocation."""

    def __str__(self):
        return 'Allocation failed'
