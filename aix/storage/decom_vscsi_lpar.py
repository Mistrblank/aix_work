#!/usr/bin/env python

""" decom_vscsi_lpar.py: This is a script to go through the process of
    decommisioning an lpar on a system that uses vscsi.  This script has a short
    shelf life because we will only use vscsi in a limited capacity and we're
    getting rid of those hosts.

    Script requires that the current user have ssh keys to the HMC and SVC

    Another assumption is that the svc host names for the vio servers will
    match with the lpar names for these.

    The script will not perform system alterations itself, it's sole purpose is
    to create the commands to modify the host.
"""

__author__  = "Vincent Johnson"
__status__ = "In Development"

# Import section
import subprocess as sub, os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--LPAR", required=True)
parser.add_argument("--HMC", required=True)
parser.add_argument("--CEC", required=True)
parser.add_argument("--SVC", required=True)
args=vars(parser.parse_args())

print "Using CLI Args: %s" % args

LPAR=args["LPAR"]
HMC=args["HMC"]
CEC=args["CEC"]
SVC=args["SVC"]

##Create a global list of commands to run.  this will be output at the end
commandQueue = []

# what slots does it exist on at the VIO.  The slots should be the same from VIO
# to VIO.
sshCommand = "lshwres -m %s -r virtualio --rsubtype scsi --level lpar --filter \"lpar_names=%s\"" \
             % (CEC, LPAR)
print "(%s)" % sshCommand
output = sub.Popen(["ssh", "-q", HMC, sshCommand],
                   shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                   ).communicate()[0].strip().split("\n")
print output
## The next line is my new favorite line in Python
outputArray=[dict(item.split("=") for item in line.split(",")) for line in output]
print outputArray
## I should probably put some syntax here to make sure that the lpar exists

## Ensure that the host is down
sshCommand = "lssyscfg -m %s -r lpar -F state --filter \"lpar_names=%s\"" \
             % (CEC, LPAR)
if "Not Activated\n" != (sub.Popen(["ssh", "-q", HMC, sshCommand],
                                   shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                                   ).communicate()[0]):
    ## Add code here for shutdown
    print "LPAR Not in \"Not Activated\" state, please shutdown %s before continuing" % LPAR
    quit()

## Create a global list to capture the Serials
diskSerialList=[]

## Here I should obtain the vhosts.
for adapterLine in outputArray:
    print "Identifying vadapter on vio id:%s" % adapterLine["remote_lpar_id"]
    sshCommand = "viosvrcmd -m %s --id %s -c \"lsdev -vpd\"" % (CEC, adapterLine["remote_lpar_id"]) \
                 + " | grep C%s | grep vhost" % (adapterLine["remote_slot_num"])
    print "(%s)" % sshCommand
    vadapter = sub.Popen(["ssh", "-q", HMC, sshCommand],
                       shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                       ).communicate()[0]
    if vadapter == "":
        print "No vhost adapter found on VIOS id: %s" % adapterLine["remote_lpar_id"]
    else:
        ## An adapter was found, split the line and grab the vhost id
        vadapter = vadapter.split()[0]

        ## Generate scripting to remove the mappings and the adapters:
        sshCommand = "echo \"viosvrcmd -m %s --id %s -c \\\"rmdev -dev %s -recursive\\\"\" | ssh -q %s" \
                     % (CEC, adapterLine["remote_lpar_id"], vadapter, HMC)
        commandQueue.append("# Remove the adapters with following commands:")
        commandQueue.append(sshCommand)

        ## Generate scripts to dynamically remove the adapter from the vio server.
        sshCommand = "ssh -q %s chhwres -r virtualio -m %s -o r --id %s -s %s" \
                     % (HMC, CEC, adapterLine["remote_lpar_id"], adapterLine["remote_slot_num"])
        commandQueue.append("# Dynamically Remove the adapter from the active lpar with the following command:")
        commandQueue.append(sshCommand)

        ## With the vhost known now, lets identify disks
        print "Obtaining Disk List for %s on VIOS id: %s" % (vadapter, adapterLine["remote_lpar_id"])
        sshCommand = "viosvrcmd -m %s --id %s -c \"lsmap -vadapter %s\" " % (CEC, adapterLine["remote_lpar_id"], vadapter) \
                    + "| grep Backing"
        print "(%s)" % sshCommand
        if sub.Popen(["ssh", "-q", HMC, sshCommand],
                     shell=False, stdout=sub.PIPE).communicate()[0] == "":
            print "No disks found on %s on VIOS id: %s" % (vadapter, adapterLine["remote_lpar_id"])
        else:
            diskList = [disk.split()[2] for disk in sub.Popen(["ssh", "-q", HMC, sshCommand],
                                        shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                                        ).communicate()[0].strip().split("\n")]
            print "The disk list for %s on vio id: %s : %s" % (vadapter, adapterLine["remote_lpar_id"], diskList)

            print "Capturing the serial numbers for disks..."
            ## Capture Serials and remove the disks
            for disk in diskList:
                sshCommand = "viosvrcmd -m %s --id %s -c \"lsdev -dev %s -vpd\" | grep Serial" \
                             % (CEC, adapterLine["remote_lpar_id"], disk)
                #print "(%s)" % sshCommand
                diskSerial = sub.Popen(["ssh", "-q", HMC, sshCommand],
                                       shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                                       ).communicate()[0].strip().split(".")[15]
                print "Found Disk %s :%s:" % (disk, diskSerial)
                diskSerialList.append(diskSerial)

                sshCommand = "echo \"viosvrcmd -m %s --id %s -c \\\"rmdev -dev %s\\\"\" | ssh -q %s" \
                             % (CEC, adapterLine["remote_lpar_id"], disk, HMC)
                commandQueue.append("# Remove the hdisk %s with command:" % (disk))
                commandQueue.append(sshCommand)

## Generate the code to remove the lpar
sshCommand = "ssh -q %s rmsyscfg -m %s -r lpar -n %s" % (HMC, CEC, LPAR)
commandQueue.append("# Remove the lpar with the following command:")
commandQueue.append(sshCommand)

## Generate the code to remove the disks:
commandQueue.append("# Remove the disk from the SVC:")
for uid in list(set(diskSerialList)):
    sshCommand = "lsvdisk -filtervalue vdisk_UID=%s -nohdr -delim :" % uid
    print "(%s)" % sshCommand
    vdisk = sub.Popen(["ssh", "-q", SVC, sshCommand],
                      shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                      ).communicate()[0].split(":")
    print "Disk Found name:%s id:%s UID:%s" % (vdisk[1], vdisk[0], vdisk[13])

    sshCommand = "lsvdiskhostmap -nohdr -delim : %s" % vdisk[1]
    print "(%s)" % sshCommand
    vdiskHosts = sub.Popen(["ssh", "-q", SVC, sshCommand],
                           shell=False, stdout=sub.PIPE, stderr=sub.PIPE
                           ).communicate()[0].strip().split("\n")
    for mappedDisk in vdiskHosts:
        print "vDisk Host Mapping Found: name: %s id:%s host:%s" \
              % (vdisk[1], vdisk[0], mappedDisk.split(":")[4])
        commandQueue.append("ssh -q %s rmvdiskhostmap -host %s %s" \
                            % (SVC, mappedDisk.split(":")[4], vdisk[1]))
    commandQueue.append("ssh -q %s rmvdisk %s" % (SVC, vdisk[1]))

## Print a separator
print "------------------------------"
for command in commandQueue:
    print command

## Exit
quit()
