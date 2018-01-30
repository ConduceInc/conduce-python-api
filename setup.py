from setuptools import setup
import os

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), "r") as f:
    required = f.read().splitlines()


setup(
    name="conduce",
    version="2.1.0",
    description="Python Distribution Utilities",
    author="Conduce",
    author_email="support@conduce.com",
    url="https://www.conduce.com",
    install_requires=required,
    packages=["conduce"],
    package_dir={"conduce": ""},
    entry_points={
        "console_scripts": ["conduce-api=conduce.conduce:main"],
    },
)
