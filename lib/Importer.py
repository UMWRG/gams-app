
# (c) Copyright 2013, 2014, 2015 University of Manchester\

import os
import sys
from HydraLib import PluginLib

import re
import logging
import json
import copy

from operator import mul

from HydraLib.HydraException import HydraPluginError
from HydraLib.hydra_dateutil import ordinal_to_timestamp, date_to_string
from HydraLib.PluginLib import JSONPlugin
from decimal import Decimal

from HydraGAMSlib import import_gms_data, get_gams_path

log = logging.getLogger(__name__)

gdxcc=None


def get_gdx_files(filename):
    if filename is None:
        raise HydraPluginError("gdx file not specified.")
    import gdxcc

    filename = os.path.abspath(filename)
    gdx_handle=gdxcc.new_gdxHandle_tp()
    gdxcc.gdxOpenRead(gdx_handle, filename)

    x, symbol_count, element_count = \
        gdxcc.gdxSystemInfo(gdx_handle)
    print "INFO: =====>>>>>>", x, symbol_count, element_count

    if x != 1:
        raise HydraPluginError('GDX file could not be opened.')

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
        if info[1].endswith('_Pool_X'):
            self.name = info[1].replace('_Pool_X','')
        else:
            self.name = info[1]
        print "===========>Toz ", self.name
        self.dim = info[2]
        self.records = extinfo[1]
        self.description = extinfo[3]



def get_index(index_file_names):
    import gdxcc
    gdxcc = gdxcc
    gdx_handle = gdxcc.new_gdxHandle_tp()
    rc = gdxcc.gdxCreate(gdx_handle, gdxcc.GMS_SSSIZE)
    gdxcc.gdxOpenRead(gdx_handle, index_file_names)
    x, symbol_count, element_count = \
        gdxcc.gdxSystemInfo(gdx_handle)

    for i in range(symbol_count):
        gdx_variable = GDXvariable()
        info = gdxcc.gdxSymbolInfo(gdx_handle, i + 1)
        extinfo = gdxcc.gdxSymbolInfoX(gdx_handle, i + 1)
        gdx_variable.set_info(info, extinfo)
        gdxcc.gdxDataReadStrStart(gdx_handle, i + 1)
        MGA_index = []
        for n in range(gdx_variable.records):
            x, idx, data, y = gdxcc.gdxDataReadStr(gdx_handle)
            MGA_index.append(idx[0])
        return MGA_index


