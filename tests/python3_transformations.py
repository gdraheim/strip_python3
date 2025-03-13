#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,invalid-name,line-too-long,multiple-statements,too-many-lines
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-public-methods,too-many-branches,too-many-statements,consider-using-with,no-else-return,unspecified-encoding
""" tests for strip_python3 """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "0.9.1104"

from typing import List, Union, Optional, Iterator, Iterable, NamedTuple
import unittest
from fnmatch import fnmatchcase as fnmatch
import inspect
import re
import os
import sys
import subprocess
import shutil
import datetime
import time
import logging

NOTE = (logging.INFO + logging.WARNING) // 2
HINT = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(HINT, "HINT")

DEBUG_TOML = logging.DEBUG

logg = logging.getLogger(__name__.replace("/", "."))
STRIP = "src/strip_python3.py"
PYTHON = "python3.11"
COVERAGE = 0
KEEP = 0
OK = True
NIX = ""
LONGER = 2
ENDSLEEP = 0.1
FIXCOVERAGE = True
RMCOVERAGE = True

basestring = str

def get_caller_name() -> str:
    currentframe = inspect.currentframe()
    if currentframe is None:
        return "global"
    if currentframe.f_back is None:
        return "global"
    if currentframe.f_back.f_back is None:
        return "global"
    frame = currentframe.f_back.f_back
    return frame.f_code.co_name
def get_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if currentframe is None:
        return "global"
    if currentframe.f_back is None:
        return "global"
    if currentframe.f_back.f_back is None:
        return "global"
    if currentframe.f_back.f_back.f_back is None:
        return "global"
    frame = currentframe.f_back.f_back.f_back
    return frame.f_code.co_name
def get_caller_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if currentframe is None:
        return "global"
    if currentframe.f_back is None:
        return "global"
    if currentframe.f_back.f_back is None:
        return "global"
    if currentframe.f_back.f_back.f_back is None:
        return "global"
    if currentframe.f_back.f_back.f_back.f_back is None:
        return "global"
    frame = currentframe.f_back.f_back.f_back.f_back
    return frame.f_code.co_name

def decodes(text: Union[None, bytes, str]) -> Optional[str]:
    if text is None: return None
    return decodes_(text)
def decodes_(text: Union[bytes, str]) -> Optional[str]:
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except:  # pylint: disable=bare-except
            return text.decode("latin-1")
    return text

def _lines(lines: Union[str, Iterable[str]]) -> Iterable[str]:
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
        return lines
    return lines
def lines4(text: Union[str, Iterable[str]]) -> List[str]:
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def _grep(pattern: str, lines: Union[str, Iterable[str]]) -> Iterator[str]:
    for line in _lines(lines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def grep(pattern: str, lines: Union[str, Iterable[str]]) -> List[str]:
    return list(_grep(pattern, lines))
def greps(lines: Union[str, List[str]], pattern: str) -> List[str]:
    return list(_grep(pattern, lines))

def text4(content: str) -> str:
    if content.startswith("\n"):
        text = ""
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                if not line.strip():
                    line = ""
                else:
                    line = line[len(indent):]
            text += line + "\n"
        if text.endswith("\n\n"):
            return text[:-1]
        else:
            return text
    else:
        return content

def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if filedir not in ["", "."] and not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w", encoding="utf-8")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line + "\n")
    else:
        f.write(content)
    f.close()
def file_text4(filename: str, delim: str = "\n") -> str:
    return file_text(filename, delim)
def file_text(filename: str, delim: str = "^") -> str:
    if os.path.isfile(filename):
        with open(filename, encoding="utf-8") as f:
            text = f.read()
            return text.replace("\n", delim)
    return NIX

class ShellResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str
    @property
    def err(self) -> str:
        return self.stderr.rstrip()
    @property
    def out(self) -> str:
        return self.stdout.rstrip()
    @property
    def ret(self) -> int:
        return self.returncode
class ShellException(Exception):
    def __init__(self, msg: str, result: ShellResult) -> None:
        Exception.__init__(self, msg)
        self.result = result
def sh(cmd: str, shell: bool = True, check: bool = True, ok: Optional[bool] = None, default: str = "", cwd: Optional[str] = None) -> ShellResult:
    if ok is None: ok = OK  # a parameter "ok = OK" does not work in python
    if not ok:
        logg.info("skip %s", cmd)
        return ShellResult(0, default or "", "")
    cwdir = cwd if cwd is None else os.path.abspath(cwd)
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = cwdir)
    run.wait()
    assert run.stdout is not None and run.stderr is not None
    result = ShellResult(run.returncode, decodes_(run.stdout.read()) or "", decodes_(run.stderr.read()) or "")
    if check and result.returncode:
        logg.error("CMD %s", cmd)
        logg.error("EXIT %s", result.returncode)
        logg.error("STDOUT %s", result.stdout)
        logg.error("STDERR %s", result.stderr)
        raise ShellException("shell command failed", result)
    return result

