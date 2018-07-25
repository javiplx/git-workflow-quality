
set -e


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


TMPREPO=testrepo_multitarget_$RANDOM

rm -rf multitarget.git
mkdir multitarget.git
cd multitarget.git
git init --bare
cd ..


git clone multitarget.git ${TMPREPO}
cd ${TMPREPO}

make_commits master 1

make_commits branch1 0

make_commits master 2 2

make_commits branch2 0

make_commits master 3 3

make_commits branch3 1 0

make_merge branch3 branch2

make_commits master 5 3

make_commits branch1 1 1

make_commits branch3 2 2

make_merge branch3 branch1

make_commits branch3 3 3

make_commits branch2 3 2

make_commits master 5 5

make_commits branch1 2 2

make_merge branch3 master

make_commits master 6 6

git push origin master branch1 branch2 branch3

cd ..
rm -rf ${TMPREPO}

