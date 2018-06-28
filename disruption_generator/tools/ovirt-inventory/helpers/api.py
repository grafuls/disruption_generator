"""
Classes that gets data from engine API
"""

import requests

from helpers.config import api as api_config


class RhvmApi:
    """
    Class that processes API calls
    """

    # dict with values for sections api, ssh and other
    config = None
    # part of url for api (with / in the end)
    api_url = ""
    # server http adress (without / in the end)
    server_url = ""

    def __init__(self, config, server):
        self.config = config
        self.server_url = "https://%s" % server

        self.api_url = self.config["api"]["URL"]
        if self.api_url[-1] != "/":
            self.api_url += "/"
        if self.api_url[0] != "/":
            self.api_url = "/" + self.api_url

        requests.packages.urllib3.disable_warnings()

    def get_api_url_part(self, url_part=""):
        """
        Get proper address as url part for sel.get()

        Arguments:
            url_part (str): url address part to process
        Returns: (str) url part for self.get()
        """
        return url_part.replace(self.api_url, "")

    def get(self, url_part="", data=None):
        """
        Get data from api

        Arguments:
            url_part (str): url address part to call (after adress to api e.g.
                /ovirt-engine/api)
        Returns: (dict) data from api call
        Raises: (ApiException) In case api call was not sucessfull
        """
        url = self.server_url + self.api_url + url_part
        api_result = requests.get(
            url,
            auth=(self.config["api"]["USER"], self.config["api"]["PASSWORD"]),
            data=data,
            headers={"Accept": "application/json", "Prefer": "persistent-auth"},
            verify=False,
        )
        try:
            return api_result.json()
        except Exception:
            raise ApiException("GET {}: {}".format(url, str(api_result)))


