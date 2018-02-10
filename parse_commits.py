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
                for parent in self.parents :
                    merges[parent] = True
        self.branch = None

    def set_branch ( self , branch ) :
        if self.branch :
            raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def __str__ ( self ) :
        parents = " ".join(self.parents)
        if self.parent :
            return "%s %s %s" % ( self.sha , self.parent.sha , parents )
        return "%s None %s" % ( self.sha , parents )


fd = sys.stdin
line = fd.readline()
while line[:-1] :
    c = commit(line[:-1].split(None, 5))
    commits[c.sha] = c
    line = fd.readline()
fd.close()


# Iterate over all branches showing the life line of each one. The last one listed is the first one in history
show_main = False

branchnames = dict([ (branches[key],key) for key in branches ])

for branch in 'master' , 'develop' :
    if show_main : print "branch", branch
    sha = branchnames.pop(branch)
    c = commits[sha]
    while c :
        if not c.parent or c.branch :
            break
        if show_main :
            parents = " ".join(c.parents)
            if commits.has_key(parents) :
                print "%s %s" % ( c.sha , commits[parents].branch or parents )
            else :
                print "%s %s" % ( c.sha , parents )
        c.set_branch(branch)
        sha = c.parent.sha
        c = commits[sha]
    if show_main : print

for branch in branchnames.keys() :
    print "branch", branch
    sha = branchnames.pop(branch)
    c = commits[sha]
    while c :
        if not c.parent or c.branch :
            break
        parents = " ".join(c.parents)
        if commits.has_key(parents) :
            print "%s %s" % ( c.sha , commits[parents].branch or parents )
        else :
            print "%s %s" % ( c.sha , parents )
        c.set_branch(branch)
        sha = c.parent.sha
        c = commits[sha]
    print


count = 0
for sha in merges :
    if not commits[sha].branch :
        count += 1
        branch = "removed_%s" % count
        print "branch", branch
        c = commits[sha]
        while c :
            if not c.parent or c.branch :
                break
            parents = " ".join(c.parents)
            if commits.has_key(parents) :
                print "%s %s" % ( c.sha , commits[parents].branch or parents )
            else :
                print "%s %s" % ( c.sha , parents )
            c.set_branch(branch)
            sha = c.parent.sha
            c = commits[sha]
        print

