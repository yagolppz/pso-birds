from setuptools import find_packages, setup


setup(
    name="pso-birds",
    version="0.1.0",
    description="Sistema PSO modular para evaluacion academica de paralelismo y concurrencia.",
    python_requires=">=3.10",
    packages=find_packages(
        include=[
            "core",
            "core.*",
            "experiments",
            "experiments.*",
            "io",
            "io.*",
            "objectives",
            "objectives.*",
            "parallel",
            "parallel.*",
            "viz",
            "viz.*",
        ],
        exclude=["results", "results.*", "tests", "tests.*"],
    ),
)
