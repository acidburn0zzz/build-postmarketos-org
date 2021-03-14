# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import glob
import os

import bpo.helpers.job
import bpo.images


def get_entries(path, reverse=False):
    """ Get a sorted list of entries (files, directories) in a given path.
        :param reverse: order in reverse
        :returns: list of entries """
    ret = []
    for entry in list(sorted(glob.glob(f"{path}/*"), reverse=reverse)):
        ret.append(os.path.basename(entry))
    return ret


def get_file_size_human(path):
    """ Get human readable size of path """
    size = os.path.getsize(path)
    for unit in ["", "Ki", "Mi", "Gi"]:
        if abs(size) < 1024.0 or unit == "Gi":
            break
        size /= 1024.0
    return f"{size} {unit}B"


def write_index(path, template, **context):
    """ Write an index.html in the specified path based on the supplied
        template
        :param path: full path to the directory for the index.html
        :param template: template filename
        :param context: arguments for the template """
    # Title
    relpath = os.path.relpath(path, bpo.config.args.images_path)
    title = "postmarketOS // Official Images"
    if relpath != ".":
        title = f"{relpath} - {title}"
    context["title"] = title

    # Navigation with format: [(url1, dirname1), (url2, dirname2), ...]
    navigation = [(bpo.config.args.url_images, "bpo")]
    if relpath != ".":
        relpath_split = relpath.split("/")
        for i, dirname in enumerate(relpath_split):
            url = "../" * (len(relpath_split) - i - 1)
            navigation.append([url, dirname])
    context["navigation"] = navigation

    context["bpo_url"] = bpo.config.const.url
    context["img_url"] = bpo.config.args.url_images

    if "entries" not in context:
        context["entries"] = get_entries(path)

    template = bpo.ui.env.get_template(f"images/{template}")
    html = template.render(**context)
    with open(os.path.join(path, "index.html"), "w") as handle:
        handle.write(html)


def write_index_file_list(path, template):
    """ Write the index.html for the file list of one build. Each file in the
        directory gets metadata attached as it gets passed to the template
        (file size, checksums).
        :param path: full path to the directory for the index.html
        :param template: template filename """
    image = bpo.images.db_obj_from_path(path)
    job_link = bpo.helpers.job.get_link(image.job_id)
    codename = os.path.basename(os.path.dirname(os.path.dirname(path[:-1])))

    # Add metadata to each entry
    # entries = [{name: "20210612-0119-postmarketO...line-modem.img.xz",
    #             sha256: "24892374982374...",
    #             sha512: "5464256432354...",
    #             size: "1337 MiB"},
    #             {...}, ...]
    entries = []
    for name in get_entries(path):
        if name.endswith(".sha256") or name.endswith(".sha512"):
            continue

        entry = {"name": name,
                 "size": get_file_size_human(f"{path}/{name}")}

        for checksum in ["sha256", "sha512"]:
            checksum_path = f"{path}/{name}.{checksum}"
            if not os.path.exists(checksum_path):
                continue
            with open(checksum_path) as handle:
                entry[checksum] = handle.read().strip().split(' ')[0]

        entries.append(entry)

    write_index(path, template, entries=entries, job_link=job_link,
                codename=codename)


def write_index_all():
    """ For each directory in the images dir (recursively), write the HTML
        files. The files are always overwritten. """

    for path in glob.iglob(f"{bpo.config.args.images_path}/**/",
                           recursive=True):
        relpath = os.path.relpath(path, bpo.config.args.images_path)

        if relpath == ".":
            entries = get_entries(path, True)
            if "edge" in entries:
                entries.remove("edge")
                entries = ["edge"] + entries
            write_index(path, "01_releases.html", entries=entries)
        elif relpath.count('/') == 0:
            write_index(path, "02_devices.html")
        elif relpath.count('/') == 1:
            write_index(path, "03_userinterfaces.html")
        elif relpath.count('/') == 2:
            write_index(path, "04_dates.html")
        else:
            write_index_file_list(path, "05_files.html")
