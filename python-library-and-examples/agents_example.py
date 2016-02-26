#!/usr/bin/env python
import pyacc
class App(pyacc.AccCommandLineApp):
    """List agents along with os and app server info"""
    def main(self):
        for agent in self.acc.agents():
            print "\t".join([agent["agentName"], agent["osName"], agent["appServerName"]])
if __name__ == "__main__":
    App().run()