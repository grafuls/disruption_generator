# Setting for engine's external providers
# format:
#     [{
#         'url': <url part after api_url>
#         'variable': <name of variable in api result containing providers>
#         'type': <ansible type of the provider>
#     }, ...]
EXT_PROVIDERS = [
    {
        "url": "openstackimageproviders",
        "variable": "openstack_image_provider",
        "type": "os_image",
    },
    {
        "url": "openstackvolumeproviders",
        "variable": "openstack_volume_provider",
        "type": "os_volume",
    },
    {
        "url": "openstacknetworkproviders",
        "variable": "openstack_network_provider",
        "type": "network",
    },
]
# keys from api data that are used for authentication
EXT_PROVIDER_AUTH_KEYS = {"username", "tenant_name", "authentication_url"}
