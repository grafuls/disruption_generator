# order of subtemplates defined below
SUBTEMPLATES_ORDER = [
    "clusters",
    "hosts",
    "storages",
    "extra_storages",
    "external_providers",
    "external_templates",
    "vms_header",
    "vms",
    "users",
    "groups",
]

# sub templates of which the yaml file consist
#
# format: {
#   <key in engine's data>: {
#     # mandatory
#     'template': <template name>
#     # optional - templates that should be added
#     'header': <header of section in yaml comment>
#     'no_data': <True/False - api has no data, must be changed manually>
#     'additional': {
#     <key in data from parent key>: {
#       'template': <template name>,
#       ...
#     },
#     ...}
#
#   }
# }
SUBTEMPLATES = {
    "clusters": {
        "header": "clusters",
        "template": "cluster",
        "additional": {
            "external_providers": {
                "header": "external_network_providers", "template": "row_name3"
            }
        },
    },
    "hosts": {"header": "hosts", "template": "host"},
    "storages": {
        "header": "storages",
        "template": "storage",
        "additional": {
            "domain_function": {"template": "domain_function"},
            "nfs": {"template": "storage_nfs"},
            "iscsi": {
                "template": "storage_iscsi",
                "additional": {"luns": {"header": "lun_id", "template": "row4"}},
            },
        },
    },
    "extra_storages": {"template": "extra_storages", "no_data": True},
    "external_providers": {
        "header": "external_providers",
        "template": "external_provider",
        "additional": {"authentication": {"template": "external_provider_auth"}},
    },
    "external_templates": {"template": "external_template", "no_data": True},
    "vms_header": {"template": "vm_header", "no_data": True},
    "vms": {"header": "vms", "template": "vm"},
    "users": {"header": "users", "template": "user"},
    "groups": {
        "header": "user_groups",
        "template": "group",
        "additional": {"users": {"template": "row3"}},
    },
}
