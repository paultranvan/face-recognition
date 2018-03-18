#!/bin/bash

DEFAULT_HOST="cozy1.local:8080"

if [ $# -lt 1 ]; then
    echo "Usage : $0 host doctypes"
    exit 1
fi
HOST=$1

COZY_CLIENT_ID=$(cozy-stack instances client-oauth $HOST http://localhost test github.com/cozy/test)

COZY_STACK_TOKEN=$(cozy-stack instances token-oauth $HOST $COZY_CLIENT_ID ${@:2})

echo $COZY_STACK_TOKEN
