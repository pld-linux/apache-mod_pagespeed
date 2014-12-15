#
# Conditional build:
%bcond_without	verbose		# verbose build (V=1)

# NOTE
# - relase notes: https://developers.google.com/speed/pagespeed/module/release_notes
# - http://code.google.com/p/modpagespeed/wiki/HowToBuild
# - http://wiki.mediatemple.net/w/(dv)_HOWTO:_Install_mod_pagespeed
# TODO
# - add unit tests running
# - possible sysdeps (uses release tags)
#  "serf_src": "http://serf.googlecode.com/svn/tags/0.3.1",
#  "gflags_root": "http://google-gflags.googlecode.com/svn/tags/gflags-1.3/src",
#  "google_sparsehash_root": "http://google-sparsehash.googlecode.com/svn/tags/sparsehash-1.8.1/src",
#  protobuf_lite

%define		mod_name	pagespeed
%define		apxs		%{_sbindir}/apxs
Summary:	Apache module for rewriting web pages to reduce latency and bandwidth
Name:		apache-mod_%{mod_name}
Version:	1.5.27.2
Release:	3
License:	Apache v2.0
Group:		Networking/Daemons/HTTP
Source0:	modpagespeed-%{version}.tar.xz
# Source0-md5:	fa8d6a80fc4ca7f929910fa4eeb4a941
Source1:	get-source.sh
Source2:	gclient.conf
Patch0:		system-libs.patch
Patch1:		gcc-headers.patch
Patch2:		bug-632.patch
Patch3:		opencv.patch
Patch4:		no-dev-stdout.patch
URL:		https://developers.google.com/speed/pagespeed/module
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	glib2-devel
BuildRequires:	gperf
BuildRequires:	libselinux-devel
BuildRequires:	libstdc++-devel >= 5:4.1
BuildRequires:	opencv-devel >= 2.3.1
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	python-devel >= 1:2.6
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

%description
mod_pagespeed automates the application of those rules in an Apache
server. HTML, CSS, JavaScript, and images are changed dynamically
during the web serving process, so that the best practices recommended
by Page Speed can be used without having to change the way the web
site is maintained.

%prep
%setup -q -n modpagespeed-%{version}
%patch0 -p2
%patch1 -p2
%patch2 -p1
%patch3 -p3
%patch4 -p1

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
	-Duse_system_libjpeg=1 \
	-Duse_system_libpng=1 \
	-Duse_system_opencv=1 \
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
