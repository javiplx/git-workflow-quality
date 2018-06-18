
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
  this.parent = parent;
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
    if ( typeof this.path[i].parent !== "undefined" ) {
      doMerge(this.path[i].parent.x, this.path[i].parent.branch.row, this.path[i].x, this.row);
      }
    }
  context.stroke();
  context.closePath();
  }

branches = [];

branch0 = new Branch('master', 1);
branches.push( branch0 );

branch1 = new Branch('branch_1', 2);
branches.push( branch1 );

branch2 = new Branch('branch_2', 3);
branches.push( branch2 );


branch0.push( 12 );
branch0.push( 9 );
c0 = branch0.push( 6 );
c2 = branch0.push( 3 );
branch0.push( 2 );

branch2.push( 10 );
c1 = branch2.push( 5 );
branch2.push( 4, c2 );

branch1.push( 11 );
branch1.push( 8, c1 );
branch1.push( 7, c0 );


branch0.draw("red");
branch1.draw("green");
branch2.draw("blue");