def coverage(tool: str, cwd: Optional[str] = None) -> str:
    pre = ""
    if cwd:
        subdir = cwd if cwd.endswith("/") else cwd + "/"
        pre = "../" * (subdir.count("/"))
    if COVERAGE:
        return PYTHON + " -m coverage " + " run " + pre + tool
    return PYTHON + " " + pre + tool

class StripTest(unittest.TestCase):
    "all tests should start with '0'."
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
    def testdir(self, testname: Optional[str] = None, keep: Optional[bool] = None) -> str:
        keeps = KEEP if keep is None else keep
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir) and not keeps:
            logg.log(DEBUG_TOML, "testdir rmtree %s", newdir)
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
    def coverage(self, testname: Optional[str] = None) -> None:
        testname = testname or self.caller_testname()
        testdir = self.testdir(testname, keep=True)
        time.sleep(ENDSLEEP)
        written = []
        if os.path.isfile(".coverage"):
            logg.log(DEBUG_TOML, "%s: found %s", testname, ".coverage")
            newcoverage = ".coverage."+testname
            # shutil.copy(".coverage", newcoverage)
            with open(".coverage", "rb") as inp:
                text = inp.read()
            if FIXCOVERAGE:
                text2 = re.sub(rb"(\]\}\})[^{}]*(\]\}\})$", rb"\1", text)
            else:
                text2 = text
            with open(newcoverage, "wb") as out:
                out.write(text2)
                written.append(newcoverage)
            if RMCOVERAGE:
                os.unlink(".coverage")
        if os.path.isfile(F"{testdir}/.coverage"):
            logg.log(DEBUG_TOML, "%s: found %s", testname, F"{testdir}/.coverage")
            newcoverage = ".coverage."+testname+".testdir"
            with open(F"{testdir}/.coverage", "rb") as inp:
                text = inp.read()
            if FIXCOVERAGE:
                text2 = re.sub(rb"(\]\}\})[^{}]*(\]\}\})$", rb"\1", text)
            else:
                text2 = text
            with open(newcoverage, "wb") as out:
                out.write(text2)
                written.append(newcoverage)
            if RMCOVERAGE:
                os.unlink(F"{testdir}/.coverage")
        logg.log(DEBUG_TOML, "coverage written %s", written)
    def begin(self) -> str:
        self._started = time.monotonic() # pylint: disable=attribute-defined-outside-init
        logg.debug("[[%s]]", datetime.datetime.fromtimestamp(self._started).strftime("%H:%M:%S"))
        return "-vv"
    def end(self, maximum: int = 99) -> None:
        runtime = time.monotonic() - self._started
        self.assertLess(runtime, maximum * LONGER)
    # all tests should start with '0'.
    def test_0000(self) -> None:
        if os.path.isfile(".coverage"):
            os.unlink(".coverage")
    def test_0011(self) -> None:
        strip = coverage(STRIP)
        run = sh(F"{strip} --help")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertFalse(run.err)
        self.assertTrue(greps(run.out, "this help message"))
        self.rm_testdir()
    def test_0021(self) -> None:
        strip = coverage(STRIP)
        run = sh(F"{strip} --show")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(lines4(run.stderr), lines4(text4("""
        NOTE:strip:python-version-int = (2, 7)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 1
        NOTE:strip:define-range = 1
        NOTE:strip:define-callable = 1
        NOTE:strip:define-print-function = 1
        NOTE:strip:define-float-division = 1
        NOTE:strip:define-absolute-import = 1
        NOTE:strip:replace-fstring = 1
        NOTE:strip:remove-keywordsonly = 1
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 1
        """)))
        self.rm_testdir()
    def test_0022(self) -> None:
        strip = coverage(STRIP)
        run = sh(F"{strip} --show --py36")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 6)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 0
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 0
        NOTE:strip:remove-typehints = 0
        """))
        self.rm_testdir()
    def test_0024(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/pyproject.toml", """
        [tool.strip-python3]
        python-version = "3.6"
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 6)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 0
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 0
        NOTE:strip:remove-typehints = 0
        """))
        self.rm_testdir()
    def test_0025(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/pyproject.toml", """
        [tool.strip-python3]
        python-version = "3.5"
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 1
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 0
        """))
        self.rm_testdir()
    def test_0026(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/pyproject.toml", """
        [tool.strip-python3]
        python-version = "3.5"
        remove-typehints = 1
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 1
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 1
        """))
        self.rm_testdir()
    def test_0027(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/pyproject.toml", """
        [tool.strip-python3]
        python-version = "3.5"
        no-replace-fstring = 1
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 0
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 0
        """))
        self.coverage()
        self.rm_testdir()
    def test_0028(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/pyproject.toml", """
        [tool.strip-python3]
        python-version = "3.5"
        pyi-version = 35
        no-replace-fstring = 1
        define-callable = 0
        define-range = 1
        define-basestring = 1979-05-27T07:32:00Z
        define-unknown = 1
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(lines4(run.stderr), lines4(text4("""
        pyproject.toml[pyi-version]: expecting str but found <class 'int'>
        pyproject.toml[define-basestring]: expecting int but found <class 'datetime.datetime'>
        pyproject.toml[define-unknown]: unknown setting found
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 1
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 0
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 0
        """)))
        self.rm_testdir()
    def test_0034(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/setup.cfg", """
        [strip-python3]
        python-version = 3.6
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 6)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 0
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 0
        NOTE:strip:remove-typehints = 0
        """))
        self.rm_testdir()
    def test_0035(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/setup.cfg", """
        [strip-python3]
        python-version = 3.5
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 1
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 0
        """))
        self.rm_testdir()
    def test_0036(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/setup.cfg", """
        [strip-python3]
        python-version = 3.5
        remove-typehints = 1
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(run.stderr, text4("""
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 0
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 1
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 1
        """))
        self.rm_testdir()
    def test_0038(self) -> None:
        tmp = self.testdir()
        strip = coverage(STRIP, tmp)
        text_file(F"{tmp}/setup.cfg", """
        [strip-python3]
        python-version = 3.5
        no-replace-fstring = 1
        define-callable = 0
        define-range = 1
        define-basestring = unknown
        define-unknown = 1
        """)
        run = sh(F"{strip} --show", cwd=tmp)
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.coverage()
        self.assertEqual(lines4(run.stderr), lines4(text4("""
        setup.cfg[define-basestring]: expecting int but found unknown
        setup.cfg[define-unknown]: unknown setting found
        NOTE:strip:python-version-int = (3, 5)
        NOTE:strip:pyi-version-int = (3, 6)
        NOTE:strip:define-basestring = 0
        NOTE:strip:define-range = 1
        NOTE:strip:define-callable = 0
        NOTE:strip:define-print-function = 0
        NOTE:strip:define-float-division = 0
        NOTE:strip:define-absolute-import = 0
        NOTE:strip:replace-fstring = 0
        NOTE:strip:remove-keywordsonly = 0
        NOTE:strip:remove-positionalonly = 1
        NOTE:strip:remove-pyi-positionalonly = 1
        NOTE:strip:remove-var-typehints = 1
        NOTE:strip:remove-typehints = 0
        """)))
        self.rm_testdir()
    def test_0101(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """a: int = 1""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "a = 1^")
        self.assertEqual(pyi, "a: int^")
        self.coverage()
        self.rm_testdir()
    def test_0102(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """a: int = 1 # foo""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "a = 1  # foo^")
        self.assertEqual(pyi, "a: int^")
        self.coverage()
        self.rm_testdir()
    def test_0103(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """a: int""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "")
        self.assertEqual(pyi, "a: int^")
        self.coverage()
        self.rm_testdir()
    def test_0104(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int
        b: int = 2""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "b = 2^")
        self.assertEqual(pyi, "a: int^b: int^")
        self.coverage()
        self.rm_testdir()
    def test_0105(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int # foo
        b: int = 2
        c: str """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "  # foo^b = 2^")
        self.assertEqual(pyi, "a: int^b: int^c: str^")
        self.coverage()
        self.rm_testdir()
    def test_0106(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        # foo
        b: int = 2
        c: str # bar""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "# foo^b = 2  # bar^") # actually a whitespace problem
        self.assertEqual(pyi, "a: int^b: int^c: str^")
        self.coverage()
        self.rm_testdir()
    def test_0111(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "class B:^    b = 2^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^")
        self.coverage()
        self.rm_testdir()
    def test_0112(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int
           c: str""")
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "class B:^    pass^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^")
        self.coverage()
        self.rm_testdir()
    def test_0113(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int
           c: str""")
        run = sh(F"{strip} {tmp}/tmp1.py --pyi -o {tmp}/tmp2.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp2.py"), file_text(F"{tmp}/tmp2.pyi")
        self.assertEqual(py, "class B:^    pass^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^")
        self.coverage()
        self.rm_testdir()
    def test_0114(self) -> None:
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        a: int 
        class B:
           b: int
           c: str""")
        run = sh(F"{strip} -3 {tmp}/test3.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        self.assertTrue(os.path.exists(F"{tmp}/test.pyi"))
        py, pyi = file_text(F"{tmp}/test.py"), file_text(F"{tmp}/test.pyi")
        self.assertEqual(py, "class B:^    pass^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^")
        self.coverage()
        self.rm_testdir()
    def test_0121(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str
           def __str__(self) -> str:
               return self.c 
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "class B:^    b = 2^^    def __str__(self):^        return self.c^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^^    def __str__(self) -> str:^        pass^")
        self.coverage()
        self.rm_testdir()
    def test_0122(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int
           c: str
           def __str__(self) -> str:
               return self.c 
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "class B:^^    def __str__(self):^        return self.c^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^^    def __str__(self) -> str:^        pass^")
        self.coverage()
        self.rm_testdir()
    def test_0131(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str
           def __add__(self, y: str) -> str:
               return self.c + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "class B:^    b = 2^^    def __add__(self, y):^        return self.c + y^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^^    def __add__(self, y: str) -> str:^        pass^")
        self.coverage()
        self.rm_testdir()
    def test_0132(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: str) -> str:
               return self.c + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text(F"{tmp}/tmp1_2.py"), file_text(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, "class B:^^    def __add__(self, y):^        return self.c + y^")
        self.assertEqual(pyi, "a: int^^class B:^    b: int^    c: str^^    def __add__(self, y: str) -> str:^        pass^")
        self.coverage()
        self.rm_testdir()
    def test_0141(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str
           def __add__(self, y: int = 1) -> int:
               return self.b + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, text4("""
        class B:
            b = 2
            
            def __add__(self, y=1):
                return self.b + y"""))
        self.assertEqual(pyi, text4("""
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: int=1) -> int:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0142(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str
           def __add__(self, *, y: int = 1) -> int:
               return self.b + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, text4("""
        class B:
            b = 2
            
            def __add__(self, y=1):
                return self.b + y"""))
        self.assertEqual(pyi, text4("""
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, *, y: int=1) -> int:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0143(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str
           def __add__(self, *, y: int = 1) -> int:
               return self.b + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv} --py36")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, text4("""
        a: int

        class B:
            b: int = 2
            c: str
           
            def __add__(self, *, y=1):
                return self.b + y"""))
        self.assertEqual(pyi, text4("""
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, *, y: int=1) -> int:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0144(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int = 2
           c: str
           def __add__(self, *, y: int = 1) -> int:
               return self.b + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv} --python-version 3.5")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, text4("""
        class B:
            b = 2
           
            def __add__(self, *, y=1):
                return self.b + y"""))
        self.assertEqual(pyi, text4("""
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, *, y: int=1) -> int:
                pass"""))
        self.coverage()
        self.rm_testdir()

    def test_0150(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: str) -> str:
               x: str = "v"
               def twice(u: str) -> str:
                   return u + u
               return self.c + double(x) + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, text4("""
        class B:
            
            def __add__(self, y):
                x = 'v'
        
                def twice(u):
                    return u + u
                return self.c + double(x) + y"""))
        self.assertEqual(pyi, text4("""
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: str) -> str:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0151(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import List
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: List[str]) -> List[str]:
               return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        self.assertEqual(py, text4("""
        class B:
        
            def __add__(self, y):
                return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str]) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0161(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import List
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: List[str], /, a: int = 0, *, b: int = 0) -> List[str]:
               return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        class B:
        
            def __add__(self, y, a=0, b=0):
                return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: int=0, *, b: int=0) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0162(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: int = 0, *, b: int = 0) -> list[str]:
               return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        class B:
        
            def __add__(self, y, a=0, b=0):
                return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: int=0, *, b: int=0) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0163(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int = 0) -> list[str]:
               return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        class B:
        
            def __add__(self, y, a=0, b=0):
                return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: int=0, *, b: int=0) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0164(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | str = 0) -> list[str]:
               x = int(b)
               return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        class B:
        
            def __add__(self, y, a=0, b=0):
                x = int(b)
                return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Union
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: int=0, *, b: Union[int, str]=0) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0165(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
               x = int(b)
               return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        class B:
        
            def __add__(self, y, a=0, b=0):
                x = int(b)
                return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0166(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from pydantic import Field
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> Self:
               x = int(b)
               return self
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        class B:
        
            def __add__(self, y, a=0, b=0):
                x = int(b)
                return self
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional, TypeVar
        a: int
        SelfB = TypeVar('SelfB', bound='B')
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> SelfB:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0167(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from pydantic import Field
        a: int 
        class B:
           b: int
           c: str
           def __add__(self, y: list[str], /, a: Self, *, b: int | None = 0) -> Self:
               x = int(b)
               return a
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        class B:
        
            def __add__(self, y, a, b=0):
                x = int(b)
                return a
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional, TypeVar
        a: int
        SelfB = TypeVar('SelfB', bound='B')
        
        class B:
            b: int
            c: str
            
            def __add__(self, y: List[str], a: SelfB, *, b: Optional[int]=0) -> SelfB:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0175(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            x = int(b)
            return [self.c] + y
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            return [self.c] + y
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0181(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if x := int(b):
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if x:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0182(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if (x := int(b)) > 1:
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if x > 1:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0183(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if (x := int(b)) - 1:
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if x - 1:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0184(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if 1 < (x := int(b)):
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if 1 < x:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0185(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if 1 - (x := int(b)):
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if 1 - x:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0186(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if "foo" == (x := int(b)):
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if 'foo' == x:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0187(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            if (x := int(b)) is not None:
                return [self.c] + y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            x = int(b)
            if x is not None:
                return [self.c] + y
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0189(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from pydantic import Field
        a: int 
        class B:
            def adds(self, y: list[str]) -> list[str]:
                for elem in y:
                    try:
                        with open(y, "r") as f:
                            if (x := f.read(1)) is not None:
                                a = int(x)
                            else:
                                a = 3
                    except:
                        a = 2
                    finally:
                        b = 1
                    while a > 1:
                        a -= 1
                    else:
                        pass
                else:
                    pass
                return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field

        class B:

            def adds(self, y):
                for elem in y:
                    try:
                        with open(y, 'r') as f:
                            x = f.read(1)
                            if x is not None:
                                a = int(x)
                            else:
                                a = 3
                    except:
                        a = 2
                    finally:
                        b = 1
                    while a > 1:
                        a -= 1
                    else:
                        pass
                else:
                    pass
                return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List
        a: int
        
        class B:
        
            def adds(self, y: List[str]) -> List[str]:
                pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0191(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while x := int(b):
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if x:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0192(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while (x := int(b)) > 1:
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if x > 1:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0193(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while (x := int(b)) - 1:
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if x - 1:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0194(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while 1 < (x := int(b)):
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if 1 < x:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0195(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while 1 - (x := int(b)):
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if 1 - x:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0196(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while "foo" == (x := int(b)):
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if 'foo' == x:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()
    def test_0197(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        from typing import Annotated
        from pydantic import Field
        a: int 
        def adds(self, y: list[str], /, a: Annotated[int, Field(gt=0)] = 0, *, b: int | None = 0) -> list[str]:
            while (x := int(b)) is not None:
                b += y
            return 0
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py --pyi {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.pyi"))
        py, pyi = file_text4(F"{tmp}/tmp1_2.py"), file_text4(F"{tmp}/tmp1_2.pyi")
        logg.debug("--- py:\n%s\n--- pyi:\n%s\n---", py, pyi)
        self.assertEqual(py, text4("""
        from pydantic import Field
        
        def adds(self, y, a=0, b=0):
            while True:
                x = int(b)
                if x is not None:
                    b += y
                else:
                    break
            return 0
        """))
        self.assertEqual(pyi, text4("""
        from typing import List, Optional
        a: int
        
        def adds(self, y: List[str], a: int=0, *, b: Optional[int]=0) -> List[str]:
            pass"""))
        self.coverage()
        self.rm_testdir()


    def test_0201(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a = 1.
        b = 'x'
        y = F"{a:.2} {b}"
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        py = file_text4(F"{tmp}/tmp1_2.py")
        self.assertEqual(py, text4("""
        a = 1.0
        b = 'x'
        y = '{:.2} {}'.format(a, b)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0202(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a = 1.
        b = 'x'
        y = F"{a:.2} {b!s}"
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        py = file_text4(F"{tmp}/tmp1_2.py")
        self.assertEqual(py, text4("""
        a = 1.0
        b = 'x'
        y = '{:.2} {!s}'.format(a, b)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0203(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a = 1.
        b = 'x'
        y = F"{a:.2}"
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        py = file_text4(F"{tmp}/tmp1_2.py")
        self.assertEqual(py, text4("""
        a = 1.0
        b = 'x'
        y = '{:.2}'.format(a)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0204(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/tmp1.py", """
        a = 1.
        b = 'x'
        y = F"{a}"
        """)
        run = sh(F"{strip} -2 {tmp}/tmp1.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp1_2.py"))
        py = file_text4(F"{tmp}/tmp1_2.py")
        self.assertEqual(py, text4("""
        a = 1.0
        b = 'x'
        y = '{}'.format(a)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0301(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import sys
        def func1():
            for x in range(3):
                print(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} --nop")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        import sys
        if sys.version_info[0] < 3:
            range = xrange
        
        def func1():
            for x in range(3):
                print(x)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0311(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import sys
        def func1(x: Any):
            if isinstance(x, str):
                print(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} --nop")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        import sys
        if sys.version_info[0] >= 3:
            basestring = str
        
        def func1(x):
            if isinstance(x, basestring):
                print(x)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0321(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import sys
        def func1(x: Any):
            if callable(x):
                repr(x())
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        import sys
        if sys.version_info[0] == 3 and sys.version_info[1] >= 0 and (sys.version_info[1] < 2):
        
            def callable(x):
                return hasattr(x, '__call__')
        
        def func1(x):
            if callable(x):
                repr(x())
        """))
        self.coverage()
        self.rm_testdir()
    def test_0331(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import sys
        def func1(x: Any):
            print(x())
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        from __future__ import print_function
        import sys
        
        def func1(x):
            print(x())
        """))
        self.coverage()
        self.rm_testdir()
    def test_0332(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        #! /usr/bin/env python
        def func1(x: Any):
            print(x())
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        #! /usr/bin/env python
        from __future__ import print_function
        
        def func1(x):
            print(x())
        """))
        self.coverage()
        self.rm_testdir()
    def test_0341(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import sys
        def func1(x: Any):
            repr(x / 2)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        from __future__ import division
        import sys
        
        def func1(x):
            repr(x / 2)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0343(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import sys
        def func1(x: Any):
            print(x / 2)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        from __future__ import division
        from __future__ import print_function
        import sys
        
        def func1(x):
            print(x / 2)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0353(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        from .exceptions import MyException
        def func1(x: Any):
            print(x / 2)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(py, text4("""
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        from .exceptions import MyException
        
        def func1(x):
            print(x / 2)
        """))
        self.coverage()
        self.rm_testdir()
    def test_0401(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import datetime.datetime
        def func1(x: x) -> datetime.datetime:
            return datetime.datetime.fromisoformat(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        import datetime.datetime
        if sys.version_info[0] > 3 or (sys.version_info[0] == 3 and sys.version_info[1] >= 7):

            def datetime_fromisoformat(x):
                return datetime.datetime.fromisoformat(x)
        else:
        
            def datetime_fromisoformat(x):
                import re
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d).(\\\\d\\\\d\\\\d\\\\d\\\\d\\\\d)', x)
                if m:
                    return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d).(\\\\d\\\\d\\\\d)', x)
                if m:
                    return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) * 1000)
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d)', x)
                if m:
                    return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d)', x)
                if m:
                    return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d)', x)
                if m:
                    return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                raise ValueError('not a datetime isoformat: ' + x)
        
        def func1(x):
            return datetime_fromisoformat(x)
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0402(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import datetime.datetime as Time
        def func1(x: x) -> datetime.datetime:
            return Time.fromisoformat(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        import datetime.datetime as Time
        if sys.version_info[0] > 3 or (sys.version_info[0] == 3 and sys.version_info[1] >= 7):

            def Time_fromisoformat(x):
                return Time.fromisoformat(x)
        else:
        
            def Time_fromisoformat(x):
                import re
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d).(\\\\d\\\\d\\\\d\\\\d\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d).(\\\\d\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) * 1000)
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d):(\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d).(\\\\d\\\\d):(\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
                m = re.match('(\\\\d\\\\d\\\\d\\\\d)-(\\\\d\\\\d)-(\\\\d\\\\d)', x)
                if m:
                    return Time(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                raise ValueError('not a datetime isoformat: ' + x)
        
        def func1(x):
            return Time_fromisoformat(x)
        """)))
        self.coverage()
        self.rm_testdir()

    def test_0411(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import subprocess
        def func1() -> str:
            return subprocess.run("echo ok", shell=True).stdout
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv}")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        logg.debug("%s: %s", F"{tmp}/test.py", lines4(open(F"{tmp}/test.py")))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        import subprocess
        if sys.version_info[0] > 3 or (sys.version_info[0] == 3 and sys.version_info[1] >= 5):
            subprocess_run = subprocess.run
        else:
        
            class CompletedProcess:
        
                def __init__(self, args, returncode, outs, errs):
                    self.args = args
                    self.returncode = returncode
                    self.stdout = outs
                    self.stderr = errs
        
                def check_returncode(self):
                    if self.returncode:
                        raise subprocess.CalledProcessError(self.returncode, self.args)

            def subprocess_run(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
                outs, errs = proc.communicate(input=input)
                completed = CompletedProcess(args, proc.returncode, outs, errs)
                if check:
                    completed.check_returncode()
                return completed
        
        def func1():
            return subprocess_run('echo ok', shell=True).stdout
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0412(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import subprocess
        def func1() -> str:
            return subprocess.run("echo ok", shell=True).stdout
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} --python-version=3.3")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        logg.debug("%s: %s", F"{tmp}/test.py", lines4(open(F"{tmp}/test.py")))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        import subprocess
        if sys.version_info[0] > 3 or (sys.version_info[0] == 3 and sys.version_info[1] >= 5):
            subprocess_run = subprocess.run
        else:
        
            class CompletedProcess:
        
                def __init__(self, args, returncode, outs, errs):
                    self.args = args
                    self.returncode = returncode
                    self.stdout = outs
                    self.stderr = errs
        
                def check_returncode(self):
                    if self.returncode:
                        raise subprocess.CalledProcessError(self.returncode, self.args)

            def subprocess_run(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
                try:
                    outs, errs = proc.communicate(input=input, timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                completed = CompletedProcess(args, proc.returncode, outs, errs)
                if check:
                    completed.check_returncode()
                return completed
        
        def func1():
            return subprocess_run('echo ok', shell=True).stdout
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0421(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import pathlib
        def func1(x: str) -> pathlib.PurePath:
            return pathlib.PurePath(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 3):
            import pathlib2 as pathlib
        else:
            import pathlib
        
        def func1(x):
            return pathlib.PurePath(x)
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0422(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import pathlib as fs
        def func1(x: str) -> fs.PurePath:
            return fs.PurePath(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 3):
            import pathlib2 as fs
        else:
            import pathlib as fs
        
        def func1(x):
            return fs.PurePath(x)
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0431(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import tomllib
        def func1(x: str) -> Dict[str, Any]:
            return tomllib.loads(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 11):
            import toml as tomllib
        else:
            import tomllib
        
        def func1(x):
            return tomllib.loads(x)
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0432(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import tomllib as toml
        def func1(x: str) -> Dict[str, Any]:
            return toml.loads(x)
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 11):
            import toml as toml
        else:
            import tomllib as toml
        
        def func1(x):
            return toml.loads(x)
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0441(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import zoneinfo
        def func1() -> List[str]:
            return zoneinfo.available_timezones()
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 9):
            from backports import zoneinfo
        else:
            import zoneinfo
        
        def func1():
            return zoneinfo.available_timezones()
        """)))
        self.coverage()
        self.rm_testdir()
    def test_0444(self) -> None:
        vv = self.begin()
        strip = coverage(STRIP)
        tmp = self.testdir()
        text_file(F"{tmp}/test3.py", """
        import zoneinfo as tz
        def func1() -> List[str]:
            return tz.available_timezones()
        """)
        run = sh(F"{strip} -3 {tmp}/test3.py {vv} -VVV")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/test.py"))
        py = file_text4(F"{tmp}/test.py")
        self.assertEqual(lines4(py), lines4(text4("""
        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 9):
            from backports import zoneinfo as tz
        else:
            import zoneinfo as tz

        def func1():
            return tz.available_timezones()
        """)))
        self.coverage()
        self.rm_testdir()

    def test_0999(self) -> None:
        if COVERAGE:
            coverage3 = PYTHON + " -m coverage "
            run = sh(F"{coverage3} combine", check=False)
            if run.err:
                logg.error("%s", run.err)
            if run.out:
                logg.debug("combine:\n%s", run.out)
            run = sh(F"{coverage3} report")
            if run.err:
                logg.error("%s", run.err)
            if run.out:
                print("\n"+run.out)
            run = sh(F"{coverage3} annotate")
            if run.err:
                logg.error("%s", run.err)
            if run.out:
                logg.log(HINT, "annotate:\n %s", run.out.replace("\n", "\n "))
            run = sh(F"wc -l {STRIP},cover")
            if run.err:
                logg.error("%s", run.err)
            print("\n  "+run.out.replace("\n", "\n  "))


def runtests() -> None:
    global PYTHON, KEEP, COVERAGE # pylint: disable=global-statement
    from optparse import OptionParser  # pylint: disable=deprecated-module,import-outside-toplevel
    cmdline = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    cmdline.add_option("-v", "--verbose", action="count", default=0,
                      help="increase logging level [%default]")
    cmdline.add_option("-p", "--python", metavar="EXE", default=PYTHON,
                  help="use another python execution engine [%default]")
    cmdline.add_option("-a", "--coverage", action="count", default=0,
                  help="gather coverage.py data (use -aa for new set) [%default]")
    cmdline.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    cmdline.add_option("--keep", action="count", default=KEEP,
                  help="keep tempdir and other data after testcase [%default]")
    cmdline.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    cmdline.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = NOTE - opt.verbose * 5)
    PYTHON = opt.python
    KEEP = opt.keep
    COVERAGE = opt.coverage
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
    if opt.coverage:
        if opt.coverage > 1:
            if os.path.exists(".coverage"):
                logg.info("rm .coverage")
                os.remove(".coverage")
    # unittest.main()
    suite = unittest.TestSuite()
    if not cmdline_args:
        cmdline_args = ["test_*"]
    for cmdline_arg in cmdline_args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if cmdline_arg.endswith("/"):
                    cmdline_arg = cmdline_arg[:-1]
                if "*" not in cmdline_arg:
                    cmdline_arg += "*"
                if len(cmdline_arg) > 2 and cmdline_arg[1] == "_":
                    cmdline_arg = "test" + cmdline_arg[1:]
                if fnmatch(method, cmdline_arg):
                    suite.addTest(testclass(method))
    # select runner
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w", encoding="utf-8")
        logg.info("xml results into %s", opt.xmlresults)
    if not logfile:
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped,unused-ignore] # pylint: disable=import-error,import-outside-toplevel
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped,unused-ignore] # pylint: disable=import-error,import-outside-toplevel
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite)
    if not testresult.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    runtests()
