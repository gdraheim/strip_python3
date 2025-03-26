#! /usr/bin/env python3.11
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,no-else-return,line-too-long,too-many-lines
# pylint: disable=too-many-instance-attributes,too-few-public-methods,too-many-branches,too-many-locals,too-many-nested-blocks,too-many-statements
# pylint: disable=wrong-import-order,wrong-import-position
""" easy way to transform and remove python3 typehints """

__copyright__ = "(C) 2025 Guido Draheim, licensed under MIT License"
__author__ = "Guido U. Draheim"
__version__ = "1.1.1123"

from typing import Set, List, Dict, Optional, Union, Tuple, cast, NamedTuple, TypeVar, Deque, Iterable
import sys
import re
import os
import os.path as fs
import configparser
import logging
from collections import deque
if sys.version_info >= (3,11,0):
    import tomllib
else:
    try:
        import tomli as tomllib # type: ignore[no-redef,import-untyped]
    except ImportError:
        try:
            import strip_qtoml_decoder as tomllib # type: ignore[no-redef,import-untyped]
        except ImportError:
            tomllib = None # type: ignore[assignment]
DEBUG_TOML = logging.DEBUG
DEBUG_TYPING = logging.DEBUG
NIX = ""
OK = True

DONE = (logging.ERROR + logging.WARNING) // 2
NOTE = (logging.INFO + logging.WARNING) // 2
HINT = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(DONE, "DONE")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(HINT, "HINT")
logg = logging.getLogger("strip" if __name__ == "__main__" else __name__.replace("/", "."))

if sys.version_info < (3,9,0):
    logg.info("python3.9 has ast.unparse()")
    logg.fatal("you need alteast python3.9 to run strip-python3!")
    sys.exit(os.EX_SOFTWARE)

# ........
# import ast
# import ast_comments as ast
import strip_ast_comments as ast  # pylint: disable=wrong-import-position

from ast import TypeIgnore

TypeAST = TypeVar("TypeAST", bound=ast.AST) # pylint: disable=invalid-name
def copy_location(new_node: TypeAST, old_node: ast.AST) -> TypeAST:
    """ similar to ast.copy_location """
    if hasattr(old_node, "lineno") and hasattr(old_node, "end_lineno"):
        setattr(new_node, "lineno", old_node.lineno)
        setattr(new_node, "end_lineno", old_node.end_lineno)
    return new_node

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

def to_int(x: str) -> int:
    if x.isdigit():
        return int(x)
    if x in ["y", "yes", "true", "True", "ok", "OK"]:
        return 1
    return 0

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
    import_pathlib2 = to_int(os.environ.get("PYTHON3_IMPORT_PATHLIB2", NIX))
    import_backports_zoneinfo = to_int(os.environ.get("PYTHON3_IMPORT_BACKBORTS_ZONEINFO", NIX))
    import_toml = to_int(os.environ.get("PYTHON3_IMPORT_TOML", NIX))

want = Want()

