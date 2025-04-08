#!/usr/bin/env python
from setuptools import setup, find_packages

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="textcleaner",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for converting various file formats to clean, LLM-friendly text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/textcleaner",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "pypdf>=3.15.1",  # Replaced PyPDF2 with pypdf (PyPDF2 is deprecated)
        "pdfminer.six>=20220524",
        "python-docx>=0.8.11",
        "openpyxl>=3.0.10",
        "python-pptx>=0.6.21",
        "pandas>=1.5.0",
        "beautifulsoup4>=4.11.1",
        "html2text>=2020.1.16",
        "nltk>=3.7",
        "pyyaml>=6.0",
        "click>=8.1.3",
        "tqdm>=4.64.1",
    ],
    entry_points={
        "console_scripts": [
            "textcleaner=textcleaner.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing :: General",
    ],
)
