from setuptools import setup, find_packages

setup(
    name="railway-cli",
    version="0.1.0",
    description="Israel Railways CLI for searching train routes",
    author="Aviv Shafir",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "fire",
        "israelrailapi",
        "pytz",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "railwaycli=railwaycli.cli:main",
        ],
    },
    scripts=["bin/railwaycli"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
)
