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
     The moment at which the entity state described by this sample is valid.

And one of the following location fields:
 **point**
     A coordinate pair that defines a location in a 2D cartisian coordinate system.
 **path**
     A list of coordinates that define a series of connected line segments in a 2D cartisian coordinate system.
 **polygon**
     A list of coordinates that define a closed shape in a 2D cartisian coordinate system.
 **geopoint**
     A latitude and longitude (decimal degrees) that define the location at which the entity exists.
 **geopath**
     A list of geographical coordinates that define a series of connected line segments.
 **geopolygon**
     A list of geographical coordinates that define closed shape.

These options provide the user with the means to define entities with three different spatial representations and convenient structures for defining geographic coordinates.

++++++++++++++++++++
Locations
++++++++++++++++++++

Location fields are used to define where an entity exists and the entity's shape.

--------------------
Point sample
--------------------

A point sample defines an entity as a point in space.  Point samples are best used to represent entities in substrates other than the world map.::

    {
        "id": 1,
        "kind": "ball",
        "time": 1508840529000,
        "point": {
            "x": 571045,
            "y": 22131
        }
    }

--------------------
GeoPoint sample
--------------------

A geopoint sample defines an entity at a point in space.  Coordinates are defined in latitude and longitude for convenience.::

    {
        "id": 1,
        "kind": "truck",
        "time": 1508840529000,
        "geopoint": {
            "lon": -91.571045,
            "lat": 38.022131
        },
    }

A geographic sample could also be represented with a point sample.::

    {
        "id": 1,
        "kind": "truck",
        "time": 1508840529000,
        "point": {
            "x": -91.571045,
            "y": 38.022131
        },
    }

This same pattern follows for the other location types.  The "geo" types provide a convenient way to specify latitude and longitude.


--------------------
Path sample
--------------------

A path sample describes a connected sequence of points.  A path requires at least two points.::

    {
        "id": 1,
        "kind": "trace",
        "time": 1508840529000,
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

--------------------
GeoPath sample
--------------------

A geographic path sample describes a connected sequence of points in geographic coordinates.  A path requires at least two points.::

    {
        "id": 1,
        "kind": "road",
        "time": 1508840529000,
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

A polygon sample describes a closed sequence of points.  A polygon requires at least three points.  The last point in the list is implicitly connected to the first.::

    {
        "id": 1,
        "kind": "trace",
        "time": 1508840529000,
        "path": [{
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

--------------------
GeoPolygon sample
--------------------

A geographic polygon sample describes a closed sequence of points in geographic coordinates.  Otherwise it has the same requirements as a polygon sample.::

    {
        "id": 1,
        "kind": "road",
        "time": 1508840529000,
        "path": [{
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
        "time": 1508840529000,
        "point": {
            "x": 571045,
            "y": 22131
        }
        "color": "red",
        "size": 5,
        "velocity": 12.4,
        "pressure": 12
    }

Here we've extended the entity sample from the previous example with attributes that further define the entity.  Each attribute can be used to affect how an entity is rendered in Conduce.
