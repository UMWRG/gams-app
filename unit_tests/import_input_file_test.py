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

    def tearDown(self):
        pass

    def test_import_resource_attributes(self):
        pass

    def test_import_links(self):
        expected_sets=read_file_contenet(r'links_sets.txt')
        links_sets = self.exporter.export_links()
        assert expected_sets.strip() == links_sets.strip()

    def test_import_nodes(self):
        expected_sets = read_file_contenet(r'nodes_sets.txt')
        nodes_sets = self.exporter.export_nodes()
        assert expected_sets.strip() == nodes_sets.strip()

    def test_import_network(self):
        pass
