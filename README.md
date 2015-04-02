# bumblebee 
**Application core environment automation**

Bumblebee is an application core environment automater written in python.  Environments with valid debuginfo packages are spun up on demand on the container host using docker.  

## Client install from source

 * Python 2.x
 * `pip install scp uuid validators`
 * Edit environment variables `containerhost` and `corevol` inside `create-container.py` 

## Server requirements

 * Subscribed to the debuginfo and default repositories for your distro.
 * Temporary space to house incoming core files and dockerfile's.
 * Plenty of space to host containers.  Due to the size of debuginfo packages, containers may become quite large.
 * docker images for each minor version of your distro.  If you don't have these you can create them using the mkimage.sh scripts provided within the docker repo under `docker/contrib` 


## How it works

1. bumblebee requires a container host to connect to which must be configured with a directory to store user core information.  At this time, clients will need to have passwordless ssh access to the container host (in the future this won't be neccessary).  
2. Once bumblebee is invoked it will request package and version information for the package that produced the application core as well as the version of OS that the core was created on.  Finally it will ask for the location of the core file the user would like an environment created for.
3. Next, the client will connect to the server and spin up a container instance based on osversion, pkgversion and copy the core file to the root of the container.The environment will be created and the correct debuginfo's and other dependencies for the core file will be installed.
4. bumblebee will provide `docker attach` information for the user to attach to their environment to browse the core file in `gdb`.

