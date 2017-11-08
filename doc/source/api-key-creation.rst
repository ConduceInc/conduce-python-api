.. _api-key-creation:

====================
API Key Creation
====================

API keys are used to authenticate requests made using the Conduce REST API.  API keys are created by the user and should be protected like passwords.  Anyone with an API key can make requests to Conduce and perform operations as the user who owns the key.

Generally, there are three methods used to authenticate Conduce REST requests:

**username/password**
    used to establish a session
**session cookie**
    returned from a user name password login.  Used to continue a session started with a username/password login.
**API key**
    a unique string generated upon request that can be used to authenticate requests.

-------------------
Generating API keys
-------------------

In order to generate an API key, you must have a Conduce account.  Contact support@conduce.com if you do not already have an account.  Once your account is registered, you may create an API key.  It is easiest to do this using the Conduce command line utility.  Once you have installed the Conduce Python API from `GitHub <https://github.com/ConduceInc/conduce-python-api>`_ execute the following command from your shell prompt::

    conduce-api create-api-key --user=<email_address> --host=app.conduce.com

After entering the command you will be prompted for your password. After password submission, the new API key will be printed to the prompt and the command will finish.  Alternatively you may run a Python REPL and call :py:func:`api.create_api_key` directly.::

    import conduce
    conduce.api.create_api_key(user="<email_address>", host="app.conduce.com")

Again, you will be prompted for your password.  Upon submission, the new API key will be written to the prompt.

.. CAUTION::
    API keys can be used to perform any user operation.  This includes access to private data and personal information.  Be sure to protect API keys accordingly.


-------------------
Retreiving API keys
-------------------

API keys you have created may be retreived using the following command::

    conduce-api list-api-keys --user=<email_address> host=app.conduce.com

The API keys and the date on which they were created will be printed to the terminal.  As with API creation, the API keys may be listed using the Python API directly using :py:func:`api.list_api_keys`.

--------------
Using API keys
--------------

Once you have created an API key you may now execute API calls without password authentication.  The API key is therefore a substitute for your username and password.  We can use an API key as follows::

    conduce-api list-api-keys --api-key=<your-api-key> --host=app.conduce.com

or::

    import conduce
    conduce.api.list_api_keys(api_key="<your-api-key>" host="app.conduce.com")

API keys can be used in place of email addresses for all Conduce API requests.    

-------------------
Destroying API keys
-------------------

You may, from time to time, need to delete an API key (for example, if the key was shared with someone you no longer wish to have access).  When deleting an API key, you cannot use the key you are deleting as the authentication key.  You can either provide a username and password or an alternate key for the same account that owns the key you wish to delete.  You can delete an API key with the following command::

    conduce-api remove-api-key <the-api-key-to-remove> --api-key=<valid-api-key> --host=app.conduce.com

or::

    conduce-api remove-api-key <the-api-key-to-remove> --user=<email_address> --host=app.conduce.com

or::

    import conduce
    conduce.api.remove_api_key("<the-api-key-to-remove>", api_key="<valid-api-key>", host="app.conduce.com")

