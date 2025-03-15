[![Type Check](https://github.com/gdraheim/strip_python3/actions/workflows/typecheck.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/strip_python3/actions/workflows/typecheck.yml)
[![Lint Check](https://github.com/gdraheim/strip_python3/actions/workflows/lintcheck.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/strip_python3/actions/workflows/lintcheck.yml)
[![Unit Tests](https://github.com/gdraheim/strip_python3/actions/workflows/unittests.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/strip_python3/actions/workflows/unittests.yml)
[![Code Coverage](https://img.shields.io/badge/84%20test-92%25%20coverage-brightgreen)](https://github.com/gdraheim/strip_python3/blob/main/strip_python3.tests.py)
[![PyPI version](https://badge.fury.io/py/strip_python3.svg)](https://pypi.org/project/strip-python3/)


# remove python3 typehints and transform source code to older python compatibility

This project has been inspired by `'strip-hints'` and `'py-backwards'` but it is
now based on the Python 3.9+ standard library's `'ast.unparse()'`. More specifically
it is using `'ast_comments'` to keep the comments. The implementation wants to make
it very easy so that you can add your own source code transformations to support
compatibility with older python versions.

The `'strip-python3'` tool can extract typehints to `'*.pyi'` file containing only
the outer object-oriented interface. That allows you to ship modern typed python3
code to older systems, possibly even having only python2 preinstalled. The extra
pyi however will allow to run it on older systems with a python3.6 installed.

The default configuration is to strip the `*.py` file to python2 syntax that can 
also work in python3 (using `__print_function__`), and (when using `-2` or `-3`)
to put a `*.pyi` file next to it containing the typehints in a syntax compatible 
with python3.6. When not using `-2` or `-3` it just prints the type-stripped and
backward-transformed python script to stdout.

# references

* https://github.com/t3rn0/ast-comments/blob/master/ast_comments.py (copied)
* https://github.com/python/typed_ast (archived)
* https://github.com/nvbn/py-backwards (stopped)
* https://github.com/abarker/strip-hints (still active)

# background

The "typed_ast" project was started in April 2016 showing a way to handle type comments.
The "py-backwards" project delivered an "unparse()" function for "typed_ast" in May 2017.
It also showed a generic approach to code transformers. However the syntactic sugar for
python3 grew over time and with only the standard "ast.parse()" to understand all features. 
Since  Python 3.8 in 2019 the "typed_ast" project was officialy discontinued, and finally
archived in 2023. Since Python 3.9 in 2020 the standard "ast" module got its own "unparse()" 
function, basically taking over the approach from "py-backwards". That's nice. The only 
missing part was that standard python does not even load comments. But in 2022 the 
"ast-comments" project showed how to hook into the standard module for that - the 
standard python3's "ast.parse()" got an "enrich()" phase for adding "Comment" nodes, 
and the standard python3 Unparser class got a "handle_Comment" method to generate decent 
source code back from it.

Since then the standard python3 features a NodeTransformer class that is supposedly
making it easy to rewrite python code. However we are missing examples - if it is
used then it is buried deep in other projects. I would like to assemble some of these
python code transformations, specifically for removing newer features so that python
code can be shipped and used on older systems with some possibly archaic python version.
The "py-backwards" has stopped at a point somehwere around python 3.6, so a new start
is required with a code base that makes it easier to get contributions by users.

Specifically for removing typehints, the "strip-hints" project shows how to use the
standard python "tokenizer" module which is clearly better than using some grep/sed
style text transformations. In both variants however you need to guess what kind of code
you have on a specific line, which is where "ast"-based approaches have a much easier
time. The standard python3 "unparse()" is however producing source code that is 
formatted already good enough for shipping via pypi and other distribution channels. 
The differences to the output of code beautyfiers have become minimal. Note however 
that the code removal does sometimes make comments appear on lines where they don't 
belong to.

# configuration

Configuration occurs in this order - with last overriding first
 * environment variables - on `PYTHON3_REMOVE_POSITIONAL=true`
 * setup.cfg settings -  in `[strip-python3]` on `remove_positional=true`
 * pyproject.toml settings - in `[tool.strip-python3]` on `remove_positional=true`
 * commandline options - using `--remove-positional` option
 * setup.cfg python-version in `[strip-python3]` on `python_version=3.6`
 * pyproject.toml python-version - in `[toml.strip-python3]` on `python_version=3.6`
 * commandline python-version - using `--python-version=3.6`
 * setup.cfg no-setting `[strip-python3]` on `no_remove_positional=true`
 * pyproject.toml no-setting - in `[toml.strip-python3]` on `no_remove_positional=true`
 * commandline no-setting - using `--no-remove-positional` option

 Some implementation options can be selected only by environment variables to
 allow for extended testing. They don't show up as commandline options while
 you can see most configuration options from `strip_python3.py --help`.
 
# transformations

Transformations are automatically selected by the minimum target python version
that is given by --python-version=3.6 (which has a shorthand --py36). The default
is to support even python2.

Each transformation can be selectivly enabled or disabled. This can also be done
in a pyproject.toml `[tool.strip-python3]` or setup.cfg `[strip-python3]` section.
The names are the same as the commandline options, just without a leading "--".

## define-print-function

If `print()` is used then `from __future__ import print_function` is added
if python2 compatibility is requested.

## define-float-division

If `/` is used then `from __future__ import division` is added
if python2 compatibility is requested.

## define-absolute-import

If `.localtypes` is used then `from __future__ import absolute_import` is added
if python2 compatibility is requested.

## define-basestring

If `isinstance(x, str)` is used then each is replaced by `isinstance(x, basestring)`
if python2 compatibility is requested. It does also import `basestring = str` for
python3 versions.

## define-range

If `range(x)` is used then `range = xrange` is defined for python2 versions
if python2 compatibility is required.

## define-callable

If `callable(x)` is used then a `def callable` boilerplate is added for python3
versions where it was not predefined (3.0 and 3.1)

## datetime-fromisoformat

If `datetime.datetime.fromisoformat` is used then it is replaced by `datetime_fromisodate`
with boilerplate code if python2 or python3 older than 3.7.

## subprocess-run

If `subprocess.run` is used then it is replaced by `subprocess_run`
with boilerplate code if python2 or python3 older than 3.5.

## time-monotonic

If `time.monotonic` is used then it is replaced by `time_monotonic`
with boilerplate code based on `time.time`. This is needed for 
python2 or python3 older than 3.3.

## import-pathlib2

If `import pathlib` is used then it is replaced by `import pathlib2`
if python2 compatiblity is requested. Pathlib exists since python 3.3
but there is a backport available (to be installed seperately)

## import-backports-zoneinfo

If `import zoneinfo` is used then it is replaced by `from backports import zoneinfo`
if python3 compatiblity is requested before python 3.9 (backport requires atleast 3.6)

## import-toml

If `import tomllib` is used then it is replaced by `import toml`
if compatiblity with python older than 3.11 is requested. The
external toml package (to be installed seperately) did exist 
before and was integrated into the standard lib.

## replace-fstring

If `F"string {part}"` is used then it is replaced by `"string {}".format(part)`
if python2 compatibility requested, as well as python3 older than 3.5.

The transformation scheme works nicely with any expression. So that
you can write `F"string {len(part):4n}: {part}"` which gets expanded to:

    "string {:4n}: {}".format(len(part), part)

## replace-walrus-operator

If `if x := fu(): pass` is used then it is replaced by `x = fu()` followed
by `if x: pass` if python2 compatibility requested, as well as python3 older than 3.8.

Currently only if-walrus and while-walrus are supported. Only a direct
assignment or compare/binop is supported, i.e `if (x:= fu()) > 0` works
as well as `while (x:= fu()) != "end": print(x)`. That one gets expanded to:

    while True:
        x = fu()
        if x != 'end':
            print(x)
        else:
            break

## replace-annotated-typing

If `var: Annotated[int, Field(gt=0)]` is used then it is replaced by `var: int`
if python2 compatibility requested, as well as python3 older than 3.9.

## replace-builtin-typing

If `var: list[int]` is used then it is replaced by `var: List[int]`
if python2 compatibility requested, as well as python3 older than 3.9.

## replace-union-typing

If `var: int|str` is used then it is replaced by `var: Union[int, str]`
if python2 compatibility requested, as well as python3 older than 3.10.
It does also replace `var: int|None` by `var: Optional[int]`

## replace-self-typing

If `param: Self` is used then it is replaced by `param: SelfB`
if python2 compatibility requested, as well as python3 older than 3.11.
It does declare a `SelfB = TypeVar("SelfB", bound="B")` as suggested 
in PEP 673, and it works for the return type of a class method as well.

## remove-keywordsonly

The keywordsonly syntax became available in python 3.0, so it need to be
removed for python2

## remove-positionalonly

The postionalonly syntax became available in python 3.8, so it need to be
removed for python2 and python3 older than 3.8

## remove-var-typehints

The var typehints became available in python 3.6, so they need to be
removed for older python3 (or python2)

## remove-typehints

The function annotations became available in python 3.0, so they need to
be removed for python2. Note that the typehints syntax became available
in python 3.5 - before that the "typing" module did not exist.

...

# pyi typehint include files generation

The `"*.pyi"` file generation needs to be requested with the "--pyi" commandline option.

The transformations are automatically selected by the minimum target python version
that is given by --pyi-version=3.6 (which is the default). 

## remove-pyi-positionalonly

The postionalonly syntax became available in python 3.8, so it need to be
removed for python3 compatiblity older than 3.8.

## outer interface only

Note that not all variable annotations and function typehints are being exported.

Only the global variables and classes, and the direct class methods and member
annotations are reproduced in the `"*.pyi"` typehints file. That's good enough for
type checkers that want to know the type of imported elements in the `"*.py"` file.

Be aware that there is no type inference done for global variables without a
type annotation. They will simply not exist in the pyi typehints file.

## option -2 and option -3

If you only provide one input file on the commandline then you can select the
output file as `"-o output.py"`. If no output is selected then all input files
are converted and printed to standard output.

If multiple files are provided on the command line then the output file is
selected based on "-1" or "-2" or "-3", where "-1" means to modify the file
in place (i.e. overwrite it).

If all your files are named like "myfile3.py" then "-3" will remove the 3
and each output file will be named like "myfile.py" and "myfile.pyi". Otherwise 
let "-2" append a "_2" so that "myfile.py" becomes "myfile_2.py" and "myfile_2.pyi"
after transformations.

If no `*.pyi` file is wanted then disable it with "--no-pyi" again.

# Development

  * make lint
  * make check
  * make python
  * make checks
  * for release:
     * make version (and run github actions)
     * make coverage (and update README.MD)
     * make build (as a test before tagging)
     * git tag and git push --tags (for github)
     * make build (and push to pypi)

__I take patches!__

The source code has a lot of code duplications and ifelse lists. That is intentional to allow anyone to quickly add corner cases.

https://github.com/gdraheim/strip_python3/issues

