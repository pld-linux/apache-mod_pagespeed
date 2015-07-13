#!/bin/sh
# Usage:
# ./get-source.sh
# Author: Elan Ruusamäe <glen@pld-linux.org>
#
# To see release notes, see this page:
# https://developers.google.com/speed/docs/mod_pagespeed/release_notes
# Bulding from source notes:
# https://developers.google.com/speed/pagespeed/module/build_mod_pagespeed_from_source

package=modpagespeed
repo_url=https://github.com/pagespeed/mod_pagespeed.git
# leave empty to use latest tag, or "trunk" for trunk
# specific version, "latest-stable" or "master" (bleeding edge version)
version=latest-stable
spec=apache-mod_pagespeed.spec
# depth to clone, do not use this as ./build/lastchange.sh uses 'git rev-list --all --count' to count revision
depth=
force=0

# abort on errors
set -e
# work in package dir
dir=$(readlink -f $(dirname "$0"))
cd "$dir"

if [[ "$1" = *force ]]; then
	force=1
	shift
fi

if [ "$1" ]; then
	version=$1
fi

export GIT_DIR=$package/src/.git

# refs to fetch: master and latest-stable
refs="refs/heads/master:refs/remotes/origin/master refs/heads/latest-stable:refs/remotes/origin/latest-stable"

if [ ! -d $GIT_DIR ]; then
	install -d $GIT_DIR
#	git init --bare
	git init
	git remote add origin $repo_url
	git fetch ${depth:+--depth $depth} origin $refs
else
	git fetch origin $refs
fi
unset GIT_DIR

cd $package/src
git checkout $version

version=$(git describe --tags)
echo "Version: $version"

release_dir=$package-$version
tarball=$dir/$release_dir.tar.xz

if [ -f $tarball -a $force != 1 ]; then
	echo "Tarball $tarball already exists"
	exit 0
fi

# gclient needs python 2.6
if python -c "import sys; sys.exit(sys.version[:3] > '2.6')"; then
	echo >&2 "Need python >= 2.6 for gclient"
	exit 1
fi

gclient=$(which gclient 2>/dev/null)
if [ -z "$gclient" ]; then
	# http://www.chromium.org/developers/how-tos/install-depot-tools
	test -d depot_tools || {
		# could also checkout:
		# svn co http://src.chromium.org/svn/trunk/tools/depot_tools
		wget -c https://src.chromium.org/svn/trunk/tools/depot_tools.zip
		unzip -qq depot_tools.zip
		chmod a+x depot_tools/gclient depot_tools/update_depot_tools
	}
	gclient=$dir/depot_tools/gclient
fi

gclientfile=$dir/gclient.conf
cd $dir/$package

if [ ! -f $gclientfile ]; then
	# create initial config that can be later modified
	$gclient config $repo_url --gclientfile=$gclientfile --unmanaged --name=src
fi

cp -p $gclientfile .gclient

# emulate gclient config, preserving our deps
sed -i -re '/"url"/ s,"http[^"]+","'$repo_url'",' .gclient

$gclient sync --nohooks -v

cd src

sh -x $dir/clean-source.sh

# Populate the LASTCHANGE file template as we will not include VCS info in tarball
./build/lastchange.sh . -o LASTCHANGE.in

cd ../..

XZ_OPT=-e9 \
tar --transform="s:^$package/src:$release_dir:" \
	-caf $tarball --exclude-vcs $package/src

../md5 $spec
../dropin $tarball &
