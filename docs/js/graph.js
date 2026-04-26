// A* pathfinding algorithm, path reconstruction and navigation instruction generation

function getNodeById(id){
    // Find and return the node with the given id in GRAPH.nodes
    id = id.toLowerCase().trim(); 
    for (var j =0; j< GRAPH.nodes.length; j++){
        if (GRAPH.nodes[j].id=== id){
            return GRAPH.nodes[j];
        }
    }
    console.log("ID non trouvé dans GRAPH : ", id);
    return null;
}

function distance (nodeA, nodeB){
    // Returns the Euclidean distance between two nodes
    var dx = nodeA.x - nodeB.x;
    var dy = nodeA.y - nodeB.y;
    return Math.sqrt(dx*dx + dy*dy);
}

function initNeighbors(){
    //Build an adjency list from the graph edges
    var neighbors={};
    
    for (var i=0; i<GRAPH.nodes.length; i++){
        var n = GRAPH.nodes[i];
        neighbors[n.id]=[];
    }

    var pmr = document.getElementById('pmr-mode').checked;

    for (var i=0; i<GRAPH.edges.length; i++){
        var edge = GRAPH.edges[i];
        // PMR mode : skip stairs and steps, keep elevators
        if (pmr && edge.type === 'stair') continue;      
        if (pmr && edge.type === 'steps') continue;
        // Non PMR mode : skip elevators, keep stairs
        if (!pmr && edge.type === 'elevator') continue; 
        // Graph is undirected : add both directions
        neighbors[edge.from].push(edge.to);
        neighbors[edge.to].push(edge.from);
    }

    return neighbors;
}

function initScores(){
    // Initialize gScore and fScore to Infinity for all nodes
    var gScore={};
    var fScore={};

    for (var i=0; i<GRAPH.nodes.length; i++){
        var n = GRAPH.nodes[i];
        gScore[n.id]= Infinity;
        fScore[n.id]= Infinity;
    }

    // Start node : gScore=0 and fScore = heuristic distance to end node
    gScore[startNode.id]=0;
    fScore[startNode.id]= distance(startNode, endNode)

    // Initial heuristic distance
    console.log('[INFO] - Distance euclidienne départ->arrivée (heuristique initiale) : '
    +distance(startNode, endNode).toFixed(1) + ' px');

    return {gScore, fScore};
}

function reconstructPath(cameFrom){
    // Reconstruct the path from end to start using cameFrom map
    var path=[];
    var step = endNode.id;

    // While step is not undefined
    while (step !== undefined){
        // Add this node to the beginning of path
        path.unshift(getNodeById(step));
        // go back one step in cameFrom
        step= cameFrom[step];
    }
    return path;
}

function aStar(neighbors, gScore, fScore){
    // A* path finding algorithm

    // toExplore = list of nodes to explore, starting with the start node
    var toExplore=[startNode.id];

    // cameFrom = for each visited node, stores which node it was reached from
    // used to reconstruct the path at the end
    var cameFrom={};

    // Counters and timers for performance
    var nodesExplored = 0;
    var t0_astart= performance.now();

    // While there are nodes to explore
    while(toExplore.length>0){
        // current = node with the lowest fScore in toExplore
        var current = toExplore[0];

        for (var i=0; i<toExplore.length; i++){
            if (fScore[toExplore[i]]<fScore[current]){
                current= toExplore[i];
            }
        }

        // Count each processed node
        nodesExplored++;

        // If current == end node -> reconstruct the path using cameFrom
        if (current === endNode.id){
            pathNodes=reconstructPath(cameFrom);

            // Performance results
            var t1_astar = performance.now();
            var duration = (t1_astar- t0_astart).toFixed(3);

            console.log('[PERF] - Résultats A*');
            console.log('[PERF] - Temps de calcul A* : ' + duration+ ' ms');
            console.log('[PERF] - Noeuds explorés : ' + nodesExplored + '/' + GRAPH.nodes.length);

            // Path validation
            console.assert(pathNodes.length >=2, '[TEST] - Le chemin doit contenir au moins 2 noeuds');
            console.assert(pathNodes[0].id === startNode.id, '[TEST] - Premier noeud != départ');
            console.assert(pathNodes[pathNodes.length -1].id ===  endNode.id, '[TEST] - Dernier noeud != arrivée');
            console.log('[TEST] - Chemin valide :'+ startNode.label + '->' + endNode.label + '(' + pathNodes.length + ' noeuds');

            displayResult();
            return true;
        }

        // Remove current from toExplore
        var indexCurrent = toExplore.indexOf(current);
        toExplore.splice(indexCurrent,1);

        // For each neighbor of current
        for (var i=0; i<neighbors[current].length; i++){
            var neighbor = neighbors[current][i];

            // current and neighbor are ids, we need to get the node objects to compute the distance
            var currentNode = getNodeById(current);
            var neighborNode = getNodeById(neighbor);

            newG = gScore[current] + distance(currentNode,neighborNode);

            // A node can be searched from multiple nodes, so we update its gScore
            // if we find a shorter path to reach it
            if (newG < gScore[neighbor]){
                cameFrom[neighbor]=current;
                gScore[neighbor]= newG;
                fScore[neighbor]= newG+ distance(neighborNode, endNode);

                // If neighbor not yet in toExplore -> add it
                if (toExplore.indexOf(neighbor)==-1){
                        toExplore.push(neighbor);
                }
            }
        }
    }

    // No path found
    var t1_astar = performance.now();
    console.warn('[PERF] - Aucun chemin trouvé')

    return false;
}

