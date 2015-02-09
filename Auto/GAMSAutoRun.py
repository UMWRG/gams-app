#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# GAMSAutoRun is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# GAMSAutoRun is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with GAMSAutoRun.  If not, see <http://www.gnu.org/licenses/>\
#
'''

plugin_name: GAMS
            - Export a network from Hydra to a gams input text file.
            - Rum GAMS.
            - Import a gdx results file into Hydra.

mandatory_args
==============
====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to GAMS.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
--template-id         -tp    TEMPLATE    ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output              -o     OUTPUT      Filename of the output file.
--gams-model          -m     GMS_FILE    Full path to the GAMS model (*.gms)
                                         used for the simulation.


Server-based arguments
======================

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
``--server_url``       ``-u`` SERVER_URL   Url of the server the plugin will 
                                           connect to.
                                           Defaults to localhost.
``--session_id``       ``-c`` SESSION_ID   Session ID used by the calling software
                                           If left empty, the plugin will attempt 
                                           to log in itself.

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
--gams-path            -G     GAMS_PATH  File path of the GAMS installation.
--gdx-file             -f     GDX_FILE   GDX file containing GAMS results

**Optional arguments:**

====================== ======= ========== =========================================
--group-nodes-by        -gn     GROUP_ATTR Group nodes by this attribute(s).
--group_links-by        -gl     GROUP_ATTR Group links by this attribute(s).
====================== ======= ========== =========================================

For Export function:
====================

Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ======= ========== ======================================
--start-date            -st   START_DATE  Start date of the time period used for
                                          simulation.
--end-date              -en   END_DATE    End date of the time period used for
                                          simulation.
--time-step             -dt   TIME_STEP   Time step used for simulation. The
                                          time step needs to be specified as a
                                          valid time length as supported by
                                          Hydra's unit conversion function (e.g.
                                          1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
====================== ======= ========== ======================================

**Option 2:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ======= ========== ======================================
--time-axis             -tx    TIME_AXIS  Time axis for the modelling period (a
                                          list of comma separated time stamps).
====================== ======= ========== ======================================


Example:
=========
        -t 4 -s 4 -tx  2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo2.dat" -m "c:\temp\Demo2.gms"


'''
import sys
import os
import time
from datetime import datetime

pythondir = os.path.dirname(os.path.realpath(__file__))
gamslibpath=os.path.join(pythondir, '..', 'lib')
api_path = os.path.realpath(gamslibpath)
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################


from HydraLib.HydraException import HydraPluginError

from Export import GAMSExport
from Import import GAMSImport
from HydraLib import PluginLib
from HydraGAMSlib import commandline_parser
from dateutil import parser
from HydraLib.PluginLib import write_progress
from RunGamsModel import GamsModel

import logging
log = logging.getLogger(__name__)

def get_files_list(directory, ext):
    '''
    return list of files with specific ext on a folder with their last modified dates and times
    '''
    files_list={}
    for file_ in os.listdir(directory):
        if(file_.endswith(ext)):
            absolute_path = os.stat(os.path.join(directory,file_))
            files_list[file_]=time.ctime(absolute_path.st_mtime)
    return files_list

def get_input_file_name(gams_model):
    '''
    return  output data file name if it is not provided by the user
    '''
    inputfilename=None
    gamsfile=open(gams_model, "r")
    for line in gamsfile:
            sline = line.strip()
            if len(sline) > 0 and sline[0] == '$':
                lineparts = sline.split()
                if lineparts[1] == 'include':
                    name=sline
                    name=name.replace('$','')
                    name=name.replace('"','')
                    name=name.replace(';','')
                    name=name.replace('include','')
                    name=name.strip()
                    inputfilename=os.path.join(os.path.dirname(gams_model),name)
                    break
    gamsfile.close()
    log.info("Exporting data to: %s", inputfilename)
    return inputfilename

