Experimental Python backend for hS. It supports simple, straight line scripts
that only use `subprocess.run` calls to do work.


## Correctness Limitations

- Ignores python file-state changes (ex: `open`)
- Ignores stderr
- Assumes sandboxed evaluation context cannot make changes to system.

## Performance Limitations

- Only straightline code plus for loops
- Statically known arguments to commands
- Only can speculate loops with statically known iterators
- Only open() with statements that do a simple redirect of a command
