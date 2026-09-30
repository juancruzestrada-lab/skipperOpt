"""
optimize_agents.py
Bayesian optimization of LTA-controlled silicon detectors, run as three
cooperating agents (acquisition, objective, optimizer).

Same config file, command-line options, output files and optimization
results as optimize_sensor_LTA.py; the only difference is that image
acquisition and objective evaluation run in their own processes.

Usage
-----
    python optimize_agents.py --config config_skipper.json
    python optimize_agents.py --config config_skipper.json --amplifier 2
    python optimize_agents.py --config config_skipper.json --resume path/to/gp_results.csv
"""

import argparse
import json

from agents import OptimizerAgent


def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Bayesian optimization driver for LTA-controlled silicon "
                    "detectors (multi-agent)."
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
    parser.add_argument(
        "--no-message-log", action="store_true",
        help="Do not write the <run>_messages.jsonl record of agent messages."
    )
    args = parser.parse_args()

    OptimizerAgent(
        load_config(args.config),
        amplifier=args.amplifier,
        resume=args.resume,
        log_messages=not args.no_message_log,
    ).run()


if __name__ == "__main__":
    main()
