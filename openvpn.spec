%define plugindir %_libdir/%name

Summary:	A Secure TCP/UDP Tunneling Daemon
Name:		openvpn
Version:	2.1.4
Release:	%mkrel 3
URL:		http://openvpn.net/
Source0:	http://openvpn.net/release/openvpn-%{version}.tar.gz
Patch0:		%{name}-own-user.patch
Patch1:		openvpn-adding-routes.patch
Patch3:		openvpn-2.0.5-pinit.patch
Patch4:		openvpn-2.1_rc1.openvpn_user.patch
Patch6:		openvpn-2.1_rc15-wformat.patch
Patch7:		openvpn-pushc.patch
License:	GPLv2
Group:		Networking/Other
BuildRequires:	liblzo-devel
BuildRequires:	libpkcs11-helper-devel
BuildRequires:	openssl-devel
BuildRequires:	pam-devel
Requires(pre):	rpm-helper
Requires(preun): 	rpm-helper
Requires(post):	rpm-helper
Requires(postun):	rpm-helper
Suggests:	openvpn-auth-ldap
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
OpenVPN is a robust and highly flexible tunneling application that  uses
all of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP port.

%prep

%setup -q -n openvpn-%{version}
%patch0 -p0
%patch1 -p1
%patch3 -p1
%patch4 -p1
%patch6 -p1
%patch7 -p1

%build
autoreconf -fi
%serverbuild

CFLAGS="%{optflags} -fPIC" CCFLAGS="%{optflags} -fPIC"
%configure2_5x \
    --enable-pthread \
    --with-lzo-headers=%{_includedir}/lzo

%make

# plugins
%make -C plugin/down-root
%make -C plugin/auth-pam

%install
rm -rf %{buildroot}

%makeinstall_std

install -m755 sample-scripts/%{name}.init -D %{buildroot}/%{_initrddir}/%{name}
install -d %{buildroot}%{_sysconfdir}/%{name}

mkdir -p %{buildroot}%{_datadir}/%{name}
cp -pr easy-rsa sample-{config-file,key,script}s %{buildroot}%{_datadir}/%{name}

%{__chmod} 0755 %{buildroot}%{_datadir}/%{name}/easy-rsa/1.0/revoke-crt \
  %{buildroot}%{_datadir}/%{name}/easy-rsa/1.0/make-crl \
  %{buildroot}%{_datadir}/%{name}/easy-rsa/1.0/list-crl
%{__rm} -r %{buildroot}%{_datadir}/%{name}/easy-rsa/Windows/init-config.bat

install -d %{buildroot}%{_localstatedir}/lib/%{name}

#plugins
mkdir -p %{buildroot}%{plugindir}

for pi in down-root auth-pam; do
	%{__cp} -pf plugin/$pi/README plugin/README.$pi
	%{__install} -c -p -m 755 plugin/$pi/openvpn-$pi.so %{buildroot}%plugindir/openvpn-$pi.so
done

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
%doc AUTHORS INSTALL PORTS README plugin/README.*
%dir %{_sysconfdir}/%{name}
%{_initrddir}/%{name}
%{_sbindir}/%{name}
%{_datadir}/%{name}
%dir %{_localstatedir}/lib/%{name}
%dir %plugindir
%plugindir/*.so
%{_mandir}/man8/%{name}.8*
