#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A set of classes to facilitate import and export from and to GAMS.

Basics
~~~~~~

The GAMS import and export plug-in provides pre- and post-processing facilities
for GAMS models. The basic idea is that this plug-in exports data and
constraints from Hydra to a text file which can be imported into an existing
GAMS model using the ``$ import`` statement.

API docs
~~~~~~~~
"""

import os

from HydraLib.PluginLib import HydraResource
from HydraLib.PluginLib import HydraNetwork
import argparse as ap



class GAMSnetwork(HydraNetwork):
    def gams_names_for_links(self, linkformat=None):
        """Add a string to each link that can be used directly in GAMS code in
        order to define a link."""
        if linkformat == 'nn':
            for i, link in enumerate(self.links):
                self.links[i].gams_name = link.from_node + ' . ' + link.to_node
        elif linkformat == 'l':
            for i, link in enumerate(self.links):
                self.links[i].gams_name = link.from_node + ' . ' + \
                    link.name + ' . ' + link.to_node


class GAMSlink(HydraResource):

    gams_name = None
    from_node = None
    to_node = None


def convert_date_to_timeindex(date):
    totalseconds = date.hour * 3600 + date.minute * 60 + date.second
    return date.toordinal() + float(totalseconds) / 86400


def arr_to_matrix(arr, dim):
    """
    Reshape a multidimensional array to a 2 dimensional matrix.
    """
    tmp_arr = []
    for n in range(len(dim) - 2):
        for inner in arr:
            for i in inner:
                tmp_arr.append(i)
        arr = tmp_arr
        tmp_arr = []
    return arr


def create_arr_index(dim):
    arr_idx = []
    L = 1
    for d in dim:
        L *= d

    for l in range(L):
        arr_idx.append(())

    K = 1
    for d in dim:
        L = L / d
        n = 0
        for k in range(K):
            for i in range(d):
                for l in range(L):
                    arr_idx[n] += (i,)
                    n += 1
        K = K * d

    return arr_idx


def import_gms_data(filename):
    """
    Read whole .gms file and expand all $ include statements found.
    """
    """Read whole .gms file and expand all $ include statements found.
    """
    basepath = os.path.dirname(filename)
    gms_data = ''
    with open(filename) as f:
        while True:
            line = f.readline()
            if line == '':
                break
            sline = line.strip()
            if len(sline) > 0 and sline[0] == '$':
                lineparts = sline.split()
                #lineparts2 = sline.split("\"")

                if len(lineparts) > 2 and \
                        lineparts[1] == 'include':
                    ff=sline
                    ff=ff.replace('$','')
                    ff=ff.replace('"','')
                    ff=ff.replace(';','')
                    ff=ff.replace('include','')
                    ff=ff.strip()
                 ##   for ll in lineparts:
                     ##    print ll
                     ####    if(ll.__contains__('include')|ll.__contains__('$')):
                        ##     continue

                    ##     ff=ff+ll

                    #line = import_gms_data(os.path.join(basepath, lineparts[2]))
                    line = import_gms_data(os.path.join(basepath, ff))
                elif len(lineparts) == 2 and lineparts[0] == '$include':
                    line = import_gms_data(os.path.join(basepath, lineparts[1]))
            gms_data += line
    return gms_data

def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Run a GAMS model using data exported from Hydra.
                    (c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information, web site will available soon",
        formatter_class=ap.RawDescriptionHelpFormatter)

    parser.add_argument('-G', '--gams-path',
                        help='Path of the GAMS installation.')
    parser.add_argument('-sh', '--switch',
                        help='option to set the plugin function, the options are: A: Auto, export, run then import (default), E: export only. I: Import only')
    parser.add_argument('-t', '--network',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario',
                        help='''ID of the scenario that will be exported.''')
    parser.add_argument('-tp', '--template-id',
                        help='''ID of the template to be used.''')
    parser.add_argument('-m', '--gms-file',
                        help='''Full path to the GAMS model (*.gms) used for
                        the simulation.''')
    parser.add_argument('-o', '--output',
                        help='''Output file containing exported data''')
    parser.add_argument('-nn', '--node-node', action='store_true',
                        help="""(Default) Export links as 'from_name .
                        end_name'.""")
    parser.add_argument('-ln', '--link-name', action='store_true',
                        help="""Export links as link name only. If two nodes
                        can be connected by more than one link, you should
                        choose this option.""")
    parser.add_argument('-st', '--start-date', nargs='+',
                        help='''Start date of the time period used for
                        simulation.''')
    parser.add_argument('-en', '--end-date', nargs='+',
                        help='''End date of the time period used for
                        simulation.''')
    parser.add_argument('-dt', '--time-step', nargs='+',
                        help='''Time step used for simulation.''')
    parser.add_argument('-tx', '--time-axis', nargs='+',
                        help='''Time axis for the modelling period (a list of
                        comma separated time stamps).''')
    parser.add_argument('-f', '--gdx-file',
                        help='GDX file containing GAMS results.')
    parser.add_argument('-e', '--export_only', action='store_true',
                        help='''Export data to file, don't run the model''')
    # Optional arguments
    #if(parser.export_only==False):
    parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')
    return parser

#print progress to stdout
def write_output(step, total):
    message = "Progress %s/%s"%(step, total)
    print message

def get_gams_path():
    if os.name == 'nt':
        base = 'C://GAMS/'
        #Try looking in the default location.
        if os.path.exists(base):
            wintypes = [f for f in os.listdir(base) if f.find('win') >= 0]
            if len(wintypes) > 0:
                gams_win_dir = base + wintypes[0] + '/'
                gams_versions = [v for v in os.listdir(gams_win_dir)]
                #Attempt to find the highest version by sorting the version
                #directories and picking the last one
                gams_versions.sort()
                if len(gams_versions) > 0:
                    gams_path = gams_win_dir + gams_versions[-1]
    else:
        base = '/opt/gams/'
        #Try looking in the default location.
        if os.path.exists(base):
            linuxtypes = [f for f in os.listdir(base) if f.find('linux') >= 0]
            linuxtypes.sort()
            #Attempt to find the highest version by sorting the version
            #directories and picking the last one
            if len(linuxtypes) > 0:
                gams_path = base + linuxtypes[-1]

    return gams_path
