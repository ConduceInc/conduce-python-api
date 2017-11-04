.. _data-ingest:

.. toctree::
    :hidden:

    conduce-entities

====================
Intro to Data Ingest
====================

Visualizing your data in Conduce begins with ingest.  Ingest is the process translating your data into a format that Conduce understands.  Conduce uses entities to define unique objects.  Entities are ingested into datasets.  Datasets hold collections of related entities and provide the interface a user needs to connect their data to a visualization renderer.

Conduce needs a few key pieces of information in order to visualize your data in space and time, those are:

**Identity**
   Identities distinguish one entity from another.  An entity exists in Conduce as one more more samples.  All samples that describe the same entity share an identity.
**Location**
   An entities location describes where in space the entity exists.  Locations are defined in units according to the coordinate system in which they are displayed. (Latitude and Longitude on a world map.)
**Time**
   Time defines the moment in time at which the rest of the information describing an entity is valid.

With this information Conduce can build a representation of an object that exists in space and time.  Entity definitions can be more complex, for more information on how to build entities please read :doc:`conduce-entities`.

--------
Datasets
--------

Datasets are the containers that hold entities.  A dataset may be thought of as a table.  Each entity in a dataset is similar in nature, but has unique properties.  In order to represent and entity in Conduce, its sample data must be ingested into a dataset.  In order to perform any API operations it is recommended that you generate an API key.  (See :doc:`api-key-creation` for more information.)  The first step in ingesting data is acquiring a dataset ID.  If you are ingesting data into a new dataset you'll need to create the dataset  before entities can be ingested.

:py:func:`api.create_dataset`::

    my_dataset_id = conduce.api.create_dataset('my dataset name', host='app.conduce.com', api-key='00000000-0000-0000-0000-000000000000')


The dataset ID returned is a UUID.  It will be passed as a function parameter to the :py:func:`api.ingest_samples` function.

If you want to ingest data into an existing dataset you will need to acquire its dataset ID.  Datasets are Conduce resources.  All resources have an ID and can be queried with the resource API.  The Conduce Python API provides convenience methods for listing datasets

:py:func:`api.list_datasets`::

    datasets = conduce.api.list_datasets(host='app.conduce.com', api-key='00000000-0000-0000-0000-000000000000')

This call returns a list of dictionaries, each contains information about a particular dataset::

    {
       "name": "US Cities",
       "tags": [],
       "create_time": 1506544998452,
       "version": 0,
       "mime": "application/json",
       "modify_time": 1508869186664,
       "revision": 4,
       "type": "DATASET",
       "id": "a262342b-22d2-4368-4698-cf75b62b7cb3",
       "size": 2
     }

This dataset object contains information to help identify a dataset.  The fields ``name`` and ``tags``, along with ``create_time`` and ``modify_time`` are particularly useful for identifying datasets.  The :py:func:`api.find_datasets` function can be used to list only datasets that match certain search criteria.

------------------
Ingesting entities
------------------

In order to ingest our source data we must first convert each record into an entity sample as described above.  Once converted, the samples are added to a list.  The list may contain samples for multiple entities.  Once we have created our sample list we call :py:func:`api.ingest_samples`::

    conduce.api.ingest_samples(dataset_id, sample_list, host=app.conduce.com, api-key=00000000-0000-0000-0000-000000000000)

This function takes a dataset ID as the first argument.  A dataset must exist before samples can be ingested.

-----------------
Updating entities
-----------------

Stuff about updating the state of an entity (append API)

.. list-table:: Data update: shipment 1
   :header-rows: 1
   :widths: auto

   * - ID
     - Method
     - Date
     - Latitude
     - Longitude
     - Value
     - State
   * - 1
     - ground
     - 2017-10-24T10:23:14+00:00
     - 38.022131
     - -91.571045
     - $102,325.26
     - delivered

