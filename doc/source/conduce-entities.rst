.. _conduce-entities:


================
Conduce Entities
================


------------------
What is an entity?
------------------

Conduce uses a concept called entity to define a person, place, or thing that exists in space and time. An entity can exist for an instant or across a span of time. It can describe a point in space, a path (sequence of points), or a region (polygon). An entity also has attributes that describe its characteristics. An entity’s location and attributes can change over time. When an entity changes over time it is said to be dynamic.  If it does not change, it is considered static.  To understand when to use each type, it is helpful to understand dynamic entities first.

++++++++++++++++
Dynamic entities
++++++++++++++++
Dynamic entities are composed of a sequence of samples.  The term sample is taken from the `signal processing domain <https://en.wikipedia.org/wiki/Sampling_(signal_processing)>`_ and describes the state of an entity at a discrete moment in time.  A sample describes an entity's location and other attributes.  Attributes can change from sample to sample so that when a visualization is constructed, these state changes can be visualized.  A sequence of samples that share the same ID define the entity, and so, an entity is a sequence of samples.  Entities defined this way are said to be `dynamic`.  Conduce does not require that an entity's sampling interval be regular.  This allows users to update entities based on events (state changes) rather than period (time changes).  However, note that some types of entities should be sampled regularly in order to generate an accurate visual representation.

+++++++++++++++
Static entities
+++++++++++++++
A static entity is one that does not change over time.  If an entity has a state that does not change, it may be ingested with a single message that does not have a time field.  As such, the entity is a sequence with one element that defines the entity for all time.  Entities defined by a single state are considered `static`.  This document focuses on dynamic entities.  However, the same basic principles apply for ingesting static entities, with the exception that static entities do not have ``time`` fields and, because the entity exists across all time, only one instance of the entity can exist in the dataset.  See :doc:`data-ingest` for an example of ingesting static entities.

-----------------
Creating entities
-----------------

A dynamic entity is created by defining a series of samples that describe the state of an object over a period of time. Each sample is the representation of an entity's momentary state.  Samples are created from user data.  User data should describe people or things that exist in some location during some time span.  Data can be ingested from static files with thousands of records or real-time streams that provide state updates in real-time.  As an example we'll ingest the following real-time shipment data into an existing dataset named ``shipments``:

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

The data in this table represents the present location of 5 shipments.  Each shipment has an ID, a shipping method, a date when it was last updated and a location in geographic coordinates.  Additionally, the current state and value of the shipment is documented.  A Conduce entity is able to capture and represent all of this information.  These data records will be ingested as the first samples of 5 unique entities of the ``shipments`` dataset.

An entity sample requires four fields:
 **id**
     a unique string that identifies the entity described by this sample.
 **kind**
     the type or category of the object.
 **time**
     a :py:class:`datetime.datetime` at which the entity state described by this sample is valid.

And one of:
 **point**
     a coordinate pair that defines a location in a 2D Cartesian coordinate system.
 **path**
     a list of coordinates that define a series of connected line segments in a 2D Cartesian coordinate system.
 **polygon**
     a list of coordinates that define a closed shape in a 2D Cartesian coordinate system.

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

In the example above the ISO-8601 datetime string is converted to a :py:class:`datetime.datetime` using :py:func:`dateutil.parser.parse`.

More :ref:`example sample definitions <entity-sample-definitions>`

------------------
Ingesting entities
------------------

In order to ingest our source data we must first convert each record into an entity sample as described above.  Once converted, the samples are added to a list.  The list may contain samples for multiple entities.  Once we have created our sample list we call :py:func:`api.ingest_samples`::

    conduce.api.ingest_samples(dataset_id, 
        sample_list, host=app.conduce.com,
        api-key=00000000-0000-0000-0000-000000000000)

This function takes a dataset ID as the first argument.  A dataset must exist before samples can be ingested.  See :py:func:`api.create_dataset` for more information on how to create a dataset.

-----------------
Updating entities
-----------------

When the state of an entity changes the updates need to be ingested by Conduce to be visualized.

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

In the table above, ID 1 has changed location and its state has been updated to "delivered."  To update the entity follow the same process used to ingest the initial sample.  Convert the data to a sample and call :py:func:`api.ingest_samples`.

-----------
Particulars
-----------

+ The **kind** of an entity may change.
+ Conduce will not allow an entity to exist in two different states at the same time.  That is to say that two samples describing the same entity cannot have the same timestamp.
+ A dataset should contain only static or dynamic entities, not both  

