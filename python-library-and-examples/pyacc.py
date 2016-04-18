#!/usr/bin/env python

"""
CA ACC REST API Python client library.

James Hilling (hilja07@ca.com)

July 2015

This module provides a clean interface to CA ACC REST API, taking care of the details
of handling the handling the http/JSON details and letting you concentrate on writing the code
to solve your problem, without distraction of handling details of making and handling
REST calls.

Features:
    Automatic page handling.
    Lazy ACC objects - fetched from the server as they are used.
    Command line building classes - write a ACC command line app just a few lines of code,
    including profiles for saving access tokens.

https://wiki.ca.com/display/APMDEVOPS98/CA+APM+Command+Center+API

ConfigServer
    Controllers
        Agents
            Diagnostic Report
            Log Level

References:
https://docs.python.org/2/library/httplib.html

Github location of other scripts which use the ACC REST API:
https://github.com/CA-APM/ca-apm-acc-api-scripts

TODO

Push uploaded file to all agents

Out-of-policy agents

"""

from __future__ import print_function

import os
import sys
import errno
import argparse
import urlparse
import urllib
import httplib
import json
import pprint
import mimetypes
import datetime
import time

SERVER_URL = "https://example.com:8443"  # Can be http/8088 if security switch off on the Config Server
SECURITY_TOKEN = ""  # you will need to generate your own.  See createApiSecurityToken.py
PAGE_SIZE = 20
debug_mode = False


TASK_COMPLETED = "COMPLETED"
TASK_FAILED = "FAILED"


class ACCException(Exception):
    pass


class ACCConfigurationException(ACCException):
    def __init__(self, configuration_item):
        self.configuration_item = configuration_item

    def __str__(self):
        return "Missing configuration item: '%s'" % self.configuration_item


class ACCHttpException(ACCException):

    def __init__(self, res):
        self.res = res
        self.status = res.status
        self.reason = res.reason

        # ACC returned info
        self.error_message = None

        try:
            self.json = json.loads(res.read())
            self.error_message = self.json["errorMessage"]
        except:
            pass

    def __str__(self):
        err = "status: %s, reason: %s, message: %s" % (self.status, self.reason, self.error_message)
        # err += "\nerror json: %s" % (self.json)
        return err


def debug(msg):
    if debug_mode:
        print("DEBUG: %s" % msg, file=sys.stderr)


def safe(val):
    if val is None:
        return "None"
    return str(val)


def write_content_to_file(res, filename, chunk_size=1048576):

    # print("response headers:")
    # print(res.msg)

    if os.path.exists(filename):
        print("Skipping writing existing:", filename)
    else:
        content_length = long(res.msg["content-length"])
        print("Content length is", content_length);

        with open(filename, "wb") as fout:
            print("Fetching payload to:", filename)
            print("-" * ((content_length * 2 / chunk_size) + 2))

            while 1:
                print("r", end="")
                sys.stdout.flush()

                content = res.read(chunk_size)
                if not content:
                    break

                print("w", end="")
                sys.stdout.flush()

                fout.write(content)
        print()


def parse_date(date):
    """
    Parse dates as from the format that they are the returned from the rest api.
    Expecting date to look like this: 2016-02-25T17:29:52.418Z
    """
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")


class AccRaw(object):

    """
    A thin wrapper around around the ACC REST API.
    This is used by the higher level AccApi which is the interface designed for consumers.
    """

    def __init__(self, server=SERVER_URL, token=SECURITY_TOKEN, page_size=20):
        self.server = server
        self.url = urlparse.urlparse(server)
        self.headers = {"content-type": "application/json"}
        self.page_size = page_size
        self.token = token

        if token:
            self.headers["authorization"] = "Bearer " + token

        self.params = {}

    def _get_conn(self):
        if self.url.scheme == "https":
            return httplib.HTTPSConnection(self.url.netloc)
        elif self.url.scheme == "http":
            return httplib.HTTPConnection(self.url.netloc)
        else:
            raise ACCException("Unsupported scheme '%s' in server URL '%s'" % (
                               self.url.scheme, self.server))

    def http_get_raw(self, url, headers):

        debug("url is GET %s%s" % (self.server, url))
        debug("request headers are %s" % headers)

        conn = self._get_conn()  # create a new connection for each call.

        # def request(self, method, url, body=None, headers={}):
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        return res

    def http_get(self, part, item_id, headers=None, **kwargs):
        """
        Low-level call to do the HTTP GET to ACC ConfigServer and return
        the JSON object. Throw exception on any non 200 (OK) return codes
        """

        if item_id is None:
            url = part
        else:
            url = "%s/%s" % (part, item_id)

        debug("kwargs %s" % kwargs)

        if kwargs:
            this_params = self.params.copy()

            # If a page specified, include our default page size
            if kwargs.get("page") is not None:
                this_params["size"] = self.page_size

            # Now add any other kwargs (page, filters etc)
            this_params.update(kwargs)
            url += "?" + urllib.urlencode(this_params)

        res = self.http_get_raw(url, headers or self.headers)

        if res.status != httplib.OK:
            raise ACCHttpException(res)

        return res

    def http_get_json(self, part, item_id, **kwargs):
        return json.loads(self.http_get(part, item_id, **kwargs).read())

    def http_post_raw(self, part, body, headers):

        """
        Do a HTTP POST to ACC ConfigServer
        """

        debug("url is POST %s%s" % (self.server, part))
        debug(part)
        debug(body)
        debug(headers)

        conn = self._get_conn()
        conn.request("POST", part, body=body, headers=headers)
        res = conn.getresponse()

        return res

    def http_post(self, part, body):
        """
        Do a HTTP POST to ACC ConfigServer and return json object.
        Throw exception on any non 201 (CREATED) return codes
        """

        res = self.http_post_raw(part, body, self.headers)

        if res.status == httplib.CREATED:
            return res, json.loads(res.read())

        raise ACCHttpException(res)

    def http_post_multipart(self, part, fields, files):
        content_type, body = self._encode_multipart_formdata(fields, files)