def read_defaults(*files: str) -> Dict[str, Union[str, int]]:
    settings: Dict[str, Union[str, int]] = {"verbose": 0, # ..
        "python-version": NIX, "pyi-version": NIX, "remove-typehints": 0, "remove-var-typehints": 0, # ..
        "remove-positionalonly": 0, "remove-pyi-positionalonly": 0, "no-remove-positionalonly": 0, "no-remove-pyi-positionalonly": 0, # ..
        "remove-keywordonly": 0, "no-remove-keywordonly": 0, # ..
        "define-print-function": 0, "no-define-print-function": 0, # ..
        "define-absolute-import": 0, "no-define-absolute-import": 0, # ..
        "define-float-division": 0, "no-define-float-division": 0, # ..
        "define-callable": 0, "no-define-callable": 0, # ..
        "define-basestring": 0, "no-define-basestring": 0, # ..
        "define-range": 0, "no-define-range": 0, # ..
        "replace-fstring": 0, "no-replace-fstring": 0, # ..
        "replace-walrus-operator": 0, "no-replace-walrus-operator": 0, # ..
        "replace-annotated-typing": 0, "no-replace-annotated-typing": 0, # ..
        "replace-builtin-typing": 0, "no-replace-builtin-typing": 0, # ..
        "replace-union-typing": 0, "no-replace-union-typing": 0, # ..
        "replace-self-typing": 0, "no-replace-self-typing": 0, # ..
        "datetime-fromisoformat": 0, "no-datetime-fromisoformat": 0, # ..
        "subprocess-run": 0, "no-subprocess-run": 0,  # ..
        "time-monotonic": 0, "no-time-monotonic": 0,  # ..
        "import-pathlib2": 0, "no-import-pathlib2": 0,  # ..
        "import-backports-zoneinfo": 0, "no-import-backports-zoneinfo": 0, # ..
        "import-toml": 0, "no-import-toml": 0,  # ..
    }

    for configfile in files:
        if fs.isfile(configfile):
            if configfile.endswith(".toml") and tomllib:
                logg.log(DEBUG_TOML, "found toml configfile %s", configfile)
                with open(configfile, "rb") as f:
                    conf = tomllib.load(f)
                    section1: Dict[str, Union[str, int, bool]] = {}
                    if "tool" in conf and "strip-python3" in conf["tool"]:
                        section1 = conf["tool"]["strip-python3"]
                    else:
                        logg.log(DEBUG_TOML, "have sections %s", list(section1.keys()))
                    if section1:
                        logg.log(DEBUG_TOML, "have section1 data:\n%s", section1)
                        for setting in section1:
                            if setting in settings:
                                oldvalue = settings[setting]
                                setvalue = section1[setting]
                                if isinstance(oldvalue, str):
                                    if isinstance(setvalue, str):
                                        settings[setting] = setvalue
                                    else:
                                        logg.error("%s[%s]: expecting str but found %s", configfile, setting, type(setvalue))
                                elif isinstance(oldvalue, int):
                                    if isinstance(setvalue, (int, float, bool)):
                                        settings[setting] = int(setvalue)
                                    else:
                                        logg.error("%s[%s]: expecting int but found %s", configfile, setting, type(setvalue))
                                else:  # pragma: nocover
                                    logg.error("%s[%s]: unknown setting type found %s", configfile, setting, type(setvalue))
                            else:
                                logg.error("%s[%s]: unknown setting found", configfile, setting)
                                logg.debug("%s: known options are %s", configfile, ", ".join(settings.keys()))
            elif configfile.endswith(".cfg"):
                logg.log(DEBUG_TOML, "found ini configfile %s", configfile)
                confs = configparser.ConfigParser()
                confs.read(configfile)
                if "strip-python3" in confs:
                    section2 = confs["strip-python3"]
                    logg.log(DEBUG_TOML, "have section2 data:\n%s", section2)
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
                                else:  # pragma: nocover
                                    logg.error("%s[%s]: unknown setting type found %s", configfile, option, setvalue)
                            else:
                                logg.error("%s[%s]: unknown setting found", configfile, option)
                                logg.debug("%s: known options are %s", configfile, ", ".join(settings.keys()))
            else:  # pragma: nocover
                logg.log(DEBUG_TOML, "unknown configfile found %s", configfile)
        else:
            logg.log(DEBUG_TOML, "no configfile found %s", configfile)
    return settings

