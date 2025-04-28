#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long,too-many-lines,too-many-public-methods
# pylint: disable=invalid-name,unspecified-encoding,consider-using-with
""" testing functions directly in strip_python3 module """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "1.3.1167"

from typing import cast
import sys
import unittest
import logging
import os.path
from fnmatch import fnmatchcase as fnmatch
import ast

logg = logging.getLogger(os.path.basename(__file__))

sys.path = [os.path.abspath(os.curdir)] + sys.path
from strip3 import strip_python3 as app # pylint: disable=wrong-import-position,import-error,no-name-in-module

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
        other = ast.Expr(ast.Constant(1)) # unknown script element
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
    # .................................
    def test_1300(self) -> None:
        want = ["callable"]
        text1 = app.text4("""
        if callable(x):
            pass""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        have = sorted(found.keys())
        self.assertEqual(want, have)
    def test_1301(self) -> None:
        want = ["callable"]
        text1 = app.text4("""
        def function() -> None:
            def __inner_():
                if callable(x):
                    pass""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        have = sorted(found.keys())
        self.assertEqual(want, have)
    def test_1302(self) -> None:
        want = ["callable"]
        text1 = app.text4("""
        class A:
            def __add__(self):
                if callable(x):
                    pass""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        have = sorted(found.keys())
        self.assertEqual(want, have)
    def test_1303(self) -> None:
        want = ["callable", "function"]
        text1 = app.text4("""
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        have = sorted(found.keys())
        self.assertEqual(want, have)
    def test_1310(self) -> None:
        # note how it ignores the local function returning the imported one
        want = {"callable": "callable", "X.function": "function"}
        uses = {"callable": "callable", "function": "X.function"}
        text1 = app.text4("""
        from X import function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1311(self) -> None:
        want = {"callable": "callable", "X.function2": "function"}
        uses = {"callable": "callable", "function": "X.function2"}
        text1 = app.text4("""
        from X import function2 as function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1312(self) -> None:
        want = {"callable": "callable", "X.Y.function2": "function"}
        uses = {"callable": "callable", "function": "X.Y.function2"}
        text1 = app.text4("""
        from X.Y import function2 as function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1313(self) -> None:
        want = {"callable": "callable", "X.Y.Z.function2": "function"}
        uses = {"callable": "callable", "function": "X.Y.Z.function2"}
        text1 = app.text4("""
        from X.Y.Z import function2 as function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1314(self) -> None:
        want = {"callable": "callable", "X.Y.Z.function": "function"}
        uses = {"callable": "callable", "function": "X.Y.Z.function"}
        text1 = app.text4("""
        from X.Y.Z import function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1315(self) -> None:
        want = {"callable": "callable", "X.Y.Z.function": "function"}
        uses = {"callable": "callable", "function": "X.Y.Z.function"}
        text1 = app.text4("""
        from X.Y.Z import function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1319(self) -> None:
        want = {"callable": "callable", "X.Y.Z.function": "function2"}
        uses = {"callable": "callable", "function2": "X.Y.Z.function"}
        text1 = app.text4("""
        from X.Y.Z import function
        function2 = function
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    function2()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        if TODO:
            logg.info("would be nice - allowing renames")
            self.assertEqual(want, found)
            self.assertEqual(uses, calls)
        else:
            real = {"callable": "callable", "function2": "function2"}
            self.assertEqual(real, found)
            self.assertEqual(real, calls)
    def test_1320(self) -> None:
        # note how it ignores the local function returning the imported one
        want = {"callable": "callable", "X.function": "X.function"}
        uses = {"callable": "callable", "X.function": "X.function"}
        text1 = app.text4("""
        import X
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1321(self) -> None:
        want = {"callable": "callable", "X.Y.function": "X.Y.function"}
        uses = {"callable": "callable", "X.Y.function": "X.Y.function"}
        text1 = app.text4("""
        import X.Y
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.Y.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    @unittest.expectedFailure
    def test_1322(self) -> None:
        want = {"callable": "callable", "X.Y.Z.function": "X.Y.Z.function"}
        uses = {"callable": "callable", "X.Y.Z.function": "X.Y.Z.function"}
        text1 = app.text4("""
        import X.Y.Z
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.Y.Z.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1323(self) -> None:
        want = {"callable": "callable", "X.Y.Z.function": "P.function"}
        uses = {"callable": "callable", "P.function": "X.Y.Z.function"}
        text1 = app.text4("""
        import X.Y.Z as P
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    P.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1329(self) -> None:
        # note how it ignores the local function returning the imported one
        want = {"callable": "callable", "X.Y.Z.function": "Q.function"}
        uses = {"callable": "callable", "Q.function": "X.Y.Z.function"}
        text1 = app.text4("""
        import X.Y.Z as P
        Q = P
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    Q.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        if TODO:
            self.assertEqual(want, found)
            self.assertEqual(uses, calls)
        else:
            real = {'callable': 'callable'}
            self.assertEqual(real, found)
            self.assertEqual(real, calls)
    def test_1331(self) -> None:
        want = {"callable": "callable"}
        uses = {"callable": "callable"}
        text1 = app.text4("""
        import Q
        class X:
            def function():
                pass
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1332(self) -> None:
        want = {"callable": "callable"}
        uses = {"callable": "callable"}
        text1 = app.text4("""
        import Q
        class X:
            class Y:
                def function():
                    pass
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.Y.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1333(self) -> None:
        want = {"callable": "callable"}
        uses = {"callable": "callable"}
        text1 = app.text4("""
        import Q
        class X:
            class Y:
                class Z:
                    def function():
                       pass
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.Y.Z.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)
    def test_1334(self) -> None:
        want = {"callable": "callable"}
        uses = {"callable": "callable"}
        text1 = app.text4("""
        import Q
        class X:
            class Y:
                class Z:
                    class U:
                       def function():
                          pass
        def function() -> None:
            pass
        class A:
            def __add__(self):
                if callable(x):
                    X.Y.Z.U.function()""")
        tree1 = ast.parse(text1)
        deep1 = app.DetectImportedFunctionCalls()
        deep1.visit(tree1)
        found = deep1.found
        calls = deep1.calls
        logg.info("found %s", found)
        logg.info("calls %s", calls)
        self.assertEqual(want, found)
        self.assertEqual(uses, calls)

    # .................................
    def test_1400(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 0):
            a = b
        x = 1""")
        self.assertEqual(want, have)
    def test_1401(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 0):
            a = b
        x = 1""")
        self.assertEqual(want, have)
    def test_1402(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1403(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1404(self) -> None:
        text1 = app.text4("""
        "testing"
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        \"\"\"testing\"\"\"
        import b
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1405(self) -> None:
        text1 = app.text4("""
        "testing"
        import b
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        \"\"\"testing\"\"\"
        import b
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1406(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1407(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1408(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2([], body=ast.parse("a = b").body, orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1409(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3([], body=ast.parse("a = b").body, orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)

    def test_1412(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], (3,5), ["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 5):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1413(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], (3,5), ["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 5):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1414(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 5) or sys.version_info >= (3, 7):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1415(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 5) and sys.version_info < (3, 7):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1416(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2([], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info < (3, 5) or sys.version_info >= (3, 7):
            pass
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1417(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3([], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        if sys.version_info >= (3, 5) and sys.version_info < (3, 7):
            pass
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)

    def test_1418(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2([], (3,5), [], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        x = 1""")
        self.assertEqual(want, have)
    def test_1419(self) -> None:
        text1 = app.text4("""
        import b
        
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3([], (3,5), [], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        import b
        x = 1""")
        self.assertEqual(want, have)
    def test_1450(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 0):
            a = b
        x = 1""")
        self.assertEqual(want, have)
    def test_1451(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 0):
            a = b
        x = 1""")
        self.assertEqual(want, have)
    def test_1452(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1453(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1454(self) -> None:
        text1 = app.text4("""
        "testing"
       
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        \"\"\"testing\"\"\"
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1455(self) -> None:
        text1 = app.text4("""
        "testing"

        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], or_else=["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        \"\"\"testing\"\"\"
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)

    def test_1456(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1457(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1458(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2([], body=ast.parse("a = b").body, orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1459(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3([], body=ast.parse("a = b").body, orelse=ast.parse("a = None").body)
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 0):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)

    def test_1462(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], (3,5), ["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 5):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1463(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], (3,5), ["a = None"])
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 5):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1464(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2(["a = b"], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 5) or sys.version_info >= (3, 7):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1465(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3(["a = b"], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 5) and sys.version_info < (3, 7):
            a = b
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1466(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2([], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info < (3, 5) or sys.version_info >= (3, 7):
            pass
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1467(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3([], (3,5), ["a = None"], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        if sys.version_info >= (3, 5) and sys.version_info < (3, 7):
            pass
        else:
            a = None
        x = 1""")
        self.assertEqual(want, have)
    def test_1468(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython2([], (3,5), [], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        x = 1""")
        self.assertEqual(want, have)
    def test_1469(self) -> None:
        text1 = app.text4("""
        x = 1""")
        tree1 = ast.parse(text1)
        defs1 = app.DefineIfPython3([], (3,5), [], (3, 7))
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        x = 1""")
        self.assertEqual(want, have)
    def test_1500(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F""
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = ''
        print(s)""")
        self.assertEqual(want, have)
    def test_1501(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"{y}"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = '{}'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1502(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"{y}"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = '{}'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1503(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'x{}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1504(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y=}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'xy={!r}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1510(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y!r}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'x{!r}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1511(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y!s}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'x{!s}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1512(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y!a}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'x{!a}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1519(self) -> None:
        want = True
        have = False
        text1 = app.text4("""
        y = 1
        s = F"x{y!q}z"
        print(s)""")
        try:
            __tree1 = ast.parse(text1)
        except SyntaxError:
            have = True
        self.assertEqual(want, have)
    def test_1520(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"{y:n}"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = '{:n}'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1522(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y:n}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'x{:n}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1523(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y:3.2n}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'x{:3.2n}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1529(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"x{y=:3.2n}z"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = 'xy={:3.2n}z'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1530(self) -> None:
        text1 = app.text4("""
        y = 1
        s = F"{y!a:n}"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = '{!a:n}'.format(y)
        print(s)""")
        self.assertEqual(want, have)
    def test_1540(self) -> None:
        text1 = app.text4("""
        y = 1
        z = 2
        s = F"{y:n}{z=}"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        z = 2
        s = '{:n}z={!r}'.format(y, z)
        print(s)""")
        self.assertEqual(want, have)
    def test_1541(self) -> None:
        text1 = app.text4("""
        y = 1
        z = 2
        s = F"{y:n}{z:s}"
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringToFormatTransformer()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        z = 2
        s = '{:n}{:s}'.format(y, z)
        print(s)""")
        self.assertEqual(want, have)
    def test_1550(self) -> None:
        old = app.want.fstring_numbered
        app.want.fstring_numbered = True
        try:
            text1 = app.text4("""
            y = 1
            z = 2
            s = F"{y:n}{z=}"
            print(s)""")
            tree1 = ast.parse(text1)
            defs1 = app.FStringToFormatTransformer()
            tree2 = defs1.visit(tree1)
            have = ast.unparse(tree2) + "\n"
            want = app.text4("""
            y = 1
            z = 2
            s = '{1:n}z={2!r}'.format(y, z)
            print(s)""")
            self.assertEqual(want, have)
        finally:
            app.want.fstring_numbered = old
    def test_1551(self) -> None:
        old = app.want.fstring_numbered
        app.want.fstring_numbered = True
        try:
            text1 = app.text4("""
            y = 1
            z = 2
            s = F"{y:n}{z:s}"
            print(s)""")
            tree1 = ast.parse(text1)
            defs1 = app.FStringToFormatTransformer()
            tree2 = defs1.visit(tree1)
            have = ast.unparse(tree2) + "\n"
            want = app.text4("""
            y = 1
            z = 2
            s = '{1:n}{2:s}'.format(y, z)
            print(s)""")
            self.assertEqual(want, have)
        finally:
            app.want.fstring_numbered = old
    def test_1581(self) -> None:
        text1 = app.text4("""
        y = 1
        s = "{y:n}".format(**locals())
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringFromLocalsFormat()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = f'{y:n}'
        print(s)""")
        self.assertEqual(want, have)
    def test_1585(self) -> None:
        text1 = app.text4("""
        y = 1
        x = "{y:n}"
        print(x.format(**locals()))""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringFromVarLocalsFormat()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        print(f'{y:n}')""")
        self.assertEqual(want, have)
    def test_1586(self) -> None:
        text1 = app.text4("""
        y = 1
        x = "{y:n}"
        logg.debug(x.format(**locals()))""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringFromVarLocalsFormat()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        logg.debug(f'{y:n}')""")
        self.assertEqual(want, have)
    def test_1587(self) -> None:
        text1 = app.text4("""
        y = 1
        x = "{y:n}"
        s = foo(x.format(**locals()))
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringFromVarLocalsFormat()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        s = foo(f'{y:n}')
        print(s)""")
        self.assertEqual(want, have)
    def test_1589(self) -> None:
        text1 = app.text4("""
        y = 1
        x = "{y:n}"
        logg.warning("running %s", x)
        s = foo(x.format(**locals()))
        print(s)""")
        tree1 = ast.parse(text1)
        defs1 = app.FStringFromVarLocalsFormat()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        y = 1
        x = '{y:n}'
        logg.warning('running %s', x)
        s = foo(f'{y:n}')
        print(s)""")
        self.assertEqual(want, have)

    def test_1600(self) -> None:
        text1 = app.text4("""
        class A:
            def func1(self) -> int:
                return 0
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        class A:

            def func1(self) -> int:
                return 0
        """)
        self.assertEqual(want, have)
    def test_1601(self) -> None:
        text1 = app.text4("""
        class A:
            def func1(self) -> Self:
                return self
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:

            def func1(self) -> SelfA:
                return self
        """)
        self.assertEqual(want, have)
    def test_1602(self) -> None:
        text1 = app.text4("""
        class A:
            b: int
            def func1(self, other: Self) -> int:
                return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:
            b: int

            def func1(self, other: SelfA) -> int:
                return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1603(self) -> None:
        text1 = app.text4("""
        class A:
            b: int
            def func1(self, other: Self, /, c: int) -> int:
                return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:
            b: int

            def func1(self, other: SelfA, /, c: int) -> int:
                return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1604(self) -> None:
        text1 = app.text4("""
        class A:
            b: int
            def func1(self, c: int, /, other: Self) -> int:
                return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:
            b: int

            def func1(self, c: int, /, other: SelfA) -> int:
                return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1605(self) -> None:
        text1 = app.text4("""
        class A:
            b: int
            def func1(self, c: int, *, other: Self) -> int:
                return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:
            b: int

            def func1(self, c: int, *, other: SelfA) -> int:
                return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1606(self) -> None:
        text1 = app.text4("""
        class A:
            b: int
            def func1(self, c: int, *other: Self) -> int:
                return a.b + other[0].b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:
            b: int

            def func1(self, c: int, *other: SelfA) -> int:
                return a.b + other[0].b
        """)
        self.assertEqual(want, have)
    def test_1607(self) -> None:
        text1 = app.text4("""
        class A:
            b: int
            def func1(self, c: int, **other: Self) -> int:
                return a.b + other[0].b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        SelfA = TypeVar('SelfA', bound='A')

        class A:
            b: int

            def func1(self, c: int, **other: SelfA) -> int:
                return a.b + other[0].b
        """)
        self.assertEqual(want, have)
    def test_1610(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                def func1(self) -> int:
                    return 0
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:

            class A:

                def func1(self) -> int:
                    return 0
        """)
        self.assertEqual(want, have)
    def test_1611(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                def func1(self) -> Self:
                    return self
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:

                def func1(self) -> SelfA:
                    return self
        """)
        self.assertEqual(want, have)
    def test_1612(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                b: int
                def func1(self, other: Self) -> int:
                    return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:
                b: int

                def func1(self, other: SelfA) -> int:
                    return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1613(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                b: int
                def func1(self, other: Self, /, c: int) -> int:
                    return a.b + other.b
            """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:
                b: int

                def func1(self, other: SelfA, /, c: int) -> int:
                    return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1614(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                b: int
                def func1(self, c: int, /, other: Self) -> int:
                    return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:
                b: int

                def func1(self, c: int, /, other: SelfA) -> int:
                    return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1615(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                b: int
                def func1(self, c: int, *, other: Self) -> int:
                    return a.b + other.b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:
                b: int

                def func1(self, c: int, *, other: SelfA) -> int:
                    return a.b + other.b
        """)
        self.assertEqual(want, have)
    def test_1616(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                b: int
                def func1(self, c: int, *other: Self) -> int:
                    return a.b + other[0].b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:
                b: int

                def func1(self, c: int, *other: SelfA) -> int:
                    return a.b + other[0].b
        """)
        self.assertEqual(want, have)
    def test_1617(self) -> None:
        text1 = app.text4("""
        def foo1() -> None:
            class A:
                b: int
                def func1(self, c: int, **other: Self) -> int:
                    return a.b + other[0].b
        """)
        tree1 = ast.parse(text1)
        defs1 = app.ReplaceSelfByTypevar()
        tree2 = defs1.visit(tree1)
        have = ast.unparse(tree2) + "\n"
        want = app.text4("""
        def foo1() -> None:
            SelfA = TypeVar('SelfA', bound='A')

            class A:
                b: int

                def func1(self, c: int, **other: SelfA) -> int:
                    return a.b + other[0].b
        """)
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
