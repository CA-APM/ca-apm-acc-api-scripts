#!/usr/bin/env python

from __future__ import print_function

import os

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    Download files for the given file ids from the config server
    or list available files
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('-w', '--write', action='store_true', help="Write files in addition to listing them")

        self.parser.add_argument('file_ids', metavar='FILE_ID', nargs='*', type=str, help='Id of file to download')

        self.parser.add_argument('--last', action="store_true", help='Sort latest files first')
        self.parser.add_argument('--page', action="store", help='Page of data to fetch')

    def main(self):

        if self.args.file_ids:
            list_of_files = self.acc.file_meta_many(self.args.file_ids)
        else:

            # automatically build this on the object
            # self.add_request_param("sort", "modified,asc")
            # self.add_request_param("page",  self.args.page)  # could already be done for us?
            request_params = {"page": "modified,asc"}

            if self.args.page:
                request_params["page"] = self.args.page

            if self.args.last and self.args.page is None:
                # Only return the first page of data if we want to see the last registered
                # agents, unless a page has explicitly been specified
                request_params["page"] = 0

            list_of_files = self.acc.files(**request_params)

        if not self.args.write:

            # Print the meta data of each file
            for file_meta in list_of_files:
                print("\t".join([
                    str(file_meta["id"]),
                    file_meta["name"],
                    file_meta["modified"],
                    str(file_meta["size"])
                ]))
        else:
            # Download the file ids from the config server
            for file_meta in list_of_files:
                if not self.args.write:
                    # Just print the result
                    result = file_meta.download_file()
                    print(result)
                else:
                    # Write the file out
                    dest_path = "acc_%s_%s" % (file_meta["id"],  file_meta["name"])
                    if os.path.exists(dest_path):
                        print("Skipping as already exists:", dest_path)
                    else:
                        print("Writing", file_meta["id"], file_meta["name"], "to", dest_path)
                        with open(dest_path, "wb") as fout:
                            fout.write(file_meta.download_file())

if __name__ == "__main__":
    App().run()
