#!/usr/bin/python3

import pygit2

class Repo ( dict ) :
    def __init__ ( self , path='.' ) :
        super().__init__()
        self.repo =  pygit2.Repository(path)
        self.branches = {}
    def branch ( self , branch_name ) :
        if branch_name not in self.branches :
            self.branches[branch_name] = Branch(self.repo.references[branch_name], self)
        return self.branches[branch_name]

class Branch ( list ) : # Debiera heredar de _pygit2.Reference
    def __init__ ( self , reference , repo ) :
        super().__init__()
        self.me = reference
        self.repo = repo
    def append ( self , commit ) :
        super().append(commit)
        self.repo[commit.id] = Commit(commit, self.me)
        return commit
    def walk ( self , show=False ) :
        walker = self.repo.repo.walk(self.me.target, pygit2.GIT_SORT_TOPOLOGICAL)
        walker.simplify_first_parent()
        for commit in walker :
            if commit.id in self.repo :
                if show :
                    print("created from %s"%commit.oid)
                break
            new = self.append(commit)
            if show :
                print(new.id)
                if commit.parents[1:] :
                    print('    merge from %s'%commit.parent_ids[1])
                    if self.repo.repo.merge_commits(commit.parent_ids[0], commit.parent_ids[1]).conflicts :
                        print('        conflicted')
        return commit

class Commit :

    def __init__ ( self , commit , branch ) :
        self.commit = commit
        self.branch = branch

    def __str__ ( self ) :
        return str(self.commit.id)


myRepo = Repo()

primary = 'refs/heads/master'
c = myRepo.branch(primary).walk()
print('Branch : %s'%primary)
print('# commits', len(myRepo.branches[primary]))
print("")

for branch in myRepo.repo.references :
    if branch == 'refs/remotes/origin/HEAD' or branch in myRepo.branches :
        continue
    print('Branch : %s'%branch)
    c = myRepo.branch(branch).walk() # show=True)

    if len(myRepo.branches[branch]) :
        print('# commits', len(myRepo.branches[branch]))
        print('real origin', myRepo[c.id])
        print('merge base ', myRepo.repo.merge_base(myRepo.branch('refs/heads/master').me.target, myRepo.branch('refs/heads/bugfix/complex_branch_concatenation').me.target))
    else :
        print('-duplicated-')

    print('')


import sys

sys.exit()

branch = 'refs/heads/bugfix/complex_branch_concatenation'
c = myRepo.branch(branch).walk(True)

print('')

print('# commits', len(myRepo.branches[branch]))
print('real origin', myRepo[c.id])

print('')
print('merge base ', myRepo.repo.merge_base(myRepo.branch('refs/heads/master').me.target, myRepo.branch('refs/heads/bugfix/complex_branch_concatenation').me.target))

print('')

for j in myRepo.repo.references :
    if j == 'refs/remotes/origin/HEAD' or j in myRepo.branches :
        continue
    print(j)

