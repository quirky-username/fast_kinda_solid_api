from setuptools import find_packages, setup

setup(
    name="update_all",
    version="0.1",
    packages=find_packages(),
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "update_all=main:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.12",
)
