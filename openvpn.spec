%define beta _rc22
%define auth_ldap_version 2.0.3

%define plugindir %_libdir/%name
%bcond_without ldap

# There is an issue with gcc, so disable for amd64
# waiting reply/fix
%ifarch amd64
%bcond_without ldap
%endif

Summary:	A Secure UDP Tunneling Daemon
Name:		openvpn
Version:	2.1
Release:	%mkrel 0.rc22.1
URL:		http://openvpn.net/
Source0:	http://openvpn.net/release/openvpn-%{version}%{beta}.tar.gz
Source2:	http://www.opendarwin.org/~landonf/software/openvpn-auth-ldap/auth-ldap-%{auth_ldap_version}.tar.gz
Patch0:		%{name}-own-user.patch
Patch1:		openvpn-adding-routes.patch
Patch3:		openvpn-2.0.5-pinit.patch
Patch4:		openvpn-2.1_rc1.openvpn_user.patch
Patch5:		openvpn-auth-ldap-2.0.3-disable-tests.patch
Patch6:		openvpn-2.1_rc15-wformat.patch
Patch7:		openvpn-pushc.patch
License:	GPLv2
Group:		Networking/Other
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires:	liblzo-devel openssl-devel
BuildRequires:	pam-devel
BuildRequires:	libpkcs11-helper-devel
BuildRequires:	automake1.8
%if %with ldap
BuildRequires:	gcc-objc
BuildRequires:	openldap-devel
BuildRequires:	re2c
%endif
Requires(pre):	rpm-helper
Requires(preun): 	rpm-helper
Requires(post):	rpm-helper
Requires(postun):	rpm-helper

%description
OpenVPN is a robust and highly flexible tunneling application that  uses
all of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP port.

%if %with ldap
This package contains the auth-ldap plugin
%endif

%prep
%setup -q -n openvpn-%{version}%{beta}
%if %with ldap
%setup -q -n openvpn-%{version}%{beta} -a 2
%{__mv} auth-ldap-%{auth_ldap_version}/README auth-ldap-%{auth_ldap_version}/README-openvpn-auth-ldap
%endif
%patch0 -p0
%patch1 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p0
%patch6 -p1
%patch7 -p1

%build
%serverbuild
#./pre-touch
aclocal-1.8
automake-1.8
autoconf

CFLAGS="%{optflags} -fPIC" CCFLAGS="%{optflags} -fPIC"
%configure2_5x --enable-pthread --with-lzo-headers=%{_includedir}/lzo
%make
# plugins
%make -C plugin/down-root
%make -C plugin/auth-pam

%if %with ldap
pushd auth-ldap-%{auth_ldap_version}
%configure2_5x --with-openvpn=`pwd`/../ --libdir=%{plugindir}
%make
popd
%endif

%install
rm -rf $RPM_BUILD_ROOT
%makeinstall_std

#install -m755 %{name}.8 -D %{buildroot}%{_mandir}/man8/%{name}.8
#install -m755 %{name} -D %{buildroot}%{_sbindir}/%{name}
install -m755 sample-scripts/%{name}.init -D %{buildroot}/%{_initrddir}/%{name}
install -d %{buildroot}%{_sysconfdir}/%{name}

mkdir -p %{buildroot}%{_datadir}/%{name}
cp -pr easy-rsa sample-{config-file,key,script}s %{buildroot}%{_datadir}/%{name}

%{__chmod} 0755 %{buildroot}%{_datadir}/%{name}/easy-rsa/1.0/revoke-crt \
  %{buildroot}%{_datadir}/%{name}/easy-rsa/1.0/make-crl \
  %{buildroot}%{_datadir}/%{name}/easy-rsa/1.0/list-crl
%{__rm} -r %{buildroot}%{_datadir}/%{name}/easy-rsa/Windows/init-config.bat
	
install -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}

#plugins
mkdir -p %{buildroot}%{plugindir}

for pi in down-root auth-pam; do
	%{__cp} -pf plugin/$pi/README plugin/README.$pi
	%{__install} -c -p -m 755 plugin/$pi/openvpn-$pi.so %{buildroot}%plugindir/openvpn-$pi.so
done

%if %with ldap
pushd auth-ldap-%{auth_ldap_version}
%makeinstall_std
popd
%endif

%clean
rm -rf %{buildroot}

%pre
%_pre_useradd %{name} %{_localstatedir}/lib/%{name} /bin/true

%post
%_post_service %{name}

%preun
%_preun_service %{name}

%postun
%_postun_userdel %{name}

%files
%defattr(-,root,root,0755)
%doc AUTHORS INSTALL PORTS README
%doc plugin/README.*
%if %with ldap
%doc auth-ldap-%auth_ldap_version/README-openvpn-auth-ldap
%endif
%{_mandir}/man8/%{name}.8*
%{_sbindir}/%{name}
%{_datadir}/%{name}
%dir %{_sysconfdir}/%{name}
%{_initrddir}/%{name}
%dir %{_localstatedir}/lib/%{name}
%dir %plugindir
%plugindir/*.so
