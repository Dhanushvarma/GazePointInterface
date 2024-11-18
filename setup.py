from setuptools import setup, find_packages

setup(
    name="gazepointinterface",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["numpy", "threading", "socket"],
    author="Dhanush",
    description="GazePoint Interface with simulation support",
    python_requires=">=3.6",
)

from .gaze_sensor_server import GazepointClient, DataForwardingServer
from sim_client.gaze_data_client import SimGazeClient
from sim_client.gaze_data_processor import GazeDataUtil

__version__ = "0.1.0"
