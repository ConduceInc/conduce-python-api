.. _conduce-entities:

.. toctree::
    :hidden:

    entity-sample-definitions

================
Conduce Entities
================

.. note:: WIP

Conduce uses a concept called entity to define objects that exist in space and time.  An entity can exist for an instant or across a time span.  It can describe a point in space, a path (sequence of points), or a region (polygon).  An entity is defined by a series of samples that describe it's location in space over a period of time.  An entity also has attributes that describe it's characteristics. An entity's attributes can change over time.

-----------------
Creating entities
-----------------

An entity is a series of samples that describe the state of and object over a period of time.  A sample is the representation of an entity's momentary state.  Samples are created from user data.  User data should describe people or things that exist in some location during some time span.  Data can be ingested from static files with thousands of records or real-time streams that provide state updates in real-time.  As an example we'll ingest the following real-time shipment data into an existing dataset named ``shipments``:

.. list-table:: Source data: real-time shipment status
   :header-rows: 1
   :widths: auto

   * - ID
     - Method
     - Date
     - Latitude
     - Longitude
     - Value
     - Status 
   * - 1
     - ground
     - 2017-10-24T10:22:09+00:00
     - 37.952861
     - -91.922607
     - $102,325.26
     - transit
   * - 2
     - air
     - 2017-10-24T10:22:11+00:00
     - 38.289937
     - -100.107422
     - $3,216,757.84
     - transit
   * - 3
     - ground
     - 2017-10-24T10:22:08+00:00
     - 40.354917
     - -89.104614
     - $204,694.41
     - processing
   * - 4
     - air
     - 2017-10-24T10:22:06+00:00
     - 35.85344
     - -115.993652
     - $102,325.26
     - transit
   * - 5
     - freight
     - 2017-10-24T10:22:18+00:00
     - 25.029996
     - -134.318848
     - $1,431,873,345.01
     - transit

The data in this table represents the present location of 5 shipments.  Each shipment has an ID, a shipping method, a date when it was last updated and a location in geographic coordinates.  Additionally the current state and value of the shipment is documented.  A Conduce entity is able to capture and represent all of this information.  These data records will be ingested as the first samples of 5 unique entities of the ``shipments`` dataset.

An entity sample requires four fields:
 **id**
     a unique string that identifies the entity described by this sample.
 **kind**
     the type or category of the object.
 **time**
     A :py:class:`datetime.datetime` at which the entity state described by this sample is valid.

And one of:
 **point**
     A coordinate pair that defines a location in a 2D cartisian coordinate system.
 **path**
     A list of coordinates that define a series of connected line segments in a 2D cartisian coordinate system.
 **polygon**
     A list of coordinates that define a closed shape in a 2D cartisian coordinate system.

Each can be specified in (x,y) or (latitude,longitude).  If coordinate types are mixed or multiple coordinate types are specified, a :py:func:`KeyError` will be raised.  If more than one location type is defined, a :py:func:`KeyError` will be raised.

Optionally, a Conduce entity may contain an arbitrary list of attributes.  These may be strings, integers, or floating point numbers.

A source data record maps to a sample as follows::

    {
        "id": <ID>,
        "kind": <Method>,
        "time": <Date> (converted to a datetime object)
        "point": {
            "lat": <Longitude>,
            "lon": <Latitude>
        },
        "Value": <Value>,
        "Status": <Status>
    }

Example (first record in table)::

    {
        "id": 1,
        "kind": "ground",
        "time": dateutil.parser.parse('2017-10-24T10:22:09+00:00'),
        "point": {
            "lon": -91.571045,
            "lat": 38.022131
        },
        "Value": 102325.26,
        "Status": "delivered" 
    }

In the example above the ISO-8601 date time string is converted to a :py:class:`datetime.datetime` using :py:func:`dateutil.parser.parse`.

More :ref:`example sample definitions <entity-sample-definitions>`

------------------
Ingesting entities
------------------

In order to ingest our source data we must first convert each record into an entity sample as described above.  Once converted, the samples are added to a list.  The list may contain samples for multiple entities.  Once we have created our sample list we call :py:func:`api.ingest_samples`::

    conduce.api.ingest_samples(dataset_id, sample_list, host=app.conduce.com, api-key=00000000-0000-0000-0000-000000000000)

This function takes a dataset ID as the first argument.  A dataset must exist before samples can be ingested.  See :py:func:`api.create_dataset` for more information on how to create a dataset.

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

-----------
Particulars
-----------

+ The kind of an entity may change.
+ Conduce will not allow an entity to exist in two different states at the same time.  That is to say that two samples describing the same entity cannot have the same timestamp. 
