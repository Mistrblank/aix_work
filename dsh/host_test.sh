#!/bin/sh

## This host should run from your bastion host.  It can run from any user id
# that is intended to work with dsh.  The purpose is to identify hosts in your
# machines.list files that are not responsive.  The resulting diff will identify
# which hosts are inaccessible. 

LC_ALL=C
LC_COLLATE=C

dsh -ac date | awk '{print $1}' | sed 's/://' | sort | uniq > /tmp/host_test.tmp
sort $HOME/.dsh/machines.list > /tmp/machines.list
diff -c /tmp/machines.list /tmp/host_test.tmp

rm /tmp/host_test.tmp
rm /tmp/machines.list
