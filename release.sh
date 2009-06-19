#!/bin/bash

TARGETDIR=__RELEASE

rm -rf ${TARGETDIR}

VERSION=$( sed 's/.*"\(.*\)"/\1/' <( grep ^version= pyepisoder/episoder.py ) )
echo Preparing release ${VERSION}

mkdir -p ${TARGETDIR}/episoder-${VERSION}

cp -r [!_]* ${TARGETDIR}/episoder-${VERSION}
rm -f ${TARGETDIR}/episoder-${VERSION}/release.sh
rm -rf ${TARGETDIR}/episoder-${VERSION}/test
find ${TARGETDIR} -type d -name '.svn' | xargs rm -rf

cd ${TARGETDIR}
tar cf episoder-${VERSION}.tar episoder-${VERSION}
gzip episoder-${VERSION}.tar

mkdir tgz
cp episoder-${VERSION}.tar.gz tgz
