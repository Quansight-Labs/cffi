#
# ----------------------------------------------
# WARNING, ALL LITERALS IN THIS FILE ARE UNICODE
# ----------------------------------------------
#
from __future__ import unicode_literals
#
#
#
from _cffi_ft_backend import FFI


def test_cast():
    ffi = FFI()
    assert int(ffi.cast("int", 3.14)) == 3        # unicode literal

def test_new():
    ffi = FFI()
    assert ffi.new("int[]", [3, 4, 5])[2] == 5    # unicode literal

def test_typeof():
    ffi = FFI()
    tp = ffi.typeof("int[51]")                    # unicode literal
    assert tp.length == 51

def test_sizeof():
    ffi = FFI()
    assert ffi.sizeof("int[51]") == 51 * 4        # unicode literal

def test_alignof():
    ffi = FFI()
    assert ffi.alignof("int[51]") == 4            # unicode literal

def test_getctype():
    ffi = FFI()
    assert ffi.getctype("int**") == "int * *"     # unicode literal
    assert type(ffi.getctype("int**")) is str

def test_callback():
    ffi = FFI()
    cb = ffi.callback("int(int)",                 # unicode literal
                      lambda x: x + 42)
    assert cb(5) == 47
