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


logg = logging.getLogger(__name__.replace("/", "."))

OK = True
NIX = ""

class StripHints(ast.NodeTransformer):
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.ImportFrom = node
        logg.debug("-imports: %s", ast.dump(imports))
        if imports.module != "typing":
            return node # unchanged
        return None
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        calls: ast.Call = node
        logg.debug("-calls: %s", ast.dump(calls))
        if calls.func != "cast":
            return node # unchanged
        if len(calls.args) > 1:
            return self.generic_visit(calls.args[1])
        logg.error("-bad cast: %s", ast.dump(node))
        return ast.Constant(None)
    def visit_AnnAssign(self, node: ast.AnnAssign) -> Optional[ast.AST]:  # pylint: disable=invalid-name
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
        vargarg = func.args.vararg
        if OK:
            for arg in func.args.posonlyargs:
                logg.debug("-pos arg: %s", ast.dump(arg))
                posonlyargs.append(ast.arg(arg.arg))
                if arg.annotation: 
                    annos += 1
        if OK:
            for arg in func.args.args:
                logg.debug("-fun arg: %s", ast.dump(arg))
                functionargs.append(ast.arg(arg.arg))
                if arg.annotation: 
                    annos += 1
        if vargarg is not None:
            if vargarg.annotation:
                annos += 1
            vargarg = ast.arg(vargarg.arg)
        if not annos and not func.returns:
            return self.generic_visit(node) # unchanged
        args2 = ast.arguments(posonlyargs, functionargs, vargarg, # ..
            func.args.kwonlyargs, func.args.kw_defaults, func.args.kwarg, func.args.defaults)
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
                    assign: ast.AnnAssign = child
                    logg.debug("assign: %s", ast.dump(assign))
                    if assign.value is not None:
                        assign2 = ast.Assign(targets=[assign.target], value=assign.value)
                        assign2.lineno = assign.lineno
                        body.append(assign2)
                    else:
                        logg.debug("skip simple")
                    assign3 = ast.AnnAssign(target=assign.target, annotation=assign.annotation, value=None, simple=assign.simple)
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
                            vargarg = func.args.vararg
                            for arg in func.args.posonlyargs:
                                logg.debug("pos arg: %s", ast.dump(arg))
                                posonlyargs.append(ast.arg(arg.arg))
                                if arg.annotation: 
                                    annos += 1
                            for arg in func.args.args:
                                logg.debug("fun arg: %s", ast.dump(arg))
                                functionargs.append(ast.arg(arg.arg))
                                if arg.annotation: 
                                    annos += 1
                            if vargarg is not None:
                                if vargarg.annotation:
                                    annos += 1
                                vargarg = ast.arg(vargarg.arg)
                            if not annos and not func.returns:
                                stmt.append(func)
                            else:
                                logg.debug("args: %s", ast.dump(func.args))
                                args2 = ast.arguments(posonlyargs, functionargs, vargarg, # ..
                                        func.args.kwonlyargs, func.args.kw_defaults, func.args.kwarg, func.args.defaults)
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

def main(args: List[str], remove3: int = 0, outfile: str = "", pyi: int = 0) -> int:
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
        elif arg.endswith(".py"):
            out = arg[:-len(".py")]+"_2.py"
        if OK:
            with open(out, "w", encoding="utf-8") as w:
                w.write(done)
                if done and not done.endswith("\n"):
                    w.write("\n")
            logg.info("written %s", out)
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
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py becomes file.py")
    cmdline.add_option("-y", "--pyi", action="count", default=0, help="generate file.pyi as well")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, logging.WARNING - 10 * opt.verbose))
    sys.exit(main(cmdline_args, remove3=opt.remove3, outfile=opt.outfile, pyi=opt.pyi))
