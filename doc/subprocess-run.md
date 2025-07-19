## subprocess-run

Python developers had often asked to have similar way to call
the underlying system shell. Many other scripting languages have
something like ``echo foo`` as part of the syntax. The discussions
let to half of a solution - there is a `run(x: str)` function
in the stdlib `subprocess` module since python 3.5.

When `subprocess.run` us used in the code then it is replaced
by `subprocess_run` which calls `subprocess.run` in case that
the python interpreter is actually python 3.5 or later.
Otherwise it adds some boilerplate code based on `Popen`. 
Note that the boilerplate can not have all functionality
as `Popen` did get additional arguments over time as well
and here we try to be the most backward compatible.

        # original
        import subprocess
        def func1() -> str:
            return subprocess.run("echo ok", shell=True).stdout

        # transformed for --python-version=3.3
        import sys
        import subprocess
        if sys.version_info >= (3, 5):
            subprocess_run = subprocess.run
        else:
        
            class CompletedProcess:
        
                def __init__(self, args, returncode, outs, errs):
                    self.args = args
                    self.returncode = returncode
                    self.stdout = outs
                    self.stderr = errs
        
                def check_returncode(self):
                    if self.returncode:
                        raise subprocess.CalledProcessError(self.returncode, self.args)

            def subprocess_run(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
                try:
                    outs, errs = proc.communicate(input=input, timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                completed = CompletedProcess(args, proc.returncode, outs, errs)
                if check:
                    completed.check_returncode()
                return completed
        
        def func1():
            return subprocess_run('echo ok', shell=True).stdout
           
        # transformed (without the TimeoutExpired part)
        import sys
        import subprocess
        if sys.version_info >= (3, 5):
            subprocess_run = subprocess.run
        else:
        
            class CompletedProcess:
        
                def __init__(self, args, returncode, outs, errs):
                    self.args = args
                    self.returncode = returncode
                    self.stdout = outs
                    self.stderr = errs
        
                def check_returncode(self):
                    if self.returncode:
                        raise subprocess.CalledProcessError(self.returncode, self.args)

            def subprocess_run(args, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, env=None):
                proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, cwd=cwd, env=env)
                outs, errs = proc.communicate(input=input)
                completed = CompletedProcess(args, proc.returncode, outs, errs)
                if check:
                    completed.check_returncode()
                return completed
        
        def func1():
            return subprocess_run('echo ok', shell=True).stdout

Note that if a `--python-version` of 3.5 or later is selected then
this transformer will not be executed at all. And just like with
[datetime-fromisoformat.md] if `subprocess` was already imported 
under a different name then that name is used as the prefix for 
the boilerplate function as well. The `CompletedProcess` however
is kept.

