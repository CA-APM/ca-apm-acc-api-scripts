/**
 * This is a Node.js (JavaScript) sample script that can be used to exercise how CA APM Command Center
 * controller upgrade task works.
 *
 * @author bariali.mahmood@ca.com
 *
 * *Read Me:
 * 1 - install Node.js from https://nodejs.org/ and then add it to your system path.
 * 2 - cd\ to the location where this script resides
 * 3 - import node js modules:
 *  [i]     npm install commander
 *  [ii]    npm install sync-request
 * 4 - to run the script, do the following to see usage options:
 *  [i]     node upgrade-controller.js -h
 *
 *  Note: server url, security token, and wait status timeout set by default.
 *  the security token might expire in which case you need to pass a newly generated
 *  token via -t|--token flag.
 */

// NodeJs modules
var program = require('commander');
var request = require('sync-request');

// tell node to ignore checking ssl cert
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// command line options
program
    .version('1.0', '-v, --version [SAMPLE-SCRIPT-VERSION]')
    .usage('[options] -s|--server [SERVER-URL] -t|--token [SECURITY-TOKEN] -l|--list [LIST] -u|--upgrade [UPGRADE] -w|--wait [STATUS-WAIT-TIMEOUT]')
    .option('-s, --server [SERVER]', 'URL to APM Command Center, default set to https://accdemowin01:8443/apm/acc')
    .option('-t, --token [SECURITY-TOKEN]', 'Security token to use for autorization')
    .option('-l, --list [LIST]', 'Display list of available out of date controllers')
    .option('-u, --upgrade [UPGRADE]', 'Specify "*" to upgrade all outdated controllers, or UUID(s) separated by "," to upgrade just selected controllers')
    .option('-w, --wait [STATUS-WAIT-TIMEOUT]', 'Default wait timeout set to (180) secs for upgrade operation to report its status. Zero means no waiting.')
    .parse(process.argv);

var argServer = program.server,
    argToken = program.token,
    argList = program.list,
    argUpgrade = program.upgrade,
    argWait = parseInt(program.wait);

var uuids = []
var serverName = [];
var taskIds = [];
var taskStatus = [];
var outDatedControllers = [];
var controllers;
var currentServerVersion;
var SERVER_URL = 'https://accdemowin01:8443/apm/acc'
var SECURITY_TOKEN  = '545b63eb-3378-4669-835f-d32cb233ffbd';
var WAIT = 180;

// reset if options passed via cmd
var serverUrl = argServer || SERVER_URL;
var securityToken = argToken || SECURITY_TOKEN;
var wait = argWait || WAIT; // if you assign argWait a string, it'll be replaced by NAN

// set headers for request
var headers = {'content-Type': 'application/json', 'authorization': 'Bearer ' + securityToken};

/**
 * sets current server version.
 */
function prepareCurrentServerVersion(){
    var resp = request(
        'GET',
        serverUrl,
        {headers: headers, timeout: 10000} //abort request after 10 sec
    );

    var parsedBody = JSON.parse(resp.getBody('utf8'));
    if (resp.statusCode !== 200) {
        console.error('%s %s', parsedBody.errorMessage, parsedBody.errorCode);
        process.exit(1);
    }

    currentServerVersion = parsedBody['serverVersion'];

    if (!currentServerVersion){
        console.error('Current server version is not defined');
        process.exit(1);
    }
    //console.info('Current server version: %s', currentServerVersion);
}

/**
 * prepares all available controllers.
 */
function prepareAllControllers () {
    var resp = request(
        'GET',
        serverUrl + '/controller?size=1000',
        {headers: headers, timeout: 10000}
    );

    var parsedBody = JSON.parse(resp.getBody('utf8'));
    if (resp.statusCode !== 200) {
        console.error('%s %s', parsedBody.errorMessage, parsedBody.errorCode);
        process.exit(1);
    }

    // All available controllers
    controllers = parsedBody['_embedded']['controller'];

    if (controllers.length === 0) {
        console.error('No controllers found...');
        process.exit(1);
    }
    //console.info('Total available controller(s): %s', controllers.length);
}

/**
 * populate outdated controllers.
 */
function populateOutdatedControllers() {
    for (var controller in controllers) {
        if (controllers[controller]['version'] !== currentServerVersion &&
            controllers[controller]['available']) {
            outDatedControllers.push(controllers[controller]);
            uuids.push(controllers[controller]['id']);
            serverName.push(controllers[controller]['serverName']);
        }
    }
    //console.info('Total outdated controller(s): %s', outDatedControllers.length);
}

