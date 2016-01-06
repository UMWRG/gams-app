# GAMSApp

plugin_name: GAMSExporter
--------------------------
The plug-in provides an easy to use tool for exporting data from
HydraPlatform to custom GAMS models. The basic idea is that this plug-in
exports a network and associated data from HydraPlatform to a text file which
can be imported into an existing GAMS model using the ``$ import`` statement.

Using the commandline tool
--------------------------

**Mandatory arguments:**

====================== ======= ========== ======================================
Option                 Short   Parameter  Description
====================== ======= ========== ======================================
--network              -t      NETWORK    ID of the network that will be
                                          exported.
--scenario             -s      SCENARIO   ID of the scenario that will be
                                          exported.
--template-id          -tp     TEMPLATE   ID of the template used for exporting
                                          resources. Attributes that don't
                                          belong to this template are ignored.
--output               -o      OUTPUT     Filename of the output file.
====================== ======= ========== ======================================

**Optional arguments:**

====================== ======= ========== ======================================
Option                 Short   Parameter  Description
====================== ======= ========== ======================================
--group-nodes-by       -gn     GROUP_ATTR Group nodes by this attribute(s).
--group_links-by       -gl     GROUP_ATTR Group links by this attribute(s).
====================== ======= ========== ======================================

**Switches:**

====================== ====== =========================================
Option                 Short  Description
====================== ====== =========================================
--export_by_type       -et    Set export data based on types or based
                              on attributes only, default is export
                              data by attributes unless this option
                              is set.
====================== ====== =========================================


Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ======= ========== ======================================
--start-date           -st     START_DATE Start date of the time period used for
                                          simulation.
--end-date             -en     END_DATE   End date of the time period used for
                                          simulation.
--time-step            -dt     TIME_STEP  Time step used for simulation. The
                                          time step needs to be specified as a
                                          valid time length as supported by
                                          Hydra's unit conversion function (e.g.
                                          1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
====================== ======= ========== ======================================

**Option 2:**

====================== ======= ========== ======================================
--time-axis            -tx     TIME_AXIS  Time axis for the modelling period (a
                                          list of comma separated time stamps).
====================== ======= ========== ======================================

================================================================================
================================================================================

plugin_name: GAMSAuto
----------------------
The GAMSAutoRun plug-in provides an easy to:

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

================================================================================
================================================================================

plugin_name: GAMSImporter	          

This plug-in imports results after running a GAMS model. All results need to
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