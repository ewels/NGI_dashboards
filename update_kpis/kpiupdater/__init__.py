import numpy as np
import json
import re
from genologics.entities import *
from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD
from datetime import datetime, timedelta
from decimal import Decimal
lims = Lims(BASEURI, USERNAME, PASSWORD)


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

def sequencing_success(num_days=30):
    start_date = datetime.now() - timedelta(days=num_days)
    flowcells = lims.get_containers(type=["Patterned Flow Cell", "Illumina Flow Cell", "MiSeq Reagent Cartridge"], 
            last_modified=start_date.strftime("%Y-%m-%dT00:00:00Z"))
    finished_lanes = 0.0
    passed_lanes = 0.0
    for fc in flowcells:
        fc_arts = lims.get_artifacts(containername=fc.name)
        for art in fc_arts:
            if art.qc_flag != "UNKNOWN":
                finished_lanes += 1
                if art.qc_flag == "PASSED":
                    passed_lanes += 1

    return round(passed_lanes / finished_lanes,2)


def estimate_lanes_per_artifact(art):
    lanes=0
    for sample in art.samples:
        try:
            lanes+=float(sample.project.udf['Sequence units ordered (lanes)']) / lims.get_sample_number(projectlimsid=sample.project.id)
        except:
            pass

    return round(Decimal(lanes), 2)

def sequencing_load():

    #This handles the QUEUES only
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
        for art in q.artifacts:
            miseq_l+=estimate_lanes_per_artifact(art)
    for s in q_miseq_p_ids:
        q=Queue(lims, id=s)
        miseq_p+=len(q.artifacts)
        for art in q.artifacts:
            miseq_l+=estimate_lanes_per_artifact(art)
    for s in q_hiseq_s_ids:
        q=Queue(lims, id=s)
        hiseq_s+=len(q.artifacts)
        for art in q.artifacts:
            hiseq_l+=estimate_lanes_per_artifact(art)
    for s in q_hiseq_p_ids:
        q=Queue(lims, id=s)
        hiseq_p+=len(q.artifacts)
        for art in q.artifacts:
            hiseq_l+=estimate_lanes_per_artifact(art)
    for s in q_hiseqX_s_ids:
        q=Queue(lims, id=s)
        hiseqX_s+=len(q.artifacts)
        for art in q.artifacts:
            hiseqX_l+=estimate_lanes_per_artifact(art)
    for s in q_hiseqX_p_ids:
        q=Queue(lims, id=s)
        hiseqX_p+=len(q.artifacts)
        for art in q.artifacts:
            hiseqX_l+=estimate_lanes_per_artifact(art)
    #This handles what is currently running
    hiseq_rl=0
    hiseqx_rl=0
    miseq_rl=0
    starting_date=datetime.now() - timedelta(5)
    hiseq_pr=lims.get_processes(type="Illumina Sequencing (Illumina SBS) 4.0", last_modified=starting_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    for pro in hiseq_pr:
        if not pro.udf.get("Finish Date"):
            hiseq_rl+=len(pro.all_inputs())
    hiseqx_pr=lims.get_processes(type="Illumina Sequencing (HiSeq X) 1.0", last_modified=starting_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    for pro in hiseqx_pr:
        if not pro.udf.get("Finish Date"):
            hiseqx_rl+=len(pro.all_inputs())
    miseq_pr=lims.get_processes(type="MiSeq Run (MiSeq) 4.0", last_modified=starting_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    for pro in miseq_pr:
        if not pro.udf.get("Finish Date"):
            miseq_rl+=len(pro.all_inputs())



    return [miseq_s, miseq_p, int(miseq_l), hiseq_s, hiseq_p, int(hiseq_l), hiseqX_s, hiseqX_p, int(hiseqX_l), int(hiseq_rl), int(hiseqx_rl), int(miseq_rl)]
