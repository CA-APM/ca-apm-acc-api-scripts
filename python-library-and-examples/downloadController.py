#!/usr/bin/env python

from __future__ import print_function

import os

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    Download the controller package from the Config Server.
    By default, automatically choose the tar for posix systems and zip for everything else.
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        exgroup = self.parser.add_mutually_exclusive_group()
        exgroup.add_argument('--format', action='store', choices=["zip", "tar"], help='write files in the given format.')
        exgroup.add_argument('--filename', action='store', help='Override default filename and/or extension')

    def main(self):
        fmt = self.args.format
        filename = self.args.filename
        if filename:
            name, ext = os.path.splitext(filename)
            fmt = ext[1:]
            if fmt not in ["zip", "tar"]:
                self.parser.error("Could not infer zip or tar from " + filename)

        self.acc.download_controller(fmt, filename)

if __name__ == "__main__":
    App().run()
