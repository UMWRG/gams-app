# check how to get attribute type for resources ........
# excel app needs to be checked also for that purpose .....
# (c) Copyright 2013, 2014, 2015, 2016 University of Manchester\

from string import ascii_lowercase

from HydraLib.PluginLib import JSONPlugin
from HydraLib.HydraException import HydraPluginError
from HydraLib.hydra_dateutil import reindex_timeseries

from HydraGAMSlib import GAMSnetwork
from HydraGAMSlib import convert_date_to_timeindex

from decimal import Decimal

import json

import logging
log = logging.getLogger(__name__)

class GAMSExporter(JSONPlugin):
    def __init__(self, args):
        if args.template_id is not None:
            self.template_id = int(args.template_id)

        self.use_gams_date_index=False
        self.network_id = int(args.network_id)
        self.scenario_id = int(args.scenario_id)
        self.template_id = int(args.template_id) if args.template_id is not None else None
        self.filename = args.output
        self.time_index = []
        self.time_axis =None
        self.sets=[]
        self.hashtables_keys={}
        self.output=''
        self.added_pars=[]
        self.junc_node={}

        self.connect(args)
        if args.time_axis is not None:
            args.time_axis = ' '.join(args.time_axis).split(' ')

        if(args.start_date is not None and args.end_date is not None and args.time_step is not None):
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

    def get_network(self, is_licensed):
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

        self.resourcescenarios_ids=get_resourcescenarios_ids(net.scenarios[0].resourcescenarios)
        self.network = GAMSnetwork()
        log.info("Loading net into gams network.")
        self.network.load(net, self.attrs)
        if (self.time_axis == None):
            if ('start_time' in net.scenarios[0] and 'time_step' in net.scenarios[0] and 'end_time' in net.scenarios[
                0]):
                self.time_axis = self.get_time_axis(net.scenarios[0]['start_time'],
                                               net.scenarios[0]['end_time'],
                                               net.scenarios[0]['time_step'],
                                               time_axis=None)
        if (self.time_axis is None):
            self.get_time_axix_from_attributes_values(self.network.nodes)
        if (self.time_axis is None):
            self.get_time_axix_from_attributes_values(self.network.links)
        self.get_junc_link()
        if (len(self.junc_node) > 0):
            self.use_jun = True
        else:
            self.use_jun = False
        if(is_licensed is False):
            if len(self.network.nodes)>20:
                raise HydraPluginError("The licence is limited demo (maximum limits are 20 nodes and 20 times steps).  Please contact software vendor (hydraplatform1@gmail.com) to get a full licence")
            if self.time_axis is not None and len (self.time_axis)>20:
                raise HydraPluginError("The licence is limited demo (maximum limits are 20 nodes and 20 times steps).  Please contact software vendor (hydraplatform1@gmail.com) to get a full licence")
        log.info("Gams network loaded")
        self.network.gams_names_for_links(use_link_name=self.links_as_name)
        log.info("Names for links retrieved")
        self.sets = """* Data exported from Hydra using GAMSplugin.
* (c) Copyright 2015, University of Manchester
*
* %s: %s
* Network-ID:  %s
* Scenario-ID: %s
*******************************************************************************
""" % (self.network.name, self.network.description,
            self.network.ID, self.network.scenario_id)

    def check_links_between_nodes(self):
        for link in self.network.links:
            for link_ in self.network.links:
                if(link== link_):
                    continue
                if(link_.to_node==link.to_node and link_.from_node==link.from_node):
                    self.links_as_name = True
                    break

    def export_network(self):
        if self.links_as_name is False and len(self.junc_node)==0:
            self.check_links_between_nodes()
        self.get_longest_node_link_name();
        self.sets += '* Network definition\n\n'
        log.info("Exporting nodes")
        self.export_nodes()
        log.info("Exporting node groups")
        self.export_node_groups()
        log.info("Exporting links")
        self.export_links()
        log.info("Exporting link groups")
        self.export_link_groups()
        log.info("Creating connectivity matrix")
        #self.create_connectivity_matrix()
        log.info("Writing nodes coordinates")
        self.export_resources_coordinates()
        log.info("Matrix created")

    def get_longest_node_link_name(self):
        node_name_len=0
        for node in self.network.nodes:
            if len(node.name)>node_name_len:
                node_name_len=len(node.name)

        self.name_len=str(node_name_len*2+5)
        self.array_len=str(node_name_len*2+15)

    def export_nodes(self):
        self.sets += 'SETS\n\n'
        # Write all nodes ...
        self.sets += 'i vector of all nodes /\n'
        for node in self.network.nodes:
            self.sets += node.name + '\n'
        self.sets += '    /\n\n'
        # ... and create an alias for the index i called j:
        self.sets += 'Alias(i,j)\n\n'
        # After an 'Alias; command another 'SETS' command is needed
        self.sets += '* Node types\n\n'
        self.sets += 'SETS\n\n'
        # Group nodes by type
        self.sets += 'nodes_types   /\n'
        for object_type in self.network.get_node_types(template_id=self.template_id):
            self.sets += object_type+'\n'
        self.sets += '/\n\n'

        for object_type in self.network.get_node_types(template_id=self.template_id):
            self.sets += object_type + '(i) /\n'
            for node in self.network.get_node(node_type=object_type):
                self.sets += node.name + '\n'
            self.sets += '/\n\n'

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
            self.sets += '* Node groups\n\n'
            self.sets += 'node_groups vector of all node groups /\n'
            for group in node_groups:
                self.sets += group.name + '\n'
            self.sets += '/\n\n'
            for gstring in group_strings:
                self.sets += gstring


    def get_junc_link(self):
        for link in self.network.links:
                    res=link.get_attribute(attr_name="jun_node")
                    if res is None or res.value is None:
                          continue
                    self.junc_node[link.name]=res.value

    def export_links(self):
        self.sets += 'SETS\n\n'
        # Write all links ...
        if self.links_as_name:
            self.sets += 'link_name /\n'
            for link in self.network.links:
                self.sets +=link.name+'\n'
            self.sets += '/\n\n'
            self.sets += 'links (link_name) vector of all links /\n'
        else:
            if self.use_jun==True:
                self.sets += 'links(i, jun_set, j) vector of all links /\n'
            else:
                self.sets += 'links(i,j) vector of all links /\n'
        for link in self.network.links:
            if self.links_as_name:
                self.sets += link.name +'\n'
            else:
                if(self.use_jun==True):
                    jun=self.junc_node[link.name]
                    self.sets += link.from_node+' . ' +jun+' . '+link.to_node+ '\n'
                else:
                    self.sets += link.gams_name + '\n'
        self.sets += '    /\n\n'
        # Group links by type
        self.sets += '* Link types\n\n'
        self.sets += 'links_types   /\n'
        for object_type in self.network.get_link_types(template_id=self.template_id):
            self.sets += object_type + '\n'
        self.sets += '/\n\n'

        for object_type in self.network.get_link_types(template_id=self.template_id):
            self.sets += object_type
            if self.links_as_name:
                self.sets +=  'link_name /\n'
            else:
                if self.use_jun == True:
                    self.sets += 'links(i, jun_set, j) vector of '+object_type+' links /\n'
                else:
                    self.sets += '(i,j) /\n'
            for link in self.network.get_link(link_type=object_type):
                if self.links_as_name:
                    self.sets += link.name + '\n'
                else:
                    if self.use_jun == True:
                        jun = self.junc_node[link.name]
                        self.sets += link.from_node + ' . ' + jun + ' . ' + link.to_node + '\n'
                    else:
                        self.sets += link.gams_name + '\n'
            self.sets += '/\n\n'

    def export_link_groups(self):
        "Export link groups if there are any."
        self.sets += '* Link groups ....\n\n'
        link_groups = []
        link_strings = []
        links_groups_members={}

        for group in self.network.groups:
            group_links = []
            for link in self.network.links:
                if group.ID in link.groups:
                    group_links.append(link)
                else:
                    for item in link.groups:
                        if item ==group.ID or group.ID in item:
                            group_links.append(link)
                            break

            #group_links = self.network.get_link(group=group.ID)
            if len(group_links) > 0:
                links_groups_members[group.name]=group_links
                #print "It is biggere thank zero...."
                link_groups.append(group)
                lstring = ''
                if self.links_as_name:
                    lstring +=  group.name+' /\n'
                else:
                    if self.use_jun == True:
                        lstring += group.name+ '(i, jun_set, j) vector links group /\n'
                    else:
                        lstring += '(i,j) /\n'
                #lstring += group.name + '(i,j) /\n'
                for link in group_links:
                    if self.links_as_name:
                        lstring += link.name + '\n'
                    else:
                        if self.use_jun == True:
                            jun = self.junc_node[link.name]
                            lstring += link.from_node + ' . ' + jun + ' . ' + link.to_node + '\n'
                        else:
                            lstring += link.gams_name + '\n'
                    #lstring += link.gams_name + '\n'
                lstring += '/\n\n'
                link_strings.append(lstring)

        EXCLUSIVITY_SET=[]
        DEPENDENCY_SET=[]
        if len(link_groups) > 0:
            self.output += '* Link groups\n\n'
            self.sets += 'link_groups vector of all link groups /\n'
            for group in link_groups:
                if group.name.lower().startswith("dependency"):
                    DEPENDENCY_SET.append(group.name)
                if group.name.lower().startswith("exclusivity"):
                    EXCLUSIVITY_SET.append(group.name)
                self.sets += group.name + '\n'
            self.sets += '/\n\n'
            for lstring in link_strings:
                self.sets += lstring

        # the following to be used with AW EBSD
        self.links_groups_members=links_groups_members
        if len (EXCLUSIVITY_SET)>0:
            self.EXCLUSIVITY_SET = EXCLUSIVITY_SET
            self.sets += 'EXCLUSIVITY_SET /\n'
            for item in EXCLUSIVITY_SET:
                self.sets += item + '\n'
            self.sets += '/\n\n'

        if len(DEPENDENCY_SET)>0:
            self.DEPENDENCY_SET = DEPENDENCY_SET
            self.sets += 'DEPENDENCY_SET /\n'
            for item in DEPENDENCY_SET:
                self.sets += item + '\n'
            self.sets += '/\n\n'


    def create_connectivity_matrix(self):
        ff='{0:<'+self.name_len+'}'

        self.output += '* Connectivity matrix.\n'
        self.output += 'Table Connect(i,j)\n'
        self.output +=ff.format('')
        node_names = [node.name for node in self.network.nodes]
        for name in node_names:
            self.output += ff.format( name)
        self.output += '\n'
        conn = [[0 for node in node_names] for node in node_names]
        for link in self.network.links:
            conn[node_names.index(link.from_node)]\
                [node_names.index(link.to_node)] = 1

        connlen = len(conn)
        rows = []
        for i in range(connlen):
            rows.append(ff.format( node_names[i]))
            txt = []
            for j in range(connlen):
                txt.append(ff.format( conn[i][j]))
            x = "".join(txt)
            rows.append("%s%s"%(x, '\n\n'))

        self.output = self.output + "".join(rows)

    def export_resources_coordinates(self):
        ff='{0:<'+self.name_len+'}'
        threeplaces = Decimal('0.001')
        self.output += ('\nParameter x_coord (i)/\n')

        for node in self.network.nodes:
            self.output += (ff.format(node.name))
            x_coord = Decimal(node.X).quantize(threeplaces)
            self.output += (ff.format(x_coord))
            self.output += ('\n')

        self.output += ('/;\n\nParameter y_coord (i)/\n')
        for node in self.network.nodes:
            self.output += (ff.format(node.name))
            y_coord = Decimal(node.Y).quantize(threeplaces)
            self.output += (ff.format(y_coord))
            self.output += ('\n')
        self.output += ('/;\n\n');

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
            # data.extend(self.export_arrays(nodes))
            data.extend(self.export_hashtable(nodes))

        # Export link data for each node type
        data.append('* Link data\n\n')
        for link_type in self.network.get_link_types(template_id=self.template_id):
            data.append('* Data for link type %s\n\n' % link_type)
            links = self.network.get_link(link_type=link_type)
            data.extend(self.export_parameters_using_type(links, link_type, 'scalar', res_type='LINK'))
            data.extend(self.export_parameters_using_type(links, link_type,'descriptor', res_type='LINK'))
            data.extend(self.export_timeseries_using_type(links, link_type, res_type='LINK'))
            #self.export_arrays(links)
            data.extend(self.export_hashtable(links))
        self.output = "%s%s"%(self.output, ''.join(data))
        log.info("Data exported")

    def export_data_using_attributes (self):
        log.info("Exporting data")
        # Export node data for each node

        self.time_table={}
        data = ['\n* Network data\n']
        data.extend(self.export_parameters_using_attributes([self.network],'scalar',res_type='NETWORK'))
        self.export_descriptor_parameters_using_attributes([self.network])

        data.extend(self.export_hashtable([self.network],res_type='NETWORK'))

        data.append('\n\n\n* Nodes data\n')
        data.extend(self.export_parameters_using_attributes(self.network.nodes,'scalar'))
        self.export_descriptor_parameters_using_attributes(self.network.nodes)
        #data.extend(self.export_parameters_using_attributes (self.network.nodes,'descriptor'))
        data.extend(self.export_timeseries_using_attributes (self.network.nodes))
        #data.extend(self.export_arrays(self.network.nodes)) #?????
        data.extend(self.export_hashtable(self.network.nodes))

        # Export link data for each node
        data.append('\n\n\n* Links data\n')
        #links = self.network.get_link(link_type=link_type)
        data.extend(self.export_parameters_using_attributes (self.network.links,'scalar', res_type='LINK'))
        self.export_descriptor_parameters_using_attributes(self.network.links)
        #data.extend(self.export_parameters_using_attributes (self.network.links, 'descriptor', res_type='LINK'))
        data.extend(self.export_timeseries_using_attributes (self.network.links, res_type='LINK'))
        #self.export_arrays(self.network.links) #??????
        data.extend(self.export_hashtable(self.network.links, res_type = 'LINK'))
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
                    if self.use_jun==True:
                        obj_index = 'i, jun_set, j,'
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
            counter_=0
            attributes = []
            attr_names = []
            attr_outputs = []
            for resource in resources:
                for attr in resource.attributes:
                    if attr.dataset_type == datatype and attr.is_var is False:
                        translated_attr_name = translate_attr_name(attr.name)
                        res = resource.get_attribute(attr_name=attr.name)
                        attr.name = translated_attr_name
                        if attr.name not in attr_names:
                            attributes.append(attr)
                            attr_names.append(attr.name)

            ff='{0:<'+self.name_len+'}'
            if datatype=="descriptor":
                title="set"
            else:
                if res_type =='NETWORK':
                    title= "Scalar"
                else:
                    title="Parameter"
            for attribute in attributes:
                if islink == True:
                    if self.links_as_name:
                        attr_outputs.append('\n'+title+' '+ attribute.name+'(link_name)\n')
                    else:
                        if self.use_jun ==True:
                            attr_outputs.append('\n' + title + ' ' + attribute.name + '(i,jun_set,j)\n')
                        else:
                            attr_outputs.append('\n'+title+ ' '+ attribute.name+'(i,j)\n')
                elif(res_type is 'NETWORK'):
                     attr_outputs.append('\n'+title +' '+ attribute.name+'\n')
                else:
                    attr_outputs.append('\n'+title+' '+ attribute.name+'(i)\n')

                attr_outputs.append(ff.format('/'))
                #attr_outputs.append(ff.format(0))
                attr_outputs.append('\n')

                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)

                    if attr is None or attr.value is None or attr.dataset_type != datatype:
                        continue
                    add = resource.name + "_" + attr.name
                    if add in self.added_pars:
                        continue
                    counter_+=1
                    if islink:
                        if self.links_as_name:
                            attr_outputs.append(ff.format(resource.name+ '.'+resource.from_node+'.'+resource.to_node))
                            attr_outputs.append(ff.format('\t'))
                        else:
                            if self.use_jun == True:
                                jun = self.junc_node[resource.name]
                                attr_outputs.append(ff.format(resource.from_node+' . '+jun+' . '+ resource.to_node))
                            else:
                                attr_outputs.append(ff.format(resource.gams_name))
                    elif(res_type is 'NETWORK'):
                         pass
                    else:
                        attr_outputs.append(ff.format(resource.name))

                    attr_outputs.append(ff.format(attr.value))
                    attr_outputs.append('\n')

                attr_outputs.append(ff.format('/;\n'))
            if(counter_>0):
                return attr_outputs
            else:
                return []

    def export_descriptor_parameters_using_attributes(self, resources):
        """Export scalars or descriptors.
        """
        datatype='descriptor'
        counter_ = 0
        attributes = []
        attr_names = []
        attr_outputs = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == datatype and attr.is_var is False:
                    translated_attr_name = translate_attr_name(attr.name)
                    res = resource.get_attribute(attr_name=attr.name)
                    attr.name = translated_attr_name
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)
        for attribute in attributes:
            list = []

            # attr_outputs.append(ff.format(0))
            attr_outputs.append('\n')

            for resource in resources:
                attr = resource.get_attribute(attr_name=attribute.name)

                if attr is None or attr.value is None or attr.dataset_type != datatype:
                    continue
                if attr.value not in list:
                    list.append(attr.value)


            if (list > 0):
                self.hashtables_keys[attribute.name]=list


    def export_timeseries_using_type(self, resources, obj_type, res_type=None):
        """Export time series.
        """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attr_outputs = []

        #Identify only the timeseries values we're interested in.
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
            resource_data_cache = {}
            for timestamp in self.time_index:
                attr_outputs.append('{0:<7}'.format(self.times_table[timestamp]))

                for attribute in attributes:
                    for resource in resources:
                        attr = resource.get_attribute(attr_name=attribute.name)

                        #Only interested in attributes with data
                        if attr is None or attr.dataset_id is None:
                            continue

                        #Pass in the JSON value and the list of timestamps,
                        #Get back a dictionary with values, keyed on the timestamps
                        try:
                            all_data = resource_data_cache.get((resource.name, attribute.name))
                            if all_data is None:
                                all_data = self.get_time_value(attr.value, self.time_index)
                                resource_data_cache[(resource.name, attribute.name)] = all_data
                        except Exception, e:
                            log.exception(e)
                            all_data = None

                        if all_data is None:
                            raise HydraPluginError("Error finding value attribute %s on"
                                                  "resource %s"%(attr.name, resource.name))

                        #Get each value in turn and add it to the line
                        data = all_data[timestamp]

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

    def get_time_axix_from_attributes_values(self, resources):
        attributes = []
        attr_names = []
        t_axis = []
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'timeseries' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name not in attr_names:
                        attributes.append(attr)
                        attr_names.append(attr.name)

        for attribute in attributes:
            for resource in resources:
                attr = resource.get_attribute(attr_name=attribute.name)
                if (attr != None):
                    vv = json.loads(attr.value)
                    for key in vv.keys():
                        for date in vv[key].keys():
                            if '9999' in date:
                                break
                            t_axis.append(date)
                if len(t_axis) > 0:
                    self.time_axis = self.get_time_axis(None,
                                                        None,
                                                        None,
                                                        time_axis=t_axis)
                    return

    def export_timeseries_using_attributes(self, resources, res_type=None):
            """Export time series.
            """
            islink = res_type == 'LINK'
            attributes = []
            attr_names = []
            attr_outputs = []
            counter_ = 0

            # Identify all the timeseries attributes and unique attribute
            # names
            for resource in resources:
                for attr in resource.attributes:
                    if attr.dataset_type == 'timeseries' and attr.is_var is False:
                        attr.name = translate_attr_name(attr.name)
                        if attr.name not in attr_names:
                            attributes.append(attr)
                            attr_names.append(attr.name)

            ff = '{0:<' + self.name_len + '}'
            t_ = ff.format('')

            for timestamp in self.time_index:
                t_ = t_ + ff.format(self.times_table[timestamp])

            for attribute in attributes:
                if(self.time_axis is None):
                    raise HydraPluginError("Missing time axis or start date, end date and time step or bad format")

                attr_outputs.append('\n*'+attribute.name)

                if islink:
                    if self.links_as_name:
                        attr_outputs.append('\nTable '+attribute.name + ' (link_name,i,j')
                    else:
                        attr_outputs.append('\nTable '+attribute.name + ' (i,j')
                else:
                    attr_outputs.append('\nTable '+attribute.name + ' (i')

                if self.use_gams_date_index is True:
                    attr_outputs.append(', yr, mn, dy)\n')
                else:
                    attr_outputs.append(', t)\n')

                if self.links_as_name:
                    attr_outputs.append('\n'+ff.format(''))
                    attr_outputs.append(str(t_))
                else:
                    attr_outputs.append('\n'+str(t_))

                #Identify the datasets that we need data for
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)

                    #Only interested in attributes with data and that are timeseries
                    if attr is None or attr.dataset_id is None or attr.dataset_type != "timeseries":
                        continue
                    add = resource.name + "_" + attr.name
                    if add in self.added_pars:
                        continue
                    counter_+=1

                    #Pass in the JSON value and the list of timestamps,
                    #Get back a dictionary with values, keyed on the timestamps
                    try:
                        all_data = self.get_time_value(attr.value, self.time_index)
                    except Exception, e:
                        log.exception(e)
                        all_data = None

                    if all_data is None:
                        raise HydraPluginError("Error finding value attribute %s on"
                                              "resource %s"%(attr.name, resource.name))
                    if islink:
                        if self.links_as_name:
                            attr_outputs.append('\n'+ff.format(resource.name+ '.'+resource.from_node+'.'+resource.to_node))
                            attr_outputs.append(ff.format('\t'))

                        else:
                            attr_outputs.append('\n'+ff.format(resource.gams_name))
                    else:
                        attr_outputs.append('\n'+ff.format(resource.name))

                    #Get each value in turn and add it to the line
                    for timestamp in self.time_index:
                        tmp = all_data[timestamp]

                        if isinstance(tmp, list):
                            data="-".join(tmp)
                            ff_='{0:<'+self.array_len+'}'
                            data_str = ff_.format(str(data))
                        else:
                            data=str(tmp)
                            data_str = ff.format(str(float(data)))
                        attr_outputs.append(data_str)

                attr_outputs.append('\n')

            attr_outputs.append('\n')
            if(counter_>0):
                return attr_outputs
            else:
                return []

    def get_time_value(self, value, timestamps):
        '''
            get data for timmp
            :param a JSON string
            :param a timestamp or list of timestamps (datetimes)
            :returns a dictionary, keyed on the timestamps provided.
            return None if no data is found
        '''
        converted_ts = reindex_timeseries(value, timestamps)

        #For simplicity, turn this into a standard python dict with
        #no columns.
        value_dict = {}

        val_is_array = False
        if len(converted_ts.columns) > 1:
            val_is_array = True

        if val_is_array:
            for t in timestamps:
                value_dict[t] = converted_ts.loc[t].values.tolist()
        else:
            first_col = converted_ts.columns[0]
            for t in timestamps:
                value_dict[t] = converted_ts.loc[t][first_col]

        return value_dict

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


    def compare_sets(self, key, key_):
        for item_ in key_:
            if(item_ not in key):
                key.append(item_)
        if(len(key_)!=len(key)):
            to_be_aded=[]
            for i in range (0, len(key_)):
                item_ =key_[i]
            for j in range(0, len(key)):
                item=key[j]
                #for item in key:
                if str(item).strip().lower()==str(item_).strip().lower():
                    continue
                if j==len(key)-1:
                    to_be_aded.append(item)
            key=key+to_be_aded
        return key


    def export_hashtable (self, resources,res_type=None):
        """Export hashtable which includes seasonal data .
                    """
        islink = res_type == 'LINK'
        attributes = []
        attr_names = []
        attr_outputs = []
        id='default'
        ids={}
        ids_key={}
        data_types={}
        sets_namess={}
        # Identify all the timeseries attributes and unique attribute
        # names
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'array' and attr.is_var is False:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name  in ids.keys():
                        ar=ids[attr.name ]
                    else:
                        ar=[]
                        ids[attr.name ]=ar
                    ar.append({resource:self.resourcescenarios_ids[attr.resource_attr_id]})
                    if attr.name not in data_types.keys():
                        type_=json.loads(self.resourcescenarios_ids[attr.resource_attr_id].value.metadata)
                        if "data_type" in type_.keys():
                            data_types[attr.name]=type_["data_type"].lower()
                        if 'id' in type_.keys():
                            id_=type_['id']
                             # "Found id and it -------------->", id_, attr.name
                            ids_key[attr.name]=id_
                    if attr.name not in sets_namess.keys():
                        if "key" in type_.keys():
                            sets_namess[attr.name] = type_["key"].lower()

                    if "sub_key" in type_.keys():
                        if attr.name+"_sub_key" not in sets_namess.keys():
                            sets_namess[attr.name+"_sub_key"] = type_["sub_key"].lower()

        for attribute_name in ids.keys():
            attr_outputs.append('\n\n\n*' + attribute_name)
            ff = '{0:<' + self.array_len + '}'
            t_ = ff.format('')
            counter=0
            #print "====>>>>",attribute_name
            type_= data_types[attribute_name]
            if attribute_name in sets_namess.keys():
                set_name=sets_namess[attribute_name]
            else:
                set_name=attribute_name+"_index"
            if(type_ == "hashtable" or type_ == "seasonal" ):
                for res in ids[attribute_name]:
                    resource=res.keys()[0]
                    add=resource.name+"_"+attribute_name
                    if add in self.added_pars:
                        continue
                    value_=json.loads(res.values()[0].value.value)
                    value_ =value_[value_.keys()[0]]
                    keys=sorted(value_.keys())
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name]=keys
                    else:
                        keys_=self.hashtables_keys[set_name]
                        self.hashtables_keys[set_name]=self.compare_sets(keys, keys_)
                    #values=value_[1]
                    for key in keys:
                        t_ = t_ + ff.format(key)
                    if(counter ==0):
                        if islink == True:
                            if self.links_as_name:
                                attr_outputs.append('\n\nTable ' + attribute_name + ' (link_name, '+set_name+')')
                            else:
                                '''
                                id default is links start and end nodes and junction if have any
                                 if id is defined them it will be used to be the link id
                                '''
                                if attribute_name in ids_key.keys():
                                    id=ids_key[attribute_name]
                                else:
                                    id= 'default'
                                if(id=='default'):
                                    if self.use_jun ==False:
                                        attr_outputs.append('\n\nTable ' + attribute_name + ' (i,j, '+set_name+')')
                                    else:
                                        attr_outputs.append('\n\nTable ' + attribute_name + ' (i,jun_set,j, ' + set_name + ')')
                                else:
                                    attr_outputs.append(
                                        '\n\nTable ' + attribute_name + ' ('+ id +', '+ set_name + ')')
                        elif res_type == "NETWORK":
                            attr_outputs.append('\n\nParameter '+ attribute_name + ' ('+ set_name + ')')

                        else:
                            attr_outputs.append('\n\nTable ' + attribute_name + ' (i, '+set_name+')')

                        if self.links_as_name:
                            attr_outputs.append('\n')# + ff.format(''))
                            attr_outputs.append(str(t_))
                        elif res_type != "NETWORK":
                            attr_outputs.append('\n' + str(t_))
                    counter+=1

                    if islink:
                        if self.links_as_name:
                            attr_outputs.append(
                                '\n' + ff.format(resource.name))
                            #attr_outputs.append(ff.format('\t'))

                        else:
                            if(id == 'default'):
                                if self.use_jun ==False:
                                    attr_outputs.append('\n' + ff.format(resource.from_node + '.' + resource.to_node))
                                else:
                                    jun = self.junc_node[resource.name]
                                    attr_outputs.append('\n' + ff.format(resource.from_node + '.' + jun+' . '+resource.to_node))
                            else:

                                id_value = resource.get_attribute(attr_name=id)
                                if id_value.value == None:
                                    break
                                attr_outputs.append('\n' + ff.format(id_value.value))

                    elif res_type == "NETWORK":
                        attr_outputs.append('\n' + ff.format('/')+'\n')

                    else:
                        attr_outputs.append('\n' + ff.format(resource.name))

                    for i in xrange(len(keys)):
                        key=keys[i]
                        #print i, key, "======>>>>>>",type(value_), attribute_name, value_.keys()
                        #print "----->>>>>>",keys

                        data=value_[key]
                        if res_type != "NETWORK":
                            data_str = ff.format(str((data)))
                            attr_outputs.append(data_str)
                        else:
                            #print "=========>", data, attribute_name, "----------------------->"
                            data_str = ff.format(keys[i])+ff.format(str(float(data)))
                            attr_outputs.append(data_str+'\n')
            elif type_ =="nested_hashtable":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    add=resource.name+"_"+attribute_name

                    if add in self.added_pars:
                        continue
                    value_ = json.loads(res.values()[0].value.value)
                    value_=value_[value_.keys()[0]]
                    keys = sorted(value_.keys())
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys
                    #values_=value_[1]

                    #sub_key =value_[1][0]
                    #values=value_[1][1]
                    if attribute_name+"_sub_key" in sets_namess.keys():
                        sub_set_name = sets_namess[attribute_name+"_sub_key" ]
                    else:
                        sub_set_name = attribute_name + "sub_set__index"

                    values= value_[keys[0]]
                    list=[]
                    for key in sorted(values.keys()):
                        try:
                            list.append(int(key))
                        except:
                            list.append(key)

                    for key in sorted(list):
                        t_ = t_ + ff.format(key)

                    if (counter == 0):
                        if islink:
                            if self.links_as_name:
                                attr_outputs.append(
                                    '\n\nTable ' + attribute_name + ' (link_name,' + set_name +','+sub_set_name+ ')')
                            else:
                                if self.use_jun==False:
                                    attr_outputs.append('\n\nTable ' + attribute_name + ' ('+set_name +', i,j, ' +sub_set_name+ ')')
                                else:
                                    attr_outputs.append(
                                        '\n\nTable ' + attribute_name + ' (' + set_name + ', i, jun_set, j, ' + sub_set_name + ')')
                        elif res_type == "NETWORK":
                            attr_outputs.append('\n\nTable ' + attribute_name + ' (' + set_name +','+sub_set_name+ ')')

                        else:
                            attr_outputs.append('\n\nTable ' + attribute_name + ' ('+set_name+', i, '+sub_set_name+ ')')
                        if self.links_as_name:
                            attr_outputs.append('\n' )#+ ff.format(''))
                            attr_outputs.append(str(t_))
                        elif res_type != "NETWORK":
                            attr_outputs.append('\n' + str(t_))
                    counter += 1
                    for i in xrange(len(keys)):
                        key=keys[i]
                        #value_[1][i]
                        if islink == True:
                            if self.links_as_name:
                                attr_outputs.append(
                                    '\n' + ff.format(key+'.'+resource.name ))
                                attr_outputs.append(ff.format('\t'))

                            else:
                                if self.junc_node ==False:
                                    attr_outputs.append('\n' + ff.format(key+'.'+resource.from_node + '.' + resource.to_node))
                                else:
                                    jun = self.junc_node[resource.name]
                                    attr_outputs.append(
                                        '\n' + ff.format(key + '.' + resource.from_node + '.' +jun+ '.' + resource.to_node))

                        elif res_type == "NETWORK":
                            attr_outputs.append('\n' + ff.format(key) + '\n')

                        else:
                            attr_outputs.append('\n' + ff.format(key+'.'+resource.name))
                        #all_data = json.loads(value_[1][i])


                        if (sub_set_name not in self.hashtables_keys.keys()):
                            self.hashtables_keys[sub_set_name] = list

                        for j in xrange(len(list)):
                            su_key=str(list[j])
                            if res_type != "NETWORK":
                                #print attribute_name, "--->>>>",attribute_name,key, su_key, sub_set_name, list, resource.name, value_[key]
                                if su_key not in value_[key]:
                                    continue
                                #print "value_[key][su_key]", type(value_[key]), su_key
                                data_str = ff.format(str((value_[key][su_key])))
                                attr_outputs.append(data_str)
                            else:
                                data_str = ff.format(keys[i]) + ff.format(str(float(value_[key][su_key])))
                                attr_outputs.append(data_str + '\n')
            elif type_ == "nodes_array_collection" and res_type == "NETWORK":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    value_ = json.loads(res.values()[0].value.value)
                    keys = value_[0]
                    attr_outputs.extend(self.get_resourcess_array_pars_collection(self.network.nodes, attribute_name, keys, set_name))
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys
                    else:
                        keys_ = self.hashtables_keys[set_name]
                        self.hashtables_keys[set_name] = self.compare_sets(keys, keys_)

            elif type_ == "links_array_collection" and res_type == "NETWORK":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    value_ = json.loads(res.values()[0].value.value)
                    keys = value_[0]
                    attr_outputs.extend(self.get_resourcess_array_pars_collection(self.network.links, attribute_name, keys, set_name, True))
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys
                    else:
                        keys_ = self.hashtables_keys[set_name]
                        self.hashtables_keys[set_name] = self.compare_sets(keys, keys_)
            elif type_ == "nodes_scalar_collection" and res_type == "NETWORK":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    value_ = json.loads(res.values()[0].value.value)
                    keys = value_[0]

                    attr_outputs.extend(self.get_resourcess_scalar_pars_collection(self.network.nodes, attribute_name, keys, set_name))
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys
                    else:
                        keys_ = self.hashtables_keys[set_name]
                        self.hashtables_keys[set_name] = self.compare_sets(keys, keys_)
            elif type_ == "links_scalar_collection" and res_type == "NETWORK":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    value_ = json.loads(res.values()[0].value.value)
                    keys = value_[0]
                    attr_outputs.extend(self.get_resourcess_scalar_pars_collection(self.network.links, attribute_name, keys, set_name, True))
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys
                    else:
                        keys_ = self.hashtables_keys[set_name]
                        self.hashtables_keys[set_name] = self.compare_sets(keys, keys_)

            elif type_ == "links_set_collection" and res_type == "NETWORK":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    value_ = json.loads(res.values()[0].value.value)
                    keys = value_[0]

                    if attribute_name in ids_key.keys():
                        id=ids_key[attribute_name]
                    else:
                        id='default'

                    attr_outputs.extend(
                        self.get_resourcess_set_collection(self.network.links, attribute_name, keys,id,
                                                                   True))
            elif type_ == "set_collection" and res_type == "NETWORK":
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    value_ = json.loads(res.values()[0].value.value)
                    keys = value_[0]

                    if attribute_name not in self.hashtables_keys.keys():
                        self.hashtables_keys[attribute_name]=keys


            if res_type == "NETWORK":
                attr_outputs.append('/;')
        return attr_outputs


    def prepare_hashtable_date(selfself):
        pass

    def is_it_in_list(self, item, list):
        for item_ in list:
            if item.lower().strip() == item_.lower().strip():
                return True
        return False

    def get_resourcess_array_pars_collection(self, resources, attribute_name_, pars_collections, set_name_, islink=False):
        attributes = []
        attr_names = []
        attr_outputs = []
        ids = {}
        data_types = {}
        sets_namess = {}
        # Identify all the timeseries attributes and unique attribute
        # names
        main_key=''
        sub_key=''
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'array' and attr.is_var is False and self.is_it_in_list(attr.name, pars_collections)==True:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name in ids.keys():
                        ar = ids[attr.name]
                    else:
                        ar = []
                        ids[attr.name] = ar
                    ar.append({resource: self.resourcescenarios_ids[attr.resource_attr_id]})
                    if attr.name not in data_types.keys():
                        type_ = json.loads(self.resourcescenarios_ids[attr.resource_attr_id].value.metadata)
                        if "data_type" in type_.keys():
                            data_types[attr.name] = type_["data_type"].lower()
                    if attr.name not in sets_namess.keys():
                        if "key" in type_.keys():
                            sets_namess[attr.name] = type_["key"].lower()
                            main_key= type_["key"].lower()
                    if "sub_key" in type_.keys():
                        if attr.name + "_sub_key" not in sets_namess.keys():
                            sets_namess[attr.name + "_sub_key"] = type_["sub_key"].lower()
                            sub_key=type_["sub_key"].lower()
        if islink ==True:
            res_type='link'
        else:
            res_type='node'
        counter=0
        for attribute_name in ids.keys():
            attr_outputs.append('*' + attribute_name)
            ff = '{0:<' + self.array_len + '}'
            type_ = data_types[attribute_name]
            if attribute_name in sets_namess.keys():
                set_name = sets_namess[attribute_name]
            else:
                set_name = attribute_name + "_index"
            if (type_ == "hashtable" or type_ == "seasonal"):
                if counter==0:
                    if (islink == False):
                        attr_outputs.append(
                            'Parameter ' + attribute_name_ + ' (i,' + set_name_ + ', ' + main_key + ')')
                    else:
                        if self.links_as_name:
                            attr_outputs.append(
                                'Parameter ' + attribute_name_ + ' (link_name,' + set_name_ + ', ' + main_key + ')')
                        else:
                            if self.use_jun:
                                jun = self.junc_node[resource.name]
                                attr_outputs.append(
                                    'Parameter ' + attribute_name_ + ' (i, jun_set, j, ' + set_name_ + ',' + main_key + ')')
                            else:
                                attr_outputs.append(
                                    'Parameter ' + attribute_name_ + ' (i, j, ' + set_name_ + ',' + main_key + ')')
                    attr_outputs.append('/')
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    add = resource.name + "_" + attribute_name
                    if not add in self.added_pars:
                        self.added_pars.append(add)
                    value_ = json.loads(res.values()[0].value.value)
                    value_=value_[value_.keys()[0]]

                    keys = sorted(value_.keys())
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys
                    else:
                        keys_ = self.hashtables_keys[set_name]
                        self.hashtables_keys[set_name] = self.compare_sets(keys, keys_)
                    #values = value_[1]
                    for i in xrange(len(keys)):
                        k=keys[i]
                        if(k not in value_):
                            continue
                        data_str = ff.format(str((value_[k])))
                        if islink == True:
                            if self.links_as_name:
                                attr_outputs.append(
                                    resource.name+' . '+ attribute_name+k + ' . ' + '   ' + data_str)
                            else:
                                if self.use_jun == False:
                                    attr_outputs.append(resource.from_node + ' . ' + resource.to_node+' . '+ attribute_name +k + '  ' +data_str)
                                else:
                                    jun = self.junc_node[resource.name]
                                    attr_outputs.append(
                                        resource.from_node + ' . ' + jun+' . '+resource.to_node + ' . ' + attribute_name + ' . '+k + '  ' + data_str)

                        else:
                            attr_outputs.append(resource.name+ ' . ' + attribute_name+' . '+k + '   ' + data_str)
                counter+=1
            elif type_ == "nested_hashtable":
                if counter==0:
                    if (islink == False):
                        attr_outputs.append(
                            'Parameter ' + attribute_name_ + ' (' + main_key + ', ' + sub_key + ', ' + set_name_ + ', i)')
                    else:
                        if self.links_as_name == True:
                            attr_outputs.append(
                                'Parameter ' + attribute_name_ + ' (' + main_key + ', ' + sub_key + ',' + set_name_ + ', link_name)')
                        else:
                            if self.use_jun == False:
                                attr_outputs.append('Parameter ' + attribute_name_ + ' (' + main_key + ', ' + sub_key + ',' + set_name_ + ', i, j)')
                            else:
                                attr_outputs.append('Parameter ' + attribute_name_ + ' (' + main_key + ', ' + sub_key + ',' + set_name_ + ', i, jun_set, j)')

                    attr_outputs.append('/')
                for res in ids[attribute_name]:
                    resource = res.keys()[0]
                    add = resource.name + "_" + attribute_name
                    if not add in self.added_pars:
                        self.added_pars.append(add)
                    value_ = json.loads(res.values()[0].value.value)
                    value_=value_[value_.keys()[0]]
                    keys = sorted(value_.keys())#value_[0]
                    if (set_name not in self.hashtables_keys.keys()):
                        self.hashtables_keys[set_name] = keys

                    list = []
                    for i in range (0, len(keys)):
                        vv=value_[keys[i]]
                        for key in sorted(vv.keys()):
                            try:
                                if(not int(key) in list):
                                    list.append(int(key))
                            except:
                                if (not key in list):
                                    list.append(key)

                    for i in xrange(len(keys)):
                        key = keys[i]
                        vv=value_[key]
                        #if not isinstance(value_[1][i], dict):
                        #    vv = (json.loads(value_[1][i]))
                        #else:
                        #    vv = (value_[1][i])

                        for j in range(0, len(list)):
                            if (not list[j] in vv.keys()):
                                continue
                            if islink:
                                if self.links_as_name:
                                    attr_outputs.append(
                                         (key + ' . ' +list[j] +' . '+ attribute_name+ ' . ' +resource.name+'    '+vv[list[j]]))


                                else:
                                    if self.use_jun == False:
                                        attr_outputs.append((key + ' . ' + list[
                                            j] + ' . ' + attribute_name + ' . ' + resource.from_node + '.' + resource.to_node + '    ' + str(vv[list[j]])))
                                    else:
                                        jun = self.junc_node[resource.name]
                                        attr_outputs.append((key + ' . ' + list[
                                            j] + ' . ' + attribute_name + ' . ' + resource.from_node + '.' + jun+'.'+resource.to_node + '    ' +
                                                             vv[list[j]]))

                            else:
                                attr_outputs.append(
                                    (key + ' . ' + list[j] + ' . ' + attribute_name + ' . ' + resource.name + '    ' + str(vv[list[j]])))
                counter += 1
        #attr_outputs.append('/;')
        #ss='\n'.join(attr_outputs)
        #with open("c:\\temp\\"+attribute_name_+".txt", 'w') as f:
        #    f.write(ss)
        return '\n'.join(attr_outputs)

    def get_resourcess_scalar_pars_collection(self, resources, attribute_name_, pars_collections, set_name_,
                                             islink=False):
        attributes = []
        attr_names = []
        attr_outputs = []
        ids = {}
        data_types = {}
        sets_namess = {}
        if islink == True:
            res_type = 'link'
        else:
            res_type = 'node'
        # Identify all the timeseries attributes and unique attribute
        # names
        for resource in resources:
            for attr in resource.attributes:
                if attr.dataset_type == 'scalar' and attr.is_var is False and self.is_it_in_list(attr.name,
                                                                                                pars_collections) == True:
                    attr.name = translate_attr_name(attr.name)
                    if attr.name in ids.keys():
                        ar = ids[attr.name]
                    else:
                        ar = []
                        ids[attr.name] = ar
                    ar.append({resource: self.resourcescenarios_ids[attr.resource_attr_id]})


        counter = 0
        for attribute_name in ids.keys():
            attr_outputs.append('*' + attribute_name)
            ff = '{0:<' + self.array_len + '}'
            if counter == 0:
                if (islink == True):
                    if self.links_as_name:
                        attr_outputs.append('Parameter ' + attribute_name_ + ' (' + set_name_ + ')')
                    else:
                        if self.use_jun == False:
                            attr_outputs.append('Parameter ' + attribute_name_ + ' (i, j, ' + set_name_ +  ')')
                        else:
                            attr_outputs.append('Parameter ' + attribute_name_ + ' (i, jun_set, j, ' + set_name_ + ')')
                else:
                    attr_outputs.append(
                        'Parameter ' + attribute_name_ + ' (i,' + set_name_ + ')')
                attr_outputs.append('/')
            for res in ids[attribute_name]:
                resource = res.keys()[0]
                add = resource.name + "_" + attribute_name
                if not add in self.added_pars:
                    self.added_pars.append(add)
                value_ = (res.values()[0].value.value)
                if islink:
                    if self.links_as_name:
                        attr_outputs.append(
                            resource.name + ' . ' + attribute_name + '   ' + value_)
                    else:
                        if self.use_jun == False:
                            attr_outputs.append(resource.from_node + ' . ' + resource.to_node + ' . ' + attribute_name + '  ' + value_)
                        else:
                            jun = self.junc_node[resource.name]
                            attr_outputs.append(
                                resource.from_node + ' . '+jun+' . ' + resource.to_node + ' . ' + attribute_name + '  ' + value_)

                else:
                    attr_outputs.append(resource.name + ' . ' + attribute_name +  '   ' + value_)
            counter += 1
        #attr_outputs.append('/;')
        #ss = '\n'.join(attr_outputs)
        #with open("c:\\temp\\" + attribute_name_ + ".txt", 'w') as f:
        #    f.write(ss)
        return '\n'.join(attr_outputs)


    ###########################
    def get_resourcess_set_collection(self, resources, set_title_, set_collections, id,
                                      islink=False):

        attr_outputs = []
        ids = {}

        if islink == True:
            res_type = 'link'
        else:
            res_type = 'node'
        title=''
        if id == 'default':
            if (islink == True):
                if self.links_as_name:
                    title='set ' + set_title_ + ' ( link_name '
                else:
                    if self.use_jun == False:
                        title='set ' + set_title_ + ' (i, j '
                    else:
                        title='set ' + set_title_ + ' (i, jun_set, j '
            else:
                title='set ' + set_title_ + ' (i'
        elif id == 'none' or id =='group':
            title='set '+set_title_ + ' ('

        for set in set_collections:
            if(title.endswith('(') ):
                if set == 'to_NODE_type' or set == 'from_NODE_type':
                    title = title + 'nodes_types'
                else:
                    title = title + set
            else:

                if set =='to_NODE_type' or set=='from_NODE_type':
                    title=title+',nodes_types'
                else:
                    title = title +','+set
        title=title+')\n/'
        attr_outputs.append('')
        attr_outputs.append(title)
        ###################
        if id == 'group':
            #print "It group ....", len(set_collections)
            if set_collections[0].lower() == 'dependency_set' and len(set_collections) == 3:
                para1 = set_collections[1]
                parr2 = set_collections[2]
                for group in self.DEPENDENCY_SET:
                    for link in self.links_groups_members[group]:
                        tt = link.get_attribute(attr_name=para1).value
                        tt2 = link.get_attribute(attr_name=parr2).value
                        lin=group +" . "+tt+" . "+tt2
                        if (lin):
                            attr_outputs.append(lin)
                return '\n'.join(attr_outputs)
            elif set_collections[0].lower() == 'exclusivity_set' and len(set_collections) == 2:
                for group in self.EXCLUSIVITY_SET:
                    for link in self.links_groups_members[group]:
                        lin = group + " . " + link.get_attribute(attr_name=set_collections[1]).value
                        if (lin):
                            attr_outputs.append(lin)
                return '\n'.join(attr_outputs)
        ##################
        for resource in resources:
            line=''
            if id == 'default':
                if islink:
                    if self.links_as_name:
                        line=resource.name
                    else:
                        if self.use_jun == False:
                            line=resource.from_node + ' . ' + resource.to_node
                        else:
                            jun = self.junc_node[resource.name]
                            line=resource.from_node + ' . ' + jun + ' . ' + resource.to_node
                else:
                    line=resource.name
            for set in set_collections:
                    if(islink ==True):
                        if set== 'to_NODE_type':
                            tt=self.network.get_node(node_name=resource.to_node).template[1][0]
                            if line:
                                line = line + ' . '+tt
                            else:
                                line=tt
                        elif  set == 'from_NODE_type':
                            tt=self.network.get_node(node_name=resource.from_node).template[1][0]
                            if line:
                                line = line + ' . '+tt
                            else:
                                line=tt
                        elif set == 'links_types':
                            tt=self.network.get_link(link_name=resource.name).template[1][0]
                            if line:
                                line = line + ' . ' + tt
                            else:
                                line = tt
                        else:
                            tt=resource.get_attribute(attr_name=set)
                            if tt==None:
                                break
                            if line:
                                line=line+' . '+tt.value
                            else:
                                line =  tt.value
            if(line):
                 attr_outputs.append(line)


        return '\n'.join(attr_outputs)

    ##########################


    def export_arrays(self, resources):
        """Export arrays.
        """
        attributes = []
        attr_names = []
        attr_outputs = []
        ff='{0:<'+self.name_len+'}'
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
             att_res_dims={}
             for attribute in attributes:
                # This exporter only supports 'rectangular' arrays
                dim_=None
                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.value is not None:
                        array=json.loads(attr.value)
                        dim = self.get_dim(array)
                        if (dim_ is None):
                            dim_=dim
                        elif(dim > dim_):
                            dim_=dim
                att_res_dims[attribute]=dim
             for attribute in attributes:
                # This exporter only supports 'rectangular' arrays
                dim=att_res_dims[attribute]
                if len(dim) is not 1:
                    continue

                attr_outputs.append('* Array for attribute %s, ' % \
                            (attribute.name))
                attr_outputs.append('dimensions are %s\n\n' % dim)
                        # Generate array indices
                attr_outputs.append('SETS\n\n')
                indexvars = list(ascii_lowercase)
                attr_outputs.append(attribute.name +"_index"+'/\n')
                if(len(dim)==1):
                    for idx in range(dim[0]):
                        attr_outputs.append(str(idx+1) + '\n')
                attr_outputs.append('/\n')
                attr_outputs.append('Table '+  attribute.name + ' (i, *)\n\n')#+attribute.name+'_index)\n\n')
                attr_outputs.append(ff.format(''))
                for k  in range (dim[0]):
                    attr_outputs.append(ff.format(str(k+1)))
                attr_outputs.append('\n')

                for resource in resources:
                    attr = resource.get_attribute(attr_name=attribute.name)
                    if attr is not None and attr.value is not None:
                        array=json.loads(attr.value)
                        #dim = self.get_dim(array)
                        '''
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
                        '''
                        i=0
                        attr_outputs.append(ff.format(resource.name))
                        #print "len(dim): ", len(dim)
                        #print "array len: ", len(array)
                        #print array
                        if(len(dim) is 1):
                            #print "dime[0]: ", dim[0]
                            for k  in range (dim[0]):
                                #print k, "It is ", len(array)
                                if len(array)==dim[0]:
                                    item=array[k]
                                elif len(array[0])==dim[0]:
                                     item=array[0][k]

                                ##attr_outputs.append("\n")
                                c=0
                                if(item is None):
                                    pass
                                elif type(item) is list:
                                    attr_outputs.append(format(str(i) + " . " + str(c)))
                                    i+=1
                                    for value in item:
                                        if c is 0:
                                           attr_outputs.append('{0:15}'.format(value))
                                        else:
                                             attr_outputs.append('{0:20}'.format(value))
                                        c+=1
                                else:
                                    #attr_outputs.append(format(str(i)))
                                    i+=1
                                    if c is 0:
                                        attr_outputs.append(ff.format(item))
                                    else:
                                        attr_outputs.append(ff.format(item))
                                    c+=1
                            attr_outputs.append('\n')
        attr_outputs.append('\n\n')
        return attr_outputs


    def get_years_months_days(self):
        '''
        used to get years, months days in time axis to
         write them in case of use_gams_date_index is true
        '''
        years=[]
        months=[]
        days=[]
        for date in self.time_axis:
            if date.year in years:
                pass
            else:
                years.append(date.year)
            if date.month in months:
                pass
            else:
                months.append(date.month)
            if date.day in days:
                pass
            else:
                days.append((date.day))
        return years, months, days

    def write_time_index(self):
        """
            Using the time-axis determined in __init__, write the time
            axis to the output file.
        """
        if(self.time_axis is None):
            return
        log.info("Writing time index")

        self.times_table={}
        try:
            if self.use_gams_date_index is True:
                years, months, days= self.get_years_months_days()

                t='SETS\n yr  /\n'
                for year in years:
                    t=t+str(year)+'\n'
                t=t+'/\n\n'

                t=t+'SETS\n mn  /\n'
                for month in months:
                    t=t+str(month)+'\n'
                t=t+'/\n\n'
                t=t+'SETS\n dy  /\n'
                for day in days:
                      t=t+str(day)+'\n'
                #t=t+'/\n\n'
                time_index = [t+'\n\n']####', '* Time index\n','t(yr, mn, dy)  time index /\n']
            else:
                time_index = ['SETS\n\n', '* Time index\n','t time index /\n']

            t = 0
            for date in self.time_axis:
                self.time_index.append(date)
                if self.use_gams_date_index is True:
                     _t=str(date.year)+" . "+str(date.month)+" . "+str(date.day)
                     self.times_table[date]=_t
                else:
                     time_index.append('%s\n' % t)
                     self.times_table[date]=t
                t += 1

            time_index.append('/\n\n')

            time_index.append('* define time steps dependent on time index (t)\n\n')
            if self.use_gams_date_index is True:
                time_index.append('Parameter timestamp(yr, mn, dy) ;\n\n')
            else:
                time_index.append('Parameter timestamp(t) ;\n\n')
            #print "wrinting time"
            for t, date in enumerate(self.time_index):
                if self.use_gams_date_index is True:
                    keyy=str(date.year)+"\",\""+str(date.month)+"\", \""+str(date.day)
                    time_index.append('    timestamp("%s") = %s ;\n' % \
                    (keyy, convert_date_to_timeindex(date)))
                else:
                    time_index.append('    timestamp("%s") = %s ;\n' % \
                    (self.times_table[date], convert_date_to_timeindex(date)))
            time_index.append('\n\n')

            self.output = self.output + ''.join(time_index)
            log.info("Time index written")
        except Exception as e:
            log.exception(e)
            raise HydraPluginError("Please check time-axis or start time, end times and time step.")

    def write_file(self):
        log.info("Writing file %s.", self.filename)
        for key in self.hashtables_keys.keys():
            self.sets +=('\n'+key+'\n/')
            for val in self.hashtables_keys[key]:
                self.sets +=('\n' + val)
            self.sets += ('\n/\n\n')

        with open(self.filename, 'w') as f:
            f.write(self.sets+self.output)

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



def get_dict(obj):
    if type(obj) is list:
        list_results=[]
        for item in obj:
            list_results.append(get_dict(item))
        return list_results

    if not hasattr(obj, "__dict__"):
         return obj

    result = {}
    for key, val in obj.__dict__.items():
        if key.startswith("_"):
            continue
        if isinstance(val, list):
            element = []
            for item in val:
                element.append(get_dict(item))
        else:
            element = get_dict(obj.__dict__[key])
        result[key] = element
    return result

def get_resourcescenarios_ids(resourcescenarios):
    resourcescenarios_ids={}
    for res in resourcescenarios:
        #print "==============================>", get_dict(res)
        #print type(res)
        resourcescenarios_ids[res.resource_attr_id]=res
    return resourcescenarios_ids