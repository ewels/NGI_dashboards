import numpy as np
import json
import re
from genologics.entities import *
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
lims = Lims(BASEURI, USERNAME, PASSWORD)
from datetime import datetime, timedelta

class KPIGenerator(object):

    def __init__(self, project_summary, project_samples, project_dates, worksets_name):
        #TODO: reduce these three views to a single dictionary
        self.project_summary = project_summary
        self.project_samples = project_samples
        self.project_dates = project_dates
        self.worksets_name = worksets_name

    def process_load(self, start="2014-07-01"):
        pldict = {
                "initial_qc_samples": 0,
                "initial_qc_lanes": 0,
                "library_prep_queue": 0,
                "library_prep": 0,
                "sequencing": 0
        }
        sample_ongoing = {} #samples either in queue or ongoing

        # projectsDB
        for project in self.project_summary:
            key = project["key"]
            value = project["value"] 
            details = value.get("details", {})
            aborted = details.get("aborted")

            if "open_date" in value.keys() and aborted is None and "close_date" not in value.keys():
                open_date = datetime.strptime(value.get("open_date"), "%Y-%m-%d")
                ptype = details.get("type", "")
                try:
                    queued = details["queued"]
                except KeyError:
                    queued = value.get("project_summary", {}).get("queued")
                samples = self.project_samples[key[1]]
                if not len(samples.rows) == 1:
                    continue
                samples = samples.rows[0]

                # Initial QC
                if ptype == "Production" and queued is None:
                    if details.get("sample_type") == "Finished Library": 
                        try: 
                            pldict["initial_qc_lanes"] += details.get("sequence_units_ordered_(lanes)")
                        except TypeError:
                            pass #TODO maybe log. But there are some "special" projects with no lanes ordered
                    else: 
                        try:
                            pldict["initial_qc_samples"] += value.get("no_samples")
                        except TypeError:
                            pldict["initial_qc_samples"] += details.get("sample_units_ordered", 0)

                # Library prep
                elif ptype == "Production" and queued is not None and not details.get("sample_type") == "Finished Library":
                    for sample_key, sample in samples.value.items():
                        details = sample.get("details", {})
                        if details.get("status_(manual)") == "In Progress":
                            # This is probably queued for prep
                            if "library_prep" not in sample.keys():
                                sample_ongoing[sample_key] = False
                            # The latest library prep failed and its probably ongoing
                            # TODO: Replace with library pooling information when available
                            else:
                                prep_re = re.compile('^[A-Z]$')
                                preps = sorted([m for m in sample["library_prep"].keys() if prep_re.match(m)])
                                if sample["library_prep"][preps[-1]].get("prep_status") == "FAILED":
                                    sample_ongoing[sample_key] = True

        # WorksetsDB
        for ws_doc in self.worksets_name:
            ws = ws_doc.get("value")
            for k, project in ws.get("projects",{}).items(): #TODO could make a view in worksetDB to do this
                for sample in project.get("samples",{}).keys():
                    if sample in sample_ongoing.keys():
                        # Sample has been sequenced
                        if len(project["samples"][sample].get("sequencing", {})) > 0:
                            sample_ongoing.pop(sample, None)
                        # It has a prep in worksetDB, which might not be present in projectDB
                        else:
                            sample_ongoing[sample] = True

        for k, ongoing in sorted(sample_ongoing.items(), key=lambda x: x[0]):
            if ongoing:
                pldict["library_prep"] += 1
            else:
                pldict["library_prep_queue"] += 1

        # Sequencing (Thanks @Galithil)
        # TODO move LIMS connection specific code to script
        weekAgo = datetime.now() - timedelta(days=7)
        process_types = ["Illumina Sequencing (Illumina SBS) 4.0",
                "MiSeq Run (MiSeq) 4.0",
                "Illumina Sequencing (HiSeq X) 1.0"]
        seq = lims.get_processes(type=process_types, 
            last_modified=weekAgo.strftime("%Y-%m-%dT00:00:00Z"))

        for pro in seq:
            if not "Finish Date" in pro.udf or not pro.udf['Finish Date']:
                pldict["sequencing"] += len(pro.all_inputs())
        return pldict


    def turnaround(self, max_days=30):
        qc_list = []
        libprep_list = []
        seq_list = []
        prep_projs = []
        finlib_projs = []

        start_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(max_days)

        for project in self.project_summary:
            proj_key = project["key"][1]
            value = project["value"]
            details = value.get("details", {})
            open_date = value.get("open_date")
            try:
                queued = details["queued"]
            except KeyError:
                queued = value.get("project_summary", {}).get("queued")
            close_date = value.get("close_date")
            aborted = details.get("aborted")
            sample_type = details.get("sample_type")
            if details.get("type") == "Production" and aborted is None:

                try:
                    proj_dates = self.project_dates[[proj_key]].rows[0]["value"]
                except:
                    proj_dates = {}
                seq_date = proj_dates.get("sequencing_start_date")
                prep_date = proj_dates.get("library_prep_start")
                prep_finished = proj_dates.get("qc_library_finished")

                # Projects TaT
                try:
                    proj_end = datetime.strptime(close_date, "%Y-%m-%d")
                    if proj_end > start_date: 
                        if sample_type == "Finished Library":
                            seq_start = datetime.strptime(seq_date, "%Y-%m-%d")
                            finlib_days = (proj_end - seq_start).days
                            finlib_projs.append(finlib_days)
                        else:
                            prep_start = datetime.strptime(prep_date, "%Y-%m-%d")
                            proj_days = (proj_end - prep_start).days
                            prep_projs.append(proj_days)
                except TypeError:
                    pass
                
                # Library prep TaT
                try:
                    prep_start = datetime.strptime(prep_date, "%Y-%m-%d")
                    prep_end = datetime.strptime(prep_finished, "%Y-%m-%d")
                    prep_days = (prep_end - prep_start).days
                    if prep_end > start_date and prep_days >= 0:
                        libprep_list.append(prep_days)
                except TypeError:
                    pass

                # Intial QC TaT
                try:
                    qc_start = datetime.strptime(open_date, "%Y-%m-%d")
                    qc_end = datetime.strptime(queued, "%Y-%m-%d")
                    qc_days = (qc_end - qc_start).days
                    if qc_end > start_date and qc_days >= 0:
                        qc_list.append(qc_days)
                except TypeError:
                    pass

        return({
            "library_prep": self._get_percentile(libprep_list, 90),
            "initial_qc": self._get_percentile(qc_list, 90),
            "finished_library_project": self._get_percentile(finlib_projs, 90),
            "library_prep_project": self._get_percentile(prep_projs, 90)
        })


    def _get_percentile(self, vector, percentile):
        if len(vector) > 0:
            pct = np.percentile(np.array(vector), percentile)
            return round(pct, 2)
        else:
            return None


    def projects(self, max_weeks=4):
        projdict = {
                "finished_libraries": 0, 
                "library_prep": 0, 
                "in_production": 0, 
                "in_applications": 0,
                "opened_last_7_days": 0,
                "closed_last_7_days": 0,
                "opened_n_weeks_ago": {key: 0 for key in range(0,max_weeks)},
                "closed_n_weeks_ago": {key: 0 for key in range(0,max_weeks)}
        }

        dnow = datetime.now()
        dweekend = datetime.strptime("{0}-{1}-0".format(*dnow.isocalendar()),"%Y-%W-%w")
        for project in self.project_summary:
            key = project["key"]
            value = project["value"]
            details = value.get("details", {})
            if "open_date" in value.keys() and "close_date" not in value.keys() and "aborted" not in details.keys():
                #open project types
                ptype = details.get("type", "")
                if ptype == "Production":
                    projdict["in_production"] += 1
                elif ptype == "Application":
                    projdict["in_applications"] += 1
                if details.get("sample_type") == "Finished Library":
                    projdict["finished_libraries"] += 1
                else:
                    projdict["library_prep"] += 1

                #opened project stats
                open_value = value.get("open_date", "2001-01-01")
                open_date = datetime.strptime(open_value, "%Y-%m-%d")
                d_weeks = (dweekend - open_date).days / 7
                if d_weeks < max_weeks:
                    projdict["opened_n_weeks_ago"][d_weeks] += 1
                if (dnow - open_date).days < 7:
                    projdict["opened_last_7_days"] += 1
            elif "open_date" in value.keys() and "close_date" in value.keys() and "aborted" not in details.keys():
                #closed project stats
                close_value = value.get("close_date", "2001-01-01")
                close_date = datetime.strptime(close_value, "%Y-%m-%d")
                d_weeks = (dweekend - close_date).days / 7
                if d_weeks < max_weeks:
                    projdict["closed_n_weeks_ago"][d_weeks] += 1
                if (dnow - close_date).days < 7:
                    projdict["closed_last_7_days"] += 1

        return projdict

    def success_rate(self, max_days=30):
        start_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(max_days)

        initial_qc_fails = 0
        prep_started = 0
        prep_finished = 0
        prep_passed = 0


        for ws_doc in self.worksets_name:
            ws = ws_doc.get("value")
            ws_start = ws.get("date_run")
            last_agg = ws.get("last_aggregate")

            if ws_start is not None:
                ws_start = datetime.strptime(ws_start, "%Y-%m-%d")
            else:
                continue

            if last_agg is not None:
                last_agg = datetime.strptime(last_agg, "%Y-%m-%d")

            for proj in ws.get("projects", {}).keys():
                for s_key, sample in ws["projects"][proj].get("samples", {}).items():
                    rec_ctrl = sample.get("rec_ctrl", {}).get("status")
                    if rec_ctrl is not None and ws_start > start_date:
                        prep_started += 1.0
                        if rec_ctrl == "FAILED":
                            initial_qc_fails += 1.0
                    prep_status = sample.get("library_status")
                    if prep_status is not None and prep_status != "UNKNOWN" and last_agg is not None and last_agg > start_date:
                        prep_finished += 1.0
                        if prep_status == "PASSED":
                            prep_passed += 1.0

        return({
            "initial_qc": round(1 - (initial_qc_fails / prep_started), 2),
            "library_prep": round(prep_passed / prep_finished, 2)
        })

            

class KPIDocument(object):
    """
    Defines the document of the KPI database in statusDB
    Use KPIDocument.__dict__ to get a dict ready made for couchdb,
    but make sure that it's JSON serializable first ;)
    """
    def __init__(self, time_created, limit_file):
        self.time_created = time_created
        with open(limit_file, "rU") as f: 
            self.limits = json.load(f)
        self.process_load = {}
        self.projects = {}
        self.success_rate = {}
        self.turnaround_times = {}
        self.version = None

