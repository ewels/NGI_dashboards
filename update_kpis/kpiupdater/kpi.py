import numpy as np
import re
from datetime import datetime, timedelta


def _get_percentile(vector, percentile):
    """Helper function to calculate a percentile"""
    if len(vector) > 0:
        pct = np.percentile(np.array(vector), percentile)
        return round(pct, 2)
    else:
        return None


def _is_ongoing(doc):
    details = doc.get("details", {})
    if "open_date" in doc.keys() and "close_date" not in doc.keys() and "aborted" not in details.keys():
        return True
    else:
        return False


class KPIBase(object):

    def __init__(self):
        self.start_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(30)
        self.state = 0

    def __call__(self, doc):
        """Computes a kpi from the document. Changes the state of this object"""
        return

    def summary(self):
        """Returns the final KPI, from the objects current state"""
        return self.state


### Success Rate


class SuccessInitialQC(KPIBase):
    """
    Definition: 1-(Samples failed/total samples that proceedes to library prep), 
    for finished libraries it is 1-(pools failed/total finished libraries 
    """
    def __init__(self):
        super(SuccessInitialQC, self).__init__()
        self.initial_qc_fails = set()
        self.samples_started = set()

    def __call__(self, doc):
        # TODO: Include finished libraries
        for ws_key, ws in doc.get("worksets", {}).items():
            ws_start = ws.get("date_run")
            try:
                ws_start = datetime.strptime(ws["date_run"], "%Y-%m-%d")
            except KeyError:
                return
            except TypeError:
                return

            for sample_key, sample in ws.get("samples").items():
                rec_ctrl = sample.get("rec_ctrl", {}).get("status")
                if rec_ctrl is not None and ws_start > self.start_date:
                    self.samples_started.add(sample_key) 
                    if rec_ctrl == "FAILED":
                        self.initial_qc_fails.add(sample_key)

    def summary(self):
        return round(1 - (float(len(self.initial_qc_fails)) / float(len(self.samples_started))), 2)


class SuccessLibraryPrep(KPIBase):
    """
    Definition: samples passed/total samples prepared
    """
    def __init__(self):
        super(SuccessLibraryPrep, self).__init__()
        self.prep_finished = 0
        self.prep_passed = 0

    def __call__(self, doc):
        for ws_key, ws in doc.get("worksets", {}).items():
            try:
                ws_start = datetime.strptime(ws["date_run"], "%Y-%m-%d")
                last_agg = datetime.strptime(ws["last_aggregate"], "%Y-%m-%d")
            except KeyError:
                return
            except TypeError:
                return

            for sample_key, sample in ws.get("samples").items():
                prep_status = sample.get("library_status")
                if prep_status is not None and prep_status != "UNKNOWN" and last_agg is not None and last_agg > self.start_date:
                    self.prep_finished += 1.0
                    if prep_status == "PASSED":
                        self.prep_passed += 1.0

    def summary(self):
        return round(self.prep_passed / self.prep_finished, 2)


### Projects


class ProjectsFinishedLib(KPIBase):
    """ Projects open which are sequenced as finished libraries """
    def __call__(self, doc):
        details = doc.get("details", {})
        if details.get("sample_type") == "Finished Library" and _is_ongoing(doc):
            self.state += 1

class ProjectsLibraryPrep(KPIBase):
    """ Projects open which are have ordered a library prep """
    def __call__(self, doc):
        details = doc.get("details", {})
        if details.get("sample_type") != "Finished Library" and _is_ongoing(doc):
            self.state += 1


class ProjectsInProduction(KPIBase):
    """Projects in in NGI Production which are currently open"""
    def __call__(self, doc):
        details = doc.get("details", {})
        if details.get("type", "") == "Production" and _is_ongoing(doc):
            self.state += 1


class ProjectsInApplications(KPIBase):
    """Projects in in NGI Applications which are currently open"""
    def __call__(self, doc):
        details = doc.get("details", {})
        if details.get("type", "") == "Application" and _is_ongoing(doc):
            self.state += 1


class ProjectsOpenedLastSeven(KPIBase):
    """ Number of projects opened in the last seven days """

    def __init__(self):
        super(ProjectsOpenedLastSeven, self).__init__()
        self.dnow = datetime.now()

    def __call__(self, doc): 
        open_date = datetime.strptime(doc.get("open_date", "2001-01-01"), "%Y-%m-%d")            
        if (self.dnow - open_date).days < 7:
            self.state += 1


