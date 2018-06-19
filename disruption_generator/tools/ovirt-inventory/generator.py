#!/usr/bin/python

import argparse
import codecs
import configparser
import os
import re
import sys
import traceback
import yaml

from cStringIO import StringIO
from helpers.api import ApiData
from helpers.engine import EngineData
from helpers.yaml import YamlGenerator
from jinja2 import Environment, FileSystemLoader


PRODUCT_MAP = {"ovirt": "ovirt-engine", "rhv": "ovirt-engine", "rhevm": "ovirt-engine"}

FILE_STORAGE_TYPES = ("nfs", "glusterfs")
BLOCK_STORAGE_TYPES = ("iscsi", "fcp")

SD_TYPES = ["nfs", "iscsi", "glusterfs", "fcp"]

RE_VERSION = re.compile(".*-(?P<version>[0-9][.][0-9])")


def generate_ge_description(ge_yaml):
    env = Environment(loader=FileSystemLoader("/"))
    template = env.get_template(ge_yaml)
    with open(ge_yaml, "r") as f:
        context = yaml.load(f)

    rendered_yaml = template.render(context)
    return rendered_yaml


def generate(ge_dscr, inventory, env_vars):
    if inventory:
        with inventory:
            generate_inventory(ge_dscr, inventory)
    if env_vars:
        with env_vars:
            generate_env_vars(ge_dscr, env_vars)


def get_data_storage(storages, storage_name):
    storage = [s for s in storages if s.get("name") == storage_name][0]
    return get_storage(storage, storage_name, "data")


def get_storage(storage, storage_name, storage_for):
    storage_details = [
        "{storage_for}_storage_type={storage_type}",
        "{storage_for}_storage_name={storage_name}",
    ] if storage_for in (
        "data", "hosted"
    ) else []
    if storage["type"] != "fcp":
        storage_details.append(
            "{storage_for}_storage_address={address}".format(
                storage_for=storage_for, address=storage.get("address")
            )
        )
    if storage["type"] in FILE_STORAGE_TYPES:
        storage_details.append("{storage_for}_storage_path=%s" % storage["path"])
    elif storage["type"] in BLOCK_STORAGE_TYPES:
        storage_details.append("{storage_for}_storage_lun=%s" % storage["lun"])
    storage_details.append("")
    return "\n".join(storage_details).format(
        storage_for=storage_for, storage_name=storage_name, storage_type=storage["type"]
    )


def generate_hosted_engine_inventory(data, hypervisors_line):
    hosted_engine_content = [
        "",
        "[all:vars]",
        "engine_fqdn={engine}",
        "admin_password={engine_admin_password}",
        "config_dir={config_dir}",
        "engine_username={engine_username}",
        "cpu_model={cpu_model}",
        "compatibility_version={version}",
        "vm_timezone={vm_timezone}",
        "product={product}",
        "",
        "{hosted_storage}",
        "{data_storage}",
        "cpu_type={cpu_type}",
        "mac_address_range='{mac_address_range}'",
        "mac_pool_name={mac_pool_name}",
        "dc_name={dc_name}",
        "cluster_name={cluster_name}",
        "ovirt_engine_db_user={engine_db_user}",
        "ovirt_engine_db_password={engine_db_password}",
        "ovirt_engine_dwh_db_user={engine_dwh_db_user}",
        "ovirt_engine_dwh_db_password={engine_dwh_db_password}",
        "engine_mac_address='{engine_mac_address}'",
        "root_password={root_password}",
        "ovirt_base_mount_path={ovirt_base_mount_path}",
        "host_name={host_name}{{ host_id }}",
        "{engine_static_address}",
        "",
        "[self_hosted_first_host]",
        "{self_hosted_first_host}",
        "",
        "[self_hosted_additional_hosts]",
        "{self_hosted_additional_hosts}",
        "",
        "[hosted_hypervisors:children]",
        "self_hosted_first_host",
        "self_hosted_additional_hosts",
        "",
        "[self_hosted_engine:children]",
        "engine",
        "",
    ]

    hypervisors_line += " host_id={host_id}"
    hosted_engine_details = data["hosted_engine_details"]
    mac_address_range = data["mac_pools"][0]["mac_pool_ranges"][0].replace(",", "-")
    hosted_storage = get_hosted_storage(hosted_engine_details["storages"])
    data_sd_name = hosted_engine_details.get("data_storage_name", "nfs_0")
    all_storages_with_type = get_all_storages_with_type(data)
    data_storage = get_data_storage(all_storages_with_type, data_sd_name)
    first_host = get_first_host(data["hosts"])
    self_hosted_first_host = hypervisors_line.format(
        **dict(first_host, nested=first_host.get("nested", False))
    )

    self_hosted_additional_hosts = "\n".join(
        hypervisors_line.format(**dict(h, nested=h.get("nested", False)))
        for h in get_additional_hosts(data["hosts"])
    )
    static_address = hosted_engine_details.get("engine_static_address", "")
    if static_address:
        static_address = "engine_vm_static_net_address=%s" % static_address

    hosted_engine_content = "\n".join(hosted_engine_content).format(
        engine=data["engine_fqdn"],
        engine_admin_password=data["password"],
        config_dir=hosted_engine_details["config_dir"],
        engine_username=data["username"],
        cpu_model=hosted_engine_details["cpu_model"],
        version=data["version"],
        vm_timezone=hosted_engine_details.get("vm_timezone", "Asia/Jerusalem"),
        product=data["product"],
        hosted_storage=hosted_storage,
        data_storage=data_storage,
        cpu_type=data["cpu_type"],
        mac_address_range=mac_address_range.replace("-", ","),
        mac_pool_name=data["mac_pools"][0]["mac_pool_name"],
        dc_name=data["data_center_name"],
        cluster_name=data["clusters"][0]["name"],
        engine_db_user=data["engine_db_user"],
        engine_db_password=data["engine_db_password"],
        engine_dwh_db_user=data["engine_dwh_db_user"],
        engine_dwh_db_password=data["engine_dwh_db_password"],
        engine_mac_address=hosted_engine_details["engine_mac_address"],
        engine_static_address=static_address,
        root_password=data["root_passwd"],
        ovirt_base_mount_path=hosted_engine_details["ovirt_base_mount_path"],
        host_name=data["hosts"][0]["name"].strip()[:-1],
        self_hosted_first_host=self_hosted_first_host,
        self_hosted_additional_hosts=self_hosted_additional_hosts,
    )
    return hosted_engine_content.replace("{", "{{").replace("}", "}}")


