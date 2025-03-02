#! /usr/bin/env python3.11
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
""" easy way to transform and remove python3 typehints """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "0.1.1087"

from typing import List, Optional
# import ast
import ast_comments as ast
import os
import os.path as fs
import sys
import logging

# PEP3102 (python 3.0) = keyword-only args
# PEP484 (python3.5) = typehints introduced
# (python3.12) = type() statement
# (python3.12) = support for generics
# PEP675 (python3.11) = LiteralString
# (python3.6) = NoReturn
# (python3.11) = Never, Self
# (python3.10) = a|b as union
# (python3.5) = ClassVar
# (python3.8) = Final
# PEP593 (python3.9) = Annotated
# PEP526 (python3.6) = variable annotations
# (python3.8) = Protocol
# (python3.11) = assert_type
# (python3.5) = is.TYPE_CHECKING
# PEP3107 (python3.0) = function annotations

logg = logging.getLogger(__name__.replace("/", "."))

OK = True
NIX = ""
BACK = 27
KEEPTYPES = False

class StripHints(ast.NodeTransformer):
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if BACK >= 35 and KEEPTYPES:
            return node
        imports: ast.ImportFrom = node
        logg.debug("-imports: %s", ast.dump(imports))
        if imports.module != "typing":
            return node # unchanged
        return None
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if BACK >= 30 and KEEPTYPES:
            return self.generic_visit(node)
        calls: ast.Call = node
        logg.debug("-calls: %s", ast.dump(calls))
        if calls.func != "cast":
            return node # unchanged
        if len(calls.args) > 1:
            return self.generic_visit(calls.args[1])
        logg.error("-bad cast: %s", ast.dump(node))
        return ast.Constant(None)
    def visit_AnnAssign(self, node: ast.AnnAssign) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if BACK >= 36 and KEEPTYPES:
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
                if BACK <= 30:
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
                if BACK <= 30:
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
        if func.args.kw_defaults and BACK < 30:
            old += 1
        if not annos and not func.returns and not old:
            return self.generic_visit(node) # unchanged
        if OK:
            for exp in func.args.defaults:
                defaults.append(exp)
        if OK:
            for kwexp in func.args.kw_defaults:
                if BACK < 30:
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
                if isinstance(child, ast.AnnAssign):
                    assign1: ast.AnnAssign = child
                    logg.debug("assign: %s", ast.dump(assign1))
                    if assign1.value is not None:
                        assign2 = ast.Assign(targets=[assign1.target], value=assign1.value)
                        assign2.lineno = assign1.lineno
                        body.append(assign2)
                    else:
                        logg.debug("skip simple")
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
                            if assign.value is not None:
                                assign2 = ast.Assign(targets=[assign.target], value=assign.value)
                                assign2.lineno = assign.lineno
                                stmt.append(assign2)
                            else:
                                logg.debug("skip simple")
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
                                    if BACK < 30:
                                        functionargs.append(ast.arg(arg.arg))
                                    else:
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
                                    if BACK < 30:
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
                            if not annos and not func.returns:
                                stmt.append(func)
                            else:
                                logg.debug("args: %s", ast.dump(func.args))
                                args2 = ast.arguments(posonlyargs, functionargs, vargarg, kwonlyargs, # ..
                                        func.args.kw_defaults, kwarg, func.args.defaults)
                                func2 = ast.FunctionDef(func.name, args2, func.body, func.decorator_list)
                                func2.lineno = func.lineno
                                stmt.append(func2)
                                func3 = ast.FunctionDef(func.name, func.args, [ast.Pass()], func.decorator_list, func.returns)
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

def main(args: List[str], remove3: int = 0, append2: int = 0, outfile: str = "", pyi: int = 0) -> int:
    written: List[str] = []
    for arg in args:
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
        tree1 = ast.parse(text, type_comments=True)
        types = TypeHints()
        tree2 = types.visit(tree1)
        strip = StripHints()
        tree3 = strip.visit(tree2)
        done = ast.unparse(tree3)
        if outfile:
            out = outfile
        elif arg.endswith("3.py") and remove3:
            out = arg[:-len("3.py")]+".py"
        elif arg.endswith(".py") and append2:
            out = arg[:-len(".py")]+"_2.py"
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
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="increase logging level")
    cmdline.add_option("--python-version", metavar="2.7", default=NIX, help="set features by version")
    cmdline.add_option("--py36", action="count", default=0, help="keep features available since python3.6")
    cmdline.add_option("-2", "--append2", action="count", default=0, help="file.py becomes file2.py")
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py becomes file.py")
    cmdline.add_option("-y", "--pyi", action="count", default=0, help="generate file.pyi as well")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, logging.WARNING - 10 * opt.verbose))
    if opt.py36:
        BACK = 36
    elif opt.python_version:
        if len(opt.python_version) >= 3 and opt.python_version[1] == ".":
            BACK = int(opt.python_version[0]) * 10 + int(opt.python_version[2:])
        else:
            logg.error("unknown --python-version %s", opt.python_version)
    sys.exit(main(cmdline_args, remove3=opt.remove3, append2=opt.append2, outfile=opt.outfile, pyi=opt.pyi))
