//const canvas = document.getElementById("streamCanvas");
//const ctx = canvas.getContext("2d");

let enableDrawing = false;
let drawing = false;
let points = [];

canvas.addEventListener("pointerdown", (e) => {
  if (!enableDrawing) return;
  drawing = true;
  points = [];

  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  ctx.beginPath();
  ctx.moveTo(x, y);

  points.push({ x, y });

  canvas.setPointerCapture(e.pointerId);
});

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

let lastPoint = null;

canvas.addEventListener("pointermove", (e) => {
  if (!drawing) return;

  const rect = canvas.getBoundingClientRect();
  const point = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  };

  if (!lastPoint || distance(lastPoint, point) > 10) {
    ctx.lineTo(point.x, point.y);
    ctx.stroke();

    points.push(point);
    lastPoint = point;
  }
});
  
canvas.addEventListener("pointerup", (e) => {
  drawing = false;
  canvas.releasePointerCapture(e.pointerId);

  console.log("Points:", points);
});

let ws_onmessage_handler = null
function enableDrawZone(){
    ws_onmessage_handler = ws.onmessage
    ws.onmessage=null
    enableDrawing=true
}
function disableDrawZone(){
    ws.onmessage=ws_onmessage_handler
    ws_onmessage_handler = null
    enableDrawing=false
}
function toggleDrawZone() {
    if(!enableDrawing){
	enableDrawZone()
    }
    else{
	disableDrawZone()
    }
    
}
