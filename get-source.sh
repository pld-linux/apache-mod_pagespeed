#!/bin/sh
# Usage:
# ./get-source.sh
# Author: Elan Ruusamäe <glen@pld-linux.org>

pkg=modpagespeed
baseurl=http://modpagespeed.googlecode.com/svn
# leave empty to use latest tag, or "trunk" for trunk
version=
spec=apache-mod_pagespeed.spec

# abort on errors
set -e
# work in package dir
dir=$(dirname "$0")
cd "$dir"

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

# gclient needs python 2.6
if python -c "import sys; sys.exit(sys.version[:3] > '2.6')"; then
	echo >&2 "Need python >= 2.6 for gclient"
	exit 1
fi

#wget -c https://chrome-browser.googlecode.com/svn-history/r37527/trunk/tools/depot_tools.tar.gz
wget -c http://distfiles.pld-linux.org/by-md5/5/6/56a3c406fcb645eaaa608a257f06a90d/depot_tools.tar.gz
test -d depot_tools || {
	tar xzf depot_tools.tar.gz
	cd depot_tools
	svn upgrade
	cd ..
}

install -d $pkg
cd $pkg
# force update
rm -f .gclient

../depot_tools/gclient config $svnurl
../depot_tools/gclient sync

# Populate the LASTCHANGE file template as we will not include VCS info in tarball
(cd src/build && svnversion > LASTCHANGE.in)
cd ..

tar -cjf $tarball --exclude-vcs $pkg
../md5 $spec
../dropin $tarball &
