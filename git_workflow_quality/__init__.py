
import gitgraphjs
import gitnetwork

import subprocess
import re
import os


class Commit :

    def __init__ ( self , sha , author , committer , message ) :
        self.sha = sha
        self.author = author
        self.committer = committer
        self.message = message.replace('"', '&quot;' )
        self.parent = None
        self.parents = ()
        self.branch = None
        self.child = None
        self.forks = []
        self.rendered = False

    def set_branch ( self , branch , child=None ) :
        if branch <= self.branch :
            # self.branch has a higher weight respect to branch
            return
        if self.branch and not branch.is_primary() :
            print "WARNING : cannot assign %s to %s, already owned by %s" % ( branch.pretty() , self.sha , self.branch.pretty() )
            return
        branch.append( self )
        if child :
            self.set_child( child )

    def set_child ( self , child ) :
        if self.child and self.child != child :
            self.forks.append( self.child )
            if child in self.forks :
                self.forks.remove( child )
        self.child = child

    def add_child ( self , child ) :
        if not self.child or self.child == child :
            self.child = child
        elif child not in self.forks :
            self.forks.append( child )

    def get_parents ( self , full=True ) :
        parents = []
        if self.parent :
          if full or self.branch != self.parent.branch :
            parents.append( self.parent )
        parents.extend( self.parents )
        return parents

    def get_childs ( self , full=True ) :
        childs = []
        if self.child :
          if full or self.branch != self.child.branch :
            childs.append( self.child )
        childs.extend( self.forks )
        return childs

    def render ( self , fd , render_merge=True , switch_parents=False ) :
        if self.parents and render_merge :
            if switch_parents :
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( self.parent.branch.as_var() , self.branch.as_var() , self.sha , self.message ) )
            else :
                fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( self.parents[0].branch.as_var() , self.branch.as_var() , self.sha , self.message ) )
        else :
            fd.write( '%s.commit({sha1:"%s", message:"%s"});\n' % ( self.branch.as_var() , self.sha , self.message ) )
        self.rendered = True

    def __str__ ( self ) :
        parents = " ".join([p.sha for p in self.parents])
        child =  self.child and self.child.sha or '<None>'
        forks = " ".join([f.sha for f in self.forks])
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , self.parent.sha , child , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , '<None>' , child , parents , forks , self.message )


