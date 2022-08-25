# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import re

# Regular expressions for resulting dir and file names
pattern_dir = re.compile("^[0-9]{8}-[0-9]{4}$")
pattern_file = re.compile(
        "^[0-9]{8}-[0-9]{4}-postmarketOS-[a-z0-9._+-]+\\.img\\.xz"
        "(\\.sha(256|512))?$")

# Default password for regular (non-installer) images
password = "147147"

# Branches to build images for, can be overridden per device in 'images' below
branches_default = [
        "master",
        "v22.06",
    ]

# Prevent errors by listing explicitly allowed UIs here. Notably "none" is
# missing, as the UI does not follow the usual naming scheme
# (postmarketos-ui-none/APKBUILD doesn't exist). Code in bpo.jobs.build_image
# would try to extract the pkgver from the file and do something undefined.
# Use "console" instead.
ui_allowlist = [
        "asteroid",
        "console",
        "fbkeyboard",
        "glacier",
        "gnome",
        "i3wm",
        "kodi",
        "lxqt",
        "mate",
        "phosh",
        "plasma-bigscreen",
        "plasma-desktop",
        "plasma-mobile",
        "shelli",
        "sway",
        "sxmo-de-dwm",
        "sxmo-de-sway",
        "weston",
        "xfce4"
    ]

# Build configuration, can be overridden per device/branch in 'images' below
branch_config_default = {
    # Schedule a new image each {date-interval} days, start at {date-start}.
    "date-interval": 7,
    "date-start": "2021-07-21",  # Wednesday

    # User interfaces to build. At least one UI must be set for each device,
    # otherwise no image for that device will be built.
    "ui": [
        "phosh",
        "plasma-mobile",
        "sxmo-de-sway",
    ],

    # Build images with the on-device installer. If set to False, build one
    # image without the installer. If set to True, build another image, which
    # wraps the first image with the installer.
    "installer": False,

    # To create additional images with other kernels selected, override this
    # variable. For qemu-amd64, this could be ["virt", "lts"].
    # https://postmarketos.org/multiple-kernels
    "kernels": [""],

    # How many images (image directories) to keep of one branch:device:ui
    # combination. Older images will get deleted to free up space.
    "keep": 3
}

# For each image you add here, make sure there is a proper wiki redirect for
# https://wiki.postmarketos.org/wiki/<codename>. That is what will show up in
# the generated readme.html!
images = {
    "arrow-db410c": {
        "branch_configs": {
            "all": {
                "ui": [
                    "console",
                ],
            },
        },
    },
    "asus-me176c": {
    },
    "bq-paella": {
    },
    "fairphone-fp4": {
        "branches": [
            "master",
        ],
    },
    "lenovo-a6000": {
    },
    "lenovo-a6010": {
    },
    "motorola-harpia": {
    },
    "nokia-n900": {
        "branch_configs": {
            "all": {
                "ui": [
                    "i3wm",
                ],
            },
         },
    },
    "odroid-hc2": {
        "branch_configs": {
            "all": {
                "ui": [
                    "console",
                ],
            },
        },
    },
    "oneplus-enchilada": {
    },
    "oneplus-fajita": {
    },
    "pine64-pinebookpro": {
        "branch_configs": {
            "all": {
                "ui": [
                    "console",
                    "gnome",
                    "plasma-desktop",
                    "sway",
                    "phosh",
                ],
                "installer": True,
            },
        },
    },
    "pine64-pinephone": {
        "branch_configs": {
            "all": {
                "installer": True,
            },
        },
    },
    "pine64-pinephonepro": {
        "branch_configs": {
            "all": {
                "installer": True,
            },
        },
    },
    "pine64-pinetab": {
        "branch_configs": {
            "all": {
                "installer": True,
                "kernels": [
                    "allwinner",
                ],
            },
        },
    },
    "pine64-rockpro64": {
        "branch_configs": {
            "all": {
                "ui": [
                    "console",
                    "plasma-bigscreen",
                ],
            },
        },
    },
    "purism-librem5": {
        "branch_configs": {
            "all": {
                "installer": True,
            },
        },
    },
    "samsung-a3": {
    },
    "samsung-a5": {
    },
    "samsung-e7": {
    },
    "samsung-espresso3g": {
        "branch_configs": {
            "all": {
                "ui": [
                    "phosh",
                    "xfce4",
                ],
            },
        },
    },
    "samsung-gt510": {
    },
    "samsung-gt58": {
    },
    "samsung-m0": {
        "branches": [
            "master",
            "v22.06",
        ],
        "branch_configs": {
            "all": {
                "ui": [
                    "phosh",
                    "sxmo-de-sway",
                ],
            },
        },
    },
    "samsung-serranove": {
    },
    "shift-axolotl": {
        "branches": [
            "master",
            "v22.06",
        ],
    },
    "wileyfox-crackling": {
    },
    "xiaomi-beryllium": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "tianma",
                    "ebbg",
                ],
            },
        },
    },
    "xiaomi-scorpio": {
    },
    "xiaomi-wt88047": {
    },
}