#         print(content_type)
#         print(body)
        conn = self._get_conn()

        conn.putrequest('POST', part)

        conn.putheader('content-type', content_type)
        conn.putheader('content-length', str(len(body)))

        if self.headers.get("authorization"):
            conn.putheader('authorization', self.headers["authorization"])

        conn.endheaders()

        conn.send(body)

        res = conn.getresponse()
        # errcode, errmsg, headers = conn.getreply()

        if res.status in (httplib.CREATED, httplib.OK):
            return res, json.loads(res.read())

        raise ACCHttpException(res)

    def _encode_multipart_formdata(self, fields, files):
        limit = '----------lImIt_of_THE_fIle_eW_$'
        form = []
        for (key, value) in fields:
            form.append('--' + limit)
            form.append('Content-Disposition: form-data; name="%s"' % key)
            form.append('')
            form.append(value)

        for (key, filename, value) in files:
            form.append('--' + limit)
            form.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (
                        key, filename))
            form.append('Content-Type: %s' % self._get_content_type(filename))
            form.append('')
            form.append(value)

        form.append('--' + limit + '--')
        form.append('')
        body = '\r\n'.join(form)
        content_type = 'multipart/form-data; boundary=%s' % limit
        return content_type, body

    def http_patch_raw(self, part, body, headers):
        """
        Do a HTTP PATCH to ACC ConfigServer
        """

        debug("url is PATCH %s%s" % (self.server, part))
        debug(part)
        debug(body)
        debug(headers)

        conn = self._get_conn()
        conn.request("PATCH", part, body=body, headers=headers)
        res = conn.getresponse()

        return res

    def http_patch(self, part, body):
        res = self.http_patch_raw(part, body, self.headers)

        if res.status == httplib.OK:
            return res, json.loads(res.read())

        raise ACCHttpException(res)

    def http_delete_raw(self, url, headers):

        debug("url is DELETE %s%s" % (self.server, url))
        debug("headers are %s" % headers)

        conn = self._get_conn()  # create a new connection for each call.

        # def request(self, method, url, body=None, headers={}):
        conn.request("DELETE", url, headers=headers)
        res = conn.getresponse()
        return res

    # noinspection PyMethodMayBeStatic
    def _get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


