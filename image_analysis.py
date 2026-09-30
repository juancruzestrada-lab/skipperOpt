"""
image_analysis.py
Detector image I/O and objective function evaluation.

Readout-system agnostic: operates on numpy arrays and FITS files regardless
of whether the data came from the LTA, Archon, or any other controller.
Knows about detector physics (gain, noise, overscan structure) but nothing
about how the image was acquired.

Objective function
------------------
    F = min(|noise_overscan / gain|, max_baseline) + sum_i coeff_i * raw_i**power_i

where each raw_i is computed by one of the registered penalty functions.
Penalty entries in the config JSON with "_disabled": true are skipped.

Registered penalty types
------------------------
    negative_gain       max(0, -gain)
    noise_exceeds_gain  max(0, noise_overscan - gain)
    saturation          max(0, 2 * noise_overscan - noise_active)
    gaussian_centering  norm.pdf(0, scale) - norm.pdf(charge_region, scale)
                        params: region ("active"|"overscan"), scale (ADU)
"""

import os
import glob
import numpy as np
import fitsio
from scipy.stats import norm


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_latest_fz_file(directory: str):
    """
    Return the most recently modified .fz file in directory, or None.

    Parameters
    ----------
    directory : str
        Path to search.

    Returns
    -------
    str or None
    """
    fz_files = glob.glob(os.path.join(directory, "*.fz"))
    if not fz_files:
        print("  No .fz files found in the directory.")
        return None
    return max(fz_files, key=os.path.getmtime)


def read_image(path: str, amplifier: int) -> np.ndarray:
    """
    Read a FITS image extension into a numpy array.

    Parameters
    ----------
    path : str
        Path to the .fz (or .fits) file.
    amplifier : int
        FITS extension index corresponding to the amplifier.

    Returns
    -------
    np.ndarray
        2D pixel array.
    """
    data, _ = fitsio.read(path, ext=amplifier, header=True)
    return data


# ---------------------------------------------------------------------------
# Derived statistics
# ---------------------------------------------------------------------------

def compute_derived_stats(data: np.ndarray, det_cfg: dict) -> dict:
    """
    Extract active and overscan regions and compute summary statistics.

    Parameters
    ----------
    data : np.ndarray
        Full 2D image array.
    det_cfg : dict
        config["detector"]. Expected structure::

            {
                "active":   {"rows": [r0, r1], "cols": [c0, c1]},
                "overscan": {"rows": [r0, r1], "cols": [c0, c1]}
            }

    Returns
    -------
    dict with keys:
        charge_active, charge_overscan, noise_active, noise_overscan,
        gain, active (2D array), overscan (2D array)
    """
    ar,  ac  = det_cfg["active"]["rows"],   det_cfg["active"]["cols"]
    orr, oc  = det_cfg["overscan"]["rows"], det_cfg["overscan"]["cols"]

    active   = data[ar[0]:ar[1],   ac[0]:ac[1]]
    overscan = data[orr[0]:orr[1], oc[0]:oc[1]]

    charge_active   = float(np.median(active))
    charge_overscan = float(np.median(overscan))
    noise_active    = float(np.std(active))
    noise_overscan  = float(np.std(overscan))
    gain            = charge_active - charge_overscan

    return {
        "charge_active":   charge_active,
        "charge_overscan": charge_overscan,
        "noise_active":    noise_active,
        "noise_overscan":  noise_overscan,
        "gain":            gain,
        "active":          active,
        "overscan":        overscan,
    }


# ---------------------------------------------------------------------------
# Penalty registry
# ---------------------------------------------------------------------------
# Each function receives (derived: dict, params: dict) and returns a
# non-negative scalar. The engine applies: F += coeff * raw**power.

def _penalty_negative_gain(d: dict, p: dict) -> float:
    """Penalizes inverted gain: max(0, -gain)."""
    return max(0.0, -d["gain"])


def _penalty_noise_exceeds_gain(d: dict, p: dict) -> float:
    """Penalizes overscan noise larger than signal gain: max(0, noise_os - gain)."""
    return max(0.0, d["noise_overscan"] - d["gain"])