def main() -> int:
    # global want
    defs = read_defaults("pyproject.toml", "setup.cfg")
    from optparse import OptionParser # pylint: disable=deprecated-module, import-outside-toplevel
    cmdline = OptionParser("%prog [options] file3.py", description=__doc__.strip(), epilog=": -o - : default is to print the type-stripped and back-transformed py code")
    cmdline.formatter.max_help_position = 37
    cmdline.add_option("-v", "--verbose", action="count", default=defs["verbose"], help="increase logging level")
    cmdline.add_option("--no-define-range", action="count", default=defs["no-define-range"], help="3.0 define range()")
    cmdline.add_option("--no-define-basestring", action="count", default=defs["no-define-basestring"], help="3.0 isinstance(str)")
    cmdline.add_option("--no-define-callable", "--noc", action="count", default=defs["no-define-callable"], help="3.2 callable(x)")
    cmdline.add_option("--no-define-print-function", "--nop", action="count", default=defs["no-define-print-function"], help="3.0 print() function")
    cmdline.add_option("--no-define-float-division", "--nod", action="count", default=defs["no-define-float-division"], help="3.0 float division")
    cmdline.add_option("--no-define-absolute-import", action="count", default=defs["no-define-absolute-import"], help="3.0 absolute import")
    cmdline.add_option("--no-datetime-fromisoformat", action="count", default=defs["no-datetime-fromisoformat"], help="3.7 datetime.fromisoformat")
    cmdline.add_option("--no-subprocess-run", action="count", default=defs["no-subprocess-run"], help="3.5 subprocess.run")
    cmdline.add_option("--no-time-monotonic", action="count", default=defs["no-time-monotonic"], help="3.3 time.monotonic")
    cmdline.add_option("--no-import-pathlib2", action="count", default=defs["no-import-pathlib2"], help="3.3 pathlib to python2 pathlib2")
    cmdline.add_option("--no-import-backports-zoneinfo", action="count", default=defs["no-import-backports-zoneinfo"], help="3.9 zoneinfo from backports")
    cmdline.add_option("--no-import-toml", action="count", default=defs["no-import-toml"], help="3.11 tomllib to external toml")
    cmdline.add_option("--no-replace-fstring", action="count", default=defs["no-replace-fstring"], help="3.6 f-strings")
    cmdline.add_option("--no-replace-walrus-operator", action="count", default=defs["no-replace-walrus-operator"], help="3.8 walrus-operator")
    cmdline.add_option("--no-replace-annotated-typing", action="count", default=defs["no-replace-annotated-typing"], help="3.9 Annotated[int, x] (in pyi)")
    cmdline.add_option("--no-replace-builtin-typing", action="count", default=defs["no-replace-builtin-typing"], help="3.9 list[int] (in pyi)")
    cmdline.add_option("--no-replace-union-typing", action="count", default=defs["no-replace-union-typing"], help="3.10 int|str (in pyi)")
    cmdline.add_option("--no-replace-self-typing", action="count", default=defs["no-replace-self-typing"], help="3.11 Self (in pyi)")
    cmdline.add_option("--no-remove-keywordonly", action="count", default=defs["no-remove-keywordonly"], help="3.0 keywordonly parameters")
    cmdline.add_option("--no-remove-positionalonly", action="count", default=defs["no-remove-positionalonly"], help="3.8 positionalonly parameters")
    cmdline.add_option("--no-remove-pyi-positionalonly", action="count", default=defs["no-remove-pyi-positionalonly"], help="3.8 positionalonly in *.pyi")
    cmdline.add_option("--define-range", action="count", default=defs["define-range"], help="3.0 define range() to xrange() iterator")
    cmdline.add_option("--define-basestring", action="count", default=defs["define-basestring"], help="3.0 isinstance(str) is basestring python2")
    cmdline.add_option("--define-callable", action="count", default=defs["define-callable"], help="3.2 callable(x) as in python2")
    cmdline.add_option("--define-print-function", action="count", default=defs["define-print-function"], help="3.0 print() or from __future__")
    cmdline.add_option("--define-float-division", action="count", default=defs["define-float-division"], help="3.0 float division or from __future__")
    cmdline.add_option("--define-absolute-import", action="count", default=defs["define-absolute-import"], help="3.0 absolute import or from __future__")
    cmdline.add_option("--datetime-fromisoformat", action="count", default=defs["datetime-fromisoformat"], help="3.7 datetime.fromisoformat or boilerplate")
    cmdline.add_option("--subprocess-run", action="count", default=defs["subprocess-run"], help="3.5 subprocess.run or use boilerplate")
    cmdline.add_option("--time-monotonic", action="count", default=defs["time-monotonic"], help="3.3 time.monotonic or use time.time")
    cmdline.add_option("--import-pathlib2", action="count", default=defs["no-import-pathlib2"], help="3.3 import pathlib2 as pathlib")
    cmdline.add_option("--import-backports-zoneinfo", action="count", default=defs["import-backports-zoneinfo"], help="3.9 import zoneinfo from backports")
    cmdline.add_option("--import-toml", action="count", default=defs["import-toml"], help="3.11 import toml as tomllib")
    cmdline.add_option("--replace-fstring", action="count", default=defs["replace-fstring"], help="3.6 f-strings to string.format")
    cmdline.add_option("--replace-walrus-operator", action="count", default=defs["replace-walrus-operator"], help="3.8 walrus 'if x := ():' to 'if x:'")
    cmdline.add_option("--replace-annotated-typing", action="count", default=defs["replace-annotated-typing"], help="3.9 Annotated[int, x] converted to int")
    cmdline.add_option("--replace-builtin-typing", action="count", default=defs["replace-builtin-typing"], help="3.9 list[int] converted to List[int]")
    cmdline.add_option("--replace-union-typing", action="count", default=defs["replace-union-typing"], help="3.10 int|str converted to Union[int,str]")
    cmdline.add_option("--replace-self-typing", action="count", default=defs["replace-self-typing"], help="3.11 Self converted to SelfClass TypeVar")
    cmdline.add_option("--remove-typehints", action="count", default=defs["remove-typehints"], help="3.5 function annotations and cast()")
    cmdline.add_option("--remove-keywordonly", action="count", default=defs["remove-keywordonly"], help="3.0 keywordonly parameters")
    cmdline.add_option("--remove-positionalonly", action="count", default=defs["remove-positionalonly"], help="3.8 positionalonly parameters")
    cmdline.add_option("--remove-pyi-positionalonly", action="count", default=defs["remove-pyi-positionalonly"], help="3.8 positionalonly parameters in *.pyi")
    cmdline.add_option("--remove-var-typehints", action="count", default=defs["remove-var-typehints"], help="only 3.6 variable annotations (typehints)")
    cmdline.add_option("--show", action="count", default=0, help="show transformer settings (from above)")
    cmdline.add_option("--pyi-version", metavar="3.6", default=defs["pyi-version"], help="set python version for py-includes")
    cmdline.add_option("--python-version", metavar="2.7", default=defs["python-version"], help="set python features by version")
    cmdline.add_option("-6", "--py36", action="count", default=0, help="set python feat to --python-version=3.6")
    cmdline.add_option("-V", "--dump", action="count", default=0, help="show ast tree before (and after) changes")
    cmdline.add_option("-1", "--inplace", action="count", default=0, help="file.py gets overwritten (+ file.pyi)")
    cmdline.add_option("-2", "--append2", action="count", default=0, help="file.py into file_2.py + file_2.pyi")
    cmdline.add_option("-3", "--remove3", action="count", default=0, help="file3.py into file.py + file.pyi")
    cmdline.add_option("-n", "--no-pyi", "--no-make-pyi", action="count", default=0, help="do not generate file.pyi includes")
    cmdline.add_option("-y", "--pyi", "--make-pyi", action="count", default=0, help="generate file.pyi includes as well")
    cmdline.add_option("-o", "--outfile", metavar="FILE", default=NIX, help="explicit instead of file3_2.py")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, NOTE - 5 * opt.verbose))
    pyi_version = (3,6)
    if opt.pyi_version:
        if len(opt.pyi_version) >= 3 and opt.pyi_version[1] == ".":
            pyi_version = int(opt.pyi_version[0]), int(opt.pyi_version[2:])
        else:
            logg.error("unknown --pyi-version %s", opt.pyi_version)
    back_version = (2,7)
    if opt.py36:
        back_version = (3,6)
    elif opt.python_version:
        if len(opt.python_version) >= 3 and opt.python_version[1] == ".":
            back_version = int(opt.python_version[0]), int(opt.python_version[2:])
        else:
            logg.error("unknown --python-version %s", opt.python_version)
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
    make_pyi = opt.pyi or opt.append2 or opt.remove3 or opt.inplace
    return transform(cmdline_args, eachfile=eachfile, outfile=opt.outfile, pyi=make_pyi and not opt.no_pyi, minversion=back_version)

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
    block: Deque[ast.AST]

    def __init__(self) -> None:
        self.block = deque()

    def visit(self, node: TypeAST) -> TypeAST:
        """Visit a node."""
        if isinstance(node, ast.Module):
            self.block.appendleft(node)
            modbody: List[ast.stmt] = []
            for stmt in node.body:
                logg.log(DEBUG_TYPING, "stmt Module %s", ast.dump(stmt))
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                for elem in visitor(stmt):
                    modbody.append(copy_location(elem, stmt))
            node.body = modbody
            self.block.popleft()
        else:
            nodes = self.generic_visit(node)
            if len(nodes) > 0:
                return nodes[0]
        return node
    def generic_visit(self, node: TypeAST) -> List[TypeAST]:
        if isinstance(node, ast.ClassDef):
            self.block.appendleft(node)
            classbody: List[ast.stmt] = []
            for stmt in node.body:
                logg.log(DEBUG_TYPING, "stmt ClassDef %s", ast.dump(stmt))
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        classbody.append(copy_location(elem, stmt))
                else:
                    classbody.append(result)
            node.body = classbody
            self.block.popleft()
        elif isinstance(node, ast.FunctionDef):
            self.block.appendleft(node)
            funcbody: List[ast.stmt] = []
            for stmt in node.body:
                logg.log(DEBUG_TYPING, "stmt FunctionDef %s", ast.dump(stmt))
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        funcbody.append(copy_location(elem, stmt))
                else:
                    funcbody.append(copy_location(result, stmt))
            node.body = funcbody
            self.block.popleft()
        elif isinstance(node, ast.With):
            self.block.appendleft(node)
            withbody: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        withbody.append(copy_location(elem, stmt))
                else:
                    withbody.append(copy_location(result, stmt))
            node.body = withbody
            self.block.popleft()
        elif isinstance(node, ast.If):
            self.block.appendleft(node)
            ifbody: List[ast.stmt] = []
            ifelse: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        ifbody.append(copy_location(elem, stmt))
                else:
                    ifbody.append(copy_location(result, stmt))
            for stmt in node.orelse:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        ifelse.append(copy_location(elem, stmt))
                else:
                    ifelse.append(copy_location(result, stmt))
            node.body = ifbody
            node.orelse = ifelse
            self.block.popleft()
        elif isinstance(node, ast.While):
            self.block.appendleft(node)
            whilebody: List[ast.stmt] = []
            whileelse: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        whilebody.append(copy_location(elem, stmt))
                else:
                    whilebody.append(copy_location(result, stmt))
            for stmt in node.orelse:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        whileelse.append(copy_location(elem, stmt))
                else:
                    whileelse.append(copy_location(result, stmt))
            node.body = whilebody
            node.orelse = whileelse
            self.block.popleft()
        elif isinstance(node, ast.For):
            self.block.appendleft(node)
            forbody: List[ast.stmt] = []
            forelse: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                for elem in visitor(stmt):
                    forbody.append(copy_location(elem, stmt))
            for stmt in node.orelse:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        forelse.append(copy_location(elem, stmt))
                else:
                    forelse.append(copy_location(result, stmt))
            node.body = forbody
            node.orelse = forelse
            self.block.popleft()
        elif isinstance(node, ast.Try):
            self.block.appendleft(node)
            trybody: List[ast.stmt] = []
            tryelse: List[ast.stmt] = []
            tryfinal: List[ast.stmt] = []
            for stmt in node.body:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        trybody.append(copy_location(elem, stmt))
                else:
                    trybody.append(copy_location(result, stmt))
            for excpt in node.handlers:
                excptbody: List[ast.stmt] = []
                for stmt in excpt.body:
                    method = 'visit_' + stmt.__class__.__name__
                    visitor = getattr(self, method, self.generic_visit)
                    result = visitor(stmt)
                    if isinstance(result, Iterable):
                        for elem in result:
                            excptbody.append(copy_location(elem, stmt))
                    else:
                        excptbody.append(copy_location(result, stmt))
                    excpt.body = excptbody
            for stmt in node.orelse:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        tryelse.append(copy_location(elem, stmt))
                else:
                    tryelse.append(copy_location(result, stmt))
            for stmt in node.finalbody:
                method = 'visit_' + stmt.__class__.__name__
                visitor = getattr(self, method, self.generic_visit)
                result = visitor(stmt)
                if isinstance(result, Iterable):
                    for elem in result:
                        tryfinal.append(copy_location(elem, stmt))
                else:
                    tryfinal.append(copy_location(result, stmt))
            node.body = trybody
            node.orelse = tryelse
            node.finalbody = tryfinal
            self.block.popleft()
        else:
            pass
        return [node]

