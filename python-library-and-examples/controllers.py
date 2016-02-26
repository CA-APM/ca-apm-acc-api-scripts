#!/usr/bin/env python

from __future__ import print_function

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    List controllers
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()
        self.parser.add_argument('-a', '--agents', dest='agents', action='store_true',
                                 help="include agents for controller")
        self.parser.add_argument('controller_ids', metavar='CONTROLLER_ID', nargs='*', type=str,
                                 help='Query the given controller ids')

    def main(self):

        if self.args.controller_ids:
            # Create a list of Agent objects initialized with the agent id.
            # The data will be fetched from the Config Server when the object
            # is queried (e.g. "agent["agentName"])
            controllers = self.acc.controllers_many(self.args.controller_ids)
        else:
            # This will fetch all agents (a page a time)
            controllers = self.acc.controllers()

        for controller in controllers:

            if self.args.agents:
                # Print the status of the controller + agents
                print("\t".join([controller["id"], controller["serverName"], str(controller["available"])]))

                for agent in controller.agents():
                    print("\t%s" % agent["agentName"])
            else:
                # Print the status of the controller
                print("\t".join([
                    controller["id"],
                    controller["serverName"],
                    controller["version"],
                    str(controller["available"])
                ]))


if __name__ == "__main__":
    App().run()
