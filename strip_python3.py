#! /usr/bin/env python3.11
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long
""" easy way to transform and remove python3 typehints """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "0.2.1093"

from typing import List, Dict, Optional, cast
import sys
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



logg = logging.getLogger(__name__.replace("/", "."))

OK = True
NIX = ""
FSTRING_NUMBERED = False

REMOVE_VAR_TYPEHINTS = False
REMOVE_TYPEHINTS = False
REMOVE_KEYWORDONLY = False
REMOVE_POSITIONAL = False
REMOVE_PYI_POSITIONAL = False
REPLACE_FSTRING = False
DEFINE_RANGE = False

class DetectFunctionCalls(ast.NodeTransformer):
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.found: Dict[str, int] = {}
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        calls: ast.Call = node
        if not isinstance(calls.func, ast.Name):
            return self.generic_visit(node)
        callfunc: ast.Name = calls.func
        if callfunc.id not in self.found:
            self.found[callfunc.id] = 0
        self.found[callfunc.id] += 1
        return self.generic_visit(node)

class DefineIfPython2:
    body: List[ast.stmt]
    def __init__(self, expr: List[str]) -> None:
        self.body = []
        for stmtlist in [ast.parse(e).body for e in expr]:
            self.body += stmtlist
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module):
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
                    python2 = ast.If(test=ast.Compare(left=ast.Subscript(value=ast.Attribute(value=ast.Name("sys"), attr="version_info"), slice=cast(ast.expr, ast.Index(value=ast.Num(0)))), ops=[ast.Lt()], comparators=[ast.Num(3)]), body=self.body, orelse=[])
                    python2.lineno = stmt.lineno
                    body.append(python2)
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
        if DEFINE_RANGE:
            calls = DetectFunctionCalls()
            calls.visit(tree)
            if "range" in calls.found:
                defs = DefineIfPython2(["range = xrange"])
                tree = defs.visit(tree)
        done = ast.unparse(tree)
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

if __name__ == "__main__":
    from optparse import OptionParser # pylint: disable=deprecated-module
    cmdline = OptionParser("%prog [options] file3.py", description=__doc__.strip())
    cmdline.formatter.max_help_position = 30
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="increase logging level")
    cmdline.add_option("--pyi-version", metavar="3.6", default=NIX, help="set python version for py-includes")
    cmdline.add_option("--python-version", metavar="2.7", default=NIX, help="set python features by version")
    cmdline.add_option("--py36", action="count", default=0, help="keep features available since python3.6")
    cmdline.add_option("--remove-typehints", action="count", default=0, help="3.5 function annotations and cast operator")
    cmdline.add_option("--remove-var-typehints", action="count", default=0, help="only 3.6 variable annotations (for typehints)")
    cmdline.add_option("--remove-keywordonly", action="count", default=0, help="3.0 keywordonly parameters")
    cmdline.add_option("--remove-positionalonly", action="count", default=0, help="3.8 positionalonly parameters")
    cmdline.add_option("--remove-pyi-positionalonly", action="count", default=0, help="3.8 positionalonly parameters in *.pyi")
    cmdline.add_option("--replace-fstring", action="count", default=0, help="3.6 f-strings to string.format")
    cmdline.add_option("--define-range", action="count", default=0, help="3.0 define range() to xrange() iterator")
    cmdline.add_option("-1", "--inplace", action="count", default=0, help="file.py gets overwritten")
    cmdline.add_option("-2", "--append2", action="count", default=0, help="file.py becomes file2.py")
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py becomes file.py")
    cmdline.add_option("-y", "--pyi", action="count", default=0, help="generate file.pyi as well")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, logging.WARNING - 10 * opt.verbose))
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
        REMOVE_PYI_POSITIONAL = True
    if BACK_VERSION < 38 or opt.remove_positionalonly:
        REMOVE_POSITIONAL = True
    if BACK_VERSION < 30 or opt.remove_keywordonly:
        REMOVE_KEYWORDONLY = True
    if BACK_VERSION < 36 or opt.remove_typehints or opt.remove_var_typehints:
        REMOVE_VAR_TYPEHINTS = True
    if BACK_VERSION < 35 or opt.remove_typehints:
        REMOVE_TYPEHINTS = True
    if BACK_VERSION < 36 or opt.replace_fstring:
        REPLACE_FSTRING = True
        if opt.replace_fstring > 1:
            FSTRING_NUMBERED = True
    if BACK_VERSION < 30 or opt.define_range:
        DEFINE_RANGE = True
    _EACHFILE = EACH_REMOVE3 if opt.remove3 else 0
    _EACHFILE |= EACH_APPEND2 if opt.append2 else 0
    _EACHFILE |= EACH_INPLACE if opt.inplace else 0
    sys.exit(main(cmdline_args, eachfile=_EACHFILE, outfile=opt.outfile, pyi=opt.pyi))
