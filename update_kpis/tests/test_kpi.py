from kpiupdater.kpi import *
import yaml
import unittest
from datetime import datetime


class TestProjectsKPI(unittest.TestCase):

    def setUp(self):
        with open("data/projects.yaml") as f:
            projs = yaml.load(f)

        self.p_iter = projs.itervalues()

    def test_in_production(self):
        p_inprod = ProjectsInProduction()
        p_inprod.start_date = datetime(2016, 1, 1, 0, 0)
        for doc in self.p_iter:
            p_inprod(doc)
        self.assertEqual(1, p_inprod.summary())

    def test_in_application(self):
        p_inapp = ProjectsInApplications()
        p_inapp.start_date = datetime(2016, 1, 1, 0, 0)
        for doc in self.p_iter:
            p_inapp(doc)
        self.assertEqual(2, p_inapp.summary())

    def test_finished_lib(self):
        p_finlib = ProjectsFinishedLib()
        p_finlib.start_date = datetime(2016, 1, 1, 0, 0)
        for doc in self.p_iter:
            p_finlib(doc)
        self.assertEqual(0, p_finlib.summary())

    def test_libprep(self):
        p_libprep = ProjectsLibraryPrep()
        p_libprep.start_date = datetime(2016, 1, 1, 0, 0)
        for doc in self.p_iter:
            p_libprep(doc)
        self.assertEqual(3, p_libprep.summary())

    def test_closedseven(self):
        p_cseven = ProjectsClosedLastSeven()
        p_cseven.dnow = datetime(2016, 2, 8, 0, 0)
        for doc in self.p_iter:
            p_cseven(doc)
        self.assertEqual(1, p_cseven.summary())

    def test_openedseven(self):
        p_oseven = ProjectsOpenedLastSeven()
        p_oseven.dnow = datetime(2016, 2, 8, 0, 0)
        for doc in self.p_iter:
            p_oseven(doc)
        self.assertEqual(1, p_oseven.summary())

    def test_closedNweeks(self):
        p_cnweeks = ProjectsClosedNWeeks()
        p_cnweeks.dnow = datetime(2016, 2, 8, 0, 0)
        for doc in self.p_iter:
            p_cnweeks(doc)
        self.assertEqual({0: 0, 1: 1, 2: 1, 3: 0}, p_cnweeks.summary())

    def test_openedNweeks(self):
        p_onweeks = ProjectsOpenedNWeeks()
        p_onweeks.dnow = datetime(2016, 2, 8, 0, 0)
        for doc in self.p_iter:
            p_onweeks(doc)
        self.assertEqual({0: 0, 1: 1, 2: 0, 3: 1}, p_onweeks.summary())


class TestSuccessKPI(unittest.TestCase):

    def setUp(self):
        with open("data/success.yaml") as f:
            projs = yaml.load(f)
        self.p_iter = projs.itervalues()

    def test_initialqc(self):
        s_initqc = SuccessInitialQC()
        s_initqc.start_date = datetime(2016, 1, 1, 0, 0)
        for doc in self.p_iter:
            s_initqc(doc)
        self.assertEqual(1, len(s_initqc.initial_qc_fails))
        self.assertEqual(3, len(s_initqc.samples_started))

    def test_libraryprep(self):
        s_libprep =  SuccessLibraryPrep()
        s_libprep.start_date = datetime(2016, 1, 1, 0, 0)
        for doc in self.p_iter:
            s_libprep(doc)
        self.assertEqual(3.0, s_libprep.prep_finished)
        self.assertEqual(2.0, s_libprep.prep_passed)

