from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="edmrn",
    version="2.3.0",
    author="Ninurta Kalhu",
    author_email="ninurtakalhu@gmail.com",
    description="ED Multi Route Navigation - Elite Dangerous route optimization and tracking tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
    ],
    python_requires=">=3.8",
    install_requires=[
        "customtkinter>=5.2.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "scipy>=1.10.0",
        "python-tsp>=0.2.0",
        "tqdm>=4.65.0",
        "Pillow>=10.0.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "edmrn=edmrn.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "edmrn": ["assets/*"],
    },
)