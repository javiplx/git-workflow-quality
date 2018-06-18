
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

function Commit(x, X,Y) {
  this.x = x;
  this.X = X;
  this.Y = Y;
  return this;
  }

function Branch(name, row) {
  this.row = row;
  this.path = [];
  return this;
  }

Branch.prototype.push = function (x, X,Y) {
  this.path.push( new Commit(x, X,Y) );
  }

Branch.prototype.draw = function (color) {
  context.beginPath();
  context.fillStyle = color;
  context.strokeStyle = color;
  for ( i in this.path ) {
    doCommit(this.path[i].x, this.row);
    if ( this.path[i].X !== null && this.path[i].Y !== null ) {
      doMerge(this.path[i].X, this.path[i].Y, this.path[i].x, this.row);
      }
    }
  context.stroke();
  context.closePath();
  }

branches = [];

branch = new Branch('master', 1);
branches.push( branch );
branch.push( 12 );
branch.push( 9 );
branch.push( 6 );
branch.push( 3 );
branch.push( 2 );

branch.draw("red");


branch1 = new Branch('branch_1', 2);
branches.push( branch1 );
branch1.push( 11 );
branch1.push( 8, 5,3 );
branch1.push( 7, 6,1 );

branch1.draw("green");


branch2 = new Branch('branch_2', 3);
branches.push( branch2 );
branch2.push( 10 );
branch2.push( 5 );
branch2.push( 4, 3,1 );

branch2.draw("blue");

