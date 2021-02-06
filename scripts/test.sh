#!/bin/bash
set -euxo pipefail

# set nocasematch option
shopt -s nocasematch

if [[ $OS =~ ^WIN ]]; then
    # XTRA_OPT="-x --count 10"
    XTRA_OPT="--count 1"
fi

poetry run pytest -s -n auto --cov=cruft/ --cov=tests --cov-report=term-missing ${@-} --cov-report xml --cov-report html $XTRA_OPT

./scripts/lint.sh
