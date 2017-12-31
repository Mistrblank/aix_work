#!/bin/bash

#Vars
OUTFILE=svcdata.csv
##Change this to the appropriate location
OUTDIR=/home/USERNAME/data
SVCCONNECT=$1
SVCNAME=$2

DATE=`date '+%m/%d/%y'`

if [ ! -d $OUTDIR ]; then
	mkdir -p $OUTDIR
fi

if [ ! -f $OUTDIR/$OUTFILE ]; then
	touch $OUTDIR/$OUTFILE
fi

#Collect the data
ssh $SVCCONNECT svcinfo lsmdiskgrp -delim , -bytes | grep -v ^id | awk '{ print date","svcname","$0 }' date=$DATE svcname=$SVCNAME >> $OUTDIR/$OUTFILE
