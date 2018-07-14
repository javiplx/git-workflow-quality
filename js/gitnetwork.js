(function () {

dotSize = 5.5;
lineSize = 20;
lineWidth = 2.25;

function GitNetwork(length) {

  this.canvas = document.getElementById('gitNetwork');
  this.context = this.canvas.getContext("2d");

  this.branches = [];
  this.drift = 0;
  this.maxrow = 0;
  this.length = length;
  this.pointer = length;

  // The number is the pixel with, and must be underestimated
  this.history_limit = 16000 / lineSize;

  this.palette = ["black", "blue", "green", "magenta", "gold", "darkblue", "orange"];

  }

GitNetwork.prototype.xpos = function (x) {
  return ( ( x - this.drift ) - this.pointer ) * lineSize;
  }

GitNetwork.prototype.ypos = function (y) {
  return ( y + 1 ) * lineSize;
  }

GitNetwork.prototype.draw = function () {
  this.canvas.width = Math.min( this.history_limit , this.length - this.pointer );
  this.drift = Math.max( 0 , ( this.length - this.pointer ) - this.history_limit );
  this.canvas.width = ( this.canvas.width + 6 ) * lineSize;
  this.canvas.height = ( this.maxrow + 2 ) * lineSize;
  this.branches.map( function(b) { b.draw() } );
  }

GitNetwork.prototype.branch = function (options) {
  options.graph = this;
  options.context = this.context;
  var branch = new Branch(options);
  if ( branch.row > this.maxrow )
    this.maxrow = branch.row;
  this.branches.push(branch);
  return branch;
  }


function Commit(branch, sha) {
  this.graph = branch.graph;
  this.sha = sha;
  this.childs = [];
  this.x = branch.graph.pointer;
  this.y = branch.row;
  this.context = branch.context;
  this.branch = branch;
  branch.graph.pointer--;
  return this;
  }

Commit.prototype.addChild = function (sha) {
  this.childs.push( this.graph.branches.filter( function(x) { return x.has(sha) } )[0].get(sha) );
  }

Commit.prototype.draw = function () {
  x = this.graph.xpos(this.x);
  y = this.graph.ypos(this.y);
  this.doParent();
  this.context.moveTo(x+dotSize, y);
  this.context.arc(x, y, dotSize-this.context.lineWidth, 0, 2 * Math.PI, false);
  this.doRewind();
  this.context.fill();
  this.context.save();
  this.context.translate(x, y);
  this.context.rotate(-Math.PI / 4);
  this.context.translate(-x, -y);
  this.context.fillText(this.sha, x+0.25*lineSize, y-0.25*lineSize);
  this.context.restore();
  }

Commit.prototype.doParent = function (parent) {
  x = this.graph.xpos(this.x);
  y = this.graph.ypos(this.y);
  if ( typeof parent != "undefined" ) {
    X = parent.graph.xpos(parent.x);
    Y = parent.graph.ypos(parent.y);
    if ( parent.sha == parent.branch.path[parent.branch.path.length-1].sha ) {
      delta = lineSize / 2;
      this.context.lineTo(x+delta, Y);
      this.context.moveTo(x+delta, Y);
    } else if ( parent.sha == parent.branch.path[0].sha ) {
      this.context.lineTo(x-delta, Y);
      this.context.moveTo(x-delta, Y);
    } else {
      delta = - lineSize / 2;
      this.context.lineTo(X-delta, y+lineSize/2);
      this.context.moveTo(X-delta, y+lineSize/2);
      this.context.lineTo(x+delta, y+lineSize/2);
      this.context.moveTo(x+delta, y+lineSize/2);
      }
    }
  this.context.lineTo(x, y);
  }

Commit.prototype.doRewind = function () {
  x = this.graph.xpos(this.x);
  y = this.graph.ypos(this.y);
  this.context.moveTo(x, y);
  }


function Branch(options) {
  this.name = options.name;
  this.row = options.column + 1;
  this.graph = options.graph;
  this.context = options.context;
  this.open = options.open;
  this.path = [];
  this.column = -1;
  this.color = this.graph.palette[(options.column-1)%this.graph.palette.length];
  return this;
  }

Branch.prototype.head = function () {
  return this.path[this.path.length-1];
  }

Branch.prototype.has = function (sha) {
  var commit = this.path.filter( function(c) { return c.sha == sha } );
  return commit.length > 0;
  }

Branch.prototype.get = function (sha) {
  var commit = this.path.filter( function(c) { return c.sha == sha } );
  return commit[0];
  }

Branch.prototype.push = function (sha) {
  var commit = new Commit(this, sha);
  this.path.push( commit );
  return commit;
  }

Branch.prototype.draw = function () {
  this.context.beginPath();
  this.context.fillStyle = this.color;
  this.context.strokeStyle = this.color;
  this.context.lineWidth = lineWidth;
  for ( i in this.path ) {
    this.path[i].draw();
    for ( commit of this.path[i].childs ) {
      this.doJoin(commit, this.path[i]);
      }
    }
  x = this.graph.xpos(this.path[0].x);
  y = this.graph.ypos(this.row);
  if ( this.open )
    this.context.fillText(this.name, x+0.5*lineSize, y+0.15*lineSize);
  else
    this.context.fillText(this.name, x+0.25*lineSize, y+0.5*lineSize);
  this.context.stroke();
  this.context.closePath();
  }

Branch.prototype.doJoin = function (commit, parent) {
  commit.doParent(parent);
  parent.doRewind();
  }


// Expose GitGraph object
window.GitNetwork = GitNetwork;
})();
