%define easy_rsa_version 2.2.2
%define plugindir %{_libdir}/%{name}/plugins
%define _tmpfilesdir %{_prefix}/lib/tmpfiles.d
%define __noautoreq 'perl\\(POSIX\\)|perl\\(Authen::PAM\\)'

Summary:	A Secure TCP/UDP Tunneling Daemon
Name:		openvpn
Version:	2.3.11
Release:	1
License:	GPLv2
Group:		Networking/Other
Url:		http://openvpn.net/
Source0:	http://swupdate.openvpn.org/community/releases/%{name}-%{version}.tar.gz
Source3:	dhcp.sh
Source4:	openvpn-tmpfile.conf
Source5:	openvpn@.service
Source6:	openvpn.target
Source7:	https://github.com/downloads/OpenVPN/easy-rsa/easy-rsa-%{easy_rsa_version}.tar.gz
Patch1:		openvpn-2.3.openvpn_user.patch
Patch2:		openvpn-2.3.1_rc15-wformat.patch
BuildRequires:	lzo-devel
BuildRequires:	pam-devel
BuildRequires:	pkgconfig(libpkcs11-helper-1)
BuildRequires:	pkgconfig(openssl)
BuildRequires:	pkgconfig(systemd)
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	pkgconfig(libsystemd-daemon)
Requires(pre,preun,post,postun):	rpm-helper
Suggests:	openvpn-auth-ldap

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
%setup -q -a 7
%apply_patches
# %%doc items shouldn't be executable.
find contrib sample -type f -perm /100 \
    -exec chmod a-x {} \;
sed -i -e 's,%{_datadir}/openvpn/plugin,%{_libdir}/openvpn/plugin,' doc/openvpn.8
autoreconf -fi

%build
CFLAGS="%{optflags} -fPIC" CCFLAGS="%{optflags} -fPIC"
%serverbuild
%configure \
	--enable-systemd \
	--enable-password-save || cat config.log

%make

# plugins
%make -C src/plugins/down-root
%make -C src/plugins/auth-pam

pushd easy-rsa-%{easy_rsa_version}
autoreconf -fi
%configure \
	--with-easyrsadir=%{_datadir}/%{name}/easy-rsa
%make
popd

%install
%makeinstall_std
mkdir -p %{buildroot}%{_datadir}/%{name}/easy-rsa
%makeinstall_std -C easy-rsa-%{easy_rsa_version}

install -d %{buildroot}%{_sysconfdir}/%{name}
# (cg) NB The sample config file is needed for drakvpn
cp -pr sample/sample-{config-file,key,script}s %{buildroot}%{_datadir}/%{name}

mkdir -p %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_localstatedir}/lib/%{name}

# (cg) Nuke sysvinit script
rm -f %{buildroot}%{_datadir}/%{name}/sample-scripts/openvpn.init

# (cg) Add systemd units
install -D -m 644 %{SOURCE4} %{buildroot}%{_tmpfilesdir}/openvpn.conf
install -D -m 644 %{SOURCE5} %{buildroot}%{_unitdir}/openvpn@.service
install -D -m 644 %{SOURCE6} %{buildroot}%{_unitdir}/openvpn.target

#plugins
mkdir -p %{buildroot}%{plugindir}

install -m755 %{SOURCE3} %{buildroot}%{_datadir}/%{name}

install -d %{buildroot}%{_presetdir}
cat > %{buildroot}%{_presetdir}/86-openvpn.preset << EOF
enable openvpn.service
enable openvpn.target
EOF

%pre
%_pre_useradd %{name} %{_localstatedir}/lib/%{name} /bin/true

%post
# (cg) This is a templated unit, so we have to manually convert to systemd
if [ ! -f %{_localstatedir}/lib/rpm-helper/systemd-migration/%{name} ]; then
  if [ -f %{_sysconfdir}/rc3.d/S??%{name} ]; then
    for conf in %{_sysconfdir}/%{name}/*.conf; do
      [ "$conf" = "%{_sysconfdir}/%{name}/*.conf" ] && continue
      conf=$(basename $conf .conf)
      mkdir -p %{_sysconfdir}/systemd/system/%{name}.target.wants
      ln -s %{_unitdir}/%{name}@.service %{_sysconfdir}/systemd/system/%{name}.target.wants/%{name}@$conf.service
    done
    systemctl --quiet enable %{name}.target
  fi
  mkdir -p %{_localstatedir}/lib/rpm-helper/systemd-migration
  touch %{_localstatedir}/lib/rpm-helper/systemd-migration/%{name}
else
  # (cg) Older versions were not controlled by their own target
  UNITS=
  for unit in %{_sysconfdir}/systemd/system/multi-user.target.wants/%{name}@?*.service; do
    [ "$unit" = "%{_sysconfdir}/systemd/system/multi-user.target.wants/%{name}@?*.service" ] && continue
    UNITS="$UNITS $unit"
  done
  if [ -n "$UNITS" ]; then
    mkdir %{_sysconfdir}/systemd/system/%{name}.target.wants
    mv $UNITS %{_sysconfdir}/systemd/system/%{name}.target.wants
    systemctl --quiet enable %{name}.target
  fi
fi

%files
%doc AUTHORS INSTALL PORTS README 
%doc src/plugins/*/README.*
%{_docdir}/easy-rsa/*
%dir %{_sysconfdir}/%{name}
%{_presetdir}/86-openvpn.preset
%{_unitdir}/%{name}*.service
%{_unitdir}/%{name}.target
%{_tmpfilesdir}/%{name}.conf
%{_sbindir}/%{name}
%{_mandir}/man8/%{name}.8*
%{_datadir}/%{name}
%dir %{plugindir}
%{plugindir}/*.so
%dir %{_localstatedir}/lib/%{name}

%files devel
%{_includedir}/openvpn-plugin.h

