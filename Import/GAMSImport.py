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



Examples:
=========
     -t 4 -s 4 -f "c:\temp\Results.gdx" -m "c:\temp\Demo2.gms"


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
from Import import GAMSImport, set_gams_path
from HydraLib import PluginLib

from HydraLib.PluginLib import write_progress

import logging
log = logging.getLogger(__name__)

def import_results(args):
        write_progress(1, steps)
        gdximport = GAMSImport(session_id=args.session_id,url=args.server_url)
        write_progress(2, steps)
        gdximport.load_network(args.network, args.scenario)

        write_progress(3, steps)
        gdximport.load_gams_file(args.gms_file)
       
        write_progress(4, steps)
        gdximport.parse_time_index()
        
        write_progress(5, steps)
        gdximport.open_gdx_file(args.gdx_file)
        
        write_progress(6, steps)
        gdximport.read_gdx_data()
        
        write_progress(7, steps)
        gdximport.parse_variables()
        
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

    parser.add_argument('-t', '--network',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario',
                        help='''ID of the scenario that will be exported.''')

    parser.add_argument('-m', '--gms-file',
                        help='''Full path to the GAMS model (*.gms) used for
                        the simulation.''')
    parser.add_argument('-f', '--gdx-file',
                        help='GDX file containing GAMS results.')

    # Optional arguments
    #if(parser.export_only==False):
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
        raise HydraPluginError('Gams file: '+args.gms_file+', is not exist')

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
            message="Run successfully"
            print PluginLib.create_xml_response('GAMSImport', args.network, [args.scenario], message=message)

    except HydraPluginError, e:
        log.exception(e)
        errors = [e.message]
        err = PluginLib.create_xml_response('GAMSImport', args.network, [args.scenario], errors = errors)
        print err
    except Exception, e:
        log.exception(e)
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
        err = PluginLib.create_xml_response('GAMSImport', args.network, [args.scenario], errors = errors)
        print err



