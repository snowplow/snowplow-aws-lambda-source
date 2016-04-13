#!/bin/bash
set -e

# Constants
bintray_user=deploy-snowplow-generic


# Similar to Perl die
function die() {
    echo "$@" 1>&2 ; exit 1;
}

# Check if our Vagrant box is running. Expects `vagrant status` to look like:
#
# > Current machine states:
# >
# > default                   poweroff (virtualbox)
# >
# > The VM is powered off. To restart the VM, simply run `vagrant up`
#
# Parameters:
# 1. out_running (out parameter)
function is_running {
    [ "$#" -eq 1 ] || die "1 argument required, $# provided"
    local __out_running=$1

    set +e
    vagrant status | sed -n 3p | grep -q "^default\s*running (virtualbox)$"
    local retval=${?}
    set -e
    if [ ${retval} -eq "0" ] ; then
        eval ${__out_running}=1
    else
        eval ${__out_running}=0
    fi
}

# Get version, checking we are on the latest
#
# Parameters:
# 1. out_version (out parameter)
# 2. out_error (out parameter)
function get_version {
    [ "$#" -eq 2 ] || die "2 arguments required, $# provided"
    local __out_version=$1
    local __out_error=$2

    # get the version number in a line like 'version = "0.1.0"' from Cargo.toml (e.g 0.1.0)
    file_version="$(vagrant ssh -c 'cd /vagrant && gradle printVersion --quiet' | perl -ne 'print $1 if /(\d+\.\d+\.\d+)/')"
    # take the latest tag, stripping anything not looking like a version (e.g. 0.1.0-rc99 => 0.1.0)
    tag_version="$(git describe --abbrev=0 --tags | perl -ne 'print $1 if /(\d+\.\d+\.\d+)/')"
    
    tag_name="$(git describe --abbrev=0 --tags)"
    
    if [[ "${file_version}" != "${tag_version}" ]]; then
        eval ${__out_error}="'File version ${file_version} != tag version ${tag_version}'"
    else
        eval ${__out_version}=${tag_name}
    fi
}

# Go to parent-parent dir of this script
function cd_root() {
    source="${BASH_SOURCE[0]}"
    while [ -h "${source}" ] ; do source="$(readlink "${source}")"; done
    dir="$( cd -P "$( dirname "${source}" )/.." && pwd )"
    cd ${dir}
}



cd_root

# Precondition for running
running=0 && is_running "running"
[ ${running} -eq 1 ] || die "Vagrant guest must be running to push"

# Precondition
version="" && error="" && get_version "version" "error"
[ "${error}" ] && die "Versions don't match: ${error}. Are you trying to publish an old version, or maybe on the wrong branch?"

# get the api key
read -es -p "Please enter API key for Bintray user ${bintray_user}: " bintray_api_key
echo

vagrant ssh -c "cd /vagrant && ./gradlew bintrayUpload -PBINTRAY_USER=${bintray_user} -PBINTRAY_KEY=${bintray_api_key}"

