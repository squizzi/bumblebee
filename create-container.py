#!/usr/bin/env python
import sys
import paramiko
import os
import os.path
import uuid
from scp import SCPClient
#import dockerpy

# Environment variables
containerhost = "hostname.example.com"
corevol = "/cores"

# Input requests
osversion = raw_input('Enter the RHEL version the core file was created on (4, 5, 6 or 7): ')
pkgversion = raw_input('Enter the full package name-version.arch (ex. autofs-5.0.5-109.el6_6.1.x86_64): ')
corelocation = raw_input('Enter the full path to the core file you need analyzed: ')
print '\n'

# Verification
print "Creating an environment with the following details: "
print "* OS version: %s" %osversion
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
ssh.connect(containerhost, username="root",password="password", look_for_keys=False)

print "Initializing docker container..."

# Build the docker file locally from the dockerfile skeleton and copy it to the container host
u = uuid.uuid4()
newfile = u.hex
corefile = os.path.basename(corelocation)
infile = open('dockerfile')
outfile = open(newfile, 'w')
replacements = {'$osversion':osversion, '$pkgversion':pkgversion, '$corefile':corefile}

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

# FIXME: Monitor the progress of docker build


# All done, tell the user where to go
# We're placing dockerun in a string for use later
dockerrun = "docker run -ti %s /usr/bin/gdb %s" % (newfile, corefile)
print "Container generated.  Access the core file by running:" dockerrun

# Cleanup
# Remove generated dockerfile on client and container host
print "Cleaning up temporary files..."
os.remove(newfile)
removefile = "cd %s; rm %s" % (corevol, corefile)
ssh.exec_command(removefile)
sys.exit(1)
