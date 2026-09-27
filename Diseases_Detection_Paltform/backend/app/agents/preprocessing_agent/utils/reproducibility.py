"""Reproducibility utilities for seed management and environment tracking."""

import os
import random
import sys
import numpy as np
import pandas as pd
import sklearn
from typing import Dict, Any


def set_seed(seed: int = 42) -> None:
    """Sets random seeds across python, numpy, and environment."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def get_environment_info() -> Dict[str, Any]:
    """Captures runtime environment versions for reproducibility."""
    return {
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "sklearn_version": sklearn.__version__,
    }
