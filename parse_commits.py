#!/usr/bin/env python

import sys

branches = {}

fd = open("branches.list")
line = fd.readline()
while line[:-1] :
    if not line[:-1].endswith('HEAD') :
        items = line[:-1].split(None, 2)
        branches[items[0]] = items[1]
    line = fd.readline()
fd.close()


commits = {}
merges = {}

class commit :

    def __init__ ( self , line ) :
        self.sha = line[0]
        self.author_date = line[1]
        self.committer_date = line[2]
        self.parent = None
        self.parents = ()
        if len(line) > 3 :
            self.parent = commits[line[3]]
            if len(line) > 4 :
                self.parents = line[4].split()
                if len(self.parents) > 1 :
                    raise Exception( "Octopus merges on %s from %s not handled" % ( self.sha , ", ".join(self.parents) ) )
                for parent in self.parents :
                    merges[parent] = True
        self.branch = None
        self.forks = []

    def set_branch ( self , branch ) :
        if self.branch :
            raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def __str__ ( self ) :
        parents = " ".join(self.parents)
        if self.parent :
            return "%s %s %s | %s" % ( self.sha , self.parent.sha , parents , " ".join(self.forks) )
        return "%s None %s | %s" % ( self.sha , parents , " ".join(self.forks) )


fd = sys.stdin
line = fd.readline()
while line[:-1] :
    c = commit(line[:-1].split(None, 5))
    commits[c.sha] = c
    line = fd.readline()
fd.close()


branchnames = dict([ (branches[key],key) for key in branches ])

for branch in 'master' , 'develop' :
    c = commits[branchnames.pop(branch)]
    while c :
        if not c.parent or c.branch :
            break
        c.set_branch(branch)
        c = commits[c.parent.sha]

for branch in branchnames.keys() :
    c = commits[branchnames.pop(branch)]
    while c :
        if not c.parent or c.branch :
            break
        c.set_branch(branch)
        c = commits[c.parent.sha]


otherbranches = {}
count = 0
for sha in merges :
    if not commits[sha].branch :
        count += 1
        branch = "removed_%s" % count
        otherbranches[branch] = sha
        c = commits[sha]
        while c :
            if not c.parent or c.branch :
                break
            c.set_branch(branch)
            c = commits[c.parent.sha]


for c in commits.values() :
    if not c.parents :
        continue
    for sha in c.parents :
        commits[sha].forks.append( c.sha )


branchnames = dict([ (branches[key],key) for key in branches ])

# Iterate over all branches showing the life line of each one. The last one listed is the first one in history
show_main = False

for branch in 'master' , 'develop' :
    if show_main : print "branch", branch
    c = commits[branchnames.pop(branch)]
    while c :
        if c.branch != branch :
            break
        if show_main :
            if c.parents :
                for parent in c.parents :
                    print "%s %s | %s" % ( c.sha , commits[parents].branch , " ".join(c.forks) )
            else :
                print "%s %s : %s" % ( c.sha , " ".join(c.parents) , " ".join(c.forks) )
        c = commits[c.parent.sha]
    if show_main : print

for branch in branchnames.keys() :
    print "branch", branch
    c = commits[branchnames.pop(branch)]
    while c :
        if c.branch != branch :
            break
        if c.parents :
            for parent in c.parents :
                print "%s %s | %s" % ( c.sha , commits[parent].branch , " ".join(c.forks) )
        else :
            print "%s %s : %s" % ( c.sha , " ".join(c.parents) , " ".join(c.forks) )
        c = commits[c.parent.sha]
    print

for branch in otherbranches.keys() :
    print "branch", branch
    c = commits[otherbranches.pop(branch)]
    while c :
        if c.branch != branch :
            break
        if c.parents :
            for parent in c.parents :
                print "%s %s | %s" % ( c.sha , commits[parent].branch , " ".join(c.forks) )
        else :
            print "%s %s : %s" % ( c.sha , " ".join(c.parents) , " ".join(c.forks) )
        c = commits[c.parent.sha]
    print


