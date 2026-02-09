Taken from https://www.kaggle.com/code/dschettler8845/captk-brats-preprocessing-cleaned-commented

Changes made manually:
- Inlined all the functions
- Converting all python file IO functions into subprocess.run based ones (ex: `os.remove` -> `run(["rm", ...])`)
- Moved all the directory making code to a separate for loop
- Inlined the train labels from train_labels.csv and removed test labels.
