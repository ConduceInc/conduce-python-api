# Conduce Command Line Utilities

## Getting started
If you want to use the CLI without any setup you may fully specify your requests on the command line.

To list all datasets just:

```
python conduce.py list datasets --host=dev-app.conduce.com --user=enterprise_test@conduce.com
```

Otherwise you'll want to setup a configuration, either by adding `~/.conduceconfig` and entering the configuration data, or by using the `config` subcommand:


To list configuration options and syntax:

```
python conduce.py config --help
```

The basics:

```
python conduce.py config set default-user valid_user_name
python conduce.py config set default-host valid_host_name
```

If you want to avoid typing your password add API keys for the desired accounts:

```
python conduce.py config set api-key --key=valid_api_key --user=valid_user --host=valid_host
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
