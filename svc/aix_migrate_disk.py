#!/usr/bin/env python

""" aix_migrate_disk.py: This is a script that will migrate an hdisk on a host
    to another SVC storage platform.  I will be doing a lot of these in the
    near future.

    You should have ssh key access to other hosts.
"""

__author__  = "Vincent Johnson"
__status__ = "In Development"

### Imports
import subprocess as sub
import os
import sys
import argparse
import getpass
import paramiko

def verify_root():
    if getpass.getuser() != "root":
        print "Must run this command as root."
        quit()

### Functions
def openSSH(target, user):
    """
        The purpose of this function is to lump together the calls to build an
        ssh connection with Paramiko since it will be a very repetetive process.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(target, username=user)
    return ssh

def getvdiskcollection(svc):
    ##connect the source svc
    source_svc_ssh = openSSH(svc, getpass.getuser())
    ## Get a list of all of the vdisks mapped to the host
    # lshostvdiskmap
    vdiskList = source_svc_ssh.exec_command(
                "lsvdisk -nohdr -delim : -bytes")[1].readlines()
    vdiskCollection = {}
    for vdisk in vdiskList:
        ## So I want to create a dictionary of vdisk's
        valList = vdisk.strip().split(":")
        valDict = getDiskDict(vdisk)
        ## Add the list of hosts this is attached to
        valDict["hostlist"] = []
        for host in source_svc_ssh.exec_command(
                      "lsvdiskhostmap -nohdr -delim : %s" %
                      valDict["name"])[1].readlines():
            valDict["hostlist"].append(host.split(":")[4])
        #vdiskCollection.append(valDict)
        vdiskCollection[valDict["name"]] = valDict
    ## At this state I have a collection of disk information
    ## Close the connection.
    source_svc_ssh.close()
    return vdiskCollection

def getDiskDict(vdisk):
    ## Accepts a disk string from the lsvdisk command
    ## Returns a dict object of the vdisk
    keyList = ["id", "name", "IO_group_id", "IO_group_name", "status", \
               "mdisk_grp_id", "mdisk_grp_name", "capacity", "type", "FC_id",
               "FC_name", "RC_id", "RC_name", "vdisk_UID", "fc_map_count",
               "copy_count", "fast_write_state", "se_copy_count", "RC_change",
               "compressed_copy_count"]
    valList = vdisk.strip().split(":")
    valDict = {}
    for iterator in range(0, len(keyList)):
        valDict[keyList[iterator]] = valList[iterator]
    return valDict

def get_vdisk_by_host(svc, host):
    ##connect the source svc
    svc_ssh = openSSH(svc, getpass.getuser())
    ## Get a list of all of the vdisks mapped to the host
    # lshostvdiskmap
    command = "lshostvdiskmap -nohdr -delim : " + host
    vdiskList = svc_ssh.exec_command(command)[1].readlines()
    vdiskCollection = []
    for vdisk in vdiskList:
        ## So I want to create a dictionary of vdisk's
        vdiskCollection.append(vdisk.strip().split(":")[4])
        ## Close the connection.
        svc_ssh.close()
    return vdiskCollection

def mapCopyToHost(disk, host, target_svc):
    target_svc_ssh = openSSH(target_svc, getpass.getuser())
    command = "mkvdiskhostmap -host " + host + " " + disk
    print "Mapping disk %s to %s" % (disk, host)
    for line in target_svc_ssh.exec_command(command)[1].readlines():
        print line
    target_svc_ssh.close()

def createCopyVdisk(disk, target_svc):
    ##Connect to the target
    target_svc_ssh = openSSH(target_svc, getpass.getuser())
    ## I'm sort of making the assumption below to use mdiskgrp 0, this should
    ## Be cleaned up in future versions of this code.
    command = "mkvdisk -mdiskgrp " + "0" + " -iogrp " + disk["IO_group_id"] + \
                " -rsize 5% -autoexpand -unit b -size " + disk["capacity"] +  \
                " -name " + disk["name"]
    print "Creating disk: %s" % command
    for line in target_svc_ssh.exec_command(command)[1].readlines():
        print line
    target_svc_ssh.close()

def getvg(host, disk):
    """
        This is some reused code, which is why it's style doesn't match
    """
    sshCommand = "lspv | grep '^%s ' | awk '{print $3}'" % disk
    vgName = sub.Popen(["ssh", "-q", host, sshCommand],
    shell=False, stdout=sub.PIPE, stderr=sub.PIPE
    ).communicate()[0].strip()
    return vgName

def diskExistsInCollection(disk, vdiskCollection):
    ## Disk should be a dict object
    ## vdiskCollection should be a list of dicts representing vdisks
    for item in vdiskCollection:
        if disk["name"] == item["name"]:
            return True
    return False

def findDiskOnHost(disk, host):
    """
        disk will be a disk dict.
        host will be a hostname string.

        will return a tuple that contains the following:
        (hdisk, vgname)
    """
    host_ssh = openSSH(host, "root")
    hdisksList = host_ssh.exec_command("lspv | awk '{print $1, $3}'")[1].readlines()
    for hdisk in hdisksList:
        hdisk_uid = host_ssh.exec_command("lsattr -El %s | grep unique_id" % \
                                          hdisk.strip().split()[0])[1].readlines()
        if disk["vdisk_UID"] in hdisk_uid[0]:
            host_ssh.close()
            return (hdisk.strip().split()[0], hdisk.strip().split()[1])
    host_ssh.close()
    ## If we've come this far, we've failed.
    return ("fail", "fail")

def run_cfgmgr_on_host(host):
    ## Host is just a text string of the host to connect to.
    host_ssh = openSSH(host, "root")
    print "Running cfgmgr on %s..." % host
    output = host_ssh.exec_command("cfgmgr")[1].readlines()
    for line in output:
        print line.strip()
    host_ssh.close

def migrate_disk_on_host(host, source_hdisk, target_hdisk, vgname):
    host_ssh = openSSH(host, "root")
    # extend the vg to include the new volume
    print "Extending the vg..."
    command = "extendvg %s %s" % (vgname, target_hdisk)
    print command
    output = host_ssh.exec_command(command)[1].readlines()
    for line in output:
        print line.strip()
    # migrate the disk from source to target
    print "Migrating Volume..."
    command = "migratepv %s %s" % (source_hdisk, target_hdisk)
    print command
    output = host_ssh.exec_command(command)[1].readlines()
    for line in output:
        print line.strip()
    ## Code for Rootvg exception belongs here
    if vgname == "rootvg":
        # In this case we have a few other things that need to be executed.
        print "This is a rootvg, executing extra steps..."
        print "Executing bosboot against the new volume..."
        command = "bosboot -ad /dev/%s" % target_hdisk
        print command
        output = host_ssh.exec_command(command)[1].readlines()
        for line in output:
            print line.strip()

        print "This is the old boot order..."
        command = "bootlist -m normal -o"
        output = host_ssh.exec_command(command)[1].readlines()
        for line in output:
            print line.strip()

        print "Changing the boot order (you may need to change if rootvg is mirrored)..."
        command = "bootlist -m normal %s" % target_hdisk
        print command
        output = host_ssh.exec_command(command)[1].readlines()
        for line in output:
            print line.strip()

        print "This is the new boot order..."
        command = "bootlist -m normal -o"
        output = host_ssh.exec_command(command)[1].readlines()
        for line in output:
            print line.strip()

    # reduce the vg
    print "Reduce the old Volume from the VG..."
    command = "reducevg %s %s" % (vgname, source_hdisk)
    print command
    output = host_ssh.exec_command(command)[1].readlines()
    for line in output:
        print line.strip()
    host_ssh.close()
    ##End migrate_disk_on_host

def remove_disk_on_host(host, hdisk):
    host_ssh = openSSH(host, "root")
    print "Removing %s on %s..." % (hdisk, host)
    output = host_ssh.exec_command("rmdev -dRl %s" % hdisk)[1].readlines()
    for line in output:
        print line
    ##End remove_disk_on_host

def remove_vdisk_from_svc(svc, vdisk):
    """
        source_svc is a string
        vdisk is a dictionary for a vdisk
    """
    svc_ssh = openSSH(svc, getpass.getuser())
    ## First we need to unmap from the host
    print "Removing the mapping between %s on %s..." % (vdisk["name"],
                                                        vdisk["hostlist"][0])
    command = "rmvdiskhostmap -host %s %s" % (vdisk["hostlist"][0],
                                              vdisk["name"])
    print command
    output = svc_ssh.exec_command(command)[1].readlines()
    for line in output:
        print line.strip()
    ## Remove the volume
    print "Removing the vdisk %s..." % vdisk["name"]
    command = "rmvdisk %s" % vdisk["name"]
    print command
    output = svc_ssh.exec_command(command)[1].readlines()
    for line in output:
        print line.strip()
    svc_ssh.close()
    ## End remove_vdisk_from_svc

def test_main():
    """
        The sole purpose of this function is to place any test code.
        This function should only replace the main() function and not be
        executed anywhere else.  Yes, I'm aware that I need to up my ability
        to write test code.

        Because this is just test code, the code itself is irrelevant, it just
        needs to pass the parser.
    """

    ## Put any test code here
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_svc", required=True)
    parser.add_argument("--target_svc", required=True)
    parser.add_argument("--host", required=True)
    args=vars(parser.parse_args())

    ## For this test I need the disk collections
    sourceVdiskCollection = getvdiskcollection(args["source_svc"])
    #targetVdiskCollection = getvdiskcollection(args["target_svc"])
    remove_vdisk_from_svc(args["source_svc"], sourceVdiskCollection["web01_d01"])
    remove_vdisk_from_svc(args["source_svc"], sourceVdiskCollection["web01_r01"])

### Main
def main():
    ### All of the primary execution occurs here.

    ## List of things I need to know
    # The source svc
    # The new svc (target_svc)
    # The host I want to focus on

    ## Read the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_svc", required=True)
    parser.add_argument("--target_svc", required=True)
    parser.add_argument("--host", required=True)
    args=vars(parser.parse_args())

    sourceVdiskCollection = getvdiskcollection(args["source_svc"])
    targetVdiskCollection = getvdiskcollection(args["target_svc"])

    for vdisk in get_vdisk_by_host(args["source_svc"], args["host"]):
        ## Does a copy exist on the target?
        if vdisk in targetVdiskCollection.keys():
            print "skipping %s, copy exists on target" % vdisk
        else:
            if len(sourceVdiskCollection[vdisk]["hostlist"]) > 1:
                print "skipping %s, this volume belongs to more than one host" \
                        % vdisk
                continue
            else:
                ## Copy the disk
                createCopyVdisk(sourceVdiskCollection[vdisk], args["target_svc"])
                ## Map the disk
                mapCopyToHost(vdisk, args["host"], args["target_svc"])

                ## Recollect the targetVdiskCollection (probably a better way)
                targetVdiskCollection = getvdiskcollection(args["target_svc"])
                print "This is the information for the disk created: %s" % \
                            targetVdiskCollection[vdisk]

                ## run cfgmgr on the host
                run_cfgmgr_on_host(args["host"])
                ## identify source disk on host
                (source_hdisk, vgname) = findDiskOnHost(sourceVdiskCollection[vdisk], args["host"])
                ## identify target disk on host (as a dict)
                (target_hdisk, none) = findDiskOnHost(targetVdiskCollection[vdisk], args["host"])
                ## Execute a migration on the client
                print "Source hdisk: %s Target hdisk: %s VGName: %s" % (source_hdisk, target_hdisk, vgname)
                migrate_disk_on_host(args["host"], source_hdisk, target_hdisk, vgname)
                # Remove the disk from the host
                remove_disk_on_host(args["host"], source_hdisk)
                # Remove the volume from the old svc
                remove_vdisk_from_svc(args["source_svc"], sourceVdiskCollection[vdisk])

main()
quit()
