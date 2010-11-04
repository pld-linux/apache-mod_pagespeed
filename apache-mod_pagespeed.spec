%define		svnrev	128
%define		rel		0.1
%define		mod_name	pagespeed
%define 	apxs		%{_sbindir}/apxs
Summary:	Apache module for rewriting web pages to reduce latency and bandwidth
Name:		apache-mod_%{mod_name}
Version:	0.9.0.0
Release:	0.2
License:	Apache v2.0
Group:		Networking/Daemons/HTTP
Source0:	https://dl-ssl.google.com/dl/linux/direct/mod-pagespeed-beta_current_i386.rpm
# Source0-md5:	f2c98801bce8bd69d07bb1dcc951f88d
Source1:	https://dl-ssl.google.com/dl/linux/direct/mod-pagespeed-beta_current_x86_64.rpm
# Source1-md5:	fe63524cbcae79034767caccc56da7df
URL:		http://code.google.com/p/modpagespeed/
BuildRequires:	%{apxs}
BuildRequires:	apache-devel >= 2.2
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	sed >= 4.0
Requires:	apache(modules-api) = %apache_modules_api
Suggests:	apache-mod_deflate
ExclusiveArch:	%{ix86} %{x8664}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_pkglibdir	%(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define		_sysconfdir	%(%{apxs} -q SYSCONFDIR 2>/dev/null)/conf.d

%define		_enable_debug_packages	0
%define		no_install_post_strip	1

%description
mod_pagespeed automates the application of those rules in an Apache
server. HTML, CSS, JavaScript, and images are changed dynamically
during the web serving process, so that the best practices recommended
by Page Speed can be used without having to change the way the web
site is maintained.

%prep
%setup -qcT
%ifarch %{ix86}
SOURCE=%{S:0}
%endif
%ifarch %{x8664}
SOURCE=%{S:1}
%endif

V=$(rpm -qp --nodigest --nosignature --qf '%{V}' $SOURCE)
R=$(rpm -qp --nodigest --nosignature --qf '%{R}' $SOURCE)
if [ version:$V != version:%{version} -o svnrev:$R != svnrev:%{svnrev} ]; then
	exit 1
fi
rpm2cpio $SOURCE | cpio -i -d

mv etc/httpd/conf.d/pagespeed.conf apache.conf
mv usr/lib/httpd/modules .

%{__sed} -i -e '
	# fix module load path
	s,/''usr/lib/httpd/modules/mod_pagespeed.so,%{_pkglibdir}/mod_%{mod_name}.so,

	# drop loading of deflate module
	3,6d

	# fixup paths
    s,/var/mod_pagespeed/cache/,/var/cache/mod_%{mod_name}/,
    s,/var/mod_pagespeed/files/,/var/lib/mod_%{mod_name}/,
' apache.conf

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_pkglibdir},%{_sysconfdir}}
install -p modules/mod_%{mod_name}.so $RPM_BUILD_ROOT%{_pkglibdir}
cp -a apache.conf $RPM_BUILD_ROOT%{_sysconfdir}/90_mod_%{mod_name}.conf

# cache and files dir
install -d $RPM_BUILD_ROOT/var/{cache,lib}/mod_%{mod_name}

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
%attr(770,root,http) /var/cache/mod_%{mod_name}
%attr(770,root,http) /var/lib/mod_%{mod_name}