def generate_inventory(data, inventory):

    def get_host_dict(h):
        return dict(h, nested=h.get("nested", False))

    content = [
        "[engine:vars]",
        "ovirt_engine_type={product}",
        "ovirt_engine_version={version}",
        "ovirt_engine_dwh=True",
        "ovirt_engine_hostname={engine}",
        "ovirt_engine_organization={organization}",
        "ovirt_engine_admin_password={engine_admin_password}",
        "ovirt_engine_api_url={api_url}",
        "ovirt_engine_username={username}",
        "engine_coverage_product={coverage_product}",
        "",
        "[engine]",
        "{engine_line}",
        "",
        "[rhel-hypervisors]",
        "{rhel_hypervisors}",
        "",
        "[rhvh-hypervisors]",
        "{rhvh_hypervisors}",
        "",
        "[hypervisors:children]",
        "rhel-hypervisors",
        "rhvh-hypervisors",
        "",
        "[database]",
        "{engine_line}",
        "",
        "[dwh]",
        "{engine_line}",
        "",
    ]
    hosted_engine = True if data.get("hosted_engine_details", None) else False
    engine = "{engine}".format(engine=data["engine_fqdn"])
    engine_line = "{engine} os={os}".format(
        engine=data["engine_fqdn"], os=data["engine_os"]
    )
    if hosted_engine:
        ansible_user_pwd = " ansible_user=root ansible_ssh_pass={root_pwd}"
        engine_line += ansible_user_pwd.format(root_pwd=data["root_passwd"])
    hypervisors_line = "{address} os={os} nested={nested}"
    rhel_hypervisors = "\n".join(
        hypervisors_line.format(**get_host_dict(h))
        for h in get_rhel_hosts(data["hosts"])
    )
    rhvh_hypervisors = "\n".join(
        hypervisors_line.format(**get_host_dict(h))
        for h in get_rhvh_hosts(data["hosts"])
    )
    content = "\n".join(content).format(
        engine=engine,
        engine_line=engine_line,
        organization=data["engine_fqdn"].split(".", 1)[-1],
        engine_admin_password=data["password"],
        rhel_hypervisors=rhel_hypervisors,
        rhvh_hypervisors=rhvh_hypervisors,
        version=data["version"],
        product=PRODUCT_MAP[data["product"]],
        coverage_product=data["product"],
        username=data["username"],
        api_url=data["api_url"],
    )

    with inventory:
        inventory.write(content)
        if hosted_engine:
            inventory.write(generate_hosted_engine_inventory(data, hypervisors_line))
        print("inventory file saved to %s" % inventory.name)


def get_storage_types(storages):
    types = set()
    for storage in storages:
        type_ = storage["type"]
        if type_:
            types.add(type_)
    return list(types)


def get_all_storages_with_type(data):

    all_storages = []

    for sd_name, sd_info in data["storages"].items():
        if "domain_function" in sd_info:  # iso or export
            continue
        storage = {}
        for storage_type in SD_TYPES:
            if storage_type in sd_info:
                storage.update({"name": sd_name})
                storage.update({"type": storage_type})
                storage.update(sd_info[storage_type])
                all_storages.append(storage)

    return all_storages


def get_rhel_hosts(hosts):
    return [h for h in hosts if "rhel" in h["os"].lower()]


def get_rhvh_hosts(hosts):
    return [
        h for h in hosts if "rhvh" in h["os"].lower() or "ovirt-node" in h["os"].lower()
    ]


