#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,invalid-name,line-too-long,multiple-statements
""" tests for strip_python3 """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "0.1.1092"

from typing import List, Union, Optional, Iterator, NamedTuple
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
logg = logging.getLogger(__name__.replace("/", "."))
STRIP = "strip_python3.py"
PYTHON = "python3.11"
COVERAGE = 0
KEEP = 0
OK = True
NIX = ""
LONGER = 2


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
        except:
            return text.decode("latin-1")
    return text

def _lines(lines: Union[str, List[str]]) -> List[str]:
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def linesof(text: Union[str, List[str]]) -> List[str]:
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def _grep(pattern: str, lines: Union[str, List[str]]) -> Iterator[str]:
    for line in _lines(lines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def grep(pattern: str, lines: Union[str, List[str]]) -> List[str]:
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
def sh(cmd: str, shell: bool = True, check: bool = True, ok: Optional[bool] = None, default: str = "") -> ShellResult:
    if ok is None: ok = OK  # a parameter "ok = OK" does not work in python
    if not ok:
        logg.info("skip %s", cmd)
        return ShellResult(0, default or "", "")
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

def coverage(tool: str) -> str:
    if COVERAGE:
        return PYTHON + " -m coverage " + " run " + tool
    return PYTHON + " " + tool

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
        return "-vv"
    def end(self, maximum: int = 99) -> None:
        runtime = time.monotonic() - self._started
        self.assertLess(runtime, maximum * LONGER)
    # all tests should start with '0'.
    def test_0001(self) -> None:
        strip = coverage(STRIP)
        run = sh(F"{strip} --help")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        self.assertFalse(run.err)
        self.assertTrue(greps(run.out, "this help message"))
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
        text_file(F"{tmp}/tmp3.py", """
        a: int 
        class B:
           b: int
           c: str""")
        run = sh(F"{strip} -3 {tmp}/tmp3.py --pyi")
        logg.debug("err=%s\nout=%s", run.err, run.out)
        # self.assertFalse(run.err)
        self.assertTrue(os.path.exists(F"{tmp}/tmp.py"))
        self.assertTrue(os.path.exists(F"{tmp}/tmp.pyi"))
        py, pyi = file_text(F"{tmp}/tmp.py"), file_text(F"{tmp}/tmp.pyi")
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
    logging.basicConfig(level = logging.WARNING - opt.verbose * 10)
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
            import xmlrunner # type: ignore[import-error,import-untyped] # pylint: disable=import-error,import-outside-toplevel
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped] # pylint: disable=import-error,import-outside-toplevel
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore
    if not testresult.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    runtests()
