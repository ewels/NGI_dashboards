#!/usr/bin/env python

"""
Script to get data from KPI database and render dashboard HTML files.
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

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] [%(asctime)s]: %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

# Get package version
script_dir = os.path.dirname(os.path.realpath(__file__))
with open (os.path.join(os.path.dirname(script_dir), 'version.txt')) as f:
    p_version = f.read()

# Command line options
@click.command( context_settings = dict( help_option_names = ['-h', '--help'] ))
@click.option('--couch_user', '-u', required=True)
@click.password_option(required=True)
@click.option('--couch_server', '-s', required=True)
@click.option('--outdir', '-o', required=True, help = "Create dashboards in the specified output directory.")
@click.option('--demo', is_flag=True)
@click.version_option(p_version)
def make_dashboards(outdir, demo, couch_user, password, couch_server):
    """
    Function to get data from KPI database and render dashboard HTML files.
    """

    ### CONFIGURATION VARS
    templates_dir = os.path.join(script_dir, 'templates')
    outdir = os.path.realpath(outdir)
    logging.info("Making reports in {}".format(outdir))
    # Paths relative to make_dashboards/templates/
    internal_fn = os.path.join('internal','index.html')
    external_fn = os.path.join('external','index.html')
    
    
    ### GET THE DATA
    if demo:
        logging.warn("Using demo data")
        with open (os.path.join(script_dir, 'demo_data.json')) as f:
            data = json.loads(f.read())
    else:
        # Connect to the database
        couch = couchdb.Server("http://{}:{}@{}".format(couch_user, password, couch_server))
        data = couch["kpi"].view('dashboard/by_time', limit=1, descending=True).rows[0].value
    try:
        data['date_generated'] = datetime.strptime(data['time_created'], "%Y-%m-%dT%H:%M:%S.%f+0000").strftime("%Y-%m-%d, %H:%M")
    except KeyError:
        data['date_generated'] = 'Error'
    data['date_rendered'] = datetime.now().strftime("%Y-%m-%d, %H:%M")
    data['p_version'] = p_version
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
     
     
