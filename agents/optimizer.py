"""
optimizer.py
Optimizer agent: runs the Bayesian optimization and coordinates the others.

Starts the acquisition and objective agents in their own processes. The
objective function handed to skopt is a thin proxy: for each point it asks
the acquisition agent for an image, then asks the objective agent to score
that image, and returns the score. Everything else (search space, warm
start, progress CSV, optimizer choice, saved results) is the same code
path as optimize_sensor_LTA.py.

With optimizer type "claude" the skopt minimizer is replaced by Claude
choosing each point (agents/claude_optimizer.py); everything else is
unchanged.

Every run, of any optimizer type, ends with an entry in the lab notebook
(agents/notebook.py), also when it is interrupted. Config keys, all in
"optimizer":
    "notebook":      path, or false to turn the notebook off
                     (default <output_base>/<module>/claude_notebook.md)
    "notebook_read": false: Claude does not read the notebook at the start
                     (the entry is still written); default true
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

from . import notebook as nb
from . import protocol
from .acquisition import AcquisitionAgent
from .base import AgentHandle
from .objective import ObjectiveAgent


class OptimizerAgent:
    name = "optimizer"

    def __init__(self, cfg: dict, amplifier: int = None, resume: str = None,
                 log_messages: bool = True, config_name: str = ""):
        self.cfg          = cfg
        self.module       = cfg["module"]
        self.amplifier    = amplifier if amplifier is not None else cfg["amplifier"]
        self.resume       = resume
        self.log_messages = log_messages
        self.param_cfgs   = cfg["parameters"]
        self.opt_cfg      = cfg["optimizer"]
        self.img_cfg      = cfg.get("image", {"output_base": "images",
                                              "prefix": "optimize_"})

        self.acquisition  = None
        self.objective    = None
        self.iteration    = 0
        self.observations = []   # image stats per evaluation (used by "claude")
        self.records      = []   # this run's measurements, for the notebook
        self.config_name  = os.path.basename(config_name) if config_name else ""

        setting = self.opt_cfg.get("notebook", True)
        self.notebook_path = (None if setting is False or setting is None else
                              setting if isinstance(setting, str) else
                              os.path.join(self.img_cfg["output_base"], self.module,
                                           "claude_notebook.md"))
        self.notebook_read = bool(self.opt_cfg.get("notebook_read", True))

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
        self.observations.append(scored["stats"])
        image = acquired["image_path"]
        self.records.append({"x": [float(v) for v in x_values],
                             "F": float(scored["F"]), "stats": scored["stats"],
                             "image": os.path.basename(image) if image else None})
        return scored["F"]

    def write_notebook_entry(self, lessons: str = "", status: str = ""):
        """Append this run's entry to the lab notebook (never raises)."""
        if not self.notebook_path or not self.records:
            return
        try:
            header, body = nb.make_entry(
                self.records, self.param_cfgs, self.module, self.amplifier,
                self.opt_cfg["type"], self.config_name, self.t_start,
                datetime.now(), x0=self.x0, y0=self.y0, lessons=lessons,
                status=status)
            nb.append_notebook_entry(self.notebook_path, header, body)
            print(f"\nLab notebook entry added to {self.notebook_path}:\n"
                  f"## {header}\n\n{body}")
        except Exception as err:
            print(f"\nWARNING: could not write the lab notebook entry ({err}); "
                  "the campaign results are unaffected.")

    def save_resume_csv(self, result, output_directory: str):
        """
        Write gp_results.csv (same format as bo.save_results) after every
        iteration, so an interrupted run can be continued with --resume.
        """
        df = pd.DataFrame(result.x_iters,
                          columns=[f"param_{i}" for i in range(len(self.param_cfgs))])
        df["objective"] = result.func_vals
        path = output_directory + "gp_results.csv"
        df.to_csv(path + ".tmp", index=False)
        os.replace(path + ".tmp", path)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        self.t_start = datetime.now()
        self.x0, self.y0 = None, None
        date = self.t_start.strftime("%b-%d-%Y")

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

        lessons, failure = "", None
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
                self.x0, self.y0 = x0, y0
            else:
                print("No resume file — starting fresh.")

            # ----------------------------------------------------------
            # Initial exposure before the optimization loop
            # ----------------------------------------------------------
            self.acquisition.request("initial_exposure")

            # ----------------------------------------------------------
            # Run optimization
            # ----------------------------------------------------------
            progress = bo.make_progress_callback(
                writer, file_handle, self.param_cfgs, output_directory,
                find_latest_fn=img.find_latest_fz_file,
            )

            def callback(result):
                progress(result)
                self.save_resume_csv(result, output_directory)
            is_claude = self.opt_cfg["type"] == "claude"
            notebook_text = ""
            if self.notebook_path:
                if is_claude and self.notebook_read:
                    notebook_text = nb.load_notebook(
                        self.notebook_path,
                        self.opt_cfg.get("notebook_max_chars",
                                         nb.DEFAULT_NOTEBOOK_MAX_CHARS))
                    state = (f"loaded, {len(notebook_text)} characters"
                             if notebook_text else "empty")
                elif is_claude:
                    state = "not read for this run (notebook_read is false)"
                else:
                    state = "not read by this optimizer"
                print(f"Lab notebook: {self.notebook_path} ({state}); "
                      "an entry is added at the end of the run.")

            if is_claude:
                from .claude_optimizer import build_claude_call
                minimize_fn, opt_kwargs = build_claude_call(
                    self.opt_cfg, space, objective_function, callback,
                    self.param_cfgs, self.cfg["objective"], self.observations,
                    output_directory + file_name[:-4] + "_claude_decisions.jsonl",
                    x0=x0, y0=y0,
                    notebook_text=notebook_text,
                    lessons=bool(self.notebook_path),
                    module=self.module,
                    amplifier=self.amplifier,
                )
            else:
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
            lessons = result.specs.get("lessons", "") if is_claude else ""

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

        except BaseException as err:
            failure = err
            raise

        finally:
            if not (isinstance(failure, SystemExit) and not self.records):
                self.write_notebook_entry(
                    lessons=lessons,
                    status=f"interrupted ({type(failure).__name__})" if failure else "")
            for handle in (self.objective, self.acquisition):
                if handle is not None:
                    handle.shutdown()
            if not file_handle.closed:
                file_handle.close()
            log.close()
