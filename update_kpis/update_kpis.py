import click
import yaml
import os
from couchdb import Server
from datetime import datetime
from kpigenerator import KPIGenerator, KPIDocument

script_dir = os.path.dirname(os.path.realpath(__file__))
with open (os.path.join(os.path.dirname(script_dir), 'version.txt')) as f:
    p_version = f.read()

@click.command()
@click.option("--couch_user", "-u", required=True)
@click.password_option(required=True)
@click.option("--couch_server", "-s", required=True)
def update_kpi(couch_user, password, couch_server):
    """
    Connect to StatusDB projects and flocell databases and 
    compute current KPIs to be added to a new document in the kpi database.
    This script should be run every hour, and it should have a yaml configuration 
    file in '$HOME/.dashbordrc' with program parameters:

        couch_user: foo_user

        password: bar_password

        couch_server: baz_couch.server:port
    """
    couch = Server("http://{}:{}@{}".format(couch_user, password, couch_server))
    if couch:
        projects_db = couch["projects"]
        worksets_db = couch["worksets"]
        kpi_db = couch["kpi"]
    else:
        raise IOError("Cannot connect to couchdb")

    p_summary = projects_db.view('project/summary')
    p_samples = projects_db.view('project/samples')
    p_dates = projects_db.view('project/summary_dates', group_level=1)
    w_name = worksets_db.view('worksets/name')
    kpis = KPIGenerator(p_summary, p_samples, p_dates, w_name)

    utc_time = "{}+0000".format(datetime.isoformat(datetime.utcnow()))
    limit_file = os.path.join(os.path.dirname(__file__), "config/limits.json")
    doc = KPIDocument(utc_time, limit_file)
    doc.version = p_version
    doc.projects = kpis.projects()
    doc.process_load = kpis.process_load()
    doc.turnaround_times = kpis.turnaround()
    doc.success_rate = kpis.success_rate()
    kpi_db.create(doc.__dict__)

if __name__ == '__main__':
    try:
        conf_file = os.path.join(os.environ.get('HOME'), '.dashboardrc')
        with open(conf_file, "r") as f:
            config = yaml.load(f)
    except IOError:
        click.secho("Could not open the config file {}".format(conf_file), fg="red")
        config = {}
    update_kpi(default_map=config)

