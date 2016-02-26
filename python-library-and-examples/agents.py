#!/usr/bin/env python

from __future__ import print_function

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    List agents, with optional filtering (not when agents ids specified)
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('--glassfish', action="store_true", help='Filter on Glassfish agents')
        self.parser.add_argument('--jboss',     action="store_true", help='Filter on JBoss agents')
        self.parser.add_argument('--tomcat',    action="store_true", help='Filter on Tomcat agents')
        self.parser.add_argument('--weblogic',  action="store_true", help='Filter on Weblogic agents')
        self.parser.add_argument('--websphere', action="store_true", help='Filter on Websphere agents')
        self.parser.add_argument('--query',     action="store",
                                 help='Advanced query, e.g. --query="logLevel:info OR logLevel:debug"')

        self.parser.add_argument('--last', action="store_true", help='Sort latest agents first')
        self.parser.add_argument('--page', action="store", help='Page of data to fetch')

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

        if self.args.last:
            return "registrationTimestamp,desc"

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

            if self.args.page:
                request_params["page"] = self.args.page

            if self.args.last and self.args.page is None:
                # Only return the first page of data if we want to see the last registered
                # agents, unless a page has explicitly been specified
                request_params["page"] = 0

            # This will fetch a filtered list of agents a page a time when we iterate over it
            agents = self.acc.agents(**request_params)

        # Print the status of the agents
        cols = ("id", "agentName", "osName", "appServerName", "appServerVersion", "status", "metricCount", "version")
        print("\t".join(cols))

        for agent in agents:
            # Use a list comprehension to pull out the agent fields from the column names
            print("\t".join([str(agent[x]) for x in cols]))


if __name__ == "__main__":
    App().run()
