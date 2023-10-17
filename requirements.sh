#!/bin/bash

sudo apt-get install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade

sudo apt install jhbuild
jhbuild sysdeps --install pygobject
jhbuild sysdeps --install gtk+-3