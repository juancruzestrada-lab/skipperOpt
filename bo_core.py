"""
bo_core.py
Readout-system and detector agnostic Bayesian optimization machinery.

Provides:
    - Normalized coordinate transforms ([-1, 1] <-> physical units)
    - Optimizer factory supporting gp, forest, gbrt, dummy (skopt)
    - Progress callback factory (CSV logging)
    - File/directory utilities shared across all optimize_*.py drivers

No hardware calls, no image I/O, no detector physics — this module
has no dependencies on lta_control or image_analysis.
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from skopt import gp_minimize, forest_minimize, gbrt_minimize, dummy_minimize
from skopt import dump as skopt_dump


# ---------------------------------------------------------------------------
# Optimizer registry
# ---------------------------------------------------------------------------

OPTIMIZER_MAP = {
    "gp":     gp_minimize,
    "forest": forest_minimize,
    "gbrt":   gbrt_minimize,
    "dummy":  dummy_minimize,
}

# Per-optimizer whitelist of kwargs accepted beyond the common set.
# Keys not in this set (including underscore-prefixed JSON comment keys)
# are silently dropped so the JSON can carry disabled/commented entries.
OPTIMIZER_KWARGS_WHITELIST = {
    "gp": {
        "acq_func", "acq_optimizer", "initial_point_generator",
        "n_points", "xi", "kappa", "noise", "n_jobs",
    },
    "forest": {
        "base_estimator", "acq_func", "initial_point_generator",
        "n_points", "xi", "kappa", "n_jobs",
    },
    "gbrt": {
        "base_estimator", "acq_func", "initial_point_generator",
        "n_points", "xi", "kappa", "n_jobs",
    },
    "dummy": set(),
}

# Keys handled explicitly in build_optimizer_call; never forwarded as **kwargs.
_COMMON_KEYS = {"type", "n_calls", "n_initial_points", "random_state"}


# ---------------------------------------------------------------------------
# Coordinate transforms
# ---------------------------------------------------------------------------

def to_normalized(x: float, lo: float, hi: float) -> float:
    """Map physical value x in [lo, hi] to normalized value in [-1, 1]."""
    return 2.0 * (x - lo) / (hi - lo) - 1.0


def from_normalized(x_norm: float, lo: float, hi: float) -> float:
    """Map normalized value in [-1, 1] to physical value in [lo, hi]."""
    return lo + (x_norm + 1.0) / 2.0 * (hi - lo)


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------

def initialize_directory(output_dir: str):
    """Create output_dir if it does not exist."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    else:
        print(f"Directory already exists: {output_dir}")


def get_unique_filename(odir: str, ccd_code: str, date: str) -> str:
    """
    Return a unique CSV filename of the form <date>_results-<ccd_code>-NNN.csv
    by incrementing NNN until no file exists at odir+filename.
    """
    base = f"{date}_results-{ccd_code}"
    counter = 0
    while True:
        fname = f"{base}-{counter:03d}.csv"
        if not os.path.exists(odir + fname):
            return fname
        counter += 1


# ---------------------------------------------------------------------------
# CSV header builder
# ---------------------------------------------------------------------------

def build_csv_header(param_cfgs: list) -> list:
    """
    Build the CSV column header for progress logging.

    Columns: iteration | filename | <name> (current) * N | F (current)
                                  | <name> (best)    * N | F (best)
    """
    header = ["iteration", "filename"]
    for p in param_cfgs:
        header.append(f"{p['name']} (current)")
    header.append("F (current)")
    for p in param_cfgs:
        header.append(f"{p['name']} (best)")
    header.append("F (best)")
    return header


# ---------------------------------------------------------------------------
# Progress callback factory
# ---------------------------------------------------------------------------

def make_progress_callback(writer: csv.writer, file_handle,
                            param_cfgs: list, output_dir: str,
                            find_latest_fn):
    """
    Return a skopt-compatible callback that writes one CSV row per iteration.

    Parameters
    ----------
    writer : csv.writer
    file_handle : file object
        Open file; flushed after each write.
    param_cfgs : list[dict]
        Parameter definitions from config["parameters"].
    output_dir : str
        Passed to find_latest_fn for image filename logging.
    find_latest_fn : callable
        find_latest_fz_file(directory) -> str | None.
        Passed in to avoid importing image_analysis here.

    Returns
    -------
    callable
        Callback with signature callback(OptimizeResult).
    """
    def callback(result):
        n      = len(result.x_iters)
        latest = find_latest_fn(output_dir)
        fname  = os.path.basename(latest) if latest else "N/A"
        print(f"Iteration {n}: best F = {result.fun:.5f}")

        row = [n, fname]

        for i, pcfg in enumerate(param_cfgs):
            lo, hi = pcfg["bounds"]
            val    = from_normalized(result.x_iters[-1][i], lo, hi)
            row.append(round(val, pcfg.get("precision", 2)))
        row.append(round(float(result.func_vals[-1]), 5))

        for i, pcfg in enumerate(param_cfgs):
            lo, hi = pcfg["bounds"]
            val    = from_normalized(result.x[i], lo, hi)
            row.append(round(val, pcfg.get("precision", 2)))
        row.append(round(float(result.fun), 5))

        writer.writerow(row)
        file_handle.flush()

    return callback


