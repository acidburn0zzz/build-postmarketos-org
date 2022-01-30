# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import logging
import os
import shutil

import bpo.config.args


def pmos_ver(branch):
    """ Just like in Alpine, name the images from master branch "edge". """
    if branch == "master":
        return "edge"
    return branch


def branch_from_pmos_ver(pmos_ver):
    """ Invert of pmos_ver(). """
    if pmos_ver == "edge":
        return "master"
    return pmos_ver


def path(branch, device, ui, dir_name):
    """ :returns: absolute path to where the files for a certain image are
                  stored. """
    assert branch
    assert device
    assert ui
    assert dir_name
    return os.path.join(bpo.config.args.images_path,
                        pmos_ver(branch),
                        device,
                        ui,
                        dir_name)


def path_db_obj(obj):
    """ Shortcut for path() with a suitable database object (Log, Image). """
    return path(obj.branch, obj.device, obj.ui, obj.dir_name)


def url_db_obj(obj):
    """ Get the URL pointing to the files for a given image.
    :param obj: suitable database object (Log, Image)
    :returns: url like "https://images.postmarketos.org/bpo/edge/qemu-..."
    """
    return os.path.join(bpo.config.args.url_images,
                        pmos_ver(obj.branch),
                        obj.device,
                        obj.ui,
                        obj.dir_name)


def db_obj_from_path(path):
    """ Invert of path_db_obj().
        :param path: full path to an image directory, as returned by path()
                     (without trailing slash)
        :returns: bpo.db.Image object or None """
    relpath = os.path.relpath(path, bpo.config.args.images_path)
    pmos_ver, device, ui, dir_name = relpath.split("/")
    branch = branch_from_pmos_ver(pmos_ver)

    session = bpo.db.session()
    result = session.query(bpo.db.Image).\
        filter_by(branch=branch, device=device, ui=ui, dir_name=dir_name).all()
    if not len(result):
        logging.warning(f"{path}: couldn't find related image in database")
        return None
    return result[0]


def remove_old():
    """ Remove old images from the filesystem and database. """
    session = bpo.db.session()

    for img_cfg in bpo.images.config.get_images():
        branch = img_cfg["branch"]
        device = img_cfg["device"]
        ui = img_cfg["ui"]
        keep = img_cfg["keep"]

        session = bpo.db.session()
        result = session.query(bpo.db.Image).\
            filter_by(branch=branch, device=device, ui=ui,
                      status=bpo.db.ImageStatus.published).\
            order_by(bpo.db.Image.date.desc()).\
            all()

        for i in range(keep, len(result)):
            image = result[i]

            # Remove from disk
            path = path_db_obj(image)
            if os.path.exists(path):
                shutil.rmtree(path)
            else:
                logging.warning("Tried to delete old image path, but it"
                                f" doesn't exist: {path}")

            # Update database
            bpo.ui.log_image(image, "remove_old_image")
            session.delete(image)
            session.commit()
