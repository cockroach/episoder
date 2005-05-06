#!/bin/sh
# episoder installer v0.2.2, http://tools.desire.ch/episoder/
#
# Copyright (c) 2004, 2005 Stefan Ott. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

install() {
    EPISODER_HOME=$BASE_DIR/share/episoder
    MAN_DIR=$BASE_DIR/share/man/man.1

    mkdir -p $EPISODER_HOME
    mkdir -p $BASE_DIR/bin
    mkdir -p $MAN_DIR

    cp scripts/*sh $EPISODER_HOME
    cp plugins/* $EPISODER_HOME
    cp scripts/episoder $BASE_DIR/bin
    cp episoder.1 $MAN_DIR/
}

case "$1" in
    install)
	if [ -z "$2" ]; then
	    BASE_DIR=/usr/local
	else
	    BASE_DIR=$2
	fi
	install
	;;
    help|*)
	echo Usage: $0 install [base_dir]
    	;;
esac
