Taken from https://github.com/hamiddi/bioinfo-autoimmune/blob/main/ch7/chipseq_pipeline.py

Changes made manually:
- Inlined all the functions
- Inlined metadata object listing files to run
- Commented out all but two datasets to analyze to reduce runtime.
- Converting all python file IO functions into subprocess.run based ones (ex: `os.remove` -> `run(["rm", ...])`)
