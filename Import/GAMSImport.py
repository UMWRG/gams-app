#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# GAMSImport is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# GAMSImport is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with GAMSImport.  If not, see <http://www.gnu.org/licenses/>\
#


'''
 plugin_name: Import GAMS
	          Import a gdx results file into Hydra.

A Hydra plug-in to import results from a GAMS model run. All results need to
be stored in a *.gdx file (the GAMS proprietary binary format). Also, variables
that will be imported need to be present in HydraPlatform, before results can
be loaded. We strongly recommend the use of a template.

Basics
~~~~~~

The GAMS import plug-in provides an easy to use tool to import results from a
model run back into HydraPlatform. It is recommended that the input data for
this GAMS model is generated using the GAMSexport plug-in. This is because
GAMSimport depends on a specific definition of the time axis and on the
presence of variables (attributes) in HydraPlatform that will hold the results
after import.


**Mandatory Arguments:**


====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to GAMS.
--scenario            -s     SCENARIO    ID of the underlying scenario used for
--gams-model          -m     GMS_FILE    Full path to the GAMS model (*.gms)
                                         used for the simulation.
--gdx-file            -f     GDX_FILE   GDX file containing GAMS results


**Server-based arguments:**

====================== ====== ========== =========================================
Option                 Short  Parameter  Description
====================== ====== ========== =========================================
--server_url           -u     SERVER_URL Url of the server the plugin will 
                                         connect to.
                                         Defaults to localhost.
--session_id           -c     SESSION_ID Session ID used by the calling software 
                                         If left empty, the plugin will attempt 
                                         to log in itself.

**Manually specifying the gams path:**

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--gams-path            -G     GAMS_PATH  File path of the GAMS installation.


GAMSimport needs a wrapper script that sets an environment variable
(``LD_LIBRARY_PATH``) before the gamsAPI library is loaded. This can not be
done at run-time because environment variables can not be set from a
running process.

Examples:
=========
python GAMSImport.py -t 4 -s 4 -f "c:\temp\Results.gdx" -m "c:\temp\Demo2.gms"


'''
import sys
import os
import argparse as ap

pythondir = os.path.dirname(os.path.realpath(__file__))
gamslibpath=os.path.join(pythondir, '..', 'lib')
api_path = os.path.realpath(gamslibpath)
if api_path not in sys.path:
    sys.path.insert(0, api_path)
##########################

from HydraLib.HydraException import HydraPluginError
from Importer import GAMSImporter, set_gams_path
from HydraLib import PluginLib

from HydraLib.PluginLib import write_progress

import logging
log = logging.getLogger(__name__)

def import_results(args):
    write_progress(1, steps)
    gdximport = GAMSImporter(args)
    write_progress(2, steps)
    gdximport.load_network()

    write_progress(3, steps)
    gdximport.load_gams_file(args.gms_file)
   
    write_progress(4, steps)
    gdximport.parse_time_index()
    
    write_progress(5, steps)
    gdximport.open_gdx_file(args.gdx_file)
    
    write_progress(6, steps)
    gdximport.read_gdx_data()
    
    write_progress(7, steps)
    gdximport.parse_variables('variables')
    gdximport.parse_variables('positive variables')
    gdximport.parse_variables('positive variable')
    
    write_progress(8, steps)
    gdximport.assign_attr_data()
    
    write_progress(9, steps)
    gdximport.save()


def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Import a gdx results file into Hydra.
                    (c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information, web site will available soon",
        formatter_class=ap.RawDescriptionHelpFormatter)

    parser.add_argument('-G', '--gams-path',
                        help='Path of the GAMS installation.')

    parser.add_argument('-t', '--network-id',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario-id',
                        help='''ID of the scenario that will be exported.''')

    parser.add_argument('-m', '--gms-file',
                        help='''Full path to the GAMS model (*.gms) used for
                        the simulation.''')
    parser.add_argument('-f', '--gdx-file',
                        help='GDX file containing GAMS results.')

    parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')

    parser.add_argument('-c', '--session_id',
                        help='''Session ID. If this does not exist, a login will be
                        attempted based on details in config.''')

    return parser


def check_args(args):
    if args.network==None:
        raise HydraPluginError('No network is specified')
    elif args.scenario==None:
        raise HydraPluginError('No senario is specified')
    elif args.gms_file is None:
        raise HydraPluginError('Gams file is not specifed')
    elif os.path.isfile(args.gms_file)==False:
        raise HydraPluginError('Gams file: '+args.gms_file+', does not exist')

if __name__ == '__main__':
    try:
        steps=9
        parser = commandline_parser()
        args = parser.parse_args()

        if os.environ.get('LD_LIBRARY_PATH') in ('', None):
            log.info("Setting LD_LIBRARY_PATH")
            set_gams_path()
            sysargs = [sys.executable]
            if sys.argv[0] == sys.executable:
                sysargs = sys.argv
            else:
                sysargs.extend(sys.argv)

            os.execv(sys.executable, sysargs)
        else:
            import_results(args)
            errors = []
            message="Import successful."

    except HydraPluginError, e:
        log.exception(e)
        errors = [e.message]
        write_progress(steps, steps)
    except Exception, e:
        log.exception(e)
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
        write_progress(steps, steps)

    print PluginLib.create_xml_response('GAMSImport', args.network_id, [args.scenario_id], errors = errors)
