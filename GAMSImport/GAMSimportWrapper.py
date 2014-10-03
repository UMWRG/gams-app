#!/usr/bin/env python
"""Wrapper script that sets the necessary environment variables for GAMSimport.
"""

import os
import sys
import subprocess
from HydraLib import PluginLib

cmd_args = sys.argv

gams_path = None

for i, arg in enumerate(cmd_args):
    if arg in ['-G', '--gams-path']:
        gams_path = cmd_args[i + 1]

if gams_path is None:
    if os.name == 'nt':
        base = 'C://GAMS/'
        #Try looking in the default location.
        if os.path.exists(base):
            wintypes = [f for f in os.listdir(base) if f.find('win') >= 0]
            if len(wintypes) > 0:
                gams_win_dir = base + wintypes[0] + '/'
                gams_versions = [v for v in os.listdir(gams_win_dir)]
                #Attempt to find the highest version by sorting the version
                #directories and picking the last one
                gams_versions.sort()
                if len(gams_versions) > 0:
                    gams_path = gams_win_dir + gams_versions[-1]
    else:
        base = '/opt/gams/'
        #Try looking in the default location.
        if os.path.exists(base):
            linuxtypes = [f for f in os.listdir(base) if f.find('linux') >= 0]
            linuxtypes.sort()
            #Attempt to find the highest version by sorting the version
            #directories and picking the last one
            if len(linuxtypes) > 0:
                gams_path = base + linuxtypes[-1]

if gams_path is not None:
    gams_path = os.path.abspath(gams_path)

    os.environ['LD_LIBRARY_PATH'] = gams_path
    
    gams_python_api_path = "%s/apifiles/Python/api"%gams_path

    if os.environ['PYTHONPATH'].find(gams_python_api_path) < 0:
        os.environ['PYTHONPATH'] = "%s:%s"%(os.environ['PYTHONPATH'], gams_python_api_path)

    cmd_args[0] = 'GAMSimport.py'

    stdout = sys.stdout
    stderr = sys.stderr

    cmd = subprocess.call(['python'] + cmd_args, stdout=stdout, stderr=stderr)

else:
    err = PluginLib.create_xml_response('GAMSimport', None, None, errors = ["Unable to find GAMS installation. Please specify folder containing gams executable."])
    print err

