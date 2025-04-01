#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
# pylint: disable=invalid-name,unspecified-encoding,consider-using-with
""" testing functions directly in strip_python3 module """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "1.1.1127"

from typing import cast
import sys
import unittest
import logging
import os.path
from fnmatch import fnmatchcase as fnmatch
import ast

logg = logging.getLogger(os.path.basename(__file__))

sys.path.append(os.curdir)
from src import strip_python3 as app # pylint: disable=wrong-import-position,import-error,no-name-in-module

TODO = 0
VV = "-vv"

class StripUnitTest(unittest.TestCase):
    def test_1100(self) -> None:
        x = app.to_int(2)
        y = app.to_int(1)
        n = app.to_int(0)
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(n, 0)
    def test_1101(self) -> None:
        x = app.to_int("2")
        y = app.to_int("1")
        n = app.to_int("0")
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(n, 0)
    def test_1102(self) -> None:
        x = app.to_int("x")
        y = app.to_int("y")
        n = app.to_int("n")
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(n, 0)
    def test_1110(self) -> None:
        a = app.text4("")
        b = app.text4(" ")
        c = app.text4("""
        """)
        d = app.text4("""
         """)
        e = app.text4("""
        
         """)
        self.assertEqual(a, "")
        self.assertEqual(b, " ")
        self.assertEqual(c, "\n")
        self.assertEqual(d, "\n")
        self.assertEqual(e, "\n")
    def test_1111(self) -> None:
        a = app.text4("a")
        b = app.text4(" a")
        c = app.text4("""
        a""")
        d = app.text4("""
         a""")
        e = app.text4("""
        a
         """)
        self.assertEqual(a, "a")
        self.assertEqual(b, " a")
        self.assertEqual(c, "a\n")
        self.assertEqual(d, "a\n")
        self.assertEqual(e, "a\n")
    def test_1112(self) -> None:
        a = app.text4("a b")
        b = app.text4(" a b")
        c = app.text4("""
        a
        b""")
        d = app.text4("""
         a
        b""")
        e = app.text4("""
        a
         b""")
        self.assertEqual(a, "a b")
        self.assertEqual(b, " a b")
        self.assertEqual(c, "a\nb\n")
        self.assertEqual(d, "a\n        b\n")
        self.assertEqual(e, "a\n b\n")
    def test_1201(self) -> None:
        other = ast.Constant(1) # unknown script element
        have: ast.Module = app.pyi_module([other])
        have0 = cast(ast.Constant, have.body[0])
        self.assertEqual(other.value, have0.value)
    def test_1202(self) -> None:
        want = "foo"
        script = app.text4("""
        "foo"
        """)
        script1 = ast.parse(script)
        assert isinstance(script1, ast.Module)
        pyi = script1.body
        have1: ast.Module = app.pyi_module(pyi)
        have2 = have1.body[0]
        assert isinstance(have2, ast.Expr)
        have3 = have2.value
        assert isinstance(have3, ast.Constant)
        have = have3.value
        self.assertEqual(want, have)
    def test_1203(self) -> None:
        want = "foo"
        script = app.text4("""
        class A:
            "foo"
            pass
        """)
        script1 = ast.parse(script)
        assert isinstance(script1, ast.Module)
        pyi = script1.body
        have1: ast.Module = app.pyi_module(pyi)
        have2 = have1.body[0]
        assert isinstance(have2, ast.ClassDef)
        have3 = have2.body[0]
        assert isinstance(have3, ast.Expr)
        have4 = have3.value
        assert isinstance(have4, ast.Constant)
        have = have4.value
        self.assertEqual(want, have)

    def test_1210(self) -> None:
        pyi = ast.parse(app.text4("""
        def foo(a: A) -> B:
            pass
        """))
        py1 = ast.parse(app.text4("""
        from x import A
        """))
        py2 = ast.parse(app.text4("""
        from y import B
        """))
        want = app.text4("""
        from x import A
        from y import B

        def foo(a: A) -> B:
            pass""")
        pyi2 = app.pyi_copy_imports(pyi, py1, py2)
        have = ast.unparse(pyi2) + "\n"
        self.assertEqual(want, have)
    def test_1211(self) -> None:
        pyi = ast.parse(app.text4("""
        def foo(a: A) -> B:
            pass
        """))
        py1 = ast.parse(app.text4("""
        from x.z import A
        """))
        py2 = ast.parse(app.text4("""
        from y.z import B
        """))
        want = app.text4("""
        from x.z import A
        from y.z import B

        def foo(a: A) -> B:
            pass""")
        pyi2 = app.pyi_copy_imports(pyi, py1, py2)
        have = ast.unparse(pyi2) + "\n"
        self.assertEqual(want, have)
    def test_1212(self) -> None:
        pyi = ast.parse(app.text4("""
        def foo(a: x.A) -> y.B:
            pass
        """))
        py1 = ast.parse(app.text4("""
        import x
        """))
        py2 = ast.parse(app.text4("""
        import y
        """))
        want = app.text4("""
        import x, y

        def foo(a: x.A) -> y.B:
            pass""")
        pyi2 = app.pyi_copy_imports(pyi, py1, py2)
        have = ast.unparse(pyi2) + "\n"
        self.assertEqual(want, have)
    def test_1213(self) -> None:
        pyi = ast.parse(app.text4("""
        def foo(a: x.A) -> y.B:
            pass
        """))
        py1 = ast.parse(app.text4("""
        import app1.x as x
        """))
        py2 = ast.parse(app.text4("""
        import app2.y as y
        """))
        want = app.text4("""
        from app1 import x
        from app2 import y

        def foo(a: x.A) -> y.B:
            pass""")
        pyi2 = app.pyi_copy_imports(pyi, py1, py2)
        have = ast.unparse(pyi2) + "\n"
        self.assertEqual(want, have)
    @unittest.expectedFailure
    def test_1215(self) -> None:
        pyi = ast.parse(app.text4("""
        def foo(a: app1.x.A) -> app2.y.B:
            pass
        """))
        py1 = ast.parse(app.text4("""
        import app1.x
        """))
        py2 = ast.parse(app.text4("""
        import app2.y
        """))
        want = app.text4("""
        import app1.x
        import app2.y

        def foo(a: app1.x.A) -> app2.y.B:
            pass""")
        pyi2 = app.pyi_copy_imports(pyi, py1, py2)
        have = ast.unparse(pyi2) + "\n"
        self.assertEqual(want, have)


if __name__ == "__main__":
    # unittest.main()
    from optparse import OptionParser  # pylint: disable=deprecated-module
    cmdline = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    cmdline.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    cmdline.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    cmdline.add_option("--todo", action="count", default=TODO,
                  help="show when an alternative outcome is desired [%default]")
    cmdline.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    cmdline.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    TODO = opt.todo
    VV = "-v" + ("v" * opt.verbose)
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
    if not cmdline_args:
        cmdline_args = ["test_*"]
    for arg in cmdline_args:
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
