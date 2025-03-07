#! /usr/bin/env python3.11
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long
""" easy way to transform and remove python3 typehints """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "0.5.1095"

from typing import List, Dict, Optional, Union, Tuple, cast
import sys
import re
import os.path as fs
import logging
# ........
# import ast
import ast_comments as ast

# (python3.12) = type() statement
# (python3.12) = support for generics
# (python3.6) = NoReturn
# (python3.8) = Final
# (python3.8) = Protocol
# (python3.11) = assert_type
# PEP3102 (python 3.0) keyword-only params
# PEP3107 (python3.0) function annotations
# PEP 484 (python 3.5) typehints and "typing" module (and tpying.TYPE_CHECKING)
#          including "cast", "NewType", "overload", "no_type_check", "ClassVar", AnyStr = str|bytes
# PEP 498 (python3.6) formatted string literals
# PEP 515 (python 3.6) underscores in numeric literals
# PEP 526 (python 3.6) syntax for variable annotations (variable typehints)
#         (python 3.6) NamedTuple with variables annotations (3.5 had call-syntax)
# PEP 563 (python 3.7) delayed typehints for "SelfClass" (from __future__ 3.10)
# ....... (Pyhton 3.7) Generics
# PEP 572 (python 3.8) walrus operator
# PEP 570 (python 3.8) positional-only params
# ....... (python 3.8) f-strings "{varname=}"
# PEP 591 (python 3.8) @final decorator
# PEP 593 (python 3.9) typing.Annotated
# PEP 585 (python 3.9) builtins as types (e.g "list", "dict")
# PEP 604 (python 3.10) a|b union operator
# PEP 613 (python 3.10) TypeAlias
# PEP 647 (python 3.10) TypeGuard
# PEP 654 (python 3.11) exception groups
# PEP 678 (python 3.11) exception notes
# PEP 646 (python 3.11) variadic generics
# PEP 655 (python 3.11) TypeDict items Required, NotRequired
# PEP 673 (python 3.11) Self type, Never
# PEP 675 (python 3.11) LiteralString
#         (python 3.11) Protocols, reveal_type(x), get_overloads
#         (python 3.11)  assert_never(unreachable)

DONE = (logging.ERROR + logging.WARNING) // 2
NOTE = (logging.INFO + logging.WARNING) // 2
HINT = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(DONE, "DONE")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(HINT, "HINT")

logg = logging.getLogger("strip" if __name__ == "__main__" else __name__.replace("/", "."))

OK = True
NIX = ""
FSTRING_NUMBERED = False
SHOW_DUMP = 0

REMOVE_VAR_TYPEHINTS = False
REMOVE_TYPEHINTS = False
REMOVE_KEYWORDONLY = False
REMOVE_POSITIONAL = False
REMOVE_PYI_POSITIONAL = False
REPLACE_FSTRING = False
DEFINE_RANGE = False
DEFINE_BASESTRING = False
DEFINE_CALLABLE = False
DEFINE_PRINT_FUNCTION = False
DEFINE_FLOAT_DIVISION = False
DEFINE_ABSOLUTE_IMPORT = False
DATETIME_FROMISOFORMAT = False
SUBPROCESS_RUN = False

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

class DetectImportFrom(ast.NodeTransformer):
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.found: Dict[str, Dict[str, str]] = {}
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.ImportFrom = node
        if imports.module:
            modulename = ("." * imports.level) + imports.module
            if modulename not in self.found:
                self.found[modulename] = {}
            for symbol in imports.names:
                if symbol.name not in self.found[modulename]:
                    self.found[modulename][symbol.name] = symbol.asname or symbol.name
        return self.generic_visit(node)

class RequireImportFrom:
    def __init__(self, require: List[str]) -> None:
        self.require = require
    def visit(self, node: ast.AST) -> ast.AST:
        imports = DetectImportFrom()
        imports.visit(node)
        newimport: List[str] = []
        for require in self.require:
            if "." in require:
                library, function = require.split(require, 1)
                if library in imports.found:
                    if function in imports.found[library]:
                        logg.debug("%s already imported", require)
                    else:
                        newimport.append(require)
                else:
                    newimport.append(require)
        if not newimport:
            return node
        if isinstance(node, ast.Module):
            module: ast.Module = node
            body: List[ast.stmt] = []
            done = False
            if not imports.found:
                for stmt in module.body:
                    if isinstance(stmt, ast.Comment):
                        body.append(stmt)
                    elif done:
                        body.append(stmt)
                    else:
                        for new in newimport:
                            mod, func = new.split(".", 1)
                            body.append(ast.ImportFrom(mod, [ast.alias(name=func)], 0))
                        body.append(stmt)
                        done = True
            else:
                for stmt in module.body:
                    if not isinstance(stmt, ast.ImportFrom) and not isinstance(stmt, ast.Import):
                        body.append(stmt)
                    elif done:
                        body.append(stmt)
                    else:
                        for new in newimport:
                            mod, func = new.split(".", 1)
                            body.append(ast.ImportFrom(mod, [ast.alias(name=func)], 0))
                        body.append(stmt)
                        done = True
            module.body = body
            return module
        return node

class ReplaceIsinstanceBaseType(ast.NodeTransformer):
    def __init__(self, replace: Optional[Dict[str, str]] = None) -> None:
        ast.NodeTransformer.__init__(self)
        self.replace = replace if replace is not None else { "str": "basestring"}
        self.defines: List[str] = []
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        calls: ast.Call = node
        if not isinstance(calls.func, ast.Name):
            return self.generic_visit(node)
        callfunc: ast.Name = calls.func
        if callfunc.id != "isinstance":
            return self.generic_visit(node)
        typecheck = calls.args[1]
        if isinstance(typecheck, ast.Name):
            typename = typecheck
            if typename.id in self.replace:
                origname = typename.id
                basename = self.replace[origname]
                typename.id = basename
                self.defines.append(F"{basename} = {origname}")
        return self.generic_visit(node)

