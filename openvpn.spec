%define easy_rsa_version 3.2.0
%define plugindir %{_libdir}/%{name}/plugins
%define __noautoreq 'perl\\(POSIX\\)|perl\\(Authen::PAM\\)'

Summary:	A Secure TCP/UDP Tunneling Daemon
Name:		openvpn
Version:	2.6.17
Release:	1
License:	GPLv2
Group:		Networking/Other
Url:		https://openvpn.net/
Source0:	https://github.com/OpenVPN/openvpn/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:	https://github.com/OpenVPN/easy-rsa/releases/download/v%{easy_rsa_version}/EasyRSA-%{easy_rsa_version}.tgz
Source2:	%{name}.sysusers
Source3:	dhcp.sh
#Patch2:		openvpn-2.3.1_rc15-wformat.patch
BuildRequires:	pkgconfig(lzo2)
BuildRequires:	pam-devel
BuildRequires:	pkgconfig(libcap-ng)
BuildRequires:	pkgconfig(libpkcs11-helper-1)
BuildRequires:	pkgconfig(p11-kit-1)
BuildRequires:	pkgconfig(openssl)
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	systemd-macros
BuildRequires:	rpm-helper
BuildRequires:	pkgconfig(liblz4)
BuildRequires:	iproute2
BuildRequires:	cmake
BuildRequires:	python3dist(docutils)
%systemd_requires
Suggests:	openvpn-auth-ldap
Requires:	iproute2

%description
OpenVPN is a robust and highly flexible tunneling application that  uses
all of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP port.

%package devel
Summary:	Development headers for OpenVPN plugins
Group:		Development/Other
Requires:	%{name} = %{version}-%{release}

%description devel
OpenVPN header files.

%prep
%autosetup -p1 -a 1
# %%doc items shouldn't be executable.
find contrib sample -type f -perm /100 \
    -exec chmod a-x {} \;
autoreconf -fi

%build
CFLAGS="%{optflags} -fPIC" CCFLAGS="%{optflags} -fPIC"
%serverbuild
%configure \
	--enable-systemd \
	--enable-iproute2 \
	--enable-plugins \
	--enable-pkcs11 \
	--enable-x509-alt-username \
	--with-crypto-library=openssl \
	--enable-async-push \
	SYSTEMD_UNIT_DIR=%{_unitdir} \
	TMPFILES_DIR=%{_tmpfilesdir} \
	IPROUTE=/sbin/ip \
	--enable-password-save || cat config.log

%make_build

# plugins
%make_build -C src/plugins/down-root
%make_build -C src/plugins/auth-pam

%install
%make_install
mkdir -p %{buildroot}%{_datadir}/%{name}/easy-rsa %{buildroot}%{_sysconfdir}/pki/tls
cp -a EasyRSA-%{easy_rsa_version}/easyrsa %{buildroot}%{_datadir}/%{name}/easy-rsa/
cp -a EasyRSA-%{easy_rsa_version}/openssl-easyrsa.cnf %{buildroot}%{_sysconfdir}/pki/tls/

mkdir -p -m 0750 %{buildroot}%{_sysconfdir}/%{name}/client %{buildroot}%{_sysconfdir}/%{name}/server
# Create some directories the OpenVPN package should own
mkdir -m 0710 -p %{buildroot}%{_rundir}/%{name}-{client,server}
mkdir -m 0770 -p %{buildroot}%{_sharedstatedir}/%{name}

# (cg) NB The sample config file is needed for drakvpn
cp -pr sample/sample-{config-file,key,script}s %{buildroot}%{_datadir}/%{name}

mkdir -p %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_localstatedir}/lib/%{name}

# (cg) Nuke sysvinit script
rm -f %{buildroot}%{_datadir}/%{name}/sample-scripts/openvpn.init

#plugins
mkdir -p %{buildroot}%{plugindir}

install -m755 %{SOURCE3} %{buildroot}%{_datadir}/%{name}

install -D -p -m 644 %{SOURCE2} %{buildroot}%{_sysusersdir}/%{name}.conf

install -d %{buildroot}%{_presetdir}
cat > %{buildroot}%{_presetdir}/86-openvpn.preset << EOF
enable openvpn.service
EOF

%check
# Test Crypto:
./src/openvpn/openvpn --genkey --secret key
./src/openvpn/openvpn --cipher aes-128-cbc --test-crypto --secret key
./src/openvpn/openvpn --cipher aes-256-cbc --test-crypto --secret key
./src/openvpn/openvpn --cipher aes-128-gcm --test-crypto --secret key
./src/openvpn/openvpn --cipher aes-256-gcm --test-crypto --secret key

%post
%systemd_post openvpn-client@\*.service
%systemd_post openvpn-server@\*.service

%preun
%systemd_preun openvpn-client@\*.service
%systemd_preun openvpn-server@\*.service

%postun
%systemd_postun_with_restart openvpn-client@\*.service
%systemd_postun_with_restart openvpn-server@\*.service

%files
%doc %{_docdir}/%{name}
%config %{_sysconfdir}/pki/tls/openssl-easyrsa.cnf
%config %dir %{_sysconfdir}/%{name}/
%config %dir %{_sysconfdir}/%{name}/client
%config %dir %{_sysconfdir}/%{name}/server
%attr(0710,-,-) %{_rundir}/%{name}-client
%attr(0710,-,-) %{_rundir}/%{name}-server
%{_presetdir}/86-openvpn.preset
%{_unitdir}/%{name}*.service
%{_sysusersdir}/%{name}.conf
%{_tmpfilesdir}/%{name}.conf
%{_sbindir}/%{name}
%{_mandir}/man8/%{name}.8*
%{_mandir}/man5/openvpn-examples.5.*
%{_datadir}/%{name}
%dir %{plugindir}
%{plugindir}/*.so
%dir %{_localstatedir}/lib/%{name}

%files devel
%{_includedir}/openvpn-plugin.h
%{_includedir}/openvpn-msg.h
