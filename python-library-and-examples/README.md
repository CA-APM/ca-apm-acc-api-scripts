# 10.2 ca-apm-acc-python-api
CA-ACC REST API python wrapper + examples/utilities. The CA APM Control 
Center exposes a
[REST API](https://docops.ca.com/ca-apm/10/en/administrating/ca-apm-command-center/ca-apm-command-center-api)
providing advanced administration and reporting capabilities.

### Pre-amble

This repository contains a Python library (`pyacc.py`) which makes access to 
the REST API simple and transparent by abstracting the complexities of making 
REST calls and encapsulating the API data in easy to use data types.

This allows the prospective ACC script writer to focus on coding the solution 
for their particular problem by writing regular python code *without* getting 
bogged down with the complexities of handling authentication/tokens, paging, 
encoding/decoding request/response json data etc.

The `pyacc.py` library also includes helper classes which make writing command
line driven scripts *really* easy, and many examples are included which take 
advantage of this ability.

Indeed, it is possible to write some very powerful scripts with the minimum 
code and complexity required by the consumer, which is best shown by looking 
at an example.

This examples contained herein were tested using python 2.7.6 on Linux.

### Example - list registered agents

Here is a script to list the agents registered with the ACC Config Server in 
only 8 lines of Python:

```
import pyacc
class App(pyacc.AccCommandLineApp):
    """List agents along with os and app server info"""
    def main(self):
        for agent in self.acc.agents():
            print "\t".join([agent["agentName"], agent["osName"], agent["appServerName"]])
if __name__ == "__main__":
    App().run()
```

Depending on how many agents are returned, this will produce several 
screenfuls of data.  Behind the scenes, the API will be requesting a page of 
data at a time from the Config Server, but our example script doesn't see any of 
that complexity - it simply receives a stream of agent information from the 
returned data from `self.acc.agents()`.


```
Agent-0	Microsoft Windows	Tomcat
Agent-1	Microsoft Windows	Tomcat
Agent-2	Microsoft Windows	Tomcat
Agent-3	Microsoft Windows	Tomcat
Agent-4	Microsoft Windows	Tomcat
Agent-5	Microsoft Windows	Tomcat
Agent-6	Microsoft Windows	Tomcat
Agent-7	Microsoft Windows	Tomcat
  :
  :
```

That's not all - even from those few lines of code, the example script has 
command line usage and some useful options:

```
$ ./agents_example.py  --help
usage: agents_example.py [-h] [--debug] [-p PROFILE | --server-url SERVER]
                         [--security-token TOKEN] [--page-size PAGE_SIZE]

List agents along with os and app server info

optional arguments:
  -h, --help            show this help message and exit
  --debug               Print debugging information
  -p PROFILE, --profile PROFILE
                        server connection profile from ~/.acc
  --server-url SERVER   URL to APM Command Center Server
  --security-token TOKEN
                        security token to use for authorization
  --page-size PAGE_SIZE
                        page size for multi-page requests

```

Notice how the doc string for the class in the example has automatically 
been used for the usage help text, a good example of leveraging the power of 
Python.

Other features we get provided by the library "for free" are:

* --debug

    This will cause the program to print out debugging information including 
    the URL of the REST calls. This is useful if you are experiencing 
    connectivity or other errors.

* --profile and --server-url: see section below on Profiles.

* --page-size

    This specifies the size of each chunk of data that will be returned from 
    the server. The default is 20. If working with a large volumes of 
    return data this can be increased to increase throughput.

### Profiles

You might be wondering how the example knew which server to connect to in 
order to fetch the agent list.  You might also be wondering how it 
authenticated with the server.

We could specify this as command line parameters like this:
```
$ ./agents_example.py --server-url="https://accdemowin05.ca.com:8443" --security-token 2f53b8b1-75b2-4d4b-b778-a896d6fc4b58
```

*The security token can be created in the ACC UI from the drop down in the 
right hand side of the screen in the dropdown called "API Tokens". (More on 
a faster way to do this later.)*

To avoid having to keep specifying these parameters by hand, a feature of 
the class our example is derived from (`AccCommandLineApp`),  is the concept of 
*profiles*. This is simply a way of being able to store a set of connection 
details to a Config Server with an abstract "profile" name.  The profile 
itself simply a text file with the information stored under ~/.acc/, for 
example:

```
$ cat ~/.acc/demo5 
token = 2f53b8b1-75b2-4d4b-b778-a896d6fc4b58
server = https://accdemowin05.ca.com:8443
```

*Take care with the permissions on that file - make sure the read access is 
restricted as the security tokens stored in it are secret information.*

So we could then run our example like this:

```
$ ./agents_example.py --profile=demo5
```

If no profile is specified, then a profile called `~/.acc/default` will be used
which would then reduce our command to simply:
```
$ ./agents_example.py
```

Also it is possible to specify the default profile by exporting the environment
variable `ACC_PROFILE`, for example:

```
export ACC_PROFILE=demo5
```

### Authentication

A quick and easy alternative to using the UI to create the required security 
token is to use the included helper script `createApiSecurityToken.py`
which will create the token for you and automatically write it into a 
profile.  It will pass the default out-of-the-box ACC username and password 
unless otherwise specified to achieve this. So if you have changed the 
default username and password then these need to specified as command line 
parameters to the script (see script usage message for more info).

```
$ ./createApiSecurityToken.py --server-url https://accdemowin02.ca.com:8443 
Config Server: https://accdemowin02.ca.com:8443
Token: 
No bearer token picked up, will try and use username and password to create API token (using defaults unless otherwise specified)
Cookie received back is Set-Cookie: ACCSESSIONID=qze0xs7nfj8c2fl39wssenfo; Path=/
Make request to the Config Server using {'Cookie': 'ACCSESSIONID=qze0xs7nfj8c2fl39wssenfo'}
Successfully connected to the Config Server: received server version 10.2.0.16
Create new API token
Token successfully created: b17ac310-acbc-425b-9639-b4b52a77063a
Logging out session {'Cookie': 'ACCSESSIONID=qze0xs7nfj8c2fl39wssenfo'}
Writing token to /home/hilja07/.acc/accdemowin02
Now checking connectivity with the new token b17ac310-acbc-425b-9639-b4b52a77063a
Make request to the Config Server using {'authorization': u'Bearer b17ac310-acbc-425b-9639-b4b52a77063a'}
Successfully connected to the Config Server: received server version 99.99.accFalcon-SNAPSHOT
Success.

You are now able to run the example scripts using the profile accdemowin02, for example:

agents.py -p accdemowin02


```

Notice how it wrote the token to `~/.acc/accdemowin02`

```
$ cat ~/.acc/accdemowin02
token = 27d23664-7f79-42ca-a5e9-1158b74d439e
server = https://accdemowin02.ca.com:8443
```

And now we can run `./agents.py -p accdemowin02` etc.

### The sample scripts

Here is a brief overview of some of the scripts included.  See the scripts
themselves for full details or their usage messages with --help.


#### pyacc.py

This is the ACC client library itself. This is what the subsequent scripts 
use to access the ACC data.  The file contains some examples at the end in 
the class `Examples`.  Running the pyacc.py from the command line will 
execute the example code.


#### createApiSecurityToken.py

Run this first to create an API security token for you and write it to a 
profile.  The profile can then be used by the other scripts. Also has some
simple diagnostics of common response errors.


#### tokens.py

This will list the API tokens that exist on the server, along with last used 
info etc.  Can delete tokens with this script (use with caution).


#### info.py

Dumps information about the connected Config Server including version 
information.


#### controllers.py

On a single physical machine, 1 or more Agents talk to a single Controller which 
talks to a Config Server.

This script lists controllers registered with the Config Server.  Can also 
list the agents reporting to that controller with the -a flag.


#### agents.py

Lists agents, optionally filtering by agent type by passing pre-defined flags, 
for example to list tomcat and weblogic agents:
```
$ ./agents.py --tomcat --weblogic
```


#### agentLogLevel.py

List/set agent log level. A log level change creates an audit record.


#### auditRecords.py

List audit records. 


#### diagnosticReportCreate.py

Create diagnostic reports for the given agent ids and download and write out
as a zip file.


#### diagnosticReports.py

List previsouly generated diagnostic reports, or list diagnostic report tasks


#### download.py

Download files for the given file ids from the Config Server or list available
files


#### upload.py

Upload files to config server. Note that the file upload option needs to be 
enabled on the Config Server (agent.file.management.enabled=true in 
APMCommandCenterServer/config/apmccsrv.properties)


#### bundles.py

List bundle information.  Bundles are small pieces of Agent which are 
combined together to make a complete APM Agent Package which can then be 
downloaded and deployed (see `packages.py`).


#### packages.py

List packages / add new bundles to packages / create new packages / download 
packages.

This script uses a command line subparser e.g. it can be called like with 
one of the actions list, create, modify, download and each of these actions
has its own options which can be queried with --help.

```
$ ./packages.py list|create|modify|download --help
```


Global options still apply and can be applied before the actions, e.g.

```
$ ./packages.py --profile accdemo1 list
```

For example here we create a package for the tomcat server, then view it, 
before modifying it by adding an extra bundle and finally downloading it.


```
$ ./packages.py create --appserver=tomcat mypackage # package id returned, assume 1
$ ./packages.py list --bundles 1 # list bundles for package 1
$ ./packages.py modify --add 38 1 # add bundle id 38 to package 1
$ ./packages.py download 1 # download package 1
```


#### profiles.py

List IntroscopeAgent profiles fragments associated with bundles


#### controllerUpgrade.py

List controllers which are not running the current version in the CA APM 
Command Center and optionally upgrade them.


### Writing your own scripts

Hopefully the examples provided give enough reference or building blocks for
enhancing for your own needs.


Any feedback/fixes/suggestions/enhancements gratefully received!


### FAQ / Troubleshooting

Q) I get a 401 exception when I run my script

A) Unauthorized - you need to make sure you have an API token to be able to 
communicate with the Config Server.  See the script createApiSecurityToken.py.


Q) I get exception: "Missing configuration item: 'server'"

A) The script needs to know which Config Server to talk to.  See the "Profiles" 
section above.

Q) How do I get more inforation about what is happening when my script is running?

A) Pass the --debug flag to the script








