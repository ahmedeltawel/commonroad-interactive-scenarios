"""
Helper module for the marking of tests
"""
from functools import wraps
import pytest
from enum import Enum
import threading

__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Peter Kocsis"
__email__ = "peter.kocsis@tum.de"
__status__ = "Integration"

lock_obj = threading.Lock()


class RunScope(Enum):
    """Enum for the scope of the single_Ibbenbueren methods"""

    UNIT_TEST = "unit"
    MODULE_TEST = "module"
    INTEGRATION_TEST = "integration"


class RunType(Enum):
    """Enum for the type of the single_Ibbenbueren methods"""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


def unit_test(*args, **kwargs):
    """Unit single_Ibbenbueren marker decorator"""
    return pytest.mark.scope.with_args(RunScope.UNIT_TEST)(*args, **kwargs)


def module_test(*args, **kwargs):
    """Module single_Ibbenbueren marker decorator"""
    return pytest.mark.scope.with_args(RunScope.MODULE_TEST)(*args, **kwargs)


def integration_test(*args, **kwargs):
    """Integration single_Ibbenbueren marker decorator"""
    return pytest.mark.scope.with_args(RunScope.INTEGRATION_TEST)(*args, **kwargs)


def functional(*args, **kwargs):
    """Functional single_Ibbenbueren marker decorator"""
    return pytest.mark.type.with_args(RunType.FUNCTIONAL)(*args, **kwargs)


def nonfunctional(*args, **kwargs):
    """Non-functional single_Ibbenbueren marker decorator"""
    return pytest.mark.type.with_args(RunType.NON_FUNCTIONAL)(*args, **kwargs)


def slow(*args, **kwargs):
    """Slow single_Ibbenbueren marker decorator"""
    return pytest.mark.slow(*args, **kwargs)


def serial(func):
    """Serial single_Ibbenbueren marker decorator"""
    serial_func = pytest.mark.serial(func)

    @wraps(serial_func)
    def inner_func(*args, **kwargs):
        lock_obj.acquire()
        try:
            result = serial_func(*args, **kwargs)
        finally:
            lock_obj.release()
        return result

    return inner_func
