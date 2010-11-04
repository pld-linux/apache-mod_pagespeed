%define		svndate	20101104
%define		rel		0.1
%define		mod_name	pagespeed
%define 	apxs		%{_sbindir}/apxs
Summary:	Apache module for rewriting web pages to reduce latency and bandwidth
Name:		apache-mod_%{mod_name}
Version:	0.9.0.0
Release:	0.1
License:	Apache v2.0
Group:		Networking/Daemons/HTTP
# svn co http://src.chromium.org/svn/trunk/tools/depot_tools
# install -d modpagespeed
# cd modpagespeed
# ../depot_tools/gclient config http://modpagespeed.googlecode.com/svn/trunk/src
# ../depot_tools/gclient sync
# cd -
# tar -cjf modpagespeed-$(date +%Y%m%d).tar.bz2 --exclude-vcs modpagespeed
# ../dropin modpagespeed-$(date +%Y%m%d).tar.bz2 &
Source0:	modpagespeed-%{svndate}.tar.bz2
# Source0-md5:	-
Source1:	apache.conf
URL:		http://code.google.com/p/modpagespeed/
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	rpmbuild(macros) >= 1.268
Requires:	apache(modules-api) = %apache_modules_api
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		_sysconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d

%description
mod_pagespeed automates the application of those rules in an Apache
server. HTML, CSS, JavaScript, and images are changed dynamically
during the web serving process, so that the best practices recommended
by Page Speed can be used without having to change the way the web
site is maintained.

%prep
%setup -q -n modpagespeed

%build
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
EOF
%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir}}
install -p mod_%{mod_name}.so $RPM_BUILD_ROOT%{_pkglibdir}

# module configuration
# - should contain LoadModule line
# - and directives must be between IfModule (so user could disable the module easily)
cp -a %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf

# or, if no directives needed, put just LoadModule line
echo 'LoadModule %{mod_name}_module	modules/mod_%{mod_name}.so' > \
	$RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf

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
%doc README
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/*_mod_%{mod_name}.conf
%attr(755,root,root) %{_pkglibdir}/*
