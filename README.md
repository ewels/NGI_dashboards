# NGI Dashboards

This code is for use in monitoring key performance indicators (KPIs)
at the SciLifeLab National Genomics Infrastructure in Stockholm, Sweden.

### Method Outline

1. A script polls `statusdb` for a range of KPI statistics.
   These are logged to the innovatively titled `kpi` database
   within `statusdb`.
   * The script runs on a cronjob, once per hour.
   * It can be run from anywhere with access to statusdb, but
     this will typically be on the `tools` server.
   * Genomics Status can also access this data for plotting.
2. A second script pulls information from the `kpi` database
   and uses it to parse some templates using the `jinja2` package.
   * At the time of writing, there are three templates - one for the
     internal dashboard, one for the external dashboard, and a HTML
     chunk to be displayed on the external website.
   * This script will also be run on a cron job, scheduled to run
     a few minutes after the one described above.
3. The dashboards work with raspberry PIs. These have a copy of
   Firefox running which will poll the apache server on `tools`.
   This will serve up the static HTML file generated in step 2.

### Updating KPI Targets
The KPI targets are stored in a config file held in this repository.
To change them, fork the repository and change the file. Submit a
pull request and merge the changes. Then pull these changes to `tools`.

### Contact
This code was developed by Phil Ewels (@ewels) and
Remi-Andre Olsen (@remiolsen). 
Feel free to get in touch if you have any queries.