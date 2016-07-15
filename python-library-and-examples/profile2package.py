#!/usr/bin/env python

from __future__ import print_function

import pyacc
import pickle
import os
import sys
import re

from distutils.version import LooseVersion

from pyacc import safe

CACHE_FILE = "/tmp/bundle_property_cache"


class App(pyacc.AccCommandLineApp):
    """
    Create a package based on the content of the IntroscopeAgent.profile.
    The Bundles included in the package are chosen based on the content of the profile.
    TODO create overrides for any unknown profile items.
    """

    appservers = ["other", "ctg-server", "glassfish", "interstage", "jboss", "tomcat", "weblogic", "websphere"]

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('-v', '--verbose', action='store_true', help="be more verbose")

        self.parser.add_argument('--name', action='store', help="name", default="package")
        self.parser.add_argument('--os', action='store', help="os type", default="unix", choices=["unix", "windows"])
        self.parser.add_argument('--appserver', action='store', help="appserver type", choices=App.appservers)
        self.parser.add_argument('--agent-version', action='store', help="agent version", default="10.2.0.22")
        self.parser.add_argument('--process-display-name', action='store', help="process display name", default="")
        self.parser.add_argument('--comment', action='store', help="package comment", default="")
        self.parser.add_argument('--em-host', action='store', help="EM host name", default="")
        self.parser.add_argument('--format', action='store',
                                     help='write files in the given format. "archive" means zip for windows packages, tar.gz for unix packages',
                                     default="archive", choices=["zip", "tar", "archive"])
        self.parser.add_argument('introscope_profile', metavar='introscope_profile', nargs='*', type=str, help='Introscope Profile')

    def make_property_map(self):
        bm = {}

        for bundle in self.acc.bundles():

            if self.args.verbose:
                bundle["id"]
                print(bundle)
            else:
                # Print the bundle details
                print("\t".join([
                    str(bundle["id"]),
                    safe(bundle["name"]),
                    safe(bundle["version"]),
                    # safe(bundle["displayName"]),
                    # safe(bundle["description"]),
                    # safe(bundle["compatibility"]),
                    # safe(bundle["excludes"]),
                    # safe(bundle["facets"]),
                    # safe(bundle["installInstructions"]),
                    # safe(bundle["path"]),
                    # safe(bundle["dependencies"]),
                ]))

            profile = bundle.profile()
            # profile.get_json()
            # print(profile)

            # The map looks like this
            # {"propname": {"bundlename}": {"bundleversion"}: bundle }}

            # i.e. property name -> bundle name -> bundle version
            bundle.profile_map = {}
            print("Bundle %s:%s" % (bundle["name"], bundle["version"]))

            for prop in profile["properties"] or []:
                if not prop["hidden"]:
                    # print(prop)
                    bundle_entry = bm.setdefault(prop["name"], {})
                    bundle_entry2 = bundle_entry.setdefault(bundle["name"], {})
                    bundle_entry2.setdefault(bundle["version"], bundle)

                    # Save a map of the properties within the bundle object so they get saved in the pickle
                    print("  %s=%s" % (prop["name"], prop["value"]))
                    bundle.profile_map[prop["name"]] = prop["value"]

        # print("This is the big map")
        # print(bm)

        return bm

    def is_appserver(self, bundle):
        for f in bundle["facets"]:
            print(f)
            if f == "appserver":
                return True
        return False

    def add_override(self, bundle, prop, value):
        d = self.overrides.setdefault(bundle, {})
        d[prop] = value

    def lookup(self, prop, value):

        bundle_entry = self.bm.get(prop)

        if not bundle_entry:
            print("Unknown property '%s'" % prop)
            self.add_override("java-agent", prop, value)
        else:
            last_bundle = None

            for bundle_name, versions in bundle_entry.iteritems():
                print("Found property '%s' in bundle '%s'" % (prop, bundle_name))
                for version, bundle in versions.iteritems():
                    try:
                        print("  %s:%s:%s\t\t%s=%s" % (bundle["id"], bundle["name"], bundle["version"], prop, bundle.profile_map[prop]))
                    except KeyError:
                        print("This is the profile map for", bundle["name"], bundle["version"])
                        print(bundle.profile_map)
                        raise

                bundle_appropriate_version = self.select_version(bundle_name, versions)

                if bundle_appropriate_version:

                    try:
                        bundle_appropriate_version.HITCOUNT +=1 # tag this on
                    except AttributeError:
                        bundle_appropriate_version.HITCOUNT = 1

                    if self.appserver and self.is_appserver(bundle_appropriate_version):
                        print("Ignoring bundle %s as already have an appserver %s" % (bundle_appropriate_version["name"], self.appserver["name"]))
                    elif not last_bundle:
                        if not self.appserver and bundle_appropriate_version.profile_map[prop] == value:
                            if self.is_appserver(bundle_appropriate_version):
                                self.appserver = bundle_appropriate_version
                                print("HAVE AN APPSERVER BUNDLE", self.appserver)

                        print("Initially selecting", bundle_appropriate_version["name"])
                        last_bundle = bundle_appropriate_version

                    elif last_bundle.profile_map[prop] == value:
                        print("Sticking with", last_bundle["name"])
                    else:
                        if bundle_appropriate_version.profile_map[prop] == value:
                            print("Taking bundle %s over %s" % (bundle_appropriate_version["name"], last_bundle["name"]))
                            last_bundle = bundle_appropriate_version
                        else:
                            print("Sticking with original", last_bundle["name"])

            if last_bundle:
                print("Finally Adding %s for %s" % (last_bundle["name"], prop))
                self.included_bundles[last_bundle["name"]] = last_bundle

                if not last_bundle.profile_map.get(prop):
                    # This means that the value appears in one version of the bundle, but not the one we selected.
                    print("Adding missing property as an override")
                    self.add_override(last_bundle["name"], prop, value)
                elif last_bundle.profile_map[prop] != value:
                    print("Adding override", last_bundle.profile_map[prop], value)
                    self.add_override(last_bundle["name"], prop, value)

    def select_version(self, bundle_name, versions):
        """
        TODO This needs to take compatibility into account
        """
        exist = self.included_bundles.get(bundle_name)

        if exist:
            print("Already selected version %s for bundle %s" % (exist["version"], bundle_name))
            return exist
        else:
            v = versions.get(self.args.agent_version)
            if v:
                print("Found desired version %s for bundle %s" % (v["version"], bundle_name))
                return v
            else:
                # Pick the highest version
                vmax = None
                for version, bundle in versions.iteritems():
                    v = LooseVersion(version), bundle
                    print("Have %s" % v[0])
                    if not vmax:
                        vmax = v
                    elif v[0] > vmax[0]:
                        vmax = v
                    else:
                        # stick with what we've got
                        pass
                if vmax:
                    print("Selected %s:%s" % (vmax[1]["name"], vmax[1]["version"]))
                    return vmax[1]

        return None

    def split_property(self, prop):
        prop_split = self.val_re.split(prop)
        # print("prop_split", prop_split)

        hidden = prop_split[1] == "#"
        name = prop_split[2].strip()
        value = prop_split[3].strip()
        return hidden, name, value

    def main(self):
        self.val_re = re.compile("^([#]?)(.*)=(.*)")

        self.included_bundles = {}
        self.appserver = None
        self.overrides = {}

        if os.path.exists(CACHE_FILE):
            print("Reading bundle property index from cache", CACHE_FILE)

            with open(CACHE_FILE, "r") as fin:
                self.bm = pickle.load(fin)
        else:
            print("Building bundle property index", CACHE_FILE)
            self.bm = self.make_property_map()

            with open(CACHE_FILE, "w") as fout:
                pickle.dump(self.bm, fout)

        if self.args.introscope_profile:
            for name in self.args.introscope_profile:
                print(name)
                with open(name, "r") as fobj:
                    self.do_one(fobj)
        else:
            print("Reading properties from stdin")
            self.do_one(sys.stdin)

    def do_one(self, fileobj):

        for raw in fileobj:
            line = raw.strip()
            if not line or line[0] == "#":
                continue
            try:
                hidden, name, value = self.split_property(line)
                if not hidden:
                    print("\nSearching for %s(=%s)" % (name, value))
                    self.lookup(name, value)
                else:
                    print("Skip hidden property %s" % name)
            except IndexError as e:
                print("Failed to process", line.strip())

        print("\ndetected appserver is %s\n" % self.appserver)

        print("\nThese are the selected bundles:\n")

        for bundle in self.included_bundles.itervalues():
            print("%s:%s:%s (%d)" % (bundle["id"], bundle["name"], bundle["version"], bundle.HITCOUNT))

        # TODO add overrides to the package
        print("These are the overrides")
        for bundle, props in self.overrides.iteritems():
            print("\n# BUNDLE: %s" % bundle)
            for prop, value in props.iteritems():
                print("%s=%s" % (prop, value))

        self.create_package()

    def create_package(self):

        appserver = self.args.appserver or (self.appserver and self.appserver["name"])

        if not appserver:
            print("ERROR: Could not automatically determine appserver type - please specify with --appserver")
            sys.exit(1)

        print("Creating package for %s" % appserver)

        # Need to derive the version of the agent we are creating.
        # So find the version of the java package and base it on that?
        java_agent = self.included_bundles["java-agent"]
        agent_version = java_agent["agentVersion"]
        v2 = ".".join(agent_version.split(".")[0:2])

        print("Creating package at version %s" % v2)

        new_package = self.acc.package_create(name=self.args.name,
                                              os=self.args.os,
                                              appserver=appserver,
                                              em_host=self.args.em_host,
                                              agent_version=v2,
                                              process_display_name=self.args.process_display_name or appserver,
                                              comment=self.args.comment,
                                              draft=False)

        bundles = [b["id"] for b in self.included_bundles.values()]
        print("Adding bundles to package:", bundles)
        new_package.add_bundles(bundles)

        filename = new_package.download(".", self.args.format)

        print("wrote", filename)

        # for prop in ["introscope.agent.pmi.enable.wsgwModule", "introscope.agent.sqlagent.sql.artonly"]:

if __name__ == "__main__":
    App().run()