def export_network():
    template_id = None
    exporter = GAMSExport(steps, args.network,
                          args.scenario,
                          template_id,#int(args.template_id),
                          args.output,
                          link_export_flag,
                          session_id=args.session_id,
                          url=args.server_url)

    exporter.steps=steps
    if args.template_id is not None:
        exporter.template_id = int(args.template_id)
    exporter.export_network()
    if args.start_date is not None and args.end_date is not None \
            and args.time_step is not None:
        exporter.write_time_index(start_time=args.start_date,
                                  end_time=args.end_date,
                                  time_step=args.time_step)
    elif args.time_axis is not None:
        exporter.write_time_index(time_axis=args.time_axis)
    else:
        raise HydraPluginError('Time axis not specified.')
    exporter.export_data()
    exporter.write_file()
    return exporter

def run_gams_model(args):
    log.info("Running GAMS model .....")
    cur_time=datetime.now().replace(microsecond=0)
    write_progress(9, steps)
    working_directory=os.path.dirname(args.gms_file)
    
    if working_directory == '':
        working_directory = '.'

    model = GamsModel(args.gams_path, working_directory)
    write_progress(10, steps)
    model.add_job(os.path.basename(args.gms_file))
    write_progress(11, steps)
    model.run()
    write_progress(12, steps)
    log.info("Running GAMS model finsihed")
    # if result file is not provided, it looks for it automatically at GAMS WD
    if(args.gdx_file==None):
        log.info("Extracting results from %s.", working_directory)
        files_list=get_files_list(working_directory, '.gdx')
        for file_ in files_list:
            dt = parser.parse(files_list[file_])
            log.critical(dt)
            delta= (dt-cur_time).total_seconds()
            if delta>=0:
                args.gdx_file=os.path.join(working_directory, file_)
        if(args.gdx_file==None):
              raise HydraPluginError('Result file is not provided/found.')



def read_results(network):
    write_progress(13, steps)
    gdximport = GAMSImport(session_id=args.session_id,url=args.server_url)
    gdximport.set_network(network)
    write_progress(14, steps)
    gdximport.load_gams_file(args.gms_file)
    write_progress(15, steps)
    gdximport.load_network(args.network, args.scenario)
    write_progress(16, steps)
    gdximport.parse_time_index()
    write_progress(17, steps)
    gdximport.open_gdx_file(args.gdx_file)
    write_progress(18, steps)
    gdximport.read_gdx_data()
    write_progress(19, steps)
    gdximport.parse_variables()
    write_progress(20, steps)
    gdximport.assign_attr_data()
    write_progress(21, steps)
    gdximport.save()


def check_args(args):
    try:
        int(args.network)
    except (TypeError, ValueError):
        raise HydraPluginError('No network is specified')
    try:
        int(args.scenario)
    except (TypeError, ValueError):
        raise HydraPluginError('No senario is specified')

    if args.gms_file is None:
        raise HydraPluginError('Gams file is not specifed')
    elif os.path.isfile(args.gms_file)==False:
        raise HydraPluginError('Gams file: '+args.gms_file+', is not existed')
    elif args.output==None:
        args.output=get_input_file_name(args.gms_file)
        if args.output is None:
            raise HydraPluginError('No output file specified')
    elif os.path.exists(os.path.dirname(args.output))==False:
            raise HydraPluginError('output file directory: '+ os.path.dirname(args.output)+', is not exist')

if __name__ == '__main__':
    try:
        steps=21
        cmd_parser = commandline_parser()
        args = cmd_parser.parse_args()
        check_args(args)
        link_export_flag = 'nn'
        if args.link_name is True:
             link_export_flag = 'l'
        exporter=export_network()
        run_gams_model(args)
        #if the mode is Auto, it will get the network from the exporter
        read_results(exporter.net)
        message="Run successfully"
        print PluginLib.create_xml_response('GAMSAuto', args.network, [args.scenario], message=message)
    except HydraPluginError, e:
        log.exception(e)
        err = PluginLib.create_xml_response('GAMSAuto', args.network, [args.scenario], errors = [e.message])
        print err
    except Exception as e:
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
        log.exception(e)
        err = PluginLib.create_xml_response('GAMSAuto', args.network, [args.scenario], errors = [e.message])
        print err


