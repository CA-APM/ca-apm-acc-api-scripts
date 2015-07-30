/*
 * This is a sample bash script that uses APM Command Center API to manage
 * of log level of APM Agents.
 *
 */

@Grab('org.codehaus.groovy.modules.http-builder:http-builder:0.7.1')

import groovyx.net.http.ContentType
import groovyx.net.http.HTTPBuilder
import groovyx.net.http.Method

import java.util.zip.ZipFile

def SERVER_URL = "https://accdemowin01:8443"
def SECURITY_TOKEN = "2bb96916-6d57-4a78-ad63-4e5b06236b44"

def cli = new CliBuilder(usage:'agent-diag-report.groovy [options] --dir|-d <DIR> --query|-q <QUERY>',
    header:'Uses APM Command Center API to automate download of diagnostic reports for APM Agents matching query criteria',
    footer:'\nSample queries:\n' + '--query \"serverName:ACCDemo* AND appServerName:Tomcat\"\n' +
           '--query \"osName:\\\"Windows Server 2008\\\" AND appServerName:JBoss\"\n' +
           '--query \"osName:\\\"Windows Server 2008\\\" \"\n' +
           'In the last example space before closing double quotation is required.')

cli.h(longOpt:'help', args:0, 'This help screen')
cli.s(longOpt:'server-url', args:1, argName:'URL', "The URL to APM Command Center Server. Uses ${SERVER_URL} by default.")
cli.t(longOpt:'security-token', args:1, argName:'TOKEN', 'Security token to use for authorization')
cli.q(longOpt:'query', args:1, argName:'QUERY', 'Query for the Agents to get report(s) for. Use \'*\' to get reports for all Agents (use with caution).')
cli.d(longOpt:'dir', args:1, argName:'DIR', 'Path to target directory for reports')

def options = cli.parse(args)

if (options.h) {
    cli.usage()
    System.exit(1)
}

if (!options.d) {
    println 'error: Missing required argument --dir/-d'
    cli.usage()
    System.exit(1)
}

if (!options.q) {
    println 'error: Missing required argument --query/-q'
    cli.usage()
    System.exit(1)
}

def reportsDir = options.d
if (!new File(reportsDir).exists()) {
    new File(reportsDir).mkdirs()
}

def serverUrl = options.s ? options.s : SERVER_URL
def securityToken = options.t ? options.t : SECURITY_TOKEN
def query = options.q == '*' ? [projection : 'list'] : [projection : 'list', q:options.q]

def api = new ApiClient(serverUrl, securityToken)

agents = api.getResourceList('agent', query)

if (agents == null) {
    println 'No agent(s) found matching the criteria'
    System.exit(0)
}

def diagReports = [:]

for (agent in agents) {
    def status = agent['status']
    def agentId = agent['id']
    def agentName = agent['agentName']
    def serverName = agent['serverName']
    def processName = agent['processName']
    if (status == 'ACTIVE') {
        println "Requesting diagnostic report for ${agentName} (${processName}) on host ${serverName}..."
        def report = api.post('/apm/acc/diagnosticReportTask', "{\"agent\":\"agent/${agentId}\"}")
        def reportId = report['id']
        diagReports."${reportId}" = agent
        println " -> Diagnostic report id=${reportId} initiated"
    }
}

def finishedDiagReports = [:]

println "Waiting for diagnostic report(s) to finish..."
while (true) {
    diagReports.each { reportId, agent ->
        if (finishedDiagReports."${reportId}" == null) {
            //println "Checking status of the report id=${reportId}"
            def report = api.get("/apm/acc/diagnosticReportTask/${reportId}")
            def status = report['status']
            if (status == 'COMPLETED' || status == 'FAILED') {
                finishedDiagReports."${reportId}" = report
                def agentName = agent['agentName']
                def serverName = agent['serverName']
                def processName = agent['processName']
                println " -> Report id=${reportId} for ${agentName} (${processName}) on host ${serverName} ${status}"
            }
        }
    }
    if (finishedDiagReports.size() == diagReports.size()) {
        break
    }
    sleep(3000) // Sleep for 3secs to avoid flooding Config Server with requests
}

println "Downloading reports..."
finishedDiagReports.each { reportId, report ->
    try {
        def filePath = api.download("/apm/acc/diagnosticReport/${reportId}", [format:'zip'], reportsDir)
        print " -> File ${filePath} downloaded, extracting to ${reportsDir}..."
        api.unzipReport(filePath, reportsDir)
        println 'done'
        try {
            new File(filePath).delete()
        } catch (IOException e) {
            println " -> Failed to remove report zip file" + e.getMessage()
        }
    } catch (Exception e) {
        def agentName = diagReports["${reportId}"]['agentName']
        def processName = diagReports["${reportId}"]['processName']
        def serverName = diagReports["${reportId}"]['serverName']
        printf " -> Failed to download report id=${reportId} for ${agentName} (${processName}) on host ${serverName}"
        printf e.getMessage()
    }
}