class DetectFunctionCalls(ast.NodeTransformer):
    def __init__(self, replace: Dict[str, str] = {}) -> None:
        ast.NodeTransformer.__init__(self)
        self.imported: Dict[str, str] = {}
        self.importas: Dict[str, str] = {}
        self.found: Dict[str, int] = {}
        self.divs: int = 0
        self.replace = replace
    def visit_Import(self, node: ast.Import) -> ast.AST:  # pylint: disable=invalid-name
        for alias in node.names:
            if alias.asname:
                self.imported[alias.name] = alias.asname
                self.importas[alias.asname] = alias.name
            else:
                self.imported[alias.name] = alias.name
                self.importas[alias.name] = alias.name
        return self.generic_visit(node)
    def visit_Div(self, node: ast.Div) -> ast.AST:  # pylint: disable=invalid-name
        self.divs += 1
        return self.generic_visit(node)
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        calls: ast.Call = node
        if isinstance(calls.func, ast.Name):
            call1: ast.Name = calls.func
            logg.debug("found call1: %s", call1.id)
            callname = call1.id
            if callname not in self.found:
                self.found[callname] = 0
            self.found[callname] += 1
            if callname in self.replace:
                return ast.Call(func=ast.Name(self.replace[callname]), args=calls.args, keywords=calls.keywords)
        elif isinstance(calls.func, ast.Attribute):
            call2: ast.Attribute = calls.func
            if isinstance(call2.value, ast.Name):
                call21: ast.Name = call2.value
                module2 = call21.id
                if module2 in self.importas:
                    logg.debug("found call2: %s.%s", module2, call2.attr)
                    callname = self.importas[module2] + "." + call2.attr
                    if callname not in self.found:
                        self.found[callname] = 0
                    self.found[callname] += 1
                    if callname in self.replace:
                        return ast.Call(func=ast.Name(self.replace[callname]), args=calls.args, keywords=calls.keywords)
                else:
                    logg.debug("skips call2: %s.%s", module2, call2.attr)
                    logg.debug("have imports: %s", ", ".join(self.importas.keys()))
            elif isinstance(call2.value, ast.Attribute):
                call3: ast.Attribute = call2.value
                if isinstance(call3.value, ast.Name):
                    call31: ast.Name = call3.value
                    module3 = call31.id + "." + call3.attr
                    if module3 in self.importas:
                        logg.debug("found call3: %s.%s", module3, call2.attr)
                        callname = self.importas[module3] + "." + call2.attr
                        if callname not in self.found:
                            self.found[callname] = 0
                        self.found[callname] += 1
                        if callname in self.replace:
                            return ast.Call(func=ast.Name(self.replace[callname]), args=calls.args, keywords=calls.keywords)
                    else:
                        logg.debug("skips call3: %s.%s", module3, call2.attr)
                        logg.debug("have imports: %s", ", ".join(self.importas.keys()))
                elif isinstance(call3.value, ast.Attribute):
                    logg.debug("skips call4+ (not implemented)")
                else:
                    logg.debug("skips call3+ [%s]", type(call3.value))
            else:
                logg.debug("skips call2+ [%s]", type(call2.value))
        else:
            logg.debug("skips call1+ [%s]", type(calls.func))
        return self.generic_visit(node)

class DefineIfPython2:
    body: List[ast.stmt]
    def __init__(self, expr: List[str], atleast: Optional[Tuple[int, int]] = None, before: Optional[Tuple[int, int]] = None, orelse: Union[str, List[ast.stmt]] = NIX) -> None:
        self.atleast = atleast
        self.before = before
        self.body = []
        if isinstance(orelse, str):
            if not orelse:
                self.orelse = []
            else:
                elseparsed: ast.Module = ast.parse(orelse)
                self.orelse = elseparsed.body
        else:
            self.orelse = orelse
        for stmtlist in [ast.parse(e).body for e in expr]:
            self.body += stmtlist
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and self.body:
            # pylint: disable=consider-using-f-string
            module1: ast.Module = node
            body: List[ast.stmt] = []
            before_imports = True
            after_append = False
            for stmt in module1.body:
                if isinstance(stmt, ast.ImportFrom) or isinstance(stmt, ast.Import):
                    if before_imports:
                        before_imports = False
                    body.append(stmt)
                elif before_imports or after_append:
                    body.append(stmt)
                else:
                    testcode = "sys.version_info[0] < 3"
                    testmodule: ast.Module = ast.parse(testcode)
                    assert isinstance(testmodule.body[0], ast.Expr)
                    testbody: ast.Expr = testmodule.body[0]
                    if isinstance(testbody.value, ast.Compare):
                        testcompare: ast.expr = testbody.value
                        if self.before:
                            testcode = "sys.version_info[0] < {} or sys.version_info[0] == {} and sys.version_info[1] < {}".format(self.before[0], self.before[0], self.before[1])
                            testmodule = ast.parse(testcode)
                            assert isinstance(testmodule.body[0], ast.Expr)
                            testbody = testmodule.body[0]
                            testcompare = testbody.value
                        if self.atleast:
                            testcode = "sys.version_info[0] > {} or sys.version_info[0] == {} and sys.version_info[1] >= {}".format(self.atleast[0], self.atleast[0], self.atleast[1])
                            testmodule = ast.parse(testcode)
                            assert isinstance(testmodule.body[0], ast.Expr)
                            testbody = testmodule.body[0]
                            testatleast = testbody.value
                            testcompare = ast.BoolOp(op=ast.And(), values=[testatleast, testcompare])
                        before = self.before if self.before else (3,0)
                        logg.log(HINT, "python2 atleast %s before %s", self.atleast, before)
                        if self.atleast and self.atleast[0] == before[0]:
                            testcode = "sys.version_info[0] == {} and sys.version_info[1] >= {} and sys.version_info[1] < {}".format(self.atleast[0], self.atleast[0], before[1])
                            testmodule = ast.parse(testcode)
                            assert isinstance(testmodule.body[0], ast.Expr)
                            testbody = testmodule.body[0]
                            testcompare = testbody.value
                    else:
                        logg.error("unexpected %s found for testcode: %s", type(testbody.value), testcode)  # and fallback to explicit ast-tree
                        testcompare = ast.Compare(left=ast.Subscript(value=ast.Attribute(value=ast.Name("sys"), attr="version_info"), slice=cast(ast.expr, ast.Index(value=ast.Num(0)))), ops=[ast.Lt()], comparators=[ast.Num(3)])
                    python2 = ast.If(test=testcompare, body=self.body, orelse=self.orelse)
                    python2.lineno = stmt.lineno
                    body.append(python2)
                    body.append(stmt)
                    after_append = True
            module2 = ast.Module(body, module1.type_ignores)
            return module2
        else:
            return node

