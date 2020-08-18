# Copyright (C) 2020 FireEye, Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
# You may obtain a copy of the License at: [package root]/LICENSE.txt
# Unless required by applicable law or agreed to in writing, software distributed under the License
#  is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import os
import sys
import os.path
import contextlib
import collections

import pytest

import capa.main
import capa.features.file
import capa.features.insn
import capa.features.basicblock
from capa.features import ARCH_X32, ARCH_X64

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache


CD = os.path.dirname(__file__)


@contextlib.contextmanager
def xfail(condition, reason=None):
    """
    context manager that wraps a block that is expected to fail in some cases.
    when it does fail (and is expected), then mark this as pytest.xfail.
    if its unexpected, raise an exception, so the test fails.

    example::

        # this test:
        #  - passes on py3 if foo() works
        #  - fails  on py3 if foo() fails
        #  - xfails on py2 if foo() fails
        #  - fails  on py2 if foo() works
        with xfail(sys.version_info < (3, 0), reason="py2 doesn't foo"):
            foo()
    """
    try:
        # do the block
        yield
    except:
        if condition:
            # we expected the test to fail, so raise and register this via pytest
            pytest.xfail(reason)
        else:
            # we don't expect an exception, so the test should fail
            raise
    else:
        if not condition:
            # here we expect the block to run successfully,
            # and we've received no exception,
            # so this is good
            pass
        else:
            # we expected an exception, but didn't find one. that's an error.
            raise RuntimeError("expected to fail, but didn't")


@lru_cache()
def get_viv_extractor(path):
    import capa.features.extractors.viv

    if "raw32" in path:
        vw = capa.main.get_workspace(path, "sc32", should_save=False)
    elif "raw64" in path:
        vw = capa.main.get_workspace(path, "sc64", should_save=False)
    else:
        vw = capa.main.get_workspace(path, "auto", should_save=True)
    return capa.features.extractors.viv.VivisectFeatureExtractor(vw, path)


@lru_cache()
def extract_file_features(extractor):
    features = collections.defaultdict(set)
    for feature, va in extractor.extract_file_features():
        features[feature].add(va)
    return features


# f may not be hashable (e.g. ida func_t) so cannot @lru_cache this
def extract_function_features(extractor, f):
    features = collections.defaultdict(set)
    for bb in extractor.get_basic_blocks(f):
        for insn in extractor.get_instructions(f, bb):
            for feature, va in extractor.extract_insn_features(f, bb, insn):
                features[feature].add(va)
        for feature, va in extractor.extract_basic_block_features(f, bb):
            features[feature].add(va)
    for feature, va in extractor.extract_function_features(f):
        features[feature].add(va)
    return features


# f may not be hashable (e.g. ida func_t) so cannot @lru_cache this
def extract_basic_block_features(extractor, f, bb):
    features = collections.defaultdict(set)
    for insn in extractor.get_instructions(f, bb):
        for feature, va in extractor.extract_insn_features(f, bb, insn):
            features[feature].add(va)
    for feature, va in extractor.extract_basic_block_features(f, bb):
        features[feature].add(va)
    return features