class AccApi(AccRaw):

    """
    ACC interface for general consumption.
    """

    def __str__(self):
        self.info.get_json()
        return str(self.info)

    def __init__(self, server=SERVER_URL, token=SECURITY_TOKEN, page_size=20):
        super(AccApi, self).__init__(server, token, page_size)

        debug("Server: %s Token %s" % (server, token))

        self.info = AccInfo(self)

    def __getitem__(self, key):
        return self.info[key]

    def agent(self, item_id):
        """Create a lazily initialized Agent object"""
        return Agent(self, item_id)

    def agents(self, **kwargs):
        """Fetch agents meta-data as Agent objects"""
        return Agents(self, None, **kwargs)

    def agents_many(self, agent_ids):
        """Factory to create lots of Agent objects from a list of agent ids"""
        return [Agent(self, agent_id) for agent_id in agent_ids]

    def audit_records(self, **kwargs):
        """Fetch agents meta-data"""
        return AuditRecords(self, None, **kwargs)

    def audit_records_many(self, audit_record_ids):
        return [AuditRecord(self, audit_record_id) for audit_record_id in audit_record_ids]

    def bundle(self, item_id):
        return Bundle(self, item_id)

    def bundles(self, **kwargs):
        """Fetch bundle meta-data as Bundle objects"""
        return Bundles(self, None, **kwargs)

    def bundles_many(self, bundle_ids):
        """Factory to create lots of Bundle objects from a list of bundle ids"""
        return [Bundle(self, bundle_id) for bundle_id in bundle_ids]

    def controller(self, item_id):
        """Create a lazily initialized Controller object"""
        return Controller(self, item_id)

    def controllers(self, **kwargs):
        """Fetch controller meta-data as Controller objects"""
        return Controllers(self, None, **kwargs)

    def controllers_many(self, controller_ids):
        """Easy way to create lots of lazily initialized Controller objects from a list of ids"""
        return [Controller(self, agent_id) for agent_id in controller_ids]

    def controller_from_upgrade_id(self, upgrade_id):
        """Get a controller from the upgrade id"""
        json_obj = self.http_get_json("/apm/acc/controllerUpgradeTask", str(upgrade_id) + "/controller")
        return Controller(self, json_obj)

    def diagnostic_report(self, item_id):
        """Create a lazily initialized DiagnosticReport object"""
        return DiagnosticReport(self, item_id)

    def diagnostic_reports(self, **kwargs):
        """Fetch Diagnostic Report meta-data as DiagnosticReport objects"""
        return DiagnosticReports(self, None, **kwargs)

    def diagnostic_report_tasks(self, **kwargs):
        return DiagnosticReportTasks(self, None, **kwargs)

    def diagnostic_reports_many(self, report_ids):
        """Factory to create lots of DiagnosticReport objects from a list of report ids"""
        return [DiagnosticReport(self, report_id) for report_id in report_ids]

    def download_file(self, file_id):
        """Download file with the given file_id"""
        return self.http_get("/apm/acc/file", "%s/content" % file_id, page=None).read()

    def download_controller(self, archive_type=None, filename=None):

        if not archive_type:
            # Download the appropriate type depending on what platform we're on
            if os.name == "posix":
                archive_type = "tar"
            else:
                archive_type = "zip"

        fname = "acc-controller-package.%s" % archive_type
        res = self.http_get("/package/", fname)

        if not filename:
            filename = fname

        write_content_to_file(res, filename)

        return filename

    def files(self, **kwargs):
        """Get all available files"""
        return Files(self, None, **kwargs)

    def file_meta_many(self, file_ids):
        return [FileMeta(self, file_id) for file_id in file_ids]

    def package(self, item_id):
        return Package(self, item_id)

    def packages(self, **kwargs):
        return Packages(self, None, **kwargs)

    def packages_many(self, package_ids):
        """Factory to create lots of Package objects from a list of package ids"""
        return [Package(self, package_id) for package_id in package_ids]

    def package_create(self, name, os, appserver, em_host, agent_version, process_display_name, comment):

        body = """
{"draft":false,
"environment":{"osName":"%(os)s","process":"%(appserver)s","agentVersion":"%(agent_version)s","processDisplayName":"%(process_display_name)s"},
"bundleOverrides":{},
"emHost":"%(em_host)s",
"packageName":"%(name)s",
"comment":"%(comment)s"}
""" % locals()

        res, package_json = self.http_post("/apm/acc/package", body)

        # The returned json is a package
        return self.package(package_json)

    def security_tokens(self, **kwargs):
        return SecurityTokens(self, None, **kwargs)

    def security_tokens_many(self, sec_ids):
        return [SecurityToken(self, sec_id) for sec_id in sec_ids]

    def upload_file(self, filename):
        fields = [("name", os.path.basename(filename)),
                  ("modified", datetime.datetime.utcfromtimestamp(os.path.getmtime(filename)).isoformat())]
        files = [
            ("file", os.path.basename(filename), open(filename, "rb").read())]

        res, json_obj = self.http_post_multipart("/apm/acc/file", fields, files)

        return GenericJsonObject(self, json_obj)

    def upgrade_status(self):
        return ControllerUpgradeStatus(self, None)

    def wait_for_tasks(self, tasks, id_field="id", include_failed=True, timeout_seconds=30, loop_pause_seconds=3):
        """
        Generic task waiter/yielder (generator) utility
        """

        print("Waiting for tasks")

        timeout = time.time() + timeout_seconds

        remaining_tasks = []

        while time.time() < timeout:
            remaining_tasks = []

            print("Have %d tasks to poll, %d remaining tasks" %(len(tasks), len(remaining_tasks)))
            for task in tasks:
                # print(task)

                # print("id is", task.item_id)
                task.json = None # force a refresh of the task
                print(task[id_field], task["status"])

                if task["status"] in [TASK_COMPLETED]:
                    yield task
                elif task in [TASK_FAILED]:
                    if include_failed:
                        yield task
                else:
                    remaining_tasks.append(task)

            print("Remaining tasks is", len(remaining_tasks))

            if not remaining_tasks:
                break

            tasks = remaining_tasks

            print("sleep")
            time.sleep(loop_pause_seconds)

        if include_failed:
            # yield any remaining tasks that got left out
            for task in remaining_tasks:
                yield task


