#!/bin/bash

TARGETDIR=__RELEASE

rm -rf ${TARGETDIR}

VERSION=$( sed 's/.*"\(.*\)"/\1/' <( grep ^version= pyepisoder/episoder.py ) )
echo Preparing release ${VERSION}

mkdir -p ${TARGETDIR}/episoder-${VERSION}

cp -r [!_]* ${TARGETDIR}/episoder-${VERSION}
#rm -rf $TARGETDIR/episoder-$VERSION/test
rm -f ${TARGETDIR}/episoder-${VERSION}/release.sh
find ${TARGETDIR} -type d -name '.svn' | xargs rm -rf

cd ${TARGETDIR}
tar cf episoder-${VERSION}.tar episoder-${VERSION}
gzip episoder-${VERSION}.tar

mkdir tgz
cp episoder-${VERSION}.tar.gz tgz
#mv episoder-${VERSION}.tar.gz episoder_$VERSION.orig.tar.gz

#cd episoder-$VERSION
#mkdir debian
#cp -r ../../../episoder-debian-files/* debian
#rm -rf debian/CVS
#debuild -kF01DFE92

#cd ..
#rm -rf episoder-0.4.3

#mkdir deb
#mv epi* deb
