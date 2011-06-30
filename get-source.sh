#!/bin/sh
# Usage:
# ./get-source.sh
# Author: Elan Ruusamäe <glen@pld-linux.org>

pkg=modpagespeed
baseurl=http://modpagespeed.googlecode.com/svn
# leave empty to use trunk
version=0.9.17.7
spec=apache-mod_pagespeed.spec

# abort on errors
set -e

# work in package dir
dir=$(dirname "$0")
cd "$dir"

if [ -n "$version" ]; then
	svnurl=$baseurl/tags/$version/src
	tarball=$pkg-$version.tar.bz2
else
	svnurl=$baseurl/trunk/src
	tarball=$pkg-$(date +%Y%m%d).tar.bz2
fi

wget -c http://src.chromium.org/svn/trunk/tools/depot_tools.tar.gz
test -d depot_tools || tar xzf depot_tools.tar.gz

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