def get_data_path_by_name(name):
    if name == "mimikatz":
        return os.path.join(CD, "data", "mimikatz.exe_")
    elif name == "kernel32":
        return os.path.join(CD, "data", "kernel32.dll_")
    elif name == "kernel32-64":
        return os.path.join(CD, "data", "kernel32-64.dll_")
    elif name == "pma12-04":
        return os.path.join(CD, "data", "Practical Malware Analysis Lab 12-04.exe_")
    elif name == "pma21-01":
        return os.path.join(CD, "data", "Practical Malware Analysis Lab 21-01.exe_")
    elif name == "al-khaser x86":
        return os.path.join(CD, "data", "al-khaser_x86.exe_")
    elif name.startswith("39c05"):
        return os.path.join(CD, "data", "39c05b15e9834ac93f206bc114d0a00c357c888db567ba8f5345da0529cbed41.dll_")
    elif name.startswith("499c2"):
        return os.path.join(CD, "data", "499c2a85f6e8142c3f48d4251c9c7cd6.raw32")
    elif name.startswith("9324d"):
        return os.path.join(CD, "data", "9324d1a8ae37a36ae560c37448c9705a.exe_")
    elif name.startswith("a1982"):
        return os.path.join(CD, "data", "a198216798ca38f280dc413f8c57f2c2.exe_")
    elif name.startswith("a933a"):
        return os.path.join(CD, "data", "a933a1a402775cfa94b6bee0963f4b46.dll_")
    elif name.startswith("bfb9b"):
        return os.path.join(CD, "data", "bfb9b5391a13d0afd787e87ab90f14f5.dll_")
    elif name.startswith("c9188"):
        return os.path.join(CD, "data", "c91887d861d9bd4a5872249b641bc9f9.exe_")
    else:
        raise ValueError("unexpected sample fixture")


def get_sample_md5_by_name(name):
    """used by IDA tests to ensure the correct IDB is loaded"""
    if name == "mimikatz":
        return "5f66b82558ca92e54e77f216ef4c066c"
    elif name == "kernel32":
        return "e80758cf485db142fca1ee03a34ead05"
    elif name == "kernel32-64":
        return "a8565440629ac87f6fef7d588fe3ff0f"
    elif name == "pma12-04":
        return "56bed8249e7c2982a90e54e1e55391a2"
    elif name == "pma21-01":
        return "c8403fb05244e23a7931c766409b5e22"
    elif name == "al-khaser x86":
        return "db648cd247281954344f1d810c6fd590"
    elif name.startswith("39c05"):
        return "b7841b9d5dc1f511a93cc7576672ec0c"
    elif name.startswith("499c2"):
        return "499c2a85f6e8142c3f48d4251c9c7cd6"
    elif name.startswith("9324d"):
        return "9324d1a8ae37a36ae560c37448c9705a"
    elif name.startswith("a1982"):
        return "a198216798ca38f280dc413f8c57f2c2"
    elif name.startswith("a933a"):
        return "a933a1a402775cfa94b6bee0963f4b46"
    elif name.startswith("bfb9b"):
        return "bfb9b5391a13d0afd787e87ab90f14f5"
    elif name.startswith("c9188"):
        return "c91887d861d9bd4a5872249b641bc9f9"
    else:
        raise ValueError("unexpected sample fixture")


def resolve_sample(sample):
    return get_data_path_by_name(sample)


@pytest.fixture
def sample(request):
    return resolve_sample(request.param)


def get_function(extractor, fva):
    for f in extractor.get_functions():
        if f.__int__() == fva:
            return f
    raise ValueError("function not found")


def get_basic_block(extractor, f, va):
    for bb in extractor.get_basic_blocks(f):
        if bb.__int__() == va:
            return bb
    raise ValueError("basic block not found")


def resolve_scope(scope):
    if scope == "file":

        def inner(extractor):
            return extract_file_features(extractor)

        inner.__name__ = scope
        return inner
    elif "bb=" in scope:
        # like `function=0x401000,bb=0x40100A`
        fspec, _, bbspec = scope.partition(",")
        fva = int(fspec.partition("=")[2], 0x10)
        bbva = int(bbspec.partition("=")[2], 0x10)

        def inner(extractor):
            f = get_function(extractor, fva)
            bb = get_basic_block(extractor, f, bbva)
            return extract_basic_block_features(extractor, f, bb)

        inner.__name__ = scope
        return inner
    elif scope.startswith("function"):
        # like `function=0x401000`
        va = int(scope.partition("=")[2], 0x10)

        def inner(extractor):
            f = get_function(extractor, va)
            return extract_function_features(extractor, f)

        inner.__name__ = scope
        return inner
    else:
        raise ValueError("unexpected scope fixture")


@pytest.fixture
def scope(request):
    return resolve_scope(request.param)


