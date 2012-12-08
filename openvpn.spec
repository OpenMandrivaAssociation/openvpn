%define plugindir %{_libdir}/openvpn

Summary:	A Secure TCP/UDP Tunneling Daemon
Name:		openvpn
Version:	2.2.1
Release:	%mkrel 3
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
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

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


%changelog
* Fri Jul 08 2011 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.2.1-1mdv2011.0
+ Revision: 689306
- New 2.2.1 with bugfixes

* Sat May 21 2011 Oden Eriksson <oeriksson@mandriva.com> 2.2.0-1
+ Revision: 676569
- 2.2.0
- rediff some patches
- sync changes with openvpn-2.2.0-1.fc16.src.rpm

* Wed May 18 2011 Oden Eriksson <oeriksson@mandriva.com> 2.1.4-3
+ Revision: 675958
- broke out auth-ldap to its own package
- mass rebuild

  + Luis Daniel Lucio Quiroz <dlucio@mandriva.org>
    - 2.1.4
      Fix summary

* Tue Oct 19 2010 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.1.3-1mdv2011.0
+ Revision: 586743
- 2.1.3

* Wed Aug 18 2010 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.1.2-1mdv2011.0
+ Revision: 571120
- 2.1.2

* Thu Apr 08 2010 Eugeni Dodonov <eugeni@mandriva.com> 2.1.1-3mdv2010.1
+ Revision: 533059
- Rebuild for openssl 1.0.0.

* Fri Feb 26 2010 Oden Eriksson <oeriksson@mandriva.com> 2.1.1-2mdv2010.1
+ Revision: 511606
- rebuilt against openssl-0.9.8m

* Sat Dec 12 2009 Frederik Himpe <fhimpe@mandriva.org> 2.1.1-1mdv2010.1
+ Revision: 477774
- update to new version 2.1.1

* Fri Dec 11 2009 Funda Wang <fwang@mandriva.org> 2.1.0-1mdv2010.1
+ Revision: 476390
- new version 2.1.0

* Mon Nov 23 2009 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.1-0.rc22.2mdv2010.1
+ Revision: 469177
- Source2 URL updated

* Sat Nov 21 2009 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.1-0.rc22.1mdv2010.1
+ Revision: 468162
- New rc22

* Thu Nov 12 2009 Frederik Himpe <fhimpe@mandriva.org> 2.1-0.rc20.1mdv2010.1
+ Revision: 465276
- Update to new version 2.1-rc21

* Mon Oct 05 2009 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.1-0.rc20.1mdv2010.0
+ Revision: 454239
- P7 to let compillation work because buf_printf() function
- RC20, it fixes several bugs

* Thu Jul 23 2009 Frederik Himpe <fhimpe@mandriva.org> 2.1-0.rc19.1mdv2010.0
+ Revision: 399003
- Update to new version 2.1-rc19

  + Christophe Fergeau <cfergeau@mandriva.com>
    - fix -Wformat warnings

* Sat Nov 22 2008 Frederik Himpe <fhimpe@mandriva.org> 2.1-0.rc15.1mdv2009.1
+ Revision: 305704
- Update to new version 2.1-rc15, drop UDP ssl/tls negotiation patch
  integrated upstream in 2.1-rc11

