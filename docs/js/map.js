// Floor plan display, zoom, floor switching and path drawing on the SVG overlay

function applyScale(s) {
    // Apply a zoom scale to the map container
    // The wrapper is resized to match the scaled container so the page scrolls correctly
    scale = s;
    container.style.transform = 'scale(' + s + ')';
    container.style.transformOrigin = 'top left';
    container.style.width = img.naturalWidth + 'px';
    container.style.height = img.naturalHeight + 'px';

    wrapper.style.width  = Math.ceil(img.naturalWidth  * s) + 'px';
    wrapper.style.height = Math.ceil(img.naturalHeight * s) + 'px';
}

function zoom(factor){
    // Multiply the current scale by factor to zoom in or out
    applyScale(scale*factor);
}

function getFloors(){
    // Return the list of unique floor numbers found in the graph
    var floors = [];
    for (var i = 0; i < GRAPH.nodes.length; i++) {
        var n = GRAPH.nodes[i];
        if (floors.indexOf(n.floor) === -1) {
            floors.push(n.floor);
        }
    }
    return floors;
}

function drawPath(){
    // Draw the path on the current floor as blue SVG lines
    if (pathNodes.length>1){
        for (var i=0; i<pathNodes.length-1; i++){
            var nodeA= pathNodes[i];
            var nodeB= pathNodes[i+1];

            // Skip edges that are not on the current floor
            // Number to convert "0" in 0 if it is the case
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
    // Draw a circle for each room on the current floor
    // Color : green for start, red for end, blue for others
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

        // Attach the node to the circle element so it can be retrieved on click
        circle.node = n;
        circle.style.pointerEvents = 'all';
        circle.addEventListener('click', onCircleClick);
    }
}

function drawPoints(){
    // Clear the overlay and redraw the path and room circles
    overlay.innerHTML='';
    drawPath();
    drawCircle();
}

function onInitialLoad() {
    // Called once when the page first loads, applies the initial scale
    applyScale(scale);
}

function onImgLoad() {
    // Reload overlay dimensions and redraw points when the new image is loaded
    overlay.setAttribute('width', img.naturalWidth);
    overlay.setAttribute('height', img.naturalHeight);
    applyScale(scale);
    drawPoints();
}

function setupOverlay(){
    // Set the SVG overlay dimensions to match the floor plan image
    overlay.setAttribute('width', img.naturalWidth);
    overlay.setAttribute('height', img.naturalHeight);
    applyScale(scale);
    drawPoints();
}

function switchFloor(floor){
    // Switch the displayed floor plan to the given floor
    currentFloor = floor;

    // Reload overlay dimensions and redraw points when the new image is loaded
    img.onload = onImgLoad;
    img.src = FLOOR_IMAGES[floor];

    // Update floor buttons : remove active from all, add active to the selectif one
    var btns = document.querySelectorAll('.floor-btn');
    for (var i = 0; i < btns.length; i++){
        btns[i].classList.remove('active');
    }
    btns[floor].classList.add('active');
}

function addFloorListener(btn, floor) {
    // Add a click listener to a floor button
    // The floor value is passed as a parameter to avoid closure issues in loops
    btn.addEventListener('click', function() {
        switchFloor(floor);
    });
}

function buildFloorButtons(){
    // Create a button for each floor and add it to the floor controls
    var floors=getFloors();

    for (var i=0; i<floors.length; i++){
        var f = floors[i];
        
        var btn = document.createElement('button');
        btn.className = 'floor-btn';

        if (f===0){
            btn.textContent = "RDC";
            btn.classList.add('active'); // ground floor is active by default
        }else{
            btn.textContent="1er étage"
        }


        addFloorListener(btn, f);
        document.getElementById('floor-controls').appendChild(btn);
    }
}

function initMap() {
    // Initialize the map : setup the overlay and build  the floor buttons
    if (img.complete && img.naturalWidth > 0) {
        // Image already loaded, setup immediately
        setupOverlay();
    } else {
        // Wait for the image to load before setting up
        img.onload = setupOverlay;
    }
    buildFloorButtons();
}

// Apply initial scale when the page loads
// If the image is already loaded, apply scale, if not wait for it to load
if (img.complete && img.naturalWidth > 0) {
    applyScale(scale);
} else {
    img.onload = onInitialLoad;
}