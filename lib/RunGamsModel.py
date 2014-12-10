__author__ = 'Gust'

import os
import sys
from HydraGAMSlib import get_gams_path

class GamsModel(object):
    def __init__(self, gamspath, working_directory):
        if(gamspath==None):
            gamspath=get_gams_path()
        real_path = os.path.realpath(os.path.abspath(gamspath))
        api_path = real_path + '/apifiles/Python/api/'
        if api_path not in sys.path:
            sys.path.insert(0, api_path)
        from gams import  workspace
        self.ws = workspace.GamsWorkspace(working_directory=working_directory, system_directory=gamspath, debug = 3)

    def add_job(self, model_file):
        self.job = self.ws.add_job_from_file(model_file)

    def run(self):
        self.job.run()
