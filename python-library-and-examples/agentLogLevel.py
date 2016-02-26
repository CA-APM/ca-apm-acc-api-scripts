#!/usr/bin/env python

from __future__ import print_function

import pyacc


# TODO should be able to specifiy agent ids
class App(pyacc.AccCommandLineApp):
    """
    Show or set the log level of connected agents
    """

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument(
            '-u', '--update', dest='update', action='store',
            help="update to value")

        self.parser.add_argument('agent_ids', metavar='AGENT_ID', nargs='*', type=str, help='Use the given agent ids')

    def main(self):

        if self.args.agent_ids:
            # Create a list of Agent objects initialized with the agent id.
            # The data will be fetched (and cached) from the Config Server when the object
            # is first queried (e.g. "agent["agentName"]).  Further queries on the object
            # will not re-fetch it from the server.
            agents = self.acc.agents_many(self.args.agent_ids)
        else:
            agents = self.acc.agents()

        # Print the status of the agents
        for agent in agents:

            # agent["x"] will be resolved by Agent.__getitem__()
            print("%s\t%s\t%s\t%s\t%s\t%s" % (
                  agent["id"],
                  agent["agentName"],
                  agent["processName"],
                  agent["status"],
                  agent["serverName"],
                  agent["logLevel"]))

            if self.args.update and agent["logLevel"] != self.args.update:
                print("Updating log level from %s to %s" % (agent["logLevel"], self.args.update))

                try:
                    agent.set_log_level(self.args.update)
                    print("update task is", agent.update_id)

                    # Check the status of the last
                    s = agent.task_status()
                    print("status", s)
                except pyacc.ACCHttpException as e:
                    print("Problem setting log level:", e)


if __name__ == "__main__":
    App().run()
