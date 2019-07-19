from flask import Blueprint, request, abort
from bpo.helpers.headerauth import header_auth
import bpo.api
import bpo.config.args
import bpo.db
import bpo.helpers.repo
import bpo.helpers.queue

blueprint = bpo.api.blueprint


@blueprint.route("/api/job-callback/get-repo-missing", methods=["POST"])
@header_auth("X-BPO-Token", "job_callback")
def job_callback_get_repo_missing():
    # FIXME: split up in multiple functions
    payload = request.get_json()
    session = bpo.db.session()

    # Get and validate arch
    if "X-BPO-Arch" not in request.headers:
        raise ValueError("missing X-BPO-Arch header!")
    arch = request.headers["X-BPO-Arch"]
    if arch not in bpo.config.const.architectures:
        raise ValueError("invalid X-BPO-Arch: " + arch)

    # Get and validate push_id
    if "X-BPO-Push-Id" not in request.headers:
        raise ValueError("missing X-BPO-Push-Id header!")
    push_id = request.headers["X-BPO-Push-Id"]
    result = session.query(bpo.db.Push).filter_by(id=int(push_id)).all()
    if not len(result):
        raise ValueError("invalid X-BPO-Push-Id: " + push_id)
    push = result[0]

    # Build dict of missing postmarketOS packages (DB objects)
    packages = {}
    for package_payload in payload:
        pkgname = package_payload["pkgname"]
        version = package_payload["version"]
        repo = package_payload["repo"]
        
        if pkgname in packages:
            raise ValueError("pkgname found twice in payload: " + pkgname)

        # Find existing db entry if possible (update or insert logic)
        result = session.query(bpo.db.Package).filter_by(arch=arch,
                                                         pkgname=pkgname).all()
        if len(result):
            package = result[0]
            package.version = version
            package.repo = repo
        else:
            package = bpo.db.Package(arch=arch, pkgname=pkgname,
                                     version=version, repo=repo)
        session.merge(package)
        packages[pkgname] = package

    # Add dependencies
    for package_payload in payload:
        # Build list of dependencies (DB objects)
        depends_payload = package_payload["depends"]
        depends = []
        for pkgname in depends_payload:
            depend = None
            if pkgname in packages:
                # Find dependency in payload
                depend = packages[pkgname]
            else:
                # Find dependency in DB
                result = session.query(bpo.db.Package).\
                         filter_by(arch=arch,pkgname=pkgname).all()
                if len(result):
                    depend = result[0]

            # Add dependency if we found it (otherwise it is in Alpine)
            if depend:
                depends.append(depend)
        
        # Add dependencies to package
        pkgname = package_payload["pkgname"]
        packages[pkgname].depends = depends

    # Insert into database
    log = bpo.db.Log(action="job_callback_get_repo_missing", payload=payload,
                     push=push, arch=arch)
    session.add(log)
    session.commit()

    # TODO:
    # build the queue and start the next build
    
    return "warming up build servers..."
