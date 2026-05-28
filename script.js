const WS_URL = 'ws://localhost:8080'; // 👈 Замените на ваш адрес
const canvas = document.getElementById('streamCanvas');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');

let lastBoxes = null;

const ws = new WebSocket(WS_URL);
ws.binaryType = 'blob';

ws.onopen = () => {
    statusEl.textContent = '✅ Подключено';
    statusEl.style.color = '#0f0';
};
ws.onclose = () => {
    statusEl.textContent = '❌ Отключено';
    statusEl.style.color = '#f00';
};
ws.onerror = () => {
    statusEl.textContent = '⚠️ Ошибка';
    statusEl.style.color = '#fa0';
};

function drawPolyline(points, color='#00ff00') {
    if (points.length < 2) return;

    ctx.beginPath();
    ctx.strokeStyle = color
    ctx.moveTo(points.x1, points.y1);
    //console.log("moved to", points.x1, points.y1)

    let i=1
    while ((points['x'+i] != undefined) && (points['y'+i] != undefined)) {
        ctx.lineTo(points['x'+i], points['y'+i]);
	//console.log("line to", points['x'+i], points['y'+i])
	i++
    }
    ctx.lineTo(points.x1,points.y1)
    
    ctx.stroke();
}

// 🎨 Функция отрисовки рамок
function drawBoxes(boxes) {
   // console.log("drawing...", boxes)
   // console.log("boxes is array? ", Array.isArray(boxes))
   // console.log("drawing .boxes ...", boxes.boxes)
    boxes = boxes.boxes
    //console.log("boxes is array? ", Array.isArray(boxes))
    if (!Array.isArray(boxes)) return;

    //console.log("drawing...", boxes)
    ctx.lineWidth = 2;
    ctx.font = 'bold 14px sans-serif';
    ctx.textBaseline = 'bottom';

    boxes.forEach(box => {
	//console.log("drawing box")
	// Поддерживаем два популярных формата координат:
	// 1. {x, y, width, height}
	// 2. {x1, y1, x2, y2}
	let x, y, w, h;
	//if (box.x1 !== undefined) {
	//    x = box.x1; y = box.y1;
	//    w = box.x2 - x; h = box.y2 - y;
	//} else {
	//    x = box.x; y = box.y; w = box.width; h = box.height;
	//}

	const color = box.color //|| '#00ff00';
	//console.log("color: ",color)
	drawPolyline(box, color)

	// Фон рамки (полупрозрачный)
	//ctx.fillStyle = color + '33'; // +33 = ~20% opacity в HEX
	//ctx.fillRect(x, y, w, h);

	// Обводка
	//ctx.strokeStyle = color;
	//ctx.strokeRect(x, y, w, h);

	// Подпись (label)
	//if (box.label) {
	//    const text = String(box.label);
	//    const tm = ctx.measureText(text);
	//    const pad = 4;
	//    const txtH = 18;

	//    // Плашка под текст
	//    ctx.fillStyle = color;
	//    ctx.fillRect(x, y - txtH - pad, tm.width + pad * 2, txtH + pad);

	//    // Сам текст
	//    ctx.fillStyle = '#000';
	//    ctx.fillText(text, x + pad, y - pad - 2);
	//}
    });
}

ws.onmessage = (event) => {
    const data = event.data;
    //console.log("got data from socket, type: ", typeof data)
    // 📦 JSON с рамками
    if (typeof data === 'string') {
	try {
	    lastBoxes = JSON.parse(data);
	} catch (e) {
	    console.warn('Invalid JSON:', e);
	}
	//console.log(lastBoxes)
	return;
    }

    // 🖼 Кадр (Blob)
    if (data instanceof Blob) {
	const img = new Image();
	const url = URL.createObjectURL(data);

	img.onload = () => {
	    // Подгоняем canvas под размер кадра
	    canvas.width = img.width;
	    canvas.height = img.height;

	    // 1. Рисуем кадр
	    ctx.drawImage(img, 0, 0);
	    // 2. Рисуем рамки поверх
	    drawBoxes(lastBoxes);

	    URL.revokeObjectURL(url);
	};

	img.onerror = () => URL.revokeObjectURL(url);
	img.src = url;
    }
};
