from setuptools import setup, find_packages

setup(
    name="gazepointinterface",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
    ],
    author="Dhanush",
    description="GazePoint Interface with simulation support",
    python_requires=">=3.6",
)
