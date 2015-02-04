#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# RunGamsModel is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# RunGamsModel is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with RunGamsModel.  If not, see <http://www.gnu.org/licenses/>\
#

__author__ = 'K. Mohamed'

import os
import sys

from HydraGAMSlib import get_gams_path

class GamsModel(object):
    def __init__(self, gamspath, working_directory):
        if(gamspath==None):
            gamspath=get_gams_path()
        real_path = os.path.realpath(os.path.abspath(gamspath))
        api_path = os.path.join(real_path,'apifiles','Python','api')
        if api_path not in sys.path:
            sys.path.insert(0, api_path)
        from gams import  workspace
        self.ws = workspace.GamsWorkspace(working_directory=working_directory, system_directory=gamspath, debug = 1)

    def add_job(self, model_file):
        self.job = self.ws.add_job_from_file(model_file)

    def run(self):
        self.job.run()
