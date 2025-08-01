import sys, os
import pytest
from cffi import FFI
from cffi import recompiler, ffiplatform, VerificationMissing
from testing.udir import udir
from testing.support import u, is_musl


def setup_module(mod):
    SRC = """
    #include <string.h>
    #define FOOBAR (-42)
    static const int FOOBAZ = -43;
    #define BIGPOS 420000000000L
    #define BIGNEG -420000000000L
    int add42(int x) { return x + 42; }
    int add43(int x, ...) { return x; }
    int globalvar42 = 1234;
    const int globalconst42 = 4321;
    const char *const globalconsthello = "hello";
    struct foo_s;
    typedef struct bar_s { int x; signed char a[]; } bar_t;
    enum foo_e { AA, BB, CC };

    void init_test_re_python(void) { }      /* windows hack */
    void PyInit__test_re_python(void) { }   /* windows hack */
    """
    tmpdir = udir.join('test_re_python')
    tmpdir.ensure(dir=1)
    c_file = tmpdir.join('_test_re_python.c')
    c_file.write(SRC)
    ext = ffiplatform.get_extension(
        str(c_file),
        '_test_re_python',
        export_symbols=['add42', 'add43', 'globalvar42',
                        'globalconst42', 'globalconsthello']
    )
    outputfilename = ffiplatform.compile(str(tmpdir), ext)

    # test with a non-ascii char
    ofn, oext = os.path.splitext(outputfilename)
    if sys.platform == "win32":
        unicode_name = ofn + (u+'\u03be') + oext
    else:
        unicode_name = ofn + (u+'\xe9') + oext
        try:
            unicode_name.encode(sys.getfilesystemencoding())
        except UnicodeEncodeError:
            unicode_name = None
    if unicode_name is not None:
        print(repr(outputfilename) + ' ==> ' + repr(unicode_name))
        os.rename(outputfilename, unicode_name)
        outputfilename = unicode_name

    mod.extmod = outputfilename
    mod.tmpdir = tmpdir
    #
    ffi = FFI()
    ffi.cdef("""
    #define FOOBAR -42
    static const int FOOBAZ = -43;
    #define BIGPOS 420000000000L
    #define BIGNEG -420000000000L
    int add42(int);
    int add43(int, ...);
    extern int globalvar42;
    const int globalconst42;
    const char *const globalconsthello;
    int no_such_function(int);
    extern int no_such_globalvar;
    struct foo_s;
    typedef struct bar_s { int x; signed char a[]; } bar_t;
    enum foo_e { AA, BB, CC };
    int strlen(const char *);
    struct with_union { union { int a; char b; }; };
    union with_struct { struct { int a; char b; }; };
    struct with_struct_with_union { struct { union { int x; }; } cp; };
    struct NVGcolor { union { float rgba[4]; struct { float r,g,b,a; }; }; };
    typedef struct selfref { struct selfref *next; } *selfref_ptr_t;
    """)
    ffi.set_source('re_python_pysrc', None)
    ffi.emit_python_code(str(tmpdir.join('re_python_pysrc.py')))
    mod.original_ffi = ffi
    #
    sys.path.insert(0, str(tmpdir))


def test_constant():
    from re_python_pysrc import ffi
    assert ffi.integer_const('FOOBAR') == -42
    assert ffi.integer_const('FOOBAZ') == -43

def test_large_constant():
    from re_python_pysrc import ffi
    assert ffi.integer_const('BIGPOS') == 420000000000
    assert ffi.integer_const('BIGNEG') == -420000000000

def test_function():
    import _cffi_ft_backend as _cffi_backend
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    assert lib.add42(-10) == 32
    assert type(lib.add42) is _cffi_backend.FFI.CData

def test_function_with_varargs():
    import _cffi_ft_backend as _cffi_backend
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod, 0)
    assert lib.add43(45, ffi.cast("int", -5)) == 45
    assert type(lib.add43) is _cffi_backend.FFI.CData

