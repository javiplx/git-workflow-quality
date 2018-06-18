
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

context.beginPath();
context.fillStyle = "red";
context.strokeStyle = "red";

doCommit(12,1);
doCommit(9,1);
doCommit(6,1);
doCommit(3,1);
doCommit(2,1);

context.stroke();
context.closePath();


context.beginPath();
context.fillStyle = "green";
context.strokeStyle = "green";

doCommit(11,2);
doCommit(8,2);
doMerge(5,3,8,2);
doCommit(7,2);
doMerge(6,1);

context.stroke();
context.closePath();


context.beginPath();
context.fillStyle = "blue";
context.strokeStyle = "blue";

doCommit(10,3);
doCommit(5,3);
doCommit(4,3);
doMerge(3,1);

context.stroke();
context.closePath();


