from datetime import datetime, timedelta
import numpy as np
import json
import re

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
                "library_prep": 0
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
            queued = details.get("queued")
            close_date = value.get("close_date")
            aborted = details.get("aborted")
            sample_type = details.get("sample_type")
            if details.get("type") == "Production" and aborted is None:

                # Projects TaT
                try:
                    proj_dates = self.project_dates[[proj_key]].rows[0].value
                except:
                    proj_dates = None

                try:
                    seq_date = proj_dates.get("sequencing_start_date")
                    prep_date = proj_dates.get("library_prep_start")
                    proj_end = datetime.strptime(close_date, "%Y-%m-%d")
                    if proj_end > start_date: 
                        if sample_type == "Finished Library":
                            seq_start = datetime.strptime(seq_date, "%Y-%m-%d")
                            finlib_days = (proj_end - seq_start).days
                            finlib_projs.append(finlib_days)
                        else:
                            prep_start = datetime.strptime(prep_date, "%Y-%m-%d")
                            prepped_days = (proj_end - prep_start).days
                            prep_projs.append(prepped_days)
                except TypeError:
                    pass
                except AttributeError:
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
                except ValueError:
                    pass

                # Library prep TaT
                try:
                    samples = self.project_samples[proj_key].rows[0].value
                except IndexError:
                    continue

                if samples is None:
                    continue

                for sample_key, sample in samples.items():
                    # TODO: Replace with library pooling information when available
                    first_prep_start = sample.get("first_prep_start_date")
                    if sample.get("library_prep") is None or first_prep_start is None:
                        continue

                    prep_re = re.compile('^[A-Z]$')
                    preps = sorted([m for m in sample["library_prep"].keys() if prep_re.match(m)])
                    for prep in preps:
                        final_prep_ends = []
                        if sample["library_prep"][preps[-1]].get("prep_status") == "PASSED":
                            for val_key, lib_val in sample["library_prep"][preps[-1]].get("library_validation", {}).items():
                                final_prep_ends.append(lib_val.get("finish_date"))
                        try:
                            valid_preps = [datetime.strptime(i, "%Y-%m-%d") for i in final_prep_ends if i is not None]
                            prep_end = max(valid_preps)
                            prep_start = datetime.strptime(first_prep_start, "%Y-%m-%d")
                            prep_days = (prep_end - prep_start).days
                            if prep_end > start_date and prep_days >= 0:
                                libprep_list.append(prep_days)
                        except TypeError:
                            continue
                        except ValueError:
                            continue
        return({
            "library_prep": self._ninetypct_mean(libprep_list)
            "initial_qc": self._ninetypct_mean(qc_list),
            "finished_library_project": self._ninetypct_mean(finlib_projs),
            "library_prep_project": self._ninetypct_mean(prep_projs)
        })

    def _ninetypct_mean(self, vector):
        """
        Get mean of list, excluding the top 10 % 
        TODO: Should we discard bottom 10% to make it statistically correct?
        """
        if len(vector) > 0:
            ninety_pct = np.percentile(np.array(vector), 90)
            trimmed_vector = np.array([i for i in vector if i <= ninety_pct])
            return round(trimmed_vector.mean(), 2)
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

    def success_rate(self):
        pass

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

