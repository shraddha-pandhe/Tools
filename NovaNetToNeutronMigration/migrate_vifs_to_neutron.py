#!/home/y/bin/python2.6


import exceptions
import getpass
import json
import logging
import optparse
import os
import time

import fabric
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import sudo

from Hypervisor import Hypervisor
from Parallel import Parallel
from VirtualMachine import VirtualMachine

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG_FORMAT = '%(asctime)s %(levelname)s: [%(name)s] : %(message)s'
fh = logging.FileHandler("migration.log",
                         mode='a', encoding=None,
                         delay=False)

fh.setFormatter(logging.Formatter(LOG_FORMAT))
LOG.addHandler(fh)

user = getpass.getuser()

fabric.state.output['debug'] = True


def main():
    parser = optparse.OptionParser()
    parser.add_option('-f', '--hypervisor_list', dest='hv_list',
                      help='hypervisor list to be migrated')

    (options, _) = parser.parse_args()
    env.host_string = 'localhost'
    hv_list = json.load(open(options.hv_list))

    all_vms_cluster = []
    Hypervisors = []  # List of all hypervisors in the cluster

    all_vms = []

    for hv in hypervisor_list:
        hv_obj = Hypervisor(hv)
        Hypervisors.append(hv_obj)

    # Maintain a list of all VMs
    all_vms.extend(get_list_of_all_vms(Hypervisors))

    # Start configuring network
    shutdown_all(Hypervisors)

    # nova start all in parallel
    start_all(all_vms_rack)
    LOG.debug("Sleeping for 20 seconds")
    time.sleep(20)

    # nova reboot all in parallel
    reboot_all(all_vms_rack)

    # Save all VMs in the cluster
    all_vms_cluster.extend(all_vms_rack)


def start_all(VMs):
    if VMs:
        vmList = Parallel(LOG)
        vmList.hosts = [vm.uuid for vm in VMs]
        vmList.start("nova start")


def reboot_all(VMs):
    if VMs:
        vmList = Parallel(LOG)
        vmList.hosts = [vm.uuid for vm in VMs]
        vmList.start("nova reboot")
    time.sleep(80)


def get_list_of_all_vms(Hypervisors):
    vmList = Parallel(LOG)
    vmList.hosts = [hv.hostname for hv in Hypervisors]
    vm_tables = (vmList.start("nova hypervisor-servers"))
    all_vms = []
    index = 0
    for vm_table in vm_tables:
        vms = []
        lines = vm_table['stdout'].split('\n')
        # Logic to return if no VMs on the hypervisor
        if len(lines) > 5:
            for line in lines[3:len(lines)-2]:
                uuid = line.split(" ")[1]
                vm = VirtualMachine(uuid)
                # Fetch all the information about the VM from nova
                vm.preprocess()
                vms.append(vm)
            Hypervisors[index].vms = vms
            all_vms.extend(vms)
        index = index + 1
    return all_vms


def shutdown_all(Hypervisors):
    hv_list = [hv.hostname for hv in Hypervisors]
    env.hosts = hv_list
    execute(shutdown, Hypervisors=Hypervisors)


@parallel(pool_size=7)
def shutdown(Hypervisors):
    vm_list = []
    my_hostname = sudo("hostname")

    # This code is meant to execute parallelly on all the hypervisors.
    # Hence, on the hypervisor, need the list of VMs on that hypervisor

    for hv in Hypervisors:
        if hv.hostname == my_hostname:
            vm_list = [vm for vm in hv.vms]

    if vm_list:
        # Get a list of domain names
        domains = [vm.domain for vm in vm_list]

        # Virsh shutdown all the VMs on this hypervisor
        # This is being done as a replacement for nova stop
        # Currently there is no command in nova that does a graceful
        # shutdown. Solution is to do graceful shutdown using
        # "virsh shutdown" and then run "nova start" to regenerate the
        # network config
        try:
            for domain in domains:
                sudo("virsh shutdown {0}".format(domain), quiet=True)
        except exceptions.Exception as e:
                LOG.error(e)


if __name__ == '__main__':
    main()
