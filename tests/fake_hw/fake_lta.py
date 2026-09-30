#!/usr/bin/env python3
"""
Stand-in for lta.sh (tests only).

    fake_lta.py PORT set VAR VAL | PORT VAR VAL | PORT name PREFIX | PORT read

State lives in $FAKE_LTA_STATE. "read" writes a synthetic two-extension
image whose overscan noise and signal depend on the voltages and timing
that were set, so the optimizer has a real landscape to explore.
"""
import json
import os
import sys

import numpy as np

state_path = os.environ["FAKE_LTA_STATE"]
state = json.load(open(state_path)) if os.path.exists(state_path) else {"n": 0}

args = sys.argv[2:]
if args[0] == "set":
    state[args[1]] = float(args[2])
elif args[0] == "name":
    state["name"] = args[1]
elif args[0] == "read":
    vdd, vdrain = state.get("vdd", -16.0), state.get("vdrain", -16.0)
    vr, delay = state.get("vr", -6.5), state.get("delay_H_overlap", 20.0)
    noise  = 2.0 + 0.05 * (vdd + 17) ** 2 + 0.03 * (vdrain + 14) ** 2 + 0.5 * (vr + 6.2) ** 2
    signal = 100.0 * (1.0 - 0.01 * abs(delay - 18))
    rng = np.random.default_rng(state["n"])
    rows, cols = int(state.get("NROW", 75)), 110
    img = 1000.0 + noise * rng.standard_normal((2, rows, cols))
    img[:, :, 16:56] += signal
    with open(f"{state['name']}{state['n']}.fz", "wb") as f:
        np.save(f, img)
    state["n"] += 1
else:
    state[args[0]] = float(args[1])

json.dump(state, open(state_path, "w"))
