import cffi_ft.verifier as verifier
from .test_verify import *


def setup_module():
    verifier.cleanup_tmpdir()
    verifier._FORCE_GENERIC_ENGINE = True
    # Runs all tests with _FORCE_GENERIC_ENGINE = True, to make sure we
    # also test vengine_gen.py.

def teardown_module():
    verifier._FORCE_GENERIC_ENGINE = False
