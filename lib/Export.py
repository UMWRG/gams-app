# (c) Copyright 2015, University of Manchester
#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
``--network``          ``-t``  NETWORK    ID of the network that will be
                                          exported.
``--scenario``         ``-s``  SCENARIO   ID of the scenario that will be
                                          exported.
``--template-id``      ``-tp`` TEMPLATE   ID of the template used for exporting
                                          resources. Attributes that don't
                                          belong to this template are ignored.
``--output``           ``-o``  OUTPUT     Filename of the output file.
====================== ======= ========== ======================================

**Optional arguments:**

====================== ======= ========== ======================================
``--group-nodes-by``   ``-gn`` GROUP_ATTR Group nodes by this attribute(s).
``--group_links-by``   ``-gl`` GROUP_ATTR Group links by this attribute(s).
====================== ======= ========== ======================================


Specifying the time axis
~~~~~~~~~~~~~~~~~~~~~~~~

One of the following two options for specifying the time domain of the model is
mandatory:

**Option 1:**

====================== ======= ========== ======================================
``--start-date``       ``-st`` START_DATE Start date of the time period used for
                                          simulation.
``--end-date``         ``-en`` END_DATE   End date of the time period used for
                                          simulation.
``--time-step``        ``-dt`` TIME_STEP  Time step used for simulation. The
                                          time step needs to be specified as a
                                          valid time length as supported by
                                          Hydra's unit conversion function (e.g.
                                          1 s, 3 min, 2 h, 4 day, 1 mon, 1 yr)
====================== ======= ========== ======================================

**Option 2:**

