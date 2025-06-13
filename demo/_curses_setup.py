from setuptools import setup

setup(
    name="_curses",
    version="0.1",
    py_modules=["_curses"],
    setup_requires=["cffi_ft>=1.0.dev0"],
    cffi_ft_modules=[
        "_curses_build.py:ffi",
    ],
    install_requires=["cffi_ft>=1.0.dev0"],   # should maybe be "cffi-backend" only?
    zip_safe=False,
)