class AccEnv(object):

    """
    Get server name and security token from the environment
    or ~/.acc config file.
    """

    def __init__(self, profile, **overrides):
        self.kwargs = overrides

        self.home = os.path.expanduser('~')

        self.config_dir = os.path.join(self.home, '.acc')

        # Will be dictionary of config dictionaries (or for each profile)
        self.config = {}

        self.profile = profile or self.env_get("ACC_PROFILE")

    def read_config(self, file_path, sep='=', comment_char='#'):
        """
        Read the file passed as parameter as a properties file.
        """
        props = {}

        try:
            debug("Reading %s" % file_path)
            with open(file_path, "rt") as f:
                for line in f:
                    l = line.strip()
                    if l and not l.startswith(comment_char):
                        key, value = l.split(sep, 1)
                        props[key.strip()] = value.strip()
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

        return props

    def config_get(self, profile, key):

        # Get/read the config for our profile
        config = self.config.setdefault(profile or "default",
                                        self.read_config(self.profile_path(profile or "default")))
        return config.get(key) or ""

    # noinspection PyMethodMayBeStatic
    def env_get(self, key):
        try:
            return os.environ[key]
        except KeyError:
            pass
        return ""

    def get_must_exist(self, item):
        value = self.get_can_be_empty(item)
        if not value:
            raise ACCConfigurationException(item)
        return value

    def get_can_be_empty(self, item):
        """
        Try and read the item, checking:
        1) command line setting
        2) profile settings (read from ~/.acc)
        3) environment variable ACC_SERVER ACC_TOKEN...
        """

        # An explicitly set keyword value will always win
        value = self.kwargs.get(item)
        if value:
            debug("direct value for '%s'" % item)
            return value

        if self.profile:
            debug("retrieved value from profile '%s' for '%s'" % (self.profile, item))
            # If a profile is set, only try and read the key from the config file
            return self.config_get(self.profile, item)

        # # Otherwise try and read it as an env var
        # value = self.env_get("ACC_" + item.upper())
        # if value:
        #     debug("env value for %s" % item)
        #     return value

        # Failing that, finally try from the default section of the config file
        debug("config value, default section for: %s" % item)

        value = self.config_get(self.profile, item)

        return value

    def set_config_item(self, section, key, value):
        """
        Note that this does not write to the file. See write_config.
        """
        config = self.config.setdefault(section, {})
        config[key] = value

    def profile_path(self, profile):
        return os.path.join(self.config_dir, profile)

    def write_config(self, profile):
        if not os.path.exists(self.config_dir):
            debug("creating config dir %s" % self.config_dir)
            os.mkdir(self.config_dir, 0o700)

            if profile != "default":
                # For the first time, create this as the default profile
                debug("creating as default profile")
                self.write_config2(profile, "default")

        # Now write the actual profile
        self.write_config2(profile, profile)

    def write_config2(self, profile, profile_filename):
        profile_path = self.profile_path(profile_filename)
        debug("Writing config to profile %s" % profile_path)
        # We want the file to be created with permissions: rw------
        with os.fdopen(os.open(profile_path, os.O_WRONLY | os.O_CREAT, 0o0600), "w") as fp:
            for k, v in self.config[profile].iteritems():
                fp.write("%s = %s\n" % (k, v))

    def __getitem__(self, item):
        return self.get_can_be_empty(item)


class GenericJsonObject(object):

    def __init__(self, accapi, json_obj, **kwargs):
        self.accapi = accapi
        self.json = json_obj

        # This allow us to pass extra parameters to http_get
        self.extra_args = kwargs

        self.encoding = "UTF-8"

    def __str__(self):
        if not self.json:
            return "%s containing no json" % type(self)
        return pprint.PrettyPrinter(indent=2).pformat(self.json)

    def __repr__(self):
        return self.__str__()

    def get_json(self):
        return self.json

    def __getitem__(self, key):
        """
        This enables us to use the index operator, eg: agent["osName"]
        """
        try:
            value = self.get_json()[key]
            if hasattr(value, "encode"):
                # Handle unicode characters
                return value.encode(self.encoding)
            else:
                return value
        except KeyError:
            print("ERROR: Missing key %s.  Attributes available in the json are:\n%s" % (key, self))
            raise

    # def __getattr__(self, name):
    #     """
    #     __getattr__ gets called when a real attribute is not found.
    #     __get_attribute__ gets called for ALL attribute access.
    #     This enables us to do notation like this: agent.osName
    #     Can also do getattr(agent, "osName")
    #     """
    #     debug("searching for attribute: %s" % name)
    #     return self.__getitem__(name)