====================== ======= ========== ======================================
``--time-axis``        ``-tx`` TIME_AXIS  Time axis for the modelling period (a
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

In addition to links, GAMSexport provides a connectivity matrx::

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

API docs
--------
"""

import re
import argparse as ap
from datetime import datetime
from datetime import timedelta
from string import ascii_lowercase

from HydraLib import PluginLib
from HydraLib.PluginLib import JsonConnection
from HydraLib.HydraException import HydraPluginError
from HydraLib.util import array_dim, parse_array
from HydraLib.dateutil import guess_timefmt, date_to_string


from HydraGAMSlib import GAMSnetwork
from HydraGAMSlib import create_arr_index
from HydraGAMSlib import arr_to_matrix
from HydraGAMSlib import convert_date_to_timeindex
from HydraLib.PluginLib import write_progress

import traceback

import logging
log = logging.getLogger(__name__)

class GAMSexport(object):

    def __init__(self, network_id,
                 scenario_id,
                 template_id,
                 filename,
                 link_export_flag,
                 session_id=None,
                 url=None):

        if network_id is None:
            raise HydraPluginError("No Network specified!")
        else:
            network_id = int(network_id)

        if scenario_id is None:
            raise HydraPluginError("No Scenario specified!")
        else:
            scenario_id = int(scenario_id)

        if filename is None:
            raise HydraPluginError("No Output file name specified!")


        self.filename = filename
        self.time_index = []
        self.steps=7

        self.connection = JsonConnection(url)
        if session_id is not None:
            log.info("Using existing session %s", session_id)
            self.connection.session_id=session_id
        else:
            self.connection.login()

        net = self.connection.call('get_network', {'network_id':network_id,
                                                   'include_data': 'Y',
                                                   'template_id':template_id,
                                                   'scenario_ids':[scenario_id]})
        self.net=net

        log.info("Network retrieved")
        attrs = self.connection.call('get_attributes', {})
        log.info("%s attributes retrieved", len(attrs))
        self.network = GAMSnetwork()
        log.info("Loading net into gams network.")
        self.network.load(net, attrs)
        log.info("Gams network loaded")
        if link_export_flag == 'l':
            self.links_as_name = True
        else:
            self.links_as_name = False
        self.network.gams_names_for_links(linkformat=link_export_flag)
        log.info("Names for links retrieved")
        self.template_id = None

        self.output = """* Data exported from Hydra using GAMSplugin.
* (c) Copyright 2013, 2014, University of Manchester
*
* %s: %s
* Network-ID:  %s
* Scenario-ID: %s
*******************************************************************************

""" % (self.network.name, self.network.description,
            self.network.ID, self.network.scenario_id)

    def export_network(self):
        self.output += '* Network definition\n\n'
        log.info("Exporting nodes")
        write_progress(2, self.steps)
        self.export_nodes()
        log.info("Exporting node groups")
        write_progress(3, self.steps)
        self.export_node_groups()
        log.info("Exporting links")
        write_progress(4, self.steps)
        self.export_links()
        log.info("Exporting link groups")
        write_progress(5, self.steps)
        self.export_link_groups()
        log.info("Creating connectivity matrix")
        write_progress(6, self.steps)
        self.create_connectivity_matrix()
        log.info("Matrix created")

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

    def export_data(self):
        log.info("Exporting data")
        # Export node data for each node type
        data = ['* Node data\n\n']
        for node_type in \
                self.network.get_node_types(template_id=self.template_id):
            data.append('* Data for node type %s\n\n' % node_type)
            nodes = self.network.get_node(node_type=node_type)
            data.extend(self.export_parameters(nodes, node_type, 'scalar'))
            data.extend(self.export_parameters(nodes, node_type, 'descriptor'))
            data.extend(self.export_timeseries(nodes, node_type))
            data.extend(self.export_arrays(nodes))

        # Export link data for each node type
        data.append('* Link data\n\n')
        for link_type in self.network.get_link_types(template_id=self.template_id):
            data.append('* Data for link type %s\n\n' % link_type)
            links = self.network.get_link(link_type=link_type)
            data.extend(self.export_parameters(links, link_type, 'scalar', res_type='LINK'))
            data.extend(self.export_parameters(links, link_type,'descriptor', res_type='LINK'))
            data.extend(self.export_timeseries(links, link_type, res_type='LINK'))
            self.export_arrays(links)
        self.output = "%s%s"%(self.output, ''.join(data))
        log.info("Data exported")

    def export_parameters(self, resources, obj_type, datatype, res_type=None):
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
                    if attr is None or attr.value is None:
                        continue
                    attr_outputs.append(' %14s' % attr.value.values()[0][0])
                attr_outputs.append('\n')
            attr_outputs.append('\n\n')
        return attr_outputs

    def export_timeseries(self, resources, obj_type, res_type=None):
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
                    if attr.dataset_id is not None:
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

            for t, timestamp in enumerate(self.time_index):
                attr_outputs.append('{0:<7}'.format(t))
                for attribute in attributes:
                    for resource in resources:
                        attr = resource.get_attribute(attr_name=attribute.name)
                        if attr is not None and attr.dataset_id is not None:
                            soap_time = [date_to_string(timestamp)]
                            json_data = self.connection.call('get_val_at_time',
                                                        {'dataset_id':attr.dataset_id,
                                                         'timestamps' : soap_time})

                            if json_data.data is None:
                                raise HydraPluginError("Dataset %s has no data for time %s"%(attr.dataset_id, soap_time))

                            data = parse_array(json_data.data)[0]

                            if data is None:
                                continue

                            data_str = ' %14f' % data
                            attr_outputs.append(
                                data_str.rjust(col_header_length[(attribute, resource)]))
                attr_outputs.append('\n')
            attr_outputs.append('\n')
        return attr_outputs

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
                        array_dict = attr.value['arr_data'][0]
                        array = parse_array(array_dict)
                        dim = array_dim(array)
                        attr_outputs.append('* Array %s for node %s, ' % \
                            (attr.name, resource.name))
                        attr_outputs.append('dimensions are %s\n\n' % dim)
                        # Generate array indices
                        attr_outputs.append('SETS\n\n')
                        indexvars = list(ascii_lowercase)
                        for i, n in enumerate(dim):
                            attr_outputs.append(indexvars[i] + '_' + \
                                resource.name + '_' + attr.name + \
                                ' array index /\n')
                            for idx in range(n):
                                attr_outputs.append(str(idx) + '\n')
                            attr_outputs.append('/\n\n')

                        attr_outputs.append('Table ' + resource.name + '_' + \
                            attr.name + '(')
                        for i, n in enumerate(dim):
                            attr_outputs.append(indexvars[i] + '_' + resource.name \
                                + '_' + attr.name)
                            if i < (len(dim) - 1):
                                attr_outputs.append(',')
                        attr_outputs.append(') \n\n')
                        ydim = dim[-1]
                        #attr_outputs.append(' '.join(['{0:10}'.format(y)
                        #                        for y in range(ydim)])
                        for y in range(ydim):
                            attr_outputs.append('{0:20}'.format(y))
                        attr_outputs.append('\n')
                        arr_index = create_arr_index(dim[0:-1])
                        matr_array = arr_to_matrix(array, dim)
                        for i, idx in enumerate(arr_index):
                            for n in range(ydim):
                                attr_outputs.append('{0:<10}'.format(
                                    ' . '.join([str(k) for k in idx])))
                                attr_outputs.append('{0:10}'.format(matr_array[i][n]))
                            attr_outputs.append('\n')
                        attr_outputs.append('\n\n')
        return attr_outputs

    def write_time_index(self, start_time=None, end_time=None, time_step=None,
                         time_axis=None):
        log.info("Writing time index")

        time_index = ['SETS\n\n', '* Time index\n','t time index /\n']

        if time_axis is None:
            start_date = self.parse_date(start_time)
            end_date = self.parse_date(end_time)
            delta_t = self.parse_time_step(time_step)

            t = 0
            while start_date < end_date:

                time_index.append('%s\n' % t)
                self.time_index.append(start_date)
                start_date += timedelta(delta_t)
                t += 1

            time_index.append('/\n\n')

        else:
            time_axis = ' '.join(time_axis).split(',')
            t = 0
            for timestamp in time_axis:
                date = self.parse_date(timestamp.strip())
                self.time_index.append(date)
                time_index.append('%s\n' % t)
                t += 1

            time_index.append('/\n\n')

        time_index.append('* define time steps dependent on time index (t)\n\n')
        time_index.append('Parameter timestamp(t) ;\n\n')
        for t, date in enumerate(self.time_index):
            time_index.append('    timestamp("%s") = %s ;\n' % \
                (t, convert_date_to_timeindex(date)))
        time_index.append('\n\n')

        self.output = self.output + ''.join(time_index)
        log.info("Time index written")

    def parse_time_step(self, time_step):
        """Read in the time step and convert it to days.
        """
        # export numerical value from string using regex
        value = re.findall(r'\d+', time_step)[0]
        valuelen = len(value)
        value = value
        units = time_step[valuelen:].strip()
        converted_time_step = self.connection.call('convert_units', {
            'values':[value], 'unit1':units, 'unit2':'day'})[0]

        return float(converted_time_step)

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