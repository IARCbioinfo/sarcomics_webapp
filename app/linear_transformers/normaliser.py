import numpy as np


class MinMaxNormaliser:
    """Matches ../sarcomics_wsi/sarcomics_wsi/linear_transformers/normaliser.py so min_max_norm.pkl unpickles."""

    def __init__(self, axis_norm=None):
        self.min = None
        self.max = None
        self.axis_norm = axis_norm
        self.is_fitted_ = False

    def transform(self, X):
        X_clipped = np.clip(X, self.min, self.max)
        return (X_clipped - self.min) / (self.max - self.min)
