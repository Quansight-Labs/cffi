import os, cffi, re
import pytest
import _cffi_ft_backend as _cffi_backend


def getlines():
    try:
        f = open(os.path.join(os.path.dirname(cffi.__file__),
                              '..', 'c', 'commontypes.c'))
    except IOError:
        pytest.skip("cannot find ../c/commontypes.c")
    lines = [line for line in f.readlines() if line.strip().startswith('EQ(')]
    f.close()
    return lines

def test_alphabetical_order():
    lines = getlines()
    assert lines == sorted(lines)

def test_dependencies():
    r = re.compile(r'EQ[(]"([^"]+)",(?:\s*"([A-Z0-9_]+)\s*[*]*"[)])?')
    lines = getlines()
    d = {}
    for line in lines:
        match = r.search(line)
        if match is not None:
            d[match.group(1)] = match.group(2)
    for value in d.values():
        if value:
            assert value in d

def test_get_common_types():
    d = {}
    _cffi_backend._get_common_types(d)
    assert d["bool"] == "_Bool"
