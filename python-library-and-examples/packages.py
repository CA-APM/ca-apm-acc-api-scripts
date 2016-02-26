#!/usr/bin/env python

from __future__ import print_function

import sys

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    List packages / add new bundles to packages / create new packages / download packages.
    Each sub-command (list|create|delete|modify|download) has its own options. You can
    view them for example like this:
        packages list --help
    """

    cols = ("id", "packageName", "version", "totalAgentsForPackage", "totalAgentsForVersion", "modified", "latest")

    appservers = ["other", "ctg-server", "glassfish", "interstage", "jboss", "tomcat", "weblogic", "websphere"]

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('-v', '--verbose', action='store_true', help="be more verbose")

        subparsers = self.parser.add_subparsers(help="package sub-command", dest="command")

        list_parser = subparsers.add_parser("list")  # aliases=['ls'] only works with python 3
        list_parser.add_argument('-l', '--long', action='store_true', help="print more detail")
        list_parser.add_argument('--all', action='store_true', help="include old versions of packages")
        list_parser.add_argument('-b', '--bundles', action='store_true', help="print Package bundle information")
        list_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='*', type=str,
                                 help='package ids', default=[])

        create_parser = subparsers.add_parser("create", )
        create_parser.add_argument('names', metavar='NAME', nargs='+', type=str, help='package name', default=[])
        create_parser.add_argument('--os', action='store', help="os type", default="unix", choices=["unix", "windows"])
        create_parser.add_argument('--appserver', action='store', help="appserver type", choices=App.appservers, default="other")
        create_parser.add_argument('--agent-version', action='store', help="agent version", default="10.2")
        create_parser.add_argument('--process-display-name', action='store', help="process display name", default="")
        create_parser.add_argument('--comment', action='store', help="package comment", default="")
        create_parser.add_argument('--em-host', action='store', help="package comment", default="")

        delete_parser = subparsers.add_parser("delete")
        delete_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='+', type=str,
                                   help='package ids')

        modify_parser = subparsers.add_parser("modify")
        modify_parser.add_argument('-a', '--add', action='append', help="Add a bundle to a package", default=[])
        modify_parser.add_argument('-r', '--remove', action='append', help="Remove a bundle from a package", default=[])
        modify_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='*', type=str,
                                   help='package ids', default=[])

        download_parser = subparsers.add_parser("download")
        download_parser.add_argument('--format', action='store',
                                     help='write files in the given format. "archive" means zip for windows packages, tar.gz for unix packages',
                                     default="archive", choices=["zip", "tar", "archive"])
        download_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='*', type=str,
                                     help='package ids', default=[])
        download_parser.add_argument('--all', action='store_true', help="also download old versions of packages")

    def _get_packages(self):
        if self.args.package_ids:
            # Create a list of Package objects initialized with the package id.
            # The data will be fetched from the Config Server when the object
            # is queried (e.g. "package["xxx"])
            packages = self.acc.packages_many(self.args.package_ids)
        else:
            # This will fetch all agents (a page a time)
            if self.args.all:
                packages = self.acc.packages()
            else:
                packages = self.acc.packages(q="latest:true")

        return packages

    def _print_package(self, package):
        if self.args.verbose:
            package["id"] # force a fetch
            print(package)
        else:
            # Use a list comprehension to pull out the package fields from the column names
            print("\t".join([str(package[x]) for x in App.cols]))

    def list(self):

        if self.args.long:
            self.args.verbose = True

        if not self.args.verbose:
            print("\t".join(App.cols))

        for package in self._get_packages():
            self._print_package(package)

            if self.args.bundles:
                included_ids = set()
                print("\nIncluded bundles:")
                included_bundles = []
                for cb in package.bundles():
                    name = "%s:%s" % (cb["name"], cb["version"])
                    print("\t", cb["id"], name)
                    included_bundles.append(name)
                    included_ids.add(str(cb["id"]))

                if package["downloaded"] and not package["latest"]:
                    print("\nCompatible bundles:")
                else:
                    print("\nAvailable bundles:")

                for cb in package.compatible_bundles():
                    name = "%s:%s" % (cb["name"], cb["version"])
                    if name not in included_bundles:
                        print("\t", cb["id"], name)
                print()

    def delete(self):
        for dp in self.args.package_ids:
            print("Deleting package", dp)
            p = self.acc.package(dp)
            p.delete()

    def create(self):
        for name in self.args.names:
            new_package = self.acc.package_create(name=name,
                                                  os=self.args.os,
                                                  appserver=self.args.appserver,
                                                  em_host=self.args.em_host,
                                                  agent_version=self.args.agent_version,
                                                  process_display_name=self.args.process_display_name or self.args.appserver,
                                                  comment=self.args.comment)
            print(new_package)

    def download(self):
        # The package will be named automatically by a name suggested from the Config Server
        for package in self._get_packages():
            filename = package.download(".", self.args.format)

    def modify(self):

        # If nothing specified to modify, list the packages
        if not self.args.package_ids:
            self.args.long = self.args.all = self.args.bundles = False
            self.list()
            return

        for package in self._get_packages():

            # Print the package details
            self._print_package(package)

            included_ids = set()
            print("\nIncluded bundles:")
            included_bundles = []
            for cb in package.bundles():
                name = "%s:%s" % (cb["name"], cb["version"])
                print("\t", cb["id"], name)
                included_bundles.append(name)
                included_ids.add(str(cb["id"]))

            if package["downloaded"] and not package["latest"]:
                print("\nCompatible bundles:")
            else:
                print("\nAvailable bundles:")

            for cb in package.compatible_bundles():
                name = "%s:%s" % (cb["name"], cb["version"])
                if name not in included_bundles:
                    print("\t", cb["id"], name)

            if package["downloaded"] and not package["latest"]:
                print("\nPackage id %s is read only because it has been downloaded and is not the latest version (id %d is the latest)" % (package.item_id, package["latestPackageID"]))
                if self.args.add:
                    sys.exit(1)

            if self.args.add or self.args.remove:
                print("Adding bundles", self.args.add)
                print("Removing bundles", self.args.remove)
                before = set(included_ids)

                included_ids.update(self.args.add)
                included_ids.difference_update(self.args.remove)

                if len(before ^ included_ids) == 0:
                    print("Bundle set would be unchanged - not updating Package")
                else:
                    after = sorted(included_ids, key=int)
                    print("Bundle set is", after)

                    # TODO validate/expand the input against data retrieve above. need to pass in the existing bundles.
                    package.add_bundles(after);

    def main(self):

        # Route users command to the handler
        cmd = {
            "list": self.list,
            "delete": self.delete,
            "create": self.create,
            "modify": self.modify,
            "download": self.download,
        }[self.args.command]
        cmd()

if __name__ == "__main__":
    App().run()
