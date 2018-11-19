# (c) Copyright 2013-2019 University of Manchester\

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

from hydra_client.output import write_progress, write_output, create_xml_response
from hydra_base.exceptions import HydraPluginError

from hydra_gams.lib import get_gams_path, check_gams_installation

from .Importer import GAMSImporter

import logging
log = logging.getLogger(__name__)

def import_results(args):

    """
        Import results from a GDX file into a network
    """
    steps       = 9
    errors      = []
    message="Import successful."
    
    try: 
        check_gams_installation(args.gams_path)
        write_progress(1, steps)
        gdximport = GAMSImporter(args)

        write_progress(2, steps)
        gdximport.load_network(True)
        
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
        gdximport.parse_variables('binary variables')
        gdximport.parse_variables('parameters')

        write_progress(8, steps)
        gdximport.assign_attr_data()

        write_progress(9, steps)
        gdximport.save()

    except HydraPluginError as e:
        log.exception(e)
        errors = [e.message]
        write_progress(steps, steps)
        message = "An error has occurred"
    except Exception as e:
        log.exception(e)
        errors = []
        message = "An unknown error has occurred"
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
        write_progress(steps, steps)

    text = create_xml_response('GAMSImport', args.network_id, [args.scenario_id],message=message, errors=errors)
    #log.info(text)
    print(text)
