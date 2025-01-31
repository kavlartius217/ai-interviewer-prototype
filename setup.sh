#!/bin/bash

# Set SQLite version
SQLITE_VERSION=3410200  # This is SQLite 3.41.2 (or use the latest available)

# Create a directory for the custom installation
mkdir -p $HOME/sqlite
cd $HOME/sqlite

# Download and extract SQLite
wget https://www.sqlite.org/2023/sqlite-autoconf-${SQLITE_VERSION}.tar.gz
tar xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz
cd sqlite-autoconf-${SQLITE_VERSION}

# Compile SQLite
./configure --prefix=$HOME/sqlite
make -j$(nproc)
make install

# Set environment variables for the new SQLite version
export PATH=$HOME/sqlite/bin:$PATH
export LD_LIBRARY_PATH=$HOME/sqlite/lib:$LD_LIBRARY_PATH

# Verify the installed version
sqlite3 --version
