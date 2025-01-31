#!/bin/bash

# Download and install SQLite 3.39.0 (or latest stable version)
mkdir -p $HOME/sqlite3
cd $HOME/sqlite3
wget https://www.sqlite.org/2022/sqlite-autoconf-3390000.tar.gz
tar xzf sqlite-autoconf-3390000.tar.gz
cd sqlite-autoconf-3390000
./configure --prefix=$HOME/sqlite3
make -j4
make install

# Add new SQLite to the PATH
export PATH=$HOME/sqlite3/bin:$PATH
export LD_LIBRARY_PATH=$HOME/sqlite3/lib:$LD_LIBRARY_PATH

# Verify the installed version
sqlite3 --version
