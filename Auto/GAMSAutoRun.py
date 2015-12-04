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


**Mandatory Args:**

====================== ======= ========== =========================================
Option                 Short   Parameter  Description
====================== ======= ========== =========================================
--network              -t      NETWORK    ID of the network where results will
                                          be imported to. Ideally this coincides
                                          with the network exported to GAMS.
--scenario             -s      SCENARIO   ID of the underlying scenario used for
--template-id          -tp     TEMPLATE   ID of the template used for exporting
                                          resources. Attributes that don't
                                          belong to this template are ignored.
--output               -o      OUTPUT     Filename of the output file.
--gams-model           -m      GMS_FILE   Full path to the GAMS model (*.gms)
                                          used for the simulation.


**Server-based arguments**

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
--server_url           -u     SERVER_URL Url of the server the plugin will 
                                         connect to.
                                         Defaults to localhost.
--session_id           -c     SESSION_ID Session ID used by the calling software
                                         If left empty, the plugin will attempt 
                                         to log in itself.
--gams-path            -G     GAMS_PATH  File path of the GAMS installation.
--gdx-file             -f     GDX_FILE   GDX file containing GAMS results

**Optional arguments:**

====================== ====== ========== =================================
Option                 Short  Parameter  Description
====================== ====== ========== =================================
--group-nodes-by       -gn    GROUP_ATTR Group nodes by this attribute(s).
--group_links-by       -gl    GROUP_ATTR Group links by this attribute(s).
====================== ====== ========== =================================

**Switches:**

====================== ====== =========================================
Option                 Short  Description
====================== ====== =========================================
--export_by_type       -et    Set export data based on types or based
                              on attributes only, default is export 
                              data by attributes unless this option 
                              is set.
====================== ====== =========================================


For Export function:
====================

Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ====== ========== =======================================
Option                 Short  Parameter  Description
====================== ====== ========== =======================================
--start-date           -st    START_DATE  Start date of the time period used for
                                          simulation.
--end-date             -en    END_DATE    End date of the time period used for
                                          simulation.
--time-step            -dt    TIME_STEP   Time step used for simulation. The
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
import argparse as ap

pythondir = os.path.dirname(os.path.realpath(__file__))
gamslibpath=os.path.join(pythondir, '..', 'lib')
api_path = os.path.realpath(gamslibpath)
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################


from HydraLib.HydraException import HydraPluginError
from HydraGAMSlib import check_lic

from Exporter import GAMSExporter
from Importer import GAMSImporter
from HydraLib import PluginLib
from dateutil import parser
from HydraLib.PluginLib import write_progress, write_output
from HydraGAMSlib import GamsModel

import logging
log = logging.getLogger(__name__)