def make_test_id(values):
    return "-".join(map(str, values))


def parametrize(params, values, **kwargs):
    """
    extend `pytest.mark.parametrize` to pretty-print features.
    by default, it renders objects as an opaque value.
    ref: https://docs.pytest.org/en/2.9.0/example/parametrize.html#different-options-for-test-ids
    rendered ID might look something like:
        mimikatz-function=0x403BAC-api(CryptDestroyKey)-True
    """
    ids = list(map(make_test_id, values))
    return pytest.mark.parametrize(params, values, ids=ids, **kwargs)


FEATURE_PRESENCE_TESTS = [
    # file/characteristic("embedded pe")
    ("pma12-04", "file", capa.features.Characteristic("embedded pe"), True),
    # file/string
    ("mimikatz", "file", capa.features.String("SCardControl"), True),
    ("mimikatz", "file", capa.features.String("SCardTransmit"), True),
    ("mimikatz", "file", capa.features.String("ACR  > "), True),
    ("mimikatz", "file", capa.features.String("nope"), False),
    # file/sections
    ("mimikatz", "file", capa.features.file.Section(".text"), True),
    ("mimikatz", "file", capa.features.file.Section(".nope"), False),
    # IDA doesn't extract unmapped sections by default
    # ("mimikatz", "file", capa.features.file.Section(".rsrc"), True),
    # file/exports
    ("kernel32", "file", capa.features.file.Export("BaseThreadInitThunk"), True),
    ("kernel32", "file", capa.features.file.Export("lstrlenW"), True),
    ("kernel32", "file", capa.features.file.Export("nope"), False),
    # file/imports
    ("mimikatz", "file", capa.features.file.Import("advapi32.CryptSetHashParam"), True),
    ("mimikatz", "file", capa.features.file.Import("CryptSetHashParam"), True),
    ("mimikatz", "file", capa.features.file.Import("kernel32.IsWow64Process"), True),
    ("mimikatz", "file", capa.features.file.Import("msvcrt.exit"), True),
    ("mimikatz", "file", capa.features.file.Import("cabinet.#11"), True),
    ("mimikatz", "file", capa.features.file.Import("#11"), False),
    ("mimikatz", "file", capa.features.file.Import("#nope"), False),
    ("mimikatz", "file", capa.features.file.Import("nope"), False),
    # function/characteristic(loop)
    ("mimikatz", "function=0x401517", capa.features.Characteristic("loop"), True),
    ("mimikatz", "function=0x401000", capa.features.Characteristic("loop"), False),
    # bb/characteristic(tight loop)
    ("mimikatz", "function=0x402EC4", capa.features.Characteristic("tight loop"), True),
    ("mimikatz", "function=0x401000", capa.features.Characteristic("tight loop"), False),
    # bb/characteristic(stack string)
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("stack string"), True),
    ("mimikatz", "function=0x401000", capa.features.Characteristic("stack string"), False),
    # bb/characteristic(tight loop)
    ("mimikatz", "function=0x402EC4,bb=0x402F8E", capa.features.Characteristic("tight loop"), True),
    ("mimikatz", "function=0x401000,bb=0x401000", capa.features.Characteristic("tight loop"), False),
    # insn/mnemonic
    ("mimikatz", "function=0x40105D", capa.features.insn.Mnemonic("push"), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Mnemonic("movzx"), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Mnemonic("xor"), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Mnemonic("in"), False),
    ("mimikatz", "function=0x40105D", capa.features.insn.Mnemonic("out"), False),
    # insn/number
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0xFF), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0x3136B0), True),
    # insn/number: stack adjustments
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0xC), False),
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0x10), False),
    # insn/number: arch flavors
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0xFF), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0xFF, arch=ARCH_X32), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Number(0xFF, arch=ARCH_X64), False),
    # insn/offset
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x0), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x4), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0xC), True),
    # insn/offset: stack references
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x8), False),
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x10), False),
    # insn/offset: negative
    ("mimikatz", "function=0x4011FB", capa.features.insn.Offset(-0x1), True),
    ("mimikatz", "function=0x4011FB", capa.features.insn.Offset(-0x2), True),
    # insn/offset: arch flavors
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x0), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x0, arch=ARCH_X32), True),
    ("mimikatz", "function=0x40105D", capa.features.insn.Offset(0x0, arch=ARCH_X64), False),
    # insn/api
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("advapi32.CryptAcquireContextW"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("advapi32.CryptAcquireContext"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("advapi32.CryptGenKey"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("advapi32.CryptImportKey"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("advapi32.CryptDestroyKey"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("CryptAcquireContextW"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("CryptAcquireContext"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("CryptGenKey"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("CryptImportKey"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("CryptDestroyKey"), True),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("Nope"), False),
    ("mimikatz", "function=0x403BAC", capa.features.insn.API("advapi32.Nope"), False),
    # insn/api: thunk
    ("mimikatz", "function=0x4556E5", capa.features.insn.API("advapi32.LsaQueryInformationPolicy"), True),
    ("mimikatz", "function=0x4556E5", capa.features.insn.API("LsaQueryInformationPolicy"), True),
    # insn/api: x64
    ("kernel32-64", "function=0x180001010", capa.features.insn.API("RtlVirtualUnwind"), True,),
    ("kernel32-64", "function=0x180001010", capa.features.insn.API("RtlVirtualUnwind"), True),
    # insn/api: x64 thunk
    ("kernel32-64", "function=0x1800202B0", capa.features.insn.API("RtlCaptureContext"), True,),
    ("kernel32-64", "function=0x1800202B0", capa.features.insn.API("RtlCaptureContext"), True),
    # insn/api: resolve indirect calls
    ("c91887...", "function=0x401A77", capa.features.insn.API("kernel32.CreatePipe"), True),
    ("c91887...", "function=0x401A77", capa.features.insn.API("kernel32.SetHandleInformation"), True),
    ("c91887...", "function=0x401A77", capa.features.insn.API("kernel32.CloseHandle"), True),
    ("c91887...", "function=0x401A77", capa.features.insn.API("kernel32.WriteFile"), True),
    # insn/string
    ("mimikatz", "function=0x40105D", capa.features.String("SCardControl"), True),
    ("mimikatz", "function=0x40105D", capa.features.String("SCardTransmit"), True),
    ("mimikatz", "function=0x40105D", capa.features.String("ACR  > "), True),
    ("mimikatz", "function=0x40105D", capa.features.String("nope"), False),
    # insn/string, pointer to string
    ("mimikatz", "function=0x44EDEF", capa.features.String("INPUTEVENT"), True),
    # insn/bytes
    ("mimikatz", "function=0x40105D", capa.features.Bytes("SCardControl".encode("utf-16le")), True),
    ("mimikatz", "function=0x40105D", capa.features.Bytes("SCardTransmit".encode("utf-16le")), True),
    ("mimikatz", "function=0x40105D", capa.features.Bytes("ACR  > ".encode("utf-16le")), True),
    ("mimikatz", "function=0x40105D", capa.features.Bytes("nope".encode("ascii")), False),
    # insn/bytes, pointer to bytes
    ("mimikatz", "function=0x44EDEF", capa.features.Bytes("INPUTEVENT".encode("utf-16le")), True),
    # insn/characteristic(nzxor)
    ("mimikatz", "function=0x410DFC", capa.features.Characteristic("nzxor"), True),
    ("mimikatz", "function=0x40105D", capa.features.Characteristic("nzxor"), False),
    # insn/characteristic(nzxor): no security cookies
    ("mimikatz", "function=0x46D534", capa.features.Characteristic("nzxor"), False),
    # insn/characteristic(peb access)
    ("kernel32-64", "function=0x1800017D0", capa.features.Characteristic("peb access"), True),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("peb access"), False),
    # insn/characteristic(gs access)
    ("kernel32-64", "function=0x180001068", capa.features.Characteristic("gs access"), True),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("gs access"), False),
    # insn/characteristic(cross section flow)
    ("a1982...", "function=0x4014D0", capa.features.Characteristic("cross section flow"), True),
    # insn/characteristic(cross section flow): imports don't count
    ("kernel32-64", "function=0x180001068", capa.features.Characteristic("cross section flow"), False),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("cross section flow"), False),
    # insn/characteristic(recursive call)
    ("39c05...", "function=0x10003100", capa.features.Characteristic("recursive call"), True),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("recursive call"), False),
    # insn/characteristic(indirect call)
    ("mimikatz", "function=0x4175FF", capa.features.Characteristic("indirect call"), True),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("indirect call"), False),
    # insn/characteristic(calls from)
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("calls from"), True),
    ("mimikatz", "function=0x4702FD", capa.features.Characteristic("calls from"), False),
    # function/characteristic(calls to)
    ("mimikatz", "function=0x40105D", capa.features.Characteristic("calls to"), True),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("calls to"), False),
]

