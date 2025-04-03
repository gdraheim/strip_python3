#! /usr/bin/env python3.11
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,no-else-return,line-too-long,too-many-lines,too-many-arguments
# pylint: disable=too-many-instance-attributes,too-few-public-methods,too-many-branches,too-many-locals,too-many-nested-blocks,too-many-statements
# pylint: disable=wrong-import-order,wrong-import-position,use-list-literal,use-dict-literal
""" easy way to transform and remove python3 typehints """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "1.1.1134"

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
            import strip_qtoml_decoder as tomllib # type: ignore[no-redef,import-untyped]
        except ImportError:
            tomllib = None # type: ignore[assignment]
DEBUG_TOML = logging.DEBUG
DEBUG_TYPING = logging.DEBUG
DEBUG_COPY = logging.INFO
NIX = ""
OK = True

DONE = (logging.ERROR + logging.WARNING) // 2
NOTE = (logging.INFO + logging.WARNING) // 2
HINT = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(DONE, "DONE")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(HINT, "HINT")
logg = logging.getLogger("strip" if __name__ == "__main__" else __name__.replace("/", "."))

if sys.version_info < (3,9,0): # pragma: nocover
    logg.info("python3.9 has ast.unparse()")
    logg.fatal("you need alteast python3.9 to run strip-python3!")
    sys.exit(os.EX_SOFTWARE)

# ........
import ast as python_ast
# import ast_comments as ast
try:
    import strip_ast_comments as ast # type: ignore[import-untyped] # pylint: disable=wrong-import-position
except ImportError:
    # required for unittest.py
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    import strip_ast_comments as ast # type: ignore[import-untyped] # pylint: disable=wrong-import-position

if TYPE_CHECKING: # pragma: nocover
    NodeTransformer = python_ast.NodeTransformer
    NodeVisitor = python_ast.NodeVisitor
else:
    NodeTransformer = ast.NodeTransformer
    NodeVisitor = python_ast.NodeVisitor

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
    remove_pyi_positional = to_int(os.environ.get("PYTHON3_REMOVE_PYI_POSITIONAL", NIX))
    replace_fstring = to_int(os.environ.get("PYTHON3_REPLACE_FSTRING", NIX))
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

want = Want()

from optparse import OptionParser # pylint: disable=deprecated-module

