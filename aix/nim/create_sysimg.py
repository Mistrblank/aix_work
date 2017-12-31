#!/usr/bin/env python

""" create_sysimg.py: This script creates the system image from the image host
    and distributes the image to all other nim servers.  Once distributed
    the script creates the spot image to accompany.

    Format for the system image name should be preserved:
    mksysb_sysimg_aix7100-01-06-1241_20130531

    Note this

    Script should be executed by root and should have root keys to all nim
    servers and to the system image host
"""

__author__  = "Vincent Johnson"
__status__ = "In Development"

# Import section
import subprocess as sub, os
import sys

# Variables and constants section
nimHosts = ["nim-host1", "nim-host2", "nim-host3", "nim-host4"]  # First host is base
sysImgHost = "aix71image"  # Should match hostname and nim object name

# Location where the file will be stored temporarily to disseminate to all nims
downloadLocation = "/tmp"

# Grab the Date
date = sub.Popen(["date", "+%Y%m%d"], stdout=sub.PIPE).communicate()[0].strip()

# Grab the OS Level from the host
osLevel = sub.Popen(["ssh", "-q", "root@" + sysImgHost, "oslevel", "-s"],
                    stdout=sub.PIPE).communicate()[0].strip()

nimObjectName = "mksysb_aix" + osLevel + "_" + date
# The filename of the mksysb file
nimMksysbFile = "aix" + osLevel + "_" + date + ".mksysb"
# The hardcoded path to the mksysb nim location
nimMksysbPath = "/nim/mksysb/"
nimSpotPath = "/nim/spot/"

# Begin Processing

# Check the available space first (anything below 5GB user should be notified).
print "Checking for available space on all nim hosts."
for i in nimHosts:
    command = "df -g /nim | grep -v Filesystem | awk '{print $3}'"
    ssh = sub.Popen(["ssh", "-q", "root@" + i, command],
                    shell=False,
                    stdout=sub.PIPE,
                    stderr=sub.PIPE)
    result = float(ssh.stdout.readlines()[0].strip())
    if (result < 5.0):
        input = raw_input("/nim filesystem on host " + i + " has " + str(result) + \
        "GB free, which is less than 5GB, are you sure you want to continue (\"y\" or \"yes\" to continue)? ").lower()
        if input == "y" or input == "yes":
            print "Continuing..."
        else:
            print "Canceling..."
            quit()

# Create the system image on the base nim host
command = "ssh -q root@" + nimHosts[0] + \
          " nim -o define -t mksysb -a server=master -a source=" + sysImgHost + \
          " -a mk_image=yes -a mksysb_flags=Xe -a location=" + \
          nimMksysbPath + nimMksysbFile + " " + nimObjectName
print "Creating the system image on " + nimHosts[0]
print command
retvalue = os.system(command)

if (retvalue != 0):
    print "Failure to create mksysb image.  Exiting."
    sys.exit(1)

# Copy the mksysb file to local filesystem download location
command = "scp -q root@" + nimHosts[0] + ":" + nimMksysbPath + nimMksysbFile + \
          " " + downloadLocation
print "Downloading the mksysb file from " + nimHosts[0]
print command
retvalue = os.system(command)

if (retvalue != 0):
    print "Failure to obtain mksysb file. Exiting."
    sys.exit(1)

# Create the spot on the primary nim server
command = "ssh -q root@" + nimHosts[0] + \
		  " nim -o define -t spot -a server=master -a source=" + \
		  nimObjectName + " -a location=" + nimSpotPath + " spot_" + \
		  nimObjectName
print "Creating the SPOT from mksysb object."
print command
retvalue = os.system(command)
if (retvalue != 0):
	print "Failure to create NIM SPOT object. Exiting."
	sys.exit(1)

# Copy the mksysb file to other nim servers and generate the nim objects
for i in range(1, len(nimHosts)):
    # Copy
    command = "scp -q " + downloadLocation + nimMksysbFile + " root@" + \
              nimHosts[i] + ":" + nimMksysbPath
    print "Copying mksysb file to " + nimHosts[i]
    print command
    retvalue = os.system(command)
    if (retvalue != 0):
        print "Failure to secure copy mksysb file. Exiting."
        sys.exit(1)

    # Create mksysb object
    command = "ssh -q root@" + nimHosts[i] + \
              " nim -o define -t mksysb -a server=master -a location=" + \
              nimMksysbPath + nimMksysbFile + " " + nimObjectName
    print "Creating the mksysb object in NIM"
    print command
    retvalue = os.system(command)
    if (retvalue != 0):
        print "Failure to create NIM object. Exiting."
        sys.exit(1)

    # Create the spot
    command = "ssh -q root@" + nimHosts[i] + \
              " nim -o define -t spot -a server=master -a source=" + \
              nimObjectName + " -a location=" + nimSpotPath + " spot_" + \
              nimObjectName
    print "Creating the SPOT from mksysb object."
    print command
    retvalue = os.system(command)
    if (retvalue != 0):
        print "Failure to create NIM SPOT object. Exiting."
        sys.exit(1)


# Cleanup
command = "rm " + downloadLocation + nimMksysbFile
print "Removing local temporary copy"
print command
retvale = os.system(command)
