# (c) Copyright 2015, University of Manchester
'''
 plugin_name: Import GAMS
	          Import a gdx results file into Hydra.

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
--gams-model          -m     GMS_FILE    Full path to the GAMS model (*.gms)
                                         used for the simulation.
--gdx-file            -f     GDX_FILE   GDX file containing GAMS results


non_mandatory_args
==================

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

from datetime import datetime

gamslibpath = os.path.join('..', 'lib')
api_path = os.path.realpath(os.path.abspath(gamslibpath))
if api_path not in sys.path:
    sys.path.insert(0, api_path)
##########################

from HydraLib.HydraException import HydraPluginError
from Import import GAMSimport
from HydraLib import PluginLib

from HydraLib.PluginLib import write_progress

from HydraGAMSlib import commandline_parser_Import



import logging
log = logging.getLogger(__name__)

def import_results():
        gdximport = GAMSimport()
        write_progress(1, gdximport.steps)
        gdximport.load_network(args.network, args.scenario)
        write_progress(2, gdximport.steps)
        gdximport.load_gams_file(args.gms_file)
        write_progress(3, gdximport.steps)
        gdximport.parse_time_index()
        write_progress(4, gdximport.steps)
        gdximport.open_gdx_file(args.gdx_file)
        write_progress(5, gdximport.steps)
        gdximport.read_gdx_data()
        write_progress(6, gdximport.steps)
        gdximport.parse_variables()
        write_progress(7, gdximport.steps)
        gdximport.assign_attr_data()
        write_progress(8, gdximport.steps)
        gdximport.save()

if __name__ == '__main__':
    try:
        parser = commandline_parser_Import()
        args = parser.parse_args()
        import_results()
        message="Run successfully"
        print PluginLib.create_xml_response('GAMSImport', args.network, [args.scenario], message=message)
    except HydraPluginError, e:
          errors = [e.message]
          err = PluginLib.create_xml_response('GAMSimport', args.network, [args.scenario], errors = errors)
          print err
    except Exception, e:
         errors = [e.message]
         err = PluginLib.create_xml_response('GAMSexport', args.network, [args.scenario], errors = errors)
         print err



