F= src/strip_python3.py
B= 2024
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'

GIT = git
PYTHON3 = python3
PYTHON = python3.11
PYTHON_VERSION = 3.11
TWINE = twine-3.11
AST4_PY = src/strip_ast_comments.py
TESTS_PY = strip_python3.tests.py
TESTS = $(TESTS_PY) --python=$(PYTHON)
V=-v

all: help

help:
	$(PYTHON) strip_python3.py --help

check: tests
tests: ; $(PYTHON) $(TESTS) $V
test_0%: ; $(PYTHON) $(TESTS) $V $@

st_0%: ; $(PYTHON) $(TESTS) $V te$@ --coverage


coverage:
	$(PYTHON) $(TESTS) $V --coverage

VERFILES = $F *.py *.toml
version:
	@ grep -l __version__ $(VERFILES) | { while read f; do : \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $B) \
	; D=`date +%W$(DAY) -d "$(FOR)"` ; sed -i \
	-e "/^ *version = /s/[.]-*[0123456789][0123456789][0123456789]*/.$$X$$D/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $B-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep "^version =" $(VERFILES)
	@ grep ^__version__ $(VERFILES)
	@ $(GIT) add $(VERFILES) || true
	@ ver=`cat $F | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"

PIP3 = pip3

.PHONY: build
build:
	- rm -rf build dist *.egg-info
	$(MAKE) tmp/README.MD
	# $(PIP3) install --root=~/local . -v --no-compile
	$(PYTHON) -m build
	$(TWINE) check dist/*
	: $(TWINE) upload dist/*

tmp/README.MD: README.MD Makefile
	@ test -d tmp || mkdir tmp
	cat $(notdir $@) | sed -e "/\\/badge/d" > $@

ins install:
	$(MAKE) tmp/README.MD
	test ! -d build || rm -rf build
	$(PIP3) install --no-compile --user .
	$(MAKE) show | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"

uns uninstall: 
	test -d tmp || mkdir -v tmp
	set -x; $(PIP3) uninstall -y `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//'  pyproject.toml`

show:
	@ $(PIP3) show --files `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//' pyproject.toml` \
	| sed -e "s:[^ ]*/[.][.]/\\([a-z][a-z]*\\)/:~/.local/\\1/:"

MYPY = mypy-3.11
MYPY_EXCLUDES = --exclude /$(notdir $(AST4_PY))
MYPY_WITH = --strict --show-error-codes --show-error-context 
MYPY_OPTIONS = --no-warn-unused-ignores --implicit-reexport --python-version $(PYTHON_VERSION)
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec
type:
	$(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) $(MYPY_EXCLUDES) $F

PYLINT = pylint
PYLINT_OPTIONS =
pylint:
	zypper install -y python3-pylint
lint:
	$(PYLINT) $(PYLINT_OPTIONS) $F
