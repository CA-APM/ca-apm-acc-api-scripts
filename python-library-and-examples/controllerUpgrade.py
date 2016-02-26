#!/usr/bin/env python

from __future__ import print_function

import time

import pyacc

STATUS_WAIT_TIMEOUT = 180  # secs


class App(pyacc.AccCommandLineApp):

    """
    List controllers which are not running the current version in the CA APM Command Center
    and optionally upgrade them.
    """

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument(
            '-w', '--wait', dest='timeout', action='store', default=STATUS_WAIT_TIMEOUT,
            help="""Wait TIMEOUT(180) secs for upgrade operation to report its status.
                                    Zero means no waiting.""")

        self.parser.add_argument(
            '-l', '--list', dest='list', action='store_true',
                                 help='Display a list of available out-of-date controllers')
        self.parser.add_argument(
            '-u', '--upgrade', dest='uuid', action='store', nargs='*',
            help='Upgrade controllers. Specify UUIDs to upgrade just selected Controllers.')

        self.parser.add_argument('-t', '--tasks', action='store_true', help="list tasks")

    def main(self):

        # Get controllers that do not match current_version.
        # TODO Could we do a query to do this?
        args = self.args

        if not args.tasks and not args.list and args.uuid is None:
            args.list = True

        if args.tasks:
            self.list_status()

        if args.list or args.uuid is not None:

            if args.uuid:
                # Create a controller object for each uuid specified
                controllers = self.acc.controllers_many(args.uuid)
            else:
                # Get the list of all controllers
                controllers = self.acc.controllers()

            # Get the current version of the ConfigServer.
            # We want the controllers to match this
            current_version = self.acc["serverVersion"]
            print("Current version:", current_version)

            print("Out of date Controllers:")
            print('{:<37} {:<28} {:<12} {:<12}'.format(
                "UUID:", "Server Name:", "Available:", "Version:"))
            print('-' * 37, '-' * 28, '-' * 12, '-' * 12)

            # Print the status of the controllers
            controllers_upgrading = []
            for controller in controllers:
                if controller["version"] != current_version:
                    if controller["available"]:
                        available = "yes"
                    else:
                        available = "no"

                    print('{:<37} {:<28} {:<12} {:<12}'.format(controller["id"],
                                                               controller[
                                                                   "serverName"],
                                                               available, controller["version"]))

                    if not args.list and available == "yes":
                        # Request the upgrade of out of date controllers
                        controllers_upgrading.append(controller.upgrade())

            if args.list:
                return

            # Check upgrade status
            if args.timeout > 0 and controllers_upgrading:

                print("Waiting %s secs for %d upgrade task(s) to finish..." % (args.timeout,
                                                                               len(controllers_upgrading)))

                for upgrade_status in self.acc.wait_for_tasks(controllers_upgrading, timeout_seconds=args.timeout):

                    # TODO put the status in an enum in the module
                    if upgrade_status["status"] == pyacc.TASK_COMPLETED:
                        print("%s\t%s\t%s" % (upgrade_status.controller["serverName"],
                                              upgrade_status["currentVersion"],
                                              upgrade_status["status"]))
                    else:
                        print("Did not complete", upgrade_status, upgrade_status.controller)

    def list_status(self):

        """
        ACC RESTApi does not provide a way of getting task status grouped by controller,
        so let's do it here.

        First request the status of all tasks, and create a dictionary of controllers
        which contains the list of tasks.
        """

        dic = {}

        for task in self.acc.upgrade_status():
            upgrade_id = task["id"]

            controller = self.acc.controller_from_upgrade_id(upgrade_id)
            controller_id = controller["id"]

            dic.setdefault(controller_id, []).append(task)

        cols = ("controller_id", "id", "status", "creationTimestamp", "completionTimestamp", "currentVersion")
        print("\t".join(cols))

        for controller_id, tasks in dic.iteritems():
            for task in tasks:
                print("\t".join([controller_id] + [str(task[x]) for x in cols[1:]]))
            print()

if __name__ == "__main__":
    App().run()




