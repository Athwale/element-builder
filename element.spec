%global _hardened_build 1
# For some reason the package wants to provide some libraries that we do not want.
%global __provides_exclude ^((lib.*\\.so.*))$
%global __requires_exclude ^((lib.*\\.so.*))$

# Element seems to be using js and we do not need the extra unwanted provides.
# https://docs.fedoraproject.org/en-US/packaging-guidelines/Node.js/
%{?nodejs_default_filter}

Name: element
Summary: Element messenger
# Version (Set this to one of the versions of element from https://github.com/vector-im/element-web/tags)
%define v_major 1.10
%define v_minor 4
Version: %{v_major}.%{v_minor} 
# Release (Custom number for packages built by us, we are just using 1 all the time)
Release: 1%{?dist}
# Same license as the Element repoi.
License: ASL 2.0 
URL: https://element.io/
ExclusiveArch: x86_64
BuildArch: x86_64

# Do not create debuginfo package.
%define debug_package %{nil}
# Used for file and directory names.
%define element_name matrix-element

Source0: https://github.com/vector-im/element-desktop/archive/v%{version}/element-desktop-%{version}.tar.gz
Source1: https://github.com/vector-im/element-web/archive/v%{version}/element-web-%{version}.tar.gz
# Rpmbuild command looks for compressed sources in the SOURCES dir. We dynamically create this archive from the files in that directory and freshly downloaded olm tarball.
Source2: ./SOURCES/element-fedora.tar.gz

# Packages required for building:
BuildRequires: cmake curl cargo desktop-file-utils git gcc-c++ libappstream-glib libxcrypt-compat libsecret-devel nodejs npm nodejs-yarn python pigz rust sqlcipher-devel tcl openssl-devel

# Packages required for running when installed:
Requires: sqlcipher

# To dump all defined macros for inspection use percent dump and exit 1.
# Has to be here, otherwise messes up all the define directives.
%description
Element is a free and open-source software instant messaging client implementing the Matrix protocol.

%prep
# Prepare source files for building.
# %prep = %{_topdir}/BUILD
# Extract source tarballs into {_builddir}/element/
mkdir element
%setup -q -T -D -a 0 -n element
%setup -q -T -D -a 1 -n element
%setup -q -T -D -a 2 -n element

cd %{_builddir}/element/
# Copy downloaded olm tarball into place.
mkdir -p element-web-%{version}/depends/sources
mv element-fedora/*.tgz element-web-%{version}/depends/sources/

%build
# Build works only on Fedora > 30.
# Test fedora version.
%if 0%{?fedora:1}
  echo "Fedora version: %{fedora}"
  %if 0%{?fedora} <= 30
    echo "Can not build on this OS version"
    exit 1
  %endif
%endif

# Build element-web
# TODO remove this and try without it, workaround for ERR_OSSL_EVP_UNSUPPORTED
export NODE_OPTIONS=--openssl-legacy-provider

cd %{_builddir}/element/element-web-%{version}
yarn install --openssl_fips=''

yarn run build
# Without this element does not start and shows a config error.
install -D -m644 -p config.sample.json webapp/config.json

# Build element-desktop
cd %{_builddir}/element/element-desktop-%{version}
yarn install 
yarn run build:native
yarn run build
./node_modules/.bin/asar pack %{_builddir}/element/element-web-%{version}/webapp dist/linux-unpacked/resources/webapp.asar

%install
# /usr/share/matrix-element
%define dir_install %{_datadir}/%{element_name}

# This prepares folder/file structure in the buildroot which is then packaged.
install -d -m755 -p %{buildroot}%{_bindir}
install -d %{buildroot}%{dir_install}
install -d %{buildroot}%{_datadir}/applications

cp -a element-desktop-%{version}/dist/linux-unpacked/* %{buildroot}%{dir_install}
# /bin/element -> /usr/share/matrix-element/element-desktop makes it possible to run element from command line.
ln -s %{dir_install}/%{name}-desktop %{buildroot}%{_bindir}/%{name}

install -D -m644 -p element-fedora/icons/Adwaita-%{element_name}.png %{buildroot}%{_datadir}/icons/Adwaita/64x64/apps/%{element_name}.png
install -D -m644 -p element-fedora/icons/%{element_name}.desktop %{buildroot}%{_datadir}/applications/%{element_name}.desktop

%files
# The list of files that will be installed in the end user’s system.
%defattr(-,root,root,-)
%license element-desktop-%{version}/LICENSE

# /usr/share/matrix-element
%{dir_install}

%{_bindir}/%{name}
%{_datadir}/applications/%{element_name}.desktop
%{_datadir}/icons/Adwaita/64x64/apps/%{element_name}.png

%post
umask 007
/sbin/ldconfig > /dev/null 2>&1
/usr/bin/update-desktop-database &> /dev/null || :

%postun
umask 007
/sbin/ldconfig > /dev/null 2>&1
/usr/bin/update-desktop-database &> /dev/null || :

%changelog
* Tue May 23 2022 Test Builder <test@gmail.com>
Test build