# ---------------------------------------------------------------------------
# Optimizer factory
# ---------------------------------------------------------------------------

def build_optimizer_call(opt_cfg: dict, space: list, objective_fn,
                          callback, x0=None, y0=None):
    """
    Construct (minimize_fn, kwargs) from the optimizer block of a campaign config.

    Common kwargs handled here: n_calls, n_initial_points, random_state,
    callback, x0, y0 (n_initial_points set to 0 on warm restart).

    Optimizer-specific kwargs are drawn from opt_cfg and filtered by
    OPTIMIZER_KWARGS_WHITELIST. Underscore-prefixed keys and _COMMON_KEYS
    are always dropped.

    Parameters
    ----------
    opt_cfg : dict
        config["optimizer"].
    space : list[Real]
        skopt search space.
    objective_fn : callable
    callback : callable
        Progress callback from make_progress_callback.
    x0, y0 : list or None
        Prior evaluations for warm restart.

    Returns
    -------
    (minimize_fn, kwargs) : tuple
        Call as minimize_fn(**kwargs).

    Raises
    ------
    ValueError
        If opt_cfg["type"] is not in OPTIMIZER_MAP.
    """
    opt_type = opt_cfg["type"]
    if opt_type not in OPTIMIZER_MAP:
        raise ValueError(
            f"Unknown optimizer type '{opt_type}'. "
            f"Choose from: {list(OPTIMIZER_MAP.keys())}"
        )

    minimize_fn = OPTIMIZER_MAP[opt_type]
    n_initial   = 0 if x0 is not None else int(opt_cfg.get("n_initial_points", 10))

    kwargs = {
        "func":             objective_fn,
        "dimensions":       space,
        "n_calls":          int(opt_cfg["n_calls"]),
        "n_initial_points": n_initial,
        "random_state":     opt_cfg.get("random_state", 42),
        "callback":         [callback],
    }
    if x0 is not None:
        kwargs["x0"] = x0
        kwargs["y0"] = y0

    allowed = OPTIMIZER_KWARGS_WHITELIST[opt_type]
    for key, val in opt_cfg.items():
        if key.startswith("_") or key in _COMMON_KEYS:
            continue
        if key in allowed:
            kwargs[key] = val

    return minimize_fn, kwargs


# ---------------------------------------------------------------------------
# Results persistence and plotting
# ---------------------------------------------------------------------------

def save_results(result, output_directory: str, base_name: str,
                 opt_type: str, param_cfgs: list):
    """
    Save optimization results to CSV (warm-restart compatible) and pkl files,
    and write a convergence plot PDF.

    Parameters
    ----------
    result : OptimizeResult
        Return value of gp_minimize / forest_minimize / etc.
    output_directory : str
    base_name : str
        Stem for output filenames (no extension).
    opt_type : str
        Optimizer type string (e.g. "gp"); used in pkl filename.
    param_cfgs : list[dict]
        Parameter definitions; used for column names in the CSV.
    """
    import pandas as pd

    n_params = len(param_cfgs)

    # Warm-restart CSV
    df = pd.DataFrame(result.x_iters,
                      columns=[f"param_{i}" for i in range(n_params)])
    df["objective"] = result.func_vals
    df.to_csv(output_directory + "gp_results.csv", index=False)
    
    if "callback" in result.specs.get("args", {}):
        del result.specs["args"]["callback"]
    # Pickle without objective closure
    skopt_dump(result,
               output_directory + base_name + "_gp_result.pkl",
               store_objective=False)


    skopt_dump(result,
               output_directory + base_name + f"_{opt_type}_result.pkl",
               store_objective=False)

    # Convergence plot
    module = base_name.split("_results-")[-1].split("-")[0] if "_results-" in base_name else base_name
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(np.minimum.accumulate(result.func_vals),
            label="Best F (running min)", linewidth=1.5)
    ax.plot(result.func_vals, alpha=0.35, linewidth=0.8, label="F per iteration")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Objective value F")
    ax.set_title(f"Bayesian Optimization — {module}  [{opt_type.upper()}]")
    ax.legend()
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    plot_path = output_directory + f"results-{module}.pdf"
    fig.savefig(plot_path)
    plt.close(fig)
    print(f"  Convergence plot: {plot_path}")
