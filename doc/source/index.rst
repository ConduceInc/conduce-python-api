.. Conduce Python API documentation master file, created by
   sphinx-quickstart on Wed Aug 16 19:45:43 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   getting-started
   conduce-entities
   api-key-creation
   api-ref
   data-ingest


.. |wordmark| image:: /images/conduce_logo.svg
   :height: 100

=====================
Conduce Python API
=====================

-------------------
What's covered here
-------------------
Conduce is a data visualization platform designed to enable users to integrate data from disparate systems and present them for analysis and discovery. The Python API provides users with a mechanism to ingest data, construct visualization components called lenses, and display those lenses on a two-dimensional substrate, like a map or floor plan, within the Conduce environment. This document provides a detailed description of the Python API and provides examples of its use.

-----------
User Guides
-----------
These documents descibe how to start using the Conduce Python API.  They provide step-by-step instructions for installation and some of the most common API tasks.

++++++++++++++++++++++
:doc:`getting-started`
++++++++++++++++++++++
The :doc:`getting-started` guide helps users install the Python package and download the source code.  It also gives some explanation on how to use the command line utility.

+++++++++++++++++++++++
:doc:`api-key-creation`
+++++++++++++++++++++++
API users typically authenticate requests using API keys.  :doc:`api-key-creation` discusses Conduce authentication walks the user through the API key creation process.

+++++++++++++++++++++++
:doc:`conduce-entities`
+++++++++++++++++++++++
In order to build visualizations in Conduce, users must ingest data.  :doc:`conduce-entities` explains the concepts behind Conduce entities, how to build data structures for ingestion and how to make API calls to ingest those structures.

------------
Details
------------

+++++++++++++++++++++++
:doc:`api-ref`
+++++++++++++++++++++++
The :doc:`api-ref` provides detailed specifications of API functions and their arguments.

++++++++++++++++++++++++++++++++
:doc:`entity-sample-definitions`
++++++++++++++++++++++++++++++++
:doc:`api-ref` demonstrate how to construct Conduce entity sample structures for various data types.
