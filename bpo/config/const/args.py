# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Default values for command-line arguments. After pmb.config.init() ran,
    these can be accessed in bpo.config.args (e.g.
    bpo.config.args.job_service). """
import os
import bpo.config.const

# Defaults (common)
tokens = bpo.config.const.top_dir + "/.tokens.cfg"
host = "127.0.0.1"
port = 5000
db_path = bpo.config.const.top_dir + "/bpo.db"
job_service = "local"
mirror = "http://mirror.postmarketos.org/postmarketos"
temp_path = bpo.config.const.top_dir + "/_temp"
repo_final_path = bpo.config.const.top_dir + "/_repo_final"
repo_wip_path = bpo.config.const.top_dir + "/_repo_wip"
images_path = bpo.config.const.top_dir + "/_images"
html_out = bpo.config.const.top_dir + "/_html_out"
auto_get_depends = False
url_api = "https://build.postmarketos.org"
url_repo_wip_http = "http://build.postmarketos.org/wip"
url_repo_wip_https = "https://build.postmarketos.org/wip"
force_final_repo_sign = False

# Defaults (local)
local_pmaports = os.path.realpath(bpo.config.const.top_dir +
                                  "/../pmbootstrap/aports")
local_pmbootstrap = os.path.realpath(bpo.config.const.top_dir +
                                     "/../pmbootstrap")

# Defaults (sourcehut)
sourcehut_user = "postmarketos"
