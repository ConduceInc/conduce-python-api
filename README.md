# Conduce Python API

This library implements the most commonly used Conduce API endpoints.  It can be used for creating datasets and ingesting data, managing lenses and templates, and uploading various resources.

`api.py` is the majority of the implementation.  `conduce.py` is a command line utility for invoking the API.  It also servers as a representative implementation of the library.

# Installation

To install using pip:

```
pip install git+git://github.com/ConduceInc/conduce-python-api
```

or clone the repository and run:

```
python setup.py install
```

# Conduce Command Line Utilities

## Getting started

If you want to use the CLI without any setup you may fully specify your requests on the command line.

To list all datasets just:

```
conduce-api list datasets --host=dev-app.conduce.com --user=enterprise_test@conduce.com
```

Otherwise you'll want to setup a configuration, either by adding `~/.conduceconfig` and entering the configuration data, or by using the `config` subcommand:


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

If you provide an API key for your default user and host you will never have to enter credentials to use that account as long as the API key is valid.

## Features

The CLI provides many high level functions.  These include:

- Adding and removing datasets
- Creating a dataset from a CSV or JSON file
- Adding generic data to a dataset entity
- Listing datasets and orchestrations

All CLI functionality is available through `conduce/api.py` and all API functionality should be usable with or without a `.conduceconfig` file.


## Conduce Configuration

A basic configuration looks like:

```
default-host: dev-app.conduce.com
default-user: enterprise_test@conduce.com
dhl-dev@conduce.com:
  api-keys:
    dev-app: 'valid_api_key'
    prd-app: ''
    stg-app: ''
```

and is stored at `~/.conduceconfig`