class DefineIfPython3:
    body: List[ast.stmt]
    def __init__(self, expr: List[str], atleast: Optional[Tuple[int, int]] = None, before: Optional[Tuple[int, int]] = None, orelse: Union[str, List[ast.stmt]] = NIX) -> None:
        self.atleast = atleast
        self.before = before
        self.body = []
        if isinstance(orelse, str):
            if not orelse:
                self.orelse = []
            else:
                elseparsed: ast.Module = ast.parse(orelse)
                self.orelse = elseparsed.body
        else:
            self.orelse = orelse
        for stmtlist in [ast.parse(e).body for e in expr]:
            self.body += stmtlist
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and self.body:
            # pylint: disable=consider-using-f-string
            module1: ast.Module = node
            body: List[ast.stmt] = []
            before_imports = True
            after_append = False
            for stmt in module1.body:
                if isinstance(stmt, ast.ImportFrom) or isinstance(stmt, ast.Import):
                    if before_imports:
                        before_imports = False
                    body.append(stmt)
                elif before_imports or after_append:
                    body.append(stmt)
                else:
                    testcode = "sys.version_info[0] >= 3"
                    testmodule: ast.Module = ast.parse(testcode)
                    assert isinstance(testmodule.body[0], ast.Expr)
                    testbody: ast.Expr = testmodule.body[0]
                    if isinstance(testbody.value, ast.Compare):
                        testcompare: ast.expr = testbody.value
                        if self.atleast:
                            testcode = "sys.version_info[0] > {} or sys.version_info[0] == {} and sys.version_info[1] >= {}".format(self.atleast[0], self.atleast[0], self.atleast[1])
                            testmodule = ast.parse(testcode)
                            assert isinstance(testmodule.body[0], ast.Expr)
                            testbody = testmodule.body[0]
                            testcompare = testbody.value
                        if self.before:
                            testcode = "sys.version_info[0] < {} or sys.version_info[0] == {} and sys.version_info[1] < {}".format(self.before[0], self.before[0], self.before[1])
                            testmodule = ast.parse(testcode)
                            assert isinstance(testmodule.body[0], ast.Expr)
                            testbody = testmodule.body[0]
                            testbefore = testbody.value
                            testcompare = ast.BoolOp(op=ast.And(), values=[testcompare, testbefore])
                        atleast = self.atleast if self.atleast else (3,0)
                        logg.log(HINT, "python3 atleast %s before %s", atleast, self.before)
                        if self.before and atleast[0] == self.before[0]:
                            testcode = "sys.version_info[0] == {} and sys.version_info[1] >= {} and sys.version_info[1] < {}".format(atleast[0], atleast[1], self.before[1])
                            testmodule = ast.parse(testcode)
                            assert isinstance(testmodule.body[0], ast.Expr)
                            testbody = testmodule.body[0]
                            testcompare = testbody.value
                    else:
                        logg.error("unexpected %s found for testcode: %s", type(testbody.value), testcode)  # and fallback to explicit ast-tree
                        testcompare=ast.Compare(left=ast.Subscript(value=ast.Attribute(value=ast.Name("sys"), attr="version_info"), slice=cast(ast.expr, ast.Index(value=ast.Num(0)))), ops=[ast.GtE()], comparators=[ast.Num(3)])
                    python3 = ast.If(test=testcompare, body=self.body, orelse=self.orelse)
                    python3.lineno = stmt.lineno
                    body.append(python3)
                    body.append(stmt)
                    after_append = True
            module2 = ast.Module(body, module1.type_ignores)
            return module2
        else:
            return node

class FStringToFormat(ast.NodeTransformer):
    def visit_FormattedValue(self, node: ast.FormattedValue) -> ast.Call:  # pylint: disable=invalid-name
        """ If the string contains a single formatting field and nothing else the node can be isolated otherwise it appears in JoinedStr."""
        # NOTE: I did not manage to create a test case that triggers this visitor
        num: int = 0
        form: str = ""
        args: List[ast.expr] = []
        if OK:
            if OK:
                fmt: ast.FormattedValue = node
                conv = ""
                if fmt.conversion == 115:
                    conv = "!s"
                elif fmt.conversion == 114:
                    conv = "!r"
                elif fmt.conversion == 97:
                    conv = "!a"
                elif fmt.conversion != -1:
                    logg.error("unknown conversion id in f-string: %s > %s", type(node), fmt.conversion)
                if fmt.format_spec:
                    if isinstance(fmt.format_spec, ast.JoinedStr):
                        join: ast.JoinedStr = fmt.format_spec
                        for val in join.values:
                            if isinstance(val, ast.Constant):
                                if FSTRING_NUMBERED:
                                    form += "{%i%s:%s}" % (num, conv, val.value)
                                else:
                                    form += "{%s:%s}" % (conv, val.value)
                            else:
                                logg.error("unknown part of format_spec in f-string: %s > %s", type(node), type(val))
                    else:
                        logg.error("unknown format_spec in f-string: %s", type(node))
                else:
                    if FSTRING_NUMBERED:
                        form += "{%i%s}" % (num, conv)
                    else:
                        form += "{%s}" %(conv)
                num += 1
                args += [fmt.value]
                self.generic_visit(fmt.value)
        make = ast.Call(ast.Attribute(ast.Constant(form), attr="format"), args, keywords=[])
        return make
    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.Call:  # pylint: disable=invalid-name
        num: int = 0
        form: str = ""
        args: List[ast.expr] = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                con: ast.Constant = part
                form += con.value
            elif isinstance(part, ast.FormattedValue):
                fmt: ast.FormattedValue = part
                conv = ""
                if fmt.conversion == 115:
                    conv = "!s"
                elif fmt.conversion == 114:
                    conv = "!r"
                elif fmt.conversion == 97:
                    conv = "!a"
                elif fmt.conversion != -1:
                    logg.error("unknown conversion id in f-string: %s > %s", type(node), fmt.conversion)
                if fmt.format_spec:
                    if isinstance(fmt.format_spec, ast.JoinedStr):
                        join: ast.JoinedStr = fmt.format_spec
                        for val in join.values:
                            if isinstance(val, ast.Constant):
                                if FSTRING_NUMBERED:
                                    form += "{%i%s:%s}" % (num, conv, val.value)
                                else:
                                    form += "{%s:%s}" % (conv, val.value)
                            else:
                                logg.error("unknown part of format_spec in f-string: %s > %s", type(node), type(val))
                    else:
                        logg.error("unknown format_spec in f-string: %s", type(node))
                else:
                    if FSTRING_NUMBERED:
                        form += "{%i%s}" % (num, conv)
                    else:
                        form += "{%s}" % (conv)
                num += 1
                args += [fmt.value]
                self.generic_visit(fmt.value)
            else:
                logg.error("unknown part of f-string: %s", type(node))
        make = ast.Call(ast.Attribute(ast.Constant(form), attr="format"), args, keywords=[])
        return make