class ProjectsClosedLastSeven(KPIBase):
    """ Number of projects closed in the last seven days """

    def __init__(self):
        super(ProjectsClosedLastSeven, self).__init__()
        self.dnow = datetime.now()

    def __call__(self, doc):
        close_date = datetime.strptime(doc.get("close_date", "2001-01-01"), "%Y-%m-%d")            
        if (self.dnow - close_date).days < 7:
            self.state += 1


class ProjectsOpenedNWeeks(KPIBase):
    """ 
    Number of projects opened in the N last weeks. Returns is a dict with keys n=0,1,2,3,...
    weeks ago. E.g. self.state = {0: 1, 2: 4, 3: 0, 4: 5}
    """
    def __init__(self):
        self.dnow = datetime.now()
        self.max_weeks = 4
        self.state = {key: 0 for key in range(0, self.max_weeks)}

    def __call__(self, doc):
        dweekend = datetime.strptime("{0}-{1}-0".format(*self.dnow.isocalendar()),"%Y-%W-%w")
        open_date = datetime.strptime(doc.get("open_date", "2001-01-01"), "%Y-%m-%d") 
        d_weeks = (dweekend - open_date).days / 7
        if d_weeks < self.max_weeks:
            self.state[d_weeks] += 1


class ProjectsClosedNWeeks(KPIBase):
    """ 
    Number of projects closed in the N last weeks. self.state is a dict with keys n=0,1,2,3,...
    weeks ago. E.g. self.state = {0: 1, 2: 4, 3: 0, 4: 5}
    """
    def __init__(self):
        self.dnow = datetime.now()
        self.max_weeks = 4
        self.state = {key: 0 for key in range(0, self.max_weeks)}

    def __call__(self, doc):
        dweekend = datetime.strptime("{0}-{1}-0".format(*self.dnow.isocalendar()),"%Y-%W-%w")
        close_date = datetime.strptime(doc.get("close_date", "2001-01-01"), "%Y-%m-%d") 
        d_weeks = (dweekend - close_date).days / 7
        if d_weeks < self.max_weeks:
            self.state[d_weeks] += 1


### Process Load


class ProcessLoadBase(KPIBase):

    def __call__(self, doc):
        self.details = doc.get("details",{})
        self.ptype = self.details.get("type", "")
        try:
            self.queued = self.details["queued"]
        except KeyError:
            self.queued = doc.get("project_summary", {}).get("queued")


class LoadInitialQCSamples(ProcessLoadBase):
    """
    Definition currently ongoing: total number of samples present in 
    projects with open date but no queue date. 
    """
    def __call__(self, doc):
        super(LoadInitialQCSamples, self).__call__(doc)
        if _is_ongoing(doc) and self.queued is None and self.ptype == "Production":
            if self.details.get("sample_type") != "Finished Library":
                try:
                    self.state += doc.get("no_samples")
                except TypeError:
                    self.state += self.details.get("sample_units_ordered", 0)


class LoadInitialQCLanes(ProcessLoadBase):
    """
    Definition currently ongoing: total number of lanes present in 
    projects with open date but no queue date. 
    """
    def __call__(self, doc):
        super(LoadInitialQCLanes, self).__call__(doc)
        if _is_ongoing(doc) and self.queued is None and self.ptype == "Production":
            if self.details.get("sample_type") == "Finished Library":
                try: 
                    self.state += self.details.get("sequence_units_ordered_(lanes)")
                except TypeError:
                    pass #TODO maybe log. But there are some "special" projects with no lanes ordered


class LoadLibraryPrepQueue(ProcessLoadBase):
    """
    Definition current queue: total number of samples without library prep start date, 
    present in projects with queue date
    """
    def __call__(self, doc):
        super(LoadLibraryPrepQueue, self).__call__(doc)
        qsamples = {}
        if _is_ongoing(doc) and self.queued is not None and self.ptype == "Production" and self.details.get("sample_type") != "Finished Library":
            # Find samples that are possibly in queue, ie. not aborted and probably no ongoing prep
            for s_key, sample in doc.get("project_samples", {}).items():
                s_details = sample.get("details", {})
                if s_details.get("status_(manual)") == "In Progress" and "library_prep" not in sample.keys():
                    qsamples[s_key] = 0
            # Make sure that there is no ongoing prep for these samples
            for ws_key, ws in doc.get("worksets", {}).items():
                for s_key in ws.get("samples", {}).keys():
                    if s_key in qsamples:
                        qsamples.pop(s_key)
            self.state += len(qsamples)


