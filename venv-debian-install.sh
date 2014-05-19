#! /bin/sh
cat requirements.apt | xargs sudo apt-get install -y
pip install -re requirements.txt
