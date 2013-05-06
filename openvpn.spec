%define easy_rsa_version 2.2.0_master
%define develname %mklibname %{name} -d


%define plugindir %_libdir/%name/plugins

Summary:	A Secure TCP/UDP Tunneling Daemon
Name:		openvpn
Version:	2.3.1
Release:	%mkrel 2
URL:		http://openvpn.net/
Source0:	http://openvpn.net/release/openvpn-%{version}.tar.gz
Source3:	dhcp.sh
Source4:	openvpn-tmpfile.conf
Source5:	openvpn@.service
Source6:	openvpn.target
Source7:	https://github.com/downloads/OpenVPN/easy-rsa/easy-rsa-%{easy_rsa_version}.tar.gz
Patch1:		openvpn-2.3.openvpn_user.patch
Patch2:		openvpn-2.3.1_rc15-wformat.patch
License:	GPLv2
Group:		Networking/Other
BuildRequires:	liblzo-devel openssl-devel
BuildRequires:	pam-devel
BuildRequires:	libpkcs11-helper-devel
Requires(pre):	rpm-helper
Requires(preun):	rpm-helper
Requires(post):	rpm-helper
Requires(postun):	rpm-helper
Suggests:	openvpn-auth-ldap

%description
OpenVPN is a robust and highly flexible tunneling application that  uses
all of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP port.


%package -n %develname
Summary:        Development package for OpenVPN plugins
Group:          System/Libraries
Requires:       %{name} = %version-%release

%description -n %develname
OpenVPN .h files.

%prep
%setup -q -n openvpn-%{version} -a 7
%patch1 -p1
%patch2 -p1

sed -i -e 's,%{_datadir}/openvpn/plugin,%{_libdir}/openvpn/plugin,' doc/openvpn.8

# %%doc items shouldn't be executable.
find contrib sample -type f -perm +100 \
    -exec chmod a-x {} \;

%build
CFLAGS="%{optflags} -fPIC" CCFLAGS="%{optflags} -fPIC"
%serverbuild
#./pre-touch
libtoolize --copy --force --install
aclocal
automake -a -c -f -i
autoreconf -fi

%configure2_5x \
	--enable-systemd \
	--enable-pthread \
	--with-lzo-headers=%{_includedir}/lzo \
	--enable-password-save || cat config.log

%make

# plugins
%make -C src/plugins/down-root
%make -C src/plugins/auth-pam

pushd easy-rsa-%{easy_rsa_version}
%configure2_5x \
	--with-easyrsadir=%{_datadir}/%{name}/easy-rsa
%make
popd

%install
%makeinstall_std
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
%_tmpfilescreate %{name}
%_post_service %{name} %{name}.target

%preun
%_preun_service %{name} %{name}.target

%postun
%_postun_userdel %{name}

%files
%doc AUTHORS INSTALL PORTS README 
%doc src/plugins/*/README.*
%doc 
%{_mandir}/man8/%{name}.8*
%{_sbindir}/%{name}
%{_datadir}/%{name}
%dir %{_sysconfdir}/%{name}
#{_datadir}/%{name}/dhcp.sh
%{_unitdir}/%{name}*.service
%{_unitdir}/%{name}.target
%{_tmpfilesdir}/%{name}.conf
%dir %{_localstatedir}/lib/%{name}
%dir %plugindir
%plugindir/*
%{_docdir}/easy-rsa/COPYING
%{_docdir}/easy-rsa/COPYRIGHT.GPL
%{_docdir}/easy-rsa/README-2.0

%files -n %develname
%{_includedir}/openvpn-plugin.h