class LoadLibraryPrep(ProcessLoadBase):
    """
    Definition currently ongoing: total number of samples with a library prep start date, 
    not in library pooling, dont have sequence start date, or aborted
    """
    
    def __call__(self, doc):
        super(LoadLibraryPrep, self).__call__(doc)
        osamples = {}
        if _is_ongoing(doc) and self.queued is not None and self.ptype == "Production" and self.details.get("sample_type") != "Finished Library":
            # Is the sample prepped and has the latest prep failed?
            # TODO: Replace with library pooling information when available
            for s_key, sample in doc.get("project_samples", {}).items():
                s_details = sample.get("details", {})
                if s_details.get("status_(manual)") == "In Progress" and "passed_sequencing_qc" not in s_details.keys():
                    if "library_prep" in sample.keys():
                        prep_re = re.compile('^[A-Z]$')
                        preps = sorted([m for m in sample["library_prep"].keys() if prep_re.match(m)])
                        if sample["library_prep"][preps[-1]].get("prep_status") == "FAILED":
                            osamples[s_key] = 0
                    elif "first_prep_start_date" in sample.keys():
                        osamples[s_key] = 0

            # Are any of these samples in sequencing? If so exclude them
            for ws_key, ws in doc.get("worksets", {}).items():
                for s_key, sample in ws.get("samples", {}).items():
                    if s_key in osamples and len(sample.get("sequencing", {})) == 0:
                        osamples[s_key] = 1

            self.state += sum(osamples.values())


### Turn-around times


class TaTBase(KPIBase):

    def __init__(self):
        super(TaTBase, self).__init__()
        self.state = []

    def __call__(self, doc):
        self.details = doc.get("details",{})
        self.ptype = self.details.get("type", "")
        self.sample_type = self.details.get("sample_type")
        self.aborted = self.details.get("aborted")
        self.open_date = doc.get("open_date")
        self.close_date = doc.get("close_date")
        self.seq_date = doc.get("project_dates", {}).get("sequencing_start_date")
        self.prep_date =  doc.get("project_dates", {}).get("library_prep_start")
        self.prep_finished = doc.get("project_dates", {}).get("qc_library_finished")

        try:
            self.queued = self.details["queued"]
        except KeyError:
            self.queued = doc.get("project_summary", {}).get("queued")

    def summary(self):
        return _get_percentile(self.state, 90)


class TaTLibprepProj(TaTBase):
    """Definition: library prep start to project closed"""
    def __call__(self, doc):
        super(TaTLibprepProj, self).__call__(doc)
        if self.ptype == "Production" and self.aborted is None:
            try:
                proj_end = datetime.strptime(self.close_date, "%Y-%m-%d")
                if proj_end > self.start_date: 
                    if self.sample_type != "Finished Library":
                        prep_start = datetime.strptime(self.prep_date, "%Y-%m-%d")
                        proj_days = (proj_end - prep_start).days
                        self.state.append(proj_days)
            except TypeError:
                pass


class TaTFinlibProj(TaTBase):
    """Definition:  sequencing start to project closed"""
    def __call__(self, doc):
        super(TaTFinlibProj, self).__call__(doc)
        if self.ptype == "Production" and self.aborted is None:
            try:
                proj_end = datetime.strptime(self.close_date, "%Y-%m-%d")
                if proj_end > self.start_date: 
                    if self.sample_type == "Finished Library":
                            seq_start = datetime.strptime(self.seq_date, "%Y-%m-%d")
                            finlib_days = (proj_end - seq_start).days
                            self.state.append(finlib_days)
            except TypeError:
                pass


class TaTInitialQC(TaTBase):
    """ Definition: open date to queue date  in production"""
    def __call__(self, doc):
        super(TaTInitialQC, self).__call__(doc)
        if self.ptype == "Production" and self.aborted is None:
            try:
                qc_start = datetime.strptime(self.open_date, "%Y-%m-%d")
                qc_end = datetime.strptime(self.queued, "%Y-%m-%d")
                qc_days = (qc_end - qc_start).days
                if qc_end > self.start_date and qc_days >= 0:
                    self.state.append(qc_days)
            except TypeError:
                pass


class TaTLibprep(TaTBase):
    """Definition: library prep start - in queue library pooling"""
    def __call__(self, doc):
        super(TaTLibprep, self).__call__(doc)
        if self.ptype == "Production" and self.aborted is None:
            try:
                # TODO: limit by "ququed for pooling" when available
                prep_start = datetime.strptime(self.prep_date, "%Y-%m-%d")
                prep_end = datetime.strptime(self.prep_finished, "%Y-%m-%d")
                prep_days = (prep_end - prep_start).days
                if prep_end > self.start_date and prep_days >= 0:
                    self.state.append(prep_days)
            except TypeError:
                pass



