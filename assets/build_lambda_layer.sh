#!/bin/bash
# This script builids a lambda layer. Outpits relative path of layer zip.
export CID_VERSION=$(python3 -c "from cid import _version;print(_version.__version__)")
rm -rf build

function build_layer {
    echo 'Building a layer'
    mkdir -p ./python
    python3 -m pip install . -t ./python
    zip -qr cid-$CID_VERSION.zip ./python
    ls -l cid-$CID_VERSION.zip
    rm -rf ./python
}

build_layer 1>&2

ls cid-$CID_VERSION.zip