class FetchableJsonObject(GenericJsonObject):
    """
    Add the ability to be able to fetch oneself based on ones key.
    A json fragment such as Page does not have a mapping to an API call
    so that would be a plain GenericJsonObject
    """
    def __init__(self, accapi, json_obj_or_item_id):
        super(FetchableJsonObject, self).__init__(accapi, None)

        if isinstance(json_obj_or_item_id, dict):
            self.json = json_obj_or_item_id
            self.item_id = self.json["id"]
        else:
            self.item_id = json_obj_or_item_id
            self.json_obj = None

    def get_json(self):
        if not self.json:
            self.json = self.accapi.http_get_json("/apm/acc/%s" % self.my_url(), self.item_id)
        return self.json

    def my_url(self):
        return self.my_name()

    def my_name(self):
        return ""


class PagedJsonObject(GenericJsonObject):

    def __init__(self, accapi, json_obj=None, **kwargs):
        super(PagedJsonObject, self).__init__(accapi, json_obj, **kwargs)
        self.page = Page(json_obj)

    # noinspection PyMethodOverriding
    def get_json(self, item_id, page=None):

        # Need to be careful to not pass a page=None through to the http_get function
        # so build a new dictionary of keyword args and add the page to that
        if page is not None:
            args = self.extra_args.copy()
            args["page"] = page
        else:
            args = self.extra_args

        self.json = self.accapi.http_get_json("/apm/acc/%s" % self.my_url(), item_id, **args)

        # Only try and save the page if this is a paged call
        if page is not None:
            self.page = Page(self.json)
        else:
            self.page = None

        return self.json

    def my_url(self):
        return self.my_name()

    def my_name(self):
        return ""

    def new_item(self, json_obj):
        return GenericJsonObject(self.accapi, json_obj)

    def my_items(self):
        for item in self.json["_embedded"][self.my_name()]:
            x = self.new_item(item)
            yield x

    def __iter__(self):
        """
        Iterate over items, requesting one page at a time. Caller
        just sees a constant stream of agents/controllers etc.
        If a page is specified in the keyword arguments then
        only that page of data is returned.
        """
        page_specified = self.extra_args.get("page")

        if page_specified is None:
            page_number = 0
            page_specified = False
        else:
            page_number = page_specified
            debug("have a page arg: %s" % page_number)
            page_specified = True

        while True:
            self.get_json(None, page_number)

            if not self.page.has_data():
                break

            for x in self.my_items():
                yield x

            if page_specified or self.page.is_last_page():
                break
            page_number += 1

    def __getitem__(self, key):
        """
        For a PagedJsonObject we will make an API call for the id
        to retrieve an individual item.
        """
        # print("Key is", key)

        if isinstance(key, slice):
            raise Exception("Can't handle slices")
        elif isinstance(key, int):
            r = self.new_item(self.get_json(str(key)))
        else:
            r = self.new_item(self.get_json(key))

        return r


class Page(GenericJsonObject):

    def __init__(self, json_obj=None):
        super(Page, self).__init__(None, json_obj)
        if json_obj:
            self.json = json_obj["page"]

    def has_data(self):
        """Return True if the page has some data"""
        # self.json["totalElements"]
        return self.json["number"] < self.json["totalPages"]

    def is_last_page(self):
        """Return True if this is the last page"""
        return self.json["number"] == self.json["totalPages"] - 1


class AccInfo(FetchableJsonObject):

    """
    Get details of this config server
    """
    def __init__(self, accapi):
        super(AccInfo, self).__init__(accapi, None)


class Agents(PagedJsonObject):

    """
    All Agents. See AccApi.agents
    """

    def my_name(self):
        return "agent"

    def new_item(self, json_obj):
        return Agent(self.accapi, json_obj)