def test_dlopen_none():
    import _cffi_ft_backend as _cffi_backend
    from re_python_pysrc import ffi
    name = None
    if sys.platform == 'win32':
        import ctypes.util
        name = ctypes.util.find_msvcrt()
        if name is None:
            pytest.skip("dlopen(None) cannot work on Windows with Python 3")
    lib = ffi.dlopen(name)
    assert lib.strlen(b"hello") == 5

def test_dlclose():
    import _cffi_ft_backend as _cffi_backend
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    ffi.dlclose(lib)
    if type(extmod) is not str:   # unicode, on python 2
        str_extmod = extmod.encode('utf-8')
    else:
        str_extmod = extmod
    e = pytest.raises(ffi.error, getattr, lib, 'add42')
    assert str(e.value) == (
        "library '%s' has been closed" % (str_extmod,))
    ffi.dlclose(lib)   # does not raise

def test_constant_via_lib():
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    assert lib.FOOBAR == -42
    assert lib.FOOBAZ == -43

def test_opaque_struct():
    from re_python_pysrc import ffi
    ffi.cast("struct foo_s *", 0)
    pytest.raises(TypeError, ffi.new, "struct foo_s *")

def test_nonopaque_struct():
    from re_python_pysrc import ffi
    for p in [ffi.new("struct bar_s *", [5, b"foobar"]),
              ffi.new("bar_t *", [5, b"foobar"])]:
        assert p.x == 5
        assert p.a[0] == ord('f')
        assert p.a[5] == ord('r')

def test_enum():
    from re_python_pysrc import ffi
    assert ffi.integer_const("BB") == 1
    e = ffi.cast("enum foo_e", 2)
    assert ffi.string(e) == "CC"

@pytest.mark.thread_unsafe
def test_include_1():
    sub_ffi = FFI()
    sub_ffi.cdef("static const int k2 = 121212;")
    sub_ffi.include(original_ffi)
    assert 'macro FOOBAR' in original_ffi._parser._declarations
    assert 'macro FOOBAZ' in original_ffi._parser._declarations
    sub_ffi.set_source('re_python_pysrc', None)
    sub_ffi.emit_python_code(str(tmpdir.join('_re_include_1.py')))
    #
    if sys.version_info[:2] >= (3, 3):
        import importlib
        importlib.invalidate_caches()  # issue 197 (but can't reproduce myself)
    #
    from _re_include_1 import ffi
    assert ffi.integer_const('FOOBAR') == -42
    assert ffi.integer_const('FOOBAZ') == -43
    assert ffi.integer_const('k2') == 121212
    lib = ffi.dlopen(extmod)     # <- a random unrelated library would be fine
    assert lib.FOOBAR == -42
    assert lib.FOOBAZ == -43
    assert lib.k2 == 121212
    #
    p = ffi.new("bar_t *", [5, b"foobar"])
    assert p.a[4] == ord('a')

@pytest.mark.thread_unsafe
def test_global_var():
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    assert lib.globalvar42 == 1234
    p = ffi.addressof(lib, 'globalvar42')
    lib.globalvar42 += 5
    assert p[0] == 1239
    p[0] -= 1
    assert lib.globalvar42 == 1238

def test_global_const_int():
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    assert lib.globalconst42 == 4321
    pytest.raises(AttributeError, ffi.addressof, lib, 'globalconst42')

def test_global_const_nonint():
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    assert ffi.string(lib.globalconsthello, 8) == b"hello"
    pytest.raises(AttributeError, ffi.addressof, lib, 'globalconsthello')

def test_rtld_constants():
    from re_python_pysrc import ffi
    ffi.RTLD_NOW    # check that we have the attributes
    ffi.RTLD_LAZY
    ffi.RTLD_GLOBAL

def test_no_such_function_or_global_var():
    from re_python_pysrc import ffi
    lib = ffi.dlopen(extmod)
    e = pytest.raises(ffi.error, getattr, lib, 'no_such_function')
    assert str(e.value).startswith(
        "symbol 'no_such_function' not found in library '")
    e = pytest.raises(ffi.error, getattr, lib, 'no_such_globalvar')
    assert str(e.value).startswith(
        "symbol 'no_such_globalvar' not found in library '")

