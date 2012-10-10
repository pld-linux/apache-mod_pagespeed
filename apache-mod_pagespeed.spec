#
# Conditional build:
%bcond_without	verbose		# verbose build (V=1)

# NOTE
# - http://code.google.com/p/modpagespeed/wiki/HowToBuild
# - http://wiki.mediatemple.net/w/(dv)_HOWTO:_Install_mod_pagespeed
# TODO
# - add unit tests running
# - use only source for modpagespeed if system headers are used (remove copies from tarball)
# - possible sysdeps (uses release tags)
#  "serf_src": "http://serf.googlecode.com/svn/tags/0.3.1",
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
Version:	0.10.22.7
Release:	1
License:	Apache v2.0
Group:		Networking/Daemons/HTTP
Source0:	modpagespeed-%{version}.tar.xz
# Source0-md5:	1c67625812d18899ce6a47da069c6043
Source1:	get-source.sh
Patch0:		system-libs.patch
Patch1:		gcc-headers.patch
URL:		https://developers.google.com/speed/pagespeed/
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	glib2-devel
BuildRequires:	gperf
BuildRequires:	libjpeg-devel
BuildRequires:	libselinux-devel
BuildRequires:	libstdc++-devel >= 5:4.1
BuildRequires:	opencv-devel >= 2.3.1
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	python-devel >= 1:2.6
# This version of gyp is new enough that it knows to use make for Linux 3.x
# and FreeBSD, but old enough that 'type': 'settings' works and
# LINKER_SUPPORTS_ICF hasn't been removed yet.
BuildRequires:	python-gyp >= 1-1175
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	tar >= 1:1.22
BuildRequires:	util-linux
BuildRequires:	xz
BuildRequires:	zlib-devel
# gcc4 might be installed, but not current __cc
%if "%(echo %{cc_version} | cut -d. -f1,2)" < "4.0"
BuildRequires:	__cc >= 4.0
%endif
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
%setup -q -n modpagespeed
%patch0 -p1
%patch1 -p1

%build
# re-gen makefiles
cd src
CC="%{__cc}" \
CXX="%{__cxx}" \
%{__python} build/gyp_chromium --format=make build/all.gyp \
	-Duse_openssl=1 \
	-Duse_system_apache_dev=1 \
	-Duse_system_libjpeg=1 \
	-Duse_system_libpng=1 \
	-Duse_system_opencv=1 \
	-Duse_system_zlib=1 \
	%{nil}

cd ..

# makefile wrapper so we could just invoke "make" from shell
cat > Makefile <<'EOF'
# target names from build/all.gyp
default:
	$(MAKE) -C src mod_pagespeed \
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

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir},%{cachedir}/{cache,files}}
%{__make} -j1 -C src/install staging_except_module \
	HOSTNAME=localhost \
	APACHE_ROOT=%{_pkgrootdir} \
	APACHE_MODULES=modules \
	APACHE_DOC_ROOT=%{htdocsdir} \
	MOD_PAGESPEED_FILE_ROOT=%{cachedir} \
	STAGING_DIR=staging

install -p src/out/Release/libmod_%{mod_name}.so $RPM_BUILD_ROOT%{_pkglibdir}/mod_%{mod_name}.so
cd src/install/staging
cat > $RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf <<EOF
LoadModule %{mod_name}_module	modules/mod_%{mod_name}.so

$(cat pagespeed.conf)
EOF

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
%attr(755,root,root) %{_pkglibdir}/mod_%{mod_name}.so
%{_examplesdir}/%{name}-%{version}

%dir %attr(710,root,http) %{cachedir}
%dir %attr(770,root,http) %{cachedir}/cache
%dir %attr(770,root,http) %{cachedir}/files
