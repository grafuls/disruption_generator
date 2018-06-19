# part of keys in config files to filter
DATABASE_SETUP_FILES_KEYS = ["user", "password"]

# Setting for getting database informations
# format: [{
#   'file': <file name in etc dir from defaults.cfg>
#   'regex': <regular expression of lines to filter for specific db>
#   'key_prefix': <prefix for DATABASE_SETUP_FILES_KEYS to substitute in
#       templates>
# }, ...]
DATABASE_SETUP_FILES = [
    {"file": "10-setup-database.conf", "regex": "ENGINE_DB", "key_prefix": "db"},
    {"file": "10-setup-dwh-database.conf", "regex": "DWH_DB", "key_prefix": "dwh_db"},
]
