#!/bin/python
"""
Script to get data from KPI database and render dashboard HTML files.

Typical data from database:

{
   "time_created": "2016-01-14T07:55:57.799364+0000",
   "process_load": {
       "initial_qc": 188,
       "library_prep_queue": 20,
       "library_prep": 89,
       "sequencing_queue": 2,
       "sequencing": 8
   },
   "turnaround_times": {
       "initial_qc": 5,
       "library_prep": 21,
       "sequencing": 14
   },
   "success_rate": {
       "initial_qc": 0.75,
       "library_prep": 0.87,
       "sequencing": 0.95
   }
}

"""

doc = kpi_db.view('dashboard/by_time', limit=1, descending=True).rows[0].value