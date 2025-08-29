## Correctness

- Ignores python file-state changes (ex: `open`)
- Ignores stderr

## Performance

- Only straightline code plus for loops
- Statically known arguments to commands (literals and global constants)
- Only can speculate loops with statically known iterators (uses `range` and global constants)
