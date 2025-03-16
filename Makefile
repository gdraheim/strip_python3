F= src/strip_python3.py
B= 2024
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'

GIT = git
DOCKER = docker
PYTHON39 = python3.9
PYTHON3 = python3
PYTHON = python3.11
PYTHON_VERSION = 3.11
TWINE = twine-3.11
AST4_PY = src/strip_ast_comments.py
TESTS_PY = tests/python3_transformations.py
TESTS = $(TESTS_PY) --python=$(PYTHON)
CONTAINER = strip-py
V=-v

all: help

help:
	$(PYTHON) $F --help

checks: test test27 test36 test39 test311
check: test
	: " ready for $(MAKE) checks ? "

test: ; $(PYTHON) $(TESTS) $V $@
test_0%: ; $(PYTHON) $(TESTS) $V $@ --failfast
st_0%: ; $(PYTHON) $(TESTS) $V te$@ --coverage

EXECS= tests/exec_tests.py
test__1%: ; $(PYTHON) $(EXECS) $V $@
st__1%: ; $(PYTHON) $(EXECS) $V te$@ --coverage

test27: ; $(MAKE) test_/27
test36: ; $(MAKE) test_/36
test39: ; $(MAKE) test_/39
test311: ; $(MAKE) test_/311

test%/27:
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) $(PYTHON39) /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python2 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/36:
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) $(PYTHON39) /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python3 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/39:
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) $(PYTHON39) /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python3.9 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/311:
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) python3.11 /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python3.11 --python3=/usr/bin/python3.11 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)


coverage:
	$(PYTHON) $(TESTS) $V --coverage

VERFILES = $F tests/*.py *.toml
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

# .....................

copy:
	cp -v ../docker-mirror-packages-repo/docker_mirror.py .
	cp -v ../docker-mirror-packages-repo/docker_mirror.pyi .
	cp -v ../docker-mirror-packages-repo/docker_local_image.py .

python27: $(CONTAINER)/test27
python36: $(CONTAINER)/test36
python39: $(CONTAINER)/test39
python310: $(CONTAINER)/test310
python311: $(CONTAINER)/test311
python312: $(CONTAINER)/test312

$(CONTAINER)/testt27: ; ./docker_local_image.py FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc python2" TEST "python2 --version"
$(CONTAINER)/testt36: ; ./docker_local_image.py FROM ubuntu:18.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
$(CONTAINER)/test310: ; ./docker_local_image.py FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
$(CONTAINER)/test312: ; ./docker_local_image.py FROM ubuntu:24.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"

$(CONTAINER)/test27:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "python39 procps psmisc python2" TEST "python3.9 --version" TEST "python2 --version"
$(CONTAINER)/test36:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "python39 procps psmisc python3" TEST "python3.9 --version" TEST "python3 --version"
$(CONTAINER)/test39:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python39" SYMLINK /usr/bin/python3.9:python3 TEST "python3.9 --version" TEST "python3 --version" 
$(CONTAINER)/test311: ; ./docker_local_image.py FROM opensuse/leap:15.6 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python311 $(EXTRA)" SYMLINK /usr/bin/python3.11:python3 SYMLINK /usr/bin/python3.11:python3.9 TEST "python3.9 --version" TEST "python3 --version"
$(CONTAINER)/test3111: ; $(MAKE) $(CONTAINER)/test311 EXTRA=python311-mypy

mypython: $(CONTAINER)/test3111
python: stop python27 python36 python39 python311
stop:
	$(DOCKER) ps -q -f status=exited | xargs --no-run-if-empty $(DOCKER) rm
	$(DOCKER) ps -q -f name=test | xargs --no-run-if-empty $(DOCKER) rm -f
	$(DOCKER) ps -q -f name=-repo- | xargs --no-run-if-empty $(DOCKER) rm -f

# .....................

MYPY = mypy-3.11
MYPY_EXCLUDES = --exclude /$(notdir $(AST4_PY))
MYPY_WITH = --strict --show-error-codes --show-error-context 
MYPY_OPTIONS = --no-warn-unused-ignores --implicit-reexport --python-version $(PYTHON_VERSION)
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec
type:
	$(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) $(MYPY_EXCLUDES) $F
	$(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) $(MYPY_EXCLUDES) tests/*.py


PYLINT = pylint
PYLINT_OPTIONS =
pylint:
	zypper install -y python3-pylint
lint:
	$(PYLINT) $(PYLINT_OPTIONS) $F
	for py in tests/*.py; do $(PYLINT) $(PYLINT_OPTIONS) $$py || exit 1; done
