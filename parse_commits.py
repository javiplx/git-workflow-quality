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
        self.child = None
        self.forks = []

    def set_branch ( self , branch ) :
        if self.branch :
            raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def set_child ( self , sha ) :
        if self.child :
            raise Exception( "cannot assign %s as child of %s, already parent of %s" % ( sha , self.sha , self.child ) )
        self.child = sha

    def __str__ ( self ) :
        parents = " ".join(self.parents)
        if self.parent :
            return "%s %s %s | %s , %s" % ( self.sha , self.parent.sha , parents , self.child , " ".join(self.forks) )
        return "%s None %s | %s , %s" % ( self.sha , parents , self.child , " ".join(self.forks) )


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


origins = []
for c in commits.values() :
    if not c.parent :
        c.set_branch( 'master' )
        origins.append( c )
    else :
        commits[c.parent.sha].forks.append( c.sha )
    if not c.parents :
        continue
    if len(c.parents) == 1 and commits[c.parents[0]].branch == c.branch :
        commits[c.parents[0]].set_child( c.sha )
    else :
        for sha in c.parents :
            commits[sha].forks.append( c.sha )

if len(origins) != 1 :
    raise Exception( "Multiple initial commits not supported" )


for c in commits.values() :
    if c.child or not c.forks : continue
    if len(c.forks) == 1 and commits[c.forks[0]].branch == c.branch :
        c.set_child( c.forks.pop() )
    else :
        childs = [ commits[f].sha for f in c.forks if commits[f].branch == c.branch ]
        if len(childs) == 1 :
            c.set_child( childs[0] )
            c.forks.pop(c.forks.index(c.child))
        else :
            if not branches.get(c.sha)  and not otherbranches.get(c.branch) :
                raise Exception( "Unidentified commit at the end of a branch" )


branchnames = dict([ (branches[key],key) for key in branches ])

# Iterate over all branches showing the life line of each one. The last one listed is the first one in history
show_main = True

for branch in 'master' , 'develop' :
    if show_main : print "branch", branch
    c = commits[branchnames.pop(branch)]
    while c :
        if c.branch != branch :
            break
        if show_main :
            if c.parents :
                for parent in c.parents :
                    print "%s %s" % ( c.sha , commits[parent].branch )
                    #print "%s %s | %s" % ( c.sha , commits[parent].branch , " ".join(c.forks) )
            else :
                print "%s %s" % ( c.sha , " ".join(c.parents) )
                #print "%s %s : %s" % ( c.sha , " ".join(c.parents) , " ".join(c.forks) )
        if branch == 'master' and not c.parent :
            break
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
                print "%s %s" % ( c.sha , commits[parent].branch )
                #print "%s %s | %s" % ( c.sha , commits[parent].branch , " ".join(c.forks) )
        else :
            print "%s %s" % ( c.sha , " ".join(c.parents) )
            #print "%s %s : %s" % ( c.sha , " ".join(c.parents) , " ".join(c.forks) )
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
                print "%s %s" % ( c.sha , commits[parent].branch )
                #print "%s %s | %s" % ( c.sha , commits[parent].branch , " ".join(c.forks) )
        else :
            print "%s %s" % ( c.sha , " ".join(c.parents) )
            #print "%s %s : %s" % ( c.sha , " ".join(c.parents) , " ".join(c.forks) )
        c = commits[c.parent.sha]
    print


for c in origins :
    while c.child :
        print c.branch, c.sha , c.child
        c = commits[c.child]
    print c.branch, c.sha , "FINAL COMMIT"

