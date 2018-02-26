
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


TMPREPO=testrepo_$RANDOM

rm -rf testrepo.git
mkdir testrepo.git
cd testrepo.git
git init --bare
cd ..


git clone testrepo.git ${TMPREPO}
cd ${TMPREPO}

make_commits master 1

make_commits develop 1

make_commits master 2 2

make_commits develop 2 2

make_commits topic 1 0 develop

make_merge topic master

make_merge topic develop

make_commits master 3 3

make_commits develop 3 3

git push origin master develop topic

cd ..
rm -rf ${TMPREPO}
