"""
optimizer.py
Optimizer agent: runs the Bayesian optimization and coordinates the others.

Starts the acquisition and objective agents in their own processes. The
objective function handed to skopt is a thin proxy: for each point it asks
the acquisition agent for an image, then asks the objective agent to score
that image, and returns the score. Everything else (search space, warm
start, progress CSV, optimizer choice, saved results) is the same code
path as optimize_sensor_LTA.py.
"""

import csv
import multiprocessing as mp
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from skopt.space import Real
from skopt.utils import use_named_args

import image_analysis as img
import bo_core        as bo

from . import protocol
from .acquisition import AcquisitionAgent
from .base import AgentHandle
from .objective import ObjectiveAgent


class OptimizerAgent:
    name = "optimizer"

    def __init__(self, cfg: dict, amplifier: int = None, resume: str = None,
                 log_messages: bool = True):
        self.cfg          = cfg
        self.module       = cfg["module"]
        self.amplifier    = amplifier if amplifier is not None else cfg["amplifier"]
        self.resume       = resume
        self.log_messages = log_messages
        self.param_cfgs   = cfg["parameters"]
        self.opt_cfg      = cfg["optimizer"]
        self.img_cfg      = cfg.get("image", {"output_base": "images",
                                              "prefix": "optimize_"})

        self.acquisition = None
        self.objective   = None
        self.iteration   = 0

    # ------------------------------------------------------------------
    # Proxy objective: one image in, one F out
    # ------------------------------------------------------------------

    def evaluate(self, x_values: np.ndarray) -> float:
        self.iteration += 1
        acquired = self.acquisition.request(
            "acquire", x_norm=[float(v) for v in x_values],
            iteration=self.iteration,
        )
        scored = self.objective.request(
            "evaluate", image_path=acquired["image_path"],
            iteration=self.iteration,
        )
        return scored["F"]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        date = datetime.now().strftime("%b-%d-%Y")

        # --------------------------------------------------------------
        # Output directory and progress CSV
        # --------------------------------------------------------------
        output_directory = "{}/{}/ai/{}/".format(
            self.img_cfg["output_base"], self.module, date)
        bo.initialize_directory(output_directory)

        file_name   = bo.get_unique_filename(odir=output_directory,
                                             ccd_code=self.module, date=date)
        csv_path    = output_directory + file_name
        file_handle = open(csv_path, "w", newline="")
        writer      = csv.writer(file_handle)
        writer.writerow(bo.build_csv_header(self.param_cfgs))
        file_handle.flush()

        log = protocol.MessageLog(
            output_directory + file_name[:-4] + "_messages.jsonl"
            if self.log_messages else None
        )

        try:
            # ----------------------------------------------------------
            # Start the other agents (acquisition = hardware init)
            # ----------------------------------------------------------
            ctx = mp.get_context("spawn")
            self.acquisition = AgentHandle(
                ctx, AcquisitionAgent,
                {"cfg": self.cfg, "output_directory": output_directory}, log)
            self.acquisition.wait_ready()

            self.objective = AgentHandle(
                ctx, ObjectiveAgent,
                {"cfg": self.cfg, "amplifier": self.amplifier,
                 "output_directory": output_directory}, log)
            self.objective.wait_ready()

            # ----------------------------------------------------------
            # Optimization space (all parameters normalized to [-1, 1])
            # ----------------------------------------------------------
            n_params = len(self.param_cfgs)
            space    = [Real(-1.0, 1.0, name=f"x{i}") for i in range(n_params)]

            @use_named_args(space)
            def objective_function(**X):
                return self.evaluate(np.array(list(X.values())))

            # ----------------------------------------------------------
            # Warm start
            # ----------------------------------------------------------
            x0, y0 = None, None

            if self.resume:
                if not os.path.exists(self.resume):
                    print(f"ERROR: Resume CSV not found: {self.resume}")
                    sys.exit(1)
                print(f"Loading previous results from {self.resume}...")
                df  = pd.read_csv(self.resume)
                x0  = df.drop(columns="objective").values.tolist()
                y0  = df["objective"].values.tolist()
                print(f"  Loaded {len(x0)} prior evaluations.")
            else:
                print("No resume file — starting fresh.")

            # ----------------------------------------------------------
            # Initial exposure before the optimization loop
            # ----------------------------------------------------------
            self.acquisition.request("initial_exposure")

            # ----------------------------------------------------------
            # Run optimization
            # ----------------------------------------------------------
            callback = bo.make_progress_callback(
                writer, file_handle, self.param_cfgs, output_directory,
                find_latest_fn=img.find_latest_fz_file,
            )
            minimize_fn, opt_kwargs = bo.build_optimizer_call(
                self.opt_cfg, space, objective_function, callback,
                x0=x0, y0=y0,
            )

            print(
                f"\nStarting {self.opt_cfg['type'].upper()} optimization "
                f"({self.opt_cfg['n_calls']} calls, module={self.module}, "
                f"amp={self.amplifier})...\n"
            )
            result = minimize_fn(**opt_kwargs)
            file_handle.close()

            # ----------------------------------------------------------
            # Report
            # ----------------------------------------------------------
            print("\n=== Optimization complete ===")
            for i, pcfg in enumerate(self.param_cfgs):
                lo, hi   = pcfg["bounds"]
                best_val = bo.from_normalized(result.x[i], lo, hi)
                print(f"  Best {pcfg['name']}: "
                      f"{round(best_val, pcfg.get('precision', 2))}")
            print(f"  Best F: {result.fun:.5f}")

            # ----------------------------------------------------------
            # Save results
            # ----------------------------------------------------------
            bo.save_results(
                result=result,
                output_directory=output_directory,
                base_name=file_name[:-4],
                opt_type=self.opt_cfg["type"],
                param_cfgs=self.param_cfgs,
            )
            print(f"\nAll results saved to {output_directory}")
            return result

        finally:
            for handle in (self.objective, self.acquisition):
                if handle is not None:
                    handle.shutdown()
            if not file_handle.closed:
                file_handle.close()
            log.close()
