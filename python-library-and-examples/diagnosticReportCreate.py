#!/usr/bin/env python

from __future__ import print_function

import os
from datetime import datetime

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    Create diagnostic reports for the given agent ids and download a zip files of the reports.
    By default if there is an already existing report which is newer than 10 minutes, that report will
    be downloaded rather than a new report being generated. This is a safety mechanism to prevent generating
    too many reports on the server and unnecessary touching the agents.

    Also if there is already a report being generated for the given agent, we wait for that report and then download it
    rather than generating another one.

    If the report file already exists locally, it will not be downloaded again.

    Therefore in the event of failure during the creation of reports possibly for many agents, it is possible to re-run
    the script again for the same agents without unnecessarily generating new reports, only downloading any missing
    ones.  Consider passing a higher --minutes flag in this case depending on how much time has elapsed.

    """

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()
        self.parser.add_argument('-m', '--minutes', type=int, default=10, help='Use existing reports if newer than this threshold. Pass 0 to always create.')

        self.parser.add_argument('--all', action="store_true", help='Generate reports for all agents (use with caution)')

        self.parser.add_argument('agent_ids', metavar='AGENT_ID', nargs='*', type=int, help='Create reports for the given agent ids')

    def main(self):

        if self.args.all and self.args.agent_ids:
                print("Please specify agent ids or --all, but not both")
                return
        if self.args.all:
            agents = self.acc.agents()
        else:
            if not self.args.agent_ids:
                print("Please specify some agent ids to create diagnostic reports for, or --all")
                return
            agents = self.acc.agents_many(self.args.agent_ids)
        tasks = []

        # First build map of agents/tasks
        task_lookup = {}
        for task in self.acc.diagnostic_report_tasks(size=100):
            # print(task)
            if task["status"] != pyacc.TASK_FAILED:
                task_lookup.setdefault(task["agentId"], []).append(task)

        # Now loop for each specified agent and generate the report
        for agent in agents:
            task = None

            if self.args.minutes:
                tasks_agent = task_lookup.get(agent.item_id)
                if tasks_agent:
                    # print("Tasks for this agent are", tasks_agent)
                    # Watch the last task we collected for that agent.
                    task_agent = tasks_agent[-1]
                    cts = task_agent["completionTimestamp"]
                    if cts:
                        diff = datetime.now() - pyacc.parse_date(cts)
                        print("Have existing report which which is this old:", diff)
                        if diff.seconds < (self.args.minutes * 60):
                            # Use this one, don't create another report
                            task = task_agent
                            print("Not creating a new report for agent %s as task %s (%s) is less than %d minutes old" % (agent.item_id, task.item_id, task["status"], self.args.minutes))
            if not task:
                try:
                    task = agent.create_diagnostic_report()
                    print("Task %d created for agent %s" % (task["id"], agent["agentName"]))
                except pyacc.ACCHttpException as e:
                    if e.status == 303:
                        print("Task already in progress for agent id", agent.item_id)
                        tasks_agent = task_lookup.get(agent.item_id)
                        if tasks_agent:
                            task_agent = tasks_agent[-1]
                            if task_agent:
                                task = task_agent
                                print("Watching task id %s instead of creating new task" % task.item_id)

                    elif e.status == 404:
                        print("No such agent id", agent.item_id)
                    else:
                        raise
            if task:
                tasks.append(task)

        if not tasks:
            print("No tasks")
            return

        # Wait for tasks to complete and download

        for task in self.acc.wait_for_tasks(tasks):
            # print(task)

            if task["status"] == pyacc.TASK_COMPLETED:
                # Download the report as a zip and write to a file
                # Currently only zip format is supported
                diagnostic_report = task.get_report();

                if os.path.exists(diagnostic_report.filename()):
                    print("Report %s already exists, skipping download" % diagnostic_report.filename())
                else:
                    print("Writing", diagnostic_report.filename())
                    # print(diagnostic_report)
                    diagnostic_report.download()
            else:
                print("Ignoring this task as did not complete in time")
                print(task)

if __name__ == "__main__":
    App().run()
