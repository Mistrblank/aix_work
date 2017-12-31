#!/bin/sh

RSYNC=/usr/bin/rsync
SSH=/usr/bin/ssh
RUSER=root
RHOST={{HOST}}
RPATH=/jira
LPATH=/home/{{USERNAME}}/jirabackup/
OTHEROPTS=$*

date
$RSYNC -az $OTHEROPTS -e "$SSH" $RUSER@$RHOST:$RPATH $LPATH
date
echo "-----------------------------------------------------"
