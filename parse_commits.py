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
        self.branch = branch.replace('/', '_slash_' )

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
    c = commits[otherbranches[branch]]
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


branchnames = dict([ (branches[key],key) for key in branches ])
for branch in branchnames.keys() : # + otherbranches.keys() :
    print "branch", branch
    for c in commits.values() :
        if c.branch != branch : continue
        if not c.parent :
            print "INITIAL", c.sha
        elif commits[c.parent.sha].branch != c.branch :
            print "FORK   ", c.sha
            print "   from", commits[c.parent.sha].branch , commits[c.parent.sha].sha
        if not c.child :
            print "FINAL  ", c.sha
    print


fd = open("messages.list")
line = fd.readline()
while line[:-1] :
    sha , author , committer , message = line[:-1].split(None, 3)
    commits[sha].message = message.replace('"', '&quot;' )
    line = fd.readline()
fd.close()


shown_branches = [ 'master' ]
def dump ( c , pending , fd=sys.stdout ) :
    fd.write( "// BEGIN %s BRANCH\n" % c.branch )
    fd.write( '%s.checkout();\n' % c.branch )
    first = True
    while c.child :
        if c.parents :
            sha = c.parents[0]
            if commits[sha].branch in shown_branches :
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s | %s"});\n' % ( commits[sha].branch , c.branch , c.sha , commits[sha].branch , c.message ) )
            else :
                fd.write( "// MERGE COMMIT : %s\n" % c.parents )
                fd.write( "//       %s : %s\n" % ( commits[sha].branch , commits[sha] ) )
                fd.write( "// END   %s BRANCH\n\n" % c.branch )
                return
        elif c.forks or first :
                first = False
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
        for sha in c.forks :
            if not commits[sha].branch in shown_branches :
                fd.write( 'var %s = gitgraph.branch("%s");\n' % ( commits[sha].branch , commits[sha].branch ) )
                shown_branches.append( commits[sha].branch )
            pending.append( commits[sha] )
        if c.forks :
            fd.write( '%s.checkout();\n' % c.branch )
        c = commits[c.child]
    fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
    fd.write( "// FINAL COMMIT\n" )
    fd.write( "// END   %s BRANCH\n\n" % c.branch )

fd = open( "commits.js" , 'w' )

fd.write( """
var myTemplateConfig = {
  colors: [ "#9993FF", "#47E8D4", "#6BDB52", "#F85BB5", "#FFA657", "#F85BB5" ],
  branch: {
    lineWidth: 2,
    spacingX: 40,
    showLabel: true, // display branch names on graph
    labelFont: "normal 10pt Arial",
    labelRotation: 0
  },
  commit: {
    spacingY: -30,
    dot: {
      size: 6,
      lineDash: [2]
    },
    message: {
      font: "normal 12pt Arial"
    },
    tooltipHTMLFormatter: function (commit) {
      return "<b>" + commit.sha1 + "</b>" + ": " + commit.message;
    }
  },
  arrow: {
    size: 6,
    offset: 1
  }
};

var myTemplate = new GitGraph.Template(myTemplateConfig);

var config = {
  template: myTemplate, // "blackarrow",
  reverseArrow: false,
  orientation: "horizontal",
  mode: "compact"
};

var gitgraph = new GitGraph(config);

var %s = gitgraph.branch("%s");

""" % ( origins[0].branch , origins[0].branch ) )

while origins :
    commit = origins.pop(0)
    dump(commit, origins, fd)

fd.close()

