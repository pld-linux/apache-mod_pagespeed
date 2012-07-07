#!/bin/sh
# Usage:
# ./get-source.sh
# Author: Elan Ruusamäe <glen@pld-linux.org>

pkg=modpagespeed
baseurl=http://modpagespeed.googlecode.com/svn
# leave empty to use latest tag, or "trunk" for trunk
version=
spec=apache-mod_pagespeed.spec
force=0

# abort on errors
set -e
# work in package dir
dir=$(dirname "$0")
cd "$dir"

if [[ "$1" = *force ]]; then
	force=1
	shift
fi

if [ "$1" ]; then
	version=$1
fi

if [ -z "$version" ]; then
	echo "Looking for latest version..."
	version=$(svn ls $baseurl/tags/ | sort -V | tail -n1)
	version=${version%/}
fi

if [ "$version" = "trunk" ]; then
	echo "Using trunk"
	svnurl=$baseurl/trunk/src
	tarball=$pkg-$(date +%Y%m%d).tar.bz2
else
	echo "Version: $version"
	svnurl=$baseurl/tags/$version/src
	tarball=$pkg-$version.tar.bz2
fi

if [ -f $tarball -a $force != 1 ]; then
	echo "Tarball $tarball already exists"
	exit 0
fi

# gclient needs python 2.6
if python -c "import sys; sys.exit(sys.version[:3] > '2.6')"; then
	echo >&2 "Need python >= 2.6 for gclient"
	exit 1
fi

# http://www.chromium.org/developers/how-tos/install-depot-tools
test -d depot_tools || {
	wget -c https://src.chromium.org/svn/trunk/tools/depot_tools.zip
	unzip -qq depot_tools.zip
#	cd depot_tools
#	svn upgrade
#	cd ..
	chmod a+x depot_tools/gclient depot_tools/update_depot_tools
}

topdir=${PWD:-($pwd)}
gclient=$topdir/gclient.conf
install -d $pkg
cd $pkg

if [ ! -f $gclient ]; then
	# create initial config that can be later modified
	../depot_tools/gclient config $svnurl --gclientfile=$gclient
fi

cp $gclient .gclient

# emulate gclient config, preserving our deps
sed -i -re '/"url"/ s,"http[^"]+","'$svnurl'",' .gclient

../depot_tools/gclient sync --nohooks -v

# Populate the LASTCHANGE file template as we will not include VCS info in tarball
(cd src/build && svnversion > LASTCHANGE.in)
cd ..

tar -cjf $tarball --exclude-vcs $pkg
../md5 $spec
../dropin $tarball &
