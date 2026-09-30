"""
lta_control.py
LTA (ltaDaemon) hardware interface for silicon detector readout.

Handles all os.system calls to the LTA shell script and Arduino LED/shutter
control. This module is the only place that knows about LTA command syntax —
swap it for archon_control.py (or similar) to target a different readout system
without touching bo_core or image_analysis.

Command routing:
    "set"    -> lta set <var> <val>   (bias voltages, gain settings)
    "direct" -> lta <var> <val>       (sequencer params: NSAMP, NROW, name, read)
    "timing" -> lta <var> <val>       (same format as direct; precision=0 enforces int)
"""

import os
import time
import numpy as np
import esp32_feather


# ---------------------------------------------------------------------------
# LTA session setup
# ---------------------------------------------------------------------------

def build_lta_cmd(lta_cfg: dict) -> str:
    """Construct the base LTA command string from config."""
    return "{} {}".format(lta_cfg["script"], lta_cfg["port"])


def default_init(lta: str):
    """Startup initialization. Add sequencer loads or default voltage sets here."""
    time.sleep(1)
    # os.system(lta + " set sinit 2")
    # os.system(lta + " set pinit 2")


# ---------------------------------------------------------------------------
# LTA parameter dispatch
# ---------------------------------------------------------------------------

def send_lta_param(lta: str, param_cfg: dict, physical_value: float):
    """
    Send a single parameter to the LTA controller.

    Parameters
    ----------
    lta : str
        Base LTA command string (from build_lta_cmd).
    param_cfg : dict
        Single entry from config["parameters"]. Must contain:
            command_type : "set" | "direct" | "timing"
            lta_var      : variable name as LTA expects it
            precision    : decimal places (0 → integer)
    physical_value : float
        Value in physical units (volts, counts, ns, etc.).
    """
    var       = param_cfg["lta_var"]
    precision = param_cfg.get("precision", 1)
    val       = int(round(physical_value)) if precision == 0 else round(physical_value, precision)

    cmd_type = param_cfg["command_type"]
    if cmd_type == "set":
        os.system(f"{lta} set {var} {val}")
    elif cmd_type in ("direct", "timing"):
        os.system(f"{lta} {var} {val}")
    else:
        raise ValueError(
            f"Unknown command_type '{cmd_type}' for parameter '{param_cfg['name']}'. "
            "Expected 'set', 'direct', or 'timing'."
        )


def set_opt_parameters(lta: str, x_norm: np.ndarray, param_cfgs: list,
                        from_normalized_fn):
    """
    Convert normalized optimizer values to physical units and send to LTA.

    Parameters
    ----------
    lta : str
        Base LTA command string.
    x_norm : np.ndarray
        Normalized parameter vector in [-1, 1].
    param_cfgs : list[dict]
        Parameter definitions from config["parameters"].
    from_normalized_fn : callable
        bo_core.from_normalized(x_norm, lo, hi) -> float.
    """
    for i, pcfg in enumerate(param_cfgs):
        lo, hi    = pcfg["bounds"]
        val_phys  = from_normalized_fn(x_norm[i], lo, hi)
        precision = pcfg.get("precision", 2)
        print(f"  {pcfg['name']}: {round(val_phys, precision)}")
        send_lta_param(lta, pcfg, val_phys)


# ---------------------------------------------------------------------------
# CCD sequencing
# ---------------------------------------------------------------------------

def clear_sensor(lta: str, directory: str):
    """Standard clear: single-sample full-column read."""
    time.sleep(1)
    # os.system(lta + f" name {directory}/CLEAR_")
    # os.system(lta + " NSAMP 1")
    # os.system(lta + " NROW 650")
    # os.system(lta + " read")


def clear_sensor_v2(lta: str, directory: str):
    """
    Two-phase clear: drain flush followed by reverse-clocking sequencer.
    Preferred for SiSeRO to minimize residual charge.
    """
    time.sleep(1)
    # os.system(lta + f" name {directory}/CLEAR_")
    # os.system(lta + " sseq ./sisero_scripts/clear_v4_drain_in_the_middle"
    #                 "sisero_sequencer_binned_fast.xml")
    # os.system(lta + " NSAMP 1")
    # os.system(lta + " NROW 650")
    # os.system(lta + " runseq")
    # os.system(lta + " sseq ./sisero_scripts/sisero_reverse_sequencer_binned_fast.xml")


def expose_ccd(lta: str, output_directory: str, shutter_time: float,
               counter: int, counter_limit: int, nrow: int, arduino):
    """
    Expose the CCD to light via Arduino-controlled LED.

    If counter < counter_limit, the CCD is being read out in partial strips
    and no new exposure is needed yet. Once the strip counter reaches the
    limit, the CCD is cleared and re-exposed.

    Parameters
    ----------
    lta : str
    output_directory : str
    shutter_time : float
        Exposure duration in seconds.
    counter : int
        Current strip counter.
    counter_limit : int
        Number of strips before a full re-exposure is triggered.
    nrow : int
        Rows per strip (for progress reporting).
    arduino : serial.Serial
        Connected Arduino handle from esp32_feather.connect_arduino.
    """
    if counter < counter_limit:
        print(f"  Partial read: {nrow * counter} rows accumulated.")
    else:
        print("  Clearing CCD...")
        clear_sensor_v2(lta, output_directory)
        print(f"  Exposing for {shutter_time} s...")
        esp32_feather.set_LED("255", arduino)
        time.sleep(shutter_time)
        esp32_feather.set_LED("OFF", arduino)
        print("  Exposure complete.")


def take_image(lta: str, directory: str, nsamp: int, nrow: int,
               prefix: str = "optimize_"):
    """
    Configure and trigger a single LTA readout.

    Parameters
    ----------
    lta : str
    directory : str
        Output directory passed to LTA name command.
    nsamp : int
        Number of non-destructive samples (Skipper mode).
    nrow : int
        Number of rows to read.
    prefix : str
        Filename prefix for the output image.
    """
    os.system(lta + f" NSAMP {int(nsamp)}")
    os.system(lta + f" NROW {int(nrow)}")
    os.system(lta + f" name {directory}/{prefix}")
    os.system(lta + " read")