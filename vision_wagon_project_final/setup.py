"""
Setup script for Vision Wagon Project
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("vision_wagon/requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vision-wagon",
    version="1.0.0",
    author="Vision Wagon Team",
    author_email="team@visionwagon.com",
    description="Sistema de IA Generativa y Automatización para el ecosistema Nómada Alpha",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/visionwagon/vision-wagon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vision-wagon=vision_wagon.cli:cli_main",
        ],
    },
    include_package_data=True,
    package_data={
        "vision_wagon": ["*.yaml", "*.yml", "*.json"],
    },
)