class StripHints(ast.NodeTransformer):
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if not REMOVE_TYPEHINTS:
            return node
        imports: ast.ImportFrom = node
        logg.debug("-imports: %s", ast.dump(imports))
        if imports.module != "typing":
            return node # unchanged
        return None
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if not REMOVE_TYPEHINTS:
            return self.generic_visit(node)
        calls: ast.Call = node
        logg.debug("-calls: %s", ast.dump(calls))
        if not isinstance(calls.func, ast.Name):
            return self.generic_visit(node)
        callfunc: ast.Name = calls.func
        if callfunc.id != "cast":
            return node # unchanged
        if len(calls.args) > 1:
            return self.generic_visit(calls.args[1])
        logg.error("-bad cast: %s", ast.dump(node))
        return ast.Constant(None)
    def visit_AnnAssign(self, node: ast.AnnAssign) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if not REMOVE_TYPEHINTS and not REMOVE_VAR_TYPEHINTS:
            return self.generic_visit(node)
        assign: ast.AnnAssign = node
        logg.debug("-assign: %s", ast.dump(assign))
        if assign.value is not None:
            assign2 = ast.Assign(targets=[assign.target], value=assign.value)
            assign2.lineno = assign.lineno
            return self.generic_visit(assign2)
        return None
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        func: ast.FunctionDef = node
        logg.debug("-func: %s", ast.dump(func))
        annos = 0
        posonlyargs: List[ast.arg] = []
        functionargs: List[ast.arg] = []
        kwonlyargs: List[ast.arg] = []
        vargarg = func.args.vararg
        kwarg = func.args.kwarg
        kwdefaults: List[Optional[ast.expr]] = []
        defaults: List[ast.expr] = []
        if OK:
            for arg in func.args.posonlyargs:
                logg.debug("-pos arg: %s", ast.dump(arg))
                if REMOVE_POSITIONAL:
                    functionargs.append(ast.arg(arg.arg))
                else:
                    posonlyargs.append(ast.arg(arg.arg))
                if arg.annotation:
                    annos += 1
        if OK:
            for arg in func.args.args:
                logg.debug("-fun arg: %s", ast.dump(arg))
                functionargs.append(ast.arg(arg.arg))
                if arg.annotation:
                    annos += 1
        if OK:
            for arg in func.args.kwonlyargs:
                logg.debug("-kwo arg: %s", ast.dump(arg))
                if REMOVE_KEYWORDONLY:
                    functionargs.append(ast.arg(arg.arg))
                else:
                    kwonlyargs.append(ast.arg(arg.arg))
                if arg.annotation:
                    annos += 1
        if vargarg is not None:
            if vargarg.annotation:
                annos += 1
            vargarg = ast.arg(vargarg.arg)
        if kwarg is not None:
            if kwarg.annotation:
                annos += 1
            kwarg = ast.arg(kwarg.arg)
        old = 0
        if func.args.kw_defaults and REMOVE_KEYWORDONLY:
            old += 1
        if not annos and not func.returns and not old:
            return self.generic_visit(node) # unchanged
        if OK:
            for exp in func.args.defaults:
                defaults.append(exp)
        if OK:
            for kwexp in func.args.kw_defaults:
                if REMOVE_KEYWORDONLY:
                    if kwexp is not None:
                        defaults.append(kwexp)
                else:
                    kwdefaults.append(kwexp)
        args2 = ast.arguments(posonlyargs, functionargs, vargarg, kwonlyargs, # ..
            kwdefaults, kwarg, defaults)
        func2 = ast.FunctionDef(func.name, args2, func.body, func.decorator_list)
        func2.lineno = func.lineno
        return self.generic_visit(func2)

