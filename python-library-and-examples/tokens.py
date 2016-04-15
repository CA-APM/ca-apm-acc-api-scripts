#!/usr/bin/env python

from __future__ import print_function

import pyacc


class App(pyacc.AccCommandLineApp):
    """
    List security tokens, sorted by last used by date (latest first)
    """
    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('token_ids', metavar='TOKEN_ID', nargs='*', type=str,
                                 help='Query the given token ids')

        self.parser.add_argument('--delete', action="store_true", help='Delete keys')

    def main(self):

        if self.args.delete and not self.args.token_ids:
            print("Need to specify token ids to delete")
            exit(1)

        if self.args.token_ids:
            # Create a list of Agent objects initialized with the agent id.
            # The data will be fetched from the Config Server when the object
            # is queried (e.g. "agent["agentName"])
            tokens = self.acc.security_tokens_many(self.args.token_ids)
        else:
            # This will fetch all agents (a page a time)
            tokens = self.acc.security_tokens(sort="lastUsedTimestamp,desc")

        print("\t".join(["id", "lastUsedTimestamp", "creationTimestamp", "description"]))

        for token in tokens:

            try:
                print("\t".join([
                    token.item_id,
                    token["lastUsedTimestamp"],
                    token["creationTimestamp"],
                    token["description"],
                ]))
            except pyacc.ACCHttpException as e:
                if e.status == 404:
                    print("%s\tnot found" % token.item_id)
                    continue
                else:
                    raise
            else:
                if self.args.token_ids and self.args.delete:
                    print("Deleting token", token.item_id)

                    res = self.acc.http_delete_raw("/apm/acc/private/securityToken/%s" % token.item_id, self.acc.headers)

                    if res.status != 204:
                        print("Failed to delete, rc", res.status)
                    else:
                        print("Successfully deleted token id", token.item_id)


if __name__ == "__main__":
    App().run()


