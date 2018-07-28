#!/bin/bash

set -e

SLEEP=Y
if [ "$1" = --no-sleep ] ; then
  SLEEP=N
  shift
  fi

if [ $# -ne 1 ] ; then
  echo "Usage : ${0##*/} testname"
  exit
  fi

TESTNAME=$1

if [ ! -e ${TESTNAME}.repo ] ; then
  echo "Test file '${TESTNAME}.repo' not found"
  exit
  fi

make_commits() {
  branch=$1
  max=${2:-5}
  min=${3:-0}
  source=${4:-master}

  [ $min -eq 0 -a $branch != master ] && git checkout --quiet -b $branch $source
  [ $min -eq 0 -a $branch = master ] || git checkout --quiet $branch

  for n in $( seq $min $max ) ; do
    echo $n >> $branch.txt
    git add $branch.txt
    git commit --quiet -m "$branch $n"
    [ "$SLEEP" = "N" ] || sleep 2
    done
  [ "$SLEEP" = "N" ] || sleep 2
  }

make_merge() {
  source=$1
  target=$2

  git checkout --quiet $target
  git merge --quiet --no-ff $source -m "Merge branch $source into $target"

  [ "$SLEEP" = "N" ] || sleep 2
  }


TMPREPO=testrepo_${TESTNAME}_${RANDOM}

rm -rf ${TESTNAME}.git
mkdir ${TESTNAME}.git
cd ${TESTNAME}.git
git init --quiet --bare
cd ..


git clone --quiet ${TESTNAME}.git ${TMPREPO}
cd ${TMPREPO}

. ../${TESTNAME}.repo

cd ..
rm -rf ${TMPREPO}