class Agent(FetchableJsonObject):

    """
    Agent objects are created by Controller.agents()
    """

    def __init__(self, accapi, json_obj_or_item_id):
        super(Agent, self).__init__(accapi, json_obj_or_item_id)
        self.update_id = None

    def my_name(self):
        return "agent"

    def agent_file_operation_task(self, filename, destination, operation="COPY"):
        res, json_obj = self.accapi.http_post(
            "/apm/acc/agentFileOperationTask",
            '{"agent":"agent/%s", "file":"file/%s", "destination":"%s", "operation":"%s"}' % (self.item_id,
                                                                                              filename,
                                                                                              destination,
                                                                                              operation))
        return GenericJsonObject(self.accapi, json_obj)

    def copy_file(self, filename, destination):
        return self.agent_file_operation_task(filename, destination, "COPY")

    def create_diagnostic_report(self):

        res, json_obj = self.accapi.http_post(
            "/apm/acc/diagnosticReportTask", '{"agent":"agent/%s"}' % self.item_id)

        return DiagnosticReportTask(self.accapi, json_obj)

    def set_log_level(self, value):

        res, json_obj = self.accapi.http_post(
            "/apm/acc/agentUpdateTask",
            '{"agent":"agent/%s", "property":"log4j.logger.IntroscopeAgent", "value":"%s"}' % (self.item_id, value))

        # No update id easily accessible in the json unfortunately! Would need to parse the hateous link to get the end
        self.update_id = os.path.basename(json_obj["_links"]["self"]["href"])
        return GenericJsonObject(self.accapi, json_obj)

    def task_status(self):
        """
        Get the task status of an agent
        """
        if not self.update_id:
            raise ACCException("Have no update id")

        return GenericJsonObject(self.accapi,
                                 self.accapi.http_get_json("/apm/acc/agentUpdateTask", self.update_id))

    def diagnostic_reports(self):
        """Return the diagnostic reports of the agent"""
        return DiagnosticReport(self.http_get_json("/apm/acc/agent/", self.item_id + "/diagnosticReports"))


class Controllers(PagedJsonObject):

    def my_name(self):
        return "controller"

    def new_item(self, json_obj):
        c = Controller(self.accapi, json_obj["id"])
        c.json = json_obj
        return c


class Controller(FetchableJsonObject):

    """
    See AccApi.controller
    """

    def __init__(self, accapi, json_obj_or_item_id):
        super(Controller, self).__init__(accapi, json_obj_or_item_id)
        self.agentJson = None

    def my_name(self):
        return "controller"

    def upgrade(self):
        """
        Upgrade the specified controller to the version of the ConfigServer
        """
        res, json_obj = self.accapi.http_post(
            "/apm/acc/controllerUpgradeTask", '{"controller" : "controllers/%s"}' % self.item_id)

        task = TaskStatus(self.accapi, json_obj)
        task.controller = self

        return task

    def agents(self):

        if not self.agentJson:
            self.agentJson = self.accapi.http_get_json(
                "/apm/acc/controller", str(self.item_id) + "/agents")

        try:
            for agent in self.agentJson["_embedded"]["agent"]:
                x = Agent(self.accapi, agent["id"])
                x.json = agent
                yield x
        except KeyError:
            # The controller might not have any agents
            pass


class ControllerUpgradeStatus(PagedJsonObject):
    def my_name(self):
        return "controllerUpgradeTask"

    def new_item(self, json_obj):
        return TaskStatus(self.accapi, json_obj)


# Are all tasks the same? Upgrade task? diag report task?
class TaskStatus(FetchableJsonObject):
    def my_name(self):
        return "controllerUpgradeTask"


class DiagnosticReports(PagedJsonObject):
    def my_name(self):
        return "diagnosticReport"

    def new_item(self, json_obj):
        return DiagnosticReport(self.accapi, json_obj)


class DiagnosticReport(FetchableJsonObject):
    def my_name(self):
        return "diagnosticReport"

    def filename(self):
        return "%s-%s-diagreport.zip" % (self["agentProperties"]["agentName"], self.item_id)

    def download(self, filename=None):

        if not filename:
            filename = self.filename()

        if not os.path.exists(filename):
            res = self.accapi.http_get("/apm/acc/diagnosticReport", self.item_id, format="zip")
            write_content_to_file(res, filename)

        return filename


class DiagnosticReportTasks(PagedJsonObject):
    def my_name(self):
        return "diagnosticReportTask"

    def new_item(self, json_obj):
        return DiagnosticReportTask(self.accapi, json_obj)


class DiagnosticReportTask(FetchableJsonObject):
    def my_name(self):
        return "diagnosticReportTask"

    def get_report(self):
        """Return a DiagnosticReport for the task"""
        return self.accapi.diagnostic_report(self["diagReportId"])


class Files(PagedJsonObject):
    def my_name(self):
        return "file"

    def new_item(self, json_obj):
        return FileMeta(self.accapi, json_obj)


class FileMeta(FetchableJsonObject):

    def my_name(self):
        return "file"

    def download_file(self):
        return self.accapi.download_file(self["id"])


class AuditRecords(PagedJsonObject):
    def my_name(self):
        return "auditRecord"

    def new_item(self, json_obj):
        return AuditRecord(self.accapi, json_obj)


