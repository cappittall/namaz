#!/bin/bash
sudo apt update
sudo apt install -y libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
pip3 install wheel

git clone https://gitlab.gnome.org/GNOME/pygobject.git
sudo apt install meson ninja-build libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
