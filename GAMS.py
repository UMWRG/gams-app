'''
    plugin_name: GAMS One
        - Export a network from Hydra to a gams input text file.
	    - Rum GAMS.
	    - Import a gdx results file into Hydra.

mandatory_args
==============


====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--switch               -sh    function   option to set the plugin function, the
                                         options are no witch option or A: Auto,
                                         export, run then import, E: export only,
                                         I: Import only
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


Examples:
=========

         Auto (default, no -sh switch is required) or -sh a

        -t 4 -s 4 -tx  2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"  -m "c:\temp
        \Demo2.gms"

        Importer
        -sh i  -t 4 -s 4 -f "c:\temp\Results.gdx" -m "c:\temp\Demo2.gms"

        Exporter
        -sh e -t 4 -s 4  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"
'''
import sys
import os
import time
from datetime import datetime

gamslibpath = 'lib'
api_path = os.path.realpath(os.path.abspath(gamslibpath))
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################

from HydraLib.HydraException import HydraPluginError

from Export import GAMSexport
from Import import GAMSimport
from HydraLib import PluginLib
from HydraGAMSlib import get_gams_path
from HydraGAMSlib import commandline_parser
from HydraGAMSlib import write_progress
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

    except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSexport', args.network, [args.scenario], errors = errors)
          print err
          sys.exit(0)
    return exporter

def run_gams_model():
    try:
        log.info("Running GAMS model .....")
        cur_time=datetime.now()
        working_directory=os.path.dirname(args.gms_file)
        model = GamsModel(args.gams_path, working_directory)
        model.add_job(args.gms_file)
        model.run()
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
        gdximport = GAMSimport()
        gdximport.set_network(network)
        get_result(gdximport)

    except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSimport', args.network, [args.scenario], errors = errors)
          print err

def import_results():
     try:
        gdximport = GAMSimport()
        gdximport.load_network(args.network, args.scenario)
        get_result(gdximport)

     except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSimport', args.network, [args.scenario], errors = errors)
          print err

def get_result(gdximport):
    '''
       Load gams file, result file  and extract the required data from it, then save them to database
    '''
    gdximport.load_gams_file(args.gms_file)
    gdximport.load_network(args.network, args.scenario)
    gdximport.parse_time_index()
    gdximport.open_gdx_file(args.gdx_file)
    gdximport.read_gdx_data()
    gdximport.parse_variables()
    gdximport.assign_attr_data()
    gdximport.save()

if __name__ == '__main__':
    parser = commandline_parser()
    args = parser.parse_args()
    #if switch is not provided, the default is auto is applied
    if(args.switch==None):
        args.switch='A'
    else:
        #chech the switch vrs the 3 defined modes (E, I, and A)
        if(args.switch.upper()!='I' and args.switch.upper()!='E' and args.switch.upper()!='A'):
            errors = ["Unknow swithc: -sh "+args.switch]
            err = PluginLib.create_xml_response('GAMS', args.network, [args.scenario], errors = errors)
            print err
            exit(0)
        else:
            args.switch=args.switch.upper()
    link_export_flag = 'nn'
    if args.link_name is True:
         link_export_flag = 'l'
    # run exporter if the mode is auto or export only
    if(args.switch=='A' or args.switch=='E'):
        exporter=export_network()
        #if the mode is E, it exits
        if(args.switch=='E'):
             message="Run successfully"
             print PluginLib.create_xml_response('GAMS Exporter', args.network, [args.scenario], message=message)
             exit(0)
        else:
            run_gams_model()
    #if the mode is Auto, it will get the network from the exporter
    if(args.switch=='A'):
        read_results(exporter.net)
    #if the mode is I, then network need to be loaded from database
    else:
        import_results()
    message="Run successfully"
    print PluginLib.create_xml_response('GAMS', args.network, [args.scenario], message=message)


