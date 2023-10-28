#!/bin/bash

## https://python-gtk-3-tutorial.readthedocs.io/en/latest/install.html

sudo apt update
sudo apt install -y libgirepository1.0-dev 
sudo apt install -y gcc libcairo2-dev
sudo apt install -y pkg-config
sudo apt install -y python3-dev 
sudo apt install -y gir1.2-gtk-3.0

pip3 install wheel

conda install -c conda-forge gtk3
conda install -c conda-forge pygobject
export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH


# jhbuild build pygobject
# sudo apt install jhbuild
# jhbuild sysdeps --install pygobject
# jhbuild sysdeps --install gtk+-3

