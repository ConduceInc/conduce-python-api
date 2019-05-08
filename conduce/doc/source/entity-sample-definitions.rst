.. _entity-sample-definitions:

======================
Example entity samples
======================

A sample represents an entity at a given point in time.  There are a few different ways to define an entity using the following fields:
 **id**
     a unique string that represents a specific object that exists.
 **kind**
     the type or category of the object.
 **time**
     a :py:class:`datetime.datetime` at which the entity state described by this sample is valid.

And one of the following location fields:
 **point**
     a coordinate pair that defines a location in a 2D cartisian coordinate system.
 **path**
     a list of coordinates that define a series of connected line segments in a 2D cartisian coordinate system.
 **polygon**
     a list of coordinates that define a closed shape in a 2D cartisian coordinate system.

These options provide the user with the means to define entities with three different spatial representations and convenient structures for defining geographic coordinates.

.. tip:: Entities that do not have a time component are considered infinite and exist across all time.  Excluding ``time`` from any of the following structures will produce an entity object (as opposed to a sample) that can be ingested with :py:func:`api.ingest_entities` rather than :py:func:`api.ingest_samples`.

++++++++++++++++++++
Locations
++++++++++++++++++++

Location fields are used to define where an entity exists and the entity's shape.

--------------------
Point sample
--------------------

A point sample defines an entity as a point in space.  Point samples are best used to represent entities in substrates other than the world map::

    {
        "id": 1,
        "kind": "ball",
        "time": datetime.datetime.now()
        "point": {
            "x": 571045,
            "y": 22131
        }
    }

------------------------
Geographic point sample
------------------------

A geopoint sample defines an entity at a point in space.  Coordinates are defined in latitude and longitude for convenience::

    {
        "id": 1,
        "kind": "truck",
        "time": datetime.datetime.now()
        "point": {
            "lon": -91.571045,
            "lat": 38.022131
        },
    }

A geographic sample may also be represented in x,y (x = longitude, y = latitude) notation::

    {
        "id": 1,
        "kind": "truck",
        "time": datetime.datetime.now()
        "point": {
            "x": -91.571045,
            "y": 38.022131
        },
    }

This same pattern follows for the other location types.  The geographic parameters provide a convenient way to specify latitude and longitude and avoid confusion with mapping to x and y.


--------------------
Path sample
--------------------

A path sample describes a connected sequence of points.  A path requires at least two points::

    {
        "id": 1,
        "kind": "trace",
        "time": datetime.datetime.now()
        "path": [{
            "x": 571045,
            "y": 22131
        },{
            "x": 571145,
            "y": 22231
        },{
            "x": 571245,
            "y": 22331
        }]
    }

-----------------------
Geographic path sample
-----------------------

A geographic path sample describes a connected sequence of points in geographic coordinates.  A path requires at least two points::

    {
        "id": 1,
        "kind": "road",
        "time": datetime.datetime.now()
        "path": [{
            "lon": -91.571045,
            "lat": 38.022131
        },{
            "lon": -91.571145,
            "lat": 38.022231
        },{
            "lon": -91.571245,
            "lat": 38.022331
        }]
    }


--------------------
Polygon sample
--------------------

A polygon sample describes a closed sequence of points.  A polygon requires at least three points.  The last point in the list is always connected to the first::

    {
        "id": 1,
        "kind": "trace",
        "time": datetime.datetime.now()
        "polygon": [{
            "x": 571045,
            "y": 22131
        },{
            "x": 571145,
            "y": 22231
        },{
            "x": 571245,
            "y": 22331
        },{
            "x": 571333,
            "y": 22431
        }]
    }

------------------------------
Geographic polygon sample
------------------------------

A geographic polygon sample describes a closed sequence of points in geographic coordinates.  Otherwise, it has the same requirements as a polygon sample::

    {
        "id": 1,
        "kind": "road",
        "time": datetime.datetime.now()
        "polygon": [{
            "lon": -91.571045,
            "lat": 38.022131
        },{
            "lon": -91.571145,
            "lat": 38.022231
        },{
            "lon": -91.571245,
            "lat": 38.022331
        },{
            "lon": -91.571345,
            "lat": 38.022431
        }]
    }


++++++++++++++++++++
Attributes
++++++++++++++++++++

Attributes are used to define characteristics of entities not encompassed by the four required fields.  Attributes may be strings or numbers and there is no limit to the number of attributes that are defined in an entity sample.  Attributes are added by simply extending the entity sample object with extra fields::

    {
        "id": 1,
        "kind": "ball",
        "time": dateutil.parser.parse(dateutil.parser.parse(2017-10-27T10:23:32+05:00)),
        "point": {
            "x": 571045,
            "y": 22131
        }
        "color": "red",
        "size": 5,
        "velocity": 12.4,
        "pressure": 12
    }

Here, we've extended the entity sample from the previous example with attributes that further define the entity.  Each attribute can be used to affect how an entity is rendered in Conduce.
