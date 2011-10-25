Name:           scala
Version:        2.8.1
%define fullversion %{version}.final
Release:        2
Summary:        A hybrid functional/object-oriented language for the JVM
BuildArch:      noarch
Group:          Development/Java
# License was confirmed to be standard BSD by fedora-legal
# https://www.redhat.com/archives/fedora-legal-list/2007-December/msg00012.html
License:        BSD
URL:            http://www.scala-lang.org/

# Source
Source0:        http://www.scala-lang.org/downloads/distrib/files/scala-%{fullversion}-sources.tgz

Source21:       scala.keys
Source22:       scala.mime
Source23:       scala-mime-info.xml
Source24:       scala.ant.d

Patch1:         scala-2.8.1-use_system_jline.patch
Patch2:         scala-2.8.0-tooltemplate.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%define jline_jar /usr/share/java/jline.jar

# Force build with openjdk/icedtea because gij is horribly slow and I haven't
# been successful at integrating aot compilation with the build process
BuildRequires:  java-devel-openjdk >= 0:1.6.0
BuildRequires:  ant
BuildRequires:  ant-contrib
BuildRequires:  ant-nodeps
BuildRequires:  jline
BuildRequires:  jpackage-utils
BuildRequires:  shtool
Requires:       java
Requires:       jline
Requires:       jpackage-utils
Requires:       %{jline_jar}

%description
Scala is a general purpose programming language designed to express common
programming patterns in a concise, elegant, and type-safe way. It smoothly
integrates features of object-oriented and functional languages. It is also
fully interoperable with Java.

%package apidoc
Summary:        Documentation for the Scala programming language
Group:          Development/Java

%description apidoc
Scala is a general purpose programming language for the JVM that blends
object-oriented and functional programming. This package provides
reference and API documentation for the Scala programming language.

%package -n ant-scala
Summary:        Development files for Scala
Group:          Development/Java
Requires:       scala = %{version}-%{release}, ant

%description -n ant-scala
Scala is a general purpose programming language for the JVM that blends
object-oriented and functional programming. This package enables support for
the scala ant tasks.

%package examples
Summary:        Examples for the Scala programming language
Group:          Development/Java
# Otherwise it will pick up some perl module
Autoprov:       0
Requires:       scala = %{version}-%{release}

%description examples
Scala is a general purpose programming language for the JVM that blends
object-oriented and functional programming. This package contains examples for
the Scala programming language

%define scaladir %{_datadir}/scala

%prep
%setup -q -n scala-%{fullversion}-sources
%patch1 -p1 -b .systemjline
%patch2 -p1 -b .tooltemplate
# remove all jar files except scala-library and scala-compiler needed
# for bootstrap
find . -not \( -name 'scala-library.jar' -or -name 'scala-compiler.jar' -or -name 'msil.jar' -or -name 'fjbg.jar' -or -name 'forkjoin.jar' \) -and -name '*.jar' | xargs rm -f
find . -name '*.dll' -or -name '*.so' -or -name '*.exe' | xargs rm -f

##
# Copy system jline over bundled library
##

ln -s %{jline_jar} lib/jline.jar

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

%define java_home %{_jvmdir}/java-openjdk

# rebuild internal libraries and bootstrap compiler
%ant -Dversion.number=%{fullversion} -Djava6.home=%{_jvmdir}/java-1.6.0 newlibs newforkjoin locker.clean pack.done starr.done locker.clean || exit 1

# build distribution with newly built compiler
%ant -Dversion.number=%{fullversion} newlibs libs.clean locker.clean docs.clean dist.done || exit 1

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{_mandir}/man1 $RPM_BUILD_ROOT%{_bindir}
for prog in scaladoc fsc scala scalac scalap; do
        install -p -m 755 dists/scala-%{fullversion}/bin/$prog $RPM_BUILD_ROOT%{_bindir}
        install -p -m 644 dists/scala-%{fullversion}/man/man1/$prog.1 $RPM_BUILD_ROOT%{_mandir}/man1
done

install -p -m 755 -d $RPM_BUILD_ROOT%{_javadir}/scala
install -p -m 755 -d $RPM_BUILD_ROOT%{scaladir}/lib
for libname in scala-compiler scala-dbc scala-library scala-partest scala-swing scalap ; do
        install -m 644 dists/scala-%{fullversion}/lib/$libname.jar $RPM_BUILD_ROOT%{_javadir}/scala/$libname-%{fullversion}.jar
        ln -s $libname-%{fullversion}.jar $RPM_BUILD_ROOT%{_javadir}/scala/$libname.jar
        shtool mkln -s $RPM_BUILD_ROOT%{_javadir}/scala/$libname.jar $RPM_BUILD_ROOT%{scaladir}/lib
done
shtool mkln -s $RPM_BUILD_ROOT%{jline_jar} $RPM_BUILD_ROOT%{scaladir}/lib

install -d $RPM_BUILD_ROOT%{_sysconfdir}/ant.d
install -p -m 644 %{SOURCE24} $RPM_BUILD_ROOT%{_sysconfdir}/ant.d/scala

cp -pr dists/scala-%{fullversion}/doc/scala-devel-docs/examples $RPM_BUILD_ROOT%{_datadir}/scala/

install -d $RPM_BUILD_ROOT%{_datadir}/mime-info
install -p -m 644 %{SOURCE21} %{SOURCE22} $RPM_BUILD_ROOT%{_datadir}/mime-info/

install -d $RPM_BUILD_ROOT%{_datadir}/mime/packages/
install -p -m 644 %{SOURCE23} $RPM_BUILD_ROOT%{_datadir}/mime/packages/

sed -i -e 's,@JAVADIR@,%{_javadir},g' -e 's,@DATADIR@,%{_datadir},g' $RPM_BUILD_ROOT%{_bindir}/*

%post
update-mime-database %{_datadir}/mime &> /dev/null || :

%postun
update-mime-database %{_datadir}/mime &> /dev/null || :

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/*
%{_javadir}/scala
%dir %{_datadir}/scala
%{_datadir}/scala/lib
%{_mandir}/man1/*
%doc dists/scala-%{fullversion}/doc/LICENSE
%doc dists/scala-%{fullversion}/doc/README
%{_datadir}/mime-info/*
%{_datadir}/mime/packages/*

%files -n ant-scala
%defattr(-,root,root,-)
# Following is plain config because the ant task classpath could change from
# release to release
%config %{_sysconfdir}/ant.d/*

%files apidoc
%defattr(-,root,root,-)
%doc dists/scala-%{fullversion}/doc/scala-devel-docs/api
%doc dists/scala-%{fullversion}/doc/LICENSE

%files examples
%defattr(-,root,root,-)
%{_datadir}/scala/examples

