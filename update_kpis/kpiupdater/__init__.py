import numpy as np
import json
import re
from genologics.entities import *
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
lims = Lims(BASEURI, USERNAME, PASSWORD)
from datetime import datetime, timedelta


class ProjectViewsIter:
    """
        Constructs an iterator from statusDB views, using projectsDB/project/summary as base, ie.
        {
            summary.key:        P????
            summary.value1:     ..,
            summary.value2:     ..,
            ...,
            project_dates:      projectsDB/project/summary_dates[summary.key],
            project_samples:    projectsDB/project/samples[summary.key],
            worksets:           worksetsDB/project/ws_proj[summary.key]
        }
    """
    def __init__(self, project_summary, project_samples, project_dates, worksets_proj, ofptype=None):
        self.proj_key = None
        self.value = None
        self.ofptype = ofptype
        self.summary_iter = iter(project_summary.rows)
        self.project_samples = project_samples
        self.project_dates = project_dates
        self.worksets_proj = worksets_proj

    def __iter__(self):
        return self

    def next(self):
        tmp = self.summary_iter.next()
        if self.ofptype is not None:
            while True:
                test_ptype = tmp.get("value", {}).get("details", {}).get("type")
                if test_ptype == self.ofptype:
                    break
                tmp = self.summary_iter.next()
        
        self.proj_key = tmp["key"][1]
        self.value = tmp.get("value", {})             

        try:
            self.value["project_dates"] = self.project_dates[[self.proj_key]].rows[0]["value"]
        except:
            pass

        try:
            samples = self.project_samples[self.proj_key]
            self.value["project_samples"] = samples.rows[0]["value"]
        except:
            pass

        try:
            self.value["worksets"] = {}
            for row in self.worksets_proj[self.proj_key].rows:
                self.value["worksets"].update(row.value)
        except:
            pass

        return (self.proj_key, self.value)


def sequencing_load():

    # Sequencing (Thanks @Galithil)
    lanes = 0
    weekAgo = datetime.now() - timedelta(days=7)
    process_types = ["Illumina Sequencing (Illumina SBS) 4.0",
            "MiSeq Run (MiSeq) 4.0",
            "Illumina Sequencing (HiSeq X) 1.0"]
    seq = lims.get_processes(type=process_types, 
        last_modified=weekAgo.strftime("%Y-%m-%dT00:00:00Z"))

    for pro in seq:
        if not "Finish Date" in pro.udf or not pro.udf['Finish Date']:
            lanes += len(pro.all_inputs())

    return lanes