/**
 * display out of date controllers
 *
 * @param controllers out of date controllers
 */
function displayOutdatedControllers() {

    // output error when no out of date controller(s) found.
    if (!outDatedControllers.length) {
        console.error('No out of Date controller found!');
        process.exit(1);
    }

    console.info('----------------------------------Out of Date Controllers----------------------------------');
    for (var controller in outDatedControllers) {
        console.info('UUID: %s Server Name: %s Available: %s Version: %s',
            outDatedControllers[controller]['id'],
            outDatedControllers[controller]['serverName'],
            outDatedControllers[controller]['available'],
            outDatedControllers[controller]['version']);
    }
    console.info('-------------------------------------------End---------------------------------------------');
}

/**
 * creates controller upgrade tasks
 */
function createControllerUpgradeTask() {

    // output error when no out of date controller(s) found.
    if (!outDatedControllers.length) {
        console.error('No out of Date controller found!');
        process.exit(1);
    }

    console.info('--------------------Controller(s) upgrade task started----------------------');
    for (var uuid in uuids) {
        var resp = request(
            'POST',
            serverUrl + '/controllerUpgradeTask',
            {
                headers: headers,
                timeout: 10000,
                body: '{"controller": "controllers/'+ uuids[uuid].toString() +'"}'
            }
        );

        console.info('Requesting upgrade of controller %s/%s', uuids[uuid], serverName[uuid]);

        var parsedBody = JSON.parse(resp.getBody('utf8'));
        if (resp.statusCode !== 201) {
            console.error('%s %s \n', parsedBody.errorMessage, parsedBody.errorCode);
        }
        else {
            console.info('Controller upgrade task id: %s created', parsedBody.id);
            taskIds.push(parseInt(parsedBody.id));
        }
    }
}

/**
 * pools for controller upgrade status to see if they're completed.
 */
function checkUpgradeControllerTaskStatus() {

    var upgradeErrors;

    if (!taskIds.length > 0) {
        console.info('No task(s) ID found, length is %s...', taskIds.length);
        process.exit(1);
    }
    var timeout = new Date(new Date().getTime() + (wait * 1000));
    console.info('\nWaiting %s secs for the upgrade task(s) to finish.....', wait);
    while (new Date() < timeout) {
        for (var taskId in taskIds) {
            var resp = request(
                'GET',
                serverUrl + '/controllerUpgradeTask/' + taskIds[taskId],
                {headers: headers}
            );

            var parseBody = JSON.parse(resp.getBody('utf8'));
            if (resp.statusCode !== 200) {
                console.error('%s %s', parseBody.errorMessage, parseBody.errorCode);
            }

            if (parseBody.status === 'COMPLETED' && taskStatus.indexOf(taskIds[taskId]) === -1) {
                taskStatus.push(taskIds[taskId]);
                console.info('Upgrade of controller %s/%s %s', uuids[taskId], serverName[taskId], parseBody.status);
            }

            if (parseBody.status === 'FAILED' && taskStatus.indexOf(taskIds[taskId]) === -1) {
                taskStatus.push(taskIds[taskId]);
                try {
                    upgradeErrors = parseBody.upgradeErrors;
                }
                catch (ex) {
                    upgradeErrors = '[]';
                }
                console.info('Upgrade of controller %s/%s %s with errors: %s', taskId, serverName[taskId], parseBody.status, upgradeErrors);
            }

            if (taskStatus.length === taskIds.length) {
                console.info('---------------------------------Completed---------------------------------');
                process.exit(1);
            }
        }
    }
}

/**
 * Driver.
 */
function main() {

    if(serverUrl && serverUrl.toString() === 'true') program.help();
    if (securityToken && securityToken.toString() === 'true') program.help();

    prepareCurrentServerVersion();// prepares current server version
    prepareAllControllers();// fetches all available controllers
    populateOutdatedControllers(); // list of outDated controllers

    if (argList) {
        displayOutdatedControllers();
        process.exit(1);
    }

    if (argUpgrade && argUpgrade.toString() === 'true') program.help();

    if (argUpgrade === '*') {
        createControllerUpgradeTask();
        checkUpgradeControllerTaskStatus();
    }
    else {
        uuids = argUpgrade.split(',');
        createControllerUpgradeTask();
        checkUpgradeControllerTaskStatus();
    }
}

/**
 * RUN THE SCRIPT
 */
main();