#! /usr/bin/env python3
""" Testcases for strip-python3 transformation and execution with different python versions """

# pylint: disable=line-too-long,too-many-lines,bare-except,broad-exception-caught,pointless-statement,multiple-statements,f-string-without-interpolation,import-outside-toplevel
# pylint: disable=missing-class-docstring,missing-function-docstring,unused-variable,unused-argument,unspecified-encoding,redefined-outer-name,using-constant-test,invalid-name
# pylint: disable=fixme,duplicate-code,consider-using-with,too-many-public-methods,too-many-arguments,too-many-positional-arguments
__copyright__ = "(C) Guido Draheim, licensed under the MIT license"""
__version__ = "1.1.1124"


from typing import List, Iterator, Union, Optional, TextIO, Mapping, Iterable

import subprocess
import os
import os.path
import time
import datetime
import unittest
import shutil
import inspect
import logging
import re
import sys
from fnmatch import fnmatchcase as fnmatch

string_types = (str, bytes)

NIX = ""
OK = True
logg = logging.getLogger("EXECS")
_sed = "sed"
DOCKER = "docker"
KEEP = False
SOMETIME = 222
TODO = False
DOCKER_SOCKET = "/var/run/docker.sock"
IMAGES = "localhost:5000/strip3/testing"
COVERAGE = False
IMAGE= "ubuntu:22.04"
PYTHON="python3"
PYTHON3="python3.9"
MYPY=""
STRIP="src/strip_python3.py"
VV="-vv"

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")

def decodes(text: Union[str, bytes, None]) -> str:
    if text is None: return ""
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except UnicodeDecodeError:
            return text.decode("latin-1")
    return text
def q_str(part: Union[str, int, None]) -> str:
    if part is None:
        return ""
    if isinstance(part, int):
        return str(part)
    return "'%s'" % part  # pylint: disable=consider-using-f-string
def sh____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.call(cmd, shell=shell)

class CalledProcessError(subprocess.SubprocessError):
    def __init__(self, args: Union[str, List[str]], returncode: int = 0, stdout: Union[str,bytes] = NIX, stderr: Union[str,bytes] = NIX) -> None:
        self.cmd = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.output = self.stdout
class CompletedProcess:
    def __init__(self, args: Union[str, List[str]], returncode: int = 0, stdout: Union[str,bytes] = NIX, stderr: Union[str,bytes] = NIX) -> None:
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
    def check_returncode(self) -> None:
        if self.returncode:
            raise CalledProcessError(self.args, self.returncode, self.stdout, self.stderr)
    @property
    def err(self) -> str:
        return decodes(self.stderr).rstrip()
    @property
    def out(self) -> str:
        return decodes(self.stdout).rstrip()

