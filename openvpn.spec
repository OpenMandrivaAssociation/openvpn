%define version 2.0.9
%define auth_ldap_version 1.0.1

%define plugindir %_libdir/%name
%define buildldap 1

# There is an issue with gcc, so disable for amd64
# waiting reply/fix
%ifarch amd64
%define buildldap 0
%endif

Summary:	A Secure UDP Tunneling Daemon
Name:		openvpn
Version:	%version
Release:	%mkrel 3
URL:		http://openvpn.net/
Source0:	http://openvpn.net/release/%{name}-%{version}.tar.gz
Source1:    http://openvpn.net/signatures/%{name}-%{version}.tar.gz.asc
Source2:    http://www.opendarwin.org/~landonf/software/openvpn-auth-ldap/auth-ldap-%{auth_ldap_version}.tar.gz
Patch0:		%{name}-own-user.patch
Patch1:		openvpn-adding-routes.patch
Patch2:		openvpn-auth-ldap-1.0.patch
Patch3:		openvpn-2.0.5-pinit.patch
Patch4:     openvpn-2.1_rc1.openvpn_user.patch
License:	GPL
Group:		Networking/Other
BuildRequires:  liblzo-devel openssl-devel
BuildRequires:	pam-devel
BuildRequires:  automake1.8
%if %buildldap
BuildRequires:  gcc-objc
BuildRequires:  openldap-devel
%endif
Requires(pre): rpm-helper
Requires(preun): rpm-helper
Requires(post): rpm-helper
Requires(postun): rpm-helper

%description
OpenVPN is a robust and highly flexible tunneling application that  uses
all of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP port.

%if buildldap
This package contains the auth-ldap plugin
%endif

%prep
%setup -q
%if %buildldap
%setup -q -a 2
%endif
%patch0 -p0
%patch1 -p1
%if %buildldap
%patch2 -p0
%endif
%patch3 -p1 -b .pinit
%patch4 -p1 -b .user

%build
%serverbuild
#./pre-touch
aclocal-1.8
automake-1.8
autoconf

CFLAGS="$RPM_OPT_FLAGS -fPIC" CCFLAGS="$RPM_OPT_FLAGS -fPIC"

%configure \
    --enable-pthread \
    --enable-plugin \
    --with-lzo-headers=%_includedir/lzo

%make

# plugins
%make -C plugin/down-root
%make -C plugin/auth-pam

%if %buildldap
%make -C auth-ldap-%auth_ldap_version OPENVPN=.. LDAP=/usr
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

install -d $RPM_BUILD_ROOT%{_localstatedir}/%{name}

#plugins
mkdir -p %buildroot%plugindir

for pi in down-root auth-pam; do
    %__cp -f plugin/$pi/README plugin/README.$pi
    %__install -c -m 755 plugin/$pi/openvpn-$pi.so %{buildroot}%plugindir/openvpn-$pi.so
done

%if %buildldap
%__install -c -m 755 auth-ldap-%auth_ldap_version/openvpn-auth-ldap.so %{buildroot}%plugindir/openvpn-auth-ldap.so
%__cp -f auth-ldap-%auth_ldap_version/README auth-ldap-%auth_ldap_version/README-openvpn-auth-ldap
%endif

%clean
[ %{buildroot} != "/" ] && rm -rf %{buildroot}

%pre
%_pre_useradd %{name} %{_localstatedir}/%{name} /bin/true

%post
%_post_service %{name}

%preun
%_preun_service %{name}

%postun
%_postun_userdel %{name}

%files
%defattr(-,root,root)
%doc AUTHORS INSTALL PORTS README
%doc plugin/README.*
%if %buildldap
%doc auth-ldap-%auth_ldap_version/README-openvpn-auth-ldap
%endif
%{_mandir}/man8/%{name}.8*
%{_sbindir}/%{name}
%{_datadir}/%{name}
%dir %{_sysconfdir}/%{name}
%{_initrddir}/%{name}
%dir %{_localstatedir}/%{name}
%dir %plugindir
%plugindir/*.so


