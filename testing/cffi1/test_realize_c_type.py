import sys
import pytest
from cffi import cffi_opcode


def check(input, expected_output=None, expected_ffi_error=False):
    import _cffi_ft_backend as _cffi_backend
    ffi = _cffi_backend.FFI()
    if not expected_ffi_error:
        ct = ffi.typeof(input)
        assert isinstance(ct, ffi.CType)
        assert ct.cname == (expected_output or input)
    else:
        e = pytest.raises(ffi.error, ffi.typeof, input)
        if isinstance(expected_ffi_error, str):
            assert str(e.value) == expected_ffi_error

def test_void():
    check("void", "void")
    check("  void  ", "void")

def test_int_star():
    check("int")
    check("int *")
    check("int*", "int *")
    check("long int", "long")
    check("long")

def test_noop():
    check("int(*)", "int *")

def test_array():
    check("int[6]")

def test_funcptr():
    check("int(*)(long)")
    check("int(long)", expected_ffi_error="the type 'int(long)' is a"
          " function type, not a pointer-to-function type")
    check("int(void)", expected_ffi_error="the type 'int()' is a"
          " function type, not a pointer-to-function type")

def test_funcptr_rewrite_args():
    check("int(*)(int(int))", "int(*)(int(*)(int))")
    check("int(*)(long[])", "int(*)(long *)")
    check("int(*)(long[5])", "int(*)(long *)")

def test_all_primitives():
    for name in cffi_opcode.PRIMITIVE_TO_INDEX:
        check(name, name)

def check_func(input, expected_output=None):
    import _cffi_ft_backend as _cffi_backend
    ffi = _cffi_backend.FFI()
    ct = ffi.typeof(ffi.callback(input, lambda: None))
    assert isinstance(ct, ffi.CType)
    if sys.platform != 'win32' or sys.maxsize > 2**32:
        expected_output = expected_output.replace('__stdcall *', '*')
    assert ct.cname == expected_output

def test_funcptr_stdcall():
    check_func("int(int)", "int(*)(int)")
    check_func("int foobar(int)", "int(*)(int)")
    check_func("int __stdcall(int)", "int(__stdcall *)(int)")
    check_func("int __stdcall foobar(int)", "int(__stdcall *)(int)")
    check_func("void __cdecl(void)", "void(*)()")
    check_func("void __cdecl foobar(void)", "void(*)()")
    check_func("void __stdcall(void)", "void(__stdcall *)()")
    check_func("void __stdcall foobar(long, short)",
                   "void(__stdcall *)(long, short)")
    check_func("void(void __cdecl(void), void __stdcall(void))",
                   "void(*)(void(*)(), void(__stdcall *)())")

def test_variadic_overrides_stdcall():
    check("void (__stdcall*)(int, ...)", "void(*)(int, ...)")
