#!/usr/bin/env python

"""
  The purpose of this script is to take a list of zone objects on a SAN switch
  fabric and remove them from the configuration completely using the
  expungeZoneObject fabricOS command.  The problem is that this command itself
  requires interaction.  Because of buffer issues with the ssh command and
  on the switch itself, I've had a hard time deleting large numbers of objects
  so I've encapsulated the process to remove one object in a function and then
  creating a function to iterate over a list (in a file on the local filesystem)
  of objects to remove.
"""

# Import section
import paramiko
import argparse

def expungeZoneObject(sshConnection, zoneObject):
    ## This function only expunges objects.  I could realistically tweak
    # it so that it will work to create objects one at a time.

    # Run the command to eliminate an object completely
    command = "echo \"y\" | zoneObjectExpunge %s; echo \"y\" | cfgSave; " \
              % zoneObject + "echo \"y\" | cfgEnable Normal"
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
    objectsToExpunge = open(objectFile).read().splitlines()

    print "Switch to connect to:"
    print sanSwitch
    print "Purgable objects:"
    print objectsToExpunge

    ## Create the paramiko client instance
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ## Replace user and password here
    ssh.connect(sanSwitch, username='USER', password='PASSWORD')

    for zoneObject in objectsToExpunge:
        expungeZoneObject(ssh, zoneObject)

Main()