class GAMSImporter(JSONPlugin):

    def __init__(self, args, connection=None):
        import gdxcc
        self.gdxcc=gdxcc
        self.gdx_handle = gdxcc.new_gdxHandle_tp()
        log.info("1 =========================>"+str(self.gdx_handle))
        rc = gdxcc.gdxCreate(self.gdx_handle, gdxcc.GMS_SSSIZE)
        log.info("2 =============================>"+ str(rc))
        if rc[0] == 0:
            raise HydraPluginError('Could not find GAMS installation.')
        self.symbol_count = 0
        self.element_count = 0
        self.gdx_variables = dict()
        self.gams_units = dict()
        self.gdx_ts_vars = dict()
        self.network_id = args.network_id
        self.scenario_id = args.scenario_id
        self.network = None
        self.res_scenario = None
        self.attrs = dict()
        self.time_axis = dict()
        self.gms_data = []
        self.connection = connection


        if self.connection is None:
            self.connect(args)

        attrslist = self.connection.call('get_all_attributes', {})
        for attr in attrslist:
            self.attrs.update({attr.id: attr.name})

    def load_network(self, is_licensed, network_id=None, scenario_id=None):
        """
         Load network and scenario from the server. If the network
         has been set externally (to save getting it again) then simply
         set this.res_scenario using the existing network
        """

        # Use the network id specified by the user, if it is None, fall back to
        # the network id read from the gms file
        self.is_licensed=is_licensed
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
        if(is_licensed is False):
            if len(self.network.nodes)>20:
                raise HydraPluginError("The licence is limited demo (maximum limits are 20 nodes and 20 times steps).  Please contact software vendor (hydraplatform1@gmail.com) to get a full licence")

    #####################################################
    def set_network(self,is_licensed,  network):
        """
           Load network and scenario from the server.
        """
        self.is_licensed=is_licensed
        self.network =network
        self.res_scenario = self.network.scenarios[0].resourcescenarios
        if(is_licensed is False):
            if len(self.network.nodes)>20:
                raise HydraPluginError("The licence is limited demo (maximum limits are 20 nodes and 20 times steps).  Please contact software vendor (hydraplatform1@gmail.com) to get a full licence")
    #####################################################
    def get_mga_index(self, index_file_names):
        self.MGA_index=get_index(index_file_names)
        '''
        self.gdxcc.gdxOpenRead(self.gdx_handle, index_file_names)
        x, symbol_count, element_count = \
            self.gdxcc.gdxSystemInfo(self.gdx_handle)

        for i in range(symbol_count):
            gdx_variable = GDXvariable()
            info = self.gdxcc.gdxSymbolInfo(self.gdx_handle, i + 1)
            extinfo = self.gdxcc.gdxSymbolInfoX(self.gdx_handle, i + 1)
            gdx_variable.set_info(info, extinfo)
            self.gdxcc.gdxDataReadStrStart(self.gdx_handle, i + 1)
            self.MGA_index=[]
            for n in range(gdx_variable.records):
                x, idx, data, y = self.gdxcc.gdxDataReadStr(self.gdx_handle)
                self.MGA_index.append(idx[0])
        '''

    #####################################################
    def open_gdx_file(self, filename):
        """
        Open the GDX file and read some basic information.
        """
        if filename is None:
            raise HydraPluginError("gdx file not specified.")

        if type(filename) is list:
            print "Length: ", len(filename)
            self.is_MGS=True
            self.get_mga_index(filename[0])
            self.filename=filename[1]
        else:
            self.is_MGS = False
        #filename = os.path.abspath(filename)
        self.gdxcc.gdxOpenRead(self.gdx_handle, self.filename)
        x, self.symbol_count, self.element_count = \
            self.gdxcc.gdxSystemInfo(self.gdx_handle)
        if x != 1:
            raise HydraPluginError('GDX file could not be opened.')
        log.info('Importing %s symbols and %s elements.' %
                     (self.symbol_count, self.element_count))


    def read_gdx_data(self):
        """
           Read variables and data from GDX file.
        """
        self.gdxcc.gdxOpenRead(self.gdx_handle, self.filename)

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
            #print "name ====>", gdx_variable.name
            #print "index====>", gdx_variable.index
            #print "data ====>", gdx_variable,data


    def load_gams_file(self, gms_file):
        """Read in the .gms file.
        """
        if gms_file is None:
            raise HydraPluginError(".gms file not specified.")

        gms_file = os.path.abspath(gms_file)
        
        gms_data = import_gms_data(gms_file)
        
        self.gms_data = gms_data.split('\n')
        
        if self.network_id is None or self.scenario_id is None:
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
        time_index_type=None
        for i, line in enumerate(self.gms_data):
            #if line[0:24] == 'Parameter timestamp(t) ;':
             #  break
            if line.strip().startswith('Parameter timestamp(yr, mn, dy)'):
                time_index_type='date'
                break
            elif line.strip().startswith('Parameter timestamp(t)'):
                time_index_type='t_index'
                break
        if time_index_type is "t_index":
            i += 2
            line = self.gms_data[i]
            while line.split('(', 1)[0].strip() == 'timestamp':
                idx = int(line.split('"')[1])
                timestamp = ordinal_to_timestamp(Decimal(line.split()[2]))
                timestamp = date_to_string(timestamp)
                self.time_axis.update({idx: timestamp})
                i += 1
                line = self.gms_data[i]
        elif time_index_type is "date":
           i += 2
           line = self.gms_data[i]
           while line.strip().startswith("timestamp"):
               line_parts=line.split("=")
               timestamp=ordinal_to_timestamp(Decimal(line_parts[1].replace(";","")))
               #idx=[timestamp.year, timestamp.month, timestamp.day]
               idx=str(timestamp.year)+"."+str(timestamp.month)+"."+str(timestamp.day)
               timestamp=date_to_string(timestamp)
               self.time_axis.update({idx: timestamp})
               i += 1
               line = self.gms_data[i]

        if(self.is_licensed is False):
            if len(self.time_axis)>20:
                raise HydraPluginError("The licence is limited demo (maximum limits are 20 nodes and 20 times steps).  Please contact software vendor (hydraplatform1@gmail.com) to get a full licence")

    def parse_variables(self, variable):
        """For all variables stored in the gdx file, check if these are time
        time series or not.
        """
        for i, line in enumerate(self.gms_data):
            if line.strip().lower() == variable:
                break

        i += 1
        if(i>=len(self.gms_data)):
            return

        line = self.gms_data[i]

        while line.strip() != ';':

            if len(line.strip()) is 0:
                break
            var = line.split()[0]
            splitvar = var.split('(', 1)
            if len(splitvar) <= 1:
                params = []
            else:
                params = splitvar[1][0:-1].split(',')
            varname = splitvar[0]
            if(re.search(r'\[(.*?)\]', line)!=None):
                self.gams_units.update({varname:
                                re.search(r'\[(.*?)\]', line).group(1)})
            else:
                error_message="Units are missing, units need to be added in square brackets where the variables are specified in the .gms file, ex: v1(i, t) my variable [m^3]"
                #raise HydraPluginError(error_message)
                #: "+ args.gms_file)
            if 't' in params:
                self.gdx_ts_vars.update({varname: params.index('t')})
            elif('yr' in params and 'mn' in params and 'dy' in params):
                self.gdx_ts_vars.update({varname: params.index('dy')})
            i += 1
            line = self.gms_data[i]

    def assign_attr_data(self):
        """Assign data to all variable attributes in the network.
            """
        if self.is_MGS == False:
            self.attr_data_for_single_sol()
        else:
            self.attr_data_for_MGA()

    def get_key(self, key_, table):
        for key in table:
            if key_.lower()==key.lower():
                return key
        return None

    def attr_data_for_MGA (self):
        # Network attributes
        for attr in self.network.attributes:
            # print attr.attr_id,  attr.attr_is_var
            if attr.attr_is_var == 'Y':
                MGA_values = {}
                metadata = {}
                dataset = {}
                for j in range(0, len(self.MGA_index)):
                     print "Attr: ", self.attrs[attr.attr_id]
                     _key =self.get_key(self.attrs[attr.attr_id] ,self.gdx_variables)

                     if _key!=None:
                        gdxvar = self.gdx_variables[_key]
                        dataset ['name']='GAMS import_'+ gdxvar.name
                        dataset ['name']='GAMS import_'+ gdxvar.name

                        if (gdxvar.name in self.gams_units):
                            dataset['unit'] = self.gams_units[gdxvar.name]
                        else:
                            dataset['unit'] = '-'
                        print gdxvar.index
                        print gdxvar.data
                        print self.MGA_index[j]
                        print "===================================="
                        if gdxvar.name in self.gdx_ts_vars.keys():
                            dataset['type'] = 'timeseries'
                            index = []
                            count = 0
                            for idx in gdxvar.index:
                                if len(idx) is 2:
                                    index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                                elif len(idx) is 3:
                                    index.append('.'.join(map(str, idx)))
                            data = gdxvar.data
                            MGA_values[j]= self.create_timeseries(index, data)


                        elif gdxvar.dim == 1:
                            data = gdxvar.data[j]
                            try:
                                data_ = float(data)
                                dataset['type'] = 'scalar'
                                #dataset['value'] = json.dumps(data)
                                #MGA_values[j]=json.dumps(data)
                                MGA_values[j] = data
                            except ValueError:
                                dataset['type'] = 'descriptor'
                                #dataset['value'] = data
                                MGA_values[j]=data
                        elif gdxvar.dim > 0:
                            continue
                            dataset['type'] = 'array'
                            metadata["data_type"] = "hashtable"
                            #dataset['value'] = self.create_array(gdxvar.index, gdxvar.data)
                            MGA_values[j]= self.create_arrayfrom_Mga_results(self.MGA_index[j], gdxvar.index, gdxvar.data)
                        # Add data
                if len(MGA_values)>0:
                    dataset['value']=json.dumps(MGA_values)
                    print len(MGA_values)
                    if (len(MGA_values) == 1):
                        print "length network: ", (MGA_values)
                    print len(dataset['value']), attr.id, attr.attr_id
                    dataset['type'] = 'descriptor'
                    metadata["sol_type"] = "MGA"
                    dataset['metadata'] = json.dumps(metadata)
                    dataset['dimension'] = attr.resourcescenario.value.dimension
                    res_scen = dict(resource_attr_id=attr.id,
                                    attr_id=attr.attr_id,
                                    value=dataset)
                    self.res_scenario.append(res_scen)
        # Node attributes
        nodes = dict()
        for node in self.network.nodes:
            nodes.update({node.id: node.name})
            for attr in node.attributes:
                if attr.attr_is_var == 'Y':
                    MGA_values = {}
                    metadata = {}
                    dataset = {}
                    for j in range(0, len(self.MGA_index)):
                        _key = self.get_key(self.attrs[attr.attr_id], self.gdx_variables)
                        if _key!=None:
                            gdxvar = self.gdx_variables[_key]
                            dataset['name']='GAMS import_ ' + node.name + ' ' + gdxvar.name

                            if (gdxvar.name in self.gams_units):
                                dataset['unit'] = self.gams_units[gdxvar.name]
                            else:
                                dataset['unit'] = '-'
                            if gdxvar.name in self.gdx_ts_vars.keys():
                                dataset['type'] = 'timeseries'
                                index = []
                                data = []
                                for i, idx in enumerate(gdxvar.index):
                                    if node.name in idx:
                                        if len(idx) is 4:
                                            index.append('.'.join(map(str, idx[1:])))
                                        elif len(idx) is 2:
                                            index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                                        data.append(gdxvar.data[i])
                                #dataset['value'] = self.create_timeseries(index, data)
                                MGA_values[j]=self.create_timeseries(index, data)
                            elif gdxvar.dim == 2:
                                for i, idx in enumerate(gdxvar.index):
                                    # print idx
                                    if node.name in idx:
                                        data = gdxvar.data[i]
                                        try:
                                            data_ = float(data)
                                            dataset['type'] = 'scalar'
                                            #MGA_values[j] = json.dumps(data)
                                            MGA_values[j] = data
                                        except ValueError:
                                            dataset['type'] = 'descriptor'
                                            MGA_values[j] = data
                                        break

                            elif gdxvar.dim > 2:
                                index = []
                                data = []
                                # print  gdxvar.index
                                # print  gdxvar.data
                                MGA_values[j] = self.create_arrayfrom_Mga_results(self.MGA_index[j], gdxvar.index, gdxvar.data, node.name)
                                dataset['type'] = 'array'

                    if len(MGA_values) > 0:
                        print "======================================= Node"
                        print node.name
                        print gdxvar.name
                        metadata["sol_type"] = "MGA"
                        metadata["data_type"] = "hashtable"
                        dataset['value']=json.dumps(MGA_values)
                        print len(MGA_values)
                        if (len(MGA_values) == 1):
                            print "lengthv node: ", (MGA_values)
                        print len(dataset['value']), attr.id,attr.attr_id
                        dataset['type'] = 'descriptor'
                        dataset['metadata'] = json.dumps(metadata)
                        dataset['dimension'] = attr.resourcescenario.value.dimension
                        res_scen = dict(resource_attr_id=attr.id,
                                        attr_id=attr.attr_id,
                                        value=dataset)
                        self.res_scenario.append(res_scen)
        # Link attributes
        for link in self.network.links:
            print "Links ==================>", link.name
            for attr in link.attributes:
                if attr.attr_is_var == 'Y':
                    MGA_values = {}
                    metadata = {}
                    dataset = {}
                    for j in range(0, len(self.MGA_index)):
                        #print "Link  is found 2: ", attr.attr_id
                        #print  "======================================================"
                        fromnode = nodes[link.node_1_id]
                        tonode = nodes[link.node_2_id]
                        if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                            #dataset['value']=MGA_values
                            gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                            #print gdxvar.name
                            #print "================================================="
                            dataset['name']='GAMS import_' + link.name + ' ' + gdxvar.name
                            if (gdxvar.name in self.gams_units):
                                dataset['unit'] = self.gams_units[gdxvar.name]
                            else:
                                dataset['unit'] = '-'
                            if gdxvar.name in self.gdx_ts_vars.keys():
                                dataset['type'] = 'timeseries'
                                index = []
                                data = []
                                for i, idx in enumerate(gdxvar.index):
                                    if fromnode in idx and tonode in idx and \
                                                    idx.index(fromnode) < idx.index(tonode):
                                        if len(idx) is 5:
                                            index.append('.'.join(map(str, idx[2:])))
                                        elif len(idx) is 3:
                                            index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                                        data.append(gdxvar.data[i])
                                MGA_values[j]=self.create_timeseries(index, data)
                                #dataset['value'] = self.create_timeseries(index, data)
                            elif gdxvar.dim == 2:
                                for i, idx in enumerate(gdxvar.index):
                                    if fromnode in idx and tonode in idx and \
                                                    idx.index(fromnode) < idx.index(tonode):
                                        data = gdxvar.data[i]
                                        try:
                                            data_ = float(data)
                                            dataset['type'] = 'scalar'
                                            #MGA_values[j] = json.dumps(data)
                                            MGA_values[j] = data
                                        except ValueError:
                                            dataset['type'] = 'descriptor'
                                            MGA_values[j] = (data)
                                        break
                            elif gdxvar.dim > 2:
                                is_in = False
                                if gdxvar.dim == 3:
                                    for i, idx in enumerate(gdxvar.index):
                                        if idx[0] == link.name and fromnode in idx and tonode in idx:
                                            data = gdxvar.data[i]
                                            try:
                                                data_ = float(data)
                                                dataset['type'] = 'scalar'
                                                MGA_values[j] = (data)
                                            except ValueError:
                                                dataset['type'] = 'descriptor'
                                                MGA_values[j] = (data)
                                            is_in = True
                                            break
                                if is_in is False:
                                    # continue
                                    MGA_values[j] = self.create_arrayfrom_Mga_results(self.MGA_index[j], gdxvar.index,
                                                                         gdxvar.data, link.name)

                                    # Should be removed later
                                    dataset['type'] = 'array'
                                        #sys.exit()

                                        # dataset['value'] = self.create_array(gdxvar.index,
                                    #
                                    #
                    #
                    if len(MGA_values) > 0:
                        print "============================================="
                        print gdxvar.name
                        print link.name
                        print "============================================="
                        dataset['value']=json.dumps(MGA_values)
                        print len(MGA_values)
                        if(len(MGA_values)==1):
                            print "length link: ", (MGA_values)
                        print len(dataset['value']), attr.id,attr.attr_id
                        dataset['type'] = 'descriptor'
                        metadata["sol_type"] = "MGA"
                        metadata["data_type"] = "hashtable"
                        dataset['metadata'] = json.dumps(metadata)
                        dataset['dimension'] = attr.resourcescenario.value.dimension
                        res_scen = dict(resource_attr_id=attr.id,
                                        attr_id=attr.attr_id,
                                        value=dataset)
                        self.res_scenario.append(res_scen)
                    else:
                        print zero, gdxvar, name, link.name
                        print "============================================="


    def attr_data_for_single_sol(self):  # Network attributes
        for attr in self.network.attributes:
            # print attr.attr_id,  attr.attr_is_var
            #print  "======================================================"
            if attr.attr_is_var == 'Y':
                if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                    metadata = {}
                    gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                    dataset = dict(name='GAMS import_' + gdxvar.name, )
                    if (gdxvar.name in self.gams_units):
                        dataset['unit'] = self.gams_units[gdxvar.name]
                    else:
                        dataset['unit'] = '-'

                    if gdxvar.name in self.gdx_ts_vars.keys():
                        dataset['type'] = 'timeseries'
                        index = []
                        count = 0;
                        for idx in gdxvar.index:
                            if len(idx) is 1:
                                index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                            elif len(idx) is 3:
                                index.append('.'.join(map(str, idx)))
                        data = gdxvar.data
                        dataset['value'] = self.create_timeseries(index, data)
                    elif gdxvar.dim == 0:
                        data = gdxvar.data[0]
                        try:
                            data_ = float(data)
                            dataset['type'] = 'scalar'
                            dataset['value'] = data
                        except ValueError:
                            dataset['type'] = 'descriptor'
                            dataset['value'] = data
                    elif gdxvar.dim > 0:
                        continue
                        dataset['type'] = 'array'
                        dataset['value'] = self.create_array(gdxvar.index,
                                                             gdxvar.data)
                    # Add data
                    if dataset.has_key('value'):
                        dataset['value']=json.dumps(dataset['value'])
                        dataset['metadata'] = json.dumps(metadata)
                        dataset['dimension'] = attr.resourcescenario.value.dimension
                        res_scen = dict(resource_attr_id=attr.id,
                                        attr_id=attr.attr_id,
                                        value=dataset)
                        self.res_scenario.append(res_scen)
        # Node attributes
        nodes = dict()
        for node in self.network.nodes:
            nodes.update({node.id: node.name})
            for attr in node.attributes:
                if attr.attr_is_var == 'Y':

                    if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                        metadata = {}
                        gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                        dataset = dict(name='GAMS import_' + node.name + ' ' \
                                            + gdxvar.name)

                        if (gdxvar.name in self.gams_units):
                            dataset['unit'] = self.gams_units[gdxvar.name]
                        else:
                            dataset['unit'] = '-'
                        if gdxvar.name in self.gdx_ts_vars.keys():
                            dataset['type'] = 'timeseries'
                            index = []
                            data = []
                            for i, idx in enumerate(gdxvar.index):
                                if node.name in idx:
                                    if len(idx) is 4:
                                        index.append('.'.join(map(str, idx[1:])))
                                    elif len(idx) is 2:
                                        index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                                    data.append(gdxvar.data[i])
                            dataset['value'] = self.create_timeseries(index, data)
                        elif gdxvar.dim == 1:
                            for i, idx in enumerate(gdxvar.index):
                                # print idx
                                if node.name in idx:
                                    data = gdxvar.data[i]
                                    try:
                                        data_ = float(data)
                                        dataset['type'] = 'scalar'
                                        dataset['value'] = data
                                    except ValueError:
                                        dataset['type'] = 'descriptor'
                                        dataset['value'] = data
                                    break

                        elif gdxvar.dim > 1:
                            dataset['type'] = 'array'
                            index = []
                            data = []
                            # print  gdxvar.index
                            # print  gdxvar.data
                            inx = copy.deepcopy(gdxvar.index)
                            dat = copy.deepcopy(gdxvar.data)
                            for i, idx in enumerate(inx):
                                if node.name in idx:
                                    idx.pop(idx.index(node.name))
                                    index.append(idx)
                                    data.append(dat[i])
                                    # print "index: ",index

                                    # self.arrange_array(inx, gdxvar.data)
                                    # dataset['value'] = self.create_array(inx,
                                    #                                dat, node.name)

                            dataset['value'] = self.create_array(gdxvar.index, gdxvar.data, node.name)
                            dataset['type'] = 'descriptor'
                            metadata["data_type"] = "hashtable"

                        if dataset.has_key('value'):
                            dataset['value'] = json.dumps(dataset['value'])
                            dataset['metadata'] = json.dumps(metadata)
                            dataset['dimension'] = attr.resourcescenario.value.dimension

                            res_scen = dict(resource_attr_id=attr.id,
                                            attr_id=attr.attr_id,
                                            value=dataset)
                            self.res_scenario.append(res_scen)

        # Link attributes
        for link in self.network.links:
            for attr in link.attributes:
                if attr.attr_is_var == 'Y':
                    print "Link  is found 2: ", attr.attr_id
                    print  "======================================================"
                    fromnode = nodes[link.node_1_id]
                    tonode = nodes[link.node_2_id]
                    if self.attrs[attr.attr_id] in self.gdx_variables.keys():
                        metadata = {}
                        gdxvar = self.gdx_variables[self.attrs[attr.attr_id]]
                        print gdxvar.name
                        print "================================================="
                        dataset = dict(name='GAMS import_' + link.name + ' ' \
                                            + gdxvar.name,
                                       locked='N')
                        if (gdxvar.name in self.gams_units):
                            dataset['unit'] = self.gams_units[gdxvar.name]
                        else:
                            dataset['unit'] = '-'
                        if gdxvar.name in self.gdx_ts_vars.keys():
                            dataset['type'] = 'timeseries'
                            index = []
                            data = []
                            for i, idx in enumerate(gdxvar.index):
                                if fromnode in idx and tonode in idx and \
                                                idx.index(fromnode) < idx.index(tonode):
                                    if len(idx) is 5:
                                        index.append('.'.join(map(str, idx[2:])))
                                    elif len(idx) is 3:
                                        index.append(idx[self.gdx_ts_vars[gdxvar.name]])
                                    data.append(gdxvar.data[i])
                            dataset['value'] = self.create_timeseries(index, data)
                        elif gdxvar.dim == 2:
                            for i, idx in enumerate(gdxvar.index):
                                if fromnode in idx and tonode in idx and \
                                                idx.index(fromnode) < idx.index(tonode):
                                    data = gdxvar.data[i]
                                    try:
                                        data_ = float(data)
                                        dataset['type'] = 'scalar'
                                        dataset['value'] = data
                                    except ValueError:
                                        dataset['type'] = 'descriptor'
                                        dataset['value'] = json.dumps(data)
                                    break
                        elif gdxvar.dim > 2:
                            is_in = False
                            if gdxvar.dim == 3:
                                for i, idx in enumerate(gdxvar.index):
                                    if idx[0] == link.name and fromnode in idx and tonode in idx:
                                        data = gdxvar.data[i]
                                        try:
                                            data_ = float(data)
                                            dataset['type'] = 'scalar'
                                            dataset['value'] = json.dumps(data)
                                        except ValueError:
                                            dataset['type'] = 'descriptor'
                                            dataset['value'] = json.dumps(data)
                                        is_in = True
                                        break
                            if is_in is False:
                                # continue
                                dataset['type'] = 'array'
                                '''
                                index = []
                                data = []
                                for i, idx in enumerate(gdxvar.index):
                                    if fromnode in idx and tonode in idx and \
                                       idx.index(fromnode) < idx.index(tonode):
                                        idx.pop(idx.index(fromnode))
                                        idx.pop(idx.index(tonode))
                                        index.append(idx)
                                        data.append(gdxvar.data[i])
                                '''
                                dataset['value'] = self.create_array(gdxvar.index,
                                                                     gdxvar.data, link.name)

                                # Should be removed later
                                dataset['type'] = 'descriptor'
                                metadata["data_type"] = "hashtable"
                                # dataset['value'] = self.create_array(gdxvar.index,
                                #                                    gdxvar.data)
                        if dataset.has_key('value'):
                            dataset['value'] = json.dumps(dataset['value'])
                            dataset['metadata'] = json.dumps(metadata)
                            dataset['dimension'] = attr.resourcescenario.value.dimension
                            res_scen = dict(resource_attr_id=attr.id,
                                            attr_id=attr.attr_id,
                                            value=dataset)
                            self.res_scenario.append(res_scen)



    ########################################################################################
                            ################
    def create_arrayfrom_Mga_results(slf, soln_, index, data, res):
        elements = {}
        for i in range(0, len(index)):
            if(index[i][0]==soln_):
                #print "found ....."
                if '_' in res and len(index[i]) == 5:
                    name = index[i][1] + "_" + index[i][2] + "_" + index[i][3]
                    if name == res:
                        key = index[i][4]
                        elements[key] = data[i]
                        # if(data[i]>0):9
                        #    print "Res is not zero:", res, data[i]
                        continue
                if '_' in res and len(index[i]) == 6:
                    # print index[i]
                    name = index[i][1] + "_" + index[i][2] + "_" + index[i][3]
                    # print res, name
                    if name == res:
                        # ['bury_water_reuse', 'j_cws5', 'cambridgeshireandwestsuffolk', 'DYCP', '2015-16']
                        key = index[i][5]
                        if key in elements:
                            elements[key][index[i][4]] = data[i]
                        else:
                            val = {index[i][4]: data[i]}
                            elements[key] = val
                        # if(data[i]>0):
                        #    print "Res is not zero:", res, data[i]
                        continue
                if len(index[i]) == 4 and index[i][3].strip().lower() == res.strip().lower():
                    # ['2037-38', 'NYAA', 'norfolkrural']
                    #['file15', '2035-36', 'DYCP', 'centralessex']
                    key = index[i][1]
                    if key in elements:
                        elements[key][index[i][2]] = data[i]
                    else:
                        val = {index[i][2]: data[i]}
                        elements[key] = val

                    # val={index[i][1]: data[i]}
                    # print "Itr is found ......... ",index[i][0]," : ", val
                    elements[index[i][1]] = (val)

                elif len(index[i]) == 3 and index[i][1].strip().lower() == res.strip().lower():
                    val = {index[i][1]: data[i]}
                    # print "Itr is found ......... ",index[i][0]," : ", val

                    # elements[index[i][0]] = json.dumps(val)
                    elements[index[i][1]] = (val)

                    # elements[index[i][0]] = data[i]
        return (elements)
        # return json.dumps(elements)
    #######################################################################################
    def create_array(self, index, data, res):

        elements = {}
        for i in range(0, len(index)):
            if '_' in res and len(index[i]) == 4:
                 name = index[i][0] + "_" + index[i][1] + "_" + index[i][2]
                 if name == res:
                    key = index[i][3]
                    elements[key] = data[i]
                    # if(data[i]>0):9
                    #    print "Res is not zero:", res, data[i]
                    continue
            if '_' in res and len(index[i]) == 5:
                # print index[i]
                name = index[i][0] + "_" + index[i][1] + "_" + index[i][2]
                # print res, name
                if name == res:
                    # ['bury_water_reuse', 'j_cws5', 'cambridgeshireandwestsuffolk', 'DYCP', '2015-16']
                    key = index[i][4]
                    if key in elements:
                        elements[key][index[i][3]] = data[i]
                    else:
                        val = {index[i][3]: data[i]}
                        elements[key] = val
                    # if(data[i]>0):
                    #    print "Res is not zero:", res, data[i]
                    continue
            if len(index[i]) == 3 and index[i][2].strip().lower() == res.strip().lower():
                # ['2037-38', 'NYAA', 'norfolkrural']
                key = index[i][0]
                if key in elements:
                    elements[key][index[i][1]] = data[i]
                else:
                    val = {index[i][1]: data[i]}
                    elements[key] = val

                # val={index[i][1]: data[i]}
                # print "Itr is found ......... ",index[i][0]," : ", val
                elements[index[i][0]] = (val)

            elif len(index[i]) == 2 and index[i][1].strip().lower() == res.strip().lower():
                val = {index[i][0]: data[i]}
                # print "Itr is found ......... ",index[i][0]," : ", val

                # elements[index[i][0]] = json.dumps(val)
                elements[index[i][0]] = (val)

                # elements[index[i][0]] = data[i]
        return (elements)
        # return json.dumps(elements)

    def create_array_(self, index, data):
        elements={}
        i=0;
        for key in index:
            if type (key) is list and len(key) is 1:
                try:
                    elements[int (key[0])]=data[i]
                except Exception:
                    elements[key[0]]=data[i]
            i+=1
        values=[]
        sss=sorted(elements.keys())
        for s in sss:
            values.append(elements[s])
        return values
        #return json.dumps(values)

    def create_timeseries(self, index, data):
        timeseries = {'0': {}}
        for i, idx in enumerate(index):
             if idx.find(".") is -1:
                 timeseries['0'][self.time_axis[int(idx)]] = data [i]#json.dumps(data[i])
             else:
                 timeseries['0'][self.time_axis[idx]] = data[i]#json.dumps(data[i])

        return (timeseries)
        #return json.dumps(timeseries)
        #return (timeseries)

    def create_array_(self, index, data):
        dimension = len(index[0])
        extent = []
        for n in range(dimension):
            n_idx = []
            for idx in index:
                try:
                    n_idx.append(int(idx[n]))
                except:
                    break
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
        #print array
        #print len(array)
        #print type(array)
        hydra_array = dict(arr_data = PluginLib.create_dict(array))

        return hydra_array

    def save(self):
        self.network.scenarios[0].resourcescenarios = self.res_scenario
        #print self.res_scenario
        #with open("Output.txt", "w") as text_file:
        #text_file.write(json.dumps(self.res_scenario))
        self.connection.call('update_scenario', {'scen':self.network.scenarios[0]})

def set_gams_path_old():
    gams_path=get_gams_path()
    if gams_path is not None:
        gams_path = os.path.abspath(gams_path)
        os.environ['LD_LIBRARY_PATH'] = gams_path
        gams_python_api_path = os.path.join(gams_path, 'apifiles', 'Python', 'api')
        if os.environ.get('PYTHONPATH') is not None:
            if os.environ['PYTHONPATH'].find(gams_python_api_path) < 0:
                os.environ['PYTHONPATH'] = "%s;%s"%(os.environ['PYTHONPATH'], gams_python_api_path)
                sys.path.append(gams_python_api_path)
        else:
            os.environ['PYTHONPATH'] = gams_python_api_path
            sys.path.append(gams_python_api_path)
