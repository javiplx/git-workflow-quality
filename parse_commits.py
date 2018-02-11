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

class commit :

    def __init__ ( self , sha , author , comimtter , message ) :
        self.sha = sha
        self.author = author
        self.committer = committer
        self.message = message.replace('"', '&quot;' )

    def set_params ( self , line ) :
        self.author_date = line[0]
        self.committer_date = line[1]
        self.parent = None
        self.parents = ()
        self.branch = ''
        if len(line) > 2 :
            self.parent = commits[line[2]]
            if len(line) > 3 :
                self.parents = line[3].split()
                if len(self.parents) > 1 :
                    raise Exception( "Octopus merges on %s from %s not handled" % ( self.sha , ", ".join(self.parents) ) )
        else : # This trick is required to assign a branch to the initial commit and should be revised
            self.set_branch('master')
        self.child = None
        self.forks = []

    def set_branch ( self , branch ) :
        if self.branch :
            raise Exception( "cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch ) )
        self.branch = branch

    def set_child ( self , sha ) :
        if self.branch == commits[sha].branch :
            if self.child :
                raise Exception( "cannot assign %s as child of %s, already parent of %s" % ( sha , self.sha , self.child ) )
            self.child = sha
        else :
            self.forks.append(sha)

    def __str__ ( self ) :
        parents = " ".join(self.parents)
        forks = " ".join(self.forks)
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( self.branch[:20] , self.sha , self.parent.sha , self.child , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( self.branch[:20] , self.sha , '<None>' , self.child , parents , forks , self.message )


commits = {}

fd = open("messages.list")
line = fd.readline()
while line[:-1] :
    sha , author , committer , message = line[:-1].split(None, 3)
    commits[sha] = commit( sha , author , committer , message )
    line = fd.readline()
fd.close()

order = []

fd = sys.stdin
line = fd.readline()
while line[:-1] :
    sha , params = line[:-1].split(None, 1)
    commits[sha].set_params(params.split(None, 4))
    if commits[sha].parent and commits[sha].parent.sha not in order :
        raise Exception( "Incorrect input ordering" )
    order.append( sha )
    line = fd.readline()
fd.close()


branchnames = dict([ (branches[key],key) for key in branches ])

for branch in 'master' , 'develop' :
    c = commits[branchnames[branch]]
    while c :
        if c.branch :
            break
        c.set_branch(branch)
        c = commits[c.parent.sha]

for branch in branchnames.keys() :
    c = commits[branchnames[branch]]
    while c :
        if c.branch :
            break
        c.set_branch(branch)
        c = commits[c.parent.sha]


order.reverse()

for sha in order :
    c = commits[sha]
    if not c.parents or commits[c.parents[0]].branch : continue
    idx = c.message.find( "Merge branch '" )
    if idx != -1 :
        branch_name = c.message[idx+14:]
        idx = branch_name.find( "'" )
        branch = branch_name[:idx] + " (?)"
        c = commits[c.parents[0]]
        if branch not in branchnames :
            branchnames[branch] = c.sha
            branches[c.sha] = branch
            while c :
                if not c.parent or c.branch :
                    break
                c.set_branch(branch)
                c = commits[c.parent.sha]
        else :
            idx = branch_name.find( "' into '" )
            branch_name = branch_name[idx+8:]
            idx = branch_name.find( "'" )
            branch = branch_name[:idx] + " (?)"
            if branch not in branchnames :
                branchnames[branch] = c.sha
                branches[c.sha] = branch
                while c :
                    if c.branch :
                        break
                    c.set_branch(branch)
                    c = commits[c.parent.sha]

count = 0
for sha in order :
    c = commits[sha]
    if not c.branch :
        count += 1
        branch = "removed_%s" % count
        branchnames[branch] = c.sha
        while c :
            if c.branch :
                break
            c.set_branch(branch)
            c = commits[c.parent.sha]

order.reverse()


for sha in order : # child assignment
    c = commits[sha]
    if c.parent :
        commits[c.parent.sha].set_child( sha )
        for parent in c.parents :
            commits[parent].set_child( sha )


origins = []
for c in commits.values() :
    if not c.parent :
        origins.append( c )


shown_branches = []
def forward_plot ( c , pending , fd=sys.stdout ) :
    first = True
    if not c.branch in shown_branches :
        shown_branches.append( c.branch )
    while c.child :
        if c.parents :
            sha = c.parents[0]
            if commits[sha].branch in shown_branches :
                first = True
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s | %s"});\n' % ( js_varname(commits[sha].branch) , js_varname(c.branch) , c.sha , commits[sha].branch , c.message ) )
            else :
                return
        else :
            if first :
                first = False
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
            elif c.forks :
                first = True
                fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
        new_branches = False
        for sha in c.forks :
            if not commits[sha].branch in shown_branches :
                new_branches = True
                fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(commits[sha].branch) , js_branch( commits[sha].branch , len(shown_branches) ) ) )
            if commits[sha] not in pending :
                pending.append( commits[sha] )
        if new_branches :
            first = True
            fd.write( '%s.checkout();\n' % js_varname(c.branch) )
        c = commits[c.child]
    if c.parents :
        sha = c.parents[0]
        if commits[sha].branch in shown_branches :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(commits[sha].branch) , js_varname(c.branch) , c.sha , c.message ) )
    else :
        fd.write( 'gitgraph.commit({sha1:"%s", message:"%s"});\n' % ( c.sha , c.message ) )
    for sha in c.forks :
        if not commits[sha].branch in shown_branches :
            fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(commits[sha].branch) , js_branch( commits[sha].branch , len(shown_branches) ) ) )
        if commits[sha] not in pending :
            pending.append( commits[sha] )

def chrono_plot ( sha_list , fd=sys.stdout) :
    """Assumes that commits are properly ordered, so just the commit list is given"""
    current_branch = None
    shown_branches = []
    first = True
    for sha in sha_list :
        c = commits[sha]
        if not c.branch in shown_branches :
            shown_branches.append( c.branch )
            if c.parent and commits[c.parent.sha].branch != current_branch :
                fd.write( '%s.checkout();\n' % js_varname(commits[c.parent.sha].branch) )
            fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(c.branch) , js_branch( c.branch , len(shown_branches) ) ) )
            first = True
        elif current_branch != c.branch :
            fd.write( '%s.checkout();\n' % js_varname(c.branch) )
            first = True
        current_branch = c.branch
        if not c.parents :
            if first or c.forks :
                first = False
                fd.write( 'gitgraph.commit({sha1: "%s", message: "%s"});\n' % ( c.sha , c.message ) )
        else :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( js_varname(commits[c.parents[0]].branch) , js_varname(c.branch) , c.sha , c.message ) )
            if not commits[c.parents[0]].child :
                if commits[c.parents[0]].branch in shown_branches :
                    shown_branches.remove( commits[c.parents[0]].branch )

def js_varname ( var ) :
    return var.replace(' (?)','').replace('/', '_slash_' ).replace('-', '_dash_').replace('.', '_dot_').replace(' ', '_white_').replace(':', '_colon_')

def js_branch ( name , count=2 ) :
    json = 'name:"%s"' % name
    if name == 'master' :
        json += ", column:0"
    elif name == 'develop' :
        json += ", column:1"
    else :
        json += ", column:%d" % count
    return json

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

""" )


for origin in origins :
    fd.write( 'var %s = gitgraph.branch({%s});\n' % ( js_varname(origins[0].branch) , js_branch(origins[0].branch) ) )

while origins :
    commit = origins.pop(0)
    forward_plot(commit, origins, fd)

fd.close()

