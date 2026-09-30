"""
Three-agent version of the LTA Bayesian optimization.

    AcquisitionAgent -- exposes the CCD, sets parameters, reads an image
    ObjectiveAgent   -- scores an image (objective function F)
    OptimizerAgent   -- runs skopt and coordinates the other two

Launch with optimize_agents.py.
"""

from .acquisition import AcquisitionAgent
from .objective import ObjectiveAgent
from .optimizer import OptimizerAgent