class TypeHints:
    pyi: List[ast.stmt]
    def __init__(self) -> None:
        self.pyi = []
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module):
            body: List[ast.stmt] = []
            for child in node.body:
                if isinstance(child, ast.ImportFrom):
                    imports = child
                    body.append(child)
                    if imports.module == "typing":
                        imports3 = ast.ImportFrom(imports.module, imports.names, imports.level)
                        imports3.lineno = imports.lineno
                        self.pyi.append(imports3)
                elif isinstance(child, ast.AnnAssign):
                    assign1: ast.AnnAssign = child
                    logg.debug("assign: %s", ast.dump(assign1))
                    if REMOVE_TYPEHINTS or REMOVE_VAR_TYPEHINTS:
                        if assign1.value is not None:
                            assign2 = ast.Assign(targets=[assign1.target], value=assign1.value)
                            assign2.lineno = assign1.lineno
                            body.append(assign2)
                        else:
                            logg.debug("remove simple typehint")
                    else:
                        body.append(assign1)
                    assign3 = ast.AnnAssign(target=assign1.target, annotation=assign1.annotation, value=None, simple=assign1.simple)
                    self.pyi.append(assign3)
                elif isinstance(child, ast.ClassDef):
                    logg.debug("class: %s", ast.dump(child))
                    stmt: List[ast.stmt] = []
                    decl: List[ast.stmt] = []
                    for part in child.body:
                        if isinstance(part, ast.AnnAssign):
                            assign: ast.AnnAssign = part
                            logg.debug("assign: %s", ast.dump(assign))
                            if REMOVE_TYPEHINTS or REMOVE_VAR_TYPEHINTS:
                                if assign.value is not None:
                                    assign2 = ast.Assign(targets=[assign.target], value=assign.value)
                                    assign2.lineno = assign.lineno
                                    stmt.append(assign2)
                                else:
                                    logg.debug("remove simple typehint")
                            else:
                                stmt.append(assign)
                            assign3 = ast.AnnAssign(target=assign.target, annotation=assign.annotation, value=None, simple=assign.simple)
                            decl.append(assign3)
                        elif isinstance(part, ast.FunctionDef):
                            func: ast.FunctionDef = part
                            logg.debug("func: %s", ast.dump(func))
                            annos = 0
                            posonlyargs: List[ast.arg] = []
                            functionargs: List[ast.arg] = []
                            kwonlyargs: List[ast.arg] = []
                            vargarg = func.args.vararg
                            kwarg = func.args.kwarg
                            if OK:
                                for arg in func.args.posonlyargs:
                                    logg.debug("pos arg: %s", ast.dump(arg))
                                    posonlyargs.append(ast.arg(arg.arg))
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in func.args.args:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    functionargs.append(ast.arg(arg.arg))
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in func.args.kwonlyargs:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    kwonlyargs.append(ast.arg(arg.arg))
                                    if arg.annotation:
                                        annos += 1
                            if vargarg is not None:
                                if vargarg.annotation:
                                    annos += 1
                                vargarg = ast.arg(vargarg.arg)
                            if kwarg is not None:
                                if kwarg.annotation:
                                    annos += 1
                                kwarg = ast.arg(kwarg.arg)
                            if not annos and not func.returns:
                                stmt.append(func)
                            else:
                                logg.debug("args: %s", ast.dump(func.args))
                                if not REMOVE_TYPEHINTS:
                                    rets2 = func.returns
                                    args2 = func.args
                                else:
                                    rets2 = None
                                    args2 = ast.arguments(posonlyargs, functionargs, vargarg, kwonlyargs, # ..
                                           func.args.kw_defaults, kwarg, func.args.defaults)
                                func2 = ast.FunctionDef(func.name, args2, func.body, func.decorator_list, rets2)
                                func2.lineno = func.lineno
                                stmt.append(func2)
                                args3 = func.args
                                if posonlyargs and REMOVE_PYI_POSITIONAL:
                                    posonlyargs3: List[ast.arg] = posonlyargs if not REMOVE_PYI_POSITIONAL else []
                                    functionargs3 = functionargs if not REMOVE_PYI_POSITIONAL else posonlyargs + functionargs
                                    args3 = ast.arguments(posonlyargs3, functionargs3, vargarg, kwonlyargs, # ..
                                           func.args.kw_defaults, kwarg, func.args.defaults)
                                func3 = ast.FunctionDef(func.name, args3, [ast.Pass()], func.decorator_list, func.returns)
                                func3.lineno = func.lineno
                                decl.append(func3)
                        else:
                            stmt.append(part)
                    if not stmt:
                        stmt.append(ast.Pass())
                    class2 = ast.ClassDef(child.name, child.bases, child.keywords, stmt, child.decorator_list)
                    body.append(class2)
                    if decl:
                        class3 = ast.ClassDef(child.name, child.bases, child.keywords, decl, child.decorator_list)
                        self.pyi.append(class3)
                else:
                    logg.debug("found: %s", ast.dump(child))
                    body.append(child)
            logg.debug("new module with %s children", len(body))
            return ast.Module(body, type_ignores=node.type_ignores)
        return node

# ............................................................................... MAIN

