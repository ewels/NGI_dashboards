from datetime import datetime
import json
import re

class KPIGenerator(object):

    def __init__(self, project_summary, project_samples, worksets_name):
        self.project_summary = project_summary
        self.project_samples = project_samples
        self.worksets_name = worksets_name

    def process_load(self, start="2014-07-01"):
        pldict = {
                "initial_qc_samples": 0,
                "initial_qc_lanes": 0,
                "library_prep_queue": 0,
                "library_prep": 0
                #"sequencing_queue": 0,
                #"sequencing": 0,
                #"bioinformatics": 0,
                #"bioinformatics_queue": 0
        }
        sample_ongoing = {} #samples either in queue or ongoing
        start_date = datetime.strptime(start, "%Y-%m-%d")

        # projectsDB
        for project in self.project_summary:
            key = project["key"]
            value = project["value"]
            open_date = datetime.strptime(value.get("open_date", "2001-01-01"), "%Y-%m-%d")

            if key[0] == "open" and open_date > start_date:
                details = value.get("details", {})
                ptype = details.get("type", "")
                queued = details.get("queued")
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
                            pldict["initial_qc_samples"] += value.get("no_of_samples")
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
        return pldict


    def turnaround(self, days=30):
        pass

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
        for project in self.projects_view:
            key = project["key"]
            value = project["value"]
            details = value.get("details", {})
            if key[0] == "open":
                #opened project types
                ptype = details.get("type", "")
                if ptype == "Production":
                    projdict["in_production"] += 1
                elif ptype == "Application":
                    projdict["in_applications"] += 1
                if "isFinishedLib" in value.keys():
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
            elif key[0] == "closed":
                #closed project stats
                close_value = value.get("close_date", "2001-01-01")
                close_date = datetime.strptime(close_value, "%Y-%m-%d")
                d_weeks = (dweekend - close_date).days / 7
                if d_weeks < max_weeks:
                    projdict["closed_n_weeks_ago"][d_weeks] += 1
                if (dnow - close_date).days < 7:
                    projdict["closed_last_7_days"] += 1

        return projdict


class KPIDocument(object):
    """
    Defines the document of the KPI database in statusDB
    Use KPIDocument.__dict__ to get a dict ready made for couchdb,
    but make sure that it's JSON serializable first ;)
    """
    def __init__(self, time_created, limit_file):
        self.time_created = time_created
        with open(limit_file, "rU") as f: #TODO: This path is relative
            self.limits = json.load(f)
        self.process_load = {}
        self.projects = {}
        self.success_rate = {}
        self.turnaround_times = {}

