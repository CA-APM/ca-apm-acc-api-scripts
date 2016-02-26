#!/usr/bin/env python

from __future__ import print_function

import pyacc

# TODO  and optionally push to agents?
class App(pyacc.AccCommandLineApp):
    """
    Upload files to config server. Note that the file upload option needs to be enabled on the Config Server
    (agent.file.management.enabled=true in APMCommandCenterServer/config/apmccsrv.properties)
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()
        # self.parser.add_argument('-a', '--agents', dest='agents', action='store_true', help="include agents")

        self.parser.add_argument('filenames', metavar='FILE', nargs='+', type=str, help='path to file to push')

    def main(self):

        # Upload the given files to the config server
        for filename in self.args.filenames:
            result = self.acc.upload_file(filename)
            print("\t".join([str(result["id"]), result["name"], result["modified"], str(result["size"])]))

if __name__ == "__main__":
    App().run()
