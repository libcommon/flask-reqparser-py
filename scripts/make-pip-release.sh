#!/usr/bin/env sh
## make-pip-release.sh
##
## Copyright (c) 2019 libcommon
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

if [ $# -lt 1 ]
then
    echo "usage: make-pip-release.sh version"
    echo
    echo "Prepare source files for release and generate wheel file."
    echo "NOTE: Should _not_ be run in a virtual environment"
    echo
    echo "positional arguments:"
    echo "version   Release version (should follow semver)"
    echo
    exit 1
fi

PACKAGE_VERSION="${1}"
shift 1
PACKAGE_NAME="lc_flask_reqparser"
PACKAGE_DESCRIPTION="Python library for the Flask framework to parse request parameters using the argparse library."
PACKAGE_CODE_URL="https:\/\/github.com\/libcommon\/flask-reqparser-py"
PACKAGE_MIN_PYTHON_VERSION="3.6"

BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
TAG_NAME="v${PACKAGE_VERSION}"

# Ensure package directory exists
if ! [ -d "${PACKAGE_NAME}" ]
then
    echo "::: ERROR: Package directory ${PACKAGE_NAME} does not exist"
    exit 1
fi

# Remove tests from source file(s)
./scripts/remove-tests.sh "${PACKAGE_NAME}"

echo "::: INFO: Generating Setuptools setup.py file"
cat ./scripts/setup.py | \
    sed \
        -e "s/PACKAGE_NAME/${PACKAGE_NAME}/g" \
        -e "s/PACKAGE_VERSION/${PACKAGE_VERSION}/g" \
        -e "s/PACKAGE_SHORT_DESCRIPTION/${PACKAGE_SHORT_DESCRIPTION}/g" \
        -e "s/PACKAGE_CODE_URL/${PACKAGE_CODE_URL}/g" \
        -e "s/PACKAGE_MIN_PYTHON_VERSION/${PACKAGE_MIN_PYTHON_VERSION}/g" > setup.py
chmod 744 setup.py

echo "::: INFO: Generating source distribution to dist directory"
python3 setup.py sdist

echo "::: INFO: Generating 'pure' wheel file to dist directory"
python3 setup.py bdist_wheel

# Remove development files
./scripts/remove-dev-files.sh

# Add the distribution files to source control
echo "::: INFO: Adding distribution files to source control"
git add setup.py dist/

# Commit changes
echo "::: INFO: Committing release"
git commit -am "Made release ${PACKAGE_VERSION}"

# Create local tag for release
echo "::: INFO: Creating local tag for release (${TAG_NAME})"
git tag -m "Release ${TAG_NAME}" -a "${TAG_NAME}"

# Push commit and tag to remote
echo "::: INFO: Pushing release to remote"
git push origin "${BRANCH_NAME}"
git push origin "${TAG_NAME}"
