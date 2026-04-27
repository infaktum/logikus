# File: `setup.py`
from pathlib import Path

from setuptools import setup, find_packages

readme_path = Path(__file__).with_name("README.md")
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="logikus",
    version="0.1.0",
    description="Spielcomputer LOGIKUS®",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Heiko Sippel",
    license="MIT",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "pygame-ce>=2.5.7",
    ],
    entry_points={
        "console_scripts": [
            "logikus=logikus:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
