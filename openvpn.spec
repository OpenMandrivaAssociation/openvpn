%define plugindir %{_libdir}/openvpn

Summary:	A Secure TCP/UDP Tunneling Daemon
Name:		openvpn
Version:	2.2.2
Release:	1
License:	GPLv2
Group:		Networking/Other
URL:		http://openvpn.net/
Source0:	http://swupdate.openvpn.net/community/releases/openvpn-%{version}.tar.gz
Source1:	http://swupdate.openvpn.net/community/releases/openvpn-%{version}.tar.gz.asc
Patch0:		openvpn-own-user.patch
Patch1:		openvpn-adding-routes.patch
Patch2:		openvpn-2.0.5-pinit.patch
Patch3:		openvpn-2.1_rc1.openvpn_user.patch
Patch4:		openvpn-2.1_rc15-wformat.patch
# fedora patches
Patch10:	openvpn-script-security.patch
Patch11:	openvpn-2.1.1-init.patch
Patch12:	openvpn-2.1.1-initinfo.patch
BuildRequires:	liblzo-devel
BuildRequires:	libpkcs11-helper-devel
BuildRequires:	openssl-devel
BuildRequires:	pam-devel
Requires(pre):	rpm-helper
Requires(preun): 	rpm-helper
Requires(post):	rpm-helper
Requires(postun):	rpm-helper
Suggests:	openvpn-auth-ldap

%description
OpenVPN is a robust and highly flexible tunneling application that  uses
all of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP port.

%prep

%setup -q -n openvpn-%{version}
%patch0 -p0
%patch1 -p1
%patch2 -p0
%patch3 -p1
%patch4 -p1
# fedora patches
%patch10 -p0
%patch11 -p0
%patch12 -p0

sed -i -e 's,%{_datadir}/openvpn/plugin,%{_libdir}/openvpn/plugin,' openvpn.8

# %%doc items shouldn't be executable.
find contrib sample-config-files sample-keys sample-scripts -type f -perm +100 \
    -exec chmod a-x {} \;

%build
autoreconf -fi
%serverbuild

CFLAGS="%{optflags} -fPIC" CCFLAGS="%{optflags} -fPIC"

#  --enable-pthread        Enable pthread support (Experimental for OpenVPN 2.0)
#  --enable-password-save  Allow --askpass and --auth-user-pass passwords to be
#                          read from a file
#  --enable-iproute2       Enable support for iproute2
#  --with-ifconfig-path=PATH   Path to ifconfig tool
#  --with-iproute-path=PATH    Path to iproute tool
#  --with-route-path=PATH  Path to route tool
%configure2_5x \
    --enable-pthread \
    --enable-password-save \
    --enable-iproute2 \
    --with-ifconfig-path=/sbin/ifconfig \
    --with-iproute-path=/sbin/ip \
    --with-route-path=/sbin/route \
    --with-lzo-headers=%{_includedir}/lzo

%make

# plugins
%make -C plugin/down-root
%make -C plugin/auth-pam

%check
# Test Crypto:
./openvpn --genkey --secret key
./openvpn --test-crypto --secret key

# Randomize ports for tests to avoid conflicts on the build servers.
cport=$[ 50000 + ($RANDOM % 15534) ]
sport=$[ $cport + 1 ]
sed -e 's/^\(rport\) .*$/\1 '$sport'/' \
    -e 's/^\(lport\) .*$/\1 '$cport'/' \
    < sample-config-files/loopback-client \
    > %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-client
sed -e 's/^\(rport\) .*$/\1 '$cport'/' \
    -e 's/^\(lport\) .*$/\1 '$sport'/' \
    < sample-config-files/loopback-server \
    > %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-server

# Test SSL/TLS negotiations (runs for 2 minutes):
./openvpn --config \
    %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-client &
./openvpn --config \
    %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-server
wait

rm -f %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-client \
    %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-server

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