FEATURE_COUNT_TESTS = [
    ("mimikatz", "function=0x40E5C2", capa.features.basicblock.BasicBlock(), 7),
    ("mimikatz", "function=0x4702FD", capa.features.Characteristic("calls from"), 0),
    ("mimikatz", "function=0x40E5C2", capa.features.Characteristic("calls from"), 3),
    ("mimikatz", "function=0x4556E5", capa.features.Characteristic("calls to"), 0),
    ("mimikatz", "function=0x40B1F1", capa.features.Characteristic("calls to"), 3),
]


def do_test_feature_presence(get_extractor, sample, scope, feature, expected):
    extractor = get_extractor(sample)
    features = scope(extractor)
    if expected:
        msg = "%s should be found in %s" % (str(feature), scope.__name__)
    else:
        msg = "%s should not be found in %s" % (str(feature), scope.__name__)
    assert feature.evaluate(features) == expected, msg


def do_test_feature_count(get_extractor, sample, scope, feature, expected):
    extractor = get_extractor(sample)
    features = scope(extractor)
    msg = "%s should be found %d times in %s, found: %d" % (
        str(feature),
        expected,
        scope.__name__,
        len(features[feature]),
    )
    assert len(features[feature]) == expected, msg


def get_extractor(path):
    if sys.version_info >= (3, 0):
        raise RuntimeError("no supported py3 backends yet")
    else:
        extractor = get_viv_extractor(path)

    # overload the extractor so that the fixture exposes `extractor.path`
    setattr(extractor, "path", path)
    return extractor