def get_hosts_with_host_id(start_point, hosts):
    index = start_point
    for host in hosts:
        host["host_id"] = index
        index += 1
    return hosts


def get_first_host(hosts):
    return get_hosts_with_host_id(1, [hosts[0]])[0]


def get_additional_hosts(hosts):
    return get_hosts_with_host_id(2, hosts[1:])


def main():
    """
    This script generates yaml description file for jenkins tests,
    provided information from engine API and system via SSH.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Generate yaml description file for jenkins tests.",
        epilog=(
            "Examples:\n"
            "generator.py -s engine1.example.com -s engine2.example.com\n"
            "generator.py -s engine1.example.com -c /tmp/some_defaults.cfg\n"
        ),
    )
    parser.add_argument(
        "-s",
        "--server",
        action="append",
        help="Engine server address (can be used repeatedly)",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--config",
        help=(
            "Configuration file path, with api, ssh and other sections "
            "that can override some default values from defaults.cfg"
        ),
        required=False,
    )
    parser.add_argument(
        "-i",
        "--inventory",
        help="path to inventory output",
        type=argparse.FileType("w"),
        default="inventory",
    )
    parser.add_argument(
        "-v",
        "--env-vars",
        help="export environment variables",
        type=argparse.FileType("w"),
        default=None,
    )

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read("defaults.cfg")
    # overriding the defaults
    if args.config:
        if not os.path.isfile(args.config):
            print("Configuration file was not found in given location")
            sys.exit(1)
        config.read(args.config)

    _yaml = YamlGenerator(config)

    for server in args.server:
        try:
            api = ApiData(config, server)
            data = api.get_engine_data()
            engine = EngineData(config, server)
            data.update(engine.get_data())

            path = os.path.join(config["other"]["output_dir"], "%s.yaml" % server)

            with codecs.open(path, "w", "UTF-8") as file_out:
                result, error = _yaml.write_engine(data, file_out)
                if result:
                    print("yaml file saved to %s" % file_out.name)
                else:
                    print(error)
                    sys.exit(1)
            data = generate_ge_description(path)
            stream = StringIO(data)
            data = yaml.load(stream)
            generate(data, args.inventory, args.env_vars)

        except Exception:
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

    print(
        "NOTICE: Generated yaml files are not fully functional yet,"
        " some manual changes must be done, see the yaml file."
    )
    sys.exit(0)


def get_host_os_versions(hosts):
    """
    Returns list of os address:version of given hosts.

    Args:
        hosts(list): List of hosts dict

    Returns (list): list of address:os_version
    """
    return [
        "{address}:{version}".format(
            address=host["address"],
            version=RE_VERSION.match(host["os"]).group("version"),
        )
        for host in hosts
    ]


def generate_env_vars(data, output):
    all_storages_with_type = get_all_storages_with_type(data)
    rhvh_hosts = get_rhvh_hosts(data["hosts"])
    rhel_hosts = get_rhel_hosts(data["hosts"])
    extra_conf_options = data.get("extra_configuration_options", dict())
    engine_os_release = RE_VERSION.match(data.get("engine_os")).group("version")
    content = [
        "export PRODUCT=%s" % data["product"],
        "export VERSION=%s" % data["version"],
        "export VDS=%s" % ",".join(h["address"] for h in data["hosts"]),
        "export VDS_RHEL=%s"
        % ",".join(h["address"] for h in get_rhel_hosts(data["hosts"])),
        'export VDS_RHEL_OS_VER="%s"' % " ".join(get_host_os_versions(rhel_hosts)),
        "export VDS_RHVH=%s"
        % ",".join(h["address"] for h in get_rhvh_hosts(data["hosts"])),
        'export VDS_RHVH_OS_VER="%s"'
        % " ".join(["%s:%s" % (host["address"], host["os"]) for host in rhvh_hosts]),
        "export BEAKER_HOSTS=%s"
        % ",".join(
            [h["address"] for h in data["hosts"] if h.get("managed_by") == "beaker"]
        ),
        "export ENGINE=%s" % data["engine_fqdn"],
        "export ENGINE_RHEL_RELEASE=%s" % engine_os_release,
        "export STORAGE_TYPES=%s" % ",".join(get_storage_types(all_storages_with_type)),
        "export HOSTED_ENGINE=%s"
        % (True if data.get("hosted_engine_details", None) else False),
        "export GLUSTER_ENV=%s" % extra_conf_options.get("gluster_environment", False),
    ]
    with output:
        output.write("\n".join(content))
        output.write("\n")


def get_hosted_storage(storages):
    hosted_storage_params = [get_storage(storages[0], "hosted_storage", "hosted")]
    for storage in storages:
        storage_for = "%s_hosted" % storage["type"]
        hosted_storage_params.append(
            get_storage(storage, "hosted_storage", storage_for)
        )
    return "\n".join(hosted_storage_params)


if __name__ == "__main__":
    main()