EACH_REMOVE3 = 1
EACH_APPEND2 = 2
EACH_INPLACE = 4
def main(args: List[str], eachfile: int = 0, outfile: str = "", pyi: int = 0) -> int:
    written: List[str] = []
    for arg in args:
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
        tree1 = ast.parse(text, type_comments=True)
        types = TypeHints()
        tree = types.visit(tree1)
        strip = StripHints()
        tree = strip.visit(tree)
        if REPLACE_FSTRING:
            fstring = FStringToFormat()
            tree = fstring.visit(tree)
        if DEFINE_CALLABLE or DEFINE_PRINT_FUNCTION or DEFINE_FLOAT_DIVISION:
            calls = DetectFunctionCalls()
            calls.visit(tree)
            if "callable" in calls.found and DEFINE_CALLABLE:
                defs1 = DefineIfPython3(["def callable(x): return hasattr(x, '__call__')"], before=(3,2))
                tree = defs1.visit(tree)
            if "print" in calls.found and DEFINE_PRINT_FUNCTION:
                defprint = RequireImportFrom(["__future__.print_function"])
                tree = defprint.visit(tree)
            if calls.divs and DEFINE_FLOAT_DIVISION:
                defdivs = RequireImportFrom(["__future__.division"])
                tree = defdivs.visit(tree)
            if "datetime.datetime.fromisoformat" in calls.found and DATETIME_FROMISOFORMAT:
                datetime_module = calls.importas["datetime.datetime"]
                fromisoformat = F"{datetime_module}_fromisoformat"  if "." not in datetime_module else "datetime_fromisoformat"
                isoformatdef = DefineIfPython3([F"def {fromisoformat}(x): return {datetime_module}.fromisoformat(x)"], atleast=(3,7), orelse=text4(F"""
                def {fromisoformat}(x):
                    import re
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d):(\\d\\d).(\\d\\d\\d\\d\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1), int(m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)))))
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d):(\\d\\d).(\\d\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1), int(m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) * 1000)))
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d):(\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1), int(m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)) )))
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1), int(m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)) )))
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1), int(m.group(2), int(m.group(3)) )))
                    raise ValueError("not a datetime isoformat: "+x)
                """))
                isoformatfunc = DetectFunctionCalls({"datetime.datetime.fromisoformat": fromisoformat})
                tree = isoformatdef.visit(isoformatfunc.visit(tree))
            if "subprocess.run" in calls.found and SUBPROCESS_RUN:
                subprocess_module = calls.importas["subprocess"]
                defname = subprocess_module + "_run"
                isoformatdef = DefineIfPython3([F"def {defname}(x): return {subprocess_module}.run(x)"], atleast=(3,5), orelse=text4(F"""
                class CalledProcessError({subprocess_module}.SubprocessError):
                    def __init__(self, args, returncode, stdout, stderr):
                        self.cmd = args
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr
                        self.output = self.stdout
                class CompletedProcess:
                    def __init__(self, args, returncode, stdout, stderr):
                        self.args = args
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr
                    def check_returncode(self):
                        if self.returncode:
                            raise CalledProcessError(self.args, self.returncode, self.stdout, self.stderr)
                def {defname}(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                    proc = Popen(args, stdin=stdin, input=input, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, timeout=timeout, env=env)
                    try:
                        outs, errs = proc.communicate(input=input, timeout=timeout)
                    except {subprocess_module}.TimeoutExpired:
                        proc.kill()
                        outs, errs = proc.communicate()
                    completed = CompletedProcess(args, proc.returncode, outs, errs)
                    if check:
                        completed.check_returncode()
                    return completed
                """))
                isoformatfunc = DetectFunctionCalls({"subprocess.run": defname})
                tree = isoformatdef.visit(isoformatfunc.visit(tree))
            if SHOW_DUMP:
                logg.log(HINT, "detected function calls:\n%s", "\n".join(calls.found.keys()))
        if DEFINE_ABSOLUTE_IMPORT:
            imps = DetectImportFrom()
            imps.visit(tree)
            relative = [imp for imp in imps.found if imp.startswith(".")]
            if relative:
                defimps = RequireImportFrom(["__future__.absolute_import"])
                tree = defimps.visit(tree)
        if DEFINE_RANGE:
            calls = DetectFunctionCalls()
            calls.visit(tree)
            if "range" in calls.found:
                defs2 = DefineIfPython2(["range = xrange"])
                tree = defs2.visit(tree)
        if DEFINE_BASESTRING:
            basetypes = ReplaceIsinstanceBaseType({"str": "basestring"})
            basetypes.visit(tree)
            if basetypes.replace:
                defs3 = DefineIfPython3(basetypes.defines)
                tree = defs3.visit(tree)
        if SHOW_DUMP:
            logg.log(NOTE, "%s: (before transformations)\n%s", arg, beautify_dump(ast.dump(tree1)))
        if SHOW_DUMP > 1:
            logg.log(NOTE, "%s: (after transformations)\n%s", arg, beautify_dump(ast.dump(tree)))
        done = ast.unparse(tree)
        if SHOW_DUMP > 2:
            logg.log(NOTE, "%s: (after transformations) ---------------- \n%s", arg, done)
        if outfile:
            out = outfile
        elif arg.endswith("3.py") and eachfile & EACH_REMOVE3:
            out = arg[:-len("3.py")]+".py"
        elif arg.endswith(".py") and eachfile & EACH_APPEND2:
            out = arg[:-len(".py")]+"_2.py"
        elif eachfile & EACH_INPLACE:
            out = arg
        else:
            out = "-"
        if out not in written:
            if out in ["-"]:
                if done:
                    print(done)
            else:
                with open(out, "w", encoding="utf-8") as w:
                    w.write(done)
                    if done and not done.endswith("\n"):
                        w.write("\n")
                logg.info("written %s", out)
                written.append(out)
                if pyi:
                    typehintsfile = out+"i"
                    logg.debug("--pyi => %s", typehintsfile)
                    if isinstance(tree1, ast.Module):
                        typehints = ast.Module(types.pyi, type_ignores=tree1.type_ignores)
                        with open(typehintsfile, "w", encoding="utf-8") as w:
                            done = ast.unparse(typehints)
                            w.write(done)
                            if done and not done.endswith("\n"):
                                w.write("\n")

    return 0

def beautify_dump(x: str) -> str:
    return x.replace("body=[", "\n body=[").replace("FunctionDef(", "\n FunctionDef(").replace(", ctx=Load()",",.")