* Mon Nov 17 2008 Funda Wang <fwang@mandriva.org> 2.1-0.rc10.3mdv2009.1
+ Revision: 303875
- BR libpkcs11-helper-devel (bug#45813)

* Thu Sep 18 2008 Frederik Himpe <fhimpe@mandriva.org> 2.1-0.rc10.2mdv2009.0
+ Revision: 285720
- Fix license
- Add 2.1-rc11 patch fixing TLS/SSL negotiations if UDP packets
  are dropped

* Sat Sep 13 2008 Frederik Himpe <fhimpe@mandriva.org> 2.1-0.rc10.1mdv2009.0
+ Revision: 284564
- Update to 2.1 RC 10

* Tue Aug 05 2008 Frederik Himpe <fhimpe@mandriva.org> 2.1-0.rc9.1mdv2009.0
+ Revision: 263636
- Update to new version 2.1-rc9: fixes security problem CVE-2008-3459

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Mon May 19 2008 David Walluck <walluck@mandriva.org> 2.1-0.rc7.1mdv2009.0
+ Revision: 209098
- BuildRequires: re2c for ldap support
- 2.1_rc7
- auth_ldap 2.0.3

* Wed Jan 23 2008 Thierry Vignaud <tv@mandriva.org> 2.0.9-4mdv2008.1
+ Revision: 157261
- rebuild with fixed %%serverbuild macro

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

* Mon Dec 24 2007 Oden Eriksson <oeriksson@mandriva.com> 2.0.9-3mdv2008.1
+ Revision: 137470
- rebuilt against openldap-2.4.7 libs

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Wed Jun 27 2007 Andreas Hasenack <andreas@mandriva.com> 2.0.9-2mdv2008.0
+ Revision: 45193
- using serverbuild macro (-fstack-protector-all)

* Wed May 09 2007 Olivier Thauvin <nanardon@mandriva.org> 2.0.9-1mdv2008.0
+ Revision: 25697
- 2.0.9
- don't bzip2 source, add gpg sig into source pkg


* Thu Mar 15 2007 Olivier Thauvin <nanardon@mandriva.org> 2.0.7-4mdv2007.1
+ Revision: 144578
- rebuild

* Wed Jan 31 2007 Olivier Thauvin <nanardon@mandriva.org> 2.1-0.rc2.2mdv2007.1
+ Revision: 115645
- merge patch no-user/group from 2.1 branches (Yves-Gwenael Bourhis)

* Sun Aug 13 2006 Olivier Thauvin <nanardon@mandriva.org> 2.0.7-2mdv2007.0
+ Revision: 55734
- rebuild
- add openvpn

* Thu Apr 20 2006 Olivier Thauvin <nanardon@mandriva.org> 2.0.7-1mdk
- 2.0.7

* Mon Jan 09 2006 Olivier Blin <oblin@mandriva.com> 2.0.5-5mdk
- fix typo in initscript

* Mon Jan 09 2006 Olivier Blin <oblin@mandriva.com> 2.0.5-4mdk
- convert parallel init to LSB

* Tue Jan 03 2006 Per Øyvind Karlsen <pkarlsen@mandriva.com> 2.0.5-3mdk
- add parallel init support
- fix executable-marked-as-config-file
- be sure to wipe out buildroot at the beginning of %%install
- don't ship copyright notice as the package is GPL (see common-licenses)

* Sun Nov 13 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.5-2mdk
- rebuilt against openssl-0.9.8a

* Thu Nov 10 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0.5-1mdk
- 2.0.5

* Mon Oct 17 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0.2-1mdk
- 2.0.2

* Wed Aug 31 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.1-2mdk
- rebuilt against new openldap-2.3.6 libs

* Thu Aug 25 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0.1-1mdk
- 2.0.1
- ldap patch version 1.0.1
- remove patch3, fix upstream

* Sun Jul 10 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0-4mdk
- rebuild for lzo (#16777)
- add patch3: fix -lzo2 calls

* Thu Jun 23 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0-3mdk
- rebuild for lzo (Thanks Michar)

* Thu May 12 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0-2mdk
- Request by Luis Daniel Lucio Quiroz <dlucio@okay.com.mx>
  - add native plugin
  - add openvpn-auth-ldap plugin (except for amd64)

* Wed Apr 20 2005 Olivier Thauvin <nanardon@mandriva.org> 2.0-1mdk
- 2.0 final

* Fri Apr 08 2005 Olivier Thauvin <thauvin@aerov.jussieu.fr> 2.0-0.rc20.1mdk
- 2.0-rc20

* Thu Jan 13 2005 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 1.6.0-2mdk
- rebuild
- cosmetics

* Tue Jun 01 2004 Per �yvind Karlsen <peroyvind@linux-mandrake.com> 1.6.0-1mdk
- 1.6.0
- fix buildrequires (lib64..)
- drop GPL license file, there's no reason for us to ship such common
  license files in packages, as we ship them with the common-licenses package!

