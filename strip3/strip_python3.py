#! /usr/bin/env python3.11
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,no-else-return,line-too-long,too-many-lines,too-many-arguments
# pylint: disable=too-many-instance-attributes,too-few-public-methods,too-many-branches,too-many-locals,too-many-nested-blocks,too-many-statements
# pylint: disable=wrong-import-order,wrong-import-position,use-list-literal,use-dict-literal
""" easy way to transform and remove python3 typehints """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "1.3.1287"

from typing import Set, List, Dict, Optional, Union, Tuple, cast, NamedTuple, TypeVar, Deque, Iterable, TYPE_CHECKING
import sys
import re
import os
import os.path as fs
import configparser
import logging
from collections import deque, OrderedDict
if sys.version_info >= (3,11,0):
    import tomllib
else:  # pragma: nocover
    try:
        import tomli as tomllib # type: ignore[no-redef,import-untyped]
    except ImportError:
        try:
            import qtoml_decoder as tomllib # type: ignore[no-redef,import-untyped]
        except ImportError:
            tomllib = None # type: ignore[assignment]
DEBUG_TOML = logging.DEBUG
DEBUG_TYPING = logging.DEBUG
DEBUG_COPY = logging.INFO
NIX = ""
OK = True

NOTE = (logging.INFO + logging.WARNING) // 2
HINT = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(HINT, "HINT")
logg = logging.getLogger("strip" if __name__ == "__main__" else __name__.replace("/", "."))

if sys.version_info < (3,9,0): # pragma: nocover
    logg.info("python3.9 has ast.unparse()")
    logg.fatal("you need alteast python3.9 to run strip-python3!")
    sys.exit(os.EX_SOFTWARE)

# ........
import ast
if TYPE_CHECKING:
    from ast import parse, unparse
try:
    from ast_comments import parse, unparse, Comment # type: ignore[no-redef,import-untyped] # pylint: disable=wrong-import-position
except ImportError:
    # required for unittest.py
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    try:
        from ast_comments import parse, unparse, Comment # type: ignore[no-redef,import-untyped] # pylint: disable=wrong-import-position
    except ImportError:
        class Comment(ast.Expr): # type: ignore[no-redef]
            pass

from ast import TypeIgnore

TypeAST = TypeVar("TypeAST", bound=ast.AST) # pylint: disable=invalid-name
def copy_location(new_node: TypeAST, old_node: ast.AST) -> TypeAST:
    """ similar to ast.copy_location """
    if hasattr(old_node, "lineno") and hasattr(old_node, "end_lineno"):
        setattr(new_node, "lineno", old_node.lineno)
        setattr(new_node, "end_lineno", old_node.end_lineno)
    return new_node

class TransformerSyntaxError(SyntaxError):
    pass

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
#         (python 3.6) NamedTuple classes with member annotations (3.5 had call-syntax)
# PEP 563 (python 3.7) delayed typehints for "SelfClass" (from __future__ 3.10)
# ....... (Pyhton 3.7) Generics
# PEP 572 (python 3.8) walrus operator
# PEP 570 (python 3.8) positional-only params
# ....... (python 3.8) f-strings "{varname=}"
# PEP 591 (python 3.8) @final decorator
# PEP 589 (python 3.8) TypeDict classes with member annotations (extended in 3.11 PEP 655)
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
# PEP 695 (python 3.12) compact generics syntax and "type" statements
# PEP 692 (python 3.12) TypedDict und Unpack
# PEP 698 (python 3.12) @override decorator
#         (python 3.12) warning on ast.Num ast.Str ast.Bytes ast.NameConstant ast.Ellipsis (replaced by ast.Constant in 3.8)

str_to_int_0 = ("n", "no", "false", "False", "na", "NA")
str_to_int_1 = ("y", "yes", "true", "True", "ok", "OK")
str_to_int_2 = ("x", "xtra", "more", "high", "hi", "HI")
def to_int(x: Union[int, str, None], default: int = 0) -> int:
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        if x.isdigit():
            return int(x)
        if x in str_to_int_0:
            return 0
        if x in str_to_int_1:
            return 1
        if x in str_to_int_2:
            return 2
    return default

class Want:
    show_dump = 0
    fstring_numbered = to_int(os.environ.get("PYTHON3_FSTRING_NUMBERED", NIX))
    remove_var_typehints = to_int(os.environ.get("PYTHON3_REMOVE_VAR_TYPEHINTS", NIX))
    remove_typehints = to_int(os.environ.get("PYTHON3_REMOVE_TYPEHINTS", NIX))
    remove_keywordonly = to_int(os.environ.get("PYTHON3_REMOVE_KEYWORDSONLY", NIX))
    remove_positional = to_int(os.environ.get("PYTHON3_REMOVE_POSITIONAL", NIX))
    remove_positional_pyi = to_int(os.environ.get("PYTHON3_REMOVE_POSITIONAL_PYI", NIX))
    fstring_from_locals_format = to_int(os.environ.get("PYTHON3_FSTRING_FROM_LOCALS_FORMAT", NIX))
    fstring_from_var_locals_format = to_int(os.environ.get("PYTHON3_FSTRING_FROM_VAR_LOCALS_FORMAT", NIX))
    replace_fstring = to_int(os.environ.get("PYTHON3_REPLACE_FSTRING", NIX))
    replace_namedtuple_class = to_int(os.environ.get("PYTHON3_REPLACE_NAMEDTUPLE_CLASS", NIX))
    replace_typeddict_class = to_int(os.environ.get("PYTHON3_REPLACE_TYPEDDICT_CLASS", NIX))
    replace_typeddict_pyi = to_int(os.environ.get("PYTHON3_REPLACE_TYPEDDICT_PYI", NIX))
    replace_walrus_operator = to_int(os.environ.get("PYTHON3_REPLACE_WALRUS_OPERATOR", NIX))
    replace_annotated_typing = to_int(os.environ.get("PYTHON3_REPLACE_ANNOTATED_TYPING", NIX))
    replace_builtin_typing = to_int(os.environ.get("PYTHON3_REPLACE_ANNOTATED_TYPING", NIX))
    replace_union_typing = to_int(os.environ.get("PYTHON3_REPLACE_UNION_TYPING", NIX))
    replace_self_typing = to_int(os.environ.get("PYTHON3_REPLACE_SELF_TYPING", NIX))
    define_range = to_int(os.environ.get("PYTHON3_DEFINE_RANGE", NIX))
    define_basestring =to_int(os.environ.get("PYTHON3_DEFINE_BASESTRING", NIX))
    define_callable = to_int(os.environ.get("PYTHON3_DEFINE_CALLABLE", NIX))
    define_print_function = to_int(os.environ.get("PYTHON3_DEFINE_PRINT_FUNCTION", NIX))
    define_float_division = to_int(os.environ.get("PYTHON3_DEFINE_FLOAT_DIVISION", NIX))
    define_absolute_import = to_int(os.environ.get("PYTHON3_DEFINE_ABSOLUTE_IMPORT", NIX))
    datetime_fromisoformat = to_int(os.environ.get("PYTHON3_DATETIME_FROMISOFORMAT", NIX))
    subprocess_run = to_int(os.environ.get("PYTHON3_SUBPROCESS_RUN", NIX))
    time_monotonic = to_int(os.environ.get("PYTHON3_TIME_MONOTONIC", NIX))
    time_monotonic_ns = to_int(os.environ.get("PYTHON3_TIME_MONOTONIC_NS", os.environ.get("PYTHON3_TIME_MONOTONIC", NIX)))
    import_pathlib2 = to_int(os.environ.get("PYTHON3_IMPORT_PATHLIB2", NIX))
    import_backports_zoneinfo = to_int(os.environ.get("PYTHON3_IMPORT_BACKBORTS_ZONEINFO", NIX))
    import_toml = to_int(os.environ.get("PYTHON3_IMPORT_TOML", NIX))
    setup_cfg =  os.environ.get("PYTHON3_CONFIGFILE", "setup.cfg")
    pyproject_toml = "pyproject.toml"
    toolsection = "strip-python3"
    run_python = os.environ.get("PYTHON3_RUN_PYTHON", NIX)
    no_comments = to_int(os.environ.get("PYTHON3_NO_COMMENTS", NIX))
    no_unparser = to_int(os.environ.get("PYTHON3_NO_UNPARSER", NIX))

want = Want()

def ast_parse(text: str) -> ast.Module:
    if want.no_comments:
        return ast.parse(text)
    else:
        return parse(text)

def ast_unparse(tree: ast.AST) -> str:
    if want.no_unparser:
        return ast.unparse(tree)
    else:
        return unparse(tree)

from optparse import OptionParser # pylint: disable=deprecated-module

