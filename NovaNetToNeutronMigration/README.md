The aim of this tool is to help operators migrate their OpenStack clusters from nova-network to Neutron


Some history
Current migration plan is discussed in specs https://review.openstack.org/#/c/147723/ & https://review.openstack.org/#/c/142456/.

According to the plan, the migration is divided into two steps:
1. Database Migration
2. VIF migration

The tool for database migration is under review. For VIF migration, the plan is to rely on neutron agent to do the wiring. To trigger neutron agent to do that, one option is to enable neutron agent and reboot the hypervisor. The problem with this approach is that, reboot of a hypervisor doesn't ensure graceful shutdown of the processes (VMs) running on the hypervisor. This can be a problem as the processes running on the VM will die abruptly. Ideally, we would want to gracefully shutdown the VMs before rebooting (if needed) the hypervisor.

The other option to trigger neutron agent to rename the taps is to virsh shutdown the VMs individually, and then do a nova start. This accomplishes two things:

1. virsh shutdown causes VMs to shutdown gracefully
2. nova start causes regeneration of libvirt.xml from latest network_info from instance_info_cache. This libvirt xml has the updated vif name and tag.

This approach has been tested on simple VLAN network case using ML2 plugin and openvswitch agent.