function generateInstructions(){
    var instructions=[];

    // Skip first and last nodes (start and end), iterate over intermediate nodes
    for (var i=1; i<pathNodes.length -1; i++){
        var prev = pathNodes[i-1];
        var curr = pathNodes[i];
        var next = pathNodes[i+1];

        // Floor change : add a stair/elevator instruction
        if (curr.floor !== prev.floor){
            var type;
            if (curr.type==='elevator'){
                type='ascenseur'
            }else{
                type= 'escalier';
            }

            var floorName;
            if(curr.floor===0){
                floorName='RDC';
            }else{
                floorName= '1er étage';
            }

            instructions.push('Prenez l\''+type + ' pour aller au '+floorName);
            continue;
        }

        // Direction vectors u (prev->curr) and v (curr->next)
        var dx1= curr.x - prev.x;
        var dy1= curr.y - prev.y;
        var dx2= next.x - curr.x;
        var dy2= next.y - curr.y;

        //Angle between u and v using atan2 
        var cross = dx1*dy2 - dy1*dx2;
        var dot = dx1*dx2 + dy1*dy2;
        var angle = Math.atan2(cross, dot)*180 /Math.PI;

        var instruction;
        if (angle > 30){
            instruction= 'Tournez à droite';
        }else if (angle < -30){
            instruction = 'Tournez à gauche';
        }else{
            instruction= 'Continuez tout droit';
        }

        // Merge consecutive identical instructions to avoid repetition
        if (instructions.length===0 || instructions[instructions.length-1]!==instruction)
            instructions.push(instruction);
    }

    // Add the final destination instruction
    if (pathNodes.length>0)
        instructions.push('Vous êtes arrivé à '+ endNode.label);

    return instructions;
}

function displayResult(){
    // Display the path instructions and switch to the correct floor

    // Switch to the floor of the first node in the path
    switchFloor(pathNodes[0].floor);

    // Build the instruction list as HTML
    var instructions = generateInstructions();
    var html='<ul>';
    for (var i=0; i<instructions.length; i++){
        html += '<li>' + instructions[i] + '</li>';
    }
    html+= '</ul>';
    document.getElementById('instructions').innerHTML=html;

    // Only show the title on desktop
    if (window.innerWidth > 768) {
        document.getElementById('title-instructions').style.display='block';
    }

    // Called to duplicate the instructions in the mobile panel
    syncInstructions(); 
}

function displayNoPath() {
    // Display an error message when no PMR-accessible path exists between the two points
    var msg = '<p class="no-path-pmr">'
        + 'Aucun chemin accessible PMR n\'existe entre ces deux points.<br>'
        + 'Le trajet nécessite de passer par des escaliers ou des marches.'
        + '</p>';
    document.getElementById('instructions').innerHTML = msg;

    // Only show the title on desktop
    if (window.innerWidth > 768) {
        document.getElementById('title-instructions').style.display = 'block';
    }

    // Duplicate the message in the mobile panel
    syncInstructions();
}

function calcPath() {
    // Called when the user clicks the "Calculer" button
    // Initializes the graph, runs A* and display the result

    // Summary of the requested path information
    console.log('[INFO] - Calcul du chemin demandé');
    console.log('[INFO] - Départ : ' + startNode.label +' (id=' + startNode.id + ', étage=' + startNode.floor + ')');
    console.log('[INFO] - Arrivée : ' + endNode.label   + ' (id=' + endNode.id   + ', étage=' + endNode.floor   + ')');
    console.log('[INFO] - Mode PMR : ' + (document.getElementById('pmr-mode').checked ? 'activé' : 'désactivé'));

    // Initialize the graph structures and run A*
    var neighbors = initNeighbors();
    var { gScore, fScore } = initScores();
    var found = aStar(neighbors, gScore, fScore);

    // If no path found, display an error message
    if (!found) {
        displayNoPath();
    }

    // Switch to the map tab to show the result on mobile
    switchTab('map');
}

function setStartFromQR(id) {
    // Find the node corresponding to the QR code id
    const node = getNodeById(id);

    if (!node) {
        console.error("Salle introuvable :", id);
        return;
    }

    startNode = node;

    // Update the UI with the start node label
    document.getElementById("lbl-start").textContent = node.label;
    document.getElementById("search-start").value = node.label;

    drawPoints(node);
    enableCalcButton();
}

function handleQRParams() {
    // Read the "start" parameter from the URL, set by QR codes
    const params = new URLSearchParams(window.location.search);
    const start = params.get("start");

    if (start) {
        setStartFromQR(start);
    }
}

// Trigger path calculation when the user clicks "Calculer"
document.getElementById('btn-calc').addEventListener('click', calcPath);