# (c) Copyright 2013, 2014, 2015 University of Manchester\

"""A Hydra plug-in to export a network and a scenario to a set of files, which
can be imported into a GAMS model.

The GAMS import plug-in provides an easy to use tool for exporting data from
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


Input data for GAMS
-------------------

.. note::

    The main goal of this plug-in is to provide a *generic* tool for exporting
    network topologies and data to a file readable by GAMS. In most cases it
    will be necessary to adapt existing GAMS models to the naming conventions
    used by this plug-in.

Network topology
~~~~~~~~~~~~~~~~

Nodes are exported to GAMS by name and referenced by index ``i``::

    SETS

    i vector of all nodes /
    NodeA
    NodeB
    NodeC
    /

The representation of links based on node names. The set of links therefore
refers to the list of nodes. Because there are always two nodes that are
connected by a link, the list of link refers to the index of nodes::

    Alias(i,j)

    SETS

    links(i,j) vector of all links /
    NodeA . NodeB
    NodeB . NodeC
    /

In addition to links, GAMSExport provides a connectivity matrx::

    * Connectivity matrix.
    Table Connect(i,j)
                    NodeA     NodeB     NodeC
    NodeA               0         1         0
    NodeB               0         0         1
    NodeC               0         0         0


Nodes and links are also grouped by node type::

    * Node groups

    Ntype1(i) /
    NodeA
    NodeB
    /

    Ntype2(i) /
    NodeC
    /

    * Link groups

    Ltype1(i,j) /
    NodeA . NodeB
    NodeB . NodeC
    /

If you want to learn more about node and link types, please refer to the Hydra
documentation.


Datasets
~~~~~~~~

There are four types of parameters that can be exported: scalars, descriptors,
time series and arrays. Because of the way datasets are translated to GAMS
code, data used for the same attribute of different nodes and links need to be
of the same type (scalar, descriptor, time series, array). This restriction
applies for nodes and links that are of the same type. For example, ``NodeA``
and ``NodeB`` have node type ``Ntype1``, both have an attribute ``atttr_a``.
Then both values for ``attr_a`` need to be a scalar (or both need to be a
descriptor, ...). It is also possible that one node does not have a value for
one specific attribute, while other nodes of the same type do. In this case,
make sure that the GAMS mode code supports this.

Scalars and Descriptors:
    Scalars and descriptors are exported based on node and link types. All
    scalar datasets of each node (within one node type) are exported into one
    table::

        SETS

        Ntype1_scalars /
        attr_a
        attr_c
        /

        Table Ntype1_scalar_data(i, Ntype1_scalars)

                        attr_a      attr_c
        NodeA              1.0         2.0
        NodeB           3.1415         0.0

    Descriptors are handled in exactly the same way.

Time series:
    For all time series exported, a common time index is defined::

        SETS

        * Time index
        t time index /
        0
        1
        2
        /

    In case the length of each time step is not uniform and it is used in the
    model, timestamps corresponding to each time index are stored in the
    ``timestamp`` parameter::

        Parameter timestamp(t) ;

            timestamp("0") = 730851.0 ;
            timestamp("1") = 730882.0 ;
            timestamp("2") = 730910.0 ;

    Timestamps correspond to the Gregorian ordinal of the date, where the value
    of 1 corresponds to January 1, year 1.

    Similar to scalars and descriptors, time series for one node or link type
    are summarised in one table::

        SETS

        Ntype1_timeseries /
        attr_b
        attr_d
        /

        Table Ntype1_timeseries_data(t,i,Ntype1_timeseries)

                NodeA.attr_b    NodeB.attr_b    NodeA.attr_d    NodeB.attr_b
        0                1.0            21.1          1001.2          1011.4
        1                2.0            21.0          1003.1          1109.0
        2                3.0            20.9          1005.7          1213.2



Arrays:
    Due to their nature, arrays can not be summarised by node type. For every
    array that is exported a complete structure needs to be defined. It is best
    to show this structure based on an example::

        * Array attr_e for node NodeC, dimensions are [2, 2]

        SETS

        a_NodeC_attr_e array index /
        0
        1
        /

        b_NodeC_attr_e array index /
        0
        1
        /

        Table NodeC_attr_e(a_NodeC_attr_e,b_NodeC_attr_e)

                    0       1
        0         5.0     6.0
        1         7.0     8.0

    For every additional dimension a new index is created based on letters (a
    to z). This also restricts the maximum dimensions of an array to 26.  We
    are willing to increase this restriction to 676 or more as soon as somebody
    presents us with a real-world problem that needs arrays with more than 26
    dimensions.

Examples:
=========
Exporting use time axis:
 python GAMSExport.py -t 4 -s 4  -tx 2000-01-01, 2000-02-01, 2000-03-01, 2000-04-01, 2000-05-01, 2000-06-01 -o "c:\temp\demo_2.dat"

Exporting use start time, end time and time step:
  
 python GAMSExport.py -t 40 -s 40  -st 2015-04-01 -en  2039-04-01 -dt "1 yr"  -o "c:\temp\CH2M_2.dat" -et
 python GAMSExport.py -s 37 -t 37 -o "F:\work\CAL_Model\csv data for California model\excel files final\input_f.txt" -st "1922-01-01"  -en "1993-12-01" -dt "1 mon"
"""

