import numpy as np
import json
import re
from genologics.entities import *
from genologics.lims import Lims
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


def estimate_lanes_per_pool(pool):
    lanes=0
    for sample in pool.samples:
        lanes+=float(sample.project.udf['Sequence units ordered (lanes)']) / lims.get_sample_number(projectlimsid=sample.project.id)

    return round(lanes, 2)

def sequencing_load():

    q_miseq_s_ids=['52', '53', '54', '505']
    q_miseq_p_ids=['55', '56', '253', '1002']
    q_hiseq_s_ids=['252', '46', '47', '401']
    q_hiseq_p_ids=['49', '125', '1001', '50']
    q_hiseqX_s_ids=['751', '711', '712']
    q_hiseqX_p_ids=['713', '714', '715', '716']
    miseq_s=0
    miseq_p=0
    miseq_l=0
    hiseq_s=0
    hiseq_p=0
    hiseq_l=0
    hiseqX_s=0
    hiseqX_p=0
    hiseqX_l=0
    for s in q_miseq_s_ids:
        q=Queue(lims, id=s)
        miseq_s+=len(q.artifacts)
    for s in q_miseq_p_ids:
        q=Queue(lims, id=s)
        miseq_p+=len(q.artifacts)
        for art in q.artifacts:
            miseq_l+=estimate_lanes_per_pool(art)
    for s in q_hiseq_s_ids:
        q=Queue(lims, id=s)
        hiseq_s+=len(q.artifacts)
    for s in q_hiseq_p_ids:
        q=Queue(lims, id=s)
        hiseq_p+=len(q.artifacts)
        for art in q.artifacts:
            hiseq_l+=estimate_lanes_per_pool(art)
    for s in q_hiseqX_s_ids:
        q=Queue(lims, id=s)
        hiseqX_s+=len(q.artifacts)
    for s in q_hiseqX_p_ids:
        q=Queue(lims, id=s)
        hiseqX_p+=len(q.artifacts)
        for art in q.artifacts:
            hiseqX_l+=estimate_lanes_per_pool(art)
    return [miseq_s, miseq_p, miseq_l, hiseq_s, hiseq_p, hiseq_l, hiseqX_s, hiseqX_p, hiseqX_l]
