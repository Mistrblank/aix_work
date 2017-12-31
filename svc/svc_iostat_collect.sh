#!/bin/bash

## This script connects to the SVC provided as the first argument on the command
# line and collects all performance data.  The intent was to collect this data
# and funnel it through a filebeat->logstash->elasticsearch pipeline.
# From there the data could be visualized in Kibana or Grafana

OUTDIR=/home/vjohnson/Downloads/svc_stats
SVCNAME=$1
DATE=`date '+%m/%d/%y'`
if [ ! -d $OUTDIR ]; then
        mkdir -p $OUTDIR
fi
#Collect the data
echo "Moving files to control node..."
ssh $SVCNAME "svcinfo lsnode -nohdr -filtervalue config_node=no|while read -a node;do svctask cpdumps -prefix /dumps/iostats \${node[0]}; sleep 5; done"
sleep 15
echo "Copy iostat files to $OUTDIR..."
scp $SVCNAME:/dumps/iostats/* $OUTDIR
