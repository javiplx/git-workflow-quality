
set -e

TESTNAME=multimerged

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


TMPREPO=testrepo_multimerged_$RANDOM

rm -rf multimerged.git
mkdir multimerged.git
cd multimerged.git
git init --bare
cd ..


git clone multimerged.git ${TMPREPO}
cd ${TMPREPO}

make_commits master 1

make_commits branch1 2

make_commits master 3 2

make_merge master branch1

make_commits master 4 4

make_commits branch1 3 3

git push origin master branch1

cd ..
rm -rf ${TMPREPO}

