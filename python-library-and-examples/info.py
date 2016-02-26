#!/usr/bin/env python

from __future__ import print_function

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    Print acc info
    """

    def main(self):
        print(self.acc)
        print()
        print("\t".join([self.acc["serverVersion"], self.acc["apiVersion"]]))

if __name__ == "__main__":
    App().run()