import sys
import os


pythondir = os.path.dirname(os.path.realpath(__file__))
gamslibpath=os.path.join(pythondir, '..', 'lib')
api_path = os.path.realpath(gamslibpath)
if api_path not in sys.path:
    sys.path.insert(0, api_path)

##########################

from HydraLib.HydraException import HydraPluginError
from HydraGAMSlib import check_lic
from License import LicencePluginError

from Exporter import GAMSExporter
from HydraLib import PluginLib
import argparse as ap
from HydraLib.PluginLib import write_progress, write_output


import logging
log = logging.getLogger(__name__)


def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Export a network from Hydra to a gams input text file.
                    (c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information, web site will available soon",
        formatter_class=ap.RawDescriptionHelpFormatter)

    parser.add_argument('-t', '--network-id',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario-id',
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
    parser.add_argument('-st', '--start-date',
                        help='''Start date of the time period used for
                        simulation.''')
    parser.add_argument('-en', '--end-date',
                        help='''End date of the time period used for
                        simulation.''')
    parser.add_argument('-dt', '--time-step',
                        help='''Time step used for simulation.''')
    parser.add_argument('-tx', '--time-axis', nargs='+',
                        help='''Time axis for the modelling period (a list of
                        comma separated time stamps).''')
    parser.add_argument('-et', '--export_by_type', action='store_true',
                        help='''to export data based on types, set this otion to 'y' or 'yes', default is export data by attributes.''')

    parser.add_argument('-gd', '--gams_date_time_index', action='store_true',
                        help='''Set the time indexes to be timestamps which are compatible with gams date format (dd.mm.yyyy)''')

    parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')

    parser.add_argument('-c', '--session_id',
                        help='''Session ID. If this does not exist, a login will be
                        attempted based on details in config.''')
    return parser


def export_network(args, is_licensed):

        write_progress(2, steps)
        exporter = GAMSExporter(args)


        write_progress(3, steps)
        exporter.get_network(is_licensed)

        write_progress(4, steps)
        exporter.export_network()

        write_progress(5, steps)
        if(args.gams_date_time_index is True):
            exporter.use_gams_date_index=True

        exporter.write_time_index()

        if args.export_by_type is True:
            exporter.export_data_using_types()
        else:
            exporter.export_data_using_attributes()

        write_progress(6, steps)
        exporter.write_file()


        write_progress(7, steps)

def check_args(args):
    try:
        int(args.network_id)
    except (TypeError, ValueError):
        raise HydraPluginError('No network is specified')
    try:
        int(args.scenario_id)
    except (TypeError, ValueError):
        raise HydraPluginError('No senario is specified')

    output = os.path.dirname(args.output)
    if output == '':
        output = '.'

    if  os.path.exists(output)==False:
        raise HydraPluginError('Output file directory '+
                               os.path.dirname(args.output)+
                               'does not exist')

if __name__ == '__main__':
    is_licensed=check_lic()
    message = None
    errors  = []
    steps=7
    try:
        write_progress(1, steps)
        parser = commandline_parser()
        args = parser.parse_args()
        check_args(args)

        link_export_flag = 'nn'
        if args.link_name is True:
            link_export_flag = 'l'
        exporter=export_network(args, is_licensed)
        message="Run successfully"
    except HydraPluginError, e:
        write_progress(steps, steps)
        log.exception(e)
        errors = [e.message]
    except Exception, e:
        write_progress(steps, steps)
        log.exception(e)
        errors = []
        if e.message == '':
            if hasattr(e, 'strerror'):
                errors = [e.strerror]
        else:
            errors = [e.message]
    text = PluginLib.create_xml_response('GAMSExport',
                                            args.network_id,
                                            [args.scenario_id],
                                            errors = errors,
                                            message=message)

    #log.info(text)
    print (text)


