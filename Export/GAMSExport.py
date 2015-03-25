#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# GAMSExport is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# GAMSExport is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with GAMSExport.  If not, see <http://www.gnu.org/licenses/>\
#


'''
    plugin_name: GAMS Export
                 Export a network from Hydra to a gams input text file.

**Mandatory arguments:**

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

**Server-based arguments:**

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
--server_url           -u     SERVER_URL   Url of the server the plugin will 
                                           connect to.
                                           Defaults to localhost.
--session_id           -c     SESSION_ID   Session ID used by the calling software
                                           If left empty, the plugin will attempt 
                                           to log in itself.

**Manually specifying the gams installation:**
                                           
====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--gams-path            -G     GAMS_PATH  File path of the GAMS installation.
--gdx-file             -f     GDX_FILE   GDX file containing GAMS results

**Optional Grouping arguments:**

====================== ====== ========== =================================
Option                 Short  Parameter    Description
====================== ====== ========== =================================
--group-nodes-by       -gn    GROUP_ATTR Group nodes by this attribute(s).
--group_links-by       -gl    GROUP_ATTR Group links by this attribute(s).
                                           this option is set.
====================== ======= ========= ===============================

**Switches**

================= ======= ====================================
Option            Short   Description
================= ======= ====================================
--export_by_type  -et     Set export data based on types or 
                          based on attributes only, default is
                          export data by attributes unliess 
                          this option is set.
================= ======= ====================================

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
====================== ====== ========== ======================================
--time-axis            -tx    TIME_AXIS  Time axis for the modelling period (a
                                         list of comma separated time stamps).
====================== ====== ========== ======================================


Examples:
=========
  -t 4 -s 4  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 
                 2000-06-01 -o "c:\temp\demo_2.dat"

'''
import sys
import os

pythondir = os.path.dirname(os.path.realpath(__file__))
gamslibpath=os.path.join(pythondir, '..', 'lib')
api_path = os.path.realpath(gamslibpath)
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################

from HydraLib.HydraException import HydraPluginError

from Export import GAMSExport
from HydraLib import PluginLib
import argparse as ap

import logging
log = logging.getLogger(__name__)


def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Export a network from Hydra to a gams input text file.
                    (c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information, web site will available soon",
        formatter_class=ap.RawDescriptionHelpFormatter)

    parser.add_argument('-t', '--network',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario',
                        help='''ID of the scenario that will be exported.''')
    parser.add_argument('-tp', '--template-id',
                        help='''ID of the template to be used.''')

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
    parser.add_argument('-et', '--export_by_type', action='store_true',
                        help='''to export data based on types, set this otion to 'y' or 'yes', default is export data by attributes.''')

    parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')

    parser.add_argument('-c', '--session_id',
                        help='''Session ID. If this does not exist, a login will be
                        attempted based on details in config.''')
    return parser


def export_network(args):
        template_id = None

        log.info("Server url: %s",args.server_url)
        log.info("Session ID: %s",args.session_id)
        exporter = GAMSExport(steps, args.network,
                              args.scenario,
                              template_id,
                              args.output,
                              link_export_flag,
                              session_id=args.session_id,
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

        if args.export_by_type is True:
            exporter.export_data_using_types()
        else:
            exporter.export_data_using_attributes()

        exporter.write_file()

def check_args(args):
    try:
        int(args.network)
    except (TypeError, ValueError):
        raise HydraPluginError('No network is specified')
    try:
        int(args.scenario)
    except (TypeError, ValueError):
        raise HydraPluginError('No senario is specified')

    output = os.path.dirname(args.output)
    if output == '':
        output = '.'

    if  os.path.exists(output)==False:
        raise HydraPluginError('output file directory: '+ 
                               os.path.dirname(args.output)+
                               ', is not exist')

if __name__ == '__main__':

    message = None
    errors  = []
    steps=8
    try:
        parser = commandline_parser()
        args = parser.parse_args()
        check_args(args)

        link_export_flag = 'nn'
        if args.link_name is True:
            link_export_flag = 'l'
        exporter=export_network(args)
        message="Run successfully"
    except HydraPluginError, e:
        log.exception(e)
        errors = [e.message]
    except Exception, e:
        log.exception(e)
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]

    err = PluginLib.create_xml_response('GAMSExport',
                                            args.network,
                                            [args.scenario],
                                            errors = errors,
                                            message=message)
    print err


