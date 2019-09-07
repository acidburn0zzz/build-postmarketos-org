# bpo (build.postmarketos.org)

[Work in progress.](https://postmarketos.org/blog/2019/06/23/two-years/#sourcehut-srht)

## FAQ

### Why are there no subdirs in the binary repository?

We have plenty of subdirs in pmaports.git (cross, device, firmware, hybris, kde, maemo, main, ...). For postmarketOS, it makes a lot of sense to keep the packages sorted that way. But if we turn each of them into a subdir in the binary repository, we would need to add a separate URL for them to the repositories list (/etc/apk/repositories) as well, and apk and pmbootstrap would need to download an APKINDEX for each of them. This makes the update process slower (especially for pmbootstrap, which may download these index files for multiple architectures, depending on what you are doing). So we just use one APKINDEX (per architecture and branch) without the additional subdir.
