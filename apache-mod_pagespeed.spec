#
# Conditional build:
%bcond_without	verbose		# verbose build (V=1)

# NOTE
# - relase notes: https://developers.google.com/speed/pagespeed/module/release_notes
# - http://code.google.com/p/modpagespeed/wiki/HowToBuild
# - http://wiki.mediatemple.net/w/(dv)_HOWTO:_Install_mod_pagespeed
# TODO
# - run unit tests
# third_party libraries:
# - apr - using system apr package
# - aprutil - using system apr-util, but from this repo modified apr_memcache2.c
# - gflags - system package may work
# - giflib - 4.1.6, no local modifications
# - google-sparsehash
# - httpd, httpd24 - using system apache-devel
# - icu - using system icu
# - jsoncpp - no local changes
# - libjpeg_turbo - 1.2.80 with chromium changes (but system lib should be fine)
# - libpng - no local changes
# - libwebp - 0.4.0, irrelevant local changes
# - optipng - 0.7.4, local changes: only the opngreduc component of optipng is included.
# - protobuf - should be possible to use full protobuf (not lite) to gain same functionality
# - re2 - should be possible to use system re2
# - serf - 0.7.2 bunch of google fixes
# - zlib - 1.2.5, no local changes
#
# third_party/chromium/src/base/third_party:
# - nspr - should be possible to use system lib
# - dmg_fp
# - dynamic_annotations
# - icu - not icu lib, but two files only
# - valgrind
#
# could be possible to use system libs, not packaged in pld:
# - base64
# - chromium
# - chromium_deps
# - css_parser
# - domain_registry_provider
# - instaweb
# - mod_spdy
# - modp_b64
# - rdestl

%define		mod_name	pagespeed
%define		apxs		%{_sbindir}/apxs
Summary:	Apache module for rewriting web pages to reduce latency and bandwidth
Name:		apache-mod_%{mod_name}
# beta: 1.9.32.x-beta
# stable: 1.8.31.x
Version:	1.8.31.6
Release:	1
License:	Apache v2.0
Group:		Networking/Daemons/HTTP
Source0:	modpagespeed-%{version}.tar.xz
# Source0-md5:	ab144d1d524ce60db44c4dfd6f3f8ef3
Source1:	get-source.sh
Source2:	gclient.conf
Patch0:		system-libs.patch
Patch2:		bug-632.patch
Patch4:		no-dev-stdout.patch
Patch5:		apache24-config.patch
URL:		https://developers.google.com/speed/pagespeed/module
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	bash
BuildRequires:	glib2-devel
BuildRequires:	gperf
BuildRequires:	libicu-devel
BuildRequires:	libselinux-devel
BuildRequires:	libstdc++-devel >= 5:4.1
BuildRequires:	opencv-devel >= 2.3.1
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	python-devel >= 1:2.6
BuildRequires:	yasm
# This version of gyp is new enough that it knows to use make for Linux 3.x
# and FreeBSD, but old enough that 'type': 'settings' works and
# LINKER_SUPPORTS_ICF hasn't been removed yet.
BuildRequires:	python-gyp >= 0.1-0.svn1602.1
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	tar >= 1:1.22
BuildRequires:	util-linux
BuildRequires:	xz
BuildRequires:	zlib-devel
Requires:	apache(modules-api) = %apache_modules_api
Requires:	apache-mod_authz_host
Requires:	apache-mod_headers
Suggests:	apache-mod_deflate
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		_pkgrootdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define		_sysconfdir	%{_pkgrootdir}/conf.d
%define		htdocsdir	%(%{apxs} -q htdocsdir 2>/dev/null)
%define		cachedir	%(%{apxs} -q proxycachedir 2>/dev/null)/mod_%{mod_name}

# disable strip examples, http://lists.pld-linux.org/mailman/pipermail/pld-devel-en/2015-January/024223.html
%define		_noautostrip	.*%{_examplesdir}/.*

