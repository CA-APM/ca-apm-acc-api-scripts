#!/usr/bin/env python

from __future__ import print_function

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    List agents that are not running the latest version of their package,
    with optional filtering.
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('-v', '--verbose', action='store_true', help="be more verbose")
        self.parser.add_argument('--glassfish', action="store_true", help='Filter on Glassfish agents')
        self.parser.add_argument('--jboss',     action="store_true", help='Filter on JBoss agents')
        self.parser.add_argument('--tomcat',    action="store_true", help='Filter on Tomcat agents')
        self.parser.add_argument('--weblogic',  action="store_true", help='Filter on Weblogic agents')
        self.parser.add_argument('--websphere', action="store_true", help='Filter on Websphere agents')
        self.parser.add_argument('--query',     action="store",
                                 help='Advanced query, e.g. --query="logLevel:info OR logLevel:debug"')

        # Which package states to include. If none of these 3 are specified, then all are printed.
        self.parser.add_argument('--latest', action="store_true", help='Display Agents with latest packages')
        self.parser.add_argument('--ood', action="store_true", help='Display Agents with out of date packages')
        self.parser.add_argument('--no-package', action="store_true", help='Display Agents with no package version')

        self.parser.add_argument('--no-summary', action="store_true", help='Do no print summary information')

        self.parser.add_argument('agent_ids', metavar='AGENT_ID', nargs='*', type=str, help='Query the given agent ids')

    def get_filter(self):
        """Build a filter based on the command line args"""
        q = []
        self.args.tomcat and q.append("appServerName:Tomcat")
        self.args.websphere and q.append("appServerName:Websphere")
        self.args.weblogic and q.append("appServerName:Weblogic")
        self.args.glassfish and q.append("appServerName:Glassfish")
        self.args.jboss and q.append("appServerName:JBoss")
        self.args.query and q.append(self.args.query)

        return " OR ".join(q)

    def get_sort_order(self):

        return "agentName,asc"

    def main(self):

        if self.args.agent_ids:
            # Create a list of Agent objects initialized with the agent id.
            # The data will be fetched (and cached) from the Config Server when the object
            # is first queried (e.g. "agent["agentName"]).  Further queries on the object
            # will not re-fetch it from the server.
            agents = self.acc.agents_many(self.args.agent_ids)
        else:
            request_params = {}

            agent_filter = self.get_filter()

            if agent_filter:
                request_params["q"] = agent_filter

            sort_order = self.get_sort_order()

            if sort_order:
                request_params["sort"] = sort_order

            # This will fetch a filtered list of agents a page a time when we iterate over it
            agents = self.acc.agents(**request_params)

        if not self.args.ood and not self.args.latest and not self.args.no_package:
            self.args.ood = self.args.latest = self.args.no_package = True

        # Print the status of the agents
        cols = ("a-id", "server", "process", "agent", "p-id", "version", "compliance")
        print("\t".join(cols))

        latest_count = ood_count = no_package_count = 0

        for agent in agents:

            pd = agent["packageDetails"]

            if not pd:
                no_package_count += 1
                if not self.args.no_package:
                    continue
                else:
                    pd = {"id": "-", "version": "-", "latest": "No package"}
            else:
                is_latest = bool(pd["latest"])
                pd["latest"] = "latest" if is_latest else "out of date!"

                if is_latest:
                    latest_count += 1
                    if not self.args.latest:
                        continue
                else:
                    ood_count += 1
                    if not self.args.ood:
                        continue

            print("\t".join([str(agent["id"]),
                            agent["serverName"],
                            agent["processName"],
                            agent["agentName"],
                            str(pd["id"]),
                            str(pd["version"]),
                            pd["latest"]
                             ]))

        if not self.args.no_summary:
            total = no_package_count + ood_count + latest_count
            pct = 0
            if total > 0:
                pct = (latest_count/float(total)) * 100

            print("""
Agent Package compliance summary:

  %d total agents.

  %d agents have no package.

  %d agents have an outdated package.
  %d agents have the latest package.

  %g%% agents are running the latest package version

""" % (total, no_package_count, ood_count, latest_count, pct))

if __name__ == "__main__":
    App().run()
