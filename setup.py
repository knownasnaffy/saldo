from setuptools import setup, find_packages
import re
import os


def get_version():
    """Read version from __init__.py"""
    init_file = os.path.join(os.path.dirname(__file__), "saldo", "__init__.py")
    with open(init_file, "r") as f:
        content = f.read()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="saldo",
    version=get_version(),
    author="Saldo Development Team",
    description="A command-line balance tracking application for ironing service transactions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=7.0",
    ],
    entry_points={
        "console_scripts": [
            "saldo=saldo.cli:cli",
        ],
    },
)
