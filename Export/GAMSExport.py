# (c) Copyright 2014, University of Manchester

'''
    plugin_name: GAMS Export
                 Export a network from Hydra to a gams input text file.

mandatory_args
==============


====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to GAMS.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
--template-id         -tp    TEMPLATE    ID of the template used for exporting
                                         resources. Attributes that don't
                                         belong to this template are ignored.
--output              -o    OUTPUT       Filename of the output file.

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
  -t 4 -s 4  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"

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

from Export import GAMSexport
from HydraLib import PluginLib
from HydraLib.PluginLib import write_progress
from HydraGAMSlib import commandline_parser_Export


import logging
log = logging.getLogger(__name__)

def export_network():
        template_id = None
        
        exporter = GAMSexport(args.network,
                              args.scenario,
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

if __name__ == '__main__':
    try:
        parser = commandline_parser_Export()
        args = parser.parse_args()
        link_export_flag = 'nn'
        if args.link_name is True:
            link_export_flag = 'l'
        exporter=export_network()
        message="Run successfully"
        print PluginLib.create_xml_response('GAMSExport', args.network, [args.scenario], message=message)
    except HydraPluginError, e:
        errors = [e.message]
        err = PluginLib.create_xml_response('GAMSexport', args.network, [args.scenario], errors = errors)
        print err
    except Exception, e:
        #import traceback
        #traceback.print_exc(file=sys.stdout)
        errors = [e.message]
        err = PluginLib.create_xml_response('GAMSexport', args.network, [args.scenario], errors = errors)
        print err



