#!/usr/bin/env python

"""
This script is a modification of the massZoneObjectExpunge script that instead
of just accepting objects for deletion, just accepts a list of commands and then
processes them with a cfgSave and cfgEnable.
"""

# Import section
import paramiko
import argparse

def processZoneCommand(sshConnection, zoneCommand):
    ## This function only expunges objects.  I could realistically tweak
    # it so that it will work to create objects one at a time.

    # Run the command to eliminate an object completely
    command = "%s && echo \"y\" | cfgSave && " \
              % zoneCommand + "echo \"y\" | cfgEnable Normal"
    print "Executing \"%s\"" % command
    stdin, stdout, stderr = sshConnection.exec_command(command)
    print stdout.readlines()
    print stderr.readlines()

def Main():
    ## Read the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--SWITCH", required=True)  ## This is the SAN Switch
    parser.add_argument("--OBJECTFILE", required=True)
    args=vars(parser.parse_args())
    sanSwitch=args["SWITCH"]
    objectFile=args["OBJECTFILE"]

    ## Read in the objects
    zoneCommands = open(objectFile).read().splitlines()

    print "Switch to connect to:"
    print sanSwitch
    print "Command Queue:"
    print zoneCommands

    ## Create the paramiko client instance
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ## The User and password need to be hardcoded, should fix in future.
    ssh.connect(sanSwitch, username='{{USERNAME}}', password='{{PASSWORD}}')

    for zoneCommand in zoneCommands:
        processZoneCommand(ssh, zoneCommand)

Main()
