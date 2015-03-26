#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright 2013, 2014, 2015 University of Manchester\
#\
# HydraGAMSLib is free software: you can redistribute it and/or modify\
# it under the terms of the GNU General Public License as published by\
# the Free Software Foundation, either version 3 of the License, or\
# (at your option) any later version.\
#\
# HydraGAMSLib is distributed in the hope that it will be useful,\
# but WITHOUT ANY WARRANTY; without even the implied warranty of\
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\
# GNU General Public License for more details.\
# \
# You should have received a copy of the GNU General Public License\
# along with HydraGAMSLib.  If not, see <http://www.gnu.org/licenses/>\
#

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
import sys

from HydraLib.PluginLib import HydraResource
from HydraLib.PluginLib import HydraNetwork
import argparse as ap



class GAMSnetwork(HydraNetwork):
    def gams_names_for_links(self, linkformat=None):
        """
        Add a string to each link that can be used directly in GAMS code in
        order to define a link.
        """
        if linkformat == 'nn':
            for i, link in enumerate(self.links):
                self.links[i].gams_name = link.from_node + ' . ' + link.to_node
        elif linkformat == 'l':
            for i, link in enumerate(self.links):
                #self.links[i].gams_name = link.from_node + ' . ' + \
                #    link.name + ' . ' + link.to_node
                self.links[i].gams_name = link.name


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

def get_gams_path():
    """
	Attempt to determine the path to the local GAMS installation.
    First check whether it has been specified directly.
    If not, look in the most likely place for the gams installation given
    the operating system being used.
    This will only work with gams version 23.8 and above.
    """
    cmd_args = sys.argv


    for i, arg in enumerate(sys.argv):
        if arg in ['-G', '--gams-path']:
            gams_path = cmd_args[i + 1]

    gams_path = None
    gams_python_api_path = None
    if gams_path is None:
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
                        if float(gams_versions[-1]) < 23.8:
                                raise HydraPluginError("Only GAMS versions of 23.8 and above are supported automatically."
                                            " Please download the newest GAMS from (http://www.gams.com/download/) or "
                                            " specify the folder containing gams API using --gams-path")
                        else:   
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

        if gams_path is not None:
            return gams_path
        else:  
            raise HydraPluginError("Unable to find GAMS installation. Please specify folder containing gams executable.")
    else:
        return gams_path
