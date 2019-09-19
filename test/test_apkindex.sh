#!/bin/sh -e
DIR="$(dirname "$0")"

# prepare tmpdir with extracted tools
cd "$DIR/.."
[ -d _index_tmp ] && rm -rf _index_tmp
mkdir -p _index_tmp
cd _index_tmp
tar -xf ../tools/abuild-sign-noinclude-*.apk
tar -xf ../tools/apk-tools-static-*.apk
export PATH="$PWD/usr/bin:$PWD/sbin:$PATH"

# index
cd ../_repo_staging/master/x86_64
apk.static -q index --output APKINDEX.tar.gz_ --rewrite-arch x86_64 *.apk

abuild-sign.noinclude _APKINDEX.tar.gz APKINDEX.tar.gz

rm _APKINDEX.tar.gz

# apk.static index -h || true
# abuild-tar.static || true
# abuild-sign.noinclude -h || true
echo "done!"
