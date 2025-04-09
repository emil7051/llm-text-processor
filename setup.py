from setuptools import setup, find_packages

setup(
    name="textcleaner",
    version="0.2.4",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "textcleaner=textcleaner.cli.commands:main",
        ],
    },
    python_requires=">=3.8",
    install_requires=[
        "pypdf>=3.15.1",
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
        "pdf2image>=1.16.0",
        "pytesseract>=0.3.9",
        "xlrd>=2.0.1",
        "lxml>=4.9.1",
        "requests>=2.28.1",
        "spacy>=3.4.0",
        "regex>=2022.3.15",
        "six",
    ],
) 