def main() -> int:
    # global want
    # defs = read_defaults("pyproject.toml", "setup.cfg")
    cmdline = OptionParser("%prog [options] file3.py", description=__doc__.strip(), epilog=": -o - : default is to print the type-stripped and back-transformed py code")
    cmdline.formatter.max_help_position = 37
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="increase logging level")
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
    cmdline.add_option("--no-replace-walrus-operator", action="count", default=0, help="3.8 walrus-operator")
    cmdline.add_option("--no-replace-annotated-typing", action="count", default=0, help="3.9 Annotated[int, x] (in pyi)")
    cmdline.add_option("--no-replace-builtin-typing", action="count", default=0, help="3.9 list[int] (in pyi)")
    cmdline.add_option("--no-replace-union-typing", action="count", default=0, help="3.10 int|str (in pyi)")
    cmdline.add_option("--no-replace-self-typing", action="count", default=0, help="3.11 Self (in pyi)")
    cmdline.add_option("--no-remove-keywordonly", action="count", default=0, help="3.0 keywordonly parameters")
    cmdline.add_option("--no-remove-positionalonly", action="count", default=0, help="3.8 positionalonly parameters")
    cmdline.add_option("--no-remove-pyi-positionalonly", action="count", default=0, help="3.8 positionalonly in *.pyi")
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
    cmdline.add_option("--replace-walrus-operator", action="count", default=0, help="3.8 walrus 'if x := ():' to 'if x:'")
    cmdline.add_option("--replace-annotated-typing", action="count", default=0, help="3.9 Annotated[int, x] converted to int")
    cmdline.add_option("--replace-builtin-typing", action="count", default=0, help="3.9 list[int] converted to List[int]")
    cmdline.add_option("--replace-union-typing", action="count", default=0, help="3.10 int|str converted to Union[int,str]")
    cmdline.add_option("--replace-self-typing", action="count", default=0, help="3.11 Self converted to SelfClass TypeVar")
    cmdline.add_option("--remove-typehints", action="count", default=0, help="3.5 function annotations and cast()")
    cmdline.add_option("--remove-keywordonly", action="count", default=0, help="3.0 keywordonly parameters")
    cmdline.add_option("--remove-positionalonly", action="count", default=0, help="3.8 positionalonly parameters")
    cmdline.add_option("--remove-pyi-positionalonly", action="count", default=0, help="3.8 positionalonly parameters in *.pyi")
    cmdline.add_option("--remove-var-typehints", action="count", default=0, help="only 3.6 variable annotations (typehints)")
    cmdline.add_option("--show", action="count", default=0, help="show transformer settings (from above)")
    cmdline.add_option("--pyi-version", metavar="3.6", default=NIX, help="set python version for py-includes")
    cmdline.add_option("--python-version", metavar="2.7", default=NIX, help="set python features by version")
    cmdline.add_option("-V", "--dump", action="count", default=0, help="show ast tree before (and after) changes")
    cmdline.add_option("-1", "--inplace", action="count", default=0, help="file.py gets overwritten (+ file.pyi)")
    cmdline.add_option("-2", "--append2", action="count", default=0, help="file.py into file_2.py + file_2.pyi")
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py into file.py + file.pyi")
    cmdline.add_option("-6", "--py36", action="count", default=0, help="alias --no-make-pyi --python-version=3.6")
    cmdline.add_option("-9", "--py39", action="count", default=0, help="alias --no-make-pyi --python-version=3.9")
    cmdline.add_option("-n", "--no-make-pyi", "--no-pyi", action="count", default=0, help="do not generate file.pyi includes")
    cmdline.add_option("-y", "--make-pyi", "--pyi", action="count", default=0, help="generate file.pyi includes as well")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    cmdline_set_defaults_from(cmdline, want.toolsection, want.pyproject_toml, want.setup_cfg)
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, NOTE - 5 * opt.verbose))
    no_make_pyi = opt.no_make_pyi
    pyi_version = (3,6)
    if opt.pyi_version:
        if len(opt.pyi_version) >= 3 and opt.pyi_version[1] == ".":
            pyi_version = int(opt.pyi_version[0]), int(opt.pyi_version[2:])
        else:
            logg.error("can not decode --pyi-version %s", opt.pyi_version)
    back_version = (2,7)
    if opt.py36:
        back_version = (3,6)
        no_make_pyi = True
    elif opt.py39:
        back_version = (3,9)
        no_make_pyi = True
    elif opt.python_version:
        if len(opt.python_version) >= 3 and opt.python_version[1] == ".":
            back_version = int(opt.python_version[0]), int(opt.python_version[2:])
        else:
            logg.error("can not decode --python-version %s", opt.python_version)
    logg.debug("back_version %s pyi_version %s", back_version, pyi_version)
    if pyi_version < (3,8) or opt.remove_pyi_positionalonly:
        if not opt.no_remove_pyi_positionalonly:
            want.remove_pyi_positional = max(1, opt.remove_pyi_positionalonly)
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
    if opt.show:
        logg.log(NOTE, "%s = %s", "python-version-int", back_version)
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
        logg.log(NOTE, "%s = %s", "remove-pyi-positionalonly", want.remove_pyi_positional)
        logg.log(NOTE, "%s = %s", "remove-var-typehints", want.remove_var_typehints)
        logg.log(NOTE, "%s = %s", "remove-typehints", want.remove_typehints)
    if opt.dump:
        want.show_dump = int(opt.dump)
    eachfile = EACH_REMOVE3 if opt.remove3 else 0
    eachfile |= EACH_APPEND2 if opt.append2 else 0
    eachfile |= EACH_INPLACE if opt.inplace else 0
    make_pyi = opt.make_pyi or opt.append2 or opt.remove3 or opt.inplace
    return transform(cmdline_args, eachfile=eachfile, outfile=opt.outfile, pyi=make_pyi and not no_make_pyi, minversion=back_version)

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
    def generic_visit2(self, node: TypeAST, block: Deque[ast.AST]) -> Iterable[TypeAST]:
        if isinstance(node, ast.Module):
            block.appendleft(node)
            modulebody: List[ast.stmt] = []
            for stmt in node.body:
                logg.log(DEBUG_TYPING, "stmt Module %s", ast.dump(stmt))
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    modulebody.append(copy_location(elem, stmt))
            node.body = modulebody
            block.popleft()
        elif isinstance(node, ast.ClassDef):
            block.appendleft(node)
            classbody: List[ast.stmt] = []
            for stmt in node.body:
                logg.log(DEBUG_TYPING, "stmt ClassDef %s", ast.dump(stmt))
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    classbody.append(copy_location(elem, stmt))
            node.body = classbody
            block.popleft()
        elif isinstance(node, ast.FunctionDef):
            block.appendleft(node)
            funcbody: List[ast.stmt] = []
            for stmt in node.body:
                logg.log(DEBUG_TYPING, "stmt FunctionDef %s", ast.dump(stmt))
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    funcbody.append(copy_location(elem, stmt))
            node.body = funcbody
            block.popleft()
        elif isinstance(node, ast.With):
            block.appendleft(node)
            withbody: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    withbody.append(copy_location(elem, stmt))
            node.body = withbody
            block.popleft()
        elif isinstance(node, ast.If):
            block.appendleft(node)
            ifbody: List[ast.stmt] = []
            ifelse: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    ifbody.append(copy_location(elem, stmt))
            for stmt in node.orelse:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    ifelse.append(copy_location(elem, stmt))
            node.body = ifbody
            node.orelse = ifelse
            block.popleft()
        elif isinstance(node, ast.While):
            block.appendleft(node)
            whilebody: List[ast.stmt] = []
            whileelse: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    whilebody.append(copy_location(elem, stmt))
            for stmt in node.orelse:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    whileelse.append(copy_location(elem, stmt))
            node.body = whilebody
            node.orelse = whileelse
            block.popleft()
        elif isinstance(node, ast.For):
            block.appendleft(node)
            forbody: List[ast.stmt] = []
            forelse: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                for elem in visitor(stmt, block):
                    forbody.append(copy_location(elem, stmt))
            for stmt in node.orelse:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    forelse.append(copy_location(elem, stmt))
            node.body = forbody
            node.orelse = forelse
            block.popleft()
        elif isinstance(node, ast.Try):
            block.appendleft(node)
            trybody: List[ast.stmt] = []
            tryelse: List[ast.stmt] = []
            tryfinal: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    trybody.append(copy_location(elem, stmt))
            for excpt in node.handlers:
                excptbody: List[ast.stmt] = []
                for stmt in excpt.body:
                    method = 'visit2_' + stmt.__class__.__name__
                    visitor = getattr(self, method, self.generic_visit2)
                    result = visitor(stmt, block)
                    for elem in result:
                        excptbody.append(copy_location(elem, stmt))
                    excpt.body = excptbody
            for stmt in node.orelse:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    tryelse.append(copy_location(elem, stmt))
            for stmt in node.finalbody:
                method = 'visit2_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit2)
                result = visitor(stmt, block)
                for elem in result:
                    tryfinal.append(copy_location(elem, stmt))
            node.body = trybody
            node.orelse = tryelse
            node.finalbody = tryfinal
            block.popleft()
        else:
            pass
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