class WalrusTransformer(BlockTransformer):
    def visit_If(self, node: ast.If) -> List[ast.stmt]:  # pylint: disable=invalid-name
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
    def visit_While(self, node: ast.If) -> List[ast.stmt]:  # pylint: disable=invalid-name
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

class DetectImports(ast.NodeTransformer):
    def __init__(self) -> None:
        ast.NodeTransformer.__init__(self)
        self.importfrom: Dict[str, Dict[str, str]] = {}
        self.imported: Dict[str, str] = {}
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
                    self.imported[origname] = symbol.asname or symbol.name
        return self.generic_visit(node)
    def visit_Import(self, node: ast.Import) -> Optional[ast.AST]:  # pylint: disable=invalid-name
        imports: ast.Import = node
        for symbol in imports.names:
            origname = symbol.name
            self.imported[origname] = symbol.asname or symbol.name
        return self.generic_visit(node)

class RequireImportFrom:
    def __init__(self, require: Optional[List[str]] = None) -> None:
        self.require = require if require is not None else []
    def add(self, *require: str) -> None:
        self.require += list(require)
    def append(self, requires: List[str]) -> None:
        self.require += requires
    def visit(self, node: ast.AST) -> ast.AST:
        if not self.require:
            return node
        imports = DetectImports()
        imports.visit(node)
        newimport: List[str] = []
        for require in self.require:
            if "." in require:
                library, function = require.split(require, 1)
                if library in imports.importfrom:
                    if function in imports.importfrom[library]:
                        logg.debug("%s already imported", require)
                    else:
                        newimport.append(require)
                else:
                    newimport.append(require)
        if not newimport:
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

        if imports.imported:
            body = []
            for stmt in module.body:
                if not isinstance(stmt, ast.ImportFrom) and not isinstance(stmt, ast.Import):
                    # find first Import/ImportFrom
                    body.append(stmt)
                elif done:
                    body.append(stmt)
                else:
                    for mod, funcs in mods.items():
                        body.append(ast.ImportFrom(mod, [ast.alias(name=func) for func in sorted(funcs)], 0))
                    body.append(stmt)
                    done = True
        if not done:
            body = []
            # have no Import/ImportFrom in file
            for stmt in module.body:
                if isinstance(stmt, (ast.Comment, ast.Constant)):
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
    def __init__(self, require: Optional[List[str]] = None) -> None:
        self.require = require if require is not None else []
    def add(self, *require: str) -> None:
        self.require += list(require)
    def append(self, requires: List[str]) -> None:
        self.require += requires
    def visit(self, node: ast.AST) -> ast.AST:
        if not self.require:
            return node
        imports = DetectImports()
        imports.visit(node)
        newimport: List[str] = []
        for require in self.require:
            if require not in imports.imported:
                newimport.append(require)
        if not newimport:
            return node
        if not isinstance(node, ast.Module):
            logg.warning("no module for new imports %s", newimport)
            return node
        module = cast(ast.Module, node)  # type: ignore[redundant-cast]
        body: List[ast.stmt] = []
        done = False
        simple: List[str] = []
        dotted: List[str] = []
        for new in newimport:
            if "." in new:
                if new not in dotted:
                    dotted.append(new)
            else:
                if new not in simple:
                    simple.append(new)
        if imports.imported:
            body = []
            for stmt in module.body:
                if not isinstance(stmt, ast.ImportFrom) and not isinstance(stmt, ast.Import):
                    # find first Import/ImportFrom
                    body.append(stmt)
                elif done:
                    body.append(stmt)
                else:
                    body.append(ast.Import([ast.alias(name=mod) for mod in sorted(simple)]))
                    for mod in sorted(dotted):
                        body.append(ast.Import([ast.alias(name=mod)]))
                    body.append(stmt)
                    done = True
        if not done:
            # have no Import/ImportFrom or hidden in if-blocks
            body = []
            for stmt in module.body:
                if isinstance(stmt, (ast.Comment, ast.Constant)):
                    # find first being not a Comment/String
                    body.append(stmt)
                elif done:
                    body.append(stmt)
                else:
                    body.append(ast.Import([ast.alias(name=mod) for mod in sorted(simple)]))
                    for mod in sorted(dotted):
                        body.append(ast.Import([ast.alias(name=mod)]))
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

