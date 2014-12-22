#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A Hydra plug-in to import results from a GAMS model run. All results need to
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

Options
~~~~~~~

====================== ====== ========== ======================================
Option                 Short  Parameter  Description
====================== ====== ========== ======================================
--gams-path            -G     GAMS_PATH  File path of the GAMS installation.
--network              -t     NETWORK    ID of the network where results will
                                         be imported to. Ideally this coincides
                                         with the network exported to GAMS.
--scenario             -s     SCENARIO   ID of the underlying scenario used for
                                         the most recent simulation run.
--gdx-file             -f     GDX_FILE   GDX file containing GAMS results
--gams-model           -m     GMS_FILE   Full path to the GAMS model (*.gms)
                                         used for the simulation.
====================== ====== ========== ======================================

.. note::

    GAMSimport needs a wrapper script that sets an environment variable
    (``LD_LIBRARY_PATH``) before the gamsAPI library is loaded. This can not be
    done at run-time because environment variables can not be set from a
    running process.

API docs
~~~~~~~~
"""

import os
import re
import sys
import logging
import argparse

from operator import mul

'''
if "./python" not in sys.path:
   sys.path.append("./python")
'''

from HydraLib.HydraException import HydraPluginError
from HydraLib.dateutil import ordinal_to_timestamp, date_to_string
from HydraLib import PluginLib
from HydraLib.PluginLib import JsonConnection
from decimal import Decimal
#sys.path.append("C:\\GAMS\\win32\\24.3\\apifiles\\Python\\api\\")
#import gdxcc
import traceback

from HydraGAMSlib import import_gms_data

from HydraGAMSlib import get_gams_path


log = logging.getLogger(__name__)

gdxcc=None
class GDXvariable(object):
    def __init__(self):
        self.name = None
        self.dim = 0
        self.records = 0
        self.description = None
        self.datatype = None
        self.data = []
        self.index = []

    def set_info(self, info, extinfo):
        self.name = info[1]
        self.dim = info[2]
        self.records = extinfo[1]
        self.description = extinfo[3]


class GAMSimport(object):

    def __init__(self, url=None, session_id=None):
        set_gams_path()
        import gdxcc
        self.gdxcc=gdxcc
        self.gdx_handle = gdxcc.new_gdxHandle_tp()
        rc = gdxcc.gdxCreate(self.gdx_handle, gdxcc.GMS_SSSIZE)
        if rc[0] == 0:
            raise HydraPluginError('Could not find GAMS installation.')
        self.symbol_count = 0
        self.element_count = 0
        self.gdx_variables = dict()
        self.units = dict()
        self.gdx_ts_vars = dict()
        self.network_id = None
        self.scenario_id = None
        self.network = None
        self.res_scenario = None
        self.attrs = dict()
        self.time_axis = dict()
        self.gms_data = []
        self.steps=10

        self.connection = JsonConnection(url)
        if session_id is not None:
            log.info("Using existing session %s", session_id)
            self.connection.session_id = session_id
        else:
            self.connection.login()

    def load_network(self, network_id=None, scenario_id=None):
        """
         Load network and scenario from the server.
        """
        # Use the network id specified by the user, if it is None, fall back to
        # the network id read from the gms file
        try:
            network_id = int(network_id)
        except (TypeError, ValueError):
            network_id = self.network_id
        if network_id is None:
            raise HydraPluginError("No network specified.")

        try:
            scenario_id = int(scenario_id)
        except (TypeError, ValueError):
            scenario_id = self.scenario_id
        if scenario_id is None:
            raise HydraPluginError("No scenario specified.")

        self.network = self.connection.call('get_network',
                                            {'network_id': int(network_id),
                                             'include_data': 'Y',
                                             'scenario_ids': [int(scenario_id)],
                                             'template_id': None})
        self.res_scenario = self.network.scenarios[0].resourcescenarios
        attrslist = self.connection.call('get_attributes', {})
        for attr in attrslist:
            self.attrs.update({attr.id: attr.name})

    #####################################################
    def set_network(self, network):
        """
           Load network and scenario from the server.
        """
        self.network =network
        self.res_scenario = self.network.scenarios[0].resourcescenarios
        attrslist = self.connection.call('get_attributes', {})
        for attr in attrslist:
            self.attrs.update({attr.id: attr.name})

    #####################################################
    def open_gdx_file(self, filename):
        """
        Open the GDX file and read some basic information.
        """
        if filename is None:
            raise HydraPluginError("gdx file not specified.")

        filename = os.path.abspath(filename)
        self.gdxcc.gdxOpenRead(self.gdx_handle, filename)
        x, self.symbol_count, self.element_count = \
            self.gdxcc.gdxSystemInfo(self.gdx_handle)
        if x != 1:
            raise HydraPluginError('GDX file could not be opened.')
        log.info('Importing %s symbols and %s elements.' %
                     (self.symbol_count, self.element_count))

    def read_gdx_data(self):
        """Read variables and data from GDX file.
        """
        for i in range(self.symbol_count):
            gdx_variable = GDXvariable()
            info = self.gdxcc.gdxSymbolInfo(self.gdx_handle, i + 1)
            extinfo = self.gdxcc.gdxSymbolInfoX(self.gdx_handle, i + 1)
            gdx_variable.set_info(info, extinfo)
            self.gdxcc.gdxDataReadStrStart(self.gdx_handle, i + 1)
            for n in range(gdx_variable.records):
                x, idx, data, y = self.gdxcc.gdxDataReadStr(self.gdx_handle)
                gdx_variable.index.append(idx)
                gdx_variable.data.append(data[0])
            self.gdx_variables.update({gdx_variable.name: gdx_variable})

    def load_gams_file(self, gms_file):
        """Read in the .gms file.
        """
        if gms_file is None:
            raise HydraPluginError(".gms file not specified.")
        gms_file = os.path.abspath(gms_file)
        gms_data = import_gms_data(gms_file)
        self.gms_data = gms_data.split('\n')
        self.network_id, self.scenario_id = self.get_ids_from_gms()

    def get_ids_from_gms(self):
        """Read the network and scenario ids from the GMS file. This function
        should be called when the user doesn't supply a network and/or a
        scenario id.
        """
        # Get the very first line containing 'Network-ID' and 'Scenario-ID'
        networkline = next((x for x in self.gms_data if 'Network-ID' in x),
                           None)
        scenarioline = next((x for x in self.gms_data if 'Scenario-ID' in x),
                            None)
        if networkline is not None:
            network_id = int(networkline.split(':')[1])
        else:
            network_id = None

        if scenarioline is not None:
            scenario_id = int(scenarioline.split(':')[1])
        else:
            scenario_id = None

        return network_id, scenario_id

    def parse_time_index(self):
        """
        Read the time index of the GAMS model used. This only works for
        models where data is exported from Hydra using GAMSexport.
        """
        for i, line in enumerate(self.gms_data):
            if line[0:24] == 'Parameter timestamp(t) ;':
                break
        i += 2
        line = self.gms_data[i]
        while line.split('(', 1)[0].strip() == 'timestamp':
            idx = int(line.split('"')[1])
            timestamp = ordinal_to_timestamp(Decimal(line.split()[2]))
            timestamp = date_to_string(timestamp)
            self.time_axis.update({idx: timestamp})
            i += 1
            line = self.gms_data[i]

    def parse_variables(self):
        """For all variables stored in the gdx file, check if these are time
        time series or not.
        """
        for i, line in enumerate(self.gms_data):
            if line.strip().lower() == 'variables':
                break

        i += 1
        line = self.gms_data[i]
        while line.strip() != ';':
            var = line.split()[0]
            splitvar = var.split('(', 1)
            if len(splitvar) <= 1:
                params = []
            else:
                params = splitvar[1][0:-1].split(',')
            varname = splitvar[0]
            if(re.search(r'\[(.*?)\]', line)!=None):
                self.units.update({varname:
                                re.search(r'\[(.*?)\]', line).group(1)})
            else:
                error_message="Units are missing, unit need to be added in square brackets at variable part of gams file"
                raise HydraPluginError(error_message)
                #: "+ args.gms_file)
            if 't' in params:
                self.gdx_ts_vars.update({varname: params.index('t')})

            i += 1
            line = self.gms_data[i]

    def assign_attr_data(self):
        """Assign data to all variable attributes in the network.
        """
        # Network attributes
        for attr in self.network.attributes:
            if attr.attr_is_var == 'Y':
                if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                    gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                    dataset = dict(name='GAMS import - ' + gdxvar.name,)
                    dataset['unit'] = self.units[gdxvar.name]
                    if gdxvar.name in self.gdx_ts_vars.keys():
                        dataset['type'] = 'timeseries'
                        index = []
                        for idx in gdxvar.index:
                            index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                        data = gdxvar.data
                        dataset['value'] = self.create_timeseries(index, data)
                    elif gdxvar.dim == 0:
                        data = gdxvar.data[0]
                        try:
                            data = float(data)
                            dataset['type'] = 'scalar'
                            dataset['value'] = self.create_scalar(data)
                        except ValueError:
                            dataset['type'] = 'descriptor'
                            dataset['value'] = self.create_descriptor(data)
                    elif gdxvar.dim > 0:
                        dataset['type'] = 'array'
                        dataset['value'] = self.create_array(gdxvar.index,
                                                          gdxvar.data)

                    # Add data
                    res_scen = dict(resource_attr_id = attr.id,
                                    attr_id = attr.attr_id,
                                    value = dataset)
                    self.res_scenario.append(res_scen)

        # Node attributes
        nodes = dict()
        for node in self.network.nodes:
            nodes.update({node.id: node.name})
            for attr in node.attributes:
                if attr.attr_is_var == 'Y':
                    if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                        gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                        dataset = dict(name = 'GAMS import - ' + node.name + ' ' \
                            + gdxvar.name)
                        dataset['unit'] = self.units[gdxvar.name]
                        if gdxvar.name in self.gdx_ts_vars.keys():
                            dataset['type'] = 'timeseries'
                            index = []
                            data = []
                            for i, idx in enumerate(gdxvar.index):
                                if node.name in idx:
                                    index.append(
                                        idx[self.gdx_ts_vars[gdxvar.name]])
                                    data.append(gdxvar.data[i])
                            dataset['value'] = self.create_timeseries(index, data)
                        elif gdxvar.dim == 1:
                            for i, idx in enumerate(gdxvar.index):
                                if node.name in idx:
                                    data = gdxvar.data[i]
                                    try:
                                        data = float(data)
                                        dataset['type'] = 'scalar'
                                        dataset['value'] = \
                                            self.create_scalar(data)
                                    except ValueError:
                                        dataset['type'] = 'descriptor'
                                        dataset['value'] = \
                                            self.create_descriptor(data)
                                    break
                        elif gdxvar.dim > 1:
                            dataset['type'] = 'array'
                            index = []
                            data = []
                            for i, idx in enumerate(gdxvar.index):
                                if node.name in idx:
                                    idx.pop(idx.index(node.name))
                                    index.append(idx)
                                    data.append(gdxvar.data[i])
                            dataset['value'] = self.create_array(gdxvar.index,
                                                              gdxvar.data)

                        res_scen = dict(resource_attr_id = attr.id,
                                        attr_id = attr.attr_id,
                                        value = dataset)
                        self.res_scenario.append(res_scen)

        # Link attributes
        for link in self.network.links:
            for attr in link.attributes:
                if attr.attr_is_var == 'Y':
                    fromnode = nodes[link.node_1_id]
                    tonode = nodes[link.node_2_id]
                    if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                        gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                        dataset = dict(name = 'GAMS import - ' + link.name + ' ' \
                            + gdxvar.name,
                                      locked='N')
                        dataset['unit'] = self.units[gdxvar.name]
                        if gdxvar.name in self.gdx_ts_vars.keys():
                            dataset['type'] = 'timeseries'
                            index = []
                            data = []
                            for i, idx in enumerate(gdxvar.index):
                                if fromnode in idx and tonode in idx and \
                                   idx.index(fromnode) < idx.index(tonode):
                                    index.append(
                                        idx[self.gdx_ts_vars[gdxvar.name]])
                                    data.append(gdxvar.data[i])
                            dataset['value'] = self.create_timeseries(index, data)
                        elif gdxvar.dim == 2:
                            for i, idx in enumerate(gdxvar.index):
                                if fromnode in idx and tonode in idx and \
                                   idx.index(fromnode) < idx.index(tonode):
                                    data = gdxvar.data[i]
                                    try:
                                        data = float(data)
                                        dataset['type'] = 'scalar'
                                        dataset['value'] = \
                                            self.create_scalar(data)
                                    except ValueError:
                                        dataset['type'] = 'descriptor'
                                        dataset['value'] = \
                                            self.create_descriptor(data)
                                    break
                        elif gdxvar.dim > 2:
                            dataset['type'] = 'array'
                            index = []
                            data = []
                            for i, idx in enumerate(gdxvar.index):
                                if fromnode in idx and tonode in idx and \
                                   idx.index(fromnode) < idx.index(tonode):
                                    idx.pop(idx.index(fromnode))
                                    idx.pop(idx.index(tonode))
                                    index.append(idx)
                                    data.append(gdxvar.data[i])
                            dataset['value'] = self.create_array(gdxvar.index,
                                                              gdxvar.data)

                        res_scen = dict(resource_attr_id = attr.id,
                                        attr_id = attr.attr_id,
                                        value = dataset)
                        self.res_scenario.append(res_scen)

    def create_timeseries(self, index, data):
        timeseries = {'ts_values': []}
        for i, idx in enumerate(index):
            timeseries['ts_values'].append({'ts_time':
                                            self.time_axis[int(idx)],
                                            'ts_value':
                                            float(data[i])
                                            })

        return timeseries

    def create_scalar(self, value):
        return dict(param_value = value)

    def create_array(self, index, data):
        dimension = len(index[0])
        extent = []
        for n in range(dimension):
            n_idx = []
            for idx in index:
                n_idx.append(int(idx[n]))
            extent.append(max(n_idx))

        array = 0
        for e in extent:
            new_array = [array for i in range(e)]
            array = new_array

        array = data
        while len(extent) > 1:
            i = 0
            outer_array = []
            for m in range(reduce(mul, extent[0:-1])):
                inner_array = []
                for n in range(extent[-1]):
                    inner_array.append(array[i])
                    i += 1
                outer_array.append(inner_array)
            array = outer_array
            extent = extent[0:-1]

        hydra_array = dict(arr_data = PluginLib.create_dict(array))

        return hydra_array

    def create_descriptor(self, value):
        descriptor = dict(desc_val = value)
        return descriptor

    def save(self):
        self.network.scenarios[0].resourcescenarios = self.res_scenario
        self.connection.call('update_scenario', {'scen':self.network.scenarios[0]})

def set_gams_path():
    gams_path=get_gams_path()
    if gams_path is not None:
        gams_path = os.path.abspath(gams_path)
        os.environ['LD_LIBRARY_PATH'] = gams_path
        gams_python_api_path = "%s\\apifiles\\Python\\api\\"%gams_path
        if os.environ['PYTHONPATH'].find(gams_python_api_path) < 0:
            os.environ['PYTHONPATH'] = "%s;%s"%(os.environ['PYTHONPATH'], gams_python_api_path)
            sys.path.append(gams_python_api_path)
