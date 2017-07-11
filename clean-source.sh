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

# some more unneeded files for build
rm -r net/instaweb/rewriter/testdata
rm -r third_party/aprutil/gen
#rm -r third_party/chromium/src/base/test
rm -r third_party/chromium/src/net
#rm -r third_party/gflags/src/windows
#rm -r third_party/giflib/windows
#rm -r third_party/google-sparsehash/src/windows
#rm -r third_party/libjpeg_turbo/src/{mac,win}
#rm -r third_party/protobuf/java
#rm -r third_party/protobuf/src/google/protobuf/testdata
#rm -r third_party/zlib/{contrib,examples,old,doc}
#rm -r third_party/zlib/{win32,msdos,nintendods,watcom,qnx,amiga}

find -type d -name testdata | xargs rm -r
find -type d -name mac | xargs rm -r
#find -type d -name win | xargs rm -r
#find -depth -type d -name test | xargs rm -rv
#find third_party -type d -name android | xargs rm -r

find -type f -name '*_test.cc' | xargs rm
find -type f -name '*_unittest.cc' | xargs rm

# not using gn nor ninja
#find -name BUILD.gn | xargs rm

# cleanup empty dirs
find -type d '!' -name '.' -print0 | sort -zr | xargs -0 rmdir --ignore-fail-on-non-empty

# build/linux and third_party/chromium/src/build/linux are same dirs,
# the later is not used by build system, but used by tarball packaging
#rm -r third_party/chromium/src/build/linux
#third_party/chromium/src/build/linux