class DetectFunctionCalls(ast.NodeTransformer):
    def __init__(self, replace: Optional[Dict[str, str]] = None, noimport: Optional[List[str]] = None) -> None:
        ast.NodeTransformer.__init__(self)
        self.imported: Dict[str, str] = {}
        self.importas: Dict[str, str] = {}
        self.found: Dict[str, int] = {}
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
    requires: List[str]
    def __init__(self, expr: List[str], atleast: Optional[Tuple[int, int]] = None, before: Optional[Tuple[int, int]] = None, orelse: Union[str, List[ast.stmt]] = NIX) -> None:
        self.atleast = atleast
        self.before = before
        self.requires = [] # output
        self.body = []
        if isinstance(orelse, str):
            if not orelse:
                self.orelse = []
            else:
                elseparsed: ast.Module = cast(ast.Module, ast.parse(orelse))
                self.orelse = elseparsed.body
        else:
            self.orelse = orelse
        for stmtlist in [cast(ast.Module, ast.parse(e)).body for e in expr]:
            self.body += stmtlist
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and self.body:
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
                elif before_imports or after_append:
                    body.append(stmt)
                else:
                    testcode = "sys.version_info < (3, 0)"
                    testparsed: ast.Module = cast(ast.Module, ast.parse(testcode))
                    assert isinstance(testparsed.body[0], ast.Expr)
                    testbody: ast.Expr = testparsed.body[0]
                    if isinstance(testbody.value, ast.Compare):
                        testcompare: ast.expr = testbody.value
                        if self.before:
                            testcode = "sys.version_info < ({}, {})".format(self.before[0], self.before[1])
                            testparsed = cast(ast.Module, ast.parse(testcode))
                            assert isinstance(testparsed.body[0], ast.Expr)
                            testbody = testparsed.body[0]
                            testcompare = testbody.value
                        if self.atleast:
                            testcode = "sys.version_info > ({}, {})".format(self.atleast[0], self.atleast[1])
                            testparsed = cast(ast.Module, ast.parse(testcode))
                            assert isinstance(testparsed.body[0], ast.Expr)
                            testbody = testparsed.body[0]
                            testatleast = testbody.value
                            testcompare = ast.BoolOp(op=ast.And(), values=[testatleast, testcompare])
                        before = self.before if self.before else (3,0)
                        logg.log(HINT, "python2 atleast %s before %s", self.atleast, before)
                    else:
                        logg.error("unexpected %s found for testcode: %s", type(testbody.value), testcode)  # and fallback to explicit ast-tree
                        testcompare = ast.Compare(left=ast.Subscript(value=ast.Attribute(value=ast.Name("sys"), attr="version_info"), slice=cast(ast.expr, ast.Index(value=ast.Num(0)))), ops=[ast.Lt()], comparators=[ast.Num(3)])
                    python2 = ast.If(test=testcompare, body=self.body, orelse=self.orelse)
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
    def __init__(self, expr: List[str], atleast: Optional[Tuple[int, int]] = None, before: Optional[Tuple[int, int]] = None, orelse: Union[str, List[ast.stmt]] = NIX) -> None:
        self.atleast = atleast
        self.before = before
        self.requires = [] # output
        self.body = []
        if isinstance(orelse, str):
            if not orelse:
                self.orelse = []
            else:
                elseparsed: ast.Module = cast(ast.Module, ast.parse(orelse))
                self.orelse = elseparsed.body
        else:
            self.orelse = orelse
        for stmtlist in [cast(ast.Module, ast.parse(e)).body for e in expr]:
            self.body += stmtlist
    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and self.body:
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
                elif before_imports or after_append:
                    body.append(stmt)
                else:
                    testcode = "sys.version_info >= (3, 0)"
                    testparsed: ast.Module = cast(ast.Module, ast.parse(testcode))
                    assert isinstance(testparsed.body[0], ast.Expr)
                    testbody: ast.Expr = testparsed.body[0]
                    if isinstance(testbody.value, ast.Compare):
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
                    else:
                        logg.error("unexpected %s found for testcode: %s", type(testbody.value), testcode)  # and fallback to explicit ast-tree
                        testcompare=ast.Compare(left=ast.Subscript(value=ast.Attribute(value=ast.Name("sys"), attr="version_info"), slice=cast(ast.expr, ast.Index(value=ast.Num(0)))), ops=[ast.GtE()], comparators=[ast.Num(3)])
                    python3 = ast.If(test=testcompare, body=self.body, orelse=self.orelse)
                    python3 = copy_location(python3, stmt)
                    body.append(python3)
                    body.append(stmt)
                    after_append = True
                    self.requires += [ "sys" ]
            module2 = ast.Module(body, module1.type_ignores)
            return module2
        else:
            return node

