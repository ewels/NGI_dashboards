Kpiupdater
==========

This is the module that processes the information found in StatusDB to generate the KPIs of the internal dashboard.


The iterator
------------

Most of the KPIs are are generated from StatusDB by stringing together various views from various databases into a pseudo document. This pseudo document is implemented a a python iterator. 

.. automodule:: kpiupdater
   :members: ProjectViewsIter

KPI objects 
-----------

The KPIs are python objects. They are called every time to update it's internal state. After iterating through the documents, a `summary()` is issued to generate the final statistic.

.. autoclass:: kpiupdater.kpi.KPIBase
   :members: __init__, __call__, summary

.. automodule:: kpiupdater.kpi
   :members:


LIMS KPIs
---------

There are a few KPIs which are fetched directly from the LIMS using the genologics python API.

.. automodule:: kpiupdater
   :members: sequencing_success, sequencing_load