class Branch ( list ) :

    primary = ('master', 'develop')

    def __init__ ( self , branchname , orphan=False ) :
        self.name = branchname
        self.orphan = orphan
        self.rendered = False
        list.__init__( self )

    def __hash__ ( self ) :
        return self.name.__hash__()

    def commits ( self ) :
        return [c for c in list.__iter__(self) if not c.parents]

    def merges ( self ) :
        return [c for c in list.__iter__(self) if c.parents]

    def stats ( self ) :
        return len(self), len(self.commits()), len(self.merges())

    def matches ( self , other ) :
        return self.name.startswith( other.name ) or other.name.startswith( self.name )

    def begin ( self ) :
        begins = [ c for c in list.__iter__(self) if not c.parent ]
        if not begins :
            begins = [ c for c in list.__iter__(self) if c.parent.branch != self ]
        assert len(begins) == 1
        return begins[0]

    def end ( self ) :
        ends = [ c for c in list.__iter__(self) if not c.child ]
        if not ends :
            ends = [ c for c in list.__iter__(self) if c.child.branch != self ]
            if len(ends) != 1 :
                # This just searches end on direct childs, and will not detect indirect merge-backs
                ends = [ end for end in ends if not end.child or not end.child.branch.end().child or end.child.branch.end().child.branch != self ]
        assert len(ends) == 1
        return ends[0]

    def source ( self ) :
        source = self.begin().parent
        if not source or not source.branch :
            return '<Initial>'
        return source.branch.name

    def target ( self ) :
        target = self.end().child
        if not target or not target.branch :
            return '<Final>'
        return target.branch.name

    def is_primary ( self ) :
        return self.name in Branch.primary

    def is_release ( self ) :
        return self.name.startswith('release')

    def is_orphan ( self ) :
        return self.orphan

    def __le__ ( self , other ) :
        if not other :
            return False
        if self == other :
            return False
        if self.is_primary() and other.is_primary() :
            return Branch.primary.index(other.name) < Branch.primary.index(self.name)
        if other.is_primary() :
            return True
        return False

    def ancestry ( self , commit ) :
        if commit.branch != self : return
        child = commit
        commit = commit.parent
        while commit :
            if commit.branch :
                if not self.is_primary() :
                    commit.add_child( child )
                    break
                elif self <= commit.branch :
                    commit.add_child( child )
                    break
            commit.set_branch( self , child )
            child = commit
            commit = commit.parent

    def append ( self , commit ) :
        if commit.branch :
            commit.branch.remove( commit )
        list.append( self , commit )
        commit.branch = self

    def commit_list ( self ) :
        this = self.begin()
        while this.child and this.child.branch == self :
            yield this
            this = this.child
        yield this
        raise StopIteration()

    def backward_commits ( self ) :
        this = self.end()
        while this.parent and this.parent.branch == self :
            yield this
            this = this.parent
        yield this
        raise StopIteration()

    def __str__ ( self ) :
        return self.name

    def pretty ( self ) :
        if len(str(self)) > 40 :
            return str(self)[:40] + " ..."
        return str(self)

    def relations ( self ) :
        sources = []
        targets = []
        for c in self :
            for parent in c.parents :
                sources.append( parent )
            for child in c.forks :
                targets.append( child )
        return sources , targets

    def gitgraph ( self , filename="branch.html" ) :
        shown_branches = [ self ]

        fd = open( filename , 'w' )
        fd.write( gitgraphjs.gitgraph_head )

        initials , finals = [] , []

        for commit in self.begin().get_parents() :
            if commit.branch not in shown_branches :
                shown_branches.append( commit.branch )
                commit.branch.render( fd , shown_branches=shown_branches , force=True )
                initials.append( commit )

        for commit in self.end().get_childs() :
            # Only merges are handled here. Child branches will be created on loop
            # If branch is already shown, we don't need to write any commit
            if commit.branch and commit.parents and commit.branch not in shown_branches :
                shown_branches.append( commit.branch )
                commit.branch.render( fd , shown_branches=shown_branches , force=True )
                # For proper rendering, we must choose a parent in the same branch, which means render as parent of himself as fallback
                if commit.parent.branch == commit.branch :
                    finals.append( commit.parent )
                elif commit.parents[0].branch == commit.branch :
                    finals.append( commit.parents[0] )
                else :
                    finals.append( commit )

        sources , targets = self.relations()
        for source in sources :
            if source.branch in [ target.branch for target in targets ] :
                if not source.parents and source.parent.branch == self :
                    continue
            if source.branch and source.branch not in shown_branches :
                shown_branches.append( source.branch )
                source.branch.render( fd , shown_branches=shown_branches , force=True )
                initials.append ( source )

        for target in targets :
            # Only merges are handled here. Child branches will be created on loop
            # If branch is already shown, we don't need to write any commit
            if target.branch and target.parents and target.branch not in shown_branches :
                shown_branches.append( target.branch )
                target.branch.render( fd , shown_branches=shown_branches , force=True )
                # For proper rendering, we must choose a parent in the same branch, which means render as parent of himself as fallback
                if target.parent.branch == target.branch :
                    finals.append( target.parent )
                elif target.parents[0].branch == target.branch :
                    finals.append( target.parents[0] )
                else :
                    finals.append( target )

        # All commits rendered after branch creation to avoid a single original commit
        # As we don't care about their history, we just render them as plain commits
        for commit in initials + finals :
            commit.render( fd , False )

        if self.begin().parent :
            self.render( fd , self.begin().parent.branch , shown_branches , True )
        else :
            self.render( fd , shown_branches=shown_branches , force=True )

        for c in self.commit_list() :
            # Ensure that ancestry line is clean
            assert c == self.end() or c.child.branch == self
            c.render( fd )
            for commit in c.forks :
                if commit.branch :
                    if commit.branch not in shown_branches :
                        shown_branches.append( commit.branch )
                        commit.branch.render( fd , self , shown_branches , True )
                    if commit.parents and commit.parent.branch == self :
                        commit.render( fd , switch_parents=True )
                    else :
                        commit.render( fd )
                    fd.write( "%s.checkout();\n" % self.as_var() )

        if c.child :
            if c.child.branch :
              if c.child.parents and c.child.parent.branch == self :
                c.child.render( fd , switch_parents=True )
              else :
                c.child.render( fd )
        else :
            print "WARNING : No end commit for %s" % self

        fd.write( gitgraphjs.gitgraph_tail )
        fd.close()

    def dotlabel ( self , fd=os.sys.stdout ) :
        fd.write( '  %s [ label="%s" ];\n' % ( self.as_var() , self.name.replace(' (2)', '') ) )

    def digraph ( self , fd=os.sys.stdout ) :
        if self.source() != '<Initial>' and self.begin().parent.forks :
            fd.write( "  %s -> %s;\n" % ( self.begin().parent.branch.as_var() , self.as_var() ) )
        sources , targets = self.relations()
        for parent in sources :
          if parent.branch and parent != parent.branch.end() :
            fd.write( "  %s -> %s;\n" % ( parent.branch.as_var() , self.as_var() ) )
        for child in targets :
          if child.branch and child != child.branch.begin() :
            fd.write( "  %s -> %s;\n" % ( self.as_var() , child.branch.as_var() ) )
        if self.target() != '<Final>' :
            fd.write( "  %s -> %s;\n" % ( self.as_var() , self.end().child.branch.as_var() ) )

    def report ( self , branches=False ) :
        output = [ self.name[:25] , len(self.commits()) , len(self.merges()) ]
        if branches :
          if len(self) > 0 :
            sources = self.relations()[0]
            output.extend( ( self.source() , len(sources) , self.target() ) )
          else :
            output.extend( ( "" , -1 , "" ) )
        return tuple(output)

    def as_var ( self ) :
        return "branch_" + self.name.replace(' (2)','_dup').replace('/', '_slash_' ).replace('-', '_dash_').replace('.', '_dot_').replace(' ', '_white_').replace(':', '_colon_').replace('&', '_amp_').replace('#', '_hashtag_').replace('[', '_bra_').replace(']', '_ket_')

    def render ( self , fd , parent=None , shown_branches=None , force=False ) :
        if self.is_primary() and not force :
            column = Branch.primary.index(self.name)
        else :
            column = shown_branches.index(self)
        json = 'name:"%s", column:%d' % ( str(self).replace(' (2)', ' [dup]', 1).replace(' (2)', '') , column )
        if parent :
            fd.write( 'var %s = %s.branch({%s});\n' % ( self.as_var() , parent.as_var() , json ) )
        else :
            fd.write( 'var %s = gitgraph.branch({%s});\n' % ( self.as_var() , json ) )
        self.rendered = True


