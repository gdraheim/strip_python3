F= strip_python3.py
B= 2024
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'

GIT = git
PYTHON = python3.11
TESTS = strip_python3.tests.py --python=$(PYTHON)
V=-v

all: tests

tests: ; $(PYTHON) $(TESTS) $V
test_0%: ; $(PYTHON) $(TESTS) $V $@

VERFILES = $F $(F:.py=.tests.py)
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
	@ grep ^__version__ $(VERFILES)
	@ $(GIT) add $(VERFILES) || true
	@ ver=`cat $F | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"


