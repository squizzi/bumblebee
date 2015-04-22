#!/usr/bin/env python  
import sys
import paramiko
import os
import uuid
import re
from scp import SCPClient

# ENVIRONMENT VARIABLES
# containerhost is the machine which hosts your containers, if you are running on localhost, specify that instead
containerhost = "hp-dl380pg8-6.gsslab.rdu2.redhat.com"
# corevol is a temporary space located on the container host for cores and does not need to be large as 
# core files are cleaned up following container creation 
corevol = "/cores"

# INPUT REQUESTS 
# FIXME: Change these inputs to command line flags and add a --help dialog
def getosversion():
	osversion = raw_input('Enter the full RHEL version the core file was created on in X.Y format (5, 6 and 7 supported): ')
	valid = "^[5-7]\.([0-9]$|1[0-1]$)"
	while not re.match (valid, osversion):
		osversion = raw_input('The RHEL version entered is invalid, try again: ')
	return osversion

osversion = getosversion()
pkgversion = raw_input('Enter the full package name-version.arch (ex. autofs-5.0.5-109.el6_6.1.x86_64): ')
corelocation = raw_input('Enter the full path to the core file: ')
print '\n'

# VERIFICATION
print "Creating an environment with the following details: "
print "* RHEL version: %s" %osversion
print "* Package version: %s" %pkgversion
print "* Core file: %s" %corelocation
print '\n'

yn = raw_input("Is this correct? Enter (y)es or (n)o: ") 
if yn == "yes" or yn == "y":
	print "Continuing..." 
elif yn == "no" or yn == "n": 
	print "Environment build cancelled. Exiting." 
  	sys.exit(1)

# Verify the corefile exists and is readable 
if os.path.isfile(corelocation) and os.access(corelocation, os.R_OK):
	print '\n'
else:
	print "The core file is either missing or is not readable.  Exiting."
	sys.exit(1)

# Create container environment on server
# Setup ssh/scp
# Right now we just specify username/password for testing purposes however this will use a more secure
# method in the future
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(containerhost, username="root",password="redhat", look_for_keys=False)

print "Initializing docker container..."

# Build the docker file locally from the dockerfile skeleton and copy it to the container host.
# The new docker file will be named after a randomly generated uuid, the same uuid will be used
# to tag the container on the host
u = uuid.uuid4()
newfile = u.hex
corefile = os.path.basename(corelocation)
infile = open('dockerfile')
outfile = open(newfile, 'w')
replacements = {'$osversion':osversion, '$pkgversion':pkgversion, '$corefile':corefile}

#if re.match('^[6-7].[0-11]$',osversion):
#	osversion = str(osversion)		
#    replacements = {'$osversion':osversion, '$pkgversion':pkgversion, '$corefile':corefile}
#else:
	# We have to specify the RHEL5 private registry here since there's no default rhel5 image to pull from the standard registry
#	osversion = str(osversion)		
#	replacements = {'rhel$osversion':'cc7eb88725a2', '$pkgversion':pkgversion, '$corefile':corefile}

for line in infile:
	for src, target in replacements.iteritems():
		line = line.replace(src, target)
	outfile.write(line)
infile.close()
outfile.close()

scp = SCPClient(ssh.get_transport())
scp.put(newfile, corevol)

# Copy core file to shared volume 
print "Copying core file to shared volume on container host..." 
scp.put(corelocation, corevol)

# Initialize docker container based on newly created dockerfile
# Right now we use exec_command over ssh, however in a future version we will use docker-py
print "Generating container image... this may take awhile..."

# Exec command won't accept multiple strings so we have to build the docker build command first as a string
dockerbuild = "cd %s ; docker build --tag=%s --file=%s ." % (corevol, newfile, newfile) 
stdin, stdout, stderr = ssh.exec_command(dockerbuild)

# Monitor the progress of the docker build
while not stdout.channel.exit_status_ready():
	if stdout.channel.recv_ready():
		print stdout.channel.recv(1024)

# CLEANUP
# Remove generated dockerfile on client and container host as well as remove the core file from the corevol directory since it
# is now inside the container
print "\n"
print "Container generated. Cleaning up temporary files..."
os.remove(newfile)
removefile = "cd %s; rm %s" % (corevol, corefile)
ssh.exec_command(removefile)

# COMPLETED
# Tell the user where to go
# We're placing dockerun in a string for use later
dockerrun = "docker run -ti %s /usr/bin/gdb %s" % (newfile, corefile)
print "-------------------------------------------"
print "FINISHED. Access the core file on %s with" %containerhost
print "# %s" %dockerrun 
print "-------------------------------------------"

