#!/bin/bash
python3 -m pip install virtualenv
if [ -d .venv ] ; then
    rm -rf .venv
fi

python3 -m virtualenv -p python3 .venv
.venv/bin/pip install -r requirements.txt
