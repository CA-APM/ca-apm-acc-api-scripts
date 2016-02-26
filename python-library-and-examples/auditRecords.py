#!/usr/bin/env python

from __future__ import print_function

import pyacc

class App(pyacc.AccCommandLineApp):
    """
    List audit_records
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()
        self.parser.add_argument('audit_record_ids', metavar='AUDIT_RECORD_ID', nargs='*', type=str,
                                 help='Query the given audit record ids')

    def main(self):

        if self.args.audit_record_ids:
            # Create a list of Audit_record objects initialized with the audit_record id.
            # The data will be fetched from the Config Server when the object
            # is queried (e.g. "audit_record["xxx"])
            audit_records = self.acc.audit_records_many(self.args.audit_record_ids)
        else:
            # This will fetch all agents (a page a time)
            audit_records = self.acc.audit_records()

        for audit_record in audit_records:

            # Print the audit_record details
            audit_record["id"]
            print(audit_record)

            # print("\t".join([
            #     str(audit_record["id"]),
            #     safe(audit_record["name"]),
            #     safe(audit_record["displayName"]),
            #     safe(audit_record["description"]),
            #     safe(audit_record["compatibility"]),
            #     safe(audit_record["excludes"]),
            #     safe(audit_record["facets"]),
            #     pyacc.safe(audit_record["id"]),
            #     safe(audit_record["path"]),
            #     safe(audit_record["version"]),
            #     safe(audit_record["dependencies"]),
            # ]))


if __name__ == "__main__":
    App().run()
