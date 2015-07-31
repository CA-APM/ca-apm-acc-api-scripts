#!/bin/bash
#
# This script is used to copy a single file to a group of agents.
# Usage:
#   -s <server>  
#      Command Center Server to use. Default is https://localhost:8088/
#   -f <file>
#      File to upload and send to agents.  Default is ./new.pbd
#   -t <token>
#      Security token to use. 
#   -d <destination>
#      File name and directory to use on the remote agents. 
#      Default is my-new.pbd
#   -q <query>
#      Query to use to search for agents. Default is *all* agents.
#



function usage() {
cat <<EOF
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
EOF
}

##############################################
#
# extract an int from json output
#
##############################################
getJsonIntValues() {
    local values=$(echo "$1" |  tr ',' '\n' | grep "\"$2\"[\t ]*:[\t ]*[0-9]*" | \
                   cut -f 2 -d':'| cut -f 1 -d',' | \
                   sed -e 's/^[/t ]*//g' -e 's/[/t ]*$//g')
    echo "$values"
}

##############################################
#
# extract a string from json output
#
##############################################
getJsonStringValues() {
    local values=$(echo "$1" |  tr ',' '\n' | grep "\"$2\"[\t ]*:[\t ]*\".*\"" | \
                   cut -f 2 -d':'| cut -f 1 -d',' | \
                   sed -e 's/^[/t ]*\"//g' -e 's/\"[/t ]*$//g')
    echo "$values"
}

##############################################
#
# Look for error in output
#
##############################################
function checkForError() {
    if [ -z "$1" ] 
    then
        echo No output from command >&2
        exit 1
    fi
    ERR=$(getJsonStringValues "$1" "errorMessage")
    if [ ! -z "$ERR" ]
    then
        echo $ERR >&2
        exit 1
    fi
    ERR=$(getJsonStringValues "$1" "error_description")
    if [ ! -z "$ERR" ]
    then
        echo $ERR >&2
        exit 1
    fi
}

##############################################
#
# Upload a file and return it's ID
#
##############################################
function upload() {

    #
    # Upload the file
    #
    RET=$(curl -k -s -H "Accept-Encoding: application/json" -H "$AUTHZ" -F name=$FILE -F file=@$1 $SERVER/file )

    checkForError "$RET" 


    #
    # Extract the 'ID' of the file.
    #
    ID=$(getJsonIntValues "$RET" "id")

    #
    # Strip spaces
    #
    ID=$(echo $ID)

    echo $ID
}


##############################################
#
# Get a list of agents.
# Return the agent IDs, echo agent details to stderr.
#
##############################################
function getAgents() {

    #
    # Now get list of agents to send to.
    #
    RET=$(curl -k -s -H "$AUTHZ" \
         "$SERVER/agent?projection=list&size=1000$QUERY")

    checkForError "$RET"

    #
    # Look for lines of the form
    #     "id" : 1,
    #
    IDS=($(getJsonIntValues "$RET" "id"))

    #
    # Look for lines serverName, processName, agentName.
    #
    agentName=($(getJsonStringValues "$RET" "agentName"))
    processName=($(getJsonStringValues "$RET" "processName"))
    serverName=($(getJsonStringValues "$RET" "serverName"))

    #
    # Print out the matching agents
    #
    echo "ID:    Server name:    Process name:   Agent name: " >&2
    echo "----------------------------------------------------" >&2
    for ((i=0;i<${#IDS[@]};++i))
    do
        printf "%-6s %-15s %-15s %-15s\n" "${IDS[i]}" "${serverName[i]}" "${processName[i]}" "${agentName[i]}" >&2
    done

    echo "${IDS[*]}"
    return
}

##############################################
#
# Start a task to push a file to an agent
#
##############################################
function pushFile() {

    FILE=$1
    shift
    AGENTS="$*"
    TASKS=""

    for i in $AGENTS
    do

        OUT=$(curl -k -s -H "$AUTHZ" -H "Content-Type: application/json" \
                   "$SERVER/agentFileOperationTask" \
                   -X POST -d \
                   '{"agent":"agent/'$i'", "file":"file/'$FILE'", "destination":"'$DESTINATION'", "operation":"COPY"}')

        checkForError "$OUT" || exit

        #
        # Extract ID of task we created. Add this to our list
        #
        ID=($(getJsonIntValues "$OUT" "id"))
        TASKS="$TASKS $ID"
    done

    echo $TASKS
}

##############################################
#
# Follow the progress of the tasks.
#
##############################################
function progressTasks() {
    TASKS=($*)
    COUNT=${#TASKS[@]}

    #
    # Loop until all tasks are complete or failed
    #
    while true
    do
        DONE=0

		NEW=
		QUEUED=
		STARTED=
		COMPLETED=
		FAILED=


        for i in ${TASKS[*]}
        do
            OUTPUT=$(curl -k -s -H "$AUTHZ" "$SERVER/agentFileOperationTask/$i")

            checkForError "$OUTPUT"
            STATE=($(getJsonStringValues "$OUTPUT" "status"))

            if [ "$STATE" = "COMPLETED"  -o "$STATE" = "FAILED" ]
            then
                let DONE=DONE+1
            fi
            eval let $STATE=$STATE+1
        done

        #
        # Log progress thru the various task states
        #
        echo "--------------"
        echo "New       = ${NEW:--}"
        echo "Queued    = ${QUEUED:--}"
        echo "Started   = ${STARTED:--}"
        echo "Completed = ${COMPLETED:--}"
        echo "Failed    = ${FAILED:--}"

        if [ $DONE -eq $COUNT ]
        then
            return
        fi
        
    done
}

##############################################
#
# The main script
#
##############################################

#
# Setup default values
#
SERVER=https://localhost:8088/apm/acc
FILE=new.pbd
TOKEN=e6a24777-e2cd-4076-92c4-6f98674ae2f2
DESTINATION=my-new.pbd
QUERY=""

IFS=$'\n' # Make sure array elements are created from strings separated by new line rather than space

#
# Check command line options
# 
while getopts "?s:f:t:d:q:" opt; do
    case $opt in
        s) SERVER=${OPTARG}/apm/acc;;
        f) FILE=$OPTARG;;
        t) TOKEN=$OPTARG;;
        d) DESTINATION=$OPTARG;;
        q) QUERY="&q=$OPTARG";;
        ?) usage; exit;;
        esac
done

# Set bearer token
AUTHZ="Authorization: Bearer $TOKEN"

# Check file exists
if [[ ! -f $FILE ]] ; then
    echo $FILE does not exist
    exit
fi

# Normalize url (remove //)
SERVER=$(echo "$SERVER" | sed 's!//apm!/apm!g')

##########################################
# Get agents to copy file to
##########################################

echo
echo Fetching agents ...

AGENTS=$(getAgents) || exit

if [ -z "$AGENTS" ] 
then
    echo "No agents were found"
    exit
fi

##########################################
# Upload the file to ACC
##########################################

echo
echo Uploading file
ID=$(upload $FILE) || exit

echo
echo File $FILE uploaded. Id is $ID


##########################################
# Start tasks to update those agents
##########################################

echo
echo Starting copy tasks ...
TASKS=$(pushFile $ID "$AGENTS") || exit


##########################################
# Watch the progress of those tasks
##########################################

progressTasks $TASKS

#
# Done
#
