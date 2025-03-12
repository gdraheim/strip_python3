F= src/strip_python3.py
B= 2024
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'

GIT = git
PYTHON39 = python3.9
PYTHON3 = python3
PYTHON = python3.11
PYTHON_VERSION = 3.11
TWINE = twine-3.11
AST4_PY = src/strip_ast_comments.py
TESTS_PY = tests/python3_transformations.py
TESTS = $(TESTS_PY) --python=$(PYTHON)
CONTAINER = strip-hints
V=-v

all: help

help:
	$(PYTHON) $F --help

check: ; $(PYTHON) $(TESTS) $V
test_0%: ; $(PYTHON) $(TESTS) $V $@
st_0%: ; $(PYTHON) $(TESTS) $V te$@ --coverage

EXECS= tests/exec_tests.py
test__1%: ; $(PYTHON) $(EXECS) $V $@
st__1%: ; $(PYTHON) $(EXECS) $V te$@ --coverage

27/test%:
	docker rm -f $(CONTAINER)-python27
	docker run -d --name=$(CONTAINER)-python27 strip-python$(dir $@)test sleep 9999
	docker exec $(CONTAINER)-python27 mkdir -p /src
	docker cp $(EXECS) $(CONTAINER)-python27:/
	docker cp src/strip_ast_comments.py $(CONTAINER)-python27:/src/
	docker cp src/strip_python3.py $(CONTAINER)-python27:/src/
	docker exec $(CONTAINER)-python27 chmod +x /src/strip_python3.py
	docker exec $(CONTAINER)-python27 $(PYTHON39) /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python2 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || docker cp $(CONTAINER)-python27:/.coverage .coverage.cov27
	docker rm -f $(CONTAINER)-python27
36/test%:
	docker rm -f $(CONTAINER)-python36
	docker run -d --name=$(CONTAINER)-python36 strip-python$(dir $@)test sleep 9999
	docker exec $(CONTAINER)-python36 mkdir -p /src
	docker cp $(EXECS) $(CONTAINER)-python36:/
	docker cp src/strip_ast_comments.py $(CONTAINER)-python36:/src/
	docker cp src/strip_python3.py $(CONTAINER)-python36:/src/
	docker exec $(CONTAINER)-python36 chmod +x /src/strip_python3.py
	docker exec $(CONTAINER)-python36 $(PYTHON39) /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python3 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || docker cp $(CONTAINER)-python36:/.coverage .coverage.cov36
	docker rm -f $(CONTAINER)-python36
39/test%:
	docker rm -f $(CONTAINER)-python39
	docker run -d --name=$(CONTAINER)-python39 strip-python$(dir $@)test sleep 9999
	docker exec $(CONTAINER)-python39 mkdir -p /src
	docker cp $(EXECS) $(CONTAINER)-python39:/
	docker cp src/strip_ast_comments.py $(CONTAINER)-python39:/src/
	docker cp src/strip_python3.py $(CONTAINER)-python39:/src/
	docker exec $(CONTAINER)-python39 chmod +x /src/strip_python3.py
	docker exec $(CONTAINER)-python39 $(PYTHON39) /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python3.9 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || docker cp $(CONTAINER)-python39:/.coverage .coverage.cov39
	docker rm -f $(CONTAINER)-python39
311/test%:
	docker rm -f $(CONTAINER)-python311
	docker run -d --name=$(CONTAINER)-python311 strip-python$(dir $@)test sleep 9999
	docker exec $(CONTAINER)-python311 mkdir -p /src
	docker cp $(EXECS) $(CONTAINER)-python311:/
	docker cp src/strip_ast_comments.py $(CONTAINER)-python311:/src/
	docker cp src/strip_python3.py $(CONTAINER)-python311:/src/
	docker exec $(CONTAINER)-python311 chmod +x /src/strip_python3.py
	docker exec $(CONTAINER)-python311 python3.11 /$(notdir $(EXECS)) -vv $(notdir $@) --python=/usr/bin/python3.11 --python3=/usr/bin/python3.11 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || docker cp $(CONTAINER)-python311:/.coverage .coverage.cov311
	docker rm -f $(CONTAINER)-python311


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

python27: strip-python27/test
python36: strip-python36/test
python39: strip-python39/test
python310: strip-python310/test
python311: strip-python311/test
python312: strip-python312/test

strip-python27/testt: ; ./docker_local_image.py FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc python2" TEST "python2 --version"
strip-python36/testt: ; ./docker_local_image.py FROM ubuntu:18.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
strip-python310/test: ; ./docker_local_image.py FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
strip-python312/test: ; ./docker_local_image.py FROM ubuntu:24.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"

strip-python27/test:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "python39 procps psmisc python2" TEST "python3.9 --version" TEST "python2 --version"
strip-python36/test:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "python39 procps psmisc python3" TEST "python3.9 --version" TEST "python3 --version"
strip-python39/test:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python39" SYMLINK /usr/bin/python3.9:python3 TEST "python3.9 --version" TEST "python3 --version" 
strip-python311/test: ; ./docker_local_image.py -vv FROM opensuse/leap:15.5 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python311 $(EXTRA)" SYMLINK /usr/bin/python3.11:python3 SYMLINK /usr/bin/python3.11:python3.9 TEST "python3.9 --version", TEST "python3 --version"
mypy-python311/test: ; $(MAKE) strip-python311/test EXTRA=python311-mypy

mypy: mypy-python311/test
python: python27 python36 python39 python311

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
	$(PYLINT) $(PYLINT_OPTIONS) tests/*.py
