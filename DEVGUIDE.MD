# Development

## intro

The source code has a lot of code duplications and ifelse lists. That is intentional to allow anyone to quickly add corner cases.

Please DONT refactor or modularize. If you like to copy code then just do that.

## running tests

You can run any test in any `tests/*.py` just by using the number.

* `make test_1100` # runs a unittests.py case
* `make test_2201` # runs a transformertests.py case checking py/pyi output
* `make test_3301` # runs a exectests.py case executing the py output (and validate with mypy)

Be sure to set the PYTHON variable to the interpreter you have. Many distros will default 
to Python 3.6 as "python3" so that the Makefile here is explicitly using `python3.11`.

## container tests

* `make python` will create docker containers (based on opensuse/leap:15.6)

After that the tests can be run with a specific python version. Just add it.

* `make test_3301/39`
* `make test_3301/311`

and there is a special `/11` that will run the `mypy-3.11` packaged in that distro.

* `make test_3301/11`

There is a shorthand `make checks` to do the deep analysis with containers.

## Check and Release

  * make lint
  * make check
  * make python
  * make checks
  * for release:
     * make version (and run github actions)
     * make coverage (and update README.MD)
     * make build (and push to pyi)
     * git tag and git push --tags (for github)
