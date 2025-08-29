# Path setting
DATASET_PATH = "autoharmonizer/autoharmonizer/dataset"
CORPUS_PATH = "autoharmonizer/autoharmonizer/data_corpus.bin"
CHORD_TYPES_PATH = "autoharmonizer/autoharmonizer/chord_types.bin"
WEIGHTS_PATH = "autoharmonizer/autoharmonizer/weights.hdf5"
INPUTS_PATH = "autoharmonizer/autoharmonizer/inputs"
OUTPUTS_PATH = "autoharmonizer/autoharmonizer/outputs"

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
