Taken from https://www.biostars.org/p/174807/

Changes made manually:
- Inlined all the functions
- Replaced subprocess.call with subprocess.run
- Formatting
- Hard coded inputs
- Removed logically unnecessary += statements because the preprocessor doesn't support them
- Added flags to eliminate false dependencies between JVM invocations
