"""ML inference modules."""

from .solar_inference import SolarInference, get_solar_inference
from .voltage_inference import VoltageInference, get_voltage_inference

__all__ = ["SolarInference", "VoltageInference", "get_solar_inference", "get_voltage_inference"]