def test_check_version():
    import _cffi_ft_backend as _cffi_backend
    e = pytest.raises(ImportError, _cffi_backend.FFI,
                       "foobar", _version=0x2594)
    assert str(e.value).startswith(
        "cffi out-of-line Python module 'foobar' has unknown version")

def test_partial_enum():
    ffi = FFI()
    ffi.cdef("enum foo { A, B, ... };")
    ffi.set_source('test_partial_enum', None)
    pytest.raises(VerificationMissing, ffi.emit_python_code,
                   str(tmpdir.join('test_partial_enum.py')))

@pytest.mark.thread_unsafe
def test_anonymous_union_inside_struct():
    # based on issue #357
    from re_python_pysrc import ffi
    INT = ffi.sizeof("int")
    assert ffi.offsetof("struct with_union", "a") == 0
    assert ffi.offsetof("struct with_union", "b") == 0
    assert ffi.sizeof("struct with_union") == INT
    #
    assert ffi.offsetof("union with_struct", "a") == 0
    assert ffi.offsetof("union with_struct", "b") == INT
    assert ffi.sizeof("union with_struct") >= INT + 1
    #
    assert ffi.sizeof("struct with_struct_with_union") == INT
    p = ffi.new("struct with_struct_with_union *")
    assert p.cp.x == 0
    #
    FLOAT = ffi.sizeof("float")
    assert ffi.sizeof("struct NVGcolor") == FLOAT * 4
    assert ffi.offsetof("struct NVGcolor", "rgba") == 0
    assert ffi.offsetof("struct NVGcolor", "r") == 0
    assert ffi.offsetof("struct NVGcolor", "g") == FLOAT
    assert ffi.offsetof("struct NVGcolor", "b") == FLOAT * 2
    assert ffi.offsetof("struct NVGcolor", "a") == FLOAT * 3

@pytest.mark.thread_unsafe
def test_selfref():
    # based on issue #429
    from re_python_pysrc import ffi
    ffi.new("selfref_ptr_t")

def test_dlopen_handle():
    import _cffi_ft_backend as _cffi_backend
    from re_python_pysrc import ffi
    if sys.platform == 'win32' or is_musl or sys.platform.startswith('freebsd'):
        pytest.skip("uses 'dl' explicitly")
    ffi1 = FFI()
    ffi1.cdef("""void *dlopen(const char *filename, int flags);
                 int dlclose(void *handle);""")
    lib1 = ffi1.dlopen('dl')
    handle = lib1.dlopen(extmod.encode(sys.getfilesystemencoding()),
                         _cffi_backend.RTLD_LAZY)
    assert ffi1.typeof(handle) == ffi1.typeof("void *")
    assert handle

    lib = ffi.dlopen(handle)
    assert lib.add42(-10) == 32
    assert type(lib.add42) is _cffi_backend.FFI.CData

    err = lib1.dlclose(handle)
    assert err == 0

@pytest.mark.thread_unsafe
def test_rec_structs_1():
    ffi = FFI()
    ffi.cdef("struct B { struct C* c; }; struct C { struct B b; };")
    ffi.set_source('test_rec_structs_1', None)
    ffi.emit_python_code(str(tmpdir.join('_rec_structs_1.py')))
    #
    if sys.version_info[:2] >= (3, 3):
        import importlib
        importlib.invalidate_caches()  # issue 197, maybe
    #
    from _rec_structs_1 import ffi
    # the following line used to raise TypeError
    # unless preceeded by 'ffi.sizeof("struct C")'.
    sz = ffi.sizeof("struct B")
    assert sz == ffi.sizeof("int *")

@pytest.mark.thread_unsafe
def test_rec_structs_2():
    ffi = FFI()
    ffi.cdef("struct B { struct C* c; }; struct C { struct B b; };")
    ffi.set_source('test_rec_structs_2', None)
    ffi.emit_python_code(str(tmpdir.join('_rec_structs_2.py')))
    #
    if sys.version_info[:2] >= (3, 3):
        import importlib
        importlib.invalidate_caches()  # issue 197, maybe
    #
    from _rec_structs_2 import ffi
    sz = ffi.sizeof("struct C")
    assert sz == ffi.sizeof("int *")
