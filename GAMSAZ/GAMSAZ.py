#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse as ap
import os
import sys

from GAMSexport import GAMSexport


class GamsModel(object):

    def __init__(self, gamspath):
        real_path = os.path.realpath(os.path.abspath(gamspath))
        api_path = real_path + '/apifiles/Python/api/'
        if api_path not in sys.path:
            sys.path.insert(0, api_path)
        from gams import GamsWorkspace
        self.ws = GamsWorkspace(system_directory=real_path)

    def add_job(self, model_file):
        with open(model_file) as f:
            model_str = f.read()

        # Add lines to dynamically include the data file
        add_str = "$if not set incname $abort 'Data file not provided'\n"
        add_str += "$include \%incname\%\n"
        model_str = add_str + model_str
        self.job = self.ws.add_job_from_string(model_str)

    def add_data(self, exporter):
        f = open('hydraoutput.gms', 'w')
        f.write(exporter.output)
        f.close()

        self.opt = self.ws.add_options()
        self.opt.defines['incname'] = 'hydraoutput'

    def run(self):
        self.job.run(self.opt)

    def read_results(self):
        pass


def commandline_parser():
    parser = ap.ArgumentParser(
        description="""Run a GAMS model using data exported from Hydra. This
App requires GAMS v24.3 or later.

Written by Philipp Meier <philipp@diemeiers.ch>
(c) Copyright 2014, Univeristy of Manchester.
        """, epilog="For more information visit www.hydraplatform.org",
        formatter_class=ap.RawDescriptionHelpFormatter)
    # Mandatory arguments
    #parser.add_argument('-p', '--project',
    #                    help='''ID of the project that will be exported.''')
    parser.add_argument('-G', '--gams-path',
                        help='Path of the GAMS installation.')
    parser.add_argument('-t', '--network',
                        help='''ID of the network that will be exported.''')
    parser.add_argument('-s', '--scenario',
                        help='''ID of the scenario that will be exported.''')
    parser.add_argument('-tp', '--template-id',
                        help='''ID of the template to be used.''')
    parser.add_argument('-m', '--gms-file',
                        help='''Full path to the GAMS model (*.gms) used for
                        the simulation.''')
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

    parser.add_argument('-e', '--export-only',
                        help='''Export data to file, don't run the model''')
    # Optional arguments
    parser.add_argument('-u', '--server-url',
                        help='''Specify the URL of the server to which this
                        plug-in connects.''')
    return parser


if __name__ == '__main__':
    parser = commandline_parser()
    args = parser.parse_args()

    link_export_flag = 'nn'
    if args.link_name is True:
        link_export_flag = 'l'

    exporter = GAMSexport(int(args.network),
                          int(args.scenario),
                          int(args.template_id),
                          args.output,
                          link_export_flag,
                          url=args.server_url)

    if args.template_id is not None:
        exporter.template_id = int(args.template_id)

    exporter.export_network()

    if args.start_date is not None and args.end_date is not None \
            and args.time_step is not None:
        exporter.write_time_index(start_time=args.start_date,
                                  end_time=args.end_date,
                                  time_step=args.time_step)
    elif args.time_axis is not None:
        exporter.write_time_index(time_axis=args.time_axis)
    else:
        raise HydraPluginError('Time axis not specified.')
    exporter.export_data()

    model = GamsModel(args.gams_path)
    model.add_job(args.gms_file)
    model.add_data(exporter)
    model.run()
