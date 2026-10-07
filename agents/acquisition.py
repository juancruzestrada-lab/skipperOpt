"""
acquisition.py
Acquisition agent: the only agent that touches hardware.

Owns the ESP32 (LED) connection and the LTA. For each request it exposes
the CCD, sets the operating parameters and reads out an image, then reports
the path of the new image. Swap lta_control for another readout module to
target a different controller; the other agents do not change.

Requests
--------
    initial_exposure()        -> {}
    acquire(x_norm, iteration) -> {"image_path": str | None}

A parameter's "lta_var" may be a list: the one optimized value is then sent
to every listed LTA variable (e.g. "hh" -> h1ah, h1bh, h2ch, h3ah, h3bh, as
in the LTA voltage scripts). Single-variable parameters are sent exactly as
before, through lta_control.set_opt_parameters.
"""

import numpy as np

import esp32_feather
import lta_control    as lta_ctrl
import image_analysis as img
import bo_core        as bo

from .base import Agent


def expand_linked(param_cfgs: list, x_norm) -> tuple:
    """
    One entry per LTA variable: a parameter whose lta_var is a list becomes
    one copy per variable, all with the same value.
    """
    cfgs, xs = [], []
    for pcfg, x in zip(param_cfgs, x_norm):
        if isinstance(pcfg["lta_var"], (list, tuple)):
            for var in pcfg["lta_var"]:
                cfgs.append({**pcfg, "lta_var": var,
                             "name": f"{pcfg['name']} ({var})"})
                xs.append(x)
        else:
            cfgs.append(pcfg)
            xs.append(x)
    return cfgs, np.array(xs)


class AcquisitionAgent(Agent):
    name = "acquisition"

    def __init__(self, cfg: dict, output_directory: str):
        self.cfg              = cfg
        self.output_directory = output_directory
        self.nsamp            = cfg.get("nsamp", 1)
        self.nrow             = cfg.get("nrow", 75)
        self.exp_time         = cfg.get("exposure_time", 2)
        self.param_cfgs       = cfg["parameters"]
        self.img_cfg          = cfg.get("image", {"output_base": "images",
                                                  "prefix": "optimize_"})
        self.lta              = lta_ctrl.build_lta_cmd(cfg["lta"])
        self.arduino          = None

        self.counter_limit    = 1      # full re-exposure every iteration
        self.exposure_counter = 1

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setup(self):
        self.arduino = esp32_feather.connect_arduino(self.cfg["arduino"]["port"])
        lta_ctrl.default_init(self.lta)

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def _expose(self):
        lta_ctrl.expose_ccd(
            lta=self.lta,
            output_directory=self.output_directory,
            shutter_time=self.exp_time,
            counter=self.counter_limit,
            counter_limit=self.counter_limit,
            nrow=self.nrow,
            arduino=self.arduino,
        )

    def on_initial_exposure(self):
        self._expose()
        return {}

    def on_acquire(self, x_norm: list, iteration: int = None):
        x_values = np.array(x_norm)

        # Expose
        self._expose()

        if self.exposure_counter < self.counter_limit:
            self.exposure_counter += 1
        else:
            self.exposure_counter = 1

        # Set parameters
        print("Setting parameters:")
        cfgs, xs = expand_linked(self.param_cfgs, x_values)
        lta_ctrl.set_opt_parameters(self.lta, xs, cfgs, bo.from_normalized)

        # Acquire
        lta_ctrl.take_image(
            lta=self.lta,
            directory=self.output_directory,
            nsamp=self.nsamp,
            nrow=self.nrow,
            prefix=self.img_cfg.get("prefix", "optimize_"),
        )

        return {"image_path": img.find_latest_fz_file(self.output_directory)}
