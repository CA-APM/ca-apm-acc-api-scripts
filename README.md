# CA APM Command Center API Scripts

## Description

A suite of example scripts utilizing CA APM Command Center API for automating typical tasks.

See [CA APM Command Center RESTful API](https://wiki.ca.com/display/APMDEVOPS98/CA+APM+Command+Center+API) for more information.

Also included under `python-library-and-examples` is a python wrapper library 
(`pyacc.py`) and associated sample scripts as an alternative method of writing
ACC utility scripts.

## License
[Apache License, Version 2.0, January 2004](http://www.apache.org/licenses/). See [Licensing](https://communities.ca.com/docs/DOC-231150910#license) on the CA APM Developer Community.


## Installation Instructions

### Prerequisites

* [CA APM Command Center](https://wiki.ca.com/display/APMDEVOPS98/CA+APM+Command+Center) Server version 1.1.
* Security token generated in the CA APM Command Center Web UI. See [API Authentication and Authorization](https://wiki.ca.com/display/APMDEVOPS98/API+Authentication+and+Authorization) for more information.
* The scripts directory downloaded to your local drive.

### Dependencies

* The (*.py) script(s) require Pyhton 2.7 or higher
* The (*.groovy) script(s) require Groovy 3 or higher
* The (*.js) script(s) require Node JS with commander and sync-request modules
* The (*.sh) script(s) require Bash with GNU toolset (curl version 7.18.0 or higher).

### Installation

Follow [the instructions](http://www.groovy-lang.org/install.html) on how to install the latest version of Groovy.

Install [Node.js](https://nodejs.org) and then add it to your system path.
While in the directory where this scripts resides import the modules:

	npm install commander
	npm install sync-request


### Running the scripts

All scripts require providing valid server URL and security token either as command line option argument or by hardcoding them in the scripts.
The following code snippets assume the latter.

**The agent-diag-report.groovy script**

Command line help:

	> groovy agent-diag-report.groovy --help                                                                   
	usage: agent-diag-report.groovy [options] --dir|-d <DIR> --query|-q
									<QUERY>
	Uses APM Command Center API to automate download of diagnostic reports for
	APM Agents matching query criteria
	-d,--dir <DIR>                Path to target directory for reports
	-h,--help                     This help screen
	-q,--query <QUERY>            Query for the Agents to get report(s) for.
								Use '*' to get reports for all Agents (use
								with caution).
	-s,--server-url <SERVER>      URL to APM Command Center Server. Uses
								https://accdemowin01:8443 by default.
	-t,--security-token <TOKEN>   Security token to use for authorization

	Sample query: --query "serverName:ACCDemo* AND appServerName:Tomcat"

Sample output:

	> groovy agent-diag-report.groovy --dir /tmp/reports --query "serverName:ACCDemo*"
	Requesting diagnostic report for Tomcat Agent (Tomcat) on host ACCDemoLinux01...
	-> Diagnostic report id=74 initiated
	Requesting diagnostic report for Tomcat Agent (Tomcat) on host ACCDemoWin01...
	-> Diagnostic report id=75 initiated
	Waiting for diagnostic report(s) to finish...
	-> Report id=74 for Tomcat Agent (Tomcat) on host ACCDemoLinux01 COMPLETED
	-> Report id=75 for Tomcat Agent (Tomcat) on host ACCDemoWin01 COMPLETED
	All diagnostic report(s) finished
	Downloading reports...
	Jul 23, 2015 4:55:21 PM groovyx.net.http.ParserRegistry getAt
	WARNING: Cannot find parser for content-type: application/zip -- using default parser.
	-> File /tmp/reports/ACCDemoLinux01_Tomcat_Tomcat+Agent-74-20150723-155650.zip downloaded, extracting to /tmp/reports...done
	Jul 23, 2015 4:55:23 PM groovyx.net.http.ParserRegistry getAt
	WARNING: Cannot find parser for content-type: application/zip -- using default parser.
	-> File /tmp/reports/ACCDemoWin01_Tomcat_Tomcat+Agent-75-20150723-155650.zip downloaded, extracting to /tmp/reports...done

**The agent-log-level.sh script**

Command line help:

	> ./agent-log-level.sh --help
	Uses APM Command Center API to automate handling of log levels of APM Agents
	matching query criteria

	Usage: ./agent-log-level.sh <COMMAND> [OPTIONS]

	Commands:
	-l, --list             Lists log levels for APM Agents matching query
		--set=<LOG_LEVEL>  Sets log level for APM Agents matching query
	-r, --reset            Resets log level to default INFO for APM Agents matching
						query
	Options:
	-h, --help             This help screen
	-q, --query=<QUERY>    Query to match APM Agents. If not specified, all agents
						are included in the result.
	-s, --server-url=<URL> URL to APM Command Center Server.
						Uses https://accdemowin01:8443 by default.
	-t, --security-token <TOKEN>
						Security token to use for authorization
	Sample queries:
	--query='osName:"Windows Server 2008" OR serverName:ACCDemoLinux01'

Sample outputs:

	> ./agent-log-level.sh --list -q='serverName:accdemo*'
	ID:    Agent name:     Process name:   Status:  Server name:    Log level:
	------ --------------- --------------- -------- --------------- ----------
	101    Tomcat Agent    Tomcat          ACTIVE   ACCDemoLinux01  INFO      
	102    Tomcat Agent    Tomcat          ACTIVE   ACCDemoWin01    INFO

	> ./agent-log-level.sh --set=debug --query='serverName:accdemo*'
	Setting Log Level on matching APM Agents...
	Requesting Log Level change from INFO to DEBUG on APM Agent ACCDemoLinux01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/38"
	Requesting Log Level change from INFO to DEBUG on APM Agent ACCDemoWin01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/39"

	> ./agent-log-level.sh --reset --query='serverName:accdemo*'
	Setting Log Level on matching APM Agents...
	Requesting Log Level change from DEBUG to INFO on APM Agent ACCDemoLinux01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/40"
	Requesting Log Level change from DEBUG to INFO on APM Agent ACCDemoWin01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/41"

**The out-of-date-controllers.py script**

Command line help:

	> python out-of-date-controllers.py --help             
	usage: out-of-date-controllers.py [-h] [-s SERVER] [-t TOKEN] [-w TIMEOUT]
									(-l | -u [UUID [UUID ...]])

	Handles out-of-date Controllers of CA APM Command Center

	optional arguments:
	-h, --help            show this help message and exit
	-s SERVER, --server-url SERVER
							URL to APM Command Center Server
	-t TOKEN, --security-token TOKEN
							Security token to use for authorization
	-w TIMEOUT, --wait TIMEOUT
							Wait TIMEOUT(180) secs for upgrade operation to report
							its status. Zero means no waiting.
	-l, --list            Display a list of available out-of-date controllers
	-u [UUID [UUID ...]], --upgrade [UUID [UUID ...]]
							Upgrade controllers. Specify UUIDs to upgrade just
							selected Controllers.

Sample outputs:

	> python out-of-date-controllers.py --list
	Current version: 99.99.accEagle-SNAPSHOT
	Out of date Controllers:
	UUID:                                 Server Name:         Available:   Version:
	------------------------------------  -------------------- ------------ ------------
	4d62fc3a-0000-4192-8341-a99b21a4dc50  Host-0               yes          1.1
	4d62fc3a-0001-4192-8341-a99b21a4dc50  Host-1               yes          1.1
	4d62fc3a-0002-4192-8341-a99b21a4dc50  Host-2               yes          1.1
	4d62fc3a-0003-4192-8341-a99b21a4dc50  Host-3               yes          1.1
	4d62fc3a-0004-4192-8341-a99b21a4dc50  Host-4               yes          1.1

	> python out-of-date-controllers.py -u
	Current version: 99.99.accEagle-SNAPSHOT
	Requesting upgrade of controller 4d62fc3a-0000-4192-8341-a99b21a4dc50/Host-0...
	-> Controller upgrade task id=57 created
	Requesting upgrade of controller 4d62fc3a-0001-4192-8341-a99b21a4dc50/Host-1...
	-> Controller upgrade task id=58 created
	Requesting upgrade of controller 4d62fc3a-0002-4192-8341-a99b21a4dc50/Host-2...
	-> Controller upgrade task id=59 created
	Requesting upgrade of controller 4d62fc3a-0003-4192-8341-a99b21a4dc50/Host-3...
	-> Controller upgrade task id=60 created
	Requesting upgrade of controller 4d62fc3a-0004-4192-8341-a99b21a4dc50/Host-4...
	-> Controller upgrade task id=61 created
	Waiting 180 secs for the upgrade task(s) to finish...
	-> Upgrade of controller 4d62fc3a-0002-4192-8341-a99b21a4dc50/Host-2 COMPLETED
	-> Upgrade of controller 4d62fc3a-0003-4192-8341-a99b21a4dc50/Host-3 COMPLETED
	-> Upgrade of controller 4d62fc3a-0001-4192-8341-a99b21a4dc50/Host-1 COMPLETED
	-> Upgrade of controller 4d62fc3a-0004-4192-8341-a99b21a4dc50/Host-4 COMPLETED
	-> Upgrade of controller 4d62fc3a-0000-4192-8341-a99b21a4dc50/Host-0 COMPLETED

**The upgrade-controller.js script (NodeJS version of out-of-date-controllers.py)**

Command line help:

	> node upgrade-controller.js -h

	Usage: upgrade-controller [options] -s|--server [SERVER-URL] -t|--token [SECURITY-TOKEN] -l|--list [LIST] -u|--upgrade [UPGRADE] -w|--wait [STATUS-WAIT-TIMEOUT]

	Options:

		-h, --help                             output usage information
		-v, --version [SAMPLE-SCRIPT-VERSION]  output the version number
		-s, --server [SERVER]                  URL to APM Command Center, default set to https://accdemowin01:8443/apm/acc
		-t, --token [SECURITY-TOKEN]           Security token to use for autorization
		-l, --list [LIST]                      Display list of available out of date controllers
		-u, --upgrade [UPGRADE]                Specify "*" to upgrade all outdated controllers, or UUID(s) separated by "," to upgrade just selected controllers
		-w, --wait [STATUS-WAIT-TIMEOUT]       Default wait timeout set to (180) secs for upgrade operation to report its status. Zero means no waiting.

Sample outputs:

To view all out of date controllers

	> node upgrade-controller.js -l
	----------------------------------Out of Date Controllers----------------------------------
	UUID: 4d62fc3a-0000-4192-8341-a99b21a4dc50 Server Name: Host-0 Available: true Version: 1.1
	UUID: 4d62fc3a-0001-4192-8341-a99b21a4dc50 Server Name: Host-1 Available: true Version: 1.1
	UUID: 4d62fc3a-0002-4192-8341-a99b21a4dc50 Server Name: Host-2 Available: true Version: 1.1
	UUID: 4d62fc3a-0003-4192-8341-a99b21a4dc50 Server Name: Host-3 Available: true Version: 1.1
	UUID: 4d62fc3a-0004-4192-8341-a99b21a4dc50 Server Name: Host-4 Available: true Version: 1.1
	-------------------------------------------End---------------------------------------------

Upgrade all controllers with "*"

	> node upgrade-controller.js -u *
	--------------------Controller(s) upgrade task started----------------------
	Requesting upgrade of controller 4d62fc3a-0000-4192-8341-a99b21a4dc50/Host-0
	Controller upgrade task id: 111 created
	Requesting upgrade of controller 4d62fc3a-0001-4192-8341-a99b21a4dc50/Host-1
	Controller upgrade task id: 112 created
	Requesting upgrade of controller 4d62fc3a-0002-4192-8341-a99b21a4dc50/Host-2
	Controller upgrade task id: 113 created
	Requesting upgrade of controller 4d62fc3a-0003-4192-8341-a99b21a4dc50/Host-3
	Controller upgrade task id: 114 created
	Requesting upgrade of controller 4d62fc3a-0004-4192-8341-a99b21a4dc50/Host-4
	Controller upgrade task id: 115 created

	Waiting 180 secs for the upgrade task(s) to finish.....
	Upgrade of controller 4d62fc3a-0000-4192-8341-a99b21a4dc50/Host-0 COMPLETED
	Upgrade of controller 4d62fc3a-0001-4192-8341-a99b21a4dc50/Host-1 COMPLETED
	Upgrade of controller 4d62fc3a-0002-4192-8341-a99b21a4dc50/Host-2 COMPLETED
	Upgrade of controller 4d62fc3a-0003-4192-8341-a99b21a4dc50/Host-3 COMPLETED
	Upgrade of controller 4d62fc3a-0004-4192-8341-a99b21a4dc50/Host-4 COMPLETED
	---------------------------------Completed---------------------------------

Upgrade selected controllers, note; they're separated by ","

	> node upgrade-controller.js -u 4d62fc3a-0000-4192-8341-a99b21a4dc50,4d62fc3a-0001-4192-8341-a99b21a4dc50
	--------------------Controller(s) upgrade task started----------------------
	Requesting upgrade of controller 4d62fc3a-0000-4192-8341-a99b21a4dc50/Host-0
	Controller upgrade task id: 116 created
	Requesting upgrade of controller 4d62fc3a-0001-4192-8341-a99b21a4dc50/Host-1
	Controller upgrade task id: 117 created

	Waiting 180 secs for the upgrade task(s) to finish.....
	Upgrade of controller 4d62fc3a-0001-4192-8341-a99b21a4dc50/Host-1 COMPLETED
	Upgrade of controller 4d62fc3a-0000-4192-8341-a99b21a4dc50/Host-0 COMPLETED
	---------------------------------Completed---------------------------------

**The copy-file.sh script**

_This script requires to [Enable API File Operation Tasks](https://wiki.ca.com/display/APMDEVOPS98/Enable+API+File+Operation+Tasks) that are disabled by default._

Usage:

	usage:
	-s <server>
		Command Center Server to use. Default is https://localhost:8088/
	-f <file>
		File to upload and send to agents.  Default is ./new.pbd
	-t <token>
		Security token to use.
	-d <destination>
		File name and directory to use on the remote agents.
		Default is my-new.pbd
	-q <query>
		Query to use to search for agents. Default is *all* agents.

Sample outputs:

	> ./copy-file.sh –s https://reema03-newdev:8088/

	Fetching agents ...
	ID:    Server name:    Process name:   Agent name:
	----------------------------------------------------
	1      reema03-test1   Tomcat          MyNewAgent
	2      Host-0          Tomcat          Agent-0
	3      Host-0          Weblogic        Agent-1
	4      Host-0          Tomcat          Agent-2
	5      Host-0          Weblogic        Agent-3
	6      Host-0          Tomcat          Agent-4
	7      Host-0          Weblogic        Agent-5
	8      Host-0          Tomcat          Agent-6
	9      Host-0          Weblogic        Agent-7
	10     Host-0          Tomcat          Agent-8
	11     Host-0          Weblogic        Agent-9

	Uploading file

	File new.pbd uploaded. Id is 91

	Starting copy tasks ...
	--------------
	New       = 11
	Queued    = -
	Started   = -
	Completed = -
	Failed    = -
	--------------
	New       = 4
	Queued    = 3
	Started   = -
	Completed = 4
	Failed    = -
	--------------
	New       = -
	Queued    = -
	Started   = -
	Completed = 11
	Failed    = -


## Support
This document and associated tools are made available from CA Technologies as examples and provided at no charge as a courtesy to the CA APM Community at large. This resource may require modification for use in your environment. However, please note that this resource is not supported by CA Technologies, and inclusion in this site should not be construed to be an endorsement or recommendation by CA Technologies. These utilities are not covered by the CA Technologies software license agreement and there is no explicit or implied warranty from CA Technologies. They can be used and distributed freely amongst the CA APM Community, but not sold. As such, they are unsupported software, provided as is without warranty of any kind, express or implied, including but not limited to warranties of merchantability and fitness for a particular purpose. CA Technologies does not warrant that this resource will meet your requirements or that the operation of the resource will be uninterrupted or error free or that any defects will be corrected. The use of this resource implies that you understand and agree to the terms listed herein.

Although these utilities are unsupported, please let us know if you have any problems or questions by adding a comment to the CA APM Community Site area where the resource is located, so that the Author(s) may attempt to address the issue or question.
