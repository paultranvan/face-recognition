#!/bin/bash

# This script executes all the sharing steps, on the sharer and recipient side

#SHARER="http://cozy1.local:8080"
#RECIPIENT="cozy2.local:8080"

#SHARER_HOST="cozy1.local:8080"

#SHARING_TYPE='master-slave'
#SHARING_TYPE='one-shot'
SHARING_TYPE='one-shot'

# check the parameters
echo "$#"
if [ $# -lt 3 ] ; then
    echo "Usage : $0 docid is_file sharer_instance recipient_instance"
    exit 1
fi

DOC_ID=$1
IS_FILE=$2
SHARER_HOST=$3
RECIPIENT=$4

SHARER="http://$SHARER_HOST" 

######### Step 1: create recipient: insert and register
RECIPIENT_JSON='
{
    "email": "b@ob.fr",
    "url": "http://'$RECIPIENT'"
}
'
res=$(curl -X POST -H 'Accept: application/json' -H 'Content-Type: application/json' $SHARER/sharings/recipient -d "$RECIPIENT_JSON" | jq '{id: .data.id, client_id: .data.attributes.Client.client_id'})


# The --raw-output allows to avoid the "" in the results
RECIPIENT_ID=$(echo "$res" | jq --raw-output '.id')
#CLIENT_ID=$(echo "$res" | jq --raw-output '.client_id')


######### Step 2: create sharing: insert and send mail

if [ -z "$IS_FILE" ]; then
    TYPE="io.cozy.tests"
    VALUES='["'$DOC_ID'"]'
else
    TYPE="io.cozy.files"
    VALUES='["'$DOC_ID'"]'
fi

# Generate token for authorization on this doctype
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOKEN=$($DIR/generate_token.sh $SHARER_HOST $TYPE)

echo "values : $VALUES"
echo "type : $TYPE"

SHARING_JSON='
{
    "permissions": {
        "tests": {
            "description": "test desc",
            "type": "'$TYPE'",
            "values": '$VALUES',
            "verbs": ["ALL"]
        }
    },
    "recipients": [
        {
            "recipient": {
                "type": "io.cozy.contacts",
                "id": "'$RECIPIENT_ID'"
            }
        }
    ],
    "desc": "I want you to go elsewhere!",
    "sharing_type": "'$SHARING_TYPE'"
}
'

echo $SHARING_JSON|jq '.'

# Create the sharing
sharing_res=$(curl -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" $SHARER/sharings/ -d "$SHARING_JSON")

SHARING_ID=$(echo "$sharing_res" |jq --raw-output '.data.attributes.sharing_id')
CLIENT_ID=$(echo "$sharing_res" |jq --raw-output '.data.attributes.recipients[0].Client.client_id')

echo "Client ID : $CLIENT_ID"

######### Step 3: generate sharing url
if [ -z "$IS_FILE" ]; then
    scope="$TYPE:ALL:$DOC_ID"
else
    scope="$TYPE:ALL:$DOC_ID"
fi
redirect_uri="$SHARER/sharings/answer"

SHARING_LINK="http://$RECIPIENT/sharings/request?state=$SHARING_ID&scope=$scope&response_type=code&redirect_uri=$redirect_uri&client_id=$CLIENT_ID&sharing_type=$SHARING_TYPE"


######### Step 4: accept sharing on the recipient side
COOKIE_FILE=headers
CSRF_FILE=csrf

# Activate the sharing link
echo "SHARING LINK : $SHARING_LINK"
curl $SHARING_LINK

# Login to cozy's recipient and save headers to use cookies
curl -X POST -F 'passphrase=cozy' -D "$COOKIE_FILE" "$RECIPIENT/auth/login"
cookie=$(cat "$COOKIE_FILE" |grep "Set-Cookie" | cut -d: -f2 | cut -d$' ' -f2)

# Request the authorize form to get crsf token
curl -c "$CSRF_FILE" -b "$COOKIE_FILE" "$RECIPIENT/auth/authorize?state=$SHARING_ID&scope=$scope&response_type=code&redirect_uri=$redirect_uri&client_id=$CLIENT_ID"

# Build crsf token and cookie
csrf=$(cat "$CSRF_FILE" |grep csrf | rev | cut -d$'\t' -f1 | rev)
auth_cookie="_csrf=$csrf; $cookie"

# Post authorize with cookie and redirect (-L) option
curl -Lv -H "Cookie: $auth_cookie" "$RECIPIENT/auth/authorize" -d "csrf_token=$csrf&state=$SHARING_ID&scope=$scope&response_type=code&redirect_uri=$redirect_uri&client_id=$CLIENT_ID"