class ApiClient {

    ApiClient(String serverUrl, String securityToken) {
        this.serverUrl = serverUrl
        this.securityToken = securityToken
    }

    String serverUrl
    String securityToken

    /**
     * Generic get request to the API.
     * 
     * @param path API path.
     * @return A response from the API.
     */
    def get(String path) {
        return get(path, null)
    }

    /**
     * Generic get request to the API.
     * 
     * @param path API path.
     * @param query Request query.
     * @return A response from the API.
     */
    def get(String path, query) {
        def ret = null
        def http = new HTTPBuilder(serverUrl)
        http.ignoreSSLIssues() // Required to skip peer host validation

        http.request(Method.GET, ContentType.JSON) {
            uri.path = path
            uri.query = query
            headers.'authorization' = 'Bearer ' + securityToken
            response.success = { resp, out ->
                ret = out
            }
        }
        return ret
    }

    /**
     * Handles file download request.
     * 
     * @param path API path
     * @param query Download specific query, e.g. [q:'format=zip'].
     * @param dir Destination directory
     */
    def download(String path, query, String dir) {
        def ret = null
        def http = new HTTPBuilder(serverUrl)
        http.ignoreSSLIssues() // Required to skip peer host validation
        def headers = [authorization:'Bearer ' + securityToken]
        ret = http.get(path: path, query: query, headers: headers) { resp, inputStream ->
            def props = resp.getProperties()
            def contentDisposition = resp.getFirstHeader('content-disposition').getValue()
            def fileName = contentDisposition.split("=")[1];
            def filePath = dir + "/${fileName}"
            def fileSize = writeStreamToFile(filePath, inputStream)
            //def contentLength = resp.getFirstHeader('Content-Length').getValue().toInteger()
            // println "Wrote ${fileSize} out of ${contentLength} bytes to /tmp/reports/${fileName}" 
            return filePath
        }
        return ret
    }
    
    /**
     * Writes bytes from the given stream to the specified file.
     */
    def writeStreamToFile(String filePath, InputStream inputStream) {
        def fileSize = 0
        new File(filePath).withOutputStream {
            def buf = new byte[4096]
            def len
            while((len = inputStream.read(buf)) != -1) {
                it.write(buf, 0, len)
                fileSize += len
            }
        }
        return fileSize
    }

    /**
     * Post request to the API.
     * 
     * @param path API path
     * @param payload Body of the request
     * @return 
     */
    def post(String path, String payload) {
        def ret = null
        def http = new HTTPBuilder(serverUrl)
        http.ignoreSSLIssues() // Required to skip peer host validation

        http.request(Method.POST, ContentType.JSON) {
            uri.path = path
            body = payload
            headers.'authorization' = 'Bearer ' + securityToken
            headers.'content-type' = 'application/json'
            response.success = { resp, out ->
                ret = out
            }
        }
        return ret
    }

    /**
     * Get all resources of given name. Paging is handled, so all resources will be returned.
     *  
     * @param resource Name of the resource, e.g. 'agent'
     * @param query Map of query parameters, e.g. [projection : 'list', q:'osName:\"windows server 2008\"']
     * @return Resource list
     */
    def getResourceList(String resource, query) {
        def resources = []
        if (query == null) {
            // Use maximal page size
            query = [size:'1000']
        } else if (query['size'] == null) {
            query['size'] = '1000'
        }
        def response = get("/apm/acc/" + resource, query)
        if (response['_embedded'] != null) {
            resources = response['_embedded'][resource]
        } else {
            return null
        }
        // Handle multiple pages
        if (response['page'] != null && response['page']['totalPages'].toInteger() > 1) {
            def totalPages = response['page']['totalPages']
            for (int no = 1; no < totalPages; no++) {
                query['page'] = no.toString()
                response = get("/apm/acc/" + resource, query)
                resources.addAll(response['_embedded'][resource])
            }
        }
        return resources
    }

    /**
     * Extracts report zip file to the specified directory.
     * 
     * @param zipPath Path to the report zip file
     * @param destDirPath Destination report directory.
     */
    def unzipReport(String zipPath, String destDirPath) {
        def file = new File(zipPath)
        def dirName = file.getName().replaceAll(/.zip$/, "")
        def reportDirPath = destDirPath + "/${dirName}"
        new File(reportDirPath).mkdirs()
        def zipFile = new ZipFile(file)
        zipFile.entries().each {
            def entryName = it.getName()
            zipFile.getInputStream(it).withStream {
                def entryFilePath = reportDirPath + "/${entryName}"
                def entryFile = new File(entryFilePath)
                new File(entryFile.getParent()).mkdirs()
                writeStreamToFile(entryFilePath, it)
            }
        }
    }
}
