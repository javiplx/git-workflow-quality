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

GitNetwork.prototype.draw = function () {
  this.branches.map( function(b) { b.draw() } );
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
  this.sha = sha;
  this.parents = parents.map( function(sha) { return branch.graph.branches.filter( function(x) { return x.has(sha) } )[0].get(sha); } );
  this.x = branch.graph.pointer;
  this.y = branch.row;
  this.context = branch.context;
  branch.graph.pointer--;
  return this;
  }

Commit.prototype.draw = function () {
  this.doParent();
  this.context.moveTo(this.x*lineSize+dotSize, this.y*lineSize);
  this.context.arc(this.x*lineSize, this.y*lineSize, dotSize, 0, 2 * Math.PI, false);
  this.doRewind();
  this.context.fill();
  this.context.save();
  this.context.translate(this.x*lineSize, this.y*lineSize);
  this.context.rotate(-Math.PI / 4);
  this.context.translate(-this.x*lineSize, -this.y*lineSize);
  this.context.fillText(this.sha, (this.x+0.25)*lineSize, (this.y-0.25)*lineSize);
  this.context.restore();
  }

Commit.prototype.doParent = function () {
  this.context.lineTo(this.x*lineSize, this.y*lineSize);
  }

Commit.prototype.doRewind = function () {
  this.context.moveTo(this.x*lineSize, this.y*lineSize);
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

Branch.prototype.has = function (sha) {
  var commit = this.path.filter( function(c) { return c.sha == sha } );
  return commit.length > 0;
  }

Branch.prototype.get = function (sha) {
  var commit = this.path.filter( function(c) { return c.sha == sha } );
  return commit[0];
  }

Branch.prototype.push = function (sha, parents) {
  var commit = new Commit(this, sha, parents);
  this.path.push( commit );
  return commit;
  }

Branch.prototype.draw = function () {
  this.context.beginPath();
  this.context.fillStyle = this.color;
  this.context.strokeStyle = this.color;
  for ( i in this.path ) {
    this.path[i].draw();
    for ( commit of this.path[i].parents ) {
      this.doJoin(commit, this.path[i]);
      }
    }
  this.context.fillText(this.name, (this.path[0].x+0.5)*lineSize, (this.row+0.15)*lineSize);
  this.context.stroke();
  this.context.closePath();
  }

Branch.prototype.doJoin = function (commit, parent) {
  commit.doParent();
  parent.doRewind();
  }


// Expose GitGraph object
window.GitNetwork = GitNetwork;
})();
