"""ML inference modules."""

from .solar_inference import SolarInference, get_solar_inference
from .voltage_inference import VoltageInference, get_voltage_inference

__all__ = ["SolarInference", "get_solar_inference", "VoltageInference", "get_voltage_inference"]
