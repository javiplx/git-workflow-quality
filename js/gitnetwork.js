(function () {

dotSize = 4;
lineSize = 20;

function GitNetwork(options) {

  this.canvas = document.getElementById('gitNetwork');
  this.context = this.canvas.getContext("2d");

  // 12 x 3
  this.canvas.width = (12+1) * lineSize;
  this.canvas.height = (13+1) * lineSize;

  this.branches = [];
  this.pointer = -1;

  this.palette = ["black", "blue", "green", "magenta", "gold", "darkblue", "orange"];

  }

GitNetwork.prototype.resize = function (x, y) {
  this.canvas.width = (x+1) * lineSize;
  this.canvas.height = (y+1) * lineSize;
  if ( this.pointer < 0 ) {
    this.pointer = x;
    }
  }

GitNetwork.prototype.branch = function (options) {
  options.graph = this;
  options.context = this.context;
  var branch = new Branch(options);
  this.branches.push(branch);
  return branch;
  }


function Commit(branch, sha, parents) {
  this.branch = branch; // maybe useless ???
  this.sha = sha;
  this.parents = branch.graph.branches.filter( function(x) { return parents.includes( x.name ) } ).map( function(x) { return x.path[x.path.length-1]; });
  this.x = branch.graph.pointer;
  branch.graph.pointer--;
  return this;
  }


function Branch(options) {
  this.name = options.name;
  this.row = options.column + 1;
  this.graph = options.graph;
  this.context = options.context;
  this.path = [];
  this.column = -1;
  this.color = this.graph.palette[(options.column-1)%this.graph.palette.length];
  return this;
  }

Branch.prototype.push = function (sha, parents) {
  var commit = new Commit(this, sha, parents);
  this.path.push( commit );
  return commit;
  }

Branch.prototype.draw = function (color) {
  if ( color == null ) {
    color = this.color
    }
  this.context.beginPath();
  this.context.fillStyle = color;
  this.context.strokeStyle = color;
  for ( i in this.path ) {
    this.doCommit(this.path[i], this.row);
    for ( commit of this.path[i].parents ) {
      this.doJoin(commit.x, commit.branch.row, this.path[i].x, this.row);
      }
    }
  this.context.fillText(this.name, (this.path[0].x+0.5)*lineSize, (this.row+0.15)*lineSize);
  this.context.stroke();
  this.context.closePath();
  }

Branch.prototype.doParent = function (x, y) {
  this.context.lineTo(x*lineSize, y*lineSize);
  }

Branch.prototype.doRewind = function (x, y) {
  this.context.moveTo(x*lineSize, y*lineSize);
  }

Branch.prototype.doCommit = function (commit, y) {
  this.doParent(commit.x, y);
  this.context.moveTo(commit.x*lineSize+dotSize, y*lineSize);
  this.context.arc(commit.x*lineSize, y*lineSize, dotSize, 0, 2 * Math.PI, false);
  this.doRewind(commit.x, y);
  this.context.fill();
  this.context.save();
  this.context.translate(commit.x*lineSize, y*lineSize);
  this.context.rotate(-Math.PI / 4);
  this.context.translate(-commit.x*lineSize, -y*lineSize);
  this.context.fillText(commit.sha, (commit.x+0.25)*lineSize, (y-0.25)*lineSize);
  this.context.restore();
  }

Branch.prototype.doJoin = function (x, y, X, Y) {
  this.doParent(x,y);
  if ( X !== null && Y !== null ) {
    this.doRewind(X,Y);
    }
  }


// Expose GitGraph object
window.GitNetwork = GitNetwork;
})();
