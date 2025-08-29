from pathlib import Path

CURRENT_FILE_PATH = Path(__file__)
PACKAGE_DIR = CURRENT_FILE_PATH.parent

# Path setting
DATASET_PATH = str(PACKAGE_DIR / "dataset")
CORPUS_PATH = str(PACKAGE_DIR / "data_corpus.bin")
CHORD_TYPES_PATH = str(PACKAGE_DIR / "chord_types.bin")
WEIGHTS_PATH = str(PACKAGE_DIR / "weights.hdf5")
INPUTS_PATH = str(PACKAGE_DIR / "inputs")
OUTPUTS_PATH = str(PACKAGE_DIR / "outputs")

# 'loader.py'
EXTENSION = [".musicxml", ".xml", ".mxl"]

# '.model.py'
VAL_RATIO = 0.1
DROPOUT = 0.2
SEGMENT_LENGTH = 32
RNN_SIZE = 128
NUM_LAYERS = 3
BATCH_SIZE = 2048
EPOCHS = 100

# 'harmonizor.py'
RHYTHM_DENSITY = 0.5
CHORD_PER_BAR = False
REPEAT_CHORD = False
WATER_MARK = True
