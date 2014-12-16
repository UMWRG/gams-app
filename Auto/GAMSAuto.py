# (c) Copyright 2014, University of Manchester

'''

plugin_name: GAMS Plugin
        - Export a network from Hydra to a gams input text file.
	    - Rum GAMS.
	    - Import a gdx results file into Hydra.

mandatory_args
==============


====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to GAMS.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
--template-id         -tp  TEMPLATE      ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output              -o    OUTPUT       Filename of the output file.
--gams-model          -m     GMS_FILE    Full path to the GAMS model (*.gms)
                                         used for the simulation.


non_mandatory_args
==================

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--gams-path            -G     GAMS_PATH  File path of the GAMS installation.
--gdx-file             -f     GDX_FILE   GDX file containing GAMS results

**Optional arguments:**

====================== ======= ========== ======================================
--group-nodes-by        -gn     GROUP_ATTR Group nodes by this attribute(s).
--group_links-by        -gl     GROUP_ATTR Group links by this attribute(s).
====================== ======= ========== ======================================

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

        -t 4 -s 4 -tx  2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"  -m "c:\temp
        \Demo2.gms"

'''
import sys
import os
import time
from datetime import datetime

gamslibpath = '..\lib'
api_path = os.path.realpath(os.path.abspath(gamslibpath))
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################

from HydraLib.HydraException import HydraPluginError

from GAMSexport import GAMSexport
from GAMSimport import GAMSimport
from HydraLib import PluginLib
from HydraGAMSlib import get_gams_path
from HydraGAMSlib import commandline_parser
from HydraGAMSlib import write_output
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

def export_network():
    try:
        template_id = None
        exporter = GAMSexport(int(args.network),
                              int(args.scenario),
                              template_id,#int(args.template_id),
                              args.output,
                              link_export_flag,
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
        return exporter
    except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSexport', args.network, [args.scenario], errors = errors)
          print err
          sys.exit(0)

def run_gams_model():
    try:
        log.info("Running GAMS model .....")
        cur_time=datetime.now()
        write_output(8, steps)
        working_directory=os.path.dirname(args.gms_file)
        model = GamsModel(args.gams_path, working_directory)
        write_output(9, steps)
        model.add_job(args.gms_file)
        write_output(10, steps)
        model.run()
        write_output(11, steps)
        log.info("Running GAMS model finsihed")
        # if result file is not provided, it looks for it automatically at GAMS WD
        if(args.gdx_file==None):
            log.info("Extract result file name.....")
            files_list=get_files_list(working_directory, '.gdx')
            for file_ in files_list:
                from dateutil import parser
                dt = parser.parse(files_list[file_])
                delta= (dt-cur_time).total_seconds()
                if delta>0:
                    args.gdx_file=working_directory+"\\"+file_
            if(args.gdx_file==None):
                  raise HydraPluginError('Result file is not provided/found.')

    except Exception as e:
        errors = [e.message]
        print "Error is: ", errors
        err = PluginLib.create_xml_response('GAMS_run_model', args.network, [args.scenario], errors = errors)
        print err
        sys.exit(0)

def read_results(network):
    try:
        write_output(12, steps)
        gdximport = GAMSimport()
        gdximport.set_network(network)
        write_output(13, steps)
        gdximport.load_gams_file(args.gms_file)
        write_output(14, steps)
        gdximport.load_network(args.network, args.scenario)
        write_output(15, steps)
        gdximport.parse_time_index()
        write_output(16, steps)
        gdximport.open_gdx_file(args.gdx_file)
        write_output(17, steps)
        gdximport.read_gdx_data()
        write_output(18, steps)
        gdximport.parse_variables()
        write_output(19, steps)
        gdximport.assign_attr_data()
        write_output(20, steps)
        gdximport.save()

    except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSimport', args.network, [args.scenario], errors = errors)
          print err

if __name__ == '__main__':
    steps=21
    parser = commandline_parser()
    args = parser.parse_args()
    link_export_flag = 'nn'
    if args.link_name is True:
         link_export_flag = 'l'
    exporter=export_network()
    run_gams_model()
    #if the mode is Auto, it will get the network from the exporter
    read_results(exporter.net)
    message="Run successfully"
    print PluginLib.create_xml_response('GAMS', args.network, [args.scenario], message=message)


