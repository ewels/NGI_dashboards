#!/usr/bin/env python

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

from __future__ import print_function

import click
import couchdb
from datetime import datetime
from distutils.dir_util import copy_tree
import logging
import jinja2
import json
import os
import yaml

# Command line options
@click.command( context_settings = dict( help_option_names = ['-h', '--help'] ))
@click.option('--couch_user', '-u', required=True)
@click.password_option(required=True)
@click.option('--couch_server', '-s', required=True)
@click.option('--outdir', '-o', required=True, help = "Create dashboards in the specified output directory.")
@click.version_option('0.1')
def make_dashboards(outdir, couch_user, password, couch_server):
   """
   Function to get data from KPI database and render dashboard HTML files.
   """

   ### CONFIGURATION VARS
   templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
   outdir = os.path.realpath(outdir)
   # Paths relative to make_dashboards/templates/
   internal_fn = os.path.join('internal','index.html')
   external_fn = os.path.join('external','index.html')
   
   
   ### GET THE DATA
   
   # Connect to the database
   couch = couchdb.Server("http://{}:{}@{}".format(couch_user, password, couch_server))
   data = couch["kpi"].view('dashboard/by_time', limit=1, descending=True).rows[0].value
   data['date_rendered'] = datetime.now().strftime("%Y-%m-%d, %H:%M")
   data['date_generated'] = datetime.strptime(data['time_created'], "%Y-%m-%dT%H:%M:%S.%f+0000").strftime("%Y-%m-%d, %H:%M")
   data['json'] = json.dumps(data, indent=4)

   ### RENDER THE TEMPLATES
   
   # Copy across the templates - needed so that associated assets are there
   copy_tree(templates_dir, outdir)
   
   # Load the templates
   try:
      env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
      internal_template = env.get_template(internal_fn)
      external_template = env.get_template(external_fn)
   except:
      raise IOError ("Could not load dashboard template files")
   
   # Render templates and save
   internal_output_fn = os.path.join(outdir, internal_fn)
   external_output_fn = os.path.join(outdir, external_fn)
   
   # Internal template
   internal_output = internal_template.render(d = data)
   try:
      with open (os.path.join(outdir, internal_output_fn), 'w') as f:
         print(internal_output, file=f)
   except IOError as e:
      raise IOError ("Could not print report to '{}' - {}".format(internal_output_fn, IOError(e)))
   
   # Internal template
   external_output = external_template.render(d = data)
   try:
      with open (os.path.join(outdir, external_output_fn), 'w') as f:
         print(external_output, file=f)
   except IOError as e:
      raise IOError ("Could not print report to '{}' - {}".format(external_output_fn, IOError(e)))



if __name__ == '__main__':
   try:
      conf_file = os.path.join(os.environ.get('HOME'), '.dashboardrc')
      with open(conf_file, "r") as f:
         config = yaml.load(f)
   except IOError:
      click.secho("Could not open the config file {}".format(conf_file), fg="red")
      config = {}
   make_dashboards(default_map=config)
    
    
