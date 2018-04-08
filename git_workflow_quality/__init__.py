
import gitgraphjs

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

    def set_branch ( self , branch , parent=None ) :
        if branch <= self.branch :
            # self.branch has a higher weight respect to branch
            return
        if self.branch and not branch.is_primary() :
            print "WARNING : cannot assign %s to %s, already owned by %s" % ( branch , self.sha , self.branch )
            return
        branch.append( self )
        if parent :
            self.set_child( parent )

    def set_child ( self , commit ) :
        if self.child and self.child != commit :
            self.forks.append( self.child )
            if commit in self.forks :
                self.forks.remove( commit )
        self.child = commit

    def render ( self , fd , render_merge=True ) :
        if self.parents and render_merge :
            fd.write( '%s.merge(%s, {sha1:"%s", message:"%s"});\n' % ( self.parents[0].branch.as_var() , self.branch.as_var() , self.sha , self.message ) )
        else :
            fd.write( '%s.commit({sha1:"%s", message:"%s"});\n' % ( self.branch.as_var() , self.sha , self.message ) )

    def __str__ ( self ) :
        parents = " ".join([p.sha for p in self.parents])
        child =  self.child and self.child.sha or '<None>'
        forks = " ".join([f.sha for f in self.forks])
        if self.parent :
            return "%-20s %s : %s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , self.parent.sha , child , parents , forks , self.message )
        return "%-20s %s : %40s/%s %s | %s :: %s" % ( str(self.branch)[:20] , self.sha , '<None>' , child , parents , forks , self.message )


class Branch ( list ) :

    primary = ('master', 'develop')

    def __init__ ( self , branchname ) :
        self.name = branchname
        list.__init__( self )

    def commits ( self ) :
        return [c for c in list.__iter__(self) if not c.parents]

    def merges ( self ) :
        return [c for c in list.__iter__(self) if c.parents]

    def stats ( self ) :
        return len(self), len(self.commits()), len(self.merges())

    def begin ( self ) :
        begins = [ c for c in list.__iter__(self) if not c.parent or c.parent.branch != self ]
        assert len(begins) == 1
        return begins[0]

    def end ( self ) :
        ends = [ c for c in list.__iter__(self) if not c.child or c.child.branch != self ]
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
        parent = commit
        commit = commit.parent
        while commit :
            if commit.branch and not self.is_primary() :
                if commit.child and commit.child != parent :
                    commit.forks.append( parent )
                else :
                    commit.child = parent
                break
            commit.set_branch( self , parent )
            parent = commit
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

    def __str__ ( self ) :
        return self.name

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

        initial = self.begin()
        if initial.parent :
            shown_branches.append( initial.parent.branch )
            initial.parent.branch.render( fd , shown_branches=shown_branches , force=True )
            initials.append( initial.parent )

        final = self.end()
        if final.child and final.child.branch and initial.parent.branch != final.child.branch :
            assert final.child.branch
            # Only merges are handled here. Child branches will be created on loop
            # If branch is already shown, we don't need to write any commit
            if final.child.parents and final.child.branch not in shown_branches :
                shown_branches.append( final.child.branch )
                final.child.branch.render( fd , shown_branches=shown_branches , force=True )
                # For proper rendering, we must choose a parent in the same branch, which means render as parent of himself as fallback
                if final.child.parent.branch == final.child.branch :
                    finals.append( final.child.parent )
                elif final.child.parents[0].branch == final.child.branch :
                    finals.append( final.child.parents[0] )
                else :
                    finals.append( final.child )

        for commit in initial.parents :
            if commit.branch not in shown_branches :
                shown_branches.append( commit.branch )
                commit.branch.render( fd , shown_branches=shown_branches , force=True )
                initials.append( commit )

        for commit in final.forks :
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
            if source.branch and source.branch not in shown_branches :
                shown_branches.append( source.branch )
                source.branch.render( fd , shown_branches=shown_branches , force=True )
                initials.append ( source )

        for target in targets :
            if target.branch and target.branch not in shown_branches :
                # A single parent means that will be created as a fork in main loop
                if target.parents :
                    shown_branches.append( target.branch )
                    target.branch.render( fd , shown_branches=shown_branches , force=True )
                    if target.parents[0].branch == target.branch :
                        finals.append( target.parents[0] )
                    else :
                        finals.append( target.parent )

        # All commits rendered after branch creation to avoid a single original commit
        # As we don't care about their history, we just render them as plain commits
        for commit in initials + finals :
            commit.render( fd , False )

        if initial.parent :
            self.render( fd , initial.parent.branch , shown_branches , True )
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
                    commit.render( fd )
                    fd.write( "%s.checkout();\n" % self.as_var() )

        if c.child :
            if c.child.branch :
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
            sources = self.relations()[0]
            output.extend( ( self.source() , len(sources) , self.target() ) )
        return tuple(output)

    def as_var ( self ) :
        return "branch_" + self.name.replace(' (2)','_duplicated').replace('/', '_slash_' ).replace('-', '_dash_').replace('.', '_dot_').replace(' ', '_white_').replace(':', '_colon_')

    def render ( self , fd , parent=None , shown_branches=None , force=False ) :
        if self.is_primary() :
            column = Branch.primary.index(self.name)
        else :
            column = len(shown_branches)
        if force :
            column = shown_branches.index(self)
        json = 'name:"%s", column:%d' % ( self , column )
        if parent :
            fd.write( 'var %s = %s.branch({%s});\n' % ( self.as_var() , parent.as_var() , json ) )
        else :
            fd.write( 'var %s = gitgraph.branch({%s});\n' % ( self.as_var() , json ) )