def commandline_parser():
    cmd_parser = ap.ArgumentParser(
        description=""" Export a network from Hydra to a gams input text file, Rum GAMS. and finally Import a gdx results file into Hydra.
                    (c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information, web site will available soon",
        formatter_class=ap.RawDescriptionHelpFormatter)

    cmd_parser.add_argument('-G', '--gams-path',
                        help='Path of the GAMS installation.')
    cmd_parser.add_argument('-t', '--network-id',
                        help='''ID of the network that will be exported.''')
    cmd_parser.add_argument('-s', '--scenario-id',
                        help='''ID of the scenario that will be exported.''')
    cmd_parser.add_argument('-tp', '--template-id',
                        help='''ID of the template to be used.''')
    cmd_parser.add_argument('-m', '--gms-file',
                        help='''Full path to the GAMS model (*.gms) used for
                        the simulation.''')
    cmd_parser.add_argument('-o', '--output',
                        help='''Output file containing exported data''')
    cmd_parser.add_argument('-nn', '--node-node', action='store_true',
                        help="""(Default) Export links as 'from_name .
                        end_name'.""")
    cmd_parser.add_argument('-ln', '--link-name', action='store_true',
                        help="""Export links as link name only. If two nodes
                        can be connected by more than one link, you should
                        choose this option.""")
    cmd_parser.add_argument('-st', '--start-date',
                        help='''Start date of the time period used for
                        simulation.''')
    cmd_parser.add_argument('-en', '--end-date',
                        help='''End date of the time period used for
                        simulation.''')
    cmd_parser.add_argument('-dt', '--time-step',
                        help='''Time step used for simulation.''')
    cmd_parser.add_argument('-tx', '--time-axis', nargs='+',
                        help='''Time axis for the modelling period (a list of
                        comma separated time stamps).''')
    cmd_parser.add_argument('-f', '--gdx-file',
                        help='GDX file containing GAMS results.')

    cmd_parser.add_argument('-et', '--export_by_type',action='store_true',
                        help='''Use this switch to export data based on type, rather than attribute.''')

    cmd_parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')

    cmd_parser.add_argument('-gd', '--gams_date_time_index', action='store_true',
                        help='''Set the time indexes to be timestamps which are compatible with gams date format (dd.mm.yyyy)''')


    cmd_parser.add_argument('-c', '--session_id',
                        help='''Session ID. If this does not exist, a login will be
                        attempted based on details in config.''')
    return cmd_parser 

def get_files_list(directory, ext):
    '''
    return list of files with specific ext on a folder with their last modified dates and times
    '''
    files_list={}
    for file_ in os.listdir(directory):
        if file_.endswith(ext):
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

def export_network(is_licensed):
    exporter = GAMSExporter(args)
   
    write_progress(2, steps)

    exporter.get_network(is_licensed)

    write_progress(3, steps)

    exporter.export_network()

    if(args.gams_date_time_index is True):
            exporter.use_gams_date_index=True
    
    write_progress(4, steps)
    exporter.write_time_index()

    if args.export_by_type is True:
        exporter.export_data_using_types()
    else:
        exporter.export_data_using_attributes()

    write_progress(5, steps)
    write_output("Writing output file")

    exporter.write_file()
    return exporter

def run_gams_model(args):
    log.info("Running GAMS model .....")
    cur_time=datetime.now().replace(microsecond=0)
    write_progress(6, steps)
    working_directory=os.path.dirname(args.gms_file)
    
    if working_directory == '':
        working_directory = '.'

    model = GamsModel(args.gams_path, working_directory)
    write_progress(7, steps)
    model.add_job(args.gms_file)
    write_progress(8, steps)
    model.run()
    write_progress(9, steps)
    log.info("Running GAMS model finsihed")
    # if result file is not provided, it looks for it automatically at GAMS WD
    if args.gdx_file is None:
        log.info("Extracting results from %s.", working_directory)
        files_list=get_files_list(working_directory, '.gdx')
        for file_ in files_list:
            dt = parser.parse(files_list[file_])
            delta = (dt-cur_time).total_seconds()
            if delta>=0:
                args.gdx_file = os.path.join(working_directory, file_)
        if args.gdx_file is None:
              raise HydraPluginError('Result file is not provided/found.')

def read_results(is_licensed, args, network, connection):
    """
        Instantiate a GAMSImport class, assign the network, read the 
        gdx and gms files, update the network's data and then save
        the network.
    """
    write_progress(10, steps)
    gdximport = GAMSImporter(args, connection)

    write_progress(11, steps)
    gdximport.load_gams_file(args.gms_file)
    
    write_progress(12, steps)
    gdximport.set_network(is_licensed, network)
    
    write_progress(13, steps)
    gdximport.parse_time_index()
    
    write_progress(14, steps)
    gdximport.open_gdx_file(args.gdx_file)
    
    write_progress(15, steps)
    gdximport.read_gdx_data()
    
    write_progress(16, steps)
    gdximport.parse_variables('variables')
    gdximport.parse_variables('positive variables')
    gdximport.parse_variables('positive variable')
    gdximport.parse_variables('binary variables')
    gdximport.parse_variables('parameters')

    write_progress(17, steps)
    gdximport.assign_attr_data()
    
    write_progress(18, steps)
    gdximport.save()


def check_args(args):
    try:
        int(args.network_id)
    except (TypeError, ValueError):
        raise HydraPluginError('No network is specified.')
    try:
        int(args.scenario_id)
    except (TypeError, ValueError):
        raise HydraPluginError('No senario is specified.')

    if args.gms_file is None:
        raise HydraPluginError('Gams file is not specifed.')
    elif os.path.isfile(os.path.expanduser(args.gms_file))==False:
        raise HydraPluginError('Gams file '+args.gms_file+' not found.')
    elif args.output==None:
        args.output=get_input_file_name(args.gms_file)
        if args.output is None:
            raise HydraPluginError('No output file specified')
    elif os.path.exists(os.path.dirname(os.path.realpath(args.output)))==False:
            raise HydraPluginError('Output file directory '+ os.path.dirname(args.output)+' does not exist.')

if __name__ == '__main__':
    try:
        is_licensed=check_lic()
        steps=18
        write_progress(1, steps)
        cmd_parser = commandline_parser()
        args = cmd_parser.parse_args()
        check_args(args)
        exporter=export_network(is_licensed)
        run_gams_model(args)
        #if the mode is Auto, it will get the network from the exporter
        read_results(is_licensed, args, exporter.hydranetwork, exporter.connection)
        message="Run successfully"
        errors = []

    except HydraPluginError, e:
        log.exception(e)
        write_progress(steps, steps)
        errors = [e.message]
        message = "An error has occurred"
    except Exception as e:
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
        log.exception(e)
        message = "An unknown error has occurred"
        write_progress(steps, steps)
    
    print PluginLib.create_xml_response('GAMSAuto', args.network_id, [args.scenario_id], message=message, errors=errors)