def get_branches () :
    branches = []
    refs = "refs/heads"
    info = "info/refs"
    packs = "packed-refs"
    heads = "refs/heads"
    if os.path.isdir(".git") :
        refs = "refs/remotes/origin"
        info = os.path.join( ".git" , info )
        packs = os.path.join( ".git" , packs )
        heads = os.path.join( ".git" , refs )
    if os.path.isfile(info) :
        with open(info) as fd :
            line = fd.readline()
            while line[:-1] :
                items = line[:-1].split(None, 2)
                if items[1].startswith(refs) :
                    branches.append( ( items[0] , items[1][len(refs)+1:] ) )
                line = fd.readline()
    if os.path.isfile(packs) :
        with open(packs) as fd :
            line = fd.readline()
            while line[:-1] :
                items = line[:-1].split(None, 2)
                if len(items) > 1 and items[1].startswith(refs) :
                    branch = items[1][len(refs)+1:]
                    branches = [ b for b in branches if b[1] != branch ]
                    branches.append( ( items[0] , branch ) )
                line = fd.readline()
    for root, dirs, files in os.walk(heads) :
        for f in files:
            if f == "HEAD" : continue
            filename = os.path.join(root, f)
            fd = open(filename)
            branch = filename[len(heads)+1:].replace('\\', '/')
            branches = [ b for b in branches if b[1] != branch ]
            branches.append( ( fd.readline()[:-1] , branch ) )
            fd.close()
    return branches

