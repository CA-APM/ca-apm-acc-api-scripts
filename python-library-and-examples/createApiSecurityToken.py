#!/usr/bin/env python

from __future__ import print_function

import pyacc

import json
import urllib
import Cookie
import getpass
import platform
import socket


def expect(res, expecting):
    if res.status != expecting:
        print("Was expecting return code", expecting)
        raise pyacc.ACCHttpException(res)


class App(pyacc.AccCommandLineApp):
    """
    Create an API token. Can use username/password if no token already exists.
    Created token will be added to ~/.acc
    """

    def build_arg_parser(self):
        """
        Add some more args to the standard set
        """
        super(App, self).build_arg_parser()

        self.parser.add_argument('--user', action="store", help='username to authenticate with the Config Server', default="user@example.com")
        self.parser.add_argument('--password', action="store", help='password to authenticate with the Config Server', default="acc")

        self.parser.add_argument('--alias', action="store", help='alias to write received token to')

        self.parser.add_argument('--description', action="store",
                                 help='description for the generated token. defaults to user@host',
                                 default="%s@%s" % (getpass.getuser(), platform.node()))

        self.parser.add_argument('-f', '--force', action='store_true', help="Force creation of a new token when one already exists")

    def check_connectivity(self, auth):
        # We can now access the rest api using that cookie for authentication
        print("Make request to the Config Server using", auth)
        res = self.acc.http_get_raw("/apm/acc", auth)

        if res.status == 200:
            json_info = json.loads(res.read())
            print("Successfully connected to the Config Server: received server version", json_info["serverVersion"])
            return True
        else:
            print("Failed to connect to the Config Server:", res.status)

        return False

    def get_cookie(self):
        data = urllib.urlencode({"username": self.args.user, "password": self.args.password})
        headers = {"content-type": "application/x-www-form-urlencoded"}

        res = self.acc.http_post_raw("/login", data, headers)
        # print(res)
        cookie = Cookie.SimpleCookie(res.getheader("Set-Cookie"))
        print("Cookie received back is", cookie.output())

        if not cookie:
            return None
        else:
            auth = {"Cookie": "ACCSESSIONID=%s" % cookie["ACCSESSIONID"].value}
            return auth

    def get_bearer_token(self):
        bearer_token = self.acc.headers.get("authorization")

        if bearer_token:
            print("Have token:", bearer_token)
            auth = {"authorization": bearer_token}
            return auth
        return None

    def get_auth(self):
        auth = self.get_bearer_token()

        if auth:
            if self.check_connectivity(auth):
                return True, auth
            else:
                print("Cannot access using that token, let's try username and password")
                auth = self.get_cookie()
        else:
            print("No bearer token picked up, will try and use username and password to create API token (using defaults unless otherwise specified)")
            auth = self.get_cookie()

            if not auth:
                print("No cookie returned from the Config Server, but I seemed to connect. Perhaps security is turned off, in which case I have nothing to do?")

                # Nothing to do, apart from create the alias, that is
                if self.args.alias:
                    print("but you have specified an alternative alias (%s), so will write an entry there" % self.args.alias)
                    self.write_profile(self.args.alias, self.acc.server, self.acc.token)

                return False, None

        if not self.check_connectivity(auth):
            raise pyacc.ACCException("Cannot connect to Config Server")

        return False, auth

    def write_profile(self, profile, server, token):

        existing_server = self.acc_env.config_get(profile, "server")

        if existing_server and existing_server != server:
            print("Will not update profile %s as it is for a different server (%s)" % (profile, existing_server))
        else:
            print("Writing token to", self.acc_env.profile_path(profile))
            self.acc_env.set_config_item(profile, "server", server)
            self.acc_env.set_config_item(profile, "token",  token)
            self.acc_env.write_config(profile)

    def main(self):

        print("Config Server:", self.acc.server)
        print("Token:", self.acc.token)

        is_bearer_token, auth = self.get_auth()

        if not auth:
            print("No authorization method discovered, quitting")
            return

        # Create token with either type of authorization (bearer token or username/password)
        if is_bearer_token and not self.args.force:
            print("Already have access with current bearer token, will not create another one. Use --force to force creation.")

            if self.args.alias and self.args.alias != self.acc_env.profile:
                print("but you have specified an alternative alias (%s), so will try and copy the token from %s there" % (self.args.alias, self.acc_env.profile))
                self.write_profile(self.args.alias, self.acc.server, self.acc.token)
            return

        print("Create new API token")

        # Create a new api token
        res = self.acc.http_post_raw("/apm/acc/private/securityToken?projection=IncludePrivateToken",
                                     '{"description": "%s"}' % self.args.description, auth)
        expect(res, 201)

        json_token = json.loads(res.read())
        print("Token successfully created:", json_token["privateToken"])

        if not is_bearer_token:
            print("Logging out session", auth)
            res = self.acc.http_get_raw("/logout", auth)
            expect(res, 302)

        profile_name = self.args.alias or self.acc_env.profile
        self.write_profile(profile_name, self.acc.server, json_token["privateToken"])

        print("Now checking connectivity with the new token", json_token["privateToken"])

        if self.check_connectivity({"authorization": "Bearer %s" % json_token["privateToken"]}):
            print("""Success.

You should now able to run the example scripts using the profile %(profile_name)s, for example
you can examine API token on the Config Server with:

tokens.py -p %(profile_name)s

or get Config Server information with:

info.py -p %(profile_name)s

You can also select the profile to use with the environment variable ACC_PROFILE
e.g.
export ACC_PROFILE=%(profile_name)s

""" % locals())

            return


if __name__ == "__main__":

    try:
        App().run()
    except pyacc.ACCConfigurationException as e:
        print("Configuration exception returned:", e)
        msg = \
"""
If this is the first time you have run this script, try specifying the --server-url parameter,
for example:

createApiSecurityToken.py --server-url https://accdemowin01.ca.com:8443
"""
        print(msg)

    except socket.error as e:
        if e.errno == 111: # connection refused
            print("Socket error: ", e)

            msg = \
"""
Is the url contactable?
Is the Config Server running?
Is the Config Server running on the specified port?

Example server url: https://accdemowin01.ca.com:8443
"""
            print(msg)

