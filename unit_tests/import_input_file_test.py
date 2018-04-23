import unittest
from collections import namedtuple
import json
import os
import sys

pythondir = os.path.dirname(os.path.realpath(__file__))
gamslibpath=os.path.join(pythondir, '..', 'lib')
api_path = os.path.realpath(gamslibpath)
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from Exporter import GAMSExporter
from HydraGAMSlib import GAMSnetwork


def read_file_contenet(file_name):
    f = open(file_name, 'r')
    file_string = ''
    while 1:
        line = f.readline()
        if not line: break
        file_string += line
    f.close()
    return file_string

class gams_input_file_importer(unittest.TestCase):
    def setUp(self):
        '''
        It reads json files which contains the network, attributes and application arhument
        all of them are used in the various unit tests
        these files are based on demo2 example in our demos respo
        '''
        GAMSnetwork().links = []
        GAMSnetwork().nodes = []
        hydra_json_file=r"GAMStestModel.json"
        args_file_name=r"_args.json"
        attrs_json_file=r"attrs.json"
        hydra_json_string=read_file_contenet(hydra_json_file)
        args_json_string=read_file_contenet(args_file_name)
        atttrs_json_string = read_file_contenet(attrs_json_file)
        self.hydra_network = json.loads(hydra_json_string, object_hook=lambda d: namedtuple('X', d.keys(), rename=False, verbose=False)(*d.values()))
        self.args= json.loads(args_json_string, object_hook=lambda d: namedtuple('X', d.keys(), rename=False, verbose=False)(*d.values()))
        self.attrs= json.loads(atttrs_json_string, object_hook=lambda d: namedtuple('X', d.keys(), rename=False, verbose=False)(*d.values()))
        self.exporter=GAMSExporter(self.args, self.hydra_network)
        self.exporter.prepare_network(True, self.attrs)
        self.exporter.get_longest_node_link_name()
        self.exporter.write_time_index()

    def tearDown(self):
        pass

    def test_import_resource_attributes(self):
        #sclar nodes_attributes
        expected_scalar_attr=read_file_contenet(r'nodes_scalar_attr.txt')
        nodes_scalar_attr=self.exporter.export_parameters_using_attributes(self.exporter.network.nodes, 'scalar')
        nodes_scalar_attr=''.join(nodes_scalar_attr)
        assert expected_scalar_attr.strip()==nodes_scalar_attr.strip()
        # nodes timeseries_attributes
        expected_nodes_timeseries_attrs=read_file_contenet(r'nodes_timeseries_attrs.txt')
        nodes_timeseries_attrs=self.exporter.export_timeseries_using_attributes(self.exporter.network.nodes)
        nodes_timeseries_attrs=''.join(nodes_timeseries_attrs)
        assert expected_nodes_timeseries_attrs.strip() == nodes_timeseries_attrs.strip()

        #links timeseries attributes
        expected_links_timeseries_attrs=read_file_contenet(r'links_timeseries_attrs.txt')
        linkss_timeseries_attrs=self.exporter.export_timeseries_using_attributes(self.exporter.network.links)
        linkss_timeseries_attrs=''.join(linkss_timeseries_attrs)
        assert expected_links_timeseries_attrs.strip() == linkss_timeseries_attrs.strip()


    def test_import_links(self):
        expected_sets=read_file_contenet(r'links_sets.txt')
        links_sets = self.exporter.export_links()
        assert expected_sets.strip() == links_sets.strip()

    def test_import_nodes(self):
        expected_sets = read_file_contenet(r'nodes_sets.txt')
        nodes_sets = self.exporter.export_nodes()
        assert expected_sets.strip() == nodes_sets.strip()

