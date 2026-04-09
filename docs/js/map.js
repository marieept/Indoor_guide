function initMap() {
    if (img.complete && img.naturalWidth > 0) {
        setupOverlay();
    } else {
        img.onload = setupOverlay;
    }
    buildFloorButtons();
}

function setupOverlay(){
    overlay.setAttribute('width', img.naturalWidth);
    overlay.setAttribute('height', img.naturalHeight);
    applyScale(scale);
    drawPoints();
}

function applyScale(s) {
    scale = s;
    container.style.transform = 'scale(' + s + ')';
    container.style.transformOrigin = 'top left';
    container.style.width = img.naturalWidth + 'px';
    container.style.height = img.naturalHeight + 'px';

    wrapper.style.width  = Math.ceil(img.naturalWidth  * s) + 'px';
    wrapper.style.height = Math.ceil(img.naturalHeight * s) + 'px';
}

function zoom(factor){
    applyScale(scale*factor);
}

function getFloors(){
    var floors = [];
    for (var i = 0; i < GRAPH.nodes.length; i++) {
        var n = GRAPH.nodes[i];
        if (floors.indexOf(n.floor) === -1) {
            floors.push(n.floor);
        }
    }
    return floors;
}

function switchFloor(floor){
    currentFloor = floor;
    img.onload = function() {
        overlay.setAttribute('width', img.naturalWidth);
        overlay.setAttribute('height', img.naturalHeight);
        applyScale(scale);
        drawPoints();
    };
    img.src = FLOOR_IMAGES[floor];

    // Mettre à jour les boutons
    var btns = document.querySelectorAll('.floor-btn');
    for (var i = 0; i < btns.length; i++){
        btns[i].classList.remove('active');
    }
    // Ajouter active au bon bouton
    btns[floor].classList.add('active');
}

function buildFloorButtons(){
    var floors=getFloors();

    for (var i=0; i<floors.length; i++){
        var f = floors[i];
        
        var btn = document.createElement('button');
        btn.className = 'floor-btn';

        if (f===0){
            btn.textContent = "RDC";
            btn.classList.add('active');
        }else{
            btn.textContent="1er étage"
        }
        (function(floor) {
            btn.addEventListener('click', function() {
                switchFloor(floor);
            });
        })(f);
        document.getElementById('floor-controls').appendChild(btn);
    }
}

function drawPath(){
    //Si le chemin existe, on le trace
    if (pathNodes.length>1){
        for (var i=0; i<pathNodes.length-1; i++){
            var nodeA= pathNodes[i];
            var nodeB= pathNodes[i+1];

            if (Number(nodeA.floor) !== Number(currentFloor) || Number(nodeB.floor) !== Number(currentFloor)) continue;

            var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', nodeA.x);
            line.setAttribute('y1', nodeA.y);
            line.setAttribute('x2', nodeB.x);
            line.setAttribute('y2', nodeB.y);
            line.setAttribute('stroke', 'blue');
            line.setAttribute('stroke-width', '20');
            overlay.appendChild(line);
        }
    }
}

function drawCircle(){
    // Ensuite on dessine les cercles par dessus
    for (let i=0; i<GRAPH.nodes.length; i++){
        let n = GRAPH.nodes[i];

        if (n.type !== 'room') continue;
        if (Number(n.floor) !==Number(currentFloor)) continue;

        var color = 'blue';
        
        if (startNode!==null && n.id===startNode.id){
            color='green';
        }else if(endNode!==null && n.id===endNode.id){
            color='red';
        }


        var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');

        circle.setAttribute('cx',n.x);
        circle.setAttribute('cy',n.y);
        circle.setAttribute('r', 30);
        circle.setAttribute('fill', color);
        overlay.appendChild(circle);

        circle.node = n;
        circle.style.pointerEvents = 'all';
        circle.addEventListener('click', onCircleClick);
    }
}

function drawPoints(){
    overlay.innerHTML='';
    drawPath();
    drawCircle();
}

if (img.complete && img.naturalWidth > 0) {
    applyScale(scale);
} else {
    img.onload = function() {
        applyScale(scale);
    };
}