class DetectImports(NodeTransformer):
    importfrom: Dict[str, Dict[str, str]]
    imported: Dict[str, ast.stmt]
    asimport: Dict[str, str]
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.importfrom = {}
        self.imported = {}
        self.asimport = {}
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.ImportFrom = node
        if imports.module:
            modulename = ("." * imports.level) + imports.module
            if modulename not in self.importfrom:
                self.importfrom[modulename] = {}
            for symbol in imports.names:
                if symbol.name not in self.importfrom[modulename]:
                    self.importfrom[modulename][symbol.name] = symbol.asname or symbol.name
                    origname = modulename + "." + symbol.name
                    codename = symbol.name if not symbol.asname else symbol.asname
                    stmt = ast.ImportFrom(imports.module, [ast.alias(symbol.name, symbol.asname if symbol.asname != symbol.name else None)], imports.level)
                    self.imported[origname] = stmt
                    self.asimport[codename] = origname
        return self.generic_visit(node)
    def visit_Import(self, node: ast.Import) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.Import = node
        for symbol in imports.names:
            origname = symbol.name
            codename = symbol.name if not symbol.asname else symbol.asname
            stmt = ast.Import([ast.alias(symbol.name, symbol.asname if symbol.asname != symbol.name else None)])
            self.imported[origname] = stmt
            self.asimport[codename] = origname
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
        imports = DetectImports()
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
                if isinstance(stmt, (ast.Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
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
        imports = DetectImports()
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
                if isinstance(stmt, (ast.Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
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


class ReplaceIsinstanceBaseType(NodeTransformer):
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

class DetectImportedFunctionCalls(NodeTransformer):
    def __init__(self, replace: Optional[Dict[str, str]] = None, noimport: Optional[List[str]] = None) -> None:
        ast.NodeTransformer.__init__(self)
        self.imported: Dict[str, str] = {}
        self.importas: Dict[str, str] = {}
        self.found: Dict[str, str] = {} # funcname to callname
        self.calls: Dict[str, str] = {} # callname to funcname
        self.divs: int = 0
        self.replace = replace if replace is not None else {}
        self.noimport = noimport if noimport is not None else []
    def visit_Import(self, node: ast.Import) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        if node.names and node.names[0].name in self.noimport:
            return None # to remove the node
        for alias in node.names:
            if alias.asname:
                self.imported[alias.name] = alias.asname
                self.importas[alias.asname] = alias.name
            else:
                self.imported[alias.name] = alias.name
                self.importas[alias.name] = alias.name
        return self.generic_visit(node)
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.ImportFrom = node
        if imports.module:
            modulename = ("." * imports.level) + imports.module
            for symbol in imports.names:
                moname = modulename + "." + symbol.name
                asname = symbol.asname if symbol.asname else symbol.name
                self.imported[moname] = asname
                self.importas[asname] = moname
        return self.generic_visit(node)
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
            for elselist in [cast(ast.Module, ast.parse(part)).body for part in or_else]:
                self.orelse += elselist
        if orelse:
            for stmt in orelse:
                self.orelse.append(stmt)
        for stmtlist in [cast(ast.Module, ast.parse(e)).body for e in expr]:
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
                elif before_imports or after_append or isinstance(stmt, (ast.Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    body.append(stmt)
                else:
                    testcode = "sys.version_info < (3, 0)"
                    testparsed: ast.Module = cast(ast.Module, ast.parse(testcode))
                    assert isinstance(testparsed.body[0], ast.Expr)
                    testbody: ast.Expr = testparsed.body[0]
                    assert isinstance(testbody.value, ast.Compare)
                    testcompare: ast.expr = testbody.value
                    if self.before:
                        testcode = "sys.version_info < ({}, {})".format(self.before[0], self.before[1])
                        testparsed = cast(ast.Module, ast.parse(testcode))
                        assert isinstance(testparsed.body[0], ast.Expr)
                        testbody = testparsed.body[0]
                        testcompare = testbody.value
                    if self.atleast:
                        testcode = "sys.version_info >= ({}, {})".format(self.atleast[0], self.atleast[1])
                        testparsed = cast(ast.Module, ast.parse(testcode))
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
            for elselist in [cast(ast.Module, ast.parse(part)).body for part in or_else]:
                self.orelse += elselist
        if orelse:
            for stmt in orelse:
                self.orelse.append(stmt)
        for stmtlist in [cast(ast.Module, ast.parse(e)).body for e in expr]:
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
                elif before_imports or after_append or isinstance(stmt, (ast.Comment, ast.Constant)) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    body.append(stmt)
                else:
                    testcode = "sys.version_info >= (3, 0)"
                    testparsed: ast.Module = cast(ast.Module, ast.parse(testcode))
                    assert isinstance(testparsed.body[0], ast.Expr)
                    testbody: ast.Expr = testparsed.body[0]
                    assert isinstance(testbody.value, ast.Compare)
                    testcompare: ast.expr = testbody.value
                    if self.atleast:
                        testcode = "sys.version_info >= ({}, {})".format(self.atleast[0], self.atleast[1])
                        testparsed = cast(ast.Module, ast.parse(testcode))
                        assert isinstance(testparsed.body[0], ast.Expr)
                        testbody = testparsed.body[0]
                        testcompare = testbody.value
                    if self.before:
                        testcode = "sys.version_info < ({}, {})".format(self.before[0], self.before[1])
                        testparsed = cast(ast.Module, ast.parse(testcode))
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

class FStringToFormat(NodeTransformer):
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

class DetectAnnotation(NodeVisitor):
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

def types_in_annotation(annotation: ast.expr) -> Dict[str, str]:
    detect = DetectAnnotation()
    detect.visit(annotation)
    return detect.names

class DetectHints(NodeTransformer):
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

class StripHints(NodeTransformer):
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

class StripTypeHints:
    """ modify only the outer interface - global def, global class with methods """
    pyi: List[ast.stmt]
    typing: Set[str]
    removed: Set[str]
    def __init__(self) -> None:
        self.pyi = []
        self.typing = set()
        self.removed = set()
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module):
            body: List[ast.stmt] = []
            for child in node.body:
                if isinstance(child, ast.ImportFrom):
                    imports = child
                    body.append(child)
                    if imports.module == "typing":
                        imports3 = ast.ImportFrom(imports.module, imports.names, imports.level)
                        imports3 = copy_location(imports3, imports)
                        self.pyi.append(imports3)
                elif isinstance(child, ast.AnnAssign):
                    assign1: ast.AnnAssign = child
                    logg.debug("assign: %s", ast.dump(assign1))
                    if want.remove_typehints or want.remove_var_typehints:
                        if assign1.value is not None:
                            assign2 = ast.Assign(targets=[assign1.target], value=assign1.value)
                            assign2 = copy_location(assign2, assign1)
                            body.append(assign2)
                        else:
                            logg.debug("remove simple typehint")
                    else:
                        body.append(assign1)
                    assign3 = ast.AnnAssign(target=assign1.target, annotation=assign1.annotation, value=None, simple=assign1.simple)
                    self.pyi.append(assign3)
                elif isinstance(child, ast.FunctionDef):
                    funcdef1: ast.FunctionDef = child
                    logg.debug("funcdef: %s", ast.dump(funcdef1))
                    if OK:
                        if OK:
                            annos = 0
                            posonlyargs1: List[ast.arg] = []
                            functionargs1: List[ast.arg] = []
                            kwonlyargs1: List[ast.arg] = []
                            vararg1 = funcdef1.args.vararg
                            kwarg1 = funcdef1.args.kwarg
                            if OK:
                                for arg in funcdef1.args.posonlyargs:
                                    logg.debug("pos arg: %s", ast.dump(arg))
                                    if arg.annotation:
                                        annos += 1
                                    new1 = types36_remove_typehints(arg.annotation)
                                    posonlyargs1.append(ast.arg(arg.arg, new1.annotation))
                                    self.typing.update(new1.typing)
                                    self.removed.update(new1.removed)
                            if OK:
                                for arg in funcdef1.args.args:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    if arg.annotation:
                                        annos += 1
                                    new1 = types36_remove_typehints(arg.annotation)
                                    functionargs1.append(ast.arg(arg.arg, new1.annotation))
                                    self.typing.update(new1.typing)
                                    self.removed.update(new1.removed)
                            if OK:
                                for arg in funcdef1.args.kwonlyargs:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    if arg.annotation:
                                        annos += 1
                                    new1 = types36_remove_typehints(arg.annotation)
                                    kwonlyargs1.append(ast.arg(arg.arg, new1.annotation))
                                    self.typing.update(new1.typing)
                                    self.removed.update(new1.removed)
                            if vararg1 is not None:
                                if vararg1.annotation:
                                    annos += 1
                                new1 = types36_remove_typehints(vararg1.annotation)
                                vararg1 = ast.arg(vararg1.arg, new1.annotation)
                                self.typing.update(new1.typing)
                                self.removed.update(new1.removed)
                            if kwarg1 is not None:
                                if kwarg1.annotation:
                                    annos += 1
                                new1 = types36_remove_typehints(kwarg1.annotation)
                                kwarg1 = ast.arg(kwarg1.arg, new1.annotation)
                                self.typing.update(new1.typing)
                                self.removed.update(new1.removed)
                            if not annos and not funcdef1.returns:
                                body.append(funcdef1)
                            else:
                                logg.debug("args: %s", ast.dump(funcdef1.args))
                                newret = types36_remove_typehints(funcdef1.returns)
                                self.typing.update(newret.typing)
                                self.removed.update(newret.removed)
                                rets2 = newret.annotation
                                args2 = ast.arguments(posonlyargs1, functionargs1, vararg1, kwonlyargs1, # ..
                                    funcdef1.args.kw_defaults, kwarg1, funcdef1.args.defaults)
                                funcdef2 = ast.FunctionDef(funcdef1.name, args2, funcdef1.body, funcdef1.decorator_list, rets2)
                                funcdef2 = copy_location(funcdef2, funcdef1)
                                body.append(funcdef2)
                                funcargs3 = funcdef1.args
                                if posonlyargs1 and want.remove_pyi_positional:
                                    posonly3: List[ast.arg] = funcdef1.args.posonlyargs if not want.remove_pyi_positional else []
                                    functionargs3 = funcdef1.args.args if not want.remove_pyi_positional else funcdef1.args.posonlyargs + funcdef1.args.args
                                    funcargs3 = ast.arguments(posonly3, functionargs3, vararg1, funcdef1.args.kwonlyargs, # ..
                                           funcdef1.args.kw_defaults, kwarg1, funcdef1.args.defaults)
                                funcdef3 = ast.FunctionDef(funcdef1.name, funcargs3, [ast.Pass()], funcdef1.decorator_list, funcdef1.returns)
                                funcdef3 = copy_location(funcdef3, funcdef1)
                                self.pyi.append(funcdef3)
                elif isinstance(child, ast.ClassDef):
                    logg.debug("class: %s", ast.dump(child))
                    classname = child.name
                    preclass: Dict[str, ast.stmt] = {}
                    stmt: List[ast.stmt] = []
                    decl: List[ast.stmt] = []
                    for part in child.body:
                        if isinstance(part, ast.AnnAssign):
                            assign: ast.AnnAssign = part
                            logg.debug("assign: %s", ast.dump(assign))
                            if want.remove_typehints or want.remove_var_typehints:
                                if assign.value is not None:
                                    assign2 = ast.Assign(targets=[assign.target], value=assign.value)
                                    assign2 = copy_location(assign2, assign)
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
                                    if arg.annotation:
                                        annos += 1
                                    new1 = types36_remove_typehints(arg.annotation, classname)
                                    posonlyargs.append(ast.arg(arg.arg, new1.annotation))
                                    self.typing.update(new1.typing)
                                    self.removed.update(new1.removed)
                                    preclass.update(new1.preclass)
                            if OK:
                                for arg in func.args.args:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    if arg.annotation:
                                        annos += 1
                                    new1 = types36_remove_typehints(arg.annotation, classname)
                                    functionargs.append(ast.arg(arg.arg, new1.annotation))
                                    self.typing.update(new1.typing)
                                    self.removed.update(new1.removed)
                                    preclass.update(new1.preclass)
                            if OK:
                                for arg in func.args.kwonlyargs:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    if arg.annotation:
                                        annos += 1
                                    new1 = types36_remove_typehints(arg.annotation, classname)
                                    kwonlyargs.append(ast.arg(arg.arg, new1.annotation))
                                    self.typing.update(new1.typing)
                                    self.removed.update(new1.removed)
                                    preclass.update(new1.preclass)
                            if vargarg is not None:
                                if vargarg.annotation:
                                    annos += 1
                                new1 = types36_remove_typehints(vargarg.annotation, classname)
                                vargarg = ast.arg(vargarg.arg, new1.annotation)
                                self.typing.update(new1.typing)
                                self.removed.update(new1.removed)
                                preclass.update(new1.preclass)
                            if kwarg is not None:
                                if kwarg.annotation:
                                    annos += 1
                                new1 = types36_remove_typehints(kwarg.annotation, classname)
                                kwarg = ast.arg(kwarg.arg, new1.annotation)
                                self.typing.update(new1.typing)
                                self.removed.update(new1.removed)
                                preclass.update(new1.preclass)
                            if not annos and not func.returns:
                                stmt.append(func)
                            else:
                                logg.debug("args: %s", ast.dump(func.args))
                                newret = types36_remove_typehints(func.returns, classname)
                                self.typing.update(newret.typing)
                                self.removed.update(newret.removed)
                                preclass.update(newret.preclass)
                                rets2 = newret.annotation
                                args2 = ast.arguments(posonlyargs, functionargs, vargarg, kwonlyargs, # ..
                                       func.args.kw_defaults, kwarg, func.args.defaults)
                                func2 = ast.FunctionDef(func.name, args2, func.body, func.decorator_list, rets2)
                                func2 = copy_location(func2, func)
                                stmt.append(func2)
                                args3 = func.args
                                if posonlyargs and want.remove_pyi_positional:
                                    posonlyargs3: List[ast.arg] = func.args.posonlyargs if not want.remove_pyi_positional else []
                                    functionargs3 = func.args.args if not want.remove_pyi_positional else func.args.posonlyargs + func.args.args
                                    args3 = ast.arguments(posonlyargs3, functionargs3, vargarg, func.args.kwonlyargs, # ..
                                           func.args.kw_defaults, kwarg, func.args.defaults)
                                func3 = ast.FunctionDef(func.name, args3, [ast.Pass()], func.decorator_list, func.returns)
                                func3 = copy_location(func3, func)
                                decl.append(func3)
                        else:
                            stmt.append(part)
                    if not stmt:
                        stmt.append(ast.Pass())
                    for preclassname in sorted(preclass):
                        preclassdef = preclass[preclassname]
                        logg.log(DEBUG_TYPING, "preclass: %s", ast.dump(preclassdef))
                        body.append(preclassdef)
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

class TypesTransformer(NodeTransformer):
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
    preclass: Dict[str, ast.stmt]
def types36(ann: ast.expr, classname: Optional[str] = None) -> Types36:
    logg.log(DEBUG_TYPING, "types36: %s", ast.dump(ann))
    if isinstance(ann, ast.Name) and ann.id == "Self" and classname and want.replace_self_typing:
        selfclass = F"Self{classname}"
        newann = ast.Name(selfclass)
        decl: Dict[str, ast.stmt] = {}
        typevar = ast.Call(ast.Name("TypeVar"), [ast.Constant(selfclass)], [ast.keyword("bound", ast.Constant(classname))])
        typevar = copy_location(typevar, ann)
        stmt = ast.Assign([ast.Name(selfclass)], typevar)
        stmt = copy_location(stmt, ann)
        decl[selfclass] = stmt
        typing = set()
        typing.add("TypeVar")
        logg.log(DEBUG_TYPING, "self decl: %s", ast.dump(stmt))
        return Types36(newann, typing, set(), decl)
    else:
        types = TypesTransformer()
        annotation = types.visit(ann)
        return Types36(annotation, types.typing, types.removed, {})

class OptionalTypes36(NamedTuple):
    annotation: Optional[ast.expr]
    typing: Set[str]
    removed: Set[str]
    preclass: Dict[str, ast.stmt]

def types36_remove_typehints(ann: Optional[ast.expr], classname: Optional[str] = None) -> OptionalTypes36:
    if ann and not want.remove_typehints:
        new1 = types36(ann, classname)
        return OptionalTypes36(new1.annotation, new1.typing, new1.removed, new1.preclass)
    return OptionalTypes36(None, set(), set(), {})

def pyi_module(pyi: List[ast.stmt], type_ignores: Optional[List[TypeIgnore]] = None) -> ast.Module:
    """ generates the *.pyi part - based on the output of StripTypeHints """
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
            classname = classdef.name
            preclass: Dict[str, ast.stmt] = {}
            for part in classdef.body:
                if isinstance(part, ast.AnnAssign):
                    assign: ast.AnnAssign = part
                    annv = assign.annotation
                    logg.log(DEBUG_TYPING, "annv %s", ast.dump(annv))
                    newv = types36(annv, classname)
                    assign.annotation = newv.annotation
                    typing_require.update(newv.typing)
                    typing_removed.update(newv.removed)
                    preclass.update(newv.preclass)
                elif isinstance(part, ast.FunctionDef):
                    funcdef: ast.FunctionDef = part
                    logg.log(DEBUG_TYPING, "method args %s",  [ast.dump(a) for a in funcdef.args.args])
                    for n, arg in enumerate(funcdef.args.args):
                        annp = arg.annotation
                        if annp:
                            logg.log(DEBUG_TYPING, "annp[%i] %s", n, ast.dump(annp))
                            newp = types36(annp, classname)
                            arg.annotation = newp.annotation
                            typing_require.update(newp.typing)
                            typing_removed.update(newp.removed)
                            preclass.update(newp.preclass)
                    kwargs = funcdef.args.kwonlyargs
                    if kwargs:
                        logg.log(DEBUG_TYPING, "method kwargs %s",  [ast.dump(a) for a in kwargs])
                        for k, argk in enumerate(kwargs):
                            annk = argk.annotation
                            if annk:
                                logg.log(DEBUG_TYPING, "annk[%i] %s", k, ast.dump(annk))
                                newk = types36(annk, classname)
                                argk.annotation = newk.annotation
                                typing_require.update(newk.typing)
                                typing_removed.update(newk.removed)
                                preclass.update(newk.preclass)
                    annr = funcdef.returns
                    if annr:
                        newr = types36(annr, classname)
                        funcdef.returns = newr.annotation
                        typing_require.update(newr.typing)
                        typing_removed.update(newr.removed)
                        preclass.update(newr.preclass)
                else:
                    logg.warning("unknown pyi part %s", type(part))
            for preclassname in sorted(preclass):
                preclassdef = preclass[preclassname]
                logg.log(DEBUG_TYPING, "self preclass: %s", ast.dump(preclassdef))
                body.append(preclassdef)
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
    pyi_imports = DetectImports()
    pyi_imports.visit(pyi)
    py1_imports = DetectImports()
    py1_imports.visit(py1)
    py2_imports = DetectImports()
    py2_imports.visit(py2)
    pyi_hints = DetectHints()
    pyi_hints.visit(pyi)
    logg.log(DEBUG_COPY, "found pyi used classes = %s", pyi_hints.classes)
    logg.log(DEBUG_COPY, "py1 imported %s", py1_imports.imported.values())
    logg.log(DEBUG_COPY, "py2 imported %s", py2_imports.imported.values())
    requiredimport = RequireImport()
    imports: Dict[str, str] = {}
    notfound: List[str] = []
    for name in pyi_hints.classes:
        if name not in imports:
            if name in py1_imports.asimport:
                orig = py1_imports.asimport[name]
                logg.info("found %s in py1: %s", name, orig)
                imports[name] = orig
                requiredimport.add((orig, name))
            elif "." in name:
                libname, _name = name.rsplit(".", )
                if libname in py1_imports.asimport:
                    orig = py1_imports.asimport[libname]
                    logg.info("found %s in py1: %s", libname, orig)
                    imports[name] = orig
                    requiredimport.add((orig, libname))
        if name not in imports:
            if name in py2_imports.asimport:
                orig = py2_imports.asimport[name]
                logg.info("found %s in py2: %s", name, orig)
                imports[name] = orig
                requiredimport.add((orig, name))
            elif "." in name:
                libname, _name = name.rsplit(".", )
                if libname in py2_imports.asimport:
                    orig = py2_imports.asimport[libname]
                    logg.info("found %s in py2: %s", libname, orig)
                    imports[name] = orig
                    requiredimport.add((orig, libname))
        if name not in imports:
            if name not in ["bool", "int", "float", "complex", "str", "bytes", "bytearray", "set"]: # "memoryview", "frozenset"
                notfound += [ name ]
        if notfound:
            logg.debug("name not found as import: %s", " ".join(notfound))
            logg.debug("py1 imports: %s", py1_imports.asimport)
            logg.debug("py2 imports: %s", py2_imports.asimport)
    return cast(ast.Module, requiredimport.visit(pyi))

# ............................................................................... MAIN

EACH_REMOVE3 = 1
EACH_APPEND2 = 2
EACH_INPLACE = 4
def transform(args: List[str], eachfile: int = 0, outfile: str = "", pyi: int = 0, minversion: Tuple[int, int] = (2,7)) -> int:
    written: List[str] = []
    for arg in args:
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
        typingrequires = RequireImportFrom()
        tree1 = ast.parse(text)
        striptypes = StripTypeHints()
        tree = striptypes.visit(tree1)
        striphints = StripHints()
        tree = striphints.visit(tree)
        typingrequires.importfrom("typing", *striptypes.typing)
        typingrequires.removefrom("typing", *striptypes.removed)
        typingrequires.importfrom("typing", *striphints.typing)
        typingrequires.removefrom("typing", *striphints.removed)
        if want.replace_fstring:
            fstring = FStringToFormat()
            tree = fstring.visit(tree)
        importrequires = RequireImport()
        importrequiresfrom = RequireImportFrom()
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
                importrequires.append(isoformatdef.requires)
                importrequiresfrom.remove(["datetime.datetime.fromisoformat"])
        if want.subprocess_run:
            if "subprocess.run" in calls.found:
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
                importrequires.append(subprocessrundef.requires)
                importrequiresfrom.remove(["subprocess.run"])
        if want.time_monotonic:
            if "time.monotonic" in calls.found:
                time_module = calls.imported["time"]
                defname = time_module + "_monotonic"
                monotonicdef = DefineIfPython3([F"{defname} = {time_module}.monotonic"], atleast=(3,3), # ..
                   or_else=[F"def {defname}(): return time.time()"])
                monotonicfunc = DetectImportedFunctionCalls({"time.monotonic": defname})
                tree = monotonicdef.visit(monotonicfunc.visit(tree))
                importrequires.append(monotonicdef.requires)
                importrequiresfrom.remove(["time.monotonic"])
        if want.time_monotonic_ns:
            if "time.monotonic_ns" in calls.found:
                if "time" in calls.imported:
                    time_module = calls.imported["time"]
                else:
                    time_module = "time"
                    importrequires.append(["time"])
                defname = time_module + "_monotonic_ns"
                monotonicdef = DefineIfPython3([F"{defname} = {time_module}.monotonic_ns"], atleast=(3,7), # ..
                   or_else=[F"def {defname}(): return int((time.time() - 946684800) * 1000000000)"])
                monotonicfunc = DetectImportedFunctionCalls({"time.monotonic_ns": defname})
                tree = monotonicdef.visit(monotonicfunc.visit(tree))
                importrequires.append(monotonicdef.requires)
                importrequiresfrom.remove(["time.monotonic_ns"])
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
            imps = DetectImports()
            imps.visit(tree)
            relative = [imp for imp in imps.importfrom if imp.startswith(".")]
            if relative:
                futurerequires.add("__future__.absolute_import")
        tree = importrequiresfrom.visit(tree)
        tree = importrequires.visit(tree)
        tree = typingrequires.visit(tree)
        tree = futurerequires.visit(tree)
        # the __future__ imports must be first, so we add them last (if any)
        if want.show_dump:
            logg.log(NOTE, "%s: (before transformations)\n%s", arg, beautify_dump(ast.dump(tree1)))
        if want.show_dump > 1:
            logg.log(NOTE, "%s: (after transformations)\n%s", arg, beautify_dump(ast.dump(tree)))
        done = ast.unparse(tree)
        if want.show_dump > 2:
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
            if out in ["", "."]:
                pass
            elif out in ["-"]:
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
                type_ignores: List[TypeIgnore] = []
                if isinstance(tree1, ast.Module):
                    type_ignores = tree1.type_ignores
                typehints = pyi_module(striptypes.pyi, type_ignores=type_ignores)
                typehints = pyi_copy_imports(typehints, tree1, tree)
                done = ast.unparse(typehints)
                if out in ["", ".", "-"]:
                    print("## typehints:")
                    print(done)
                else:
                    with open(typehintsfile, "w", encoding="utf-8") as w:
                        w.write(done)
                        if done and not done.endswith("\n"):
                            w.write("\n")
    return 0

def beautify_dump(x: str) -> str:
    return x.replace("body=[", "\n body=[").replace("FunctionDef(", "\n FunctionDef(").replace(", ctx=Load()",",.")


if __name__ == "__main__":
    sys.exit(main())
