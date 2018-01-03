.. _data-ingest:


====================
Intro to Data Ingest
====================

Visualizing your data in Conduce begins with data ingest.  Ingest is the process of translating your data into Conduce entities.  A conduce entity represents a unique object and is defined by entries in a dataset.  There are two types of entries:

- a series of discrete samples
- a constant continuous function (constant entity)

Entries are ingested into datasets.  Entries that share a common ID field describe the same entity.  Conduce needs a few key pieces of information in order to visualize your data in space and time, those are:

**Identity**
   Identities distinguish one entity from another.  For constant entities, each constant has a unique identity.  For other entities, all samples that describe the same entity share an identity.
**Location**
   An entity's location describes where in space the entity exists.  Locations are defined in units according to the coordinate system in which they are displayed. (Latitude and Longitude on a world map.)
**Time (samples only)**
   Time defines the moment in time at which the rest of the information describing an entity is valid.

With this information Conduce can build a representation of an object that exists in space and time.  Entity definitions can be more complex, for more information on how to build entities please read :doc:`conduce-entities`.

-----------------
Creating Datasets
-----------------

.. tip:: Use of an API key is recommended.  See :doc:`api-key-creation` for more information.

Datasets hold collections of related entities and provide the interface a user needs to connect their data to a visualization renderer.  A dataset may be thought of as a table.  Each entity in a dataset is similar in nature, but has unique properties.  In order to represent an entity in Conduce, entries that define it must be ingested into a dataset.  The first step in ingesting data is acquiring a dataset ID.  If you are ingesting data into a new dataset you'll need to create the dataset before entries can be ingested.

:py:func:`api.create_dataset`::

    world_cities_dataset = conduce.api.create_dataset('world cities', host='app.conduce.com', api-key='00000000-0000-0000-0000-000000000000')
    world_cities_dataset_id = world_cities_dataset['id']

The dataset object retuned contains a dataset ID such as '55611f65-c657-45b1-9d04-fe19227f6306'. This is a UUID which will be passed as a function parameter to the :py:func:`api.ingest_entities` function.

If you want to ingest data into an existing dataset you will need to acquire its dataset ID.  Datasets are Conduce resources.  All resources have an ID and can be queried with the REST API.  The Conduce Python API provides a convenience method (:py:func:`api.list_datasets`) for listing datasets::

    datasets = conduce.api.list_datasets(host='app.conduce.com',
        api-key='00000000-0000-0000-0000-000000000000')

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

-------------------
Populating datasets
-------------------

Once a dataset has been created, it needs to be populated before it can be visualized.  A dataset is populated by creating entries and making API calls to add them to the dataset.  See :doc:`conduce-entities` for detailed information on creating entities.

In this primer you will focus on a simple example, ingesting constant entities from a data file. Simplemaps provides a free list of world cities that you can download `here <https://simplemaps.com/data/world-cities>`_.  A version of this list is also provided in the Conduce Python API samples directory.

Once you have the data downloaded you must decide how the data should be represented in Conduce.  Each record is described by the following fields:

- city
- city_ascii
- lat
- lng
- pop
- country
- iso2
- iso3
- province

These fields are described in detail on the page from which the data is downloaded.  For this example you'll work with all the fields.  However the only fields that are required are ``lat`` and ``lng``.

A dataset entry requires the following fields in order to be ingested: ID, location, and kind.  Kind is a field that describes the type of thing the entity represents.  You'll be ingesting this data as constant entities, so a timestamp is not required.  You'll map the source data to dataset entries as follows::

    {
        "id": <UUID you will generate>,
        "kind": "city",
        "point": {
            "lat": <lat>,
            "lon": <lng>
        },
        "name": <city>,
        "long_name": <city_ascii>,
        "population": <pop>,
        "province": <province>,
        "country": <country>,
        "iso2": <iso2>,
        "iso3": <iso3>,
    }

Notice that two of the fields ``id`` and ``kind`` are not derived from the data.  You will generate a unique ID just in case any of the city names are the same.  You will hard code ``kind`` to city in case you want to ingest other types of data into this dataset in the future.  If you wanted to do something more sophisticated you could categorize the cities by population and set ``kind`` to something like "small_city," "medium_city," and "large_city."

Following this pattern, the first city in the dataset takes the following form::

    {
        "id": str(uuid.uuid4()),
        "kind": "city",
        "point": {
            "lat": 34.9830001,
            "lon": 63.13329964
        },
        "name": "Qal eh-ye",
        "long_name": "Qal eh-ye Now",
        "population": 2997,
        "province": "Badghis",
        "country": "Afghanistan",
        "iso2": "AF",
        "iso3": "AFG",
    }

Writing the code to iterate over the CSV file and convert each record to a dataset entry is left to the reader.  However there are utilities included with the Conduce Python API that provide example implementations.

The resulting entities should be compiled into a list.  Once you have generated the entity list, it is time to send the data to Conduce.

++++++
Ingest
++++++

Datasets are populated through a process called ingest.  If creating or updating constant entities call :py:func:`api.ingest_entities`.  If you are defining entities with samples, call :py:func:`api.ingest_samples`.

In this example, you are ingesting constant entities and will use :py:func:`api.ingest_entities`.  The list of entities you generated was written to a variable named ``entity_list``.  All that's left is to call the API function using the dataset ID you created earlier and the API key you generated::

    conduce.api.ingest_entities(world_cities_dataset_id,
        entity_list, host=app.conduce.com, 
        api-key=00000000-0000-0000-0000-000000000000)

After this function returns, the dataset will be populated with the entities derived from the spreadsheet.

----------
Next steps
----------

Once you have constructed a dataset, you are ready to attach it to a visualization.  Documentation for building visualizations is a work in progress.  For assistance creating visualizations contact support@conduce.com.
