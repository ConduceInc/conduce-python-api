.. _api-key-creation:

====================
API Key Creation
====================

API keys are used to authenticate requests made using the Conduce REST API.  API keys are created by the user and should be protected like passwords.  Anyone with an API key can make requests to Conduce and perform operations as the user who requested the key.

Generally, there are three methods used to authenticate Conduce REST requests:

**username/password**
    used to establish a session
**session cookie**
    returned from a user name password login.  Used to continue a session started with a username/password login.
**API key**
    a unique string generated upon request that can be used to authenticate requests.

In order to generate an API key, you must have a Conduce account.  Contact support@conduce.com if you do not already have an account.  Once your account is registered, you may create an API key.  It is easiest to do this using the Conduce command line utility.  Once you have :ref:`installed the Conduce Python API <https://github.com/ConduceInc/conduce-python-api>` execute the following command from your shell prompt::

    conduce-api create-api-key --user=new_user@conduce.com --host=app.conduce.com

After you submit your password, the new API key will be printed to the prompt and the command will finish.  Alternatively you may run a Python REPL and call :py:func:`api.create_api_key` directly.::

    import conduce
    conduce.api.create_api_key(user="new_user@conduce.com", host="app.conduce.com")

Again, you will be prompted for your password.  Upon submission, the new API key will be written to the prompt.

.. CAUTION::
    API keys can be used to perform any user operation.  This includes access to private data and personal information.  Be sure to protect API keys accordingly.

API keys you have created may be retreived using the following command::

    conduce-api list-api-keys --user=new_user@conduce.com host=app.conduce.com

The API keys and the date on which they were created will be printed to the terminal.  As with API creation.  The API keys may be listed using the Python API directly using :py:func:`api.list_api_keys`.