def _penalty_saturation(d: dict, p: dict) -> float:
    """
    Penalizes saturation or near-zero gain.
    max(0, 2 * noise_overscan - noise_active).
    Triggers when active-area noise is anomalously low relative to overscan
    noise, indicating either saturation or effectively zero signal.
    """
    return max(0.0, 2.0 * d["noise_overscan"] - d["noise_active"])


def _penalty_gaussian_centering(d: dict, p: dict) -> float:
    """
    Soft penalty for charge level deviating from zero.
    raw = pdf(0, scale) - pdf(charge, scale) >= 0.

    params
    ------
    region : "active" | "overscan"  (default "overscan")
    scale  : Gaussian sigma in ADU  (default 5e4)
    """
    region_key = (
        "charge_active" if p.get("region", "overscan") == "active"
        else "charge_overscan"
    )
    charge = d[region_key]
    scale  = float(p.get("scale", 5e4))
    return float(norm.pdf(0.0, scale=scale) - norm.pdf(charge, scale=scale))


PENALTY_FUNCTIONS = {
    "negative_gain":      _penalty_negative_gain,
    "noise_exceeds_gain": _penalty_noise_exceeds_gain,
    "saturation":         _penalty_saturation,
    "gaussian_centering": _penalty_gaussian_centering,
}


# ---------------------------------------------------------------------------
# Objective function
# ---------------------------------------------------------------------------

def compute_objective(derived: dict, obj_cfg: dict) -> float:
    """
    Evaluate the scalar objective F from pre-computed image statistics.

    F = min(|noise_overscan / gain|, max_baseline)
        + sum_i( coeff_i * raw_i**power_i )

    Penalty entries with "_disabled": true are skipped.

    Parameters
    ----------
    derived : dict
        Output of compute_derived_stats.
    obj_cfg : dict
        config["objective"]. Expected keys:
            max_baseline : float  (cap on baseline term, default 1000)
            penalties    : list[dict], each with:
                type        : str   (key into PENALTY_FUNCTIONS)
                coefficient : float
                power       : float
                params      : dict  (passed to penalty function)
                _disabled   : bool  (optional; skips entry if true)

    Returns
    -------
    float
        Objective value F (minimized by the optimizer).

    Raises
    ------
    ValueError
        If an unknown penalty type is encountered.
    """
    gain           = derived["gain"]
    noise_overscan = derived["noise_overscan"]
    max_baseline   = float(obj_cfg.get("max_baseline", 1000.0))

    baseline = abs(noise_overscan / gain) if gain != 0.0 else max_baseline
    F = min(baseline, max_baseline)

    for pen in obj_cfg.get("penalties", []):
        if pen.get("_disabled", False):
            continue
        pen_type = pen["type"]
        if pen_type not in PENALTY_FUNCTIONS:
            raise ValueError(
                f"Unknown penalty type '{pen_type}'. "
                f"Registered types: {list(PENALTY_FUNCTIONS.keys())}"
            )
        raw   = PENALTY_FUNCTIONS[pen_type](derived, pen.get("params", {}))
        coeff = float(pen.get("coefficient", 1.0))
        power = float(pen.get("power", 1.0))
        F    += coeff * (raw ** power)

    print(
        f"  noise_os={noise_overscan:.2f}  charge_os={derived['charge_overscan']:.2f}"
        f"  charge_act={derived['charge_active']:.2f}  gain={gain:.2f}  F={F:.5f}"
    )
    return F


def get_obj_value(output_directory: str, amplifier: int,
                  det_cfg: dict, obj_cfg: dict) -> float:
    """
    End-to-end evaluation: find latest image → read → compute stats → compute F.

    Parameters
    ----------
    output_directory : str
        Directory containing .fz image files.
    amplifier : int
        FITS extension index.
    det_cfg : dict
        config["detector"].
    obj_cfg : dict
        config["objective"].

    Returns
    -------
    float
        Objective value F.

    Raises
    ------
    RuntimeError
        If no .fz file is found in output_directory.
    """
    latest = find_latest_fz_file(output_directory)
    if latest is None:
        raise RuntimeError(
            f"No .fz image found in {output_directory} — cannot evaluate objective."
        )
    print(f"  Reading: {os.path.basename(latest)}")
    data    = read_image(latest, amplifier)
    derived = compute_derived_stats(data, det_cfg)
    return compute_objective(derived, obj_cfg)