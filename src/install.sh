#! /bin/bash

# Remember the current directory when the script was started:
INSTALL_DIR="${PWD}"

THIS_SCRIPT_FILE_MAYBE_RELATIVE="$0"
THIS_SCRIPT_DIR_MAYBE_RELATIVE="${THIS_SCRIPT_FILE_MAYBE_RELATIVE%/*}"
THIS_SCRIPT_DIR_ABSOLUTE=`readlink -f "${THIS_SCRIPT_DIR_MAYBE_RELATIVE}"`

linux_version_warning() {
    1>&2 echo "Found ID ${ID} and VERSION_ID ${VERSION_ID} in /etc/os-release"
    1>&2 echo "This script only supports these:"
    1>&2 echo "    ID fedora, VERSION_ID in 36 37 38"
    1>&2 echo ""
    1>&2 echo "Proceed installing manually at your own risk of"
    1>&2 echo "significant time spent figuring out how to make it all"
    1>&2 echo "work, or consider getting VirtualBox and creating a"
    1>&2 echo "virtual machine with one of the tested versions."
}

if [ ! -r /etc/os-release ]
then
    1>&2 echo "No file /etc/os-release.  Cannot determine what OS this is."
    linux_version_warning
    exit 1
fi
source /etc/os-release

supported_distribution=0
tried_but_got_build_errors=0
if [ "${ID}" = "ubuntu" ]
then
    case "${VERSION_ID}" in
	20.04)
	    supported_distribution=0
	    ;;
    esac
elif [ "${ID}" = "fedora" ]
then
    case "${VERSION_ID}" in
	36)
	    supported_distribution=1
	    ;;
	37)
	    supported_distribution=1
	    ;;
	38)
	    supported_distribution=1
	    ;;
    esac
fi

if [ ${supported_distribution} -eq 1 ]
then
    echo "Found supported ID ${ID} and VERSION_ID ${VERSION_ID} in /etc/os-release"
else
    linux_version_warning
    if [ ${tried_but_got_build_errors} -eq 1 ]
    then
	1>&2 echo ""
	1>&2 echo "This OS has been tried at least onc before, but"
	1>&2 echo "there were errors during a compilation or build"
	1>&2 echo "step that have not yet been fixed.  If you have"
	1>&2 echo "experience in fixing such matters, your help is"
	1>&2 echo "appreciated."
    fi
    exit 1
fi


set -ex
if [ ${ID} = "fedora" ]
then
    sudo dnf -y install graphviz graphviz-devel python-devel
fi

python3 -m venv ${INSTALL_DIR}/my-venv
source ${INSTALL_DIR}/my-venv/bin/activate
pip install matplotlib networkx ortools pygraphviz
set +ex

echo "You must run this command in any shell where you want to run"
echo "P416Compiler:"
echo ""
echo "    source ${INSTALL_DIR}/my-venv/bin/activate"
echo ""
echo "You can try P416Compiler on a sample input file included in this"
echo "package with these commands, after the setup above:"
echo ""
echo "    cd ${INSTALL_DIR}/src"
echo "    python3 main.py"