class Repository ( dict ) :

  def __init__ ( self ) :

    self.order = []
    self.branches = []

    cmd = subprocess.Popen( ['git', 'log', '--all', '--format="%H \"%ae\" \"%ce\" %s"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , author , committer , message = line[:-1].strip('"').split(None, 3)
        author = author.strip('"')
        committer = committer.strip('"')
        self[sha] = Commit( sha , author , committer , message )
        line = cmd.stdout.readline()
        if len(self) % 200 == 0  : os.sys.stdout.write( "%4d commits read\r" % len(self) )

    cmd = subprocess.Popen( ['git', 'log', '--all', '--date-order', '--reverse', '--format="%H %at %ct %P"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , params = line[:-1].strip('"').split(None, 1)
        self.set_params( sha , params.split(None, 4))
        if self[sha].parent and self[sha].parent not in self.order :
            raise Exception( "Incorrect input ordering" )
        self.order.append( self[sha] )
        line = cmd.stdout.readline()
        if len(self.order) % 200 == 0  : os.sys.stdout.write( "%4d commits ordered\r" % len(self.order) )

    self.set_childs()

  def set_params ( self , sha , line ) :
      self[sha].author_date = int(line[0])
      self[sha].committer_date = int(line[1])
      if len(line) > 2 :
          self[sha].parent = self[line[2]]
          if len(line) > 3 :
              self[sha].parents = [ self[sha1] for sha1 in line[3].split() ]
              if len(self[sha].parents) > 1 :
                  raise Exception( "Octopus merges on %s from %s not handled" % ( self[sha].sha , ", ".join([c.sha for c in self[sha].parents]) ) )

  def new_branch ( self , branchname , orphan=False ) :
      match = [ branch for branch in self.branches if branch.name == branchname ]
      if match :
          assert len(match) == 1
          if match[0].is_primary() :
              return match[0]
          return self.new_branch( "%s (2)" % branchname , orphan )
      else :
          self.branches.append( Branch(branchname, orphan) )
          return self.branches[-1]

  def join_branch ( self , source , branch ) :
        source.set_child( branch.begin() )
        for commit in list(branch) :
            source.branch.append( commit )
        self.branches.remove(branch)
        if len(source.branch.name) > len(branch.name) :
            source.branch.name = branch.name

  def events( self , details=False) :
      output = ['']
      event_list , msgs = self.event_list( details )

      if msgs : output.extend( msgs )

      output.append( "Branch events" )
      output.append( "  multitarget   %4d" % event_list['multitarget'] )
      output.append( "  reutilized    %4d" % event_list['reutilized'] )
      output.append( "  multimerged   %4d" % event_list['multimerged'] )
      output.append( "  indirect      %4d" % event_list['indirect'] )
      output.append( "  multisource   %4d" % event_list['multisource'] )
      output.append( "  conflict      %4d" % event_list['conflict'] )
      output.append( "" )

      return "\n".join(output)

  def event_list( self , details=False) :
      output = { 'multitarget':0 , 'reutilized':0 , 'multimerged':0 , 'indirect':0 , 'multisource':0 , 'conflict':0 }
      msgs = []

      multimerged = {}
      for commit in self.values() :
          # Skip if main child is not a merge?
          # Do we really want to skip for primary branches??
          if not commit.forks or not commit.child or ( commit.branch and commit.branch.is_primary() ) :
              continue
          merges = []
          if commit.child.parents :
              if commit.child.parent != commit :
                  if commit.child.branch == commit.branch :
                      # This is an auto-merge and should be detected somewhere
                      pass
                  else :
                      merges.append( commit.child )
          for F in [f for f in commit.forks if f.parents and f.parent != commit ] :
                  if F.branch == commit.branch :
                      # This is an auto-merge and should be detected somewhere
                      pass
                  else :
                      merges.append( F )
          if len(merges) > 1 :
              if not multimerged.has_key(len(merges)) :
                  multimerged[len(merges)] = []
              multimerged[len(merges)].append( ( commit.sha , merges ) )

      if multimerged :
          msgs.append( "Commits with multiple merges" )
          for n in sorted(multimerged.keys()) :
              msgs.append( "    %3d commits with %2d merges" % ( len(multimerged[n]) , n ) )
          msgs.append( '' )

      if details :
          if not os.path.isdir( 'branches' ) :
              os.mkdir( 'branches' )

      for branch in self.branches :
          dump = False
          if branch.is_primary() or branch.is_release() :
              continue
          end = branch.end()
          if end.child and end.forks :
              for child in end.forks :
                if child.branch and child.branch.begin() and child.branch.begin().parent :
                  if child.branch.begin().parent == end :
                      output['reutilized'] += 1
                      dump = True
          if end.child and end.parents :
              if end.parents[0] == end.child.parent :
                  output['conflict'] += 1
                  dump = True
          source = branch.source()
          if source != '<Initial>' :
              source = [ b for b in self.branches if b.name == source ][0]
          target = branch.target()
          if target != '<Final>' :
              target = [ b for b in self.branches if b.name == target ][0]
          sources , targets = branch.relations()
          if targets :
              output['multitarget'] += 1
              dump = True
          if source in [c.branch for c in sources] :
              output['multimerged'] += 1
              dump = True
          if source != target and branch.end().child :
              output['indirect'] += 1
              dump = True
          if [ branch for commit in sources if commit.branch != source ] :
              output['multisource'] += 1
              dump = True
          if dump and details :
              branch.gitgraph( "%s.html" % branch.as_var().replace('branch_', 'branches/', 1) )

      return output , msgs

  def report( self , details=False) :
      output = ['']
      output.append( "Number of commits:      %s" % len(self) )
      output.append( "Number of branches:     %s" % ( len(self.branches) - len([b for b in self.branches if b.is_primary()]) ) )
      output.append( "# initial commits:      %s" % len([c for c in self.values() if not c.parent ]) )
      output.append( "Number of merges:       %s" % len([c for c in self.values() if c.parents]) )
      output.append( "Ammended commits:       %s" % len([c for c in self.values() if c.author != c.committer and not c.parents]) )
      output.append( "# orphan commits:       %s" % len([c for c in self.values() if c.branch.is_orphan()]) )
      output.append( "Unlabelled heads:       %s" % len([c for c in self.values() if not c.branch and not c.child]) )

      report_fmt = "%25s %8d   %7d    %20s %+03d - %-20s"
      output.append( "" )
      output.append( "%-25s %8s   %7s" % ( 'PRIMARY' , '#commits' , '#merges' ) )
      for branch in [ b for b in self.branches if b.is_primary() ] :
          output.append( report_fmt % branch.report(True) )

      releases = [ b for b in self.branches if b.is_release() ]
      if releases :
          output.append( "" )
          output.append( "%-10s %8s   %7s    (%d branches)" % ( 'RELEASE' , '#commits' , '#merges' , len(releases) ) )
          stats = []
          for release in releases :
              stats.append( release.stats() )
          output.append( "           %8d   %7d" % ( sum([stat[1] for stat in stats]) , sum([stat[2] for stat in stats]) ) )
          L = sum( [ stat[1] for stat in stats ] )
          N = sum( [ 100*stat[1]/stat[0] for stat in stats ] )
          M = sum( [ 100*stat[2]/stat[0] for stat in stats ] )
          output.append( "           %8d%%  %7d%%  ; %6.1f per branch" % ( N/len(stats) , M/len(stats) , float(L) / len(releases) ) )
          if details :
              output.append( "     -----" )
              for release in releases :
                  output.append( report_fmt % release.report(True) )
                  if release.commits() :
                      output[-1] += " *** standard commits (%d)" % len(release.commits())

      branches = [ b for b in self.branches if not b.is_primary() and not b.is_release() ]
      if branches :
          output.append( "" )
          output.append( "%-10s %8s   %7s   (%d branches)" % ( 'TOPIC' , '#commits' , '#merges' , len(branches) ) )
          stats = []
          for branch in branches :
              stats.append ( branch.stats() )
          output.append( "           %8d   %7d" % ( sum([stat[1] for stat in stats]) , sum([stat[2] for stat in stats]) ) )
          L = sum( [ stat[1] for stat in stats ] )
          N = sum( [ 100.0*stat[1]/stat[0] for stat in stats ] )
          M = sum( [ 100.0*stat[2]/stat[0] for stat in stats ] )
          output.append( "           %8d%%  %7d%%  ; %6.1f per branch" % ( N/len(stats) , M/len(stats) , float(L) / len(branches) ) )
          if details :
              output.append( "     -----" )
              for branch in branches :
                  output.append( report_fmt % branch.report(True) )

      return "\n".join(output)

  def set_childs ( self ) :

    branches = []
    for commit in self.values() :
        merged = re.search("Merge (pull request #(?P<id>[0-9]*) from (?P<repo>[^/]*)/|(remote-tracking )?branch ){1}(?P<source>[^ ]*)( (of [^ ]* )?into (?P<target>[^ ]*))?", commit.message)
        if merged :
            if not commit.parents :
                print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
            else :
                if not [ b for (c,b) in branches if c == commit.parents[0] ] :
                    source = self.new_branch(merged.group('source').strip("'").replace('origin/', '')+" [auto]")
                    branches.append( ( commit.parents[0] , source ) )
                    commit.parents[0].set_branch(source, commit)
                else :
                    commit.parents[0].forks.append( commit )
                if merged.group('target') :
                    if not [ b for (c,b) in branches if c == commit ] :
                        target = self.new_branch(merged.group('target').strip("'")+" [auto]")
                        branches.append( ( commit.parent , target ) )
                        commit.parent.set_branch(target, commit)
                    else :
                        if commit.branch.name != merged.group('target').strip("'") :
                            print "WARNING : '%s [auto]' not set on commit %s, already on '%s'" % ( merged.group('target').strip("'") , commit.sha , commit.branch.pretty() )

    for sha,branchname in get_branches() :
        if not sha in self : continue
        match = [ B for B in branches if B[0] == self[sha] ]
        if match :
            c,b = match[0]
            if branchname == b.name :
                continue
            if b.is_primary() :
                # This case usually applies to remote branches created but with no commits pushed
                print "WARNING : drop branch '%s' laid over '%s' at %s" % ( branchname , b.name , sha )
                continue
            # This case only might arise when remote tips are merged into local-only branches
            print "WARNING : branch '%s' overwritten by '%s' at %s" % ( b.name , branchname , sha )
            assert len(b) == 1
            self[sha].branch = None
            self.branches.remove(b)
            branches.remove((c,b))
        branch = self.new_branch(branchname)
        branches.append( ( self[sha] , branch ) )
        self[sha].set_branch( branch )

    # Final search for merge commits without standard messages
    n = 0
    for commit in self.values() :
        for c in commit.parents :
            if not c.branch :
                n += 1
                branch = self.new_branch("removed %s" % n)
                branches.append( ( c , branch ) )
                c.set_branch( branch , commit )
            elif commit not in c.get_childs() :
                c.forks.append( commit )
    if n : print "WARNING : %d removed branches not automatically detected" % n

    # All branches detected at this point

    print
    cnt = 1
    for c,branch in branches :
        os.sys.stdout.write( "%2d %% ancestry, branch: %-40s\r" % ( 100*cnt/len(branches) , str(branch)[:40] ) )
        cnt += 1
        branch.ancestry( c )
    print

    self.order.reverse()
    for c in self.order :
        if not c.branch :
            n += 1
            branch = self.new_branch("orphan %s" % n, True)
            c.set_branch( branch )
            branch.ancestry( c )
    self.order.reverse()

    n , m = 0 , 0
    # Remove items within the loop is not safe
    __branches = [ branch for branch in self.branches ]
    for branch in __branches :
        if len(branch) == 0 :
            self.branches.remove(branch)
            m += 1
            continue

        begin = branch.begin()
        if not begin.parent : continue

        source = begin.parent
        if not source.forks and not begin.parents :
            # This is in fact a plain commit with a single edge. As ancestry assigns childs, it cannot be detected there
            self.join_branch( source , branch )
            n += 1
            continue

        # Concatenation happens in two cases :
        #   incoming merge : a parent commit whose single child is the first commit on branch
        #   outgoing merge : the first commit has a single parent, and this is the only one of their childs with a single parent
        candidates = [ c for c in begin.get_parents() if not c.forks ] + [ c.parent for c in begin.parent.get_childs() if not begin.parents and not c.parents ]
        if len(candidates) != 1 : continue

        source = candidates[0]
        if source.branch.end() == source and branch.matches( source.branch ) :
            self.join_branch( source , branch )
            n += 1

    if n :
        print "WARNING : %d branches removed by concatenation with parents" % n
    if m :
        print "ERROR : generated %d empty branches" % m