class FStringToFormat(ast.NodeTransformer):
    """ The 3.8 F="{a=}" syntax is resolved before ast nodes are generated. """
    def visit_FormattedValue(self, node: ast.FormattedValue) -> ast.Call:  # pylint: disable=invalid-name # pragma: nocover
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
                                if want.fstring_numbered:
                                    form += "{%i%s:%s}" % (num, conv, val.value)
                                else:
                                    form += "{%s:%s}" % (conv, val.value)
                            else:
                                logg.error("unknown part of format_spec in f-string: %s > %s", type(node), type(val))
                    else:
                        logg.error("unknown format_spec in f-string: %s", type(node))
                else:
                    if want.fstring_numbered:
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
                                if want.fstring_numbered:
                                    form += "{%i%s:%s}" % (num, conv, val.value)
                                else:
                                    form += "{%s:%s}" % (conv, val.value)
                            else:
                                logg.error("unknown part of format_spec in f-string: %s > %s", type(node), type(val))
                    else:
                        logg.error("unknown format_spec in f-string: %s", type(node))
                else:
                    if want.fstring_numbered:
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
                if want.remove_positional:
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
                if want.remove_keywordonly:
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
        func2 = ast.FunctionDef(func.name, args2, func.body, func.decorator_list)
        func2 = copy_location(func2, func)
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
                                    posonlyargs1.append(ast.arg(arg.arg))
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in funcdef1.args.args:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    functionargs1.append(ast.arg(arg.arg))
                                    if arg.annotation:
                                        annos += 1
                            if OK:
                                for arg in funcdef1.args.kwonlyargs:
                                    logg.debug("fun arg: %s", ast.dump(arg))
                                    kwonlyargs1.append(ast.arg(arg.arg))
                                    if arg.annotation:
                                        annos += 1
                            if vararg1 is not None:
                                if vararg1.annotation:
                                    annos += 1
                                vararg1 = ast.arg(vararg1.arg)
                            if kwarg1 is not None:
                                if kwarg1.annotation:
                                    annos += 1
                                kwarg1 = ast.arg(kwarg1.arg)
                            if not annos and not funcdef1.returns:
                                body.append(funcdef1)
                            else:
                                logg.debug("args: %s", ast.dump(funcdef1.args))
                                if not want.remove_typehints:
                                    rets2 = funcdef1.returns
                                    args2 = funcdef1.args
                                else:
                                    rets2 = None
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
                                if not want.remove_typehints:
                                    rets2 = func.returns
                                    args2 = func.args
                                else:
                                    rets2 = None
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