def main() -> int:
    # global want
    # defs = read_defaults("pyproject.toml", "setup.cfg")
    cmdline = OptionParser("%prog [options] file3.py", description=__doc__.strip(), epilog=": -o - : default is to print the type-stripped and back-transformed py code")
    cmdline.formatter.max_help_position = 37
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="more logging")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="less logging")
    cmdline.add_option("-?", "--version", action="count", default=0, help="show version info")
    cmdline.add_option("--no-define-range", action="count", default=00, help="3.0 define range()")
    cmdline.add_option("--no-define-basestring", action="count", default=0, help="3.0 isinstance(str)")
    cmdline.add_option("--no-define-callable", "--noc", action="count", default=0, help="3.2 callable(x)")
    cmdline.add_option("--no-define-print-function", "--nop", action="count", default=0, help="3.0 print() function")
    cmdline.add_option("--no-define-float-division", "--nod", action="count", default=0, help="3.0 float division")
    cmdline.add_option("--no-define-absolute-import", action="count", default=0, help="3.0 absolute import")
    cmdline.add_option("--no-datetime-fromisoformat", action="count", default=0, help="3.7 datetime.fromisoformat")
    cmdline.add_option("--no-subprocess-run", action="count", default=0, help="3.5 subprocess.run")
    cmdline.add_option("--no-time-monotonic", action="count", default=0, help="3.3 time.monotonic")
    cmdline.add_option("--no-time-monotonic-ns", action="count", default=0, help="3.7 time.monotonic_ns")
    cmdline.add_option("--no-import-pathlib2", action="count", default=0, help="3.3 pathlib to python2 pathlib2")
    cmdline.add_option("--no-import-backports-zoneinfo", action="count", default=0, help="3.9 zoneinfo from backports")
    cmdline.add_option("--no-import-toml", action="count", default=0, help="3.11 tomllib to external toml")
    cmdline.add_option("--no-replace-fstring", action="count", default=0, help="3.6 f-strings")
    cmdline.add_option("--no-replace-namedtuple-class", action="count", default=0, help="3.6 NamedTuple class")
    cmdline.add_option("--no-replace-typeddict-class", action="count", default=0, help="3.8 TypeDict class")
    cmdline.add_option("--no-replace-typeddict-pyi", action="count", default=0, help="3.8 TypeDict class (in pyi)")
    cmdline.add_option("--no-replace-walrus-operator", action="count", default=0, help="3.8 walrus-operator")
    cmdline.add_option("--no-replace-annotated-typing", action="count", default=0, help="3.9 Annotated[int, x] (in pyi)")
    cmdline.add_option("--no-replace-builtin-typing", action="count", default=0, help="3.9 list[int] (in pyi)")
    cmdline.add_option("--no-replace-union-typing", action="count", default=0, help="3.10 int|str (in pyi)")
    cmdline.add_option("--no-replace-self-typing", action="count", default=0, help="3.11 Self (in pyi)")
    cmdline.add_option("--no-remove-keywordonly", action="count", default=0, help="3.0 keywordonly parameters")
    cmdline.add_option("--no-remove-positionalonly", action="count", default=0, help="3.8 positionalonly parameters")
    cmdline.add_option("--no-remove-positional-pyi", action="count", default=0, help="3.8 positionalonly in *.pyi")
    cmdline.add_option("--define-range", action="count", default=0, help="3.0 define range() to xrange() iterator")
    cmdline.add_option("--define-basestring", action="count", default=0, help="3.0 isinstance(str) is basestring python2")
    cmdline.add_option("--define-callable", action="count", default=0, help="3.2 callable(x) as in python2")
    cmdline.add_option("--define-print-function", action="count", default=0, help="3.0 print() or from __future__")
    cmdline.add_option("--define-float-division", action="count", default=0, help="3.0 float division or from __future__")
    cmdline.add_option("--define-absolute-import", action="count", default=0, help="3.0 absolute import or from __future__")
    cmdline.add_option("--datetime-fromisoformat", action="count", default=0, help="3.7 datetime.fromisoformat or boilerplate")
    cmdline.add_option("--subprocess-run", action="count", default=0, help="3.5 subprocess.run or use boilerplate")
    cmdline.add_option("--time-monotonic", action="count", default=0, help="3.3 time.monotonic or use time.time")
    cmdline.add_option("--time-monotonic-ns", action="count", default=0, help="3.7 time.monotonic_ns or use time.time")
    cmdline.add_option("--import-pathlib2", action="count", default=0, help="3.3 import pathlib2 as pathlib")
    cmdline.add_option("--import-backports-zoneinfo", action="count", default=0, help="3.9 import zoneinfo from backports")
    cmdline.add_option("--import-toml", action="count", default=0, help="3.11 import toml as tomllib")
    cmdline.add_option("--replace-fstring", action="count", default=0, help="3.6 f-strings to string.format")
    cmdline.add_option("--replace-namedtuple-class", action="count", default=0, help="3.6 NamedTuple to collections.namedtuple")
    cmdline.add_option("--replace-typeddict-class", action="count", default=0, help="3.8 TypedDict to builtin dict")
    cmdline.add_option("--replace-typeddict-pyi", action="count", default=0, help="3.8 TypedDict to builtin dict in *.pyi")
    cmdline.add_option("--replace-walrus-operator", action="count", default=0, help="3.8 walrus 'if x := ():' to 'if x:'")
    cmdline.add_option("--replace-annotated-typing", action="count", default=0, help="3.9 Annotated[int, x] converted to int")
    cmdline.add_option("--replace-builtin-typing", action="count", default=0, help="3.9 list[int] converted to List[int]")
    cmdline.add_option("--replace-union-typing", action="count", default=0, help="3.10 int|str converted to Union[int,str]")
    cmdline.add_option("--replace-self-typing", action="count", default=0, help="3.11 Self converted to SelfClass TypeVar")
    cmdline.add_option("--remove-typehints", action="count", default=0, help="3.5 function annotations and cast()")
    cmdline.add_option("--remove-keywordonly", action="count", default=0, help="3.0 keywordonly parameters")
    cmdline.add_option("--remove-positionalonly", action="count", default=0, help="3.8 positionalonly parameters")
    cmdline.add_option("--remove-positional-pyi", action="count", default=0, help="3.8 positional parameters in *.pyi")
    cmdline.add_option("--remove-var-typehints", action="count", default=0, help="only 3.6 variable annotations (typehints)")
    cmdline.add_option("-u", "--upgrade", action="count", default=0, help="allow upgrade transformers:")
    cmdline.add_option("--fstring-from-locals-format", action="count", default=0, help="replace idiom '{name}'.format(**locals())")
    cmdline.add_option("--fstring-from-var-locals-format", action="count", default=0, help="and for x='{name}'; x.format(**locals())")
    cmdline.add_option("--no-comments", action="count", default=0, help="do not use ast_comments to parse")
    cmdline.add_option("--bare", action="count", default=0, help="do not use ast_comments (parse/unparse)")
    cmdline.add_option("--show", action="count", default=0, help="show transformer settings (from above)")
    cmdline.add_option("--pretty", action="count", default=0, help="no transformers (based on python-version)")
    cmdline.add_option("--pyi-version", metavar="3.6", default=NIX, help="set python version for py-includes")
    cmdline.add_option("--python-version", metavar="2.7", default=NIX, help="set python features by version")
    cmdline.add_option("--run-python", metavar="exe", default=NIX, help="replace shebang with #! /usr/bin/env exe")
    cmdline.add_option("-O", "--old-python", action="count", default=0, help="replace shebang with /bin/env python")
    cmdline.add_option("-V", "--dump", action="count", default=0, help="show ast tree before (and after) changes")
    cmdline.add_option("-0", "--nowrite", action="store_true", default=False, help="suppress writing the transformed file.py")
    cmdline.add_option("-1", "--inplace", action="count", default=0, help="file.py gets overwritten (+ file.pyi)")
    cmdline.add_option("-2", "--append2", action="count", default=0, help="file.py into file_2.py + file_2.pyi")
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py into file.py + file.pyi")
    cmdline.add_option("-6", "--py36", action="count", default=0, help="alias --no-make-pyi --python-version=3.6")
    cmdline.add_option("-7", "--pyi37", action="count", default=0, help="alias --pyi-version=3.7")
    cmdline.add_option("-9", "--py39", action="count", default=0, help="alias --no-make-pyi --python-version=3.9")
    cmdline.add_option("-Y", "--make-stubs", "--stubs", action="count", default=0, help="generate file-stubs/__init__.pyi for mypy")
    cmdline.add_option("-y", "--make-pyi", "--pyi", action="count", default=0, help="generate file.pyi includes as well")
    cmdline.add_option("-n", "--no-make-pyi", "--no-pyi", action="count", default=0, help="do not generate any pyi includes")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    cmdline_set_defaults_from(cmdline, want.toolsection, want.pyproject_toml, want.setup_cfg)
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, NOTE - 5 * opt.verbose + 10 * opt.quiet))
    if opt.version:
        print(F"version: {__version__}")
        print(F"author: {__author__}")
        if opt.version > 1:
            print(F"copyright: {__copyright__}")
            print("module: "+ os.path.basename(__file__))
    if opt.run_python:
        want.run_python = opt.run_python
    elif opt.old_python:
        want.run_python = "python"
    no_make_pyi = opt.no_make_pyi
    pyi_version = (3,8)
    if opt.pyi37:
        pyi_version = (3, 7)
    elif opt.pyi_version:
        if len(opt.pyi_version) >= 3 and opt.pyi_version[1] == ".":
            pyi_version = int(opt.pyi_version[0]), int(opt.pyi_version[2:])
        else:
            logg.error("can not decode --pyi-version %s", opt.pyi_version)
    py_version = (2,7)
    if opt.py36:
        py_version = (3,6)
        no_make_pyi = True
    elif opt.py39:
        py_version = (3,9)
        no_make_pyi = True
    elif opt.python_version:
        if len(opt.python_version) >= 3 and opt.python_version[1] == ".":
            py_version = int(opt.python_version[0]), int(opt.python_version[2:])
        else:
            logg.error("can not decode --python-version %s", opt.python_version)
    upgrade_version = py_version if opt.upgrade else (0, 0)
    back_version = py_version if not opt.pretty else (8, 8)
    logg.debug("back %s py_version %s pyi_version %s", back_version, py_version, pyi_version)
    if opt.pretty:
        back_version = (9, 9)
        upgrade_version = (0, 0)
    if pyi_version < (3,8) or opt.remove_positional_pyi:
        if not opt.no_remove_positional_pyi:
            want.remove_positional_pyi = max(1, opt.remove_positional_pyi)
    if back_version < (3,8) or opt.remove_positionalonly:
        if not opt.no_remove_positionalonly:
            want.remove_positional = max(1, opt.remove_positionalonly)
    if back_version < (3,0) or opt.remove_keywordonly:
        if not opt.no_remove_keywordonly:
            want.remove_keywordonly = max(1, opt.remove_keywordonly)
    if back_version < (3,6) or opt.remove_typehints or opt.remove_var_typehints:
        want.remove_var_typehints = max(1,opt.remove_typehints,opt.remove_var_typehints)
    if back_version < (3,5) or opt.remove_typehints:
        want.remove_typehints = max(1,opt.remove_typehints)
    if back_version < (3,9) or opt.replace_builtin_typing:
        if not opt.no_replace_builtin_typing:
            want.replace_builtin_typing = max(1,opt.replace_builtin_typing)
    if back_version < (3,9) or opt.replace_annotated_typing:
        if not opt.no_replace_annotated_typing:
            want.replace_annotated_typing = max(1,opt.replace_annotated_typing)
    if back_version < (3,10) or opt.replace_union_typing:
        if not opt.no_replace_union_typing:
            want.replace_union_typing = max(1,opt.replace_union_typing)
    if back_version < (3,11) or opt.replace_self_typing:
        if not opt.no_replace_self_typing:
            want.replace_self_typing = max(1,opt.replace_self_typing)
    if back_version < (3,6) or opt.replace_fstring:
        if not opt.no_replace_fstring:
            want.replace_fstring = max(1, opt.replace_fstring)
            if want.replace_fstring > 1:
                want.fstring_numbered = 1
    if back_version < (3,6) or opt.replace_namedtuple_class:
        if not opt.no_replace_namedtuple_class:
            want.replace_namedtuple_class = max(1, opt.replace_namedtuple_class)
    if back_version < (3,8) or opt.replace_typeddict_class:
        if not opt.no_replace_typeddict_class:
            want.replace_typeddict_class = max(1, opt.replace_typeddict_class)
    if pyi_version < (3,8) or opt.replace_typeddict_pyi:
        if not opt.no_replace_typeddict_pyi:
            want.replace_typeddict_pyi = max(1, opt.replace_typeddict_pyi)
    if back_version < (3,8) or opt.replace_walrus_operator:
        if not opt.no_replace_walrus_operator:
            want.replace_walrus_operator = max(1, opt.replace_walrus_operator)
    if back_version < (3,0) or opt.define_range:
        if not opt.no_define_range:
            want.define_range = max(1,opt.define_range)
    if back_version < (3,0) or opt.define_basestring:
        if not opt.no_define_basestring:
            want.define_basestring = max(1, opt.define_basestring)
    if back_version < (3,2) or opt.define_callable:
        if not opt.no_define_callable:
            want.define_callable = max(1, opt.define_callable)
    if back_version < (3,0) or opt.define_print_function:
        if not opt.no_define_print_function:
            want.define_print_function = max(1, opt.define_print_function)
    if back_version < (3,0) or opt.define_float_division:
        if not opt.no_define_float_division:
            want.define_float_division = max(1,opt.define_float_division)
    if back_version < (3,0) or opt.define_absolute_import:
        if not opt.no_define_absolute_import:
            want.define_absolute_import = max(1, opt.define_absolute_import)
    if back_version < (3,7) or opt.datetime_fromisoformat:
        if not opt.no_datetime_fromisoformat:
            want.datetime_fromisoformat = max(1,opt.datetime_fromisoformat)
    if back_version < (3,5) or opt.subprocess_run:
        if not opt.no_subprocess_run:
            want.subprocess_run = max(1,opt.subprocess_run)
    if back_version < (3,3) or opt.time_monotonic:
        if not opt.no_time_monotonic:
            want.time_monotonic = max(1, opt.time_monotonic)
    if back_version < (3,7) or opt.time_monotonic_ns or opt.time_monotonic:
        if not opt.no_time_monotonic_ns:
            want.time_monotonic_ns = max(1, opt.time_monotonic_ns)
    if back_version < (3,3) or opt.import_pathlib2:
        if not opt.no_import_pathlib2:
            want.import_pathlib2 = max(1, opt.import_pathlib2)
    if back_version < (3,9) or opt.import_backports_zoneinfo:
        if not opt.no_import_backports_zoneinfo:
            want.import_backports_zoneinfo = max(1, opt.import_backports_zoneinfo)
    if back_version < (3,11) or opt.import_toml:
        if not opt.no_import_toml:
            want.import_toml = max(1, opt.import_toml)
    if upgrade_version >= (3, 6) or opt.fstring_from_locals_format:
        want.fstring_from_locals_format = max(1, opt.fstring_from_locals_format)
    if upgrade_version >= (3, 6) or opt.fstring_from_var_locals_format:
        want.fstring_from_var_locals_format = max(1, opt.fstring_from_var_locals_format)
    if opt.no_comments:
        want.no_comments = opt.no_comments
    if opt.bare:
        want.no_comments = opt.bare
        want.no_unparser = opt.bare
    if opt.show:
        logg.log(NOTE, "%s = %s", "python-version-int", py_version)
        logg.log(NOTE, "%s = %s", "pyi-version-int", pyi_version)
        logg.log(NOTE, "%s = %s", "define-basestring", want.define_basestring)
        logg.log(NOTE, "%s = %s", "define-range", want.define_range)
        logg.log(NOTE, "%s = %s", "define-callable", want.define_callable)
        logg.log(NOTE, "%s = %s", "define-print-function", want.define_print_function)
        logg.log(NOTE, "%s = %s", "define-float-division", want.define_float_division)
        logg.log(NOTE, "%s = %s", "define-absolute-import", want.define_absolute_import)
        logg.log(NOTE, "%s = %s", "replace-fstring", want.replace_fstring)
        logg.log(NOTE, "%s = %s", "remove-keywordsonly", want.remove_keywordonly)
        logg.log(NOTE, "%s = %s", "remove-positionalonly", want.remove_positional)
        logg.log(NOTE, "%s = %s", "remove-positional-pyi", want.remove_positional_pyi)
        logg.log(NOTE, "%s = %s", "remove-var-typehints", want.remove_var_typehints)
        logg.log(NOTE, "%s = %s", "remove-typehints", want.remove_typehints)
    if opt.dump:
        want.show_dump = int(opt.dump)
    eachfile = EACH_REMOVE3 if opt.remove3 else 0
    eachfile |= EACH_APPEND2 if opt.append2 else 0
    eachfile |= EACH_INPLACE if opt.inplace else 0
    make_pyi = opt.make_pyi or opt.append2 or opt.remove3 or opt.inplace
    return transformfiles(cmdline_args, eachfile=eachfile, outfile=opt.outfile, nowrite=opt.nowrite,
        pyi = "i" if make_pyi and not no_make_pyi else NIX, stubs = "*-stubs/__init__.pyi" if opt.make_stubs and not no_make_pyi else NIX,
        minversion=py_version, run_python=want.run_python)

