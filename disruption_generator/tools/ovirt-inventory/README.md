# ovirt-inventory
Dynamic ansible inventory generator for oVirt.

## Result inventory and yaml files
* Generated inventory file contains all hosts grouped by hypervisors, engine, db.
* Generated .yaml file contains information for all clusters, storages, host, vms, templates, external providers and other. This informations are provided by REST API. 
* Task 'extra_configuration_options' is loaded from defaults.cfg or additional settings added with -c argument.
* Other informations about engine (like version, arch, engine_os) are loaded via rrmngmnt.

## Configuration
* Username and password for both engine and SSH credentials need to be updated on defaults.cfg
```
[api]
USER=admin@internal
PASSWORD=${PASS}
URL=/ovirt-engine/api

[ssh]
USER=root
PASSWORD=${PASS}
```

## Ansible modules 
Definition for tasks in .yaml file you can find on [Ansible docs](http://docs.ansible.com/ansible/latest/modules/) page.

For example ovirt_storage_domains module is used for storages or ovirt_hosts for hosts and so on.

## Examples
* $ ./generator.py -s my-engine.redhat.com -s my-engine2.redhat.com
    - generates two .yaml and inventory files for each engine

* $ ./generator.py -s my-engine.redhat.com -c ~/my-config.cfg
    - generates .yaml and inventory files for engine with overriden settings from my-config.cfg: