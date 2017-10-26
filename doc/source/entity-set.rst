.. _entity-set:

We should update Conduce to allow us to use entities in this way instead :ref:`conduce-entities`

================
Conduce Entities
================

.. note:: WIP

Conduce uses a concept called entity to define an object that exists in space and time.  An entity can exist for an instant or across a time span.  It can describe a point in space, a path (sequence of points), or a region (polygon).  An entity is defined by it's location in space and time and a unique identifier.  An entity also has attributes that describe it's characteristics. The attributes of an entity can change over time.

-----------------
Creating entities
-----------------

Entities are created from user data.  The data should describe people or things that exist in some location during some time span.  Data can be ingested from static files with thousands of records or streams that provide state updates in realtime.  As an example we'll start with the following realtime shipment data:

.. list-table:: Source data: realtime shipment updates
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

The data in this table represents the present location of 5 shipments.  Each shipment has an ID, a shipping method, a date when it was last updated and a location in geographic coordinates.  Additionally the current state and value of the shipment is documented.  A Conduce entity is able to capture and represent all of this information. 

A Conduce entity requires several fields:
 **identity**
     a unique string that represents a specific object that exists.
 **kind**
     the type or category of the object.
 **timestamp_ms**
     the time at which the data describing the entity (state) is valid.  Alternatively, the time at which the entity enters the state described by the other fields.
 **endtime_ms**
     the time at which the state is no longer valid.  For sample data (data that defines an entity's state at an instant in time), the endtime_ms and timestamp_ms fields should be set to the same value.
 **path**
     one or more points (point, path, or polygon) that describe the space occupied by the entity

Optionally, a Conduce entity may contain an arbitrary list of attributes.  These may be strings, integers, or floating point numbers.

A source data record maps to an entity as follows::

    {
        "identity": <ID>
        "kind": <Method>
        "timestamp_ms": <Date> (converted to an integer milliseconds since epoch, 1970-Jan-01)
        "endtime_ms": <Date> (converted to an integer milliseconds since epoch, 1970-Jan-01)
        "path": [{
            "x": <Longitude>
            "y": <Latitude>
            "z": 0
        }]
        "attrs": [{
            "key": "Value",
            "type": "DOUBLE"
            "number_value": <Value>            
        },{
            "key": "State",
            "type": "STRING"
            "string_value": <State>            
        }]
    }

Example (first record in table)::

    {
        "identity": 1 
        "kind": "ground"
        "timestamp_ms": 1508840529000
        "endtime_ms": 1508840529000
        "path": [{
            "x": -91.571045 
            "y": 38.022131
            "z": 0
        }]
        "attrs": [{
            "key": "Value",
            "type": "DOUBLE"
            "number_value": 102325.26 
        },{
            "key": "State",
            "type": "STRING"
            "string_value": "delivered" 
        }]
    }

In the example above you see that the ISO-8601 date time strings were converted to an integer.  This integer represents the number of milliseconds that have accumulated since epoch (``1970-01-01T00:00:00+00:00``)

------------------
Ingesting entities
------------------

In order to ingest our source data we must first convert each record into a Conduce entity as described above.  Once converted, the entities are added to a list.  That list is then set to the value of key/value pair.  The resulting object is referred to as an entity set.  An entity set is a key/value pair that holds a list of entities::

    entity_set = { "entities": [ entity1, entity2, ...] }

Once we have created our entity set we call :py:func:`api.ingest_entities`::

    ingest_entities(dataset_id, entity_set, host=app.conduce.com, api-key=00000000-0000-0000-0000-000000000000)

This function takes a dataset ID as the first argument.  A dataset must exist before entities can be ingested into it.  See :py:func:`api.create_dataset` for more information on how to create a dataset.

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

-----------------
Modifying records
-----------------

Stuff about modifying existing records (modify API)

-----------
Particulars
-----------

The kind of an entity may change.
Conduce will not allow an entity to exist in two different states at the same time.  That is to say the duration defined by one entity record may not overlap with the duration defined by another.
``endtime_ms`` must be greater than or equal to ``timestamp_ms``.

---------------
More about time
---------------

Conduce entities have two time fields.  These fields define moment when an entity enters a state, and the last moment the entity was known to be in the state the entity record defines.  The way these fields are used depends in part on the nature of the data.

Realtime typically defines the state of an entity periodically (once per second), or in an event-driven way (when the entity changes state).  In either of these cases each data point only describes the entity's state at an instant in time.  In our example, each shipment is in transit.  So the location values for each record are only valid at the moment in time when the sample was recorded.  At any other moment, the shipment is in a different location, so it would be incorrect to set timestamp_ms and endtime_ms to different values.  In these cases, timestamp_ms and endtime_ms should be set to the same value.

Static or historic data usually contains several data records.  In these cases it is possible that each record is not an instantaneous state, but rather, a duration over which an entity was in a given state.  This type of data tends to describe stationary objects that exist for finite durations.  For instance, a house was build in 1900 and demolished in 2005.  Then in 2007 a park was constructed that still exists.  Rather than creating entity records for the construction and demolition of the house, the user could create a single entity with a start time of 1900 and a 2005 end time. 