%description
mod_pagespeed automates the application of those rules in an Apache
server. HTML, CSS, JavaScript, and images are changed dynamically
during the web serving process, so that the best practices recommended
by Page Speed can be used without having to change the way the web
site is maintained.

%prep
%setup -q -n modpagespeed-%{version}
%patch0 -p2
%patch2 -p1
%patch4 -p1
%patch5 -p1

rm -r third_party/icu/source
rm -r third_party/icu/genfiles
install -d third_party/icu/source/{common,i18n}
ln -s %{_includedir}/unicode third_party/icu/source/i18n/unicode
ln -s %{_includedir}/unicode third_party/icu/source/common/unicode

%build
# re-gen makefiles
CC="%{__cc}" \
CXX="%{__cxx}" \
%{__python} build/gyp_chromium \
	--format=make \
	--depth=. \
	build/all.gyp \
	-Duse_openssl=1 \
	-Duse_system_apache_dev=1 \
	-Duse_system_icu=1 \
	-Duse_system_libjpeg=1 \
	-Duse_system_libpng=1 \
	-Duse_system_opencv=1 \
	-Duse_system_openssl=1 \
	-Duse_system_yasm=1 \
	-Duse_system_zlib=1 \
	-Dsystem_include_path_apr=%{_includedir}/apr \
	-Dsystem_include_path_aprutil=%{_includedir}/apr-util \
	-Dsystem_include_path_httpd=%{_includedir}/apache \
	%{nil}

%{__make} mod_pagespeed js_minify css_minify_main \
	BUILDTYPE=%{!?debug:Release}%{?debug:Debug} \
	%{?with_verbose:V=1} \
	CC="%{__cc}" \
	CXX="%{__cxx}" \
	CC.host="%{__cc}" \
	CXX.host="%{__cxx}" \
	LINK.host="%{__cxx}" \
	CFLAGS="%{rpmcflags} %{rpmcppflags}" \
	CXXFLAGS="%{rpmcxxflags} %{rpmcppflags}" \
	%{nil}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir},%{_bindir},%{cachedir}}

%{__make} -j1 -C install staging_except_module \
	APACHE_ROOT=%{_pkgrootdir} \
	APACHE_MODULES=modules \
	APACHE_DOC_ROOT=%{htdocsdir} \
	MOD_PAGESPEED_CACHE=%{cachedir} \
	MOD_PAGESPEED_STATS_LOG=/var/log/httpd/mod_pagespeed_stats.log \
	STAGING_DIR=staging

out=out/%{!?debug:Release}%{?debug:Debug}
install -p $out/libmod_%{mod_name}.so $RPM_BUILD_ROOT%{_pkglibdir}/mod_%{mod_name}.so
install -p $out/js_minify $RPM_BUILD_ROOT%{_bindir}/pagespeed_js_minify
install -p $out/css_minify_main $RPM_BUILD_ROOT%{_bindir}/pagespeed_css_minify

cd install/staging
cat > $RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf <<EOF
LoadModule %{mod_name}_module	modules/mod_%{mod_name}.so

$(cat pagespeed.conf)
EOF

cp -p pagespeed_libraries.conf $RPM_BUILD_ROOT%{_sysconfdir}/91_mod_%{mod_name}_libraries.conf

install -d $RPM_BUILD_ROOT%{_examplesdir}/%{name}-%{version}
cp -a mod_pagespeed_example/* $RPM_BUILD_ROOT%{_examplesdir}/%{name}-%{version}

%clean
rm -rf $RPM_BUILD_ROOT

%post
%service -q httpd restart

%postun
if [ "$1" = "0" ]; then
	%service -q httpd restart
fi

%files
%defattr(644,root,root,755)
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/*_mod_%{mod_name}.conf
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/*_mod_%{mod_name}_libraries.conf
%attr(755,root,root) %{_bindir}/pagespeed_css_minify
%attr(755,root,root) %{_bindir}/pagespeed_js_minify
%attr(755,root,root) %{_pkglibdir}/mod_%{mod_name}.so
%{_examplesdir}/%{name}-%{version}
%dir %attr(770,root,http) %{cachedir}
