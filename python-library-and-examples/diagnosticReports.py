#!/usr/bin/env python

from __future__ import print_function

import os

import pyacc

# TODO make this download the latest version like in the other script


class App(pyacc.AccCommandLineApp):
    """
    List diagnostic reports and tasks
    """

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()
        self.parser.add_argument('-t', '--tasks', action='store_true', help="list tasks")

        self.parser.add_argument('diag_report_ids', metavar='REPORT_ID', nargs='*', type=str,
                                 help='Query the given diagnostic report ids')

        self.parser.add_argument('-w', '--write', action='store_true', help="Write report zip file in addition to listing them")

    def main(self):

        if self.args.tasks:
            for diagnostic_report_task in self.acc.diagnostic_report_tasks():
                print(diagnostic_report_task)
        else:

            if self.args.diag_report_ids:
                # Create a list of Diagnostic Report objects initialized with the report id.
                # The data will be fetched from the Config Server when the object
                # is queried (e.g. "agent["agentName"])
                diagnostic_reports = self.acc.diagnostic_reports_many(self.args.diag_report_ids)
            else:
                # This will fetch all reports (a page a time)
                diagnostic_reports = self.acc.diagnostic_reports()

            for diagnostic_report in diagnostic_reports:
                diagnostic_report.get_json()
                print(diagnostic_report)

                if self.args.write:
                    if os.path.exists(diagnostic_report.filename()):
                        print("Skipping downloading existing:", diagnostic_report.filename())
                    else:
                        print("Downloading", diagnostic_report.filename())
                        diagnostic_report.download()


if __name__ == "__main__":
    App().run()
