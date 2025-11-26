Taken from https://github.com/hamiddi/bioinfo-autoimmune/blob/main/ch7/chipseq_pipeline.py

Changes made manually:
- Inlined all the functions
- Inlined metadata object listing files to run
- Converting all python file IO functions into subprocess.run based ones (ex: `os.remove` -> `run(["rm", ...])`)
- Moved the directory making code to a separate for loop
- Seeded macs3 callpeaks
- Used data downsampled to 1/4 by the download script
