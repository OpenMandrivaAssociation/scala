Name:		scala
Version:	2.8.1
%define fullversion %{version}.final
Release:	3
Summary:	A hybrid functional/object-oriented language for the JVM
BuildArch:	noarch
Group:		Development/Java
# License was confirmed to be standard BSD by fedora-legal
# https://www.redhat.com/archives/fedora-legal-list/2007-December/msg00012.html
License:	BSD
URL:		http://www.scala-lang.org/
Source0:	http://www.scala-lang.org/downloads/distrib/files/%{name}-%{fullversion}-sources.tgz
Source21:	scala.keys
Source22:	scala.mime
Source23:	scala-mime-info.xml
Source24:	scala.ant.d
Patch1:		scala-2.8.1-use_system_jline.patch
Patch2:		scala-2.8.0-tooltemplate.patch

# Force build with openjdk/icedtea because gij is horribly slow and I haven't
# been successful at integrating aot compilation with the build process
BuildRequires:	java-devel >= 1.6.0
BuildRequires:	ant
BuildRequires:	ant-contrib
BuildRequires:	ant-nodeps
BuildRequires:	jline >= 2.8.1
BuildRequires:	jpackage-utils
Requires:	java
Requires:	jline
Requires:	jpackage-utils

%description
Scala is a general purpose programming language designed to express common
programming patterns in a concise, elegant, and type-safe way. It smoothly
integrates features of object-oriented and functional languages. It is also
fully interoperable with Java.

%package	apidoc
Summary:	Documentation for the Scala programming language
Group:		Books/Computer books
Requires:	%{name} = %{EVRD}

%description apidoc
Scala is a general purpose programming language for the JVM that blends
object-oriented and functional programming. This package provides
reference and API documentation for the Scala programming language.

%package -n	ant-%{name}
Summary:	Development files for Scala
Group:		Development/Java
Requires:	%{name} = %{EVRD} ant

%description -n	ant-%{name}
Scala is a general purpose programming language for the JVM that blends
object-oriented and functional programming. This package enables support for
the %{name} ant tasks.

%package	examples
Summary:	Examples for the Scala programming language
Group:		Development/Java
Requires:	%{name} = %{EVRD}

%description	examples
Scala is a general purpose programming language for the JVM that blends
object-oriented and functional programming. This package contains examples for
the Scala programming language

%prep
%setup -q -n %{name}-%{fullversion}-sources
%patch1 -p1 -b .systemjline
%patch2 -p1 -b .tooltemplate
# remove all jar files except scala-library and scala-compiler needed
# for bootstrap
find . -not \( -name '%{name}-library.jar' -or -name '%{name}-compiler.jar' -or -name 'msil.jar' -or -name 'fjbg.jar' -or -name 'forkjoin.jar' \) -and -name '*.jar' | xargs rm -f
find . -name '*.dll' -or -name '*.so' -or -name '*.exe' | xargs rm -f

##
# Copy system jline over bundled library
##

ln -s %{_javadir}/jline.jar lib/jline.jar

%build
# Scala is written in itself and therefore requires boot-strapping from an
# initial binary build. The dist target of the ant build is a staged build
# that makes sure that the package bootstraps properly. The bundled binary
# compiler is used to compile the source code. That binary is used to 
# compile the source code again. That binary is used to compile the code
# again and the output is checked that it is exactly the same.  This makes
# sure that the build is repeatable and that the bootstrap compiler could
# be replaced with this one and successfully build the whole distribution
# again

##
# Rebuild Bundled jline
##

#(
#  cd src/jline
#  mkdir -p .m2/repository
#  mvn-jpp -Dmaven.repo.local=$PWD/.m2/repository package
#  cp target/jline-0.9.95-SNAPSHOT.jar ../../lib/jline.jar
#)

# rebuild internal libraries and bootstrap compiler
%ant -Dversion.number=%{fullversion} -Djava6.home=%{_jvmdir}/java-1.6.0 newlibs newforkjoin locker.clean pack.done starr.done locker.clean || exit 1

# build distribution with newly built compiler
%ant -Dversion.number=%{fullversion} newlibs libs.clean locker.clean docs.clean dist.done || exit 1

%install
for prog in %{name}doc fsc %{name} %{name}c %{name}p; do
	install -m755 dists/%{name}-%{fullversion}/bin/$prog -D %{buildroot}%{_bindir}/$prog
	install -m644 dists/%{name}-%{fullversion}/man/man1/$prog.1 -D %{buildroot}%{_mandir}/man1/$prog.1
done

install -d %{buildroot}%{_datadir}/%{name}/lib
for libname in %{name}-compiler %{name}-dbc %{name}-library %{name}-partest %{name}-swing %{name}p ; do
	install -m644 dists/%{name}-%{fullversion}/lib/$libname.jar -D %{buildroot}%{_javadir}/%{name}/$libname-%{fullversion}.jar
	jar -i %{buildroot}%{_javadir}/%{name}/$libname-%{fullversion}.jar
	ln -s $libname-%{fullversion}.jar %{buildroot}%{_javadir}/%{name}/$libname.jar
	ln -s %{_javadir}/%{name}/$libname.jar %{buildroot}%{_datadir}/%{name}/lib
done
ln -s %{_javadir}/jline.jar %{buildroot}%{_datadir}/%{name}/lib

cp -pr dists/%{name}-%{fullversion}/doc/%{name}-devel-docs/examples %{buildroot}%{_datadir}/%{name}/

install -m644 %{SOURCE21} -D %{buildroot}%{_datadir}/mime-info/%{name}.keys
install -m644 %{SOURCE22} -D %{buildroot}%{_datadir}/mime-info/%{name}.mime
install -m644 %{SOURCE24} -D %{buildroot}%{_sysconfdir}/ant.d/%{name}
install -m644 %{SOURCE23} -D %{buildroot}%{_datadir}/mime/packages/%{name}-mime-info.xml

sed -e 's,@JAVADIR@,%{_javadir},g' -e 's,@DATADIR@,%{_datadir},g' -i %{buildroot}%{_bindir}/*

%files
%doc dists/%{name}-%{fullversion}/doc/LICENSE
%doc dists/%{name}-%{fullversion}/doc/README
%{_bindir}/*
%{_javadir}/%{name}
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/lib
%{_mandir}/man1/*
%{_datadir}/mime-info/*
%{_datadir}/mime/packages/*

%files -n ant-%{name}
# Following is plain config because the ant task classpath could change from
# release to release
%config %{_sysconfdir}/ant.d/%{name}

%files apidoc
%doc dists/%{name}-%{fullversion}/doc/%{name}-devel-docs/api
%doc dists/%{name}-%{fullversion}/doc/LICENSE

%files examples
%{_datadir}/%{name}/examples

