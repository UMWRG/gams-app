#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# Export is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# Export is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with Export.  If not, see <http://www.gnu.org/licenses/>\
#


from datetime import datetime
from string import ascii_lowercase
from dateutil.parser import parse

from HydraLib.PluginLib import JSONPlugin 
from HydraLib.HydraException import HydraPluginError
from HydraLib.hydra_dateutil import guess_timefmt, date_to_string

from HydraGAMSlib import GAMSnetwork
from HydraGAMSlib import convert_date_to_timeindex

import json

import logging
log = logging.getLogger(__name__)

class GAMSExport(JSONPlugin):

    def __init__(self, args):


        if args.template_id is not None:
            self.template_id = int(args.template_id)

        self.use_gams_date_index=False
        self.network_id = int(args.network_id)
        self.scenario_id = int(args.scenario_id)
        self.template_id = int(args.template_id) if args.template_id is not None else None
        self.filename = args.output
        self.time_index = []
        
        self.connect(args)

        self.time_axis = self.get_time_axis(args.start_date,
                                  args.end_date,
                                  args.time_step,
                                  time_axis=args.time_axis)
        if args.link_name is True:
            self.links_as_name = True
        else:
            self.links_as_name = False

        self.attrs = self.connection.call('get_all_attributes', {})
        log.info("%s attributes retrieved", len(self.attrs))


    def get_network(self):
        net = self.connection.call('get_network', {'network_id':self.network_id,
                                                   'include_data': 'Y',
                                                   'template_id':self.template_id,
                                                   'scenario_ids':[self.scenario_id]})
        self.hydranetwork=net
        log.info("Network retrieved")

        if net.scenarios is not None:
            for s in net.scenarios:
                if s.id == self.scenario_id:
                    self.scenario=s


        self.network = GAMSnetwork()
        log.info("Loading net into gams network.")
        self.network.load(net, self.attrs)
        log.info("Gams network loaded")
        self.network.gams_names_for_links(use_link_name=self.links_as_name)
        log.info("Names for links retrieved")
        self.output = """* Data exported from Hydra using GAMSplugin.
* (c) Copyright 2015, University of Manchester
*
* %s: %s
* Network-ID:  %s
* Scenario-ID: %s
*******************************************************************************

""" % (self.network.name, self.network.description,
            self.network.ID, self.network.scenario_id)

    def export_network(self):
        self.get_longest_node_link_name();
        self.output += '* Network definition\n\n'
        log.info("Exporting nodes")
        self.export_nodes()
        log.info("Exporting node groups")
        self.export_node_groups()
        log.info("Exporting links")
        self.export_links()
        log.info("Exporting link groups")
        self.export_link_groups()
        log.info("Creating connectivity matrix")
        self.create_connectivity_matrix()
        log.info("Matrix created")

    def get_longest_node_link_name(self):
        node_name_len=0
        for node in self.network.nodes:
            if len(node.name)>node_name_len:
                node_name_len=len(node.name)

        self.name_len=str(node_name_len*2+5)
        self.array_len=str(node_name_len*2+15)

    def export_nodes(self):
        self.output += 'SETS\n\n'
        # Write all nodes ...
        self.output += 'i vector of all nodes /\n'
        for node in self.network.nodes:
            self.output += node.name + '\n'
        self.output += '    /\n\n'
        # ... and create an alias for the index i called j:
        self.output += 'Alias(i,j)\n\n'
        # After an 'Alias; command another 'SETS' command is needed
        self.output += '* Node types\n\n'
        self.output += 'SETS\n\n'
        # Group nodes by type
        for object_type in self.network.get_node_types(template_id=self.template_id):
            self.output += object_type + '(i) /\n'
            for node in self.network.get_node(node_type=object_type):
                self.output += node.name + '\n'
            self.output += '/\n\n'

    def export_node_groups(self):
        "Export node groups if there are any."
        node_groups = []
        group_strings = []
        for group in self.network.groups:
            group_nodes = self.network.get_node(group=group.ID)
            if len(group_nodes) > 0:
                node_groups.append(group)
                gstring = ''
                gstring += group.name + '(i) /\n'
                for node in group_nodes:
                    gstring += node.name + '\n'
                gstring += '/\n\n'
                group_strings.append(gstring)

        if len(node_groups) > 0:
            self.output += '* Node groups\n\n'
            self.output += 'node_groups vector of all node groups /\n'
            for group in node_groups:
                self.output += group.name + '\n'
            self.output += '/\n\n'
            for gstring in group_strings:
                self.output += gstring

    def export_links(self):
        self.output += 'SETS\n\n'
        # Write all links ...
        if self.links_as_name:
            self.output += 'links vector of all links /\n'
        else:
            self.output += 'links(i,j) vector of all links /\n'
        for link in self.network.links:
            if self.links_as_name:
                self.output += link.name + '\n'
            else:
                self.output += link.gams_name + '\n'
        self.output += '    /\n\n'
        # Group links by type
        self.output += '* Link types\n\n'
        for object_type in self.network.get_link_types(template_id=self.template_id):
            self.output += object_type
            if self.links_as_name:
                self.output += ' /\n'
            else:
                self.output += '(i,j) /\n'
            for link in self.network.get_link(link_type=object_type):
                self.output += link.gams_name + '\n'
            self.output += '/\n\n'

    def export_link_groups(self):
        "Export link groups if there are any."
        link_groups = []
        link_strings = []
        for group in self.network.groups:
            group_links = self.network.get_link(group=group.ID)
            if len(group_links) > 0:
                link_groups.append(group)
                lstring = ''
                lstring += group.name + '(i,j) /\n'
                for link in group_links:
                    lstring += link.gams_name + '\n'
                lstring += '/\n\n'
                link_strings.append(lstring)

        if len(link_groups) > 0:
            self.output += '* Link groups\n\n'
            self.output += 'link_groups vector of all link groups /\n'
            for group in link_groups:
                self.output += group.name + '\n'
            self.output += '/\n\n'
            for lstring in link_strings:
                self.output += lstring

    def create_connectivity_matrix(self):
        self.output += '* Connectivity matrix.\n'
        self.output += 'Table Connect(i,j)\n          '
        node_names = [node.name for node in self.network.nodes]
        for name in node_names:
            self.output += '%10s' % name
        self.output += '\n'
        conn = [[0 for node in node_names] for node in node_names]
        for link in self.network.links:
            conn[node_names.index(link.from_node)]\
                [node_names.index(link.to_node)] = 1

        connlen = len(conn)
        rows = []
        for i in range(connlen):
            rows.append('%10s' % node_names[i])
            txt = []
            for j in range(connlen):
                txt.append('%10s' % conn[i][j])
            x = "".join(txt)
            rows.append("%s%s"%(x, '\n\n'))

        self.output = self.output + "".join(rows)

    def export_data_using_types(self):
        log.info("Exporting data")
        # Export node data for each node type
        data = ['* Node data\n\n']
        self.time_table={}
        for node_type in \
                self.network.get_node_types(template_id=self.template_id):
            data.append('* Data for node type %s\n\n' % node_type)
            nodes = self.network.get_node(node_type=node_type)
            data.extend(self.export_parameters_using_type(nodes, node_type, 'scalar'))
            data.extend(self.export_parameters_using_type(nodes, node_type, 'descriptor'))
            data.extend(self.export_timeseries_using_type(nodes, node_type))
            data.extend(self.export_arrays(nodes))

        # Export link data for each node type
        data.append('* Link data\n\n')
        for link_type in self.network.get_link_types(template_id=self.template_id):
            data.append('* Data for link type %s\n\n' % link_type)
            links = self.network.get_link(link_type=link_type)
            data.extend(self.export_parameters_using_type(links, link_type, 'scalar', res_type='LINK'))
            data.extend(self.export_parameters_using_type(links, link_type,'descriptor', res_type='LINK'))
            data.extend(self.export_timeseries_using_type(links, link_type, res_type='LINK'))
            self.export_arrays(links)
        self.output = "%s%s"%(self.output, ''.join(data))
        log.info("Data exported")

    def export_data_using_attributes (self):
        log.info("Exporting data")
        # Export node data for each node
        data = ['* Nodes data\n']
        self.time_table={}
        data.extend(self.export_parameters_using_attributes(self.network.nodes,'scalar'))
        data.extend(self.export_parameters_using_attributes (self.network.nodes,'descriptor'))
        data.extend(self.export_timeseries_using_attributes (self.network.nodes))
        data.extend(self.export_arrays(self.network.nodes)) #?????

        # Export link data for each node
        data.append('* Links data\n')
        #links = self.network.get_link(link_type=link_type)
        data.extend(self.export_parameters_using_attributes (self.network.links,'scalar', res_type='LINK'))
        data.extend(self.export_parameters_using_attributes (self.network.links, 'descriptor', res_type='LINK'))
        data.extend(self.export_timeseries_using_attributes (self.network.links, res_type='LINK'))
        self.export_arrays(self.network.links) #??????
        self.output = "%s%s"%(self.output, ''.join(data))
        log.info("Data exported")

    def export_parameters_using_type(self, resources, obj_type, datatype, res_type=None):
        """
        Export scalars or descriptors.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attr_outputs = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == datatype and attr.is_var is False:
                    translated_attr_name = translate_attr_name(attr.name)
                    attr.name = translated_attr_name
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)

        if len(attributes) > 0:
            attr_outputs.append('SETS\n\n')  # Needed before sets are defined
            attr_outputs.append(obj_type + '_' + datatype + 's /\n')
            for attribute in attributes:
                attr_outputs.append(attribute.name + '\n')
            attr_outputs.append('/\n\n')
            if islink:
                if self.links_as_name:
                    obj_index = 'i,links,j,'
                else:
                    obj_index = 'i,j,'
                attr_outputs.append('Table ' + obj_type + '_' + datatype + \
                    '_data(' + obj_index + obj_type + '_' + datatype + \
                    's) \n\n')
            else:
                attr_outputs.append('Table ' + obj_type + '_' + datatype + \
                    '_data(i,' + obj_type + '_' + datatype + 's) \n\n')

            attr_outputs.append('                        ')
            for attribute in attributes:
                attr_outputs.append(' %14s' % attribute.name)
            attr_outputs.append('\n')
            for resource in resources:
                if islink:
                    attr_outputs.append('{0:24}'.format(resource.gams_name))
                else:
                    attr_outputs.append('{0:24}'.format(resource.name))
                for attribute in attributes:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.value is None or attr.dataset_type != datatype:
                        continue
                    attr_outputs.append(' %14s' % attr.value)
                attr_outputs.append('\n')
            attr_outputs.append('\n\n')
        return attr_outputs

    def classify_attributes(self, resources,datatype ):
        for resource in resources:
            for resource2 in resources:
                if resource==resource2 or len(resource.attributes)!=len(resource2.attributes):
                    continue
                    isItId=True
                for attr in resource.attributes:
                    if isItId is False:
                        break
                    length=0
                    for attr2 in resource.attributes2:
                        if attr.name != attr2.name:
                            isItId=False
                            break
                        if length == len(resource2.attributes):
                            pass
                        else:
                            length += 1


    def export_parameters_using_attributes (self, resources, datatype, res_type=None):
            """Export scalars or descriptors.
            """
            islink = res_type == 'LINK'
            attributes = []
            attr_names = []
            attr_outputs = []
            for resource in resources:
                for attr in resource.attributes:
                    if attr.dataset_type == datatype and attr.is_var is False:
                        translated_attr_name = translate_attr_name(attr.name)
                        attr.name = translated_attr_name
                        if attr.name not in attr_names:
                            attributes.append(attr)
                            attr_names.append(attr.name)
            ff='{0:<'+self.name_len+'}'
            for attribute in attributes:
                if islink:
                    attr_outputs.append('Table '+ attribute.name+'(i,j, t)\n')
                else:
                    attr_outputs.append('Table  '+ attribute.name+'(i, t)\n\n')
                attr_outputs.append(ff.format(''))
                attr_outputs.append(ff.format(0))
                attr_outputs.append('\n')
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is None or attr.value is None or attr.dataset_type != datatype:
                        continue
                    if islink:
                        attr_outputs.append(ff.format(resource.gams_name))
                    else:
                        attr_outputs.append(ff.format(resource.name))

                    attr_outputs.append(ff.format(attr.value))
                    attr_outputs.append('\n')
            return attr_outputs

    def export_timeseries_using_type(self, resources, obj_type, res_type=None):
        """Export time series.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attr_outputs = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'timeseries' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)
        if len(attributes) > 0:
            attr_outputs.append('SETS\n\n')  # Needed before sets are defined
            attr_outputs.append(obj_type + '_timeseries /\n')
            for attribute in attributes:
                attr_outputs.append(attribute.name + '\n')
            attr_outputs.append('/\n\n')
            if islink:
                attr_outputs.append('Table ' + obj_type + \
                    '_timeseries_data(t,i,j,' + obj_type + \
                    '_timeseries) \n\n       ')
            else:
                attr_outputs.append('Table ' + obj_type + \
                    '_timeseries_data(t,i,' + obj_type + \
                    '_timeseries) \n\n       ')
            col_header_length = dict()
            for attribute in attributes:
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.dataset_id is not None:
                        if islink:
                            col_header = ' %14s' % (resource.gams_name + '.'
                                                    + attribute.name)
                            col_header_length.update({(attribute, resource):
                                                      len(col_header)})
                            attr_outputs.append(col_header)
                        else:
                            col_header = ' %14s' % (resource.name + '.'
                                                    + attribute.name)
                            col_header_length.update({(attribute, resource):
                                                      len(col_header)})
                            attr_outputs.append(col_header)
            attr_outputs.append('\n')
            all_res_data={}
            #Identify the datasets that we need data for
            dataset_ids = []
            for attribute in attributes:
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.dataset_id is not None:
                        dataset_ids.append(attr.dataset_id)
                        value=json.loads(attr.value)
                        all_res_data[attr.dataset_id]=value

            #We need to get the value at each time in the specified time axis,
            #so we need to identify the relevant timestamps.
            soap_times = []
            for t, timestamp in enumerate(self.time_index):
                soap_times.append(date_to_string(timestamp))

            for t, timestamp in enumerate(self.time_index):
                attr_outputs.append('{0:<7}'.format(self.times_table[timestamp]))
                for attribute in attributes:
                    for resource in resources:
                        attr = resource.get_attribute(attr_name=attribute.name)
                        if attr is not None and attr.dataset_id is not None:
                            soap_time = date_to_string(timestamp)
                            ####
                            value=all_res_data[attr.dataset_id]
                            data=None
                            for st, data_ in value.items():
                                tmp=str(self.get_time_value(data_, soap_time))
                                if tmp is None or tmp=="None":
                                     raise HydraPluginError("Dataset %s has no data for time %s"%(attr.dataset_id, soap_time))
                                if data is not None:
                                    data = data+"-"+tmp
                                else:
                                    data = tmp


                            try:
                                data_str = ' %14f' % float(data)
                            except:
                                ff_='{0:<'+self.array_len+'}'
                                data_str = ff_.format(str(data))

                            attr_outputs.append(
                                data_str.rjust(col_header_length[(attribute, resource)]))
                attr_outputs.append('\n')
            attr_outputs.append('\n')
        return attr_outputs


    def export_timeseries_using_attributes (self, resources, res_type=None):
            """Export time series.
            """
            islink = res_type == 'LINK'
            attributes = []
            attr_names = []
            attr_outputs = []
            all_res_data={}
            for resource in resources:
                for attr in resource.attributes:
                    if attr.dataset_type == 'timeseries' and attr.is_var is False:
                        attr.name = translate_attr_name(attr.name)
                        if attr.name not in attr_names:
                            attributes.append(attr)
                            attr_names.append(attr.name)
            if len(attributes) > 0:
                #Identify the datasets that we need data for
                dataset_ids = []
                for attribute in attributes:
                    for resource in resources:
                        attr = resource.get_attribute(attr_name=attribute.name)
                        if attr is not None and attr.dataset_id is not None:
                            value=json.loads(attr.value)
                            all_res_data[attr.dataset_id]=value
                            dataset_ids.append(attr.dataset_id)

                #We need to get the value at each time in the specified time axis,
                #so we need to identify the relevant timestamps.
                soap_times = []
                for t, timestamp in enumerate(self.time_index):
                    soap_times.append(date_to_string(timestamp))

                #Get all the necessary data for all the datasets we have.
                #all_data = self.connection.call('get_multiple_vals_at_time',
                #                           {'dataset_ids':dataset_ids,
                #                           'timestamps' : soap_times})


                ff='{0:<'+self.name_len+'}'
                ff_='{0:<'+self.array_len+'}'
                t_=ff.format('')
                for t, timestamp in enumerate(self.time_index):
                    t_=t_+ff.format(self.times_table[timestamp])
                for attribute in attributes:
                    attr_outputs.append('\n*'+attribute.name)
                    if islink:
                        attr_outputs.append('\nTable '+attribute.name + ' (i,j, t)\n')
                    else:
                        attr_outputs.append('\nTable '+attribute.name + ' (i,t)\n')
                    attr_outputs.append('\n'+str(t_))
                    for resource in resources:
                        attr = resource.get_attribute(attr_name=attribute.name)
                        if attr is not None and attr.dataset_id is not None and attr.dataset_type == "timeseries":
                            if islink:
                                attr_outputs.append('\n'+ff.format(resource.gams_name))
                            else:
                                attr_outputs.append('\n'+ff.format(resource.name))

                            for t, timestamp in enumerate(self.time_index):
                                soap_time = date_to_string(timestamp)
                                value=all_res_data[attr.dataset_id]
                                data=None
                                for st, data_ in value.items():
                                    tmp=str(self.get_time_value(data_, soap_time))
                                    if tmp is None or tmp=="None":
                                         raise HydraPluginError("Dataset %s has no data for time %s"%(attr.dataset_id, soap_time))
                                    if data is not None:
                                        data=data+"-"+tmp
                                    else:
                                        data=tmp

                                try:
                                    data_str = ff.format(str(float(data)))
                                except:
                                    data_str = ff_.format(str(data))
                                attr_outputs.append(data_str)
                    attr_outputs.append('\n')
                attr_outputs.append('\n')
            return attr_outputs

    #########################
    def get_time_value(self, value, soap_time):
        data=None
        self.set_time_table(value.keys())
        soap_datetime = self.parse_date(soap_time)
        for date_time, item_value in value.items():
            if date_time.startswith("9999") or date_time.startswith('XXXX'):
                #copy the year from the soap time and put it as the first 4
                #characters of the seasonal datetime. 
                value_datetime = self.parse_date(soap_time[0:4]+date_time[4:])
                if value_datetime == soap_datetime:
                    data=item_value
                    break
            elif date_time==soap_time:
                data=item_value
                break
            else:
                if self.time_table[date_time]== soap_time:
                     data=item_value
                     break
                else:
                    pass
        if data is None:
            date=self.check_time( soap_time, sorted(value.keys()))
            if date is not None:
                data= value[date]
        if data is not None:
            if type(data) is list:
                new_data="["
                for v in data:
                    if new_data== "[":
                        new_data=new_data+str(v)
                    else:
                        new_data=new_data+" "+str(v)
                data=new_data+"]"

        return data


    def check_time(self, timestamp, times):
        for i in range (0, len(times)):
            if i==0:
                if timestamp<self.time_table[times[0]]:
                     return None
            if timestamp<self.time_table[times[i]]:

                if i>0 and timestamp>self.time_table[times[i-1]]:
                    return times[i-1]
        return self.get_last_valid_occurrence(timestamp, times, 12)

    def get_last_valid_occurrence(self, timestamp, times, switch=None):
        for date_time in times:
            if self.time_table[date_time][5:] == timestamp[5:]:
                return date_time
            elif switch is None:
                time=self.time_table[date_time][:5]+timestamp  [5:]
                re_time=self.check_time(time,times)
                if re_time is not None:
                    return re_time
        return None

    def set_time_table(self, times):
         for date_time in times:
             if  date_time in self.time_table:
                 pass
             else:
                 if date_time.startswith("XXXX"):
                     self.time_table[date_time]=date_to_string(parse(date_time.replace("XXXX","9999")))
                 else:
                     self.time_table[date_time]=date_to_string(parse(date_time))


    def get_dim(self, arr):
        dim = []
        if type(arr) is list:
            for i in range(len(arr)):
                if type(arr[i]) is list:
                    dim.append((len(arr[i])))
                else:
                    dim.append(len(arr))
                    break
        else:
             dim.append(len(arr))

        return dim

    def export_arrays(self, resources):
        """Export arrays.
        """
        attributes = []
        attr_names = []
        attr_outputs = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'array' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)
        if len(attributes) > 0:
            # We have to write the complete array information for every single
            # node, because they might have different sizes.
            for resource in resources:
                # This exporter only supports 'rectangular' arrays
                for attribute in attributes:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.value is not None:
                        
                        array=json.loads(attr.value)
                        dim = self.get_dim(array)
                        attr_outputs.append('* Array %s for node %s, ' % \
                            (attr.name, resource.name))
                        attr_outputs.append('dimensions are %s\n\n' % dim)
                        # Generate array indices
                        attr_outputs.append('SETS\n\n')
                        indexvars = list(ascii_lowercase)
                        for i, n in enumerate(dim):
                            attr_outputs.append(indexvars[i] + '_' + \
                                resource.name + '_' + attr.name +"_"+ str(i)+\
                                ' array_'+str(i)+' index /\n')
                            for idx in range(n):
                                attr_outputs.append(str(idx) + '\n')
                            attr_outputs.append('/\n\n')

                        attr_outputs.append('Table ' + resource.name + '_' + \
                            attr.name + '(')
                        for i, n in enumerate(dim):
                            attr_outputs.append(indexvars[i] + '_' + resource.name \
                                + '_' + attr.name+"_"+str(i))
                            if i < (len(dim) - 1):
                                attr_outputs.append(',')
                        attr_outputs.append(') \n\n')
                        ydim = dim[-1]

                        if len(dim)>1:
                            for y in range(ydim):
                                attr_outputs.append('{0:20}'.format(y))
                            attr_outputs.append('\n')
                        i=0  
                        for item in array:
                            attr_outputs.append("\n")
                            c=0
                            if type(item) is list:
                                attr_outputs.append(format(str(i) + " . " + str(c)))
                                i+=1
                                for value in item:
                                    if c is 0:
                                       attr_outputs.append('{0:15}'.format(value))
                                    else:
                                         attr_outputs.append('{0:20}'.format(value))
                                    c+=1
                            else:
                                attr_outputs.append(format(str(i)))
                                i+=1
                                if c is 0:
                                    attr_outputs.append('{0:15}'.format(value))
                                else:
                                    attr_outputs.append('{0:20}'.format(item))
                                c+=1
                        attr_outputs.append('\n')
                        attr_outputs.append('\n\n')
        return attr_outputs

    def write_time_index(self):
        """
            Using the time-axis determined in __init__, write the time
            axis to the output file.
        """
        log.info("Writing time index")
        self.times_table={}
        try:

            time_index = ['SETS\n\n', '* Time index\n','t time index /\n']

            t = 0
            for date in self.time_axis:
                _t=str(date.day)+"."+str(date.month)+"."+str(date.year)
                self.time_index.append(date)
                if self.use_gams_date_index is True:
                     time_index.append('%s\n' % _t)
                     self.times_table[date]=_t
                else:
                     time_index.append('%s\n' % t)
                     self.times_table[date]=t
                t += 1

            time_index.append('/\n\n')

            time_index.append('* define time steps dependent on time index (t)\n\n')
            time_index.append('Parameter timestamp(t) ;\n\n')
            #print "wrinting time"
            for t, date in enumerate(self.time_index):
                time_index.append('    timestamp("%s") = %s ;\n' % \
                    (self.times_table[date], convert_date_to_timeindex(date)))
            time_index.append('\n\n')

            self.output = self.output + ''.join(time_index)
            log.info("Time index written")
        except Exception as e:
            log.exception(e)
            raise HydraPluginError("Please check time-axis or start time, end times and time step.")


    def parse_date(self, date):
        """Parse date string supplied from the user. All formats supported by
        HydraLib.PluginLib.guess_timefmt can be used.
        """
        # Guess format of the string
        FORMAT = guess_timefmt(date)
        return datetime.strptime(date, FORMAT)

    def write_file(self):
        log.info("Writing file %s.", self.filename)
        with open(self.filename, 'w') as f:
            f.write(self.output)

def translate_attr_name(name):
    """Replace non alphanumeric characters with '_'. This function throws an
    error, if the first letter of an attribute name is not an alphabetic
    character.
    """
    if isinstance(name, str):
        translator = ''.join(chr(c) if chr(c).isalnum()
                             else '_' for c in range(256))
    elif isinstance(name, unicode):
        translator = UnicodeTranslate()

    name = name.translate(translator)

    return name


class UnicodeTranslate(dict):
    """Translate a unicode attribute name to a valid GAMS variable.
    """
    def __missing__(self, item):
        char = unichr(item)
        repl = u'_'
        if item < 256 and char.isalnum():
            repl = char
        self[item] = repl
        return repl
