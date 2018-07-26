#!/bin/bash

set -e

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

  [ $min -eq 0 -a $branch != master ] && git checkout -b $branch $source
  [ $min -eq 0 -a $branch = master ] || git checkout $branch

  for n in $( seq $min $max ) ; do
    echo $n >> $branch.txt
    git add $branch.txt
    git commit -m "$branch $n"
    sleep 2
    done
  sleep 2
  }

make_merge() {
  source=$1
  target=$2

  git checkout $target
  git merge --no-ff $source -m "Merge branch $source into $target"

  sleep 2
  }


TMPREPO=testrepo_${TESTNAME}_${RANDOM}

rm -rf ${TESTNAME}.git
mkdir ${TESTNAME}.git
cd ${TESTNAME}.git
git init --bare
cd ..


git clone ${TESTNAME}.git ${TMPREPO}
cd ${TMPREPO}

. ../${TESTNAME}.repo

cd ..
rm -rf ${TMPREPO}