@pytest.fixture
def mimikatz_extractor():
    return get_extractor(get_data_path_by_name("mimikatz"))


@pytest.fixture
def a933a_extractor():
    return get_extractor(get_data_path_by_name("a933a..."))


@pytest.fixture
def kernel32_extractor():
    return get_extractor(get_data_path_by_name("kernel32"))


@pytest.fixture
def a1982_extractor():
    return get_extractor(get_data_path_by_name("a1982..."))


@pytest.fixture
def z9324d_extractor():
    return get_extractor(get_data_path_by_name("9324d..."))


@pytest.fixture
def pma12_04_extractor():
    return get_extractor(get_data_path_by_name("pma12-04"))


@pytest.fixture
def bfb9b_extractor():
    return get_extractor(get_data_path_by_name("bfb9b..."))


@pytest.fixture
def pma21_01_extractor():
    return get_extractor(get_data_path_by_name("pma21-01"))


@pytest.fixture
def c9188_extractor():
    return get_extractor(get_data_path_by_name("c9188..."))


@pytest.fixture
def z39c05_extractor():
    return get_extractor(get_data_path_by_name("39c05..."))


@pytest.fixture
def z499c2_extractor():
    return get_extractor(get_data_path_by_name("499c2..."))


@pytest.fixture
def al_khaser_x86_extractor():
    return get_extractor(get_data_path_by_name("al-khaser x86"))