def read_defaults(*files: str) -> Dict[str, Union[str, int]]:
    settings: Dict[str, Union[str, int]] = {"verbose": 0, # ..
        "python-version": NIX, "pyi-version": NIX, "remove-typehints": 0, "remove-var-typehints": 0, # ..
        "remove-keywordonly": 0, "remove-positionalonly": 0, "remove-pyi-positionalonly": 0, # ..
        "replace-fstring": 0, "define-range": 0, "define-basestring": 0, "define-callable": 0, # ..
        "define-print-function": 0, "define-float-division": 0, "define-absolute-import": 0, # ..
        "no-define-print-function": 0, "no-define-float-division": 0, "no-define-absolute-import": 0, # ..
        "no-replace-fstring": 0, "no-define-range": 0, "no-define-basestring":0, "no-define-callable": 0,  # ..
        "no-remove-keywordonly": 0, "no-remove-positionalonly": 0, "no-remove-pyi-positionalonly": 0,
        "datetime-fromisoformat": 0, "no-datetime-fromisoformat": 0,
        "subprocess-run": 0, "no-subprocess-run": 0, }
    for configfile in files:
        if fs.isfile(configfile):
            if configfile.endswith(".toml"):
                logg.debug("found toml configfile %s", configfile)
                import tomllib # pylint: disable=import-outside-toplevel
                with open(configfile, "rb") as f:
                    conf = tomllib.load(f)
                    if "tool" in conf and "strip-python3" in conf["tool"]:
                        section: Dict[str, Union[str, int, bool]] = conf["tool"]["strip-python3"]
                        for setting in section:
                            if setting in settings:
                                oldvalue = settings[setting]
                                setvalue = section[setting]
                                if isinstance(oldvalue, str):
                                    if isinstance(setvalue, str):
                                        settings[setting] = setvalue
                                    else:
                                        logg.error("%s[%s]: expecting str but found %s", configfile, setting, type(setvalue))
                                elif isinstance(oldvalue, int):
                                    if isinstance(setvalue, int) or isinstance(setvalue, float):
                                        settings[setting] = int(setvalue)
                                    else:
                                        logg.error("%s[%s]: expecting int but found %s", configfile, setting, type(setvalue))
                                elif isinstance(oldvalue, bool):
                                    if isinstance(setvalue, bool):
                                        settings[setting] = 1 if setvalue is True else 0
                                    else:
                                        logg.error("%s[%s]: expecting int but found %s", configfile, setting, type(setvalue))
                                else:
                                    logg.error("%s[%s]: unknown type found %s", configfile, setting, type(setvalue))
                            else:
                                logg.error("%s: unknown setting found = %s", configfile, setting)
                                logg.debug("%s: known options are %s", configfile, ", ".join(settings.keys()))
            elif configfile.endswith(".cfg"):
                import configparser # pylint: disable=import-outside-toplevel
                confs = configparser.ConfigParser()
                confs.read(configfile)
                if "strip-python3" in confs:
                    section2 = confs["strip-python3"]
                    for option in section2:
                        if OK:
                            if option in settings:
                                oldvalue = settings[option]
                                setvalue = section2[option]
                                if isinstance(oldvalue, str):
                                    settings[option] = setvalue
                                elif isinstance(oldvalue, int):
                                    if setvalue in ["true", "True"]:
                                        settings[option] = 1
                                    elif setvalue in ["false", "False"]:
                                        settings[option] = 0
                                    elif setvalue in ["0", "1", "2", "3"]:
                                        settings[option] = int(setvalue)
                                    else:
                                        logg.error("%s[%s]: expecting int but found %s", configfile, option, setvalue)
                                else:
                                    logg.error("%s[%s]: unknown value found %s", configfile, option, setvalue)
                            else:
                                logg.error("%s: unknown setting found = %s", configfile, option)
                                logg.debug("%s: known options are %s", configfile, ", ".join(settings.keys()))
    return settings

