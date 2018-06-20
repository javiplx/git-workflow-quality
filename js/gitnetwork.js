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

  }
GitNetwork.prototype.resize = function (x, y) {
  this.canvas.width = (x+1) * lineSize;
  this.canvas.height = (y+1) * lineSize;
  }

Branch.prototype.doParent = function (x, y) {
  this.context.lineTo(x*lineSize, y*lineSize);
  }

Branch.prototype.doRewind = function (x, y) {
  this.context.moveTo(x*lineSize, y*lineSize);
  }

Branch.prototype.doCommit = function (x, y) {
  this.doParent(x, y);
  this.context.moveTo(x*lineSize+dotSize, y*lineSize);
  this.context.arc(x*lineSize, y*lineSize, dotSize, 0, 2 * Math.PI, false);
  this.doRewind(x, y);
  this.context.fill();
  }

Branch.prototype.doMerge = function (x, y, X, Y) {
  this.doParent(x,y);
  if ( X !== null && Y !== null ) {
    this.doRewind(X,Y);
    }
  }

function Commit(x, branch, parent) {
  this.x = x;
  this.branch = branch;
  if ( parent != null ) {
    this.parent = parent.path[parent.path.length-1];
  } else {
    this.parent = parent;
    }
  return this;
  }

GitNetwork.prototype.branch = function (options) {
  options.context = this.context;
  var branch = new Branch(options);
  this.branches.push(branch);
  return branch;
  }

function Branch(options) {
  this.name = options.name;
  this.context = options.context;
  this.row = options.column + 1;
  this.path = [];
  return this;
  }

Branch.prototype.push = function (x, parent) {
  var commit = new Commit(x, this, parent);
  this.path.push( commit );
  return commit;
  }

Branch.prototype.draw = function (color) {
  this.context.beginPath();
  this.context.fillStyle = color;
  this.context.strokeStyle = color;
  for ( i in this.path ) {
    this.doCommit(this.path[i].x, this.row);
    if ( this.path[i].parent != null ) {
      doMerge(this.path[i].parent.x, this.path[i].parent.branch.row, this.path[i].x, this.row);
      }
    }
  this.context.stroke();
  this.context.closePath();
  }

// Expose GitGraph object
window.GitNetwork = GitNetwork;
})();
