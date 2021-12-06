import os
from setuptools import setup, find_namespace_packages


def get_requirements():
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, "requirements.txt")) as f:
        return [line.strip() for line in f]


print(find_namespace_packages(include=["*.*", "*.*"]))
setup(
    name="analytics-content-engine",
    version="0.0.1",
    packages=find_namespace_packages(include=["*.*", "*.*"]),
    zip_safe=False,
    install_requires=get_requirements(),
    scripts=[],
    data_files=[],
    python_requires=">=3.7",
)
