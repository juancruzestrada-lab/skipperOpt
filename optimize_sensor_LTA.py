"""
optimize_lta.py
Bayesian optimization driver for LTA-controlled silicon detectors.

Wires together:
    lta_control    -- LTA hardware commands and CCD sequencing
    image_analysis -- FITS I/O, derived statistics, objective evaluation
    bo_core        -- optimizer factory, progress logging, coordinate transforms

To target a different readout system, copy this file, replace the
lta_control import with (e.g.) archon_control, and update the hardware
init / expose / take_image calls in the objective closure. Everything
else — config schema, image analysis, optimizer selection — stays the same.

Usage
-----
    python optimize_lta.py --config config_mod9.json
    python optimize_lta.py --config config_mod9.json --amplifier 2
    python optimize_lta.py --config config_mod9.json --resume path/to/gp_results.csv
"""

import argparse
import csv
import json
import sys
import os
import numpy as np
import pandas as pd
import esp32_feather

from datetime import datetime
from skopt.space import Real
from skopt.utils import use_named_args

import lta_control   as lta_ctrl
import image_analysis as img
import bo_core        as bo


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bayesian optimization driver for LTA-controlled silicon detectors."
    )
    parser.add_argument(
        "--config", required=True,
        help="Path to JSON campaign config file."
    )
    parser.add_argument(
        "--amplifier", type=int, default=None,
        help="FITS amplifier extension index (overrides config)."
    )
    parser.add_argument(
        "--resume", default=None,
        help="Path to CSV with columns [param_0, ..., param_N, objective] for warm start."
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------------
    cfg        = load_config(args.config)
    module     = cfg["module"]
    nsamp      = cfg.get("nsamp", 1)
    nrow       = cfg.get("nrow", 75)
    exp_time   = cfg.get("exposure_time", 2)
    amplifier  = args.amplifier if args.amplifier is not None else cfg["amplifier"]
    param_cfgs = cfg["parameters"]
    det_cfg    = cfg["detector"]
    obj_cfg    = cfg["objective"]
    opt_cfg    = cfg["optimizer"]
    img_cfg    = cfg.get("image", {"output_base": "images", "prefix": "optimize_"})

    lta  = lta_ctrl.build_lta_cmd(cfg["lta"])
    date = datetime.now().strftime("%b-%d-%Y")

    # ------------------------------------------------------------------
    # Output directory and progress CSV
    # ------------------------------------------------------------------
    output_directory = "{}/{}/ai/{}/".format(img_cfg["output_base"], module, date)
    bo.initialize_directory(output_directory)

    file_name   = bo.get_unique_filename(odir=output_directory, ccd_code=module, date=date)
    csv_path    = output_directory + file_name
    file_handle = open(csv_path, "w", newline="")
    writer      = csv.writer(file_handle)
    writer.writerow(bo.build_csv_header(param_cfgs))
    file_handle.flush()

    # ------------------------------------------------------------------
    # Hardware init
    # ------------------------------------------------------------------
    arduino = esp32_feather.connect_arduino(cfg["arduino"]["port"])
    lta_ctrl.default_init(lta)

    # ------------------------------------------------------------------
    # Optimization space (all parameters normalized to [-1, 1])
    # ------------------------------------------------------------------
    n_params = len(param_cfgs)
    space    = [Real(-1.0, 1.0, name=f"x{i}") for i in range(n_params)]

    # ------------------------------------------------------------------
    # Objective function closure
    # ------------------------------------------------------------------
    counter_limit    = 1          # full re-exposure every iteration
    exposure_counter = [1]        # list for mutable closure state

    @use_named_args(space)
    def objective_function(**X):
        x_values = np.array(list(X.values()))

        # Expose
        lta_ctrl.expose_ccd(
            lta=lta,
            output_directory=output_directory,
            shutter_time=exp_time,
            counter=counter_limit,
            counter_limit=counter_limit,
            nrow=nrow,
            arduino=arduino,
        )

        if exposure_counter[0] < counter_limit:
            exposure_counter[0] += 1
        else:
            exposure_counter[0] = 1

        # Set parameters
        print("Setting parameters:")
        lta_ctrl.set_opt_parameters(lta, x_values, param_cfgs, bo.from_normalized)

        # Acquire
        lta_ctrl.take_image(
            lta=lta,
            directory=output_directory,
            nsamp=nsamp,
            nrow=nrow,
            prefix=img_cfg.get("prefix", "optimize_"),
        )

        # Evaluate
        return img.get_obj_value(output_directory, amplifier, det_cfg, obj_cfg)

    # ------------------------------------------------------------------
    # Warm start
    # ------------------------------------------------------------------
    x0, y0 = None, None

    if args.resume:
        if not os.path.exists(args.resume):
            print(f"ERROR: Resume CSV not found: {args.resume}")
            sys.exit(1)
        print(f"Loading previous results from {args.resume}...")
        df  = pd.read_csv(args.resume)
        x0  = df.drop(columns="objective").values.tolist()
        y0  = df["objective"].values.tolist()
        print(f"  Loaded {len(x0)} prior evaluations.")
    else:
        print("No resume file — starting fresh.")

    # ------------------------------------------------------------------
    # Initial exposure before the optimization loop
    # ------------------------------------------------------------------
    lta_ctrl.expose_ccd(
        lta=lta,
        output_directory=output_directory,
        shutter_time=exp_time,
        counter=counter_limit,
        counter_limit=counter_limit,
        nrow=nrow,
        arduino=arduino,
    )

    # ------------------------------------------------------------------
    # Run optimization
    # ------------------------------------------------------------------
    callback = bo.make_progress_callback(
        writer, file_handle, param_cfgs, output_directory,
        find_latest_fn=img.find_latest_fz_file,
    )
    minimize_fn, opt_kwargs = bo.build_optimizer_call(
        opt_cfg, space, objective_function, callback, x0=x0, y0=y0
    )

    print(
        f"\nStarting {opt_cfg['type'].upper()} optimization "
        f"({opt_cfg['n_calls']} calls, module={module}, amp={amplifier})...\n"
    )
    result = minimize_fn(**opt_kwargs)
    file_handle.close()

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print("\n=== Optimization complete ===")
    for i, pcfg in enumerate(param_cfgs):
        lo, hi    = pcfg["bounds"]
        best_val  = bo.from_normalized(result.x[i], lo, hi)
        print(f"  Best {pcfg['name']}: {round(best_val, pcfg.get('precision', 2))}")
    print(f"  Best F: {result.fun:.5f}")

    # ------------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------------
    bo.save_results(
        result=result,
        output_directory=output_directory,
        base_name=file_name[:-4],
        opt_type=opt_cfg["type"],
        param_cfgs=param_cfgs,
    )
    print(f"\nAll results saved to {output_directory}")


if __name__ == "__main__":
    main()