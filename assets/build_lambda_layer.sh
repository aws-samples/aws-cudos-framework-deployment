#!/bin/bash
# This script builids a lambda layer. Outpits relative path of layer zip.
export CID_VERSION=$(python3 -c "from cid import _version;print(_version.__version__)")
rm -rf build

function get_hash {
    find ./cid -type f -exec md5sum {} + | md5sum | awk '{print $1}'
}

function build_layer {
    echo 'Building a layer'
    mkdir -p ./python
    python3 -m pip install . -t ./python
    zip -qr cid-$CID_VERSION.zip ./python
    ls -l cid-$CID_VERSION.zip
    rm -rf ./python
}

# Check if code has been changed
previous_hash=$(cat cid-$CID_VERSION.hash)
actual_hash=$(get_hash)
if [ "$actual_hash" == "$previous_hash" ] && [ -e "cid-$CID_VERSION.zip" ]; then
    echo "No changes in code. Reuse existing zip." 1>&2
else
    build_layer 1>&2
    echo $actual_hash > cid-$CID_VERSION.hash
fi

ls cid-$CID_VERSION.zip