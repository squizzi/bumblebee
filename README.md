# bumblebee 
**Application core environment automation**

Bumblebee is an application core environment automater written in python.  Environments with valid debuginfo packages are spun up on demand on the container host using docker.  

## Client install from source

 * Python 2.x
 * `pip install scp uuid`
 * Edit environment variables `containerhost` and `corevol` inside `create-container.py` 

## Server requirements

 * Subscribed to the debuginfo and default repositories for your distro.
 * Temporary space to house incoming core files and dockerfile's.
 * Plenty of space to host containers.  Due to the size of debuginfo packages, containers may become quite large.
 * docker images for each minor version of your distro.  If you don't have these you can create them using the mkimage.sh scripts provided within the docker repo under `docker/contrib`.  This repo contains the mkimage-yum.sh script as it was built for use on Red Hat Enterprise Linux.

### RHEL Deployment specifics 

For deploying the container host on a RHEL7 machine, create a `.secrets` directory underneath your desired `corevol`. Fill it with the following information pulled from the host machine: 

 * The contents of `/etc/pki/entitlement/`
 * The contents of `/etc/rhsm/ca/`
 * A `redhat.repo` file captured from a RHEL machine that has been subscribed via `subscription-manager`.

~~~
.secrets/
|-- entitlement
|   |-- XXXXX-key.pem
|   `-- XXXXX.pem
|-- redhat.repo
`-- rhsm
    `-- ca
        |-- candlepin-stage.pem
        `-- redhat-uep.pem
~~~

#### Z-Stream Repositories 

If you'd like to support RHEL 6.0 - 6.4 machines you will need to capture `redhat.repo` files from a RHEL6 machine where you've set the release to that specific version, for example: `subscription-manager release --set=6.4`.  This will create 5 repo files that you can pull from the `.secrets` directory: 
~~~
|-- repos
|   |-- 6.0z.repo
|   |-- 6.1z.repo
|   |-- 6.2z.repo
|   |-- 6.3z.repo
|   `-- 6.4z.repo
~~~
This will allow you to spin up environments where cores have been created on older versions of RHEL.  If you don't use z-stream repos you'll encounter issues with package versioning and your build-ids won't match.  This will result in incorrect debuginfos and you won't be able to debug the core files successfully. 

## How it works

1. bumblebee requires a container host to connect to which must be configured with a directory to store user core information.  
2. Once bumblebee is invoked it will request package and version information for the package that produced the application core as well as the version of OS that the core was created on.  Finally it will ask for the location of the core file the user would like an environment created for.
3. Next, the client will connect to the server and spin up a container instance based on osversion, pkgversion and copy the core file to the root of the container. The environment will be created and the correct debuginfo's and other dependencies for the core file will be installed.
4. bumblebee will provide `docker run` information for the user to attach to their environment to browse the core file in `gdb`.

