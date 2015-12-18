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
       "sequencing_queue": 8,
       "sequencing": 32,
       "bioinformatics_queue": 32,
       "bioinformatics": 50
   },
   "turnaround_times": {
       "initial_qc": 5,
       "library_prep": 21,
       "sequencing": 14,
       "bioinformatics": 7
   },
   "success_rate": {
       "initial_qc": 0.75,
       "library_prep": 0.87,
       "sequencing": 0.95,
       "bioinformatics": 0.69
   },
   "projects": {
       "finished_libraries": 12,
       "library_prep": 33,
       "in_production": 160,
       "in_applications": 11,
       "opened_n_weeks_ago": {
           "0": 5,
           "1": 6,
           "2": 1,
           "3": 2
       },
       "closed_n_weeks_ago": {
           "0": 10,
           "1": 2,
           "2": 3,
           "3": 3
       },
       "opened_last_7_days": 8,
       "closed_last_7_days": 10
   },
   "limits": {
       "process_load": {
           "initial_qc_samples": 200,
           "initial_qc_lanes": 80,
           "library_prep_samples": 200,
           "sequencing_lanes": 80,
           "bioinformatics_lanes": 80
       },
       "turnaround_times": {
           "initial_qc_days": 14,
           "library_prep_days": 19,
           "sequencing_days": 13,
           "bioinformatics_days": 10
       }
   }
}

"""

doc = kpi_db.view('dashboard/by_time', limit=1, descending=True).rows[0].value