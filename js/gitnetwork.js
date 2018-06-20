
dotSize = 4;
lineSize = 20;

canvas = document.getElementById('gitNetwork');
context = this.canvas.getContext("2d");

// 12 x 3
canvas.width = (12+1) * lineSize;
canvas.height = (13+1) * lineSize;

function doParent(x, y) {
  context.lineTo(x*lineSize, y*lineSize);
  }

function doRewind(x, y) {
  context.moveTo(x*lineSize, y*lineSize);
  }

function doCommit(x, y) {
  doParent(x, y);
  context.moveTo(x*lineSize+dotSize, y*lineSize);
  context.arc(x*lineSize, y*lineSize, dotSize, 0, 2 * Math.PI, false);
  doRewind(x, y);
  context.fill();
  }

function doMerge(x, y, X, Y) {
  doParent(x,y);
  if ( X !== null && Y !== null ) {
    doRewind(X,Y);
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

function Branch(name, row) {
  this.row = row;
  this.path = [];
  return this;
  }

Branch.prototype.push = function (x, parent) {
  var commit = new Commit(x, this, parent);
  this.path.push( commit );
  return commit;
  }

Branch.prototype.draw = function (color) {
  context.beginPath();
  context.fillStyle = color;
  context.strokeStyle = color;
  for ( i in this.path ) {
    doCommit(this.path[i].x, this.row);
    if ( this.path[i].parent != null ) {
      doMerge(this.path[i].parent.x, this.path[i].parent.branch.row, this.path[i].x, this.row);
      }
    }
  context.stroke();
  context.closePath();
  }

