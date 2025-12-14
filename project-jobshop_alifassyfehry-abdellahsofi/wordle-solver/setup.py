from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wordle-solver",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Un solveur Wordle intelligent combinant CSP et LLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/wordle-solver",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Puzzle Games",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "ortools>=9.8.0",
        "anthropic>=0.18.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wordle-solver=wordle_solver.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "wordle_solver": ["dictionaries/*.txt"],
    },
)
