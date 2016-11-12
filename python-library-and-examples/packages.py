#!/usr/bin/env python

from __future__ import print_function

import sys
import re

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

        create_parser = subparsers.add_parser("create")
        create_parser.add_argument('names', metavar='NAME', nargs='+', type=str, help='package name', default=[])
        create_parser.add_argument('--os', action='store', help="os type", default="unix", choices=["unix", "windows"])
        create_parser.add_argument('--appserver', action='store', help="appserver type", choices=App.appservers, default="other")
        create_parser.add_argument('--agent-version', action='store', help="agent version", default="10.2")
        create_parser.add_argument('--process-display-name', action='store', help="process display name", default="")
        create_parser.add_argument('--comment', action='store', help="package comment", default="")
        create_parser.add_argument('--em-host', action='store', help="EM host name", default="")

        modify_parser = subparsers.add_parser("modify")
        modify_parser.add_argument('-a', '--add', action='append', help="Add a bundle to a package", default=[])
        modify_parser.add_argument('-r', '--remove', action='append', help="Remove a bundle from a package", default=[])
        modify_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='*', type=str,
                                   help='package ids', default=[])

        download_parser = subparsers.add_parser("download")
        download_parser.add_argument('--format', action='store',
                                     help='write files in the given format. "archive" means zip for windows packages, tar.gz for unix packages',
                                     default="archive", choices=["zip", "tar", "tar.gz", "archive"])
        download_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='*', type=str,
                                     help='package ids', default=[])
        download_parser.add_argument('--all', action='store_true', help="also download old versions of packages")

        delete_parser = subparsers.add_parser("delete")
        delete_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='+', type=str,
                                   help='package ids')

        override_parser = subparsers.add_parser("overrides")
        override_sub_parser = override_parser.add_subparsers(help="overrides sub-command", dest="command_override")

        override_add_parser = override_sub_parser.add_parser("add")
        # # group.add_argument('--add', action='store_true', help="add overrides to a package bundle", default=False)
        override_add_parser.add_argument('--bundle', action='store', help="bundle name")
        override_add_parser.add_argument('--package', action='append', metavar='PACKAGE_ID', dest="package_ids", help="package name")
        override_add_parser.add_argument('--preamble', action='store', help="preamble text")
        override_add_parser.add_argument('--replace', action='store_true', help="replace entire existing bundle overrides (use with caution!)")
        override_add_parser.add_argument('-l', '--list', action='store_true', help="list package/bundle base properties/values")
        override_add_parser.add_argument('properties', metavar='PROPERTY=VALUE', nargs='*', type=str, help='properties')

        override_copy_parser = override_sub_parser.add_parser("copy")
        # # group.add_argument('--copy', action='store_true', help="copy overrides to another package", default=False)
        override_copy_parser.add_argument('package_ids', metavar='PACKAGE_ID', nargs='*', type=str, help='package ids')

        override_list_parser = override_sub_parser.add_parser("list")
        override_list_parser.add_argument('--bundle', action='store', help="bundle name")
        override_list_parser.add_argument('--all', action='store_true', help="include old versions of packages")
        override_list_parser.add_argument('--draft', action='store_true', help="draft versions of packages", default=False)
        override_list_parser.add_argument('--package', action='append', metavar='PACKAGE_ID', dest="package_ids", help="package name")
        override_list_parser.add_argument('ignored', metavar='IGNORED', nargs='*', type=str, help='ignored')

    def _get_packages(self):
        if self.args.package_ids:
            # Create a list of Package objects initialized with the package id.
            # The data will be fetched from the Config Server when the object
            # is queried (e.g. "package["xxx"])
            packages = self.acc.packages_many(self.args.package_ids)
        else:
            # This will fetch all packages (a page a time)
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

    def overrides(self):
        """Route override command to the handler"""
        cmd = {
            "copy": self.copy_overrides,
            "list": self.list_overrides,
            "add": self.add_overrides,
        }[self.args.command_override]
        cmd()

    def copy_overrides(self):
        src = None

        packages = self.acc.packages_many(self.args.package_ids)

        if len(packages) < 2:
            print("Need at least 2 packages (src, dest), trying listing with 'overrides list' to get the ids")
            sys.exit(1)

        for package in packages:
            package.get_json()
            if not src:
                src = package
            else:
                if src.item_id == package.item_id:
                    print("Cannot copy override onto self")
                else:
                    print("Copying overrides from %s to %s" % (src.item_id, package.item_id))
                    package.add_overrides(src["bundleOverrides"])

    def list_overrides(self):
        for package in self._get_packages():
            package.get_json()
            print("# Package id=%s, name=%s, version=%s, draft=%s, latest=%s, downloaded=%s" % (
                package.item_id, package["packageName"], package["version"], package["draft"], package["latest"],
                package["downloaded"]))

            for bundleOverride, properties in package["bundleOverrides"].iteritems():
                if self.args.bundle and bundleOverride != self.args.bundle:
                    continue

                print("\n# %s bundle overrides" % bundleOverride)

                if properties["preamble"]:
                    print("# %s" % properties["preamble"])

                # print(properties)
                for props in properties["properties"] or []:
                    # print(props)
                    print()

                    if self.args.verbose:
                        print("# (key=%s userKey=%s)" % (props["key"], props["userKey"]))

                    if props["description"]:
                        print("# %s" % props["description"].strip())

                    print("%s%s=%s" % ("#" if props["hidden"] else "",  props["name"], props["value"]))
            print()

    def add_overrides(self):

        if not self.args.package_ids:
            print("Please include a package id from:")
            self.args.all = False
            for package in self._get_packages():
                self._print_package(package)
            return

        if not self.args.bundle:
            print("Please include a bundle name from:")
            for package in self._get_packages():
                for b in package.bundles():
                    print(b["name"])
            return

        if not self.args.preamble and not self.args.replace and not self.args.properties and not self.args.list:
            # TODO list here with x=base -> x=override or something (tricky - need the map)
            print("# Nothing to do so listing existing overrides. Add --list to list base properties you may with to override:\n")
            return self.list_overrides()

        if self.args.list:
            for package in self.acc.packages_many(self.args.package_ids):
                # TODO we could validate our overrides against the overrides in the bundle
                for bundle in package.bundles():
                    if bundle["name"] == self.args.bundle:

                        print("# Base properties in bundle: %s version: %s" % (bundle["name"], bundle["version"]))
                        profile = bundle.profile()
                        profile.get_json()
                        # print(profile)

                        for prop in profile["properties"] or []:
                            print("%s=%s" % (prop["name"], prop["value"] or ""))
                        print()
                        break
                else:
                    print("didn't find bundle %s in the package" % self.args.bundle)
                    break
            return

        val_re = re.compile("^([#]?)(.*)=(.*)")

        for package in self.acc.packages_many(self.args.package_ids):
            # package.get_json()
            # print(package)
            # package.add_overrides(overrides)

            if self.args.replace:
                master = {}
            else:
                # Get the existing bundle overrides for this package
                master = package["bundleOverrides"]

            overrides = master.get(self.args.bundle)

            existing_overrides = {}

            if not overrides:
                overrides = master[self.args.bundle] = {}
            else:
                print("overrides", overrides)

                # build a lookup of non hidden existing overrides
                for bundle, properties_list in overrides.iteritems():
                    for prop in properties_list or []:
                        # print("%s%s=%s" % ("#" if prop["hidden"] else "", prop["name"], prop["value"]))
                        if not prop["hidden"]:
                            existing_overrides[prop["name"]] = prop

            if self.args.preamble:
                overrides["preamble"] = self.args.preamble

            # loop over the overrides we want to add
            for prop in self.args.properties:
                prop_split = val_re.split(prop)

                hidden = prop_split[1] == "#"
                name = prop_split[2]
                value = prop_split[3]

                properties = overrides.get("properties")

                if not properties:
                    properties = overrides["properties"] = []

                if not hidden:
                    # do any of our new properties replace the existing ones?
                    existing = existing_overrides.get(prop_split[2])

                    if existing:
                        # update the one that is there
                        print("Updating existing override %s from %s to %s" % (name, existing["value"], value))
                        existing["value"] = value
                        continue

                prop_dic = {"description": None,
                            "hidden": hidden,
                            "name":  name,
                            "value": value}

                properties.append(prop_dic)

            package.add_overrides(master)

    def main(self):

        # Route users command to the handler
        cmd = {
            "list": self.list,
            "delete": self.delete,
            "create": self.create,
            "modify": self.modify,
            "download": self.download,
            "overrides": self.overrides,
        }[self.args.command]
        cmd()

if __name__ == "__main__":
    App().run()
