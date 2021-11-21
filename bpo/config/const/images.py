# Copyright 2021 Oliver Smith
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
        "v21.06",
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
        "sxmo",  # v21.06
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
        "branches": [
            "master",
            "v21.06",
        ],
        "branch_configs": {
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "asus-me176c": {
        "branch_configs": {
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "bq-paella": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "lenovo-a6000": {
        "branches": [
            "master",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "lenovo-a6010": {
        "branches": [
            "master",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "motorola-harpia": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "nokia-n900": {
        "branch_configs": {
            "all": {
                "ui": [
                    "i3wm",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
            },
         },
    },
    "odroid-hc2": {
        "branches": [
            "master",
        ],
        "branch_configs": {
            "all": {
                "ui": [
                    "console",
                ],
            },
        },
    },
    "oneplus-enchilada": {
        "branches": [
            "master",
            "v21.06",
        ],
        "branch_configs": {
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "oneplus-fajita": {
        "branches": [
            "master",
            "v21.06",
        ],
        "branch_configs": {
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "pine64-pinebookpro": {
        "branches": [
            "master",
        ],
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
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
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
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "pine64-rockpro64": {
        "branches": [
            "master",
        ],
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
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "samsung-a3": {
        "branches": [
            "master",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "samsung-a5": {
        "branches": [
            "master",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "samsung-a3lte": {
        "branches": [
            "v21.06",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "samsung-a3ulte": {
        "branches": [
            "v21.06",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "samsung-a5lte": {
        "branches": [
            "v21.06",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "samsung-a5ulte": {
        "branches": [
            "v21.06",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "samsung-serranove": {
        "branches": [
            "master",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "samsung-serranovelte": {
        "branches": [
            "v21.06",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "wileyfox-crackling": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "xiaomi-beryllium": {
        "branches": [
            "master",
        ],
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
        "branches": [
            "master",
            "v21.06",
        ],
        "branch_configs": {
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
    "xiaomi-wt88047": {
        "branches": [
            "master",
            "v21.06",
        ],
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
            "v21.06": {
                "date-start": "2021-06-20",  # Sunday
                "kernels": [
                    "mainline-modem-wt88047",
                ],
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
            },
        },
    },
}
