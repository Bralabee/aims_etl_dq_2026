"""Setup configuration for AIMS Data Platform package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="aims-data-platform",
    version="1.0.2",
    description="AIMS data ingestion platform with incremental loading and data quality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="HS2 Data Team",
    author_email="data-team@hs2.org.uk",
    url="https://github.com/hs2/aims-data-platform",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0.0",
        "pyarrow>=14.0.0",
        "numpy>=1.24.0",
        "great-expectations>=0.18.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "azure": [
            "azure-identity>=1.15.0",
            "azure-storage-blob>=12.19.0",
            "azure-storage-file-datalake>=12.14.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aims-data=aims_data_platform.cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
    zip_safe=False,
)
