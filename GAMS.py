'''
    plugin_name: GAMS Plugin
        - Export a network from Hydra to a gams input text file.
	    - Rum GAMS.
	    - Import a gdx results file into Hydra.

	mandatory_args
	==============

        name: option
        switch: -sh, value s not case sensitive 
        option to set the plugin function, the options are:
		 no witch option or A: Auto, export, run then import 
         E: export only
         I: Import only


        name: network
        switch: -t
        ID of the network where results will be imported to. This coincides with the network exported to GAMS

        name: scenario
        switch: -s
        ID of the underlying scenario used for the most recent simulation run.

        name: template
        switch: -tp</switch>
        ID of the template used for exporting resources. Attributes that don't belong to this template are ignored.</help>

        name: output
        switch: -o
        Filename of the output file.


        name: gams-model
        switch: -m
        Full path to the GAMS model (*.gms) used for the simulation.



    non_mandatory_args
    ==================
        name: gams-path
        switch: -G
        File path of the GAMS installation (the folder containing gams.exe or equivalent).
        This is only necessary if gams is installed in a non-standard location. (e.g. c:\gams)

         name>: gdx-file
        switch: -f
        GDX file containing GAMS results (needs to import data only interface)

        name: group-nodes-by
        switch: -gn
        Group nodes by this attribute(s).

        name: group-links-by
        switch: -gl
        Group links by this attribute(s).

        name: start-date
        switch: -st
        Start date of the time period used for simulation.
        name: end-date
        switch:-en
        End date of the time period used for simulation.

        name:time-step
        switch>-dt
        Time step used for simulation. The time step needs to be specified as a valid time length as supported by Hydra's unit conversion function (e.g. 1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
        name: time-axis
        switch: -tx
        Time axis for the modelling period (a list of comma separated time stamps).

        example:

         Auto (default, no -sh switch is required)

        -t 4 -s 4 -tx  2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"   -m "c:\temp
        \Demo2.gms"  -W "c:\temp"


        Importer
        -sh i  -t 4 -s 4 -f "c:\temp\Results.gdx" -m "c:\temp\Demo2.gms"

        Exporter
        -sh e -t 4 -s 4  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"



'''

import sys
import os
import time
from datetime import datetime
import argparse as ap

gamslibpath = 'lib'
api_path = os.path.realpath(os.path.abspath(gamslibpath))
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################


from HydraLib.HydraException import HydraPluginError

from GAMSexport import GAMSexport
from GAMSimport import GAMSimport
from HydraLib import PluginLib
from HydraGAMSlib import get_gams_path
from RunGamsModel import GamsModel

import logging
log = logging.getLogger(__name__)



def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Run a GAMS model using data exported from Hydra.
                    (c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information, web site will available soon",
        formatter_class=ap.RawDescriptionHelpFormatter)

    parser.add_argument('-G', '--gams-path',
                        help='Path of the GAMS installation.')

    parser.add_argument('-sh', '--switch',
                        help='option to set the plugin function, the options are: A: Auto, export, run then import (default), E: export only. I: Import only')

    parser.add_argument('-W', '--working_directory',
                        help='Path of the working directory.')
    parser.add_argument('-t', '--network',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario',
                        help='''ID of the scenario that will be exported.''')
    parser.add_argument('-tp', '--template-id',
                        help='''ID of the template to be used.''')
    parser.add_argument('-m', '--gms-file',
                        help='''Full path to the GAMS model (*.gms) used for
                        the simulation.''')
    parser.add_argument('-o', '--output',
                        help='''Output file containing exported data''')
    parser.add_argument('-nn', '--node-node', action='store_true',
                        help="""(Default) Export links as 'from_name .
                        end_name'.""")
    parser.add_argument('-ln', '--link-name', action='store_true',
                        help="""Export links as link name only. If two nodes
                        can be connected by more than one link, you should
                        choose this option.""")
    parser.add_argument('-st', '--start-date', nargs='+',
                        help='''Start date of the time period used for
                        simulation.''')
    parser.add_argument('-en', '--end-date', nargs='+',
                        help='''End date of the time period used for
                        simulation.''')
    parser.add_argument('-dt', '--time-step', nargs='+',
                        help='''Time step used for simulation.''')
    parser.add_argument('-tx', '--time-axis', nargs='+',
                        help='''Time axis for the modelling period (a list of
                        comma separated time stamps).''')
    parser.add_argument('-f', '--gdx-file',
                        help='GDX file containing GAMS results.')

    parser.add_argument('-e', '--export_only', action='store_true',
                        help='''Export data to file, don't run the model''')
    # Optional arguments
    #if(parser.export_only==False):

    parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')
    return parser

def get_files_list(directory, ext):
    '''
    return list of files on a folder with their last modified dates and times
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
        log.info("Running GAMS mode.....")
        cur_time=datetime.now()
        model = GamsModel(args.gams_path, args.working_directory)
        model.add_job(args.gms_file)
        model.run()
        log.info("Running GAMS model finsihed")
        # if result file is not provided, it locks for it automatically at GAMS WD
        if(args.gdx_file==None):
            log.info("Extract result file name.....")
            files_list=get_files_list(args.working_directory, '.gdx')
            for file_ in files_list:
                from dateutil import parser
                dt = parser.parse(files_list[file_])
                delta= (dt-cur_time).total_seconds()
                if delta>0:
                    args.gdx_file=args.working_directory+"\\"+file_
            if(args.gdx_file==None):
                  raise HydraPluginError('Result file is not specified/found.')

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
        get_res(gdximport)

    except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSimport', args.network, [args.scenario], errors = errors)
          print err

def import_results():
     try:
        gdximport = GAMSimport()
        gdximport.load_network(args.network, args.scenario)
        get_res(gdximport)

     except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSimport', args.network, [args.scenario], errors = errors)
          print err

def get_res(gdximport):
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
    if(args.switch==None):
        args.switch='A'
    else:
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
    if(args.switch=='A' or args.switch=='E'):
        exporter=export_network()
        if(args.switch=='E'):
             message="Run successfully"
             print PluginLib.create_xml_response('GAMS Exporter', args.network, [args.scenario], message=message)
             exit(0)
    if(args.switch!='I'):
        run_gams_model()
    if(args.switch=='A'):
        read_results(exporter.net)
    else:
        import_results()
    message="Run successfully"
    print PluginLib.create_xml_response('GAMS', args.network, [args.scenario], message=message)