if __name__ == "__main__":
    defs = read_defaults("pyproject.toml", "setup.cfg")
    from optparse import OptionParser # pylint: disable=deprecated-module
    cmdline = OptionParser("%prog [options] file3.py", description=__doc__.strip())
    cmdline.formatter.max_help_position = 30
    cmdline.add_option("-v", "--verbose", action="count", default=defs["verbose"], help="increase logging level")
    cmdline.add_option("--pyi-version", metavar="3.6", default=defs["pyi-version"], help="set python version for py-includes")
    cmdline.add_option("--python-version", metavar="2.7", default=defs["python-version"], help="set python features by version")
    cmdline.add_option("--py36", action="count", default=0, help="keep features available since python3.6")
    cmdline.add_option("--remove-typehints", action="count", default=defs["remove-typehints"], help="3.5 function annotations and cast operator")
    cmdline.add_option("--remove-var-typehints", action="count", default=defs["remove-var-typehints"], help="only 3.6 variable annotations (for typehints)")
    cmdline.add_option("--remove-keywordonly", action="count", default=defs["remove-keywordonly"], help="3.0 keywordonly parameters")
    cmdline.add_option("--remove-positionalonly", action="count", default=defs["remove-positionalonly"], help="3.8 positionalonly parameters")
    cmdline.add_option("--remove-pyi-positionalonly", action="count", default=defs["remove-pyi-positionalonly"], help="3.8 positionalonly parameters in *.pyi")
    cmdline.add_option("--replace-fstring", action="count", default=defs["replace-fstring"], help="3.6 f-strings to string.format")
    cmdline.add_option("--define-range", action="count", default=defs["define-range"], help="3.0 define range() to xrange() iterator")
    cmdline.add_option("--define-basestring", action="count", default=defs["define-basestring"], help="3.0 isinstance(str) is basestring python2")
    cmdline.add_option("--define-callable", action="count", default=defs["define-callable"], help="3.2 callable(x) as in python2")
    cmdline.add_option("--define-print-function", action="count", default=defs["define-print-function"], help="3.0 print() or from __future__")
    cmdline.add_option("--define-float-division", action="count", default=defs["define-float-division"], help="3.0 float division or from __future__")
    cmdline.add_option("--define-absolute-import", action="count", default=defs["define-absolute-import"], help="3.0 absolute import or from __future__")
    cmdline.add_option("--datetime-fromisoformat", action="count", default=defs["datetime-fromisoformat"], help="3.7 datetime.fromisoformat or boilerplate")
    cmdline.add_option("--subprocess-run", action="count", default=defs["subprocess-run"], help="3.5 subprocess.run or boilerplate")
    cmdline.add_option("--no-replace-fstring", action="count", default=defs["no-replace-fstring"], help="3.6 f-strings")
    cmdline.add_option("--no-define-range", action="count", default=defs["no-define-range"], help="3.0 define range()")
    cmdline.add_option("--no-define-basestring", action="count", default=defs["no-define-basestring"], help="3.0 isinstance(str)")
    cmdline.add_option("--no-define-callable", "--noc", action="count", default=defs["no-define-callable"], help="3.2 callable(x)")
    cmdline.add_option("--no-define-print-function", "--nop", action="count", default=defs["no-define-print-function"], help="3.0 print() function")
    cmdline.add_option("--no-define-float-division", "--nod", action="count", default=defs["no-define-float-division"], help="3.0 float division")
    cmdline.add_option("--no-define-absolute-import", "--noa", action="count", default=defs["no-define-absolute-import"], help="3.0 absolute import")
    cmdline.add_option("--no-datetime-fromisoformat", action="count", default=defs["no-datetime-fromisoformat"], help="3.7 datetime.fromisoformat")
    cmdline.add_option("--no-subprocess-run", action="count", default=defs["no-subprocess-run"], help="3.5 subprocess.run")
    cmdline.add_option("--no-remove-keywordonly", action="count", default=defs["no-remove-keywordonly"], help="3.0 keywordonly parameters")
    cmdline.add_option("--no-remove-positionalonly", action="count", default=defs["no-remove-positionalonly"], help="3.8 positionalonly parameters")
    cmdline.add_option("--no-remove-pyi-positionalonly", action="count", default=defs["no-remove-pyi-positionalonly"], help="3.8 positionalonly in *.pyi")
    cmdline.add_option("--show", action="count", default=0, help="show transformer settings")
    cmdline.add_option("-V", "--dump", action="count", default=0, help="show ast tree before (and after) changes")
    cmdline.add_option("-1", "--inplace", action="count", default=0, help="file.py gets overwritten")
    cmdline.add_option("-2", "--append2", action="count", default=0, help="file.py becomes file2.py")
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py becomes file.py")
    cmdline.add_option("-y", "--pyi", action="count", default=0, help="generate file.pyi as well")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, NOTE - 5 * opt.verbose))
    PYI_VERSION = 36
    if opt.pyi_version:
        if len(opt.pyi_version) >= 3 and opt.pyi_version[1] == ".":
            PYI_VERSION = int(opt.pyi_version[0]) * 10 + int(opt.pyi_version[2:])
        else:
            logg.error("unknown --pyi-version %s", opt.pyi_version)
    BACK_VERSION = 27
    if opt.py36:
        BACK_VERSION = 36
    elif opt.python_version:
        if len(opt.python_version) >= 3 and opt.python_version[1] == ".":
            BACK_VERSION = int(opt.python_version[0]) * 10 + int(opt.python_version[2:])
        else:
            logg.error("unknown --python-version %s", opt.python_version)
    logg.debug("BACK_VERSION %s PYI_VERSION %s", BACK_VERSION, PYI_VERSION)
    if PYI_VERSION < 38 or opt.remove_pyi_positionalonly:
        if not opt.no_remove_pyi_positionalonly:
            REMOVE_PYI_POSITIONAL = True
    if BACK_VERSION < 38 or opt.remove_positionalonly:
        if not opt.no_remove_positionalonly:
            REMOVE_POSITIONAL = True
    if BACK_VERSION < 30 or opt.remove_keywordonly:
        if not opt.no_remove_keywordonly:
            REMOVE_KEYWORDONLY = True
    if BACK_VERSION < 36 or opt.remove_typehints or opt.remove_var_typehints:
        REMOVE_VAR_TYPEHINTS = True
    if BACK_VERSION < 35 or opt.remove_typehints:
        REMOVE_TYPEHINTS = True
    if BACK_VERSION < 36 or opt.replace_fstring:
        if not opt.no_replace_fstring:
            REPLACE_FSTRING = True
            if opt.replace_fstring > 1:
                FSTRING_NUMBERED = True
    if BACK_VERSION < 30 or opt.define_range:
        if not opt.no_define_range:
            DEFINE_RANGE = True
    if BACK_VERSION < 30 or opt.define_basestring:
        if not opt.no_define_basestring:
            DEFINE_BASESTRING = True
    if BACK_VERSION < 32 or opt.define_callable:
        if not opt.no_define_callable:
            DEFINE_CALLABLE = True
    if BACK_VERSION < 30 or opt.define_print_function:
        if not opt.no_define_print_function:
            DEFINE_PRINT_FUNCTION = True
    if BACK_VERSION < 30 or opt.define_float_division:
        if not opt.no_define_float_division:
            DEFINE_FLOAT_DIVISION = True
    if BACK_VERSION < 30 or opt.define_absolute_import:
        if not opt.no_define_absolute_import:
            DEFINE_ABSOLUTE_IMPORT = True
    if BACK_VERSION < 37 or opt.datetime_fromisoformat:
        if not opt.no_datetime_fromisoformat:
            DATETIME_FROMISOFORMAT = True
    if BACK_VERSION < 35 or opt.subprocess_run:
        if not opt.no_subprocess_run:
            SUBPROCESS_RUN = True
    if opt.show:
        logg.log(NOTE, "%s = %s", "python-version-int", BACK_VERSION)
        logg.log(NOTE, "%s = %s", "pyi-version-int", PYI_VERSION)
        logg.log(NOTE, "%s = %s", "define-basestring", DEFINE_BASESTRING)
        logg.log(NOTE, "%s = %s", "define-range", DEFINE_RANGE)
        logg.log(NOTE, "%s = %s", "define-callable", DEFINE_CALLABLE)
        logg.log(NOTE, "%s = %s", "define-print-function", DEFINE_PRINT_FUNCTION)
        logg.log(NOTE, "%s = %s", "define-float-division", DEFINE_FLOAT_DIVISION)
        logg.log(NOTE, "%s = %s", "define-absolute-import", DEFINE_ABSOLUTE_IMPORT)
        logg.log(NOTE, "%s = %s", "replace-fstring", REPLACE_FSTRING)
        logg.log(NOTE, "%s = %s", "remove-keywordsonly", REMOVE_KEYWORDONLY)
        logg.log(NOTE, "%s = %s", "remove-positionalonly", REMOVE_POSITIONAL)
        logg.log(NOTE, "%s = %s", "remove-pyi-positionalonly", REMOVE_PYI_POSITIONAL)
        logg.log(NOTE, "%s = %s", "remove-var-typehints", REMOVE_VAR_TYPEHINTS)
        logg.log(NOTE, "%s = %s", "remove-typehints", REMOVE_TYPEHINTS)
    if opt.dump:
        SHOW_DUMP = int(opt.dump)
    _EACHFILE = EACH_REMOVE3 if opt.remove3 else 0
    _EACHFILE |= EACH_APPEND2 if opt.append2 else 0
    _EACHFILE |= EACH_INPLACE if opt.inplace else 0
    sys.exit(main(cmdline_args, eachfile=_EACHFILE, outfile=opt.outfile, pyi=opt.pyi))
