[![Type Check](https://github.com/gdraheim/strip_python3/actions/workflows/typecheck.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/strip_python3/actions/workflows/typecheck.yml)
[![Unit Tests](https://github.com/gdraheim/strip_python3/actions/workflows/unittests.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/strip_python3/actions/workflows/unittests.yml)
[![Code Coverage](https://img.shields.io/badge/44%20test-90%25%20coverage-brightgreen)](https://github.com/gdraheim/strip_python3/blob/main/strip_python3.tests.py)
[![PyPI version](https://badge.fury.io/py/strip-python3.svg)](https://pypi.org/project/strip-python3/)


# easy way to transform and remove python3 typehints

This project has been inspired by `'strip-hints'` and `'py-backwards'` but it is
now based on the Python 3.9+ standard library's `'ast.unparse()'`. More specifically
it is using `'ast_comments'` to keep the comments. The implementation wants to make
it very easy so that you can add your own source code transformations.

As a bonus, `'strip_python3'` can extract typehints to `'*.pyi'` file containing only
the outer object-oriented interface. That allows you to ship modern typed python3
code to older systems, possibly even having only python2 preinstalled. But even
supporting systems with a base installation of python3.6 can be a challenge where
this tool can help.


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

## replace-fstring

If `F"string {part}"` is used then it is replaced by `"string {}".format(part)`
if python2 compatibility requested, as well as python3 older than 3.5.

## datetime-fromisoformat

If `datetime.datetime.fromisoformat` is used then it is replaced by `datetime_fromisodate`
with boilerplate code if python2 or python3 older than 3.7.

## subprocess-run

If `subprocess.run` is used then it is replaced by `subprocess_run`
with boilerplate code if python2 or python3 older than 3.5.

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
annotations are reproduced in the "*.pyi" typehints file. That's good enough for
type checkers that want to know the type of imported elements in the "*.py" file.

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