class ApiData:
    """
    Class that processes data from API
    """

    config = None
    server = ""

    def __init__(self, config, server):
        self.config = config
        self.server = server
        self.api = RhvmApi(config, server)

    def get_link(self, links, name):
        """
        Get proper url from links in api data

        Arguments:
            links (list): links in api data
            name (str): rel name of the link
        Returns: (str/None) found url for the link, None otherwise
        """
        for link in links:
            if "rel" in link and link["rel"] == name:
                return self.api.get_api_url_part(link["href"])
        return None

    def set_authentication(self, data):
        """
        Set authentication values for provider

        Arguments:
            data (dict): data where the authentication should be set
        """
        if "requires_authentication" in data:
            data["authentication"] = {
                key: data.get(key, "") for key in api_config.EXT_PROVIDER_AUTH_KEYS
            }

    def get_externalprovider_data(self, links):
        """
        Get network external providers from links in api data

        Arguments:
            links (list): links in api data
        Returns: (list) list of network providers
        """
        providers = []
        ext_link = self.get_link(links, "externalnetworkproviders")
        if ext_link:
            data_provider = self.api.get(ext_link)
            if "external_provider" in data_provider:
                for provider in data_provider["external_provider"]:
                    self.set_authentication(provider)
                    providers.append(provider)
        return providers

    def get_cluster_data(self):
        """
        Get clusters api data

        Returns: (list) clusters data
        """
        clusters = []
        data_clusters = self.api.get("clusters")
        for cluster in data_clusters["cluster"]:
            cluster["version"] = "{}.{}".format(
                cluster["version"]["major"], cluster["version"]["minor"]
            )
            if "cpu" in cluster:
                cluster["cpu_type"] = cluster["cpu"]["type"]
            else:
                cluster["cpu_type"] = "{{ cpu_type }}"
            cluster["external_providers"] = self.get_externalprovider_data(
                cluster["link"]
            )
            data_macpool = self.api.get(
                self.api.get_api_url_part(cluster["mac_pool"]["href"])
            )
            cluster["mac_pool_name"] = data_macpool["name"]

            clusters.append(cluster)

        return clusters

    def get_host_data(self):
        """
        Get hosts api data

        Returns: (list) hosts data
        """
        hosts = []
        data_hosts = self.api.get("hosts")
        for host in data_hosts.get("host", []):
            try:
                host["os_version"] = "{os_type}-{major_ver}.{minor_ver}".format(
                    os_type=host["os"]["type"],
                    major_ver=host["os"]["version"]["major"],
                    minor_ver=host["os"]["version"].get("minor", "x"),
                )
            except KeyError:
                host["os_version"] = ""
            data_cluster = self.api.get(
                self.api.get_api_url_part(host["cluster"]["href"])
            )
            host["cluster"] = data_cluster["name"]
            hosts.append(host)

        return hosts

    def get_storage_data(self):
        """
        Get storages api data

        Returns: (list) storages data
        """
        storages = []
        data_storages = self.api.get("storagedomains")
        for storage in data_storages.get("storage_domain", []):
            storage_ad = storage["storage"]
            if storage["type"] == "image":
                continue
            if storage_ad["type"] == "nfs":
                storage["nfs"] = storage_ad
            elif storage_ad["type"] == "iscsi":
                luns = storage_ad["volume_group"]["logical_units"]
                if not isinstance(luns["logical_unit"], list):
                    luns = [luns["logical_unit"]]
                else:
                    luns = luns["logical_unit"]
                for lun in luns:
                    if "iscsi" not in storage:
                        lun_id = lun["id"]
                        lun.pop("id")
                        storage["iscsi"] = lun
                        storage["iscsi"]["luns"] = [{"value": lun_id}]
                    else:
                        storage["iscsi"]["luns"].append({"value": lun_id})
            storage["state"] = "present"  # for testing is enough
            if storage["type"] != "data":
                storage["domain_function"] = {"value": storage["type"]}
            storages.append(storage)

        return storages

    def get_macpool_data(self):
        """
        Get mac pools api data

        Returns: (list) mac pools data
        """
        macpools = []
        data_macpools = self.api.get("macpools")
        for macpool in data_macpools["mac_pool"]:
            macpool_pom = {"name": macpool["name"], "ranges": []}
            for mac_range in macpool["ranges"]["range"]:
                macpool_pom["ranges"].append(mac_range["from"] + "," + mac_range["to"])
                macpools.append(macpool_pom)
        return macpools

    def get_ext_provider_data(self):
        """
        Get data external providers api data (from helpers.config.api)

        Returns: (list) external providers data
        """
        providers = []
        for conf_item in api_config.EXT_PROVIDERS:
            data_providers = self.api.get(conf_item["url"])
            if data_providers:
                for provider in data_providers[conf_item["variable"]]:
                    provider["type"] = conf_item["type"]
                    provider["state"] = "present"  # for testing is enough
                    self.set_authentication(provider)
                    providers.append(provider)

        return providers

    def get_vm_data(self):
        """
        Get VMs api data

        Returns: (list) VMs data
        """
        vms = []
        data_vms = self.api.get("vms")
        for vm in data_vms.get("vm", []):
            vm["tag"] = ""
            tags_link = self.get_link(vm["link"], "tags")
            if tags_link:
                data_tag = self.api.get(tags_link)
                if data_tag:
                    tags = []
                    for tag in data_tag["tag"]:
                        tags.append(tag["name"])
                    vm["tag"] = ",".join(tags)
            vms.append(vm)

        return vms

    def get_domain_data(self):
        """
        Get user's domains api data

        Returns: (list) domains data
        """
        domains = []
        data_domains = self.api.get("domains")
        for domain in data_domains["domain"]:
            domain["groups"] = []
            group_link = self.get_link(domain["link"], "groups")
            data_groups = self.api.get(group_link)
            if data_groups:
                for group in data_groups["group"]:
                    domain["groups"].append(
                        {
                            "name": group["name"],
                            "authz_name": domain["name"],
                            "users": [],
                        }
                    )

            domain["users"] = []
            user_link = self.get_link(domain["link"], "users")
            data_users = self.api.get(user_link)
            if data_users:
                for user in data_users["user"]:
                    user["authz_name"] = domain["name"]
                    if "department" not in user:
                        user["department"] = ""
                    if user["groups"]:
                        for group in user["groups"]["group"]:
                            for group2 in domain["groups"]:
                                if group["name"] == group2["name"]:
                                    group2["users"].append({"value": user["principal"]})
                    domain["users"].append(user)

            domains.append(domain)

        return domains

    def get_user_data(self, domains=[]):
        """
        Get users api data

        Arguments:
            domains (list): if defined, return only for specific user's domains
        Returns: (list) users data
        """
        users = []
        data_users = self.api.get("users")
        for user in data_users.get("user", []):
            if domains and user["domain"]["name"] not in domains:
                continue
            user["authz_name"] = user["domain"]["name"]
            if "department" not in user:
                user["department"] = ""
            if "name" not in user:
                user["name"] = ""
            users.append(user)

        return users

    def get_group_data(self):
        """
        Get user's groups api data

        Returns: (list) groups data
        """
        groups = []
        domains = self.get_domain_data()
        for domain in domains:
            if domain["groups"]:
                for group in domain["groups"]:
                    groups.append(group)

        return groups

    def get_engine_data(self):
        """
        Get engines api data

        Returns: (dict) engines data
        Raises: (ApiException) In case api data can't be loaded
        """
        try:
            data = self.api.get()
            data["name"] = self.server
            data["username"] = self.config["api"]["USER"]
            data["password"] = self.config["api"]["PASSWORD"]
            data["root_password"] = self.config["ssh"]["PASSWORD"]
            data["version"] = "{}.{}".format(
                data["product_info"]["version"]["major"],
                data["product_info"]["version"]["minor"],
            )

            data["mac_pools"] = self.get_macpool_data()
            data["clusters"] = self.get_cluster_data()
            data["hosts"] = self.get_host_data()
            data["storages"] = self.get_storage_data()
            data["nfs_server"] = ""
            for storage in data["storages"]:
                if not data["nfs_server"] and "nfs" in storage:
                    data["nfs_server"] = storage["nfs"]["address"]

            data["external_providers"] = self.get_ext_provider_data()
            data["vms"] = self.get_vm_data()
            data["users"] = self.get_user_data()
            data["groups"] = self.get_group_data()

            return data
        except ApiException as ex:
            raise ex
        except Exception as ex:
            raise ApiException("Error getting data: {}".format(ex))


class ApiException(Exception):
    """
    Class for API exceptions
    """

    def __str__(self):
        return "[API] {}".format(self.message)