class AuditRecord(FetchableJsonObject):
    def my_name(self):
        return "auditRecord"


class SecurityTokens(PagedJsonObject):

    def my_url(self):
        return "private/securityToken"

    def my_name(self):
        return "securityToken"

    def new_item(self, json_obj):

        # This json data has no form of id, pull one out of the hateous link
        # e.g. "https://accdemowin05.ca.com:8443/apm/acc/private/securityToken/18/principal"
        json_obj["id"] = json_obj["_links"]["principal"]["href"].split("/")[-2]

        return SecurityToken(self.accapi, json_obj)


class SecurityToken(FetchableJsonObject):

    def my_url(self):
        return "private/securityToken"

    def my_name(self):
        return "securityToken"


class Bundles(PagedJsonObject):

    def my_url(self):
        return "private/bundle"

    def my_name(self):
        return "bundle"

    def new_item(self, json_obj):
        return Bundle(self.accapi, json_obj)


class Bundle(FetchableJsonObject):

    def my_url(self):
        return "private/bundle"

    def my_name(self):
        return "bundle"

    # def profile(self):
    #     res = self.accapi.http_get_json("/apm/acc/bundle", "%s/profile" % self.item_id)
    #     p = Profile(res)
    #     return p


# A profile hangs off of a Bundle
class Profile(FetchableJsonObject):

    def my_name(self):
        return "profile"

    def my_url(self):
        return "private/bundle/%s/profile" % self.item_id

    # We have to override this as the parent class version will pass the item_id in which messes the derived url up.
    def get_json(self):
        if not self.json:
            self.json = self.accapi.http_get_json("/apm/acc/%s" % self.my_url(), None)
        return self.json


class Packages(PagedJsonObject):
    def my_name(self):
        return "package"

    def new_item(self, json_obj):
        return Package(self.accapi, json_obj)


class Package(FetchableJsonObject):
    def my_name(self):
        return "package"

    def download(self, base_dir=".", archive_format="archive", filename=None):

        print("Start initial download request")

        # Pass a custom header
        headers = self.accapi.headers.copy()
        headers["accept"] = "application/x-tar"
        res = self.accapi.http_get("/apm/acc/package", self.item_id, headers, format=archive_format)

        if not filename:
            cdisp = [h.strip() for h in res.msg["content-disposition"].split(";")]
            for c in cdisp:
                if c.startswith("filename="):
                    filename = c.split('=', 1)[1]
                    break

        if not filename:
            filename = "unknown"

        filename = os.path.join(base_dir, filename)
        write_content_to_file(res, filename)

        return filename

    def compatible_bundles(self):
        bundles = self.accapi.http_get_json("/apm/acc/package", "%s/%s" % (self.item_id, "compatibleBundles"))
        for bundle in bundles["_embedded"]["bundle"]:
            yield(Bundle(self.accapi, bundle))

    def bundles(self):
        bundles = self.accapi.http_get_json("/apm/acc/package", "%s/%s" % (self.item_id, "bundles"))
        for bundle in bundles["_embedded"]["bundle"]:
            yield(Bundle(self.accapi, bundle))

    def add_bundles(self, bundles):
        """{"bundles":["bundle/1","bundle/2"],"draft":false}"""

        body = '{"bundles":[%s]}' % ",".join((['"bundle/%s"' % b for b in bundles]))

        res, json_obj = self.accapi.http_patch("/apm/acc/package/" + str(self.item_id), body)

    def delete(self):
        res = self.accapi.http_delete_raw("/apm/acc/package/" + str(self.item_id), self.accapi.headers)
        if res.status not in (httplib.OK, httplib.NO_CONTENT):
            raise ACCHttpException(res)

    def add_overrides(self, overrides):

        body='{"bundleOverrides": %s}' % json.dumps(overrides)
        print("body is", body)

        res, json_obj = self.accapi.http_patch("/apm/acc/package/" + str(self.item_id), body)