def get_branches () :
    branches = []
    refs = "refs/heads"
    info = "info/refs"
    heads = "refs/heads"
    if os.path.isdir(".git") :
        refs = "refs/remotes/origin"
        info = os.path.join( ".git" , info )
        heads = os.path.join( ".git" , refs )
    if os.path.isfile(info) :
        with open(info) as fd :
            line = fd.readline()
            while line[:-1] :
                items = line[:-1].split(None, 2)
                if items[1].startswith(refs) :
                    branches.append( ( items[0] , items[1][len(refs)+1:] ) )
                line = fd.readline()
    for root, dirs, files in os.walk(heads) :
        for f in files:
            if f == "HEAD" : continue
            filename = os.path.join(root, f)
            fd = open(filename)
            branches.append( ( fd.readline()[:-1] , filename[len(heads)+1:].replace('\\', '/') ) )
            fd.close()
    return branches

class Repository ( dict ) :

  def __init__ ( self ) :

    self.order = []
    self.branches = []

    cmd = subprocess.Popen( ['git', 'log', '--all', '--format="%H %ae %ce %s"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , author , committer , message = line[:-1].strip('"').split(None, 3)
        self[sha] = Commit( sha , author , committer , message )
        line = cmd.stdout.readline()

    cmd = subprocess.Popen( ['git', 'log', '--all', '--date-order', '--reverse', '--format="%H %at %ct %P"'] , stdout=subprocess.PIPE )
    line = cmd.stdout.readline()
    while line[:-1] :
        sha , params = line[:-1].strip('"').split(None, 1)
        self.set_params( sha , params.split(None, 4))
        if self[sha].parent and self[sha].parent not in self.order :
            raise Exception( "Incorrect input ordering" )
        self.order.append( self[sha] )
        line = cmd.stdout.readline()

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

  def new_branch ( self , branchname ) :
      match = [ branch for branch in self.branches if branch.name == branchname ]
      if match :
          assert len(match) == 1
          if match[0].is_primary() :
              return match[0]
          return self.new_branch( "%s (2)" % branchname )
      else :
          self.branches.append( Branch(branchname) )
          return self.branches[-1]

  def events( self , details=False) :
      output = ['']

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
          output.append( "Commits with multiple merges" )
          for n in sorted(multimerged.keys()) :
              output.append( "    %3d commits with %2d merges" % ( len(multimerged[n]) , n ) )
          output.append( '' )

      multitarget = 0
      reutilized = 0
      multimerged = 0
      indirect = 0
      multisource = 0
      mergeconflict = 0
      for branch in self.branches :
          dump = False
          if branch.is_primary() or branch.is_release() :
              continue
          if branch.end().child and branch.end().forks :
              for child in branch.end().forks :
                if child.branch and child.branch.begin() and child.branch.begin().parent :
                  if child.branch.begin().parent == branch.end() :
                      reutilized += 1
                      dump = True
          if branch.end().child and branch.end().parents :
              if branch.end().parents[0] == branch.end().child.parent :
                  mergeconflict += 1
                  dump = True
          source = branch.source()
          target = branch.target()
          sources , targets = branch.relations()
          if targets :
              multitarget += 1
              dump = True
          if source in [c.branch for c in sources] :
              multimerged += 1
              dump = True
          if source != target and branch.end().child :
              indirect += 1
              dump = True
          if [ branch for commit in sources if commit.branch != source ] :
              multisource += 1
              dump = True
          if dump and details :
              branch.gitgraph( "%s.html" % branch.as_var().replace('branch_', 'branches/', 1) )
      output.append( "Branch events" )
      output.append( "  multitarget   %4d" % multitarget )
      output.append( "  reutilized    %4d" % reutilized )
      output.append( "  multimerged   %4d" % multimerged )
      output.append( "  indirect      %4d" % indirect )
      output.append( "  multisource   %4d" % multisource )
      output.append( "  mergeconflict %4d" % mergeconflict )
      output.append( '' )

      return "\n".join(output)

  def report( self , details=False) :
      output = ['']
      output.append( "Number of commits:      %s" % len(self) )
      output.append( "Number of branches:     %s" % ( len(self.branches) - len([b for b in self.branches if b.is_primary()]) ) )
      output.append( "# initial commits:      %s" % len([c for c in self.values() if not c.parent ]) )
      output.append( "Number of merges:       %s" % len([c for c in self.values() if c.parents]) )
      output.append( "Ammended commits:       %s" % len([c for c in self.values() if c.author != c.committer and not c.parents]) )
      output.append( "Commits with no branch: %s" % len([c for c in self.values() if not c.branch]) )
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
      merged = re.search("Merge pull request #(?P<id>[0-9]*) from (?P<repo>[^/]*)/(?P<source>.*)", commit.message )
      if merged :
         if not commit.parents :
           print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
         else :
           if not [ b for (c,b) in branches if c == commit.parents[0] ] :
             source = self.new_branch(merged.group('source').strip("'"))
             branches.append( ( commit.parents[0] , source ) )
             commit.parents[0].set_branch( source , commit )
           else :
             commit.parents[0].forks.append( commit )
      else :
        merged = re.search("Merge (branch )?(?P<source>[^ ]*) (of [^ ]* )?into (?P<target>[^ ]*)", commit.message)
        if merged :
          if not commit.parents :
            print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
          else :
            if not [ b for (c,b) in branches if c == commit.parents[0] ] :
              source = self.new_branch(merged.group('source').strip("'"))
              branches.append( ( commit.parents[0] , source ) )
              commit.parents[0].set_branch(source, commit)
            else :
              commit.parents[0].forks.append( commit )
            if not [ b for (c,b) in branches if c == commit ] :
                target = self.new_branch(merged.group('target').strip("'"))
                branches.append( ( commit.parent , target ) )
                commit.parent.set_branch(target, commit)
            else :
                if commit.branch.name != merged.group('target').strip("'") :
                    print "WARNING : '%s' not set on commit %s, already on '%s'" % ( merged.group('target').strip("'") , commit.sha , commit.branch )
        else :
            merged = re.search("Merge remote-tracking branch (?P<source>[^ ]*) into (?P<target>[^ ]*)", commit.message)
            if merged :
                if not commit.parents :
                    print "WARNING : false merge on %s %s" % ( commit.sha , commit.message )
                else :
                    if not [ b for (c,b) in branches if c == commit.parents[0] ] :
                      source = self.new_branch(merged.group('source').strip("'").replace('origin/', ''))
                      branches.append( ( commit.parents[0] , source ) )
                      commit.parents[0].set_branch(source, commit)
                    else :
                      commit.parents[0].forks.append( commit )
                    if not [ b for (c,b) in branches if c == commit ] :
                        target = self.new_branch(merged.group('target').strip("'"))
                        branches.append( ( commit.parent , target ) )
                        commit.parent.set_branch(target, commit)
                    else :
                        if commit.branch.name != merged.group('target').strip("'") :
                            print "WARNING : '%s' not set on commit %s, already on '%s'" % ( merged.group('target').strip("'") , commit.sha , commit.branch )

    for sha,branchname in get_branches() :
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
            assert len(b) < 2
            self[sha].branch = None
            self.branches.remove(b)
            branches.remove((c,b))
        branch = self.new_branch(branchname)
        branches.append( ( self[sha] , branch ) )
        self[sha].set_branch( branch )

    n = 0
    for commit in self.values() :
        for c in commit.parents :
            if not c.branch :
                n += 1
                branch = self.new_branch("removed %s" % n)
                branches.append( ( c , branch ) )
                c.set_branch( branch , commit )
            elif c.child != commit and commit not in c.forks :
                c.forks.append( commit )
    if n : print "WARNING : %d removed branch not automatically detected" % n

    # All branches detected at this point

    for c,branch in branches :
        branch.ancestry( c )

    empty = [ branch for branch in self.branches if len(branch) == 0 ]
    if empty :
        print "ERROR : generated empty branches %s" % ", ".join(map(str,empty))
        for branch in empty :
            self.branches.remove(branch)

    n = 0
    # Running in a single loop to detect empty branches seems to produce bad side effects
    for branch in self.branches :
        source = branch.begin().parent
        if source and source.child and source.child.branch == branch :
            for commit in list(branch) :
                    source.branch.append( commit )
            assert len(branch) == 0
            self.branches.remove(branch)
            n += 1
    if n :
        print "WARNING : %d branches removed by concatenation with parents" % n

