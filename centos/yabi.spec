%define version 7.1.10
%define unmangled_version 7.1.10
%define release 2
%define webapps /usr/local/webapps
%define webappname yabiadmin
%define shellname yabish

# Variables used for yabiadmin django app
%define installdir %{webapps}/%{webappname}
%define buildinstalldir %{buildroot}/%{installdir}
%define settingsdir %{buildinstalldir}/defaultsettings
%define logdir %{buildroot}/var/log/%{webappname}
%define scratchdir %{buildroot}/var/lib/%{webappname}/scratch
%define storedir %{buildroot}/var/lib/%{webappname}/store
%define mediadir %{buildroot}/var/lib/%{webappname}/media
%define staticdir %{buildinstalldir}/static

# Variables for yabish
%define shinstalldir /usr/local/yabish
%define shbuildinstalldir %{buildroot}/%{shinstalldir}


# Turn off brp-python-bytecompile because it makes it difficult to generate the file list
# We still byte compile everything by passing in -O paramaters to python
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

Summary: yabiadmin django webapp, celery backend and yabi shell utility
Name: yabi
Version: %{version}
Release: %{release}
License: GNU GPL v3
Group: Applications/Internet
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: x86_64
Vendor: Centre for Comparative Genomics <web@ccg.murdoch.edu.au>
BuildRequires: python-setuptools openssl-devel python-devel libxslt-devel libxml2-devel
Requires: openssl python-setuptools python
Requires(pre): shadow-utils

%description 
Test.

%package admin
Summary: yabiadmin Django web application
Group: Applications/Internet
Requires: httpd mod_wsgi libxml2 libxslt

%description admin
Django web application implementing the web front end for Yabi.

%package shell
Summary: yabi shell
Group: Applications/Internet

%description shell
Yabi command line shell


%install

for directory in "%{settingsdir} %{staticdir} %{logdir} %{storedir} %{scratchdir} %{mediadir}"; do
    mkdir -p $directory;
done;

# Create python prefixes for packages
mkdir -p %{buildinstalldir}/{lib,bin,include}
mkdir -p %{shbuildinstalldir}/{lib,bin,include}

if ! test -e $CCGSOURCEDIR/build-number-.txt; then
    echo '#Generated by spec file' > build-number.txt
    export TZ=Australia/Perth
    DATE=`date`
    echo "build.timestamp=\"$DATE\"" >> build-number.txt
fi
echo "build.user=\"$USER\"" >> build-number.txt
echo "build.host=\"$HOSTNAME\"" >> build-number.txt
cp build-number.txt %{buildinstalldir}/

# yabi-admin
cd $CCGSOURCEDIR/yabiadmin
export PYTHONPATH=%{buildinstalldir}/lib
python /usr/bin/easy_install -O1 --prefix %{buildinstalldir} --install-dir %{buildinstalldir}/lib .

# Create settings symlink so we can run collectstatic with the default settings
touch %{settingsdir}/__init__.py
ln -fs ..`find %{buildinstalldir} -path "*/%{webappname}/settings.py" | sed s:^%{buildinstalldir}::` %{settingsdir}/%{webappname}.py

# Create symlinks under install directory to real persistent data directories
ln -fs /var/log/%{webappname} %{buildinstalldir}/log
ln -fs /var/lib/%{webappname}/scratch %{buildinstalldir}/scratch
ln -fs /var/lib/%{webappname}/store %{buildinstalldir}/store
ln -fs /var/lib/%{webappname}/media %{buildinstalldir}/media

# Install WSGI configuration into httpd/conf.d
install -D ../centos/%{webappname}.ccg %{buildroot}/etc/httpd/conf.d/%{webappname}.ccg
install -D ../centos/django.wsgi %{buildinstalldir}/django.wsgi
install -m 0755 -D ../centos/%{webappname}-manage.py %{buildroot}/%{_bindir}/%{webappname}

# Install yabiadmin's celeryd init script system wide
install -m 0755 -D init_scripts/centos/celeryd.init %{buildroot}/etc/init.d/celeryd
install -m 0644 -D init_scripts/centos/celeryd.sysconfig %{buildroot}/etc/sysconfig/celeryd

# Fix paths for stuff in bin/
sed -i '3i import sys; sys.path.insert(1, "${installdir}/lib")' %{buildinstalldir}/bin/*

# Correct hardcoded shebangs
find %{buildinstalldir} -name '*.py' -type f | xargs sed -i 's:^#!/usr/local/bin/python:#!/usr/bin/python:'
find %{buildinstalldir} -name '*.py' -type f | xargs sed -i 's:^#!/usr/local/python:#!/usr/bin/python:'

# yabi-shell
cd $CCGSOURCEDIR/yabish
export PYTHONPATH=%{shbuildinstalldir}/lib
python /usr/bin/easy_install -O1 --prefix %{shbuildinstalldir} --install-dir %{shbuildinstalldir}/lib .

sed -i '3i import sys; sys.path.insert(1, "%{shinstalldir}/lib")' %{shbuildinstalldir}/bin/*

# Correct hardcoded shebangs
find %{shbuildinstalldir} -name '*.py' -type f | xargs sed -i 's:^#!/usr/local/bin/python:#!/usr/bin/python:'
find %{shbuildinstalldir} -name '*.py' -type f | xargs sed -i 's:^#!/usr/local/python:#!/usr/bin/python:'


%post admin
rm -rf %{installdir}/static/*
yabiadmin collectstatic --noinput > /dev/null
# Remove root-owned logged files just created by collectstatic
rm -rf /var/log/%{webappname}/*
# Touch the wsgi file to get the app reloaded by mod_wsgi
touch ${installdir}/django.wsgi

%preun admin
if [ "$1" = "0" ]; then
    # Nuke staticfiles if not upgrading
    rm -rf %{installdir}/static/*
fi

%files admin
%defattr(-,apache,apache,-)
/etc/httpd/conf.d/*
%{_bindir}/%{webappname}
%attr(-,apache,,apache) %{webapps}/%{webappname}
%attr(-,apache,,apache) /var/log/%{webappname}
%attr(-,apache,,apache) /var/lib/%{webappname}
%attr(-,root,,root) /etc/init.d/celeryd
%attr(-,root,,root) /etc/sysconfig/celeryd

%files shell
%defattr(-,root,root,-)
%{shinstalldir}
