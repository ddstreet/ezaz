Name:          python-ezaz
Summary:       Eazy Azure CLI
Version:       0.0.1
Release:       %autorelease
License:       GPLv3
URL:           https://github.com/ddstreet/ezaz
Source0:       ezaz-%{version}.tar.gz

BuildRequires: python3-devel

BuildArch:     noarch

%define _description Eazy interface to the Azure CLI. This is significantly eazier, but also significantly less comprehensive.

%description
%_description

%package -n python3-ezaz
Summary:        %{summary}
%description -n python3-ezaz
%_description

%prep
%autosetup -p1 -n ezaz-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files ezaz

%files -n python3-ezaz -f %{pyproject_files}
%license LICENSE
%doc README
%{_bindir}/ezaz

%changelog
%autochangelog