def cmdline_set_defaults_from(cmdline: OptionParser, toolsection: str, *files: str) -> Dict[str, Union[str, int]]:
    defnames: Dict[str, str] = OrderedDict()
    defaults: Dict[str, Union[str, int]] = {}
    for opt in cmdline.option_list:
        opt_string = opt.get_opt_string()
        if opt_string.startswith("--") and opt.dest is not None:
            opt_default = opt.default
            if isinstance(opt_default, (int, str)):
                defnames[opt_string[2:]] = opt.dest
                defaults[opt_string[2:]] = opt_default
    settings: Dict[str, Union[str, int]] = {}
    for configfile in files:
        if fs.isfile(configfile):
            if configfile.endswith(".toml") and tomllib:
                logg.log(DEBUG_TOML, "found toml configfile %s", configfile)
                with open(configfile, "rb") as f:
                    conf = tomllib.load(f)
                    section1: Dict[str, Union[str, int, bool]] = {}
                    if "tool" in conf and toolsection in conf["tool"]:
                        section1 = conf["tool"][toolsection]
                    else:
                        logg.log(DEBUG_TOML, "have sections %s", list(section1.keys()))
                    if section1:
                        logg.log(DEBUG_TOML, "have section1 data:\n%s", section1)
                        for setting in sorted(section1):
                            if setting in defnames:
                                destname = defnames[setting]
                                oldvalue = defaults[setting]
                                setvalue = section1[setting]
                                assert destname is not None
                                if isinstance(oldvalue, int):
                                    if isinstance(setvalue, (int, float, bool)):
                                        settings[destname] = int(setvalue)
                                    else:
                                        if setvalue not in str_to_int_0+str_to_int_1+str_to_int_2:
                                            logg.error("%s[%s]: expecting int but found %s", configfile, setting, type(setvalue))
                                        settings[destname] = to_int(setvalue)
                                else:
                                    if not isinstance(oldvalue, str):
                                        logg.warning("%s[%s]: expecting str but found %s", configfile, setting, type(setvalue))
                                    settings[destname] = str(setvalue)
                            else:
                                logg.error("%s[%s]: unknown setting found", configfile, setting)
                                logg.debug("%s: known options are %s", configfile, ", ".join(settings.keys()))
            elif configfile.endswith(".cfg"):
                logg.log(DEBUG_TOML, "found ini configfile %s", configfile)
                confs = configparser.ConfigParser()
                confs.read(configfile)
                if toolsection in confs:
                    section2 = confs[toolsection]
                    logg.log(DEBUG_TOML, "have section2 data:\n%s", section2)
                    for option in sorted(section2):
                        if OK:
                            if option in defaults:
                                destname = defnames[option]
                                oldvalue = defaults[option]
                                setvalue = section2[option]
                                if isinstance(oldvalue, int):
                                    if setvalue.isdigit():
                                        settings[destname] = int(setvalue)
                                    else:
                                        if setvalue not in str_to_int_0+str_to_int_1+str_to_int_2:
                                            logg.error("%s[%s]: expecting int but found %s", configfile, option, setvalue)
                                        settings[destname] = to_int(setvalue)
                                else:
                                    if not isinstance(oldvalue, str):
                                        logg.warning("%s[%s]: expecting str but found %s", configfile, setting, type(setvalue))
                                    settings[destname] = str(setvalue)
                            else:
                                logg.error("%s[%s]: unknown setting found", configfile, option)
                                logg.debug("%s: known options are %s", configfile, ", ".join(settings.keys()))
            else:
                logg.warning("unknown configfile type found = %s", configfile)
        else:
            logg.log(DEBUG_TOML, "no such configfile found = %s", configfile)
    logg.log(DEBUG_TOML, "settings [%s] %s",toolsection, settings)
    cmdline.set_defaults(**settings)
    return settings

# ........................................................................................................

def text4(content: str) -> str:
    if content.startswith("\n"):
        text = ""
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if not line.strip():
                line = ""
            elif line.startswith(indent):
                line = line[len(indent):]
            text += line + "\n"
        if text.endswith("\n\n"):
            return text[:-1]
        else:
            return text
    else:
        return content

# ........................................................................................................

class BlockTransformer:
    """ only runs visitor on body-elements, storing the latest block head in an attribute """
    def visit(self, node: TypeAST) -> TypeAST:
        """Visit a node."""
        nodes = self.generic_visit2(node, deque())
        for first in nodes:
            return first
        return node
    def visit2(self, node: TypeAST, block: Deque[ast.AST]) -> Iterable[TypeAST]:
        """Visit a node in a block"""
        return self.generic_visit2(node, block)
    def next_body(self, body: List[ast.stmt], block: Deque[ast.AST], part: str = NIX) -> List[ast.stmt]: # pylint: disable=unused-argument
        return body
    def done_body(self, body: List[ast.stmt], block: Deque[ast.AST], part: str = NIX) -> List[ast.stmt]: # pylint: disable=unused-argument
        return body
    def generic_visit2(self, node: TypeAST, block: Deque[ast.AST]) -> Iterable[TypeAST]:
        stmtlist_attributes = ["body", "handlers", "orelse", "finalbody"]
        for part in stmtlist_attributes:
            if hasattr(node, part):
                stmtlist: List[ast.stmt] = cast(List[ast.stmt], getattr(node, part))
                body: List[ast.stmt] = []
                block.appendleft(node)
                for stmt in self.next_body(stmtlist, block, part):
                    method = 'visit2_' + stmt.__class__.__name__
                    visitor = getattr(self, method, self.generic_visit2)
                    result = visitor(stmt, block)
                    for elem in result:
                        body.append(copy_location(elem, stmt))
                setattr(node, part, self.done_body(body, block, part))
                block.popleft()
            # note how the if.expr is ignored by this transformer
        return [node]

class WalrusTransformer(BlockTransformer):
    def visit2_If(self, node: ast.If, block: Deque[ast.AST]) -> Iterable[ast.stmt]:  # pylint: disable=invalid-name,unused-argument
        if isinstance(node.test, ast.NamedExpr):
            test: ast.NamedExpr = node.test
            logg.log(DEBUG_TYPING, "ifwalrus-test: %s", ast.dump(test))
            assign = ast.Assign([test.target], test.value)
            assign = copy_location(assign, node)
            newtest = ast.Name(test.target.id)
            newtest = copy_location(newtest, node)
            node.test = newtest
            return [assign, node]
        elif isinstance(node.test, (ast.Compare, ast.BinOp)):
            test2: Union[ast.Compare, ast.BinOp] = node.test
            if isinstance(test2.left, ast.NamedExpr):
                test = test2.left
                logg.log(DEBUG_TYPING, "ifwalrus-left: %s", ast.dump(test))
                assign = ast.Assign([test.target], test.value)
                assign = copy_location(assign, node)
                newtest = ast.Name(test.target.id)
                newtest = copy_location(newtest, node)
                test2.left = newtest
                return [assign, node]
            elif isinstance(test2, ast.BinOp) and isinstance(test2.right, ast.NamedExpr):
                test = test2.right
                logg.log(DEBUG_TYPING, "ifwalrus-right: %s", ast.dump(test))
                assign = ast.Assign([test.target], test.value)
                assign = copy_location(assign, node)
                newtest = ast.Name(test.target.id)
                newtest = copy_location(newtest, node)
                test2.right = newtest
                return [assign, node]
            elif isinstance(test2, ast.Compare) and isinstance(test2.comparators[0], ast.NamedExpr):
                test = test2.comparators[0]
                logg.log(DEBUG_TYPING, "ifwalrus-compared: %s", ast.dump(test))
                assign = ast.Assign([test.target], test.value)
                assign = copy_location(assign, node)
                newtest = ast.Name(test.target.id)
                newtest = copy_location(newtest, node)
                test2.comparators[0] = newtest
                return [assign, node]
            else:
                logg.log(DEBUG_TYPING, "ifwalrus?: %s", ast.dump(test2))
                return [node]
        else:
            logg.log(DEBUG_TYPING, "ifwalrus-if?: %s", ast.dump(node))
            return [node]

class WhileWalrusTransformer(BlockTransformer):
    def visit2_While(self, node: ast.If, block: Deque[ast.AST]) -> Iterable[ast.stmt]:  # pylint: disable=invalid-name,unused-argument
        if isinstance(node.test, ast.NamedExpr):
            test: ast.NamedExpr = node.test
            logg.log(DEBUG_TYPING, "whwalrus-test: %s", ast.dump(test))
            assign = ast.Assign([test.target], test.value)
            assign = copy_location(assign, node)
            newtest = ast.Name(test.target.id)
            newtest = copy_location(newtest, node)
            newtrue = ast.Constant(True)
            newtrue = copy_location(newtrue, node)
            node.test = newtrue
            oldbody = node.body
            oldelse = node.orelse
            node.body = []
            node.orelse = []
            newif = ast.If(newtest, oldbody, oldelse + [ast.Break()])
            newif = copy_location(newif, node)
            node.body = [assign, newif]
            return [node]
        elif isinstance(node.test, (ast.Compare, ast.BinOp)):
            test2: Union[ast.Compare, ast.BinOp] = node.test
            if isinstance(test2.left, ast.NamedExpr):
                test = test2.left
                logg.log(DEBUG_TYPING, "whwalrus-left: %s", ast.dump(test))
                assign = ast.Assign([test.target], test.value)
                assign = copy_location(assign, node)
                newtest = ast.Name(test.target.id)
                newtest = copy_location(newtest, node)
                test2.left = newtest
                newtrue = ast.Constant(True)
                newtrue = copy_location(newtrue, node)
                node.test = newtrue
                oldbody = node.body
                oldelse = node.orelse
                node.body = []
                node.orelse = []
                newif = ast.If(test2, oldbody, oldelse + [ast.Break()])
                newif = copy_location(newif, node)
                node.body = [assign, newif]
                return [node]
            elif isinstance(test2, ast.BinOp) and isinstance(test2.right, ast.NamedExpr):
                test = test2.right
                logg.log(DEBUG_TYPING, "whwalrus-right: %s", ast.dump(test))
                assign = ast.Assign([test.target], test.value)
                assign = copy_location(assign, node)
                newtest = ast.Name(test.target.id)
                newtest = copy_location(newtest, node)
                test2.right = newtest
                newtrue = ast.Constant(True)
                newtrue = copy_location(newtrue, node)
                node.test = newtrue
                oldbody = node.body
                oldelse = node.orelse
                node.body = []
                node.orelse = []
                newif = ast.If(test2, oldbody, oldelse + [ast.Break()])
                newif = copy_location(newif, node)
                node.body = [assign, newif]
                return [node]
            elif isinstance(test2, ast.Compare) and isinstance(test2.comparators[0], ast.NamedExpr):
                test = test2.comparators[0]
                logg.log(DEBUG_TYPING, "whwalrus-compared: %s", ast.dump(test))
                assign = ast.Assign([test.target], test.value)
                assign = copy_location(assign, node)
                newtest = ast.Name(test.target.id)
                newtest = copy_location(newtest, node)
                test2.comparators[0] = newtest
                newtrue = ast.Constant(True)
                newtrue = copy_location(newtrue, node)
                node.test = newtrue
                oldbody = node.body
                oldelse = node.orelse
                node.body = []
                node.orelse = []
                newif = ast.If(test2, oldbody, oldelse + [ast.Break()])
                newif = copy_location(newif, node)
                node.body = [assign, newif]
                return [node]
            else:
                logg.log(DEBUG_TYPING, "whwalrus?: %s", ast.dump(test2))
                return [node]
        else:
            logg.log(DEBUG_TYPING, "whwalrus-if?: %s", ast.dump(node))
            return [node]

class DetectImportsTransformer(ast.NodeTransformer):
    importfrom: Dict[str, Dict[str, str]]
    imported: Dict[str, str]
    importas: Dict[str, str]
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.importfrom = {}
        self.imported = {}
        self.importas = {}
    def visit_Import(self, node: ast.Import) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.Import = node
        for symbol in imports.names:
            origname = symbol.name
            codename = symbol.name if not symbol.asname else symbol.asname
            self.imported[origname] = codename
            self.importas[codename] = origname
        return self.generic_visit(node)
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.ImportFrom = node
        if imports.module:
            modulename = ("." * imports.level) + imports.module
            if modulename not in self.importfrom:
                self.importfrom[modulename] = {}
            for symbol in imports.names:
                origname = modulename + "." + symbol.name
                codename = symbol.name if not symbol.asname else symbol.asname
                self.imported[origname] = codename
                self.importas[codename] = origname
                if symbol.name not in self.importfrom[modulename]:
                    self.importfrom[modulename][symbol.name] = codename
        return self.generic_visit(node)

