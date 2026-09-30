"""Stand-in for fitsio (tests only): images are numpy .npy data with a .fz name."""
import numpy as np


def read(path, ext=0, header=False):
    data = np.load(path)[ext]
    return (data, {}) if header else data
