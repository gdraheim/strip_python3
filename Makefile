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
QTOML_PY = src/strip_qtoml_decoder.py
AST4_PY = src/strip_ast_comments.py
UNITS_PY = tests/unittests.py
EXECS_PY = tests/exectests.py
TESTS_PY = tests/transformertests.py
TESTS = $(TESTS_PY) --python=$(PYTHON)
CONTAINER = strip-py
TODO=
V=-v

all: help

help:
	$(PYTHON) $F --help

todo2: ; $(MAKE) check2 TODO=--todo
todo1: ; $(MAKE) check1 TODO=--todo
todos: ; $(MAKE) checks TODO=--todo
checks: test test27 test36 test39 test310 test311 test312 test11
check39: ; test ! -f /usr/bin/python3.9 || $(MAKE) test PYTHON=python3.9
check10: ; test ! -f /usr/bin/python3.10 || $(MAKE) test PYTHON=python3.10
check11: ; test ! -f /usr/bin/python3.11 || $(MAKE) test PYTHON=python3.11
check12: ; test ! -f /usr/bin/python3.12 || $(MAKE) test PYTHON=python3.12
check3: ; $(MAKE) test
check2: ; $(MAKE) test11 || $(MAKE) test27 || $(MAKE) test36
check1: ; $(MAKE) check39 || $(MAKE) check10 || $(MAKE) check11 || $(MAKE) check12
check: check39 check10 check11 check12
	: " ready for $(MAKE) checks ? "

todo: ; $(MAKE) test TODO=--todo
test: ; $(PYTHON) $(TESTS) $V $@ $(TODO)
test_0%: ; $(PYTHON) $(TESTS) $V $@ $(TODO) --failfast
st_0%: ; $(PYTHON) $(TESTS) $V te$@ $(TODO) --coverage

test_1%: ; $(PYTHON) $(EXECS) $V $@ $(TODO)
st_1%: ; $(PYTHON) $(EXECS) $V te$@ $(TODO) --coverage

test27: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)
test36: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)
test39: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)
test310: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)
test311: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)
test312: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)
test11: ; test -z "`$(DOCKER) images -q -f reference=$(CONTAINER)/$@`" || $(MAKE) test_/$(subst test,,$@)

test%/27:
	: echo ========== python2 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) $(PYTHON39) /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python2 $(COVERAGE1) $V $(TODO)
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/36:
	: echo ========== python3 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) $(PYTHON39) /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python3 $(COVERAGE1) $V $(TODO)
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/39:
	: echo ========== python3.9 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) $(PYTHON39) /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python3.9 $(COVERAGE1) $V $(TODO)
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/310:
	: echo ========== python3.10 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) python3.10 /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python3.10 --python3=/usr/bin/python3.10 $(COVERAGE1) $V $(TODO)
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/311:
	: echo ========== python3.11 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) python3.11 /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python3.11 --python3=/usr/bin/python3.11 $(COVERAGE1) $V $(TODO)
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/312:
	: echo ========== python3.12 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) python3.12 /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python3.12 --python3=/usr/bin/python3.12 $(COVERAGE1) $V $(TODO)
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov$(notdir $@)
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/11:
	: echo =========== mypy-3.11 + python3.11 = $@ =====================================
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p /src
	$(DOCKER) cp $(EXECS) $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp src/strip_ast_comments.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) cp src/strip_python3.py $(CONTAINER)-python$(notdir $@):/src/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /src/strip_python3.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) python3.11 /$(notdir $(EXECS)) -vv $(dir $@) --python=/usr/bin/python3.11 --python3=/usr/bin/python3.11 --mypy=mypy-3.11 $(COVERAGE1) $V $(TODO)
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
	$(MAKE) fix-metadata-version
	$(TWINE) check dist/*
	: $(TWINE) upload dist/* --verbose

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


fix-metadata-version:
	ls dist/*
	rm -rf dist.tmp; mkdir dist.tmp
	cd dist.tmp; for z in ../dist/*; do case "$$z" in *.whl) unzip $$z ;; *) tar xzvf $$z;; esac \
	; ( find . -name PKG-INFO ; find . -name METADATA ) | while read f; do echo FOUND $$f; sed -i -e "s/Metadata-Version: 2.4/Metadata-Version: 2.2/" $$f; done \
	; case "$$z" in *.whl) zip -r $$z * ;; *) tar czvf $$z *;; esac ; ls -l $$z; done


# .....................

copy:
	cp -v ../docker-mirror-packages-repo/docker_mirror.py .
	cp -v ../docker-mirror-packages-repo/docker_mirror.pyi .
	cp -v ../docker-mirror-packages-repo/docker_image.py .

LOCAL=--local
DOCKER_IMAGE = ./docker_image.py $(LOCAL)

python27: $(CONTAINER)/test27
python36: $(CONTAINER)/test36
python39: $(CONTAINER)/test39
python310: $(CONTAINER)/test310
python311: $(CONTAINER)/test311
python312: $(CONTAINER)/test312
python311: $(CONTAINER)/test11


$(CONTAINER)/testt27: ; $(DOCKER_IMAGE) FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc python2" TEST "python2 --version"
$(CONTAINER)/testt36: ; $(DOCKER_IMAGE) FROM ubuntu:18.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
$(CONTAINER)/test310: ; $(DOCKER_IMAGE) FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
$(CONTAINER)/test312: ; $(DOCKER_IMAGE) FROM ubuntu:24.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"

$(CONTAINER)/test27:  ; $(DOCKER_IMAGE) FROM opensuse/leap:15.6 INTO $@ SEARCH "setuptools mypy toml" INSTALL "python39 procps psmisc python2" TEST "$(PYTHON39) --version" TEST "python2 --version"
$(CONTAINER)/test36:  ; $(DOCKER_IMAGE) FROM opensuse/leap:15.6 INTO $@ SEARCH "setuptools mypy toml" INSTALL "python39 python3" TEST "$(PYTHON39) --version" TEST "python3 --version"
$(CONTAINER)/test39:  ; $(DOCKER_IMAGE) FROM opensuse/leap:15.6 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python39" SYMLINK /usr/bin/python3.9:python3 TEST "$(PYTHON39) --version" TEST "python3 --version" 
$(CONTAINER)/test311: ; $(DOCKER_IMAGE) FROM opensuse/leap:15.6 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python311" SYMLINK /usr/bin/python3.11:python3 SYMLINK /usr/bin/python3.11:$(PYTHON39) TEST "$(PYTHON39) --version" TEST "python3 --version"
$(CONTAINER)/test11: ; $(DOCKER_IMAGE) FROM opensuse/leap:15.6 INTO $@ SEARCH "setuptools mypy toml" INSTALL "procps psmisc python311 python311-mypy" SYMLINK /usr/bin/python3.11:python3 SYMLINK /usr/bin/python3.11:$(PYTHON39) TEST "$(PYTHON39) --version" TEST "python3 --version" TEST "mypy-3.11 --version"

mypython: $(CONTAINER)/test11
python: stop python27 python36 python39 python311 python11
stop:
	$(DOCKER) ps -q -f status=exited | xargs --no-run-if-empty $(DOCKER) rm
	$(DOCKER) ps -q -f name=test | xargs --no-run-if-empty $(DOCKER) rm -f
	$(DOCKER) ps -q -f name=-repo- | xargs --no-run-if-empty $(DOCKER) rm -f

# .....................

MYPY = mypy-3.11
MYPY_EXCLUDES = --exclude /$(notdir $(AST4_PY)) --exclude /$(notdir $(QTOML_PY))
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
