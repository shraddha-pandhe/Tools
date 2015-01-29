#!/usr/bin/python

from fabric.api import local


class VirtualMachine():

    def __init__(self, uuid):
        self.uuid = uuid

    @property
    def status(self):
        status_t = local("nova show {uuid} | grep 'status'"
                         .format(uuid=self.uuid), capture=True)
        status = status_t.split()[3]
        return status.lower()

    def start(self):
        local("nova start {uuid}".format(uuid=self.uuid))

    @property
    def hypervisor(self):
        hv_t = local("nova show {uuid} | grep hypervisor_hostname"
                     .format(uuid=self.uuid), capture=True)
        hv = hv_t.split()[3]
        return hv

    @property
    def domain(self):
        domain_t = local("nova show {uuid} | grep 'instance_name'"
                         .format(uuid=self.uuid), capture=True)
        domain = domain_t.split()[3]
        return domain

    def reboot(self):
        local("nova reboot {uuid}".format(uuid=self.uuid))