def pyi_module(pyi: List[ast.stmt], type_ignores: Optional[List[TypeIgnore]] = None) -> ast.Module:
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
        imports = ast.ImportFrom(module="typing", names=[ast.alias(name) for name in sorted(newimports + oldimports)], level=0)
        body = [imports] + body
    typehints = ast.Module(body, type_ignores=type_ignores1)
    return typehints

# ............................................................................... MAIN

EACH_REMOVE3 = 1
EACH_APPEND2 = 2
EACH_INPLACE = 4
def transform(args: List[str], eachfile: int = 0, outfile: str = "", pyi: int = 0, minversion: Tuple[int, int] = (2,7)) -> int:
    written: List[str] = []
    for arg in args:
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
        tree1 = ast.parse(text)
        types = TypeHints()
        tree = types.visit(tree1)
        strip = StripHints()
        tree = strip.visit(tree)
        if want.replace_fstring:
            fstring = FStringToFormat()
            tree = fstring.visit(tree)
        importrequires = RequireImport()
        calls = DetectFunctionCalls()
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
                isoformatdef = DefineIfPython3([F"def {fromisoformat}(x): return {datetime_module}.fromisoformat(x)"], atleast=(3,7), orelse=text4(F"""
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
                """))
                isoformatfunc = DetectFunctionCalls({"datetime.datetime.fromisoformat": fromisoformat})
                tree = isoformatdef.visit(isoformatfunc.visit(tree))
                importrequires.append(isoformatdef.requires)
        if want.subprocess_run:
            if "subprocess.run" in calls.found:
                subprocess_module = calls.imported["subprocess"]
                defname = subprocess_module + "_run"
                # there is a timeout value available since Python 3.3
                subprocessrundef33 = DefineIfPython3([F"{defname} = {subprocess_module}.run"], atleast=(3,5), orelse=text4(F"""
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
                """))
                subprocessrundef27 = DefineIfPython3([F"{defname} = {subprocess_module}.run"], atleast=(3,5), orelse=text4(F"""
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
                """))
                subprocessrundef = subprocessrundef33 if minversion >= (3,3) else subprocessrundef27
                subprocessrunfunc = DetectFunctionCalls({"subprocess.run": defname})
                tree = subprocessrundef.visit(subprocessrunfunc.visit(tree))
                importrequires.append(subprocessrundef.requires)
        if want.time_monotonic:
            if "time.monotonic" in calls.found:
                time_module = calls.imported["time"]
                defname = time_module + "_monotonic"
                monotonicdef = DefineIfPython3([F"{defname} = {time_module}.monotonic"], atleast=(3,3), # ..
                   orelse=F"def {defname}(): return time.time()")
                monotonicfunc = DetectFunctionCalls({"time.monotonic": defname})
                tree = monotonicdef.visit(monotonicfunc.visit(tree))
                importrequires.append(monotonicdef.requires)
            if "time.monotonic_ns" in calls.found:
                time_module = calls.imported["time"]
                defname = time_module + "_monotonic_ns"
                monotonicdef = DefineIfPython3([F"{defname} = {time_module}.monotonic_ns"], atleast=(3,7), # ..
                   orelse=F"def {defname}(): return int((time.time() - 946684800) * 1000000000)")
                monotonicfunc = DetectFunctionCalls({"time.monotonic_ns": defname})
                tree = monotonicdef.visit(monotonicfunc.visit(tree))
                importrequires.append(monotonicdef.requires)
        if want.import_pathlib2:
            if "pathlib" in calls.imported:
                logg.log(HINT, "detected pathlib")
                pathlibname = calls.imported["pathlib"]
                pathlibdef = DefineIfPython2([F"import pathlib2 as {pathlibname}"], before=(3,3), # ..
                   orelse=text4("import pathlib") if pathlibname == "pathlib" else text4(F"""import pathlib as {pathlibname}"""))
                pathlibdrop = DetectFunctionCalls(noimport=["pathlib"])
                tree = pathlibdef.visit(pathlibdrop.visit(tree))
                importrequires.append(pathlibdef.requires)
        if want.import_backports_zoneinfo:
            if "zoneinfo" in calls.imported:
                logg.log(HINT, "detected zoneinfo")
                zoneinfoname = calls.imported["zoneinfo"]
                as_zoneinfo = F"as {zoneinfoname}" if zoneinfoname != "zoneinfo" else ""
                zoneinfodef = DefineIfPython2([F"from backports import zoneinfo {as_zoneinfo}"], before=(3,9), # ..
                   orelse=text4("import zoneinfo") if zoneinfoname == "zoneinfo" else text4(F"""import zoneinfo as {zoneinfoname}"""))
                zoneinfodrop = DetectFunctionCalls(noimport=["zoneinfo"])
                tree = zoneinfodef.visit(zoneinfodrop.visit(tree))
                importrequires.append(zoneinfodef.requires)
        if want.import_toml:
            if "tomllib" in calls.imported:
                logg.log(HINT, "detected tomllib")
                tomllibname = calls.imported["tomllib"]
                tomllibdef = DefineIfPython2([F"import toml as {tomllibname}"], before=(3,11), # ..
                   orelse=text4("import tomllib") if tomllibname == "tomllib" else text4(F"""import tomllib as {tomllibname}"""))
                tomllibdrop = DetectFunctionCalls(noimport=["tomllib"])
                tree = tomllibdef.visit(tomllibdrop.visit(tree))
                importrequires.append(tomllibdef.requires)
        if want.define_range:
            calls = DetectFunctionCalls()
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
            calls2 = DetectFunctionCalls()
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
        tree = importrequires.visit(tree)
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
                typehints = pyi_module(types.pyi, type_ignores=type_ignores)
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
