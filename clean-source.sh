#!/bin/sh
set -xe

# There are directories we want to strip, but that are unnecessarily required by the build-system
# So we drop everything but the gyp/gypi files
almost_strip_dirs() {
	for dir in "$@"; do
		find $dir -depth -mindepth 1 '!' '(' -name '*.gyp' -o -name '*.gypi' ')' -print -delete || :
	done
}

export LC_ALL=C

# clean sources, but preserve .gyp, .gypi
almost_strip_dirs \
	third_party/apr/ \
	third_party/httpd/ \
	third_party/httpd24/ \
	third_party/instaweb/ \
	third_party/openssl/ \

# some more unneeded files for build
rm -r third_party/chromium/src/net
rm -r third_party/chromium/src/chrome
rm -r net/instaweb/rewriter/testdata

# build/linux and third_party/chromium/src/build/linux are same dirs, the latter is not usedc
#rm -r third_party/chromium/src/build/linux
#third_party/chromium/src/build/linux
