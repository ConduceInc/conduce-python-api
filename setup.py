from setuptools import setup

setup(
    name="conduce",
    version="0.1.0",
    description="Python Distribution Utilities",
    author="Conduce",
    install_requires=["httplib2", "retrying"],
    author_email="support@conduce.com",
    url="https://www.conduce.com",
    packages=["conduce"],
    package_dir={"conduce": ""},
    entry_points={
        "console_scripts": ["conduce-api=conduce.conduce:main"],
    },
)