class RequireImportFrom:
    require: Dict[str, Optional[str]]
    removes: Dict[str, Optional[str]]
    def __init__(self, require: Iterable[str] = ()) -> None:
        self.require = {}
        self.append(require)
        self.removes = {}
    def removefrom(self, module: str, *symbols: str) -> None:
        for symbol in symbols:
            self.removes[F"{module}.{symbol}"] = None
    def importfrom(self, module: str, *symbols: str) -> None:
        for symbol in symbols:
            self.require[F"{module}.{symbol}"] = None
    def add(self, *require: str) -> None:
        for req in require:
            self.require[req] = None
    def append(self, requires: Iterable[str]) -> None:
        for req in requires:
            self.require[req] = None
    def remove(self, removes: List[str]) -> None:
        for req in removes:
            self.removes[req] = None
    def visit(self, node: ast.AST) -> ast.AST:
        if not self.require and not self.removes:
            return node
        logg.debug("-- import require: %s", self.require)
        logg.debug("-- import removes: %s", self.removes)
        imports = DetectImportsTransformer()
        imports.visit(node)
        newimport: List[str] = []
        anyremove: List[str] = []
        for require in self.require:
            if "." in require:
                library, function = require.split(".", 1)
                if library in imports.importfrom:
                    if function in imports.importfrom[library]:
                        logg.debug("%s already imported", require)
                    else:
                        newimport.append(require)
                else:
                    newimport.append(require)
        for require in self.removes:
            if "." in require:
                library, function = require.split(".", 1)
                if library in imports.importfrom:
                    if function in imports.importfrom[library]:
                        anyremove.append(require)
        if not newimport and not anyremove:
            return node
        if not isinstance(node, ast.Module):
            logg.warning("no module for new imports %s", newimport)
            return node
        module = cast(ast.Module, node)  # type: ignore[redundant-cast]
        body: List[ast.stmt] = []
        done = False
        mods: Dict[str, List[str]] = {}
        for new in newimport:
            mod, func = new.split(".", 1)
            if mod not in mods:
                mods[mod] = []
            mods[mod].append(func)
        rems: Dict[str, List[str]] = {}
        for rem in anyremove:
            mod, func = rem.split(".", 1)
            if mod not in rems:
                rems[mod] = []
            rems[mod].append(func)
        if imports.importfrom:
            body = []
            for stmt in module.body:
                drop = False
                if isinstance(stmt, ast.ImportFrom):
                    importing = cast(ast.ImportFrom, stmt)  # type: ignore[redundant-cast]
                    if importing.module in rems:
                        symbols = [alias for alias in importing.names if alias.name not in rems[importing.module]]
                        if symbols:
                            importing.names = symbols
                        else:
                            drop = True
                if not isinstance(stmt, ast.ImportFrom) and not isinstance(stmt, ast.Import):
                    # find first Import/ImportFrom
                    body.append(stmt)
                elif done:
                    if not drop:
                        body.append(stmt)
                else:
                    for mod, funcs in mods.items():
                        body.append(ast.ImportFrom(mod, [ast.alias(name=func) for func in sorted(funcs)], 0))
                    if not drop:
                        body.append(stmt)
                    done = True
        if not done:
            body = []
            # have no Import/ImportFrom in file
            for stmt in module.body:
                if isinstance(stmt, (Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    # find first being not a Comment/String
                    body.append(stmt)
                elif done:
                    body.append(stmt)
                else:
                    for mod, funcs in mods.items():
                        body.append(ast.ImportFrom(mod, [ast.alias(name=func) for func in sorted(funcs)], 0))
                    body.append(stmt)
                    done = True
        if not done:
            logg.error("did not append importfrom %s", newimport)
        else:
            module.body = body
        return module

class RequireImport:
    require: Dict[str, Optional[str]]
    def __init__(self, require: Iterable[str] = ()) -> None:
        self.require = {}
        self.append(require)
    def add(self, *require: Union[str, Tuple[str, Optional[str]]]) -> None:
        for req in require:
            if isinstance(req, str):
                self.require[req] = None
            else:
                self.require[req[0]] = req[1]
    def append(self, requires: Iterable[str]) -> None:
        for req in requires:
            self.require[req] = None
    def visit(self, node: ast.AST) -> ast.AST:
        if not self.require:
            return node
        imports = DetectImportsTransformer()
        imports.visit(node)
        newimport: Dict[str, Optional[str]] = {}
        for require, asname in self.require.items():
            if require not in imports.imported:
                newimport[require] = asname
        if not newimport:
            return node
        if not isinstance(node, ast.Module):
            logg.warning("no module for new imports %s", newimport)
            return node
        module = cast(ast.Module, node)  # type: ignore[redundant-cast]
        body: List[ast.stmt] = []
        done = False
        simple: Dict[str, Optional[str]] = {}
        dotted: Dict[str, Optional[str]] = {}
        for new, asname in newimport.items():
            if "." in new:
                if new not in dotted:
                    dotted[new] = asname
            else:
                simple[new] = asname
        logg.debug("requiredimports dotted %s", dotted)
        logg.debug("requiredimports simple %s", simple)
        # if imports.imported:
        if imports.imported:
            body = []
            for stmt in module.body:
                if not isinstance(stmt, ast.ImportFrom) and not isinstance(stmt, ast.Import):
                    # find first Import/ImportFrom
                    body.append(stmt)
                elif done:
                    body.append(stmt)
                else:
                    if simple:
                        body.append(ast.Import([ast.alias(mod, simple[mod] if simple[mod] != mod else None) for mod in sorted(simple)]))
                    for mod in sorted(dotted):
                        alias = dotted[mod]
                        if alias and "." in mod:
                            libname, sym = mod.rsplit(".", 1)
                            body.append(ast.ImportFrom(libname, [ast.alias(sym, alias if alias != sym else None)], 0))
                        else:
                            body.append(ast.Import([ast.alias(mod, alias)]))
                    body.append(stmt)
                    done = True
        if not done:
            # have no Import/ImportFrom or hidden in if-blocks
            body = []
            for stmt in module.body:
                if isinstance(stmt, (Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    # find first being not a Comment/String
                    body.append(stmt)
                elif done:
                    body.append(stmt)
                else:
                    if simple:
                        body.append(ast.Import([ast.alias(mod, simple[mod] if simple[mod] != mod else None) for mod in sorted(simple)]))
                    for mod in sorted(dotted):
                        alias = dotted[mod]
                        if alias and "." in mod:
                            libname, sym = mod.rsplit(".", 1)
                            body.append(ast.ImportFrom(libname, [ast.alias(sym, alias if alias != sym else None)], 0))
                        else:
                            body.append(ast.Import([ast.alias(mod, alias)]))
                    body.append(stmt)
                    done = True
        if not done:
            logg.error("did not add imports %s %s", simple, dotted)
        else:
            module.body = body
        return module


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

class DetectImportedFunctionCalls(DetectImportsTransformer):
    def __init__(self, replace: Optional[Dict[str, str]] = None, noimport: Optional[List[str]] = None) -> None:
        DetectImportsTransformer.__init__(self)
        self.found: Dict[str, str] = {} # funcname to callname
        self.calls: Dict[str, str] = {} # callname to funcname
        self.divs: int = 0
        self.replace = replace if replace is not None else {}
        self.noimport = noimport if noimport is not None else []
    def visit_Import(self, node: ast.Import) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if node.names and node.names[0].name in self.noimport:
            return None # to remove the node
        return DetectImportsTransformer.visit_Import(self, node)
    def visit_Div(self, node: ast.Div) -> ast.AST:  # pylint: disable=invalid-name
        self.divs += 1
        return self.generic_visit(node)
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        calls: ast.Call = node
        if isinstance(calls.func, ast.Name):
            call1: ast.Name = calls.func
            callname = call1.id
            funcname = callname if callname not in self.importas else self.importas[callname]
            logg.debug("found call1: %s -> %s", callname, funcname)
            self.found[funcname] = callname
            self.calls[callname] = funcname
            if funcname in self.replace:
                return ast.Call(func=ast.Name(self.replace[funcname]), args=calls.args, keywords=calls.keywords)
        elif isinstance(calls.func, ast.Attribute):
            call2: ast.Attribute = calls.func
            if isinstance(call2.value, ast.Name):
                call21: ast.Name = call2.value
                module2 = call21.id
                if module2 in self.importas:
                    callname = module2 + "." + call2.attr
                    funcname = self.importas[module2] + "." + call2.attr
                    logg.debug("found call2: %s -> %s", callname, funcname)
                    self.found[funcname] = callname
                    self.calls[callname] = funcname
                    if funcname in self.replace:
                        return ast.Call(func=ast.Name(self.replace[funcname]), args=calls.args, keywords=calls.keywords)
                else:
                    logg.debug("skips call2: %s.%s", module2, call2.attr)
                    logg.debug("have imports: %s", ", ".join(self.importas.keys()))
            elif isinstance(call2.value, ast.Attribute):
                call3: ast.Attribute = call2.value
                if isinstance(call3.value, ast.Name):
                    call31: ast.Name = call3.value
                    module3 = call31.id + "." + call3.attr
                    if module3 in self.importas:
                        callname = module3 + "." + call2.attr
                        funcname = self.importas[module3] + "." + call2.attr
                        logg.debug("found call3: %s -> %s", callname, funcname)
                        self.found[funcname] = callname
                        self.calls[callname] = funcname
                        if funcname in self.replace:
                            return ast.Call(func=ast.Name(self.replace[funcname]), args=calls.args, keywords=calls.keywords)
                    else:
                        logg.debug("skips call3: %s.%s", module3, call2.attr)
                        logg.debug("have imports: %s", ", ".join(self.importas.keys()))
                elif isinstance(call3.value, ast.Attribute):
                    logg.debug("skips call4+ (not implemented)")
                else: # pragma: nocover
                    logg.debug("skips unknown call3+ [%s]", type(call3.value))
            else: # pragma: nocover
                logg.debug("skips unknown call2+ [%s]", type(call2.value))
        else: # pragma: nocover
            logg.debug("skips unknown call1+ [%s]", type(calls.func))
        return self.generic_visit(node)

class DefineIfPython2:
    body: List[ast.stmt]
    requires: List[str]
    orelse: List[ast.stmt]
    def __init__(self, expr: Iterable[str], before: Optional[Tuple[int, int]] = None, or_else: Iterable[str] = (), atleast: Optional[Tuple[int, int]] = None,
        *, orelse: Iterable[ast.stmt] = (), body: Iterable[ast.stmt] = ()) -> None:
        self.atleast = atleast
        self.before = before
        self.requires = [] # output
        self.body = []
        self.orelse = []
        if or_else:
            for elselist in [cast(ast.Module, ast_parse(part)).body for part in or_else]: # type: ignore[redundant-cast]
                self.orelse += elselist
        if orelse:
            for stmt in orelse:
                self.orelse.append(stmt)
        for stmtlist in [cast(ast.Module, ast_parse(e)).body for e in expr]: # type: ignore[redundant-cast]
            self.body += stmtlist
        if body:
            for stmt in body:
                self.body.append(stmt)
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and (self.body or self.orelse):
            # pylint: disable=consider-using-f-string
            module1: ast.Module = node
            body: List[ast.stmt] = []
            before_imports = True
            after_append = False
            count_imports = 0
            for stmt in module1.body:
                if isinstance(stmt, (ast.ImportFrom, ast.Import)):
                    count_imports += 1
            if not count_imports:
                before_imports = False
            for stmt in module1.body:
                if isinstance(stmt, (ast.ImportFrom, ast.Import)):
                    if before_imports:
                        before_imports = False
                    body.append(stmt)
                elif before_imports or after_append or isinstance(stmt, (Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    body.append(stmt)
                else:
                    testcode = "sys.version_info < (3, 0)"
                    testparsed: ast.Module = cast(ast.Module, ast_parse(testcode)) # type: ignore[redundant-cast]
                    assert isinstance(testparsed.body[0], ast.Expr)
                    testbody: ast.Expr = testparsed.body[0]
                    assert isinstance(testbody.value, ast.Compare)
                    testcompare: ast.expr = testbody.value
                    if self.before:
                        testcode = "sys.version_info < ({}, {})".format(self.before[0], self.before[1])
                        testparsed = cast(ast.Module, ast_parse(testcode)) # type: ignore[redundant-cast]
                        assert isinstance(testparsed.body[0], ast.Expr)
                        testbody = testparsed.body[0]
                        testcompare = testbody.value
                    if self.atleast:
                        testcode = "sys.version_info >= ({}, {})".format(self.atleast[0], self.atleast[1])
                        testparsed = cast(ast.Module, ast_parse(testcode)) # type: ignore[redundant-cast]
                        assert isinstance(testparsed.body[0], ast.Expr)
                        testbody = testparsed.body[0]
                        testatleast = testbody.value
                        testcompare = ast.BoolOp(op=ast.Or(), values=[testcompare, testatleast])
                    before = self.before if self.before else (3,0)
                    logg.log(HINT, "python2 atleast %s before %s", self.atleast, before)
                    python2 = ast.If(test=testcompare, body=self.body or [ast.Pass()], orelse=self.orelse)
                    python2 = copy_location(python2, stmt)
                    body.append(python2)
                    body.append(stmt)
                    after_append = True
                    self.requires += [ "sys" ]
            module2 = ast.Module(body, module1.type_ignores)
            return module2
        else:
            return node

class DefineIfPython3:
    body: List[ast.stmt]
    requires: List[str]
    orelse: List[ast.stmt]
    def __init__(self, expr: Iterable[str], atleast: Optional[Tuple[int, int]] = None, or_else: Iterable[str] = (), before: Optional[Tuple[int, int]] = None,
        *, orelse: Iterable[ast.stmt] = (), body: Iterable[ast.stmt] = ()) -> None:
        self.atleast = atleast
        self.before = before
        self.requires = [] # output
        self.body = []
        self.orelse = []
        if or_else:
            for elselist in [cast(ast.Module, ast_parse(part)).body for part in or_else]: # type: ignore[redundant-cast]
                self.orelse += elselist
        if orelse:
            for stmt in orelse:
                self.orelse.append(stmt)
        for stmtlist in [cast(ast.Module, ast_parse(e)).body for e in expr]: # type: ignore[redundant-cast]
            self.body += stmtlist
        if body:
            for stmt in body:
                self.body.append(stmt)
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and (self.body or self.orelse):
            # pylint: disable=consider-using-f-string
            module1: ast.Module = node
            body: List[ast.stmt] = []
            before_imports = True
            after_append = False
            count_imports = 0
            for stmt in module1.body:
                if isinstance(stmt, (ast.ImportFrom, ast.Import)):
                    count_imports += 1
            if not count_imports:
                before_imports = False
            for stmt in module1.body:
                if isinstance(stmt, (ast.ImportFrom, ast.Import)):
                    if before_imports:
                        before_imports = False
                    body.append(stmt)
                elif before_imports or after_append or isinstance(stmt, (Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    body.append(stmt)
                else:
                    testcode = "sys.version_info >= (3, 0)"
                    testparsed: ast.Module = cast(ast.Module, ast_parse(testcode)) # type: ignore[redundant-cast]
                    assert isinstance(testparsed.body[0], ast.Expr)
                    testbody: ast.Expr = testparsed.body[0]
                    assert isinstance(testbody.value, ast.Compare)
                    testcompare: ast.expr = testbody.value
                    if self.atleast:
                        testcode = "sys.version_info >= ({}, {})".format(self.atleast[0], self.atleast[1])
                        testparsed = cast(ast.Module, ast_parse(testcode)) # type: ignore[redundant-cast]
                        assert isinstance(testparsed.body[0], ast.Expr)
                        testbody = testparsed.body[0]
                        testcompare = testbody.value
                    if self.before:
                        testcode = "sys.version_info < ({}, {})".format(self.before[0], self.before[1])
                        testparsed = cast(ast.Module, ast_parse(testcode)) # type: ignore[redundant-cast]
                        assert isinstance(testparsed.body[0], ast.Expr)
                        testbody = testparsed.body[0]
                        testbefore = testbody.value
                        testcompare = ast.BoolOp(op=ast.And(), values=[testcompare, testbefore])
                    atleast = self.atleast if self.atleast else (3,0)
                    logg.log(HINT, "python3 atleast %s before %s", atleast, self.before)
                    python3 = ast.If(test=testcompare, body=self.body or [ast.Pass()], orelse=self.orelse)
                    python3 = copy_location(python3, stmt)
                    body.append(python3)
                    body.append(stmt)
                    after_append = True
                    self.requires += [ "sys" ]
            module2 = ast.Module(body, module1.type_ignores)
            return module2
        else:
            return node

class NamedTupleToCollectionsTransformer(DetectImportsTransformer):
    typedefs: List[ast.stmt]
    requiresfrom: Set[str]
    only: Set[str]
    def __init__(self) -> None:
        DetectImportsTransformer.__init__(self)
        self.typedefs = []
        self.requiresfrom = set()
        self.only = set()
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module):
            module = cast(ast.Module, node)  # type: ignore[redundant-cast]
            for stmt in module.body:
                if isinstance(stmt, ast.ClassDef):
                    self.only.add(stmt.name) # only top-level class names
        return cast(ast.AST, DetectImportsTransformer.visit(self, node))
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST: # pylint: disable=invalid-name
        classname = node.name
        for base in node.bases:
            if isinstance(base, ast.Name):
                basename = cast(ast.Name, base)  # type: ignore[redundant-cast]
                basetype = basename.id
                if basetype in self.importas:
                    if self.importas[basetype] == "typing.NamedTuple":
                        body: List[ast.stmt] = []
                        fields: List[ast.expr] = []
                        for stmt in node.body:
                            if isinstance(stmt, ast.AnnAssign):
                                assign = cast(ast.AnnAssign, stmt)   # type: ignore[redundant-cast]
                                fieldname = cast(ast.Name, assign.target).id
                                annotation = assign.annotation
                                body.append(ast.AnnAssign(ast.Name(fieldname), annotation, None, assign.simple))
                                fields.append(ast.Constant(fieldname))
                            else: # pragma: nocover
                                raise TransformerSyntaxError(F"NamedTuple {classname} - can only replace variable declarations", #  ..
                                    (None, stmt.lineno, stmt.col_offset, str(type(stmt)), stmt.end_lineno, stmt.end_col_offset))
                        typebase = ast.Name("NamedTuple")
                        copy_location(typebase, node)
                        typebases: List[ast.expr] = [typebase]
                        typeclass = ast.ClassDef(classname, typebases, body=body, keywords=[], decorator_list=[])
                        copy_location(typeclass, node)
                        if not self.only or classname in self.only:
                            self.typedefs.append(typeclass)
                        args: List[ast.expr] = [ast.Constant(classname)]
                        args.append(ast.List(fields))
                        replaced = ast.Assign([ast.Name(classname)], ast.Call(ast.Name("namedtuple"), args, []))
                        copy_location(replaced, node)
                        self.requiresfrom.add("collections.namedtuple")
                        logg.debug("replaced NamedTuple %s = %s", classname, ast.dump(replaced))
                        return replaced
        return self.generic_visit(node)

class TypedDictToDictTransformer(DetectImportsTransformer):
    typedefs: List[ast.stmt]
    requiresfrom: Set[str]
    only: Set[str]
    def __init__(self) -> None:
        DetectImportsTransformer.__init__(self)
        self.typedefs = []
        self.requiresfrom = set()
        self.only = set()
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module):
            module = cast(ast.Module, node)  # type: ignore[redundant-cast]
            for stmt in module.body:
                if isinstance(stmt, ast.ClassDef):
                    self.only.add(stmt.name) # only top-level class names
        return cast(ast.AST, DetectImportsTransformer.visit(self, node))
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST: # pylint: disable=invalid-name
        for base in node.bases:
            classname = node.name
            if isinstance(base, ast.Name):
                basename = cast(ast.Name, base)  # type: ignore[redundant-cast]
                basetype = basename.id
                if basetype in self.importas:
                    if self.importas[basetype] == "typing.TypedDict":
                        body: List[ast.stmt] = []
                        fields: List[ast.expr] = []
                        for stmt in node.body:
                            if isinstance(stmt, ast.AnnAssign):
                                assign = cast(ast.AnnAssign, stmt)   # type: ignore[redundant-cast]
                                fieldname = cast(ast.Name, assign.target).id
                                annotation = assign.annotation
                                body.append(ast.AnnAssign(ast.Name(fieldname), annotation, None, assign.simple))
                                fields.append(ast.Constant(fieldname))
                            else: # pragma: nocover
                                raise TransformerSyntaxError(F"TypedDict {classname} - must only have variable declarations", #  ..
                                    (None, stmt.lineno, stmt.col_offset, str(type(stmt)), stmt.end_lineno, stmt.end_col_offset))
                        typebase = ast.Name("TypedDict")
                        copy_location(typebase, node)
                        typebases: List[ast.expr] = [typebase]
                        typeclass = ast.ClassDef(classname, typebases, body=body, keywords=[], decorator_list=[])
                        copy_location(typeclass, node)
                        if not self.only or classname in self.only:
                            self.typedefs.append(typeclass)
                        replaced = ast.Assign([ast.Name(classname)], ast.Name("dict"))
                        copy_location(replaced, node)
                        return replaced
        return node



class FStringToFormatTransformer(ast.NodeTransformer):
    """ The 3.8 F="{a=}" syntax is resolved before ast nodes are generated. """
    def string_format(self, values: List[Union[ast.Constant, ast.FormattedValue]]) -> ast.AST:
        num: int = 1
        form: str = ""
        args: List[ast.expr] = []
        for part in values:
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
                    logg.error("unknown conversion id in f-string: %s > %s", type(part), fmt.conversion)
                if fmt.format_spec:
                    if isinstance(fmt.format_spec, ast.JoinedStr):
                        join: ast.JoinedStr = fmt.format_spec
                        for val in join.values:
                            if isinstance(val, ast.Constant):
                                if want.fstring_numbered:
                                    form += "{%i%s:%s}" % (num, conv, val.value)
                                else:
                                    form += "{%s:%s}" % (conv, val.value)
                            else:
                                logg.error("unknown part of format_spec in f-string: %s > %s", type(part), type(val))
                    else: # pragma: nocover
                        raise TransformerSyntaxError("unknown format_spec in f-string", (None, fmt.lineno, fmt.col_offset, str(type(fmt)), fmt.end_lineno, fmt.end_col_offset))
                else:
                    if want.fstring_numbered:
                        form += "{%i%s}" % (num, conv)
                    else:
                        form += "{%s}" % (conv)
                num += 1
                args += [fmt.value]
                self.generic_visit(fmt.value)
            else: # pragma: nocover
                raise TransformerSyntaxError("unknown part in f-string", (None, part.lineno, part.col_offset, str(type(part)), part.end_lineno, part.end_col_offset))
        make: ast.AST
        if not args:
            make = ast.Constant(form)
        else:
            make = ast.Call(ast.Attribute(ast.Constant(form), attr="format"), args, keywords=[])
        return make

    def visit_FormattedValue(self, node: ast.FormattedValue) -> ast.AST:  # pylint: disable=invalid-name # pragma: nocover
        """ If the string contains a single formatting field and nothing else the node can be isolated otherwise it appears in JoinedStr."""
        # NOTE: I did not manage to create a test case that triggers this visitor
        return self.string_format([node])
    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:  # pylint: disable=invalid-name
        return self.string_format(cast(List[Union[ast.Constant, ast.FormattedValue]], node.values))

class FStringFromLocalsFormat(ast.NodeTransformer):
    filename: str
    """ the portable idiom `x = "{y}+".format(**locals())` should be replaced by f-string. """
    def visit_Call(self, node: ast.Call) -> ast.AST: # pylint: disable=invalid-name
        call = cast(ast.Call, node) # type: ignore[redundant-cast]
        logg.debug("call %s", ast.dump(call))
        if isinstance(call.func, ast.Attribute):
            calls = cast(ast.Attribute, call.func) # type: ignore[redundant-cast]
            logg.debug("calls %s", ast.dump(calls))
            if isinstance(calls.value, ast.Constant):
                value = cast(ast.Constant, calls.value) # type: ignore[redundant-cast]
                if isinstance(value.value, str) and calls.attr == 'format':
                    text = cast(str, value.value) # type: ignore[redundant-cast]
                    if not call.args and call.keywords and len(call.keywords) == 1:
                        keywords = ast_unparse(call.keywords[0])
                        if keywords == '**locals()':
                            module = ast_parse(F'F"{text}"')
                            logg.debug("created %s", ast.dump(module))
                            if isinstance(module, ast.Module):
                                if module.body and isinstance(module.body[0], ast.Expr):
                                    expr = cast(ast.Expr, module.body[0]) # type: ignore[redundant-cast]
                                    return expr.value
        return node

class FStringFromVarLocalsFormat(BlockTransformer):
    filename: str
    """ the portable idiom `x = "{y}+"; print(x.format(**locals()))` should be replaced by f-string. """
    def next_body(self, body: List[ast.stmt], block: Deque[ast.AST], part: str = NIX) -> List[ast.stmt]:
        varvalue: Dict[str, str] = {}
        varused: Dict[str, int] = {}
        replaced: Dict[str, int] = {}
        for node in body:
            runs: Optional[ast.Call] = None
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                runs = cast(ast.Call, node.value) # type: ignore[redundant-cast]
                logg.debug("runs %s", ast.dump(runs))
            elif isinstance(node, ast.Assign):
                sets = cast(ast.Assign, node) # type: ignore[redundant-cast]
                logg.debug("sets %s", ast.dump(sets))
                if isinstance(sets.value, ast.Constant) and isinstance(sets.value.value, str):
                    if len(sets.targets) == 1 and isinstance(sets.targets[0], ast.Name):
                        targetname = cast(ast.Name, sets.targets[0]) # type: ignore[redundant-cast]
                        varvalue[targetname.id] = sets.value.value
                        varused[targetname.id] = 0
                        replaced[targetname.id] = 0
                elif isinstance(sets.value, ast.Call):
                    runs = cast(ast.Call, sets.value) # type: ignore[redundant-cast]
                    logg.debug("run2 %s", ast.dump(runs))
            else:
                logg.debug("? %s", ast.dump(node))
            if runs is not None:
                for n, arg in enumerate(runs.args):
                    if isinstance(arg, ast.Name):
                        use1 = cast(ast.Name, arg) # type: ignore[redundant-cast]
                        if use1.id in varused:
                            varused[use1.id] += 1
                    elif isinstance(arg, ast.Call):
                        call = cast(ast.Call, arg) # type: ignore[redundant-cast]
                        logg.debug("call %s", ast.dump(call))
                        if isinstance(call.func, ast.Attribute):
                            calls = cast(ast.Attribute, call.func) # type: ignore[redundant-cast]
                            logg.debug("calls %s", ast.dump(calls))
                            if isinstance(calls.value, ast.Name) and calls.attr == 'format':
                                name = cast(ast.Name, calls.value) # type: ignore[redundant-cast]
                                logg.debug("%s == ... %s", name.id, varvalue)
                                if name.id in varvalue:
                                    text = varvalue[name.id]
                                    logg.debug("%s == '%s'", name.id, text)
                                    if not call.args and call.keywords and len(call.keywords) == 1:
                                        keywords = ast_unparse(call.keywords[0])
                                        if keywords == '**locals()':
                                            module = ast_parse(F'F"{text}"')
                                            logg.debug("created %s", ast.dump(module))
                                            if isinstance(module, ast.Module):
                                                if module.body and isinstance(module.body[0], ast.Expr):
                                                    expr = cast(ast.Expr, module.body[0]) # type: ignore[redundant-cast]
                                                    logg.debug("expr %s", ast.dump(expr))
                                                    runs.args[n] = expr.value
                                                    replaced[name.id] += 1
        newbody: list[ast.stmt] = []
        for node in body:
            if isinstance(node, ast.Assign):
                sets = cast(ast.Assign, node) # type: ignore[redundant-cast]
                logg.debug("sets %s", ast.dump(sets))
                if isinstance(sets.value, ast.Constant) and isinstance(sets.value.value, str):
                    if len(sets.targets) == 1 and isinstance(sets.targets[0], ast.Name):
                        targetname = cast(ast.Name, sets.targets[0]) # type: ignore[redundant-cast]
                        if replaced[targetname.id]:
                            if not varused[targetname.id]:
                                continue # remove assign stmt
                            filename = getattr(self, "filename", NIX) or "line"
                            logg.warning("%s:%i: can not remove format-var '%s' as it is also used without format()", filename, node.lineno, targetname.id)
            newbody.append(node)
        return newbody



# ......................................................................................

class ReplaceCallResult(NamedTuple):
    tree: ast.AST
    requires: List[str]
    removed: List[str]

def replace_datetime_fromisoformat(tree: ast.AST, calls: Optional[DetectImportedFunctionCalls] = None) -> ReplaceCallResult:
    if calls is None:   # pragma: nocover
        calls = DetectImportedFunctionCalls()
        calls.visit(tree)
    assert calls is not None
    requires: List[str] = []
    removed: List[str] = []
    if "datetime.datetime.fromisoformat" in calls.found:
        if OK:
            if OK:
                datetime_module = calls.imported["datetime.datetime"]
                fromisoformat = F"{datetime_module}_fromisoformat"  if "." not in datetime_module else "datetime_fromisoformat"
                isoformatdef = DefineIfPython3([F"def {fromisoformat}(x): return {datetime_module}.fromisoformat(x)"], atleast=(3,7), or_else=[text4(F"""
                def {fromisoformat}(x):
                    import re
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d):(\\d\\d).(\\d\\d\\d\\d\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) )
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d):(\\d\\d).(\\d\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7)) * 1000)
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d):(\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)) )
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d).(\\d\\d):(\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)) )
                    m = re.match(r"(\\d\\d\\d\\d)-(\\d\\d)-(\\d\\d)", x)
                    if m: return {datetime_module}(int(m.group(1)), int(m.group(2)), int(m.group(3)) )
                    raise ValueError("not a datetime isoformat: "+x)
                """)])
                isoformatfunc = DetectImportedFunctionCalls({"datetime.datetime.fromisoformat": fromisoformat})
                tree = isoformatdef.visit(isoformatfunc.visit(tree))
                # importrequires.append(isoformatdef.requires)
                # importrequiresfrom.remove(["datetime.datetime.fromisoformat"])
                requires += isoformatdef.requires
                removed += ["datetime.datetime.fromisoformat"]
    return ReplaceCallResult(tree, requires, removed)

def replace_subprocess_run(tree: ast.AST, calls: Optional[DetectImportedFunctionCalls] = None, minversion: Tuple[int, int] = (2, 7)) -> ReplaceCallResult:
    if calls is None:   # pragma: nocover
        calls = DetectImportedFunctionCalls()
        calls.visit(tree)
    assert calls is not None
    requires: List[str] = []
    removed: List[str] = []
    if "subprocess.run" in calls.found:
        if OK:
            if OK:
                subprocess_module = calls.imported["subprocess"]
                defname = subprocess_module + "_run"
                # there is a timeout value available since Python 3.3
                subprocessrundef33 = DefineIfPython3([F"{defname} = {subprocess_module}.run"], atleast=(3,5), or_else=[text4(F"""
                class CompletedProcess:
                    def __init__(self, args, returncode, outs, errs):
                        self.args = args
                        self.returncode = returncode
                        self.stdout = outs
                        self.stderr = errs
                    def check_returncode(self):
                        if self.returncode:
                            raise {subprocess_module}.CalledProcessError(self.returncode, self.args)
                def {defname}(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                    proc = {subprocess_module}.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
                    try:
                        outs, errs = proc.communicate(input=input, timeout=timeout)
                    except {subprocess_module}.TimeoutExpired:
                        proc.kill()
                        outs, errs = proc.communicate()
                    completed = CompletedProcess(args, proc.returncode, outs, errs)
                    if check:
                        completed.check_returncode()
                    return completed
                """)])
                subprocessrundef27 = DefineIfPython3([F"{defname} = {subprocess_module}.run"], atleast=(3,5), or_else=[text4(F"""
                class CompletedProcess:
                    def __init__(self, args, returncode, outs, errs):
                        self.args = args
                        self.returncode = returncode
                        self.stdout = outs
                        self.stderr = errs
                    def check_returncode(self):
                        if self.returncode:
                            raise {subprocess_module}.CalledProcessError(self.returncode, self.args)
                def {defname}(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                    proc = {subprocess_module}.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
                    outs, errs = proc.communicate(input=input)
                    completed = CompletedProcess(args, proc.returncode, outs, errs)
                    if check:
                        completed.check_returncode()
                    return completed
                """)])
                subprocessrundef = subprocessrundef33 if minversion >= (3,3) else subprocessrundef27
                subprocessrunfunc = DetectImportedFunctionCalls({"subprocess.run": defname})
                tree = subprocessrundef.visit(subprocessrunfunc.visit(tree))
                # importrequires.append(subprocessrundef.requires)
                # importrequiresfrom.remove(["subprocess.run"])
                requires += subprocessrundef.requires
                removed += ["subprocess.run"]
    return ReplaceCallResult(tree, requires, removed)

def replace_time_monotonic(tree: ast.AST, calls: Optional[DetectImportedFunctionCalls] = None) -> ReplaceCallResult:
    if calls is None:   # pragma: nocover
        calls = DetectImportedFunctionCalls()
        calls.visit(tree)
    assert calls is not None
    requires: List[str] = []
    removed: List[str] = []
    if "time.monotonic" in calls.found:
        if OK:
            if OK:
                time_module = calls.imported["time"]
                defname = time_module + "_monotonic"
                monotonicdef = DefineIfPython3([F"{defname} = {time_module}.monotonic"], atleast=(3,3), # ..
                   or_else=[F"def {defname}(): return time.time()"])
                monotonicfunc = DetectImportedFunctionCalls({"time.monotonic": defname})
                tree = monotonicdef.visit(monotonicfunc.visit(tree))
                # importrequires.append(monotonicdef.requires)
                # importrequiresfrom.remove(["time.monotonic"])
                requires += monotonicdef.requires
                removed += ["time.monotonic"]
    return ReplaceCallResult(tree, requires, removed)

def replace_time_monotonic_ns(tree: ast.AST, calls: Optional[DetectImportedFunctionCalls] = None) -> ReplaceCallResult:
    if calls is None:   # pragma: nocover
        calls = DetectImportedFunctionCalls()
        calls.visit(tree)
    assert calls is not None
    requires: List[str] = []
    removed: List[str] = []
    if "time.monotonic_ns" in calls.found:
        if OK:
            if OK:
                if "time" in calls.imported:
                    time_module = calls.imported["time"]
                else:
                    time_module = "time"
                    requires += ["time"]
                defname = time_module + "_monotonic_ns"
                monotonicdef = DefineIfPython3([F"{defname} = {time_module}.monotonic_ns"], atleast=(3,7), # ..
                   or_else=[F"def {defname}(): return int((time.time() - 946684800) * 1000000000)"])
                monotonicfunc = DetectImportedFunctionCalls({"time.monotonic_ns": defname})
                tree = monotonicdef.visit(monotonicfunc.visit(tree))
                # importrequires.append(monotonicdef.requires)
                # importrequiresfrom.remove(["time.monotonic_ns"])
                requires += monotonicdef.requires
                removed += ["time.monotonic_ns"]
    return ReplaceCallResult(tree, requires, removed)

# ...................................................................................

class DetectAnnotation(ast.NodeVisitor):
    names: Dict[str, str]
    def __init__(self) -> None:
        ast.NodeVisitor.__init__(self)
        self.names = dict()
    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute: # pylint: disable=invalid-name
        if isinstance(node.value, ast.Name):
            name = node.value.id
            if node.attr:
                name += "." + node.attr
            self.names[name] = NIX
        return node
    def visit_Name(self, node: ast.Name) -> ast.Name: # pylint: disable=invalid-name
        name = node.id
        self.names[name] = NIX
        return node

def get_simple_typehint(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return cast(str, node.id) # type: ignore[redundant-cast]
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
            name = cast(str, node.value.id) # type: ignore[redundant-cast]
            if node.attr:
                name += "." + node.attr
            return name
    return NIX

class ReplaceSelfByTypevar(BlockTransformer):
    typing: List[str]
    newclasses: List[str]
    def __init__(self) -> None:
        BlockTransformer.__init__(self)
        self.typing = []
        self.newclasses = []
    def visit2_ClassDef(self, node: ast.ClassDef, block: Deque[ast.stmt]) -> List[ast.stmt]:  # pylint: disable=invalid-name,unused-argument
        classname = node.name
        selfcount = 0
        if OK:
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef):
                    func = cast(ast.FunctionDef, stmt) # type: ignore[redundant-cast]
                    if func.returns:
                        if get_simple_typehint(func.returns) == "Self":
                            selfcount += 1
                    for arg in func.args.posonlyargs:
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                selfcount += 1
                    for arg in func.args.args:
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                selfcount += 1
                    for arg in func.args.kwonlyargs:
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                selfcount += 1
                    if func.args.vararg is not None:
                        arg = func.args.vararg
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                selfcount += 1
                    if func.args.kwarg is not None:
                        arg = func.args.kwarg
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                selfcount += 1
        if selfcount:
            selfclass = F"Self{classname}"
            self.newclasses.append(selfclass)
            self.typing.append("TypeVar")
            typevar = ast.Call(ast.Name("TypeVar"), [ast.Constant(selfclass)], [ast.keyword("bound", ast.Constant(classname))])
            typevar = copy_location(typevar, node)
            newtype = ast.Assign([ast.Name(selfclass)], typevar)
            newtype = copy_location(newtype, node)
            preclass: List[ast.stmt] = [newtype]
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef):
                    func = cast(ast.FunctionDef, stmt) # type: ignore[redundant-cast]
                    if func.returns:
                        if get_simple_typehint(func.returns) == "Self":
                            func.returns = ast.Name(selfclass)
                            copy_location(func.returns, stmt)
                    for arg in func.args.posonlyargs:
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                arg.annotation = ast.Name(selfclass)
                                copy_location(arg.annotation, stmt)
                    for arg in func.args.args:
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                arg.annotation = ast.Name(selfclass)
                                copy_location(arg.annotation, stmt)
                    for arg in func.args.kwonlyargs:
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                arg.annotation = ast.Name(selfclass)
                                copy_location(arg.annotation, stmt)
                    if func.args.vararg is not None:
                        arg = func.args.vararg
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                arg.annotation = ast.Name(selfclass)
                                copy_location(arg.annotation, stmt)
                    if func.args.kwarg is not None:
                        arg = func.args.kwarg
                        if arg.annotation:
                            if get_simple_typehint(arg.annotation) == "Self":
                                arg.annotation = ast.Name(selfclass)
                                copy_location(arg.annotation, stmt)
            return preclass+[node]
        return [node]

def types_in_annotation(annotation: ast.expr) -> Dict[str, str]:
    detect = DetectAnnotation()
    detect.visit(annotation)
    return detect.names

class RemovePosonlyArgs(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        func: ast.FunctionDef = node
        if not func.args.posonlyargs:
            return node
        func.args.args = func.args.posonlyargs + func.args.args
        func.args.posonlyargs = []
        return func

class DetectHints(ast.NodeTransformer):
    """ only check all ClassDef, Function and AnnAssign in the source tree """
    typing: Dict[str, str]
    classes: Dict[str, str]
    hints: List[ast.expr]
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.typing = dict()
        self.classes = dict()
        self.hints = list()
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.ImportFrom = cast(ast.ImportFrom, node) # type: ignore[redundant-cast]
        logg.debug("?imports: %s", ast.dump(imports))
        if imports.module == "typing":
            for symbol in imports.names:
                self.typing[symbol.asname or symbol.name] = F"typing.{symbol.name}"
        return node # unchanged no recurse
    def visit_AnnAssign(self, node: ast.AnnAssign) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        assign: ast.AnnAssign = cast(ast.AnnAssign, node)  # type: ignore[redundant-cast]
        logg.debug("?assign: %s", ast.dump(assign))
        if assign.annotation:
            self.hints.append(assign.annotation)
            self.classes.update(types_in_annotation(assign.annotation))
        return node
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        func: ast.FunctionDef = node
        logg.debug("?func: %s", ast.dump(func))
        vargarg = func.args.vararg
        kwarg = func.args.kwarg
        return_annotation = func.returns
        for arg in func.args.posonlyargs:
            if arg.annotation:
                self.hints.append(arg.annotation)
                self.classes.update(types_in_annotation(arg.annotation))
        for arg in func.args.args:
            if arg.annotation:
                self.hints.append(arg.annotation)
                self.classes.update(types_in_annotation(arg.annotation))
        for arg in func.args.kwonlyargs:
            if arg.annotation:
                self.hints.append(arg.annotation)
                self.classes.update(types_in_annotation(arg.annotation))
        if vargarg is not None:
            if vargarg.annotation:
                self.hints.append(vargarg.annotation)
                self.classes.update(types_in_annotation(vargarg.annotation))
        if kwarg is not None:
            if kwarg.annotation:
                self.hints.append(kwarg.annotation)
                self.classes.update(types_in_annotation(kwarg.annotation))
        if OK:
            if return_annotation:
                self.hints.append(return_annotation)
                self.classes.update(types_in_annotation(return_annotation))
        return self.generic_visit(node)

class StripTypeHints(ast.NodeTransformer):
    """ check all ClassDef, Function and AnnAssign in the source tree """
    typing: Set[str]
    removed: Set[str]
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.typing = set()
        self.removed = set()
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if not want.remove_typehints:
            return node
        imports: ast.ImportFrom = node
        logg.debug("-imports: %s", ast.dump(imports))
        if imports.module != "typing":
            return node # unchanged
        return None
    def visit_Call(self, node: ast.Call) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if not want.remove_typehints:
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
        if not want.remove_typehints and not want.remove_var_typehints:
            return self.generic_visit(node)
        assign: ast.AnnAssign = node
        logg.debug("-assign: %s", ast.dump(assign))
        if assign.value is not None:
            assign2 = ast.Assign(targets=[assign.target], value=assign.value)
            assign2 = copy_location(assign2, assign)
            return self.generic_visit(assign2)
        return None
    def visit_ClassDef(self, node: ast.ClassDef) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        body: List[ast.stmt] = []
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign):
                stmt1 = self.visit_AnnAssign(stmt)
                if stmt1:
                    body.append(cast(ast.stmt, stmt1))
            elif isinstance(stmt, ast.FunctionDef):
                stmt2 = self.visit_FunctionDef(stmt)
                if stmt2:
                    body.append(cast(ast.stmt, stmt2))
            else:
                stmt3 = self.generic_visit(stmt)
                if stmt3:
                    body.append(cast(ast.stmt, stmt3))
        if not body:
            body.append(ast.Pass())
        node.body = body
        return node
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
                new1 = types36_remove_typehints(arg.annotation)
                arg1 = ast.arg(arg.arg, new1.annotation)
                if want.remove_positional:
                    functionargs.append(arg1)
                else:
                    posonlyargs.append(arg1)
                if arg.annotation:
                    annos += 1
                self.typing.update(new1.typing)
                self.removed.update(new1.removed)
        if OK:
            for arg in func.args.args:
                logg.debug("-fun arg: %s", ast.dump(arg))
                new1 = types36_remove_typehints(arg.annotation)
                arg1 = ast.arg(arg.arg, new1.annotation)
                functionargs.append(arg1)
                if arg.annotation:
                    annos += 1
                self.typing.update(new1.typing)
                self.removed.update(new1.removed)
        if OK:
            for arg in func.args.kwonlyargs:
                logg.debug("-kwo arg: %s", ast.dump(arg))
                new1 = types36_remove_typehints(arg.annotation)
                arg1 = ast.arg(arg.arg, new1.annotation)
                if want.remove_keywordonly:
                    functionargs.append(arg1)
                else:
                    kwonlyargs.append(arg1)
                if arg.annotation:
                    annos += 1
                self.typing.update(new1.typing)
                self.removed.update(new1.removed)
        if vargarg is not None:
            if vargarg.annotation:
                annos += 1
            if want.remove_typehints:
                new1 = types36_remove_typehints(vargarg.annotation)
                vargarg = ast.arg(vargarg.arg, new1.annotation)
                self.typing.update(new1.typing)
                self.removed.update(new1.removed)
        if kwarg is not None:
            if kwarg.annotation:
                annos += 1
            if want.remove_typehints:
                new1 = types36_remove_typehints(kwarg.annotation)
                kwarg = ast.arg(kwarg.arg, new1.annotation)
                self.typing.update(new1.typing)
                self.removed.update(new1.removed)
        old = 0
        if func.args.kw_defaults and want.remove_keywordonly:
            old += 1
        if not annos and not func.returns and not old:
            return self.generic_visit(node) # unchanged
        if OK:
            for exp in func.args.defaults:
                defaults.append(exp)
        if OK:
            for kwexp in func.args.kw_defaults:
                if want.remove_keywordonly:
                    if kwexp is not None:
                        defaults.append(kwexp)
                else:
                    kwdefaults.append(kwexp)
        args2 = ast.arguments(posonlyargs, functionargs, vargarg, kwonlyargs, # ..
            kwdefaults, kwarg, defaults)
        new2 = types36_remove_typehints(func.returns)
        self.typing.update(new2.typing)
        self.removed.update(new2.removed)
        rets2 = new2.annotation
        func2 = ast.FunctionDef(func.name, args2, func.body, func.decorator_list, rets2)
        func2 = copy_location(func2, func)
        return self.generic_visit(func2)

class ExtractTypeHints:
    """ check the outer interface - extract typedefs for pyi """
    typedefs: List[ast.stmt]
    def __init__(self) -> None:
        self.typedefs = []
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module):
            for child in node.body:
                if isinstance(child, ast.ImportFrom):
                    imports = child
                    if imports.module == "typing":
                        imports3 = ast.ImportFrom(imports.module, imports.names, imports.level)
                        imports3 = copy_location(imports3, imports)
                        self.typedefs.append(imports3)
                elif isinstance(child, ast.AnnAssign):
                    assign1: ast.AnnAssign = child
                    assign3 = ast.AnnAssign(target=assign1.target, annotation=assign1.annotation, value=None, simple=assign1.simple)
                    self.typedefs.append(assign3)
                elif isinstance(child, ast.FunctionDef):
                    funcdef1: ast.FunctionDef = child
                    if OK:
                        if OK:
                            annos = 0
                            if OK:
                                for arg in funcdef1.args.posonlyargs:
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in funcdef1.args.args:
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in funcdef1.args.kwonlyargs:
                                    if arg.annotation:
                                        annos += 1
                            if funcdef1.args.vararg is not None:
                                arg = funcdef1.args.vararg
                                if arg.annotation:
                                    annos += 1
                            if funcdef1.args.kwarg is not None:
                                arg = funcdef1.args.kwarg
                                if arg.annotation:
                                    annos += 1
                            if annos or funcdef1.returns:
                                funcargs3 = funcdef1.args
                                funcdef3 = ast.FunctionDef(funcdef1.name, funcargs3, [ast.Pass()], funcdef1.decorator_list, funcdef1.returns)
                                funcdef3 = copy_location(funcdef3, funcdef1)
                                self.typedefs.append(funcdef3)
                elif isinstance(child, ast.ClassDef):
                    decl: List[ast.stmt] = []
                    for part in child.body:
                        if isinstance(part, ast.AnnAssign):
                            assign: ast.AnnAssign = part
                            assign3 = ast.AnnAssign(target=assign.target, annotation=assign.annotation, value=None, simple=assign.simple)
                            decl.append(assign3)
                        elif isinstance(part, ast.FunctionDef):
                            func: ast.FunctionDef = part
                            annos = 0
                            if OK:
                                for arg in func.args.posonlyargs:
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in func.args.args:
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in func.args.kwonlyargs:
                                    if arg.annotation:
                                        annos += 1
                            if func.args.vararg is not None:
                                arg = func.args.vararg
                                if arg.annotation:
                                    annos += 1
                            if func.args.kwarg is not None:
                                arg = func.args.kwarg
                                if arg.annotation:
                                    annos += 1
                            if annos or func.returns:
                                args3 = func.args
                                func3 = ast.FunctionDef(func.name, args3, [ast.Pass()], func.decorator_list, func.returns)
                                func3 = copy_location(func3, func)
                                decl.append(func3)
                    if decl:
                        class3 = ast.ClassDef(child.name, child.bases, child.keywords, decl, child.decorator_list)
                        class3 = copy_location(class3, child)
                        self.typedefs.append(class3)
        return node

class TypesTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.typing: Set[str] = set()
        self.removed: Set[str] = set()
    def visit_Subscript(self, node: ast.Subscript) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        logg.log(DEBUG_TYPING, "have SUB %s", node)
        if isinstance(node.value, ast.Name):
            subname = node.value.id
            if subname == "list" and want.replace_builtin_typing:
                self.typing.add("List")
                value2 = ast.Name("List")
                slice2: ast.expr = cast(ast.expr, self.generic_visit(node.slice))
                return ast.Subscript(value2, slice2)
            if subname == "dict" and want.replace_builtin_typing:
                self.typing.add("Dict")
                value3 = ast.Name("Dict")
                slice3: ast.expr = cast(ast.expr, self.generic_visit(node.slice))
                return ast.Subscript(value3, slice3)
            if subname == "Annotated" and want.replace_annotated_typing:
                if isinstance(node.slice, ast.Tuple):
                    self.removed.add("Annotated")
                    elems: ast.Tuple = node.slice
                    return self.generic_visit(elems.elts[0])
        return self.generic_visit(node)
    def visit_BinOp(self, node: ast.BinOp) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        logg.log(DEBUG_TYPING, "have BINOP %s", ast.dump(node))
        if isinstance(node.op, ast.BitOr):
            left: ast.expr = cast(ast.expr, self.generic_visit(node.left))
            right: ast.expr = cast(ast.expr, self.generic_visit(node.right))
            if isinstance(right, ast.Constant) and right.value is None:
                self.typing.add("Optional")
                optional2 = ast.Name("Optional")
                return ast.Subscript(optional2, left)
            elif isinstance(left, ast.Constant) and left.value is None:
                self.typing.add("Optional")
                optional3 = ast.Name("Optional")
                return ast.Subscript(optional3, right)
            else:
                self.typing.add("Union")
                value4 = ast.Name("Union")
                slice4 = ast.Tuple([left, right])
                return ast.Subscript(value4, slice4)
        return self.generic_visit(node)

class Types36(NamedTuple):
    annotation: ast.expr
    typing: Set[str]
    removed: Set[str]
def types36(ann: ast.expr) -> Types36:
    logg.log(DEBUG_TYPING, "types36: %s", ast.dump(ann))
    types = TypesTransformer()
    annotation = types.visit(ann)
    return Types36(annotation, types.typing, types.removed)

class OptionalTypes36(NamedTuple):
    annotation: Optional[ast.expr]
    typing: Set[str]
    removed: Set[str]

def types36_remove_typehints(ann: Optional[ast.expr]) -> OptionalTypes36:
    if ann and not want.remove_typehints:
        new1 = types36(ann)
        return OptionalTypes36(new1.annotation, new1.typing, new1.removed)
    return OptionalTypes36(None, set(), set())

def pyi_module(pyi: List[ast.stmt], type_ignores: Optional[List[TypeIgnore]] = None) -> ast.Module:
    """ generates the *.pyi part - based on the output of ExtractTypeHints """
    type_ignores1: List[TypeIgnore] = type_ignores if type_ignores is not None else []
    typing_extensions: List[str] = []
    typing_require: Set[str] = set()
    typing_removed: Set[str] = set()
    body: List[ast.stmt] = []
    for stmt in pyi:
        if isinstance(stmt, ast.ImportFrom):
            import1: ast.ImportFrom = stmt
            if import1.module in ["typing", "typing_extensions"]:
                for alias in import1.names:
                    if alias.name not in typing_extensions:
                        typing_extensions.append(alias.name)
        elif isinstance(stmt, ast.AnnAssign):
            assign1: ast.AnnAssign = stmt
            anng = assign1.annotation
            logg.log(DEBUG_TYPING, "anng %s", ast.dump(anng))
            newg = types36(anng)
            assign1.annotation = newg.annotation
            typing_require.update(newg.typing)
            typing_removed.update(newg.removed)
            body.append(stmt)
        elif isinstance(stmt, ast.FunctionDef):
            funcdef1: ast.FunctionDef = stmt
            for n, arg1 in enumerate(funcdef1.args.posonlyargs):
                ann1 = arg1.annotation
                if ann1:
                    logg.log(DEBUG_TYPING, "anp1[%i] %s", n, ast.dump(ann1))
                    new1 = types36(ann1)
                    arg1.annotation = new1.annotation
                    typing_require.update(new1.typing)
                    typing_removed.update(new1.removed)
            for n, arg1 in enumerate(funcdef1.args.args):
                ann1 = arg1.annotation
                if ann1:
                    logg.log(DEBUG_TYPING, "ann1[%i] %s", n, ast.dump(ann1))
                    new1 = types36(ann1)
                    arg1.annotation = new1.annotation
                    typing_require.update(new1.typing)
                    typing_removed.update(new1.removed)
            kwargs2 = funcdef1.args.kwonlyargs
            if kwargs2:
                logg.log(DEBUG_TYPING, "funcdef kwargs %s",  [ast.dump(a) for a in kwargs2])
                for k2, argk2 in enumerate(kwargs2):
                    ann2 = argk2.annotation
                    if ann2:
                        logg.log(DEBUG_TYPING, "ann2[%i] %s", k2, ast.dump(ann2))
                        newk2 = types36(ann2)
                        argk2.annotation = newk2.annotation
                        typing_require.update(newk2.typing)
                        typing_removed.update(newk2.removed)
            ann0 = funcdef1.returns
            if ann0:
                logg.log(DEBUG_TYPING, "ann0 %s",ast.dump(ann0))
                new0 = types36(ann0)
                funcdef1.returns = new0.annotation
                typing_require.update(new0.typing)
                typing_removed.update(new0.removed)
            body.append(stmt)
        elif isinstance(stmt, ast.ClassDef):
            classdef: ast.ClassDef = stmt
            for part in classdef.body:
                if isinstance(part, ast.AnnAssign):
                    assign: ast.AnnAssign = part
                    annv = assign.annotation
                    logg.log(DEBUG_TYPING, "annv %s", ast.dump(annv))
                    newv = types36(annv)
                    assign.annotation = newv.annotation
                    typing_require.update(newv.typing)
                    typing_removed.update(newv.removed)
                elif isinstance(part, ast.FunctionDef):
                    funcdef: ast.FunctionDef = part
                    for n, arg in enumerate(funcdef.args.posonlyargs):
                        annp = arg.annotation
                        if annp:
                            logg.log(DEBUG_TYPING, "annp[%i] %s", n, ast.dump(annp))
                            newp = types36(annp)
                            arg.annotation = newp.annotation
                            typing_require.update(newp.typing)
                            typing_removed.update(newp.removed)
                    for n, arg in enumerate(funcdef.args.args):
                        annp = arg.annotation
                        if annp:
                            logg.log(DEBUG_TYPING, "anna[%i] %s", n, ast.dump(annp))
                            newp = types36(annp)
                            arg.annotation = newp.annotation
                            typing_require.update(newp.typing)
                            typing_removed.update(newp.removed)
                    kwargs = funcdef.args.kwonlyargs
                    if kwargs:
                        for k, argk in enumerate(kwargs):
                            annk = argk.annotation
                            if annk:
                                logg.log(DEBUG_TYPING, "annk[%i] %s", k, ast.dump(annk))
                                newk = types36(annk)
                                argk.annotation = newk.annotation
                                typing_require.update(newk.typing)
                                typing_removed.update(newk.removed)
                    annr = funcdef.returns
                    if annr:
                        newr = types36(annr)
                        funcdef.returns = newr.annotation
                        typing_require.update(newr.typing)
                        typing_removed.update(newr.removed)
                else:
                    logg.warning("unknown pyi part %s", type(part))
            body.append(stmt)
        else:
            logg.warning("unknown pyi stmt %s", type(stmt))
            body.append(stmt)
    oldimports = [typ for typ in typing_extensions if typ not in typing_removed]
    newimports = [typ for typ in typing_require if typ not in oldimports]
    if newimports or oldimports:
        # these are effecivly only the generated from-typing imports coming from downgrading the builtin types
        imports = ast.ImportFrom(module="typing", names=[ast.alias(name) for name in sorted(newimports + oldimports)], level=0)
        body = [imports] + body
    typehints = ast.Module(body, type_ignores=type_ignores1)
    return typehints

def pyi_copy_imports(pyi: ast.Module, py1: ast.AST, py2: ast.AST) -> ast.Module:
    pyi_imports = DetectImportsTransformer()
    pyi_imports.visit(pyi)
    py1_imports = DetectImportsTransformer()
    py1_imports.visit(py1)
    py2_imports = DetectImportsTransformer()
    py2_imports.visit(py2)
    pyi_hints = DetectHints()
    pyi_hints.visit(pyi)
    logg.log(DEBUG_COPY, "found pyi used classes = %s", pyi_hints.classes)
    logg.log(DEBUG_COPY, "py1 imported %s", py1_imports.imported)
    logg.log(DEBUG_COPY, "py2 imported %s", py2_imports.imported)
    requiredimport = RequireImport()
    imports: Dict[str, str] = {}
    notfound: List[str] = []
    for name in pyi_hints.classes:
        if name not in imports:
            if name in py1_imports.importas:
                orig = py1_imports.importas[name]
                logg.info("found %s in py1: %s", name, orig)
                imports[name] = orig
                requiredimport.add((orig, name))
            elif "." in name:
                libname, _name = name.rsplit(".", )
                if libname in py1_imports.importas:
                    orig = py1_imports.importas[libname]
                    logg.info("found %s in py1: %s", libname, orig)
                    imports[name] = orig
                    requiredimport.add((orig, libname))
        if name not in imports:
            if name in py2_imports.importas:
                orig = py2_imports.importas[name]
                logg.info("found %s in py2: %s", name, orig)
                imports[name] = orig
                requiredimport.add((orig, name))
            elif "." in name:
                libname, _name = name.rsplit(".", )
                if libname in py2_imports.importas:
                    orig = py2_imports.importas[libname]
                    logg.info("found %s in py2: %s", libname, orig)
                    imports[name] = orig
                    requiredimport.add((orig, libname))
        if name not in imports:
            if name not in ["bool", "int", "float", "complex", "str", "bytes", "bytearray", "set"]: # "memoryview", "frozenset"
                notfound += [ name ]
        if notfound:
            logg.debug("name not found as import: %s", " ".join(notfound))
            logg.debug("py1 imports: %s", py1_imports.importas)
            logg.debug("py2 imports: %s", py2_imports.importas)
    tree = cast(ast.Module, requiredimport.visit(pyi))
    if want.replace_self_typing:
        selftypes = ReplaceSelfByTypevar()
        tree = selftypes.visit(tree)
        typingrequires = RequireImportFrom()
        typingrequires.importfrom("typing", *selftypes.typing)
        tree = cast(ast.Module, typingrequires.visit(tree))
    if want.remove_positional_pyi:
        posonly = RemovePosonlyArgs()
        tree = posonly.visit(tree)
    if want.replace_typeddict_pyi:
        typeddict = TypedDictToDictTransformer()
        tree = cast(ast.Module, typeddict.visit(tree))
        typedrequires = RequireImportFrom()
        typedrequires.remove(["typing.TypedDict"])
        tree = cast(ast.Module, typedrequires.visit(tree))
    return tree

# ............................................................................... MAIN


EACH_REMOVE3 = 1
EACH_APPEND2 = 2
EACH_INPLACE = 4
def transformfiles(args: List[str], eachfile: int = 0, outfile: str = "", pyi: str = NIX, stubs: str = NIX, run_python: str = NIX, minversion: Tuple[int, int] = (2,7), nowrite: bool = False) -> int:
    written: List[str] = []
    for arg in args:
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
        tree1 = ast_parse(text)
        try:
            transformers = StripPythonTransformer(minversion, filename=arg)
            tree = transformers.visit(tree1)
            typedefs = transformers.typedefs
        except TransformerSyntaxError as e:  # pragma: nocover
            if e.filename is None:
                e.filename = arg
            raise
        if want.show_dump:
            logg.log(NOTE, "%s: (before transformations)\n%s", arg, _beautify_dump(ast.dump(tree1)))
        if want.show_dump > 1:
            logg.log(NOTE, "%s: (after transformations)\n%s", arg, _beautify_dump(ast.dump(tree)))
        done = ast_unparse(tree)
        if want.show_dump > 2:
            logg.log(NOTE, "%s: (after transformations) ---------------- \n%s", arg, done)
        if run_python:
            running = run_python if "/" in run_python else F"/usr/bin/env {run_python}"
            if done.startswith("#!"):
                _, done2 = done.split("\n", 1)
            else:
                done2 = done
            done = F"#! {running}\n" + done2
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
            if out in ["", "."]:
                pass
            elif out in ["-"]:
                if done:
                    print(done)
            elif not nowrite:
                with open(out, "w", encoding="utf-8") as w:
                    w.write(done)
                    if done and not done.endswith("\n"):
                        w.write("\n")
                logg.log(NOTE, "written %s", out)
                written.append(out)
            if pyi or stubs:
                type_ignores: List[TypeIgnore] = []
                if isinstance(tree1, ast.Module):
                    type_ignores = tree1.type_ignores
                typehints = pyi_module(typedefs, type_ignores=type_ignores)
                typehints = pyi_copy_imports(typehints, tree1, tree)
                done = ast_unparse(typehints)
                if out in ["", ".", "-"]:
                    print("## typehints:")
                    print(done)
                else:
                    for suffix in [pyi, stubs]:
                        if not suffix:
                            continue
                        out_name, _ = os.path.splitext(out)
                        typehintsfile = suffix.replace("*", out_name) if "*" in suffix else out+suffix
                        logg.debug("typehints: %s", typehintsfile)
                        typehintsfiledir = os.path.dirname(typehintsfile)
                        if not os.path.isdir(typehintsfiledir):
                            os.makedirs(typehintsfiledir)
                        with open(typehintsfile, "w", encoding="utf-8") as w:
                            w.write(done)
                            if done and not done.endswith("\n"):
                                w.write("\n")
                        logg.log(NOTE, "written %s", typehintsfile)

    return 0

def _beautify_dump(x: str) -> str:
    return x.replace("body=[", "\n body=[").replace("FunctionDef(", "\n FunctionDef(").replace(", ctx=Load()",",.")

class StripPythonTransformer:
    minversion: Tuple[int, int]
    typedefs: List[ast.stmt]
    def __init__(self, minversion: Tuple[int, int] = (2,7), filename: str = NIX):
        self.minversion = minversion
        self.filename = filename
        self.typedefs = []
    def visit(self, tree: ast.AST) -> ast.AST:
        typingrequires = RequireImportFrom()
        importrequires = RequireImport()
        importrequiresfrom = RequireImportFrom()
        if want.fstring_from_var_locals_format:
            formatvarlocals = FStringFromVarLocalsFormat()
            formatvarlocals.filename = self.filename
            tree = formatvarlocals.visit(tree)
        if want.fstring_from_locals_format:
            formatlocals = FStringFromLocalsFormat()
            formatlocals.filename = self.filename
            tree = formatlocals.visit(tree)
        if want.replace_fstring:
            fstring = FStringToFormatTransformer()
            tree = fstring.visit(tree)
        if want.replace_namedtuple_class:
            namedtuples = NamedTupleToCollectionsTransformer()
            tree = namedtuples.visit(tree)
            importrequiresfrom.append(namedtuples.requiresfrom)
            self.typedefs.extend(namedtuples.typedefs)
        if want.replace_typeddict_class:
            typeddict = TypedDictToDictTransformer()
            tree = typeddict.visit(tree)
            importrequiresfrom.append(typeddict.requiresfrom)
            self.typedefs.extend(typeddict.typedefs)
        extracted = ExtractTypeHints()
        tree = extracted.visit(tree)
        self.typedefs.extend(extracted.typedefs)
        striphints = StripTypeHints()
        tree = striphints.visit(tree)
        typingrequires.importfrom("typing", *striphints.typing)
        typingrequires.removefrom("typing", *striphints.removed)
        if want.replace_self_typing:
            selftypes = ReplaceSelfByTypevar()
            tree = selftypes.visit(tree)
            typingrequires.importfrom("typing", *selftypes.typing)
        calls = DetectImportedFunctionCalls()
        calls.visit(tree)
        if want.show_dump:
            logg.log(HINT, "detected module imports:\n%s", "\n".join(calls.imported.keys()))
            logg.log(HINT, "detected function calls:\n%s", "\n".join(calls.found.keys()))
        if want.define_callable:
            if "callable" in calls.found:
                defs1 = DefineIfPython3(["def callable(x): return hasattr(x, '__call__')"], before=(3,2))
                tree = defs1.visit(tree)
        if want.datetime_fromisoformat:
            if "datetime.datetime.fromisoformat" in calls.found:
                isoformatdef = replace_datetime_fromisoformat(tree, calls)
                tree = isoformatdef.tree
                importrequires.append(isoformatdef.requires)
                importrequiresfrom.remove(isoformatdef.removed)
        if want.subprocess_run:
            if "subprocess.run" in calls.found:
                subprocessrundef = replace_subprocess_run(tree, calls, self.minversion)
                tree = subprocessrundef.tree
                importrequires.append(subprocessrundef.requires)
                importrequiresfrom.remove(subprocessrundef.removed)
        if want.time_monotonic:
            if "time.monotonic" in calls.found:
                monotonicdef = replace_time_monotonic(tree, calls)
                tree = monotonicdef.tree
                importrequires.append(monotonicdef.requires)
                importrequiresfrom.remove(monotonicdef.removed)
        if want.time_monotonic_ns:
            if "time.monotonic_ns" in calls.found:
                monotonicdef = replace_time_monotonic_ns(tree, calls)
                tree = monotonicdef.tree
                importrequires.append(monotonicdef.requires)
                importrequiresfrom.remove(monotonicdef.removed)
        if want.import_pathlib2:
            if "pathlib" in calls.imported:
                logg.log(HINT, "detected pathlib")
                pathlibname = calls.imported["pathlib"]
                pathlibdef = DefineIfPython2([F"import pathlib2 as {pathlibname}"], before=(3,3), # ..
                   or_else=[text4("import pathlib") if pathlibname == "pathlib" else text4(F"""import pathlib as {pathlibname}""")])
                pathlibdrop = DetectImportedFunctionCalls(noimport=["pathlib"])
                tree = pathlibdef.visit(pathlibdrop.visit(tree))
                importrequires.append(pathlibdef.requires)
        if want.import_backports_zoneinfo:
            if "zoneinfo" in calls.imported:
                logg.log(HINT, "detected zoneinfo")
                zoneinfoname = calls.imported["zoneinfo"]
                as_zoneinfo = F"as {zoneinfoname}" if zoneinfoname != "zoneinfo" else ""
                zoneinfodef = DefineIfPython2([F"from backports import zoneinfo {as_zoneinfo}"], before=(3,9), # ..
                   or_else=[text4("import zoneinfo") if zoneinfoname == "zoneinfo" else text4(F"""import zoneinfo as {zoneinfoname}""")])
                zoneinfodrop = DetectImportedFunctionCalls(noimport=["zoneinfo"])
                tree = zoneinfodef.visit(zoneinfodrop.visit(tree))
                importrequires.append(zoneinfodef.requires)
        if want.import_toml:
            if "tomllib" in calls.imported:
                logg.log(HINT, "detected tomllib")
                tomllibname = calls.imported["tomllib"]
                tomllibdef = DefineIfPython2([F"import toml as {tomllibname}"], before=(3,11), # ..
                   or_else=[text4("import tomllib") if tomllibname == "tomllib" else text4(F"""import tomllib as {tomllibname}""")])
                tomllibdrop = DetectImportedFunctionCalls(noimport=["tomllib"])
                tree = tomllibdef.visit(tomllibdrop.visit(tree))
                importrequires.append(tomllibdef.requires)
        if want.define_range:
            calls = DetectImportedFunctionCalls()
            calls.visit(tree)
            if "range" in calls.found:
                defs2 = DefineIfPython2(["range = xrange"])
                tree = defs2.visit(tree)
        if want.define_basestring:
            basetypes = ReplaceIsinstanceBaseType({"str": "basestring"})
            basetypes.visit(tree)
            if basetypes.replace:
                defs3 = DefineIfPython3(basetypes.defines)
                tree = defs3.visit(tree)
        if want.replace_walrus_operator:
            walrus = WalrusTransformer()
            tree = walrus.visit(tree)
            whwalrus = WhileWalrusTransformer()
            tree = whwalrus.visit(tree)
        futurerequires = RequireImportFrom()
        if want.define_print_function or want.define_float_division:
            calls2 = DetectImportedFunctionCalls()
            calls2.visit(tree)
            if "print" in calls.found and want.define_print_function:
                futurerequires.add("__future__.print_function")
            if calls.divs and want.define_float_division:
                futurerequires.add("__future__.division")
        if want.define_absolute_import:
            imps = DetectImportsTransformer()
            imps.visit(tree)
            relative = [imp for imp in imps.importfrom if imp.startswith(".")]
            if relative:
                futurerequires.add("__future__.absolute_import")
        tree = importrequiresfrom.visit(tree)
        tree = importrequires.visit(tree)
        tree = typingrequires.visit(tree)
        tree = futurerequires.visit(tree)
        # the __future__ imports must be first, so we add them last (if any)
        return tree

if __name__ == "__main__":
    sys.exit(main())
