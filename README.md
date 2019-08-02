# Conduce Python API

This library implements the most commonly used Conduce API endpoints. It can be used for creating datasets and ingesting data, managing lenses and templates, and uploading various resources.

`conduce/api.py` is the majority of the implementation. `conduce/cli.py` is a command line utility for invoking the API. It also serves as a representative implementation of the library.

# Prerequisites

Conduce Python API requires that you have installed the following:

* Python 2.7 or Python 3.6: https://www.python.org/downloads/
* pip: https://pip.pypa.io/en/stable/installing/

# Installation

To install using pip:

```
pip install git+git://github.com/ConduceInc/conduce-python-api
```

or clone the repository and run:

```
pip install .
```

from the installed directory.

# Using the API

Once you have installed the API, you may use it in a python script by importing the `conduce` module:

```
import conduce.api
```

Then you may use API functions, like `create_dataset` as follows:

```
conduce.api.create_dataset('my-dataset-name',
     host='app.conduce.com', user='email@example.com')
```

However, this requires that the user authenticate with their password when the script is executed. To avoid this, provide an `api-key` argument instead of `user`. If you would like to learn more about API key creation, take a look at [API Key Creation](https://conduce-conduce-python-api.readthedocs-hosted.com/en/latest/api-key-creation.html).

The most common use for the python API is data ingest. Data ingest is too large a topic to be covered here, if you'd like to learn more, check out [Intro to Data Ingest](https://conduce-conduce-python-api.readthedocs-hosted.com/en/latest/data-ingest.html)

Other API features are documented in the [API Reference](https://conduce-conduce-python-api.readthedocs-hosted.com/en/latest/api-ref.html).

# Conduce Command Line Interface

## Getting started

The Conduce command line interface provides users with utilities for exercising common API commands, and textual feedback for inspecting and debugging. Features include:

* Creating API keys
* Adding and removing datasets
* Creating a dataset from a CSV or JSON file
* Listing datasets and other resources

All CLI functionality is available through `conduce/api.py` and all API functionality should be usable with or without a `.conduceconfig` file. If you want to use the CLI without any setup you may fully specify your requests on the command line.

As an example, you may list existing datasets with the following command:

```
conduce-api list datasets --host=app.conduce.com --user=email@example.com
```

## Setup

As mentioned above, rather than fully specifying every request, you can setup a `~/.conduceconfig` and entering the configuration data, or by using the `config` subcommand:

To list configuration options and syntax:

```
conduce-api config --help
```

The basics:

Use the following commands to avoid specifying your email address and the target server on the command line:

```
conduce-api config set default-user valid_user_name
conduce-api config set default-host valid_host_name
```

If you want to avoid typing your password add API keys for the desired accounts:

```
conduce-api config set api-key --key=valid_api_key --user=valid_user --host=valid_host
```

or create an API key by adding the `--new` flag

```
conduce-api config set api-key --new --user=valid_user --host=valid_host
```

If you configure an API key for your default user and host you will never have to enter credentials to use that account as long as the API key is valid.

## Conduce Configuration

A basic configuration looks like:

```
default-host: app.conduce.com
default-user: email@example.com
email@example.com:
  api-keys:
    dev-app: 'valid_api_key'
    prd-app: ''
    stg-app: ''
```

and is stored at `~/.conduceconfig`

# Development

## Python environment

Setup a Python 3 development environment. It is recommended that you not use the Python installed on your system, but rather manage your development environment with pyenv.

https://opensource.com/article/19/5/python-3-default-macos

Once commands `python` and `pip` point to version 3 you are ready to continue.

## Virtual environment

Clone this repository setup a virtual environment

```
$ git clone git@github.com:ConduceInc/conduce-python-api.git
$ cd conduce-python-api
$ python -m venv venv
$ . venv/bin/activate
$ pip install -r requirements-dev.txt
```

## Building documentation

Documentation is built with Sphinx. To install Sphinx and Sphinx extensions, run:

```
pip install -r requirements-all.txt
```

to install runtime and documentation dependencies, or:

```
pip install -r requirements-docs.txt
```

if you only need to install the documentation dependencies. Next, build the documentation:

```
cd doc
make html
```

The documentation will be built in:

```
doc/build/html/
```

Finally, navigate to `index.html` with a web browser to view the local copy of the documentation.

Official Conduce Python API documentation can be found online at: https://conduce-conduce-python-api.readthedocs-hosted.com/en/latest/

## Unit testing

To run unit tests (from an activated virtual environment):

```
$ python -m unittest discover -v test/
```
