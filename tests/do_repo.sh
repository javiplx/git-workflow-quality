
set -e


make_commits() {
  branch=$1
  max=${2:-5}
  min=${3:-0}

  [ $min -eq 0 -a $branch != master ] && git checkout -b $branch master
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
  git merge $source -m "Merge branch $source into $target"

  sleep 2
  }


TMPREPO=testrepo_$RANDOM

rm -rf testrepo.git
mkdir testrepo.git
cd testrepo.git
git init --bare
cd ..


git clone testrepo.git ${TMPREPO}
cd ${TMPREPO}

make_commits master 1

make_commits branch1 1

make_commits master 2 2

make_commits branch2 2

make_commits master 4 3

make_commits branch3 1

make_commits master 5 5

make_merge branch2 branch1

make_commits branch1 2 2

make_commits branch2 4 4

make_merge branch1 branch3

make_commits branch3 2 2

make_merge branch2 master

make_commits branch3 2 2

make_commits master 6 6

git push origin master branch1 branch2 branch3

cd ..
rm -rf ${TMPREPO}

