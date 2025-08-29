import os
import warnings
import pickle
import numpy as np
from config import *
from music21 import *
from tqdm import trange
from copy import deepcopy
from model import build_model
from samplings import gamma_sampling
from loader import get_filenames, convert_files
from tensorflow.python.keras.utils.np_utils import to_categorical

# use cpu
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
warnings.filterwarnings("ignore")

# Load chord types
with open(CHORD_TYPES_PATH, "rb") as filepath:
    chord_types = pickle.load(filepath)


def generate_chord(
    chord_model,
    melody_data,
    beat_data,
    key_data,
    segment_length=SEGMENT_LENGTH,
    rhythm_gamma=RHYTHM_DENSITY,
    chord_per_bar=CHORD_PER_BAR,
):

    chord_data = []

    # Process each melody sequence in the corpus
    for idx, song_melody in enumerate(melody_data):

        # Load the corresponding beat sequence
        song_melody = segment_length * [0] + song_melody + segment_length * [0]
        song_beat = segment_length * [0] + beat_data[idx] + segment_length * [0]
        song_key = segment_length * [0] + key_data[idx] + segment_length * [0]
        song_chord = segment_length * [0]

        # Predict each pair
        for idx in range(segment_length, len(song_melody) - segment_length):

            # Create input data
            melody_left = song_melody[idx - segment_length : idx]
            melody_right = song_melody[idx : idx + segment_length][::-1]
            beat_left = song_beat[idx - segment_length : idx]
            beat_right = song_beat[idx : idx + segment_length][::-1]
            key_left = song_key[idx - segment_length : idx]
            key_right = song_key[idx : idx + segment_length][::-1]
            chord_left = song_chord[idx - segment_length : idx]

            # One-hot vectorization
            melody_left = to_categorical(melody_left, num_classes=128)
            melody_right = to_categorical(melody_right, num_classes=128)
            beat_left = to_categorical(beat_left, num_classes=5)
            beat_right = to_categorical(beat_right, num_classes=5)
            key_left = to_categorical(key_left, num_classes=16)
            key_right = to_categorical(key_right, num_classes=16)
            condition_left = np.concatenate((beat_left, key_left), axis=-1)
            condition_right = np.concatenate((beat_right, key_right), axis=-1)
            chord_left = to_categorical(chord_left, num_classes=len(chord_types))

            # expand dimension
            melody_left = np.expand_dims(melody_left, axis=0)
            melody_right = np.expand_dims(melody_right, axis=0)
            condition_left = np.expand_dims(condition_left, axis=0)
            condition_right = np.expand_dims(condition_right, axis=0)
            chord_left = np.expand_dims(chord_left, axis=0)

            # Predict the next chord
            prediction = chord_model.predict(
                x=[
                    melody_left,
                    melody_right,
                    condition_left,
                    condition_right,
                    chord_left,
                ]
            )[0]

            if song_melody[idx] != 0 and song_beat[idx] == 4:
                prediction = gamma_sampling(prediction, [[0]], [1], return_probs=True)

            # Tuning rhythm density
            if chord_per_bar:
                if (
                    song_beat[idx] == 4
                    and (
                        song_melody[idx] != song_melody[idx - 1]
                        or song_beat[idx] != song_beat[idx - 1]
                    )
                    and not (idx == segment_length and song_melody[idx] == 0)
                ):
                    prediction = gamma_sampling(
                        prediction, [[song_chord[-1]]], [1], return_probs=True
                    )

                else:
                    prediction = gamma_sampling(
                        prediction, [[song_chord[-1]]], [0], return_probs=True
                    )

            else:
                prediction = gamma_sampling(
                    prediction, [[song_chord[-1]]], [rhythm_gamma], return_probs=True
                )

            cho_idx = np.argmax(prediction, axis=-1)
            song_chord.append(cho_idx)

        # Remove the leading padding
        chord_data.append(song_chord[segment_length:])

    return chord_data


def watermark(score, filename, water_mark=WATER_MARK):

    # Add water mark
    if water_mark:

        score.metadata = metadata.Metadata()
        score.metadata.title = filename
        score.metadata.composer = "harmonized by AutoHarmonizer"

    return score


def export_music(
    score,
    beat_data,
    chord_data,
    filename,
    repeat_chord=REPEAT_CHORD,
    outputs_path=OUTPUTS_PATH,
    water_mark=WATER_MARK,
):

    # Convert to music
    harmony_list = []
    offset = 0.0
    filename = os.path.basename(filename)
    filename = ".".join(filename.split(".")[:-1])

    for idx, song_chord in enumerate(chord_data):
        song_chord = [chord_types[int(cho_idx)] for cho_idx in song_chord]
        song_beat = beat_data[idx]
        pre_chord = None

        for t_idx, cho in enumerate(song_chord):
            cho = cho.replace("N.C.", "R")
            cho = cho.replace("bpedal", "-pedal")
            if cho != "R" and (
                pre_chord != cho
                or (
                    repeat_chord
                    and t_idx != 0
                    and song_beat[t_idx] == 4
                    and song_beat[t_idx - 1] != 4
                )
            ):
                chord_symbol = harmony.ChordSymbol(cho)
                chord_symbol = chord_symbol
                chord_symbol.offset = offset
                harmony_list.append(chord_symbol)
            offset += 0.25
            pre_chord = cho

    h_idx = 0
    new_score = stream.Score()

    for m in score:
        if isinstance(m, stream.Measure):
            new_m = deepcopy(m)
            new_m.clear()
            for n in m:
                if not isinstance(n, harmony.ChordSymbol):
                    if (
                        h_idx < len(harmony_list)
                        and n.offset + m.offset >= harmony_list[h_idx].offset
                    ):
                        harmony_list[h_idx].offset -= m.offset
                        new_m.insert(harmony_list[h_idx].offset, harmony_list[h_idx])
                        h_idx += 1
                    new_m.insert(n.offset, n)
            new_score.insert(m.offset, new_m)

    if water_mark:
        new_score = watermark(new_score, filename)
    new_score.write("mxl", fp=outputs_path + "/" + filename + ".mxl")


def main():

    # Load data from 'inputs'
    filenames = get_filenames(input_dir=INPUTS_PATH)
    data_corpus = convert_files(filenames, fromDataset=False)

    # Build harmonic rhythm and chord model
    model = build_model(
        SEGMENT_LENGTH, RNN_SIZE, NUM_LAYERS, DROPOUT, WEIGHTS_PATH, training=False
    )

    # Process each melody sequence
    for idx in trange(len(data_corpus)):

        melody_data = data_corpus[idx][0]
        beat_data = data_corpus[idx][1]
        key_data = data_corpus[idx][2]
        score = data_corpus[idx][3]
        filename = data_corpus[idx][4]

        # Generate harmonic rhythm and chord data
        chord_data = generate_chord(model, melody_data, beat_data, key_data)

        # Export music file
        export_music(score, beat_data, chord_data, filename)