class AccCommandLineApp(object):

    """
    Provides an easy way of writing an ACC command line tool without
    lots of boiler plate. Sets up the acc api interface (see self.acc)

    See some of the consumers of this class, e.g. controllers.py
    to see how little code is required to produce a fully fledged
    ACC command line application.
    """

    def __init__(self):
        self.acc = self.parser = self.args = self.acc_env = None
        self.parser = argparse.ArgumentParser(description=self.description())

        self.parser_group = self.parser.add_argument_group("pyacc standard options")
        self.parser_group.add_argument('--debug', action='store_true', help="print debugging information")

    def description(self):
        """
        Use the class doc string for the --help info
        """
        return self.__doc__

    def build_arg_parser(self):
        """
        Build a default set of args
        """
        group = self.parser_group.add_mutually_exclusive_group()

        group.add_argument('-p', '--profile', dest='profile', action='store', help='server connection profile from ~/.acc')

        group.add_argument(
            '--server-url', dest='server', action='store',
            help='URL to APM Command Center Server')

        self.parser_group.add_argument(
            '--security-token', dest='token', action='store',
            help='security token to use for authorization')

        self.parser_group.add_argument(
            '--page-size', dest='page_size', action='store', default=PAGE_SIZE, type=int, help='page size for multi-page requests')

    def run(self):
        self.build_arg_parser()
        self.args = self.parser.parse_args()

        if self.args.debug:
            global debug_mode
            debug_mode = not debug_mode

        self.acc_env = AccEnv(profile=self.args.profile,
                              server=self.args.server,
                              token=self.args.token)

        # Assign the server and token values depending on what AccEnv makes of it
        server = self.acc_env.get_must_exist("server")

        if not self.acc_env.profile:
            self.acc_env.profile = urlparse.urlsplit(server).hostname.split(".", 1)[0]

        token = self.acc_env.get_can_be_empty("token")

        self.acc = AccApi(server, token, self.args.page_size)
        self.main()

        # This code is to suppress "close failed in file object destructor" error and
        # IOError: [Errno 32] Broken pipe
        # when we pipe our output through head/tail etc
        try:
            sys.stdout.flush()
        except IOError as e:
            if e.errno == errno.EPIPE:
                pass
            else:
                # Something other than broken pipe, so re-raise
                raise

    def main(self):
        """
        Override this for your command line tool.
        By default, print a list of controllers
        """
        for controller in self.acc.controllers():
            print(controller)


class Examples(AccCommandLineApp):

    """Runs various API calls just for testing/example"""

    def main(self):

        acc = self.acc

        print("ACC Information")
        print(acc)
        print(acc["apiVersion"])
        print(acc["serverVersion"])

        print("All Task status")

        try:
            print("Upload file", __file__)
            x = acc.upload_file(__file__)
            print(x)
        except ACCHttpException as e:
            if e.status == 403:
                print("Uploads not allowed there - needs enabling in config")
            else:
                raise
        else:
            print("Copy that file to the agents")
            for agent in acc.agents():
                agent.copy_file(x["id"], "this_is_a_copied_file")

        print("All Diagnostic Report Tasks")
        for diagnostic_report_task in acc.diagnostic_report_tasks():
            print(diagnostic_report_task)

        print("Create diagnostic report for first active agent")
        tasks = []
        for agent in acc.agents():
            if agent["status"] == "ACTIVE":
                print(agent, "is active", "create report")

                try:
                    task = agent.create_diagnostic_report()
                except ACCHttpException as e:
                    if e.status == 303:
                        print("got a 303, probably already a task in progress, so continue")
                        continue
                    else:
                        raise
                else:
                    print(task)
                    tasks.append(task)
                    break

        for task in self.acc.wait_for_tasks(tasks, "agentId", timeout_seconds=10):

            # Now fetch the report (as json).
            print(acc.diagnostic_reports()[task["diagReportId"]])

            task.get_report().download()
        #

        print("Diagnostic Reports")
        for diagnostic_report in acc.diagnostic_reports():
            print(diagnostic_report)

        #

        print("Status of agents")
        for agent in acc.agents():

            # agent["task"] will be resolved by Agent.__getitem__()
            print("%s\t%s\t%s\t%s\t%s\t%s" % (
                agent["id"],
                agent["agentName"],
                agent["processName"],
                agent["status"],
                agent["serverName"],
                agent["logLevel"]))

        #

        print("Info on all controllers")
        for controller in acc.controllers():
            print(controller)
            print("%s\t%s\t%s\t%s\t%s" % (
                controller["id"],
                controller["serverName"],
                controller["osName"],
                controller["osVersion"],
                controller["version"]))

        #

        print("All Task status")
        one = None
        for upgrade_status in acc.upgrade_status():
            print(upgrade_status)
            one = upgrade_status["id"]

        if one:
            print("for one task status", one)
            print(acc.upgrade_status()[one])

        #

        print("Agents, fetching for individual controllers")
        for controller in acc.controllers():
            print(controller)
            for agent in controller.agents():
                print(agent)

        #

        print("Audit records")
        audit_record_id = None
        for audit_record in acc.audit_records():
            print(audit_record)

            if not audit_record_id:
                audit_record_id = audit_record["id"]

        if audit_record_id:
            print(acc.audit_records()[audit_record_id])

        #

        print("List of packages")
        for package in acc.packages():
            print(package)

            if package["latest"]:
                print("Downloading latest version of package", package["packageName"])
                package.download()


if __name__ == "__main__":
    Examples().run()
