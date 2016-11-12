# CA APM Command Center API Scripts

# Short Description

This extension provides a suite of example scripts using the CA APM Command Center API for automating typical tasks.

# Description

This extension provides a suite of example scripts using the CA APM Command Center API for automating typical tasks.

The extension `python-library-and-examples` contains a python wrapper library (`pyacc.py`) and associated sample scripts for alternative methods of writing APM Command Center utility scripts.

For installation instructons, see the ReadMe.MD file.

# License GUENTER IS THIS OK?
[Apache License, Version 2.0, January 2004](http://www.apache.org/licenses/).

# Prerequisites
* CA APM Command Center Server version 1.1 or later
* Security token generated in the CA APM Command Center Web UI. See [API Authentication and Authorization](https://wiki.ca.com/display/APMDEVOPS98/API+Authentication+and+Authorization) for more information.
* The scripts directory in the extension downloaded to your local drive.

# Dependencies
* The (*.py) script(s) require Pyhton 2.7 or higher (see comments in the scripts for changes for SSL handling introduced in Python 2.7.9)
* The (*.groovy) script(s) require Groovy 3 or higher
* The (*.js) script(s) require Node JS with commander and sync-request modules
* The (*.sh) script(s) require Bash with GNU toolset (curl version 7.18.0 or higher) and [the jq JSON parser](https://stedolan.github.io/jq/).

# Install Groovy and Node.js

1. Follow [the instructions](http://www.groovy-lang.org/install.html) on how to install the latest version of Groovy.
2. Install [Node.js](https://nodejs.org) and then add it to your system path.
3. While in the directory where this scripts resides import these modules:
	'<npm install commander>'
	'<npm install sync-request>'

# Install the Extension

## Install Using CA APM Control Center

### 10.5 

1. Download the bundle (extension) from the CA APM Marketplace.
   http://marketplace.ca.com/shop/ca/?cat=29
2. Go to the Bundles page and click the **Import** button.
2. Navigate to the downloaded bundle and click **Open**.
3. On the Packages page, add the bundle to the desired package.

### 10.2 and 10.3

1. Download the extension (bundle) from the CA APM Marketplace.
   http://marketplace.ca.com/shop/ca/?cat=29
2. Navigate to the downloaded bundle.
3. Copy the bundle to the <APMCommandCenterServer>/import directory. 
   The bundle is automatically imported into the APM Command Center database and moved to the bundles directory.

## Install the Extension Manually

### 10.5 and later

1. Download the extension from the CA APM Marketplace.
   http://marketplace.ca.com/shop/ca/?cat=29
2. Navigate to the downloaded extension and untar the file into the <*Agent_Home*> directory.
3. Copy the .tar file to the <*Agent_Home*>/extensions/deploy directory.
   The agent automatically automatically installs and deploys the extension, which starts monitoring the managed application.

### 10.3 and earlier

1. Download the extension from the CA APM Marketplace.
   http://marketplace.ca.com/shop/ca/?cat=29
2. Navigate to the downloaded extension and unzip or untar the file as appropriate into the <*Agent_Home*> directory.
3. Add the extension jar file to the <*Agent_Home*>/core/ext directory.
4. Add the .pbd or pbl files to the <*Agent_Home*>/core/config directory.
5. Update the IntroscopeAgent.profile file
6. Navigate to <*Agent_Home*>/core/config to update the IntroscopeAgent.profile file.
7. Add the .pbl files to the directives in the IntroscopeAgent.profile.

# Run Scripts
All scripts require providing valid server URL and security token either as command line option argument or by hardcoding them in the scripts.
The following code snippets assume the latter.

## Agent-diag-report.groovy script

Command line help:

	> groovy agent-diag-report.groovy --help
	usage: agent-diag-report.groovy [options] --dir|-d <DIR> --query|-q
									<QUERY>
	Uses the APM Command Center API to automate download of diagnostic reports for
	CA APM Agents matching query criteria
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

## Agent-log-level.sh script

Command line help:

	> ./agent-log-level.sh --help
	Uses APM Command Center API to automate handling of log levels of CA APM agents.
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
	Setting Log Level on matching CA APM agents.
	Requesting Log Level change from INFO to DEBUG on CA APM agent ACCDemoLinux01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/38"
	Requesting Log Level change from INFO to DEBUG on APM Agent ACCDemoWin01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/39"

	> ./agent-log-level.sh --reset --query='serverName:accdemo*'
	Setting Log Level on matching CA APM agents.
	Requesting Log Level change from DEBUG to INFO on APM Agent ACCDemoLinux01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/40"
	Requesting Log Level change from DEBUG to INFO on APM Agent ACCDemoWin01/Tomcat Agent/Tomcat
	-> Created "https://accdemowin01:8443/apm/acc/agentUpdateTask/41"

## Out-of-date-controllers.py script

Command line help:

	> python out-of-date-controllers.py --help
	usage: out-of-date-controllers.py [-h] [-s SERVER] [-t TOKEN] [-w TIMEOUT]
									(-l | -u [UUID [UUID ...]])

	Handles out-of-date Controllers of CA APM Command Center

	optional arguments:
	-h, --help            show this help message and exit
	-s SERVER, --server-url SERVER
							URL to CA APM Command Center Server
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

## Upgrade-controller.js script (NodeJS version of out-of-date-controllers.py)

Command line help:

	> node upgrade-controller.js -h

	Usage: upgrade-controller [options] -s|--server [SERVER-URL] -t|--token [SECURITY-TOKEN] -l|--list [LIST] -u|--upgrade [UPGRADE] -w|--wait [STATUS-WAIT-TIMEOUT]

	Options:

		-h, --help                             output usage information
		-v, --version [SAMPLE-SCRIPT-VERSION]  output the version number
		-s, --server [SERVER]                  URL to CA APM Command Center, default set to https://accdemowin01:8443/apm/acc
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

## Copy-file.sh script

This script is required to enable CA APM Command Center API file operation tasks.

Usage:

	usage:
	-s <server>
		Command Center Server to use. Default is https://localhost:8088/
	-f <file>
		File to upload and send to agents. Default is ./new.pbd
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


# Support
This document and extension are made available from CA Technologies. They are provided as examples at no charge as a courtesy to the CA APM Community at large. This extension might require modification for use in your environment. However, this extension is not supported by CA Technologies, and inclusion in this site should not be construed to be an endorsement or recommendation by CA Technologies. This extension is not covered by the CA Technologies software license agreement and there is no explicit or implied warranty from CA Technologies. The extension can be used and distributed freely amongst the CA APM Community, but not sold. As such, it is unsupported software, provided as is without warranty of any kind, express or implied, including but not limited to warranties of merchantability and fitness for a particular purpose. CA Technologies does not warrant that this resource will meet your requirements or that the operation of the resource will be uninterrupted or error free or that any defects will be corrected. The use of this extension implies that you understand and agree to the terms listed herein.
Although this extension is unsupported, please let us know if you have any problems or questions. You can add comments to the CA CA APM Community site so that the author(s) can attempt to address the issue or question.
Unless explicitly stated otherwise this extension is only supported on the same platforms as the CA APM Java agent. 

# Product Compatibilty Matrix
http://pcm.ca.com/

# Categories

Examples GUENTER IS THIS OK?

# Change Log
Changes for each extension version.

Version | Author | Comment
--------|--------|--------
1.0 | Guenter Grossberger | First version of the extension.