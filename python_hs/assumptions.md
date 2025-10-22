## Correctness

- Ignores python file-state changes (ex: `open`)
- Ignores stderr
- Assumes sandboxed evaluation context cannot make changes to system.

## Performance

- Only straightline code plus for loops
- Statically known arguments to commands
- Only can speculate loops with statically known iterators
- Only open() with statements that do a simple redirect of a command
