#!/bin/sh

DIR=$(dirname ${0})

echo -n "Installing ..."

python ${DIR}/setup.py build >/dev/null &&
python ${DIR}/setup.py install >/dev/null &&
python ${DIR}/setup.py clean >/dev/null &&

rm -rf ${DIR}/build >/dev/null &&

echo " Done!" &&

exit 0 || exit 1
