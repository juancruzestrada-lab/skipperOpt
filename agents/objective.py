"""
objective.py
Objective agent: turns an image into the scalar F the optimizer minimizes.

No hardware access. Runs the same steps as image_analysis.get_obj_value
(read -> derived stats -> objective), but on the image the acquisition
agent reports, and also returns the derived statistics so that whoever
coordinates the agents can inspect them.

Requests
--------
    evaluate(image_path, iteration) -> {"F": float, "stats": {...}}
"""

import os

import image_analysis as img

from .base import Agent


class ObjectiveAgent(Agent):
    name = "objective"

    def __init__(self, cfg: dict, amplifier: int, output_directory: str):
        self.det_cfg          = cfg["detector"]
        self.obj_cfg          = cfg["objective"]
        self.amplifier        = amplifier
        self.output_directory = output_directory

    def on_evaluate(self, image_path: str, iteration: int = None):
        if image_path is None:
            raise RuntimeError(
                f"No .fz image found in {self.output_directory} "
                "— cannot evaluate objective."
            )
        print(f"  Reading: {os.path.basename(image_path)}")
        data    = img.read_image(image_path, self.amplifier)
        derived = img.compute_derived_stats(data, self.det_cfg)
        F       = img.compute_objective(derived, self.obj_cfg)

        stats = {k: v for k, v in derived.items()
                 if k not in ("active", "overscan")}
        return {"F": F, "stats": stats}
