#!/usr/bin/env python
# -*- coding: utf-8 -*-

from compliance_checker.suite import CheckSuite
from compliance_checker.cf import CFBaseCheck, dimless_vertical_coordinates
from compliance_checker.cf.util import is_vertical_coordinate, is_time_variable, units_convertible, units_temporal, StandardNameTable, create_cached_data_dir, download_cf_standard_name_table
from netCDF4 import Dataset
from tempfile import gettempdir
from compliance_checker.tests.resources import STATIC_FILES
from compliance_checker.tests import BaseTestCase

import os
import re

class TestCFIntegration(BaseTestCase):

    def setUp(self):
        '''
        Initialize the dataset
        '''
        self.cs = CheckSuite()
        self.cs.load_all_available_checkers()

    # --------------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------------

    def new_nc_file(self):
        '''
        Make a new temporary netCDF file for the scope of the test
        '''
        nc_file_path = os.path.join(gettempdir(), 'example.nc')
        if os.path.exists(nc_file_path):
            raise IOError('File Exists: %s' % nc_file_path)
        nc = Dataset(nc_file_path, 'w')
        self.addCleanup(os.remove, nc_file_path)
        self.addCleanup(nc.close)
        return nc

    def load_dataset(self, nc_dataset):
        '''
        Return a loaded NC Dataset for the given path
        '''
        if not isinstance(nc_dataset, str):
            raise ValueError("nc_dataset should be a string")

        nc_dataset = Dataset(nc_dataset, 'r')
        self.addCleanup(nc_dataset.close)
        return nc_dataset

    def get_results(self, check_results):
        '''
        Returns a tuple of the value scored, possible, and a list of messages
        in the result set.
        '''
        aggregation = self.cs.build_structure('cf', check_results['cf'][0], 'test', 1)
        out_of = 0
        scored = 0
        results = aggregation['all_priorities']
        for r in results:
            if isinstance(r.value, tuple):
                out_of += r.value[1]
                scored += r.value[0]
            else:
                out_of += 1
                scored += int(r.value)

        # Store the messages
        messages = []
        for r in results:
            messages.extend(r.msgs)

        return scored, out_of, messages

    def test_sldmb_43093_agg(self):
        dataset = self.load_dataset(STATIC_FILES['sldmb_43093_agg'])
        check_results = self.cs.run(dataset, [], 'cf')
        scored, out_of, messages = self.get_results(check_results)
        assert (scored, out_of) == (140, 150)
        assert u'standard_name temperature is not defined in Standard Name Table v36' in messages
        assert (u'auxiliary coordinate specified by the coordinates attribute, precise_lat, '
                'is not a variable in this dataset') in messages
        assert (u'auxiliary coordinate specified by the coordinates attribute, precise_lon, '
                'is not a variable in this dataset') in messages

        assert (u'attribute time:_CoordianteAxisType should begin with a letter and be composed '
                'of letters, digits, and underscores') in messages

        assert (u'global attribute DODS.dimName should begin with a letter and be composed of '
                'letters, digits, and underscores') in messages