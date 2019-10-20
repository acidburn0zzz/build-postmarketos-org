# bpo (build.postmarketos.org)

[Work in progress.](https://postmarketos.org/blog/2019/06/23/two-years/#sourcehut-srht)

## Installation

Requires python 3.5 or higher.

```
$ git clone https://gitlab.com/postmarketOS/build.postmarketos.org
$ cd build.postmarketos.org
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

All commands below are intended to be executed in this venv.

## Running
## With local job service

```
$ ./bpo_local.sh
```

### With sourcehut job service

After creating a [sr.ht](https://meta.sr.ht/register) account and a dedicated [personal access oauth token](https://meta.sr.ht/oauth):

```
$ cp bpo_sourcehut.example.sh bpo_sourcehut.sh
$ $EDITOR bpo_sourcehut.sh # adjust USER
$ ./bpo_sourcehut.sh
```

Running bpo for the first time will generate the `push_hook_gitlab` and `job_callback` tokens, and display them once (and never again, only a hash is stored). Copy the tokens and set them up as push hook token in gitlab, and create a secret in sourcehut for the job_callback token.

Then edit the token file and add `sourcehut` (personal access oauth token) and `job_callback_secret` (the secret ID that sourcehut generated for the job_callback token). Finally start the bpo server again.

```
$ EDITOR .tokens.cfg
$ ./bpo_sourcehut.sh
```


### Running tests

```
$ pip install pytest pytest-cov pytest-timeout
$ .ci/pytest.sh
```

If a test is just hanging, hit ^C and look at the very top of the output. The local job is running in a different thread, so if there's nothing useful in the trace, open _html_out/index.html and check the latest log files (which are linked there).

## Network Architecture

### Job service

Either [sourcehut](https://sourcehut.org/) or "local" for local development and automated testing. The job service runs a shell script to perform a small task, such as building a package or signing an index. Its purpose is to provide a safe environment for running this task (where we feel comfortable placing our signing keys), and to show a pretty log of the shell script (so we can easily analyze what went wrong during a build). The result gets sent back to the bpo server. The job services have access to the signing key for the packages and APKINDEX that end up in the final repository, the bpo server does not.

### Bpo server

Runs the code in this git repository to orchestrate the package builds and index signing with jobs running on a job service. It should also provide a web interface, that shows the state of the repository, and links to the build logs of the job service.

### Package mirror

The URL that one can add to their /etc/apk/repositories file, to make apk download packages from there.

## Repositories

Instead of immediately publishing each single package after it has been built, we wait until all packages from the last "push" (as in "git push") have been built. One of such pushes can consist of multiple commits, and each commit may change zero or more packages. The idea is, that we don't publish a half-baked update, where for example, just half the packages of a framework are updated and the other half isn't.

### WIP repo

This repository is hosted by (a separate webserver running on) the bpo server and the build jobs running on the job service use it in order to build packages from the same push that depend on each other. After each package is built, it gets immediately added to the WIP repository. The WIP repository is indexed and signed by the server that runs the bpo code, with the WIP repository key, that is not the same as the final repository key.

### Symlink repo

Once all packages of a push are built, the bpo server creates a symlink repository. As the name suggests, this consists of symlinks to the updated packages from the WIP repo, and the existing packages (that were not updated or deleted) from the final repo. The symlink repo is only used internally in the bpo code, and not made available to the build jobs. It gets indexed (but not signed!) by the bpo server. The generated APKINDEX then gets downloaded by a job service, signed, and uploaded back to the bpo server.

With this architecture, we don't need to keep the signing key for the final repository on the bpo server, and we don't need to download the entire repository to a job running at a job service either.

### Final repo

After the index of the symlink repo is signed, the final repo gets updated to reflect what is currently in the symlink repo. When that is done, it gets published to the package mirror with rsync.

## FAQ

### Why are there no subdirs in the binary repository?

We have plenty of subdirs in pmaports.git (cross, device, firmware, hybris, kde, maemo, main, ...). For postmarketOS, it makes a lot of sense to keep the packages sorted that way. But if we turn each of them into a subdir in the binary repository, we would need to add a separate URL for them to the repositories list (/etc/apk/repositories) as well, and apk and pmbootstrap would need to download an APKINDEX for each of them. This makes the update process slower (especially for pmbootstrap, which may download these index files for multiple architectures, depending on what you are doing). So we just use one APKINDEX (per architecture and branch) without the additional subdir.

### What to do if something went wrong and the BPO server missed that a sourcehut job failed or completed?

* Run the pmaports.git trigger from gitlab again, then the bpo server will re-calculate the missing packages and update the status of the jobs that are supposed to be running right now.
* If that does not help, run the build.postmarketos.org.git trigger again from gitlab, to restart the bpo server.

### How to run the flake8 check locally?

Run it once:
```
$ pip install flake8
$ .ci/flake8.sh
```

Run it before every git commit (recommended):
```
$ ln -s .ci/flake8.sh .git/hooks/pre-commit
```
