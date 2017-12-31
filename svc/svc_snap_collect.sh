#!/bin/bash

##This bash script was used to grab snap information, the execution was scheduled
# via a cron job.
## the SVC to be connected to should be the first argument during execution
# This was vital to capturing full data for IBM Support.

OUTDIR=/home/vjohnson/Downloads/svc_snap
SVCNAME=$1
if [ ! -d $OUTDIR ]; then
        mkdir -p $OUTDIR
fi
#Collect the data
echo "Prepare and create snap..."
ssh $SVCNAME "svc_livedump -nodes all -yes; svc_snap gui3"
echo "Copy snap to local folder..."
scp $SVCNAME:/dumps/snap* $OUTDIR
echo "Clear the snaps directory..."
ssh $SVCNAME "svc_snap clean"
