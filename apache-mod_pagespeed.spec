#
# Conditional build:
%bcond_without	verbose		# verbose build (V=1)

# NOTE
# - http://code.google.com/p/modpagespeed/wiki/HowToBuild
# - http://wiki.mediatemple.net/w/(dv)_HOWTO:_Install_mod_pagespeed
# TODO
# - add unit tests running
# - c++ errors on 64bit/32bit gcc 4.5.1-4:
#   /usr/include/c++/4.5.1/bits/stl_map.h:87:5:   instantiated from here
#   /usr/include/c++/4.5.1/bits/stl_pair.h:77:11: error: ‘std::pair<_T1, _T2>::second’ has incomplete type
#   ./net/instaweb/util/public/cache_interface.h:28:7: error: forward declaration of ‘struct net_instaweb::SharedString’
#   make[1]: *** [out/Release/obj.target/mod_pagespeed_test/net/instaweb/util/cache_fetcher_test.o] Error 1
#   http://pastebin.com/Eu88BPSQ
# - sizeof(apr_int32_t) == sizeof(apr_int64_t) on 32bit (!?!):
#   third_party/apache/apr/src/strings/apr_snprintf.c: In function 'conv_os_thread_t':
#   third_party/apache/apr/src/strings/apr_snprintf.c:500:5: error: duplicate case value
#   third_party/apache/apr/src/strings/apr_snprintf.c:498:5: error: previously used here
#   third_party/apache/apr/src/strings/apr_snprintf.c: In function 'conv_os_thread_t_hex':
#   third_party/apache/apr/src/strings/apr_snprintf.c:671:5: error: duplicate case value
#   third_party/apache/apr/src/strings/apr_snprintf.c:669:5: error: previously used here
# - use only source for modpagespeed if system headers are used (remove copies from tarball)
# - possible sysdeps (uses release tags)
#  "serf_src": "http://serf.googlecode.com/svn/tags/0.3.1",
#  "apache_httpd_src": "http://svn.apache.org/repos/asf/httpd/httpd/tags/2.2.15",
#  "gflags_root": "http://google-gflags.googlecode.com/svn/tags/gflags-1.3/src",
#  "google_sparsehash_root": "http://google-sparsehash.googlecode.com/svn/tags/sparsehash-1.8.1/src",
#  protobuf_lite

%if "%{pld_release}" == "ac"
# add suffix, but allow ccache, etc in ~/.rpmmacros
%{expand:%%define	__cc	%(echo '%__cc' | sed -e 's,-gcc,-gcc4,')}
%{expand:%%define	__cxx	%(echo '%__cxx' | sed -e 's,-g++,-g++4,')}
%{expand:%%define	__cpp	%(echo '%__cpp' | sed -e 's,-gcc,-gcc4,')}
%endif

%define		mod_name	pagespeed
%define 	apxs		%{_sbindir}/apxs
Summary:	Apache module for rewriting web pages to reduce latency and bandwidth
Name:		apache-mod_%{mod_name}
Version:	0.10.22.4
Release:	0.7
License:	Apache v2.0
Group:		Networking/Daemons/HTTP
Source0:	modpagespeed-%{version}.tar.bz2
# Source0-md5:	9c9a8b091ee8d37253ee35878c3390e6
Source1:	get-source.sh
Patch0:		system-libs.patch
Patch1:		gcc-headers.patch
URL:		https://developers.google.com/speed/pagespeed/
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	dbus-glib-devel
BuildRequires:	fontconfig-devel
BuildRequires:	freetype-devel
BuildRequires:	glib2-devel
BuildRequires:	gtk+2-devel
BuildRequires:	ibus-devel >= 1.3.99.20110425
BuildRequires:	libgcrypt-devel
BuildRequires:	libgnome-keyring-devel
BuildRequires:	libjpeg-devel
BuildRequires:	libpng-devel
BuildRequires:	libselinux-devel
BuildRequires:	libstdc++-devel >= 5:4.1
BuildRequires:	opencv-devel
BuildRequires:	openssl-devel
BuildRequires:	python-devel >= 1:2.6
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	xorg-lib-libX11-devel
BuildRequires:	xorg-lib-libXext-devel
BuildRequires:	xorg-lib-libXi-devel
BuildRequires:	zlib-devel
# gcc4 might be installed, but not current __cc
%if "%(echo %{cc_version} | cut -d. -f1,2)" < "4.0"
BuildRequires:	__cc >= 4.0
%endif
Requires:	apache(modules-api) = %apache_modules_api
Requires:	apache-mod_authz_host
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
%setup -q -n modpagespeed
%patch0 -p1
%patch1 -p1

%build
# re-gen makefiles
cd src
CC="%{__cc}" \
CXX="%{__cxx}" \
%{__python} build/gyp_chromium --format=make build/all.gyp \
	-Dlinux_link_gsettings=1 \
	-Dlinux_link_gnome_keyring=1 \
	-Duse_gnome_keyring=1 \
	-Duse_openssl=1 \
	-Duse_system_apache_dev=1 \
	-Duse_system_libjpeg=1 \
	-Duse_system_libpng=1 \
	-Duse_system_opencv=1 \
	-Duse_system_zlib=1 \
	-Duse_ibus=1 \
	%{nil}

cd ..

# makefile wrapper so we could just invoke "make" from shell
cat > Makefile <<'EOF'
default:
	$(MAKE) -C src \
	BUILDTYPE=%{!?debug:Release}%{?debug:Debug} \
	%{?with_verbose:V=1} \
	CC="%{__cc}" \
	CXX="%{__cxx}" \
	CC.host="%{__cc}" \
	CXX.host="%{__cxx}" \
	LINK.host="%{__cxx}" \
	CFLAGS="%{rpmcflags} %{rpmcppflags}" \
	CXXFLAGS="%{rpmcxxflags} %{rpmcppflags}" \
	$(MAKEFLAGS) \
EOF
%{__make}

# install.gyp needs fixing, not to install ap24.so, for now duplicate
ln -f src/out/Release/libmod_pagespeed{,_ap24}.so

%install
rm -rf $RPM_BUILD_ROOT
%{__make} -j1 -C src/install staging \
	HOSTNAME=localhost \
	APACHE_ROOT=%{_pkgrootdir} \
	APACHE_MODULES=%{_pkglibdir} \
	APACHE_DOC_ROOT=%{htdocsdir} \
	MOD_PAGESPEED_FILE_ROOT=%{cachedir} \
	STAGING_DIR=staging

cd src/install/staging
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir}}
install -p mod_%{mod_name}.so $RPM_BUILD_ROOT%{_pkglibdir}
install -d $RPM_BUILD_ROOT%{cachedir}/{cache,files}
cat > $RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf <<EOF
LoadModule %{mod_name}_module	modules/mod_%{mod_name}.so

$(cat pagespeed.conf)
EOF

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
%attr(755,root,root) %{_pkglibdir}/mod_%{mod_name}.so

%dir %attr(710,root,http) %{cachedir}
%dir %attr(770,root,http) %{cachedir}/cache
%dir %attr(770,root,http) %{cachedir}/files
