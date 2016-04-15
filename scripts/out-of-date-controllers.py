#
# This is a sample Python script that uses APM Command Center API to manage
# of out-of-date Controllers.
#

import argparse, urlparse, httplib, json, time


SERVER_URL="https://accdemowin01:8443"
SECURITY_TOKEN="42f0c437-7f5f-48d0-9f6f-cdec84ab2f0c"
STATUS_WAIT_TIMEOUT=180 #secs

parser = argparse.ArgumentParser(description='Handles out-of-date Controllers of CA APM Command Center')
parser.add_argument('-s', '--server-url', dest='server', action='store', default=SERVER_URL,
						 help='URL to APM Command Center Server. Uses %s by default.' % (SERVER_URL, ))
parser.add_argument('-t', '--security-token', dest='token', action='store', default=SECURITY_TOKEN,
						 help='Security token to use for authorization')
parser.add_argument('-w', '--wait', dest='timeout', action='store', default=STATUS_WAIT_TIMEOUT,
						 help='Wait TIMEOUT(180) secs for upgrade operation to report its status. Zero means no waiting.')
actionGroup = parser.add_mutually_exclusive_group(required=True)
actionGroup.add_argument('-l', '--list', dest='list', action='store_true',
						 help='Display a list of available out-of-date controllers')
actionGroup.add_argument('-u', '--upgrade', dest='uuid', action='store', nargs='*', 
						 help='Upgrade controllers. Specify UUIDs to upgrade just selected Controllers.')
args = parser.parse_args()


url = urlparse.urlparse(args.server)
headers = {"content-Type":"application/json", "authorization":"Bearer " + args.token}
if url.scheme == "https":
	# Python 2.7.9 introduced validation of certificate as default
	# To switch it off replace the conn =... line with the following ones:
    #import ssl
	#sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
	#sslContext.verify_mode = ssl.CERT_NONE
	#conn = httplib.HTTPSConnection(url.netloc, context=sslContext)
	conn = httplib.HTTPSConnection(url.netloc)
elif url.scheme == "http":
	conn = httplib.HTTPConnection(url.netloc)
else:
	exit("Unsupported scheme '%s' in server URL '%s'" % (url.scheme, args.server, ))

uuids=[]

if args.uuid:
	uuids = args.uuid
	
serverNames={}

# Get current server version
conn.request("GET", "/apm/acc", headers=headers)
res = conn.getresponse()
if res.status != 200:
	exit("%s %s" % (res.status, res.reason, ))

currentVersion = json.loads(res.read())["serverVersion"]
print "Current version: " + currentVersion

# Get controllers not in current version. Note that controller version should match server version here.
# No paging is supported here, just one huge page consisting of up to 1000 controllers
conn.request("GET", "/apm/acc/controller?size=1000", headers=headers)
res = conn.getresponse()
if res.status != 200:
	exit("%s %s" % (res.status, res.reason, ))

if args.list:
	print "Out of date Controllers:"
	print '{:<37} {:<20} {:<12} {:<12}'.format("UUID:", "Server Name:", "Available:", "Version:")
	print '------------------------------------  -------------------- ------------ ------------'
try:
	controllers = json.loads(res.read())["_embedded"]["controller"]
except:
	exit("No controllers found...")
for controller in controllers:
	if controller["version"] != currentVersion:
		if controller["available"]:
			if not args.uuid:
				uuids.append(controller["id"])
			available = "yes"
		else:
			available = "no"
		serverNames[controller["id"]] = controller["serverName"]
		if args.list:
			print '{:<37} {:<20} {:<12} {:<12}'.format(controller["id"], controller["serverName"], available, controller["version"])
if args.list:
	exit()

taskId={}

for uuid in uuids:
	print "Requesting upgrade of controller %s/%s..." % (uuid, serverNames[uuid], )
	conn.request("POST", "/apm/acc/controllerUpgradeTask", body="{\"controller\" : \"controllers/%s\"}" % (uuid, ), headers=headers)
	res = conn.getresponse()
	if res.status == 201:
		resId = json.loads(res.read())["id"]
		print " -> Controller upgrade task id=%s created" % (resId, )
		taskId[uuid]=resId
	elif res.status == 404:
		errorMessage = json.loads(res.read())["errorMessage"]
		print " -> %s-%s: %s" % (res.status, res.reason, errorMessage)
	else:
		print " -> %s-%s" % (res.status, res.reason, )

taskStatus={}

if args.timeout > 0 and len(taskId) > 0:
	print "Waiting %ssecs for the upgrade task(s) to finish..." % (args.timeout, )
	timeout = time.time() + int(args.timeout)
	while time.time() < timeout:
		for uuid in taskId:
			conn.request("GET", "/apm/acc/controllerUpgradeTask/%s" % (taskId[uuid], ), headers=headers)
			res = conn.getresponse()
			if res.status == 200:
				status = json.loads(res.read())["status"]
				if status == "COMPLETED" and not uuid in taskStatus:
					taskStatus[uuid]=status
					print " -> Upgrade of controller %s/%s %s" % (uuid, serverNames[uuid], status, )
				if status == "FAILED" and not uuid in taskStatus:
					taskStatus[uuid]=status
					try:
						upgradeErrors = json.loads(res.read())["upgradeErrors"]
					except ValueError:
						upgradeErrors = "[]"
					print " -> Upgrade of controller %s/%s %s with errors: %s" % (uuid, serverNames[uuid], status, upgradeErrors, )
			else:
				print " -> %s-%s" % (res.status, res.reason, )
		if len(taskStatus) == len(taskId):
			break
		time.sleep(3)