def X(args: Union[str, List[str]], stdin: Optional[int]=None, inputs: Optional[bytes]=None, stdout: Optional[int]=None, stderr: Optional[int]=None,
    shell: Optional[bool]=None, cwd: Optional[str]=None, timeout: Optional[int]=None, check: bool=False, env: Optional[Mapping[bytes, str]]=None) -> CompletedProcess:
    """ a variant of subprocess.run() """
    shell = isinstance(args, str) if shell is None else shell
    stdout = subprocess.PIPE if stdout is None else stdout
    stderr = subprocess.PIPE if stderr is None else stderr
    proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
    try:
        outs, errs = proc.communicate(input=inputs, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    completed = CompletedProcess(args, proc.returncode, outs, errs)
    if check:
        completed.check_returncode()
    return completed


def reads(filename: str) -> str:
    return decodes(open(filename, "rb").read())
def _lines4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    if isinstance(textlines, string_types):
        linelist = decodes(textlines).split("\n")
        if len(linelist) and linelist[-1] == "":
            linelist = linelist[:-1]
        return linelist
    return list(textlines)
def lines4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    linelist = []
    for line in _lines4(textlines):
        linelist.append(line.rstrip())
    return linelist
def each_grep(patterns: Iterable[str], textlines: Union[str, List[str], TextIO]) -> Iterator[str]:
    for line in _lines4(textlines):
        for pattern in patterns:
            if re.search(pattern, line.rstrip()):
                yield line.rstrip()
def grep(pattern: str, textlines: Union[str, List[str], TextIO]) -> List[str]:
    return list(each_grep([pattern], textlines))
def greps(textlines: Union[str, List[str], TextIO], *pattern: str) -> List[str]:
    return list(each_grep(pattern, textlines))

def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
    logg.info("::: made %s", filename)
def shell_file(filename: str, content: str) -> None:
    text_file(filename, content)
    os.chmod(filename, 0o775)

def get_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back  # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]

def detect_local_system() -> str:
    """ checks the controller host (a real machine / your laptop)
        and returns a matching image name for it (docker style) """
    docker = DOCKER
    mirror = _mirror
    cmd = F"{mirror} detect"
    run = X(cmd)
    return decodes(run.stdout).strip()

def packages_refresh_tool() -> str:
    return "apt-get -o Acquire::AllowInsecureRepositories=true update"

def packages_search_tool() -> str:
    return "apt-cache -o Acquire::AllowInsecureRepositories=true search"

def package_tool() -> str:
    return "apt-get -o Acquire::AllowInsecureRepositories=true"


############ the real testsuite ##############

class StripPythonExecTest(unittest.TestCase):
    """ testcases for strip-python3.py """
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str] = None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testdir(self, testname: Optional[str] = None, keep: bool = False) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir) and not keep:
            shutil.rmtree(newdir)
        if not os.path.isdir(newdir):
            os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            if not KEEP:
                shutil.rmtree(newdir)
        return newdir
    def rm_docker(self, testname: str) -> None:
        docker = DOCKER
        if not KEEP:
            sx____(F"{docker} stop -t 6 {testname}")
            sx____(F"{docker} rm -f {testname}")
    def coverage(self, testname: Optional[str] = None) -> None:
        testname = testname or self.caller_testname()
        newcoverage = ".coverage."+testname
        time.sleep(1)
        if os.path.isfile(".coverage"):
            # shutil.copy(".coverage", newcoverage)
            with open(".coverage", "rb") as inp:
                text = inp.read()
            text2 = re.sub(rb"(\]\}\})[^{}]*(\]\}\})$", rb"\1", text)
            with open(newcoverage, "wb") as out:
                out.write(text2)
    def begin(self) -> str:
        self._started = time.monotonic() # pylint: disable=attribute-defined-outside-init
        logg.info("[[%s]]", datetime.datetime.fromtimestamp(self._started).strftime("%H:%M:%S"))
        return VV
    def end(self, maximum: int = 99) -> None:
        runtime = time.monotonic() - self._started
        self.assertLess(runtime, maximum)
    def test_1001(self) -> None:
        """ check that we can run python"""
        python = PYTHON
        python3 = PYTHON3
        testdir = self.testdir()
        sh____(F"{python} --version")
        self.rm_testdir()
    def test_1101(self) -> None:
        """ check that we can run python"""
        vv = self.begin()
        python = PYTHON
        python3 = PYTHON3
        testdir = self.testdir()
        text_file(F"{testdir}/test3.py", """
        class A:
           a: int
           b: str
           def __init(a: int, b:str) -> None:
              self.a = a
              self.b = b
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {testdir}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{testdir}/test.py"))
        self.assertTrue(os.path.exists(F"{testdir}/test.pyi"))
        text_file(F"{testdir}/test4.py", """
        import test
        x = test.A()
        x.b = 22
        print(x.b)
        """)
        x1 = X(F"{python} {testdir}/test4.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "22")
        if MYPY:
            x2 = X(F"{MYPY} --strict {testdir}/test4.py")
            logg.info("%s -> %s\n%s", x2.args, x2.out, x2.err)
            self.assertTrue(greps(x2.out, "Incompatible types in assignment"))
            self.assertEqual(x2.returncode, 1)
            self.rm_testdir()
    def test_1102(self) -> None:
        """ check that we can run python"""
        vv = self.begin()
        python = PYTHON
        python3 = PYTHON3
        testdir = self.testdir()
        text_file(F"{testdir}/test3.py", """
        class A:
           a: int
           b: str
           def __init(self, a: int, b:str) -> None:
              self.a = a
              self.b = b
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {testdir}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{testdir}/test.py"))
        self.assertTrue(os.path.exists(F"{testdir}/test.pyi"))
        text_file(F"{testdir}/test4.py", """
        import test
        x = test.A()
        x.a = 22
        print(x.a)
        """)
        x1 = X(F"{python} {testdir}/test4.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "22")
        if MYPY:
            x2 = X(F"{MYPY} --strict {testdir}/test4.py")
            logg.info("%s -> %s\n%s", x2.args, x2.out, x2.err)
            self.assertTrue(greps(x2.out, "no issues found"))
            self.assertEqual(x2.returncode, 0)
    def test_1331(self) -> None:
        """ check that we can print() in python"""
        vv = self.begin()
        python = PYTHON
        testdir = self.testdir()
        text_file(F"{testdir}/test3.py", """
        print("hello world")
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {testdir}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{testdir}/test.py"))
        self.assertTrue(os.path.exists(F"{testdir}/test.pyi"))
        script = lines4(open(F"{testdir}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, " print_function"))
        x1 = X(F"{python} {testdir}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "hello world")
        if MYPY:
            x2 = X(F"{MYPY} --strict {testdir}/test.py")
            logg.info("%s -> %s\n%s", x2.args, x2.out, x2.err)
            self.assertEqual(x2.out, "Success: no issues found in 1 source file")
        self.rm_testdir()
        self.end()
    def test_1341(self) -> None:
        """ check that we have float-division in python"""
        vv = self.begin()
        python = PYTHON
        testdir = self.testdir()
        text_file(F"{testdir}/test3.py", """
        x = 5
        print(5 / 2)
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {testdir}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{testdir}/test.py"))
        self.assertTrue(os.path.exists(F"{testdir}/test.pyi"))
        script = lines4(open(F"{testdir}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, " division"))
        x1 = X(F"{python} {testdir}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        if MYPY:
            x2 = X(F"{MYPY} --strict {testdir}/test.py")
            logg.info("%s -> %s\n%s", x2.args, x2.out, x2.err)
            self.assertEqual(x2.out, "Success: no issues found in 1 source file")
        self.rm_testdir()
        self.end()
    def test_1351(self) -> None:
        """ check that we have absolute-import in python"""
        vv = self.begin()
        python = PYTHON
        testdir = self.testdir()
        text_file(F"{testdir}/__init__.py","""
        """)
        text_file(F"{testdir}/main.py","""
        import test
        """)
        text_file(F"{testdir}/errno.py","""
        ENOENT = 0
        """)
        text_file(F"{testdir}/test3.py", """
        import sys
        print("=>", __name__)
        from .errno import ENOENT as err1
        from errno import ENOENT as err2
        print("OK")
        print("%i + %i" % (err1, err2))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {testdir}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{testdir}/test.py"))
        self.assertTrue(os.path.exists(F"{testdir}/test.pyi"))
        script = lines4(open(F"{testdir}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, " absolute_import"))
        # x1 = X(F"{python} {testdir}/main.py")
        x1 = X(F"{python} -m main", env={b"PYTHONPATH": testdir})
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "=> test") # TODO
        if MYPY:
            text_file(F"{testdir}/test4.py", """
            import test""")
            x2 = X(F"{MYPY} --strict {testdir}/test4.py")
            logg.info("%s -> %s\n%s", x2.args, x2.out, x2.err)
            self.assertTrue(greps(x2.err, "is not a valid Python package name"))
        self.rm_testdir()
        self.end()
    def test_1401(self) -> None:
        """ check that we have boilerplate for datetime.isoformat"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        from datetime import datetime
        def func1(x: str) -> datetime:
            return datetime.fromisoformat(x)
        print(func1("2024-12-01").strftime("%Y%m%dx"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        self.assertTrue(os.path.exists(F"{tmp}/test.pyi"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        types = lines4(open(F"{tmp}/test.pyi").read())
        logg.info("types = %s", types)

        self.assertTrue(greps(script, "def datetime_fromisoformat"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "20241201x")
        if MYPY:
            text_file(F"{tmp}/test4.py", """
            import test""")
            x2 = X(F"{MYPY} --strict {tmp}/test4.py")
            logg.info("%s -> %s\n%s", x2.args, x2.out, x2.err)
            self.assertEqual(x2.out, "Success: no issues found in 1 source file")
        self.rm_testdir()
        self.end()
    def test_1402(self) -> None:
        """ check that we have boilerplate for datetime.isoformat"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        from datetime import datetime as Time
        def func1(x: x) -> datetime:
            return Time.fromisoformat(x)
        print(func1("2024-12-01").strftime("%Y%m%dx"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "def Time_fromisoformat"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "20241201x")
        self.rm_testdir()
        self.end()
    def test_1411(self) -> None:
        """ check we have boilerplate for subprocess.run"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        shell_file(F"{tmp}/run.sh", """
        #! /bin/sh
        echo "okay"
        """)
        text_file(F"{tmp}/test3.py", F"""
        import subprocess
        def strb(x): return x.decode('utf-8') if isinstance(x, bytes) else str(x)
        def func1() -> str:
            return subprocess.run("{tmp}/run.sh", stdout=subprocess.PIPE).stdout
        print(strb(func1()).replace("o","uh"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "def subprocess_run"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "uhkay")
        self.rm_testdir()
        self.end()
    def test_1412(self) -> None:
        """ check we have boilerplate for subprocess.run"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        shell_file(F"{tmp}/run.sh", """
        #! /bin/sh
        echo "okay"
        """)
        text_file(F"{tmp}/test3.py", F"""
        import subprocess as sp
        def strb(x): return x.decode('utf-8') if isinstance(x, bytes) else str(x)
        def func1() -> str:
            return sp.run("{tmp}/run.sh", stdout=sp.PIPE).stdout
        print(strb(func1()).replace("o","uh"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "def sp_run"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "uhkay")
        self.assertFalse(greps(script, "timeout=timeout"))
        self.rm_testdir()
        self.end()
    def test_1413(self) -> None:
        """ check we have boilerplate for subprocess.run"""
        vv = self.begin()
        python = PYTHON
        if "python2" in python:
            self.skipTest("checking atleast python3.3")
        tmp = self.testdir()
        shell_file(F"{tmp}/run.sh", """
        #! /bin/sh
        echo "okay"
        """)
        text_file(F"{tmp}/test3.py", F"""
        import subprocess as sp
        def strb(x): return x.decode('utf-8') if isinstance(x, bytes) else str(x)
        def func1() -> str:
            return sp.run("{tmp}/run.sh", stdout=sp.PIPE).stdout
        print(strb(func1()).replace("o","uh"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv} --python-version=3.3")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "def sp_run"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertEqual(x1.out, "uhkay")
        self.assertTrue(greps(script, "timeout=timeout"))
        self.rm_testdir()
        self.end()
    def test_1421(self) -> None:
        """ check we have a fallback import for pathlib"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import pathlib
        def func1(x: str) -> pathlib.PurePath:
            return pathlib.PurePath(x)
        print(func1("c://a"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "pathlib2 as pathlib"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out + x1.err, "No module named pathlib2", "c:/a"))
        self.rm_testdir()
        self.end()
    def test_1422(self) -> None:
        """ check we have a fallback import for pathlib"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import pathlib as pt
        def func1(x: str) -> pt.PurePath:
            return pt.PurePath(x)
        print(func1("c://a"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "pathlib2 as pt"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out + x1.err, "No module named pathlib2", "c:/a"))
        self.rm_testdir()
        self.end()
    def test_1431(self) -> None:
        """ check we have a fallback import for tomllib"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import tomllib
        def func1(x: str) -> Dict[str, Any]:
            return tomllib.loads(x)
        print(func1("[section]\\nvalue = 1"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "toml as tomllib"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out + x1.err, "No module named toml", "No module named 'toml'", "{'section': {'value': 1}}"))
        self.rm_testdir()
        self.end()
    def test_1432(self) -> None:
        """ check we have a fallback import for tomllib"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import tomllib as tm
        def func1(x: str) -> Dict[str, Any]:
            return tm.loads(x)
        print(func1("[section]\\nvalue = 1"))
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "toml as tm"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out + x1.err, "No module named toml", "No module named 'toml'", "{'section': {'value': 1}}"))
        self.rm_testdir()
        self.end()
    def test_1441(self) -> None:
        """ check we have a fallback import for zoneinfo"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import zoneinfo
        def func1() -> List[str]:
            return zoneinfo.available_timezones()
        print(func1())
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "from backports import zoneinfo"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out + x1.err, "No module named backports", "No module named 'backports'", "Europe/Berlin"))
        self.rm_testdir()
        self.end()
    def test_1451(self) -> None:
        """ check we have a fallback for time.monotonic"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import time
        def func1() -> int:
            started = time.monotonic()
            time.sleep(0.8)
            stopped = time.monotonic()
            return stopped-started
        print(func1())
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "def time_monotonic"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out, "0.80", "0.81"))
        self.rm_testdir()
        self.end()
    def test_1452(self) -> None:
        """ check we have a fallback for time.monotonic_ns"""
        vv = self.begin()
        python = PYTHON
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import time
        def func1() -> int:
            started = time.monotonic_ns()
            time.sleep(0.8)
            stopped = time.monotonic_ns()
            return stopped-started
        print("X", func1())
        """)
        sh____(F"{PYTHON3} {STRIP} -3 {tmp}/test3.py {vv}")
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        script = lines4(open(F"{tmp}/test.py").read())
        logg.info("script = %s", script)
        self.assertTrue(greps(script, "def time_monotonic_ns"))
        x1 = X(F"{python} {tmp}/test.py")
        logg.info("%s -> %s\n%s", x1.args, x1.out, x1.err)
        self.assertTrue(greps(x1.out, "X 80", "X 81"))
        self.rm_testdir()
        self.end()


if __name__ == "__main__":
    from optparse import OptionParser  # pylint: disable=deprecated-module
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("-D", "--docker", metavar="EXE", default=DOCKER,
                  help="use another docker container tool [%default]")
    _o.add_option("-P", "--python3", metavar="EXE", default=PYTHON3,
                  help="use another python3 engine [%default]")
    _o.add_option("-p", "--python", metavar="EXE", default=PYTHON,
                  help="use another python engine [%default]")
    _o.add_option("--mypy", metavar="EXE", default=MYPY, help="mypy tool is available")
    _o.add_option("-a", "--coverage", action="count", default=0,
                  help="gather coverage.py data (use -aa for new set) [%default]")
    _o.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    _o.add_option("--keep", action="count", default=KEEP,
                  help="keep tempdir and other data after testcase [%default]")
    _o.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    _o.add_option("--sometime", metavar="SECONDS", default=SOMETIME,
                  help="SOMETIME=%default (use 666)")
    _o.add_option("--todo", action="store_true", default=TODO,
                  help="enable TODO outtakes [%default])")
    _o.add_option("-f", "--force", action="store_true", default=False,
                  help="enable the skipped IMAGE and PYTHON versions [%default])")
    _o.add_option("-C", "--chdir", metavar="PATH", default="",
                  help="change directory before running tests {%default}")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    SKIP = not opt.force
    TODO = opt.todo
    KEEP = opt.keep
    DOCKER = opt.docker
    PYTHON = opt.python
    PYTHON3 = opt.python3
    MYPY = opt.mypy
    VV = "-v" + ("v" * opt.verbose)
    #
    if opt.chdir:
        os.chdir(opt.chdir)
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    #
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = ["test_*"]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if arg.endswith("/"):
                    arg = arg[:-1]
                if "*" not in arg:
                    arg += "*"
                if len(arg) > 2 and arg[1] == "_":
                    arg = "test" + arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    if not logfile:
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore
    if not testresult.wasSuccessful():
        sys.exit(1)
