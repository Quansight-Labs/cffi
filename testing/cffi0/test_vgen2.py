import cffi_ft.verifier as verifier
from .test_vgen import *

# This test file runs normally after test_vgen.  We only clean up the .c
# sources, to check that it also works when we have only the .so.  The
# tests should run much faster than test_vgen.

def setup_module():
    verifier.cleanup_tmpdir(keep_so=True)
    verifier._FORCE_GENERIC_ENGINE = True

def teardown_module():
    verifier._FORCE_GENERIC_ENGINE = False
