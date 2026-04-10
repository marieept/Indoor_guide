function setStartFromQR(id) {
    const node = getNodeById(id);

    if (!node) {
        console.error("Salle introuvable :", id);
        return;
    }

    startNode = node;

    // UI texte
    document.getElementById("lbl-start").textContent = node.label;
    document.getElementById("search-start").value = node.label;

    drawPoints(node);
    enableCalcButton();
}

function initNeighbors(){
    //Initialiser neighbors à partir des edges
    var neighbors={};
    
    for (var i=0; i<GRAPH.nodes.length; i++){
        var n = GRAPH.nodes[i];
        neighbors[n.id]=[];
    }

    var pmr = document.getElementById('pmr-mode').checked;

    for (var i=0; i<GRAPH.edges.length; i++){
        var edge = GRAPH.edges[i];
        if (pmr && edge.type === 'stair') continue;      // PMR : ignore escaliers
        if (pmr && edge.type === 'steps') continue;
        if (!pmr && edge.type === 'elevator') continue;  // non PMR : ignore ascenseurs
        neighbors[edge.from].push(edge.to);
        neighbors[edge.to].push(edge.from);
    }

    return neighbors;
}

function initScores(){
    //Pour chaque noeud : gScore = Infini, fScore= Infini
    var gScore={};
    var fScore={};

    for (var i=0; i<GRAPH.nodes.length; i++){
        var n = GRAPH.nodes[i];
        gScore[n.id]= Infinity;
        fScore[n.id]= Infinity;
    }

    //gScore[départ]=0 et fScore[départ]= distance(départ,arrivée)
    gScore[startNode.id]=0;
    fScore[startNode.id]= distance(startNode, endNode)

    // Distance heuristique initiale
    console.log('[INFO] - Distance euclidienne départ->arrivée (heuristique initiale) : '
    +distance(startNode, endNode).toFixed(1) + ' px');

    return {gScore, fScore};
}

function getNodeById(id){
    id = id.toLowerCase().trim(); 
    //trouver le noeud qui a cet id dans GRAPH.nodes
    for (var j =0; j< GRAPH.nodes.length; j++){
        if (GRAPH.nodes[j].id=== id){
            //Ajouter ce noeuf au début de path
            return GRAPH.nodes[j];
        }
    }
    console.log("ID non trouvé dans GRAPH : ", id);
    return null;
}

function reconstructPath(cameFrom){
    var path=[];
    var step = endNode.id;

    //Tant que step n'est pas undefined
    while (step !== undefined){
        //Ajouter ce noeud au début de path
        path.unshift(getNodeById(step));
        //étape = cameFrom[étape] -> on remonte d'un cran dans cameFrom
        step= cameFrom[step];
    }
    return path;
}

function displayResult(){
    switchFloor(pathNodes[0].floor);

    var instructions = generateInstructions();
    var html='<ul>';
    for (var i=0; i<instructions.length; i++){
        html += '<li>' + instructions[i] + '</li>';
    }
    html+= '</ul>';
    document.getElementById('instructions').innerHTML=html;
    if (window.innerWidth > 768) {
        document.getElementById('title-instructions').style.display='block';
    }

    syncInstructions(); 
}

function displayNoPath() {
    var msg = '<p class="no-path-pmr">'
        + 'Aucun chemin accessible PMR n\'existe entre ces deux points.<br>'
        + 'Le trajet nécessite de passer par des escaliers ou des marches.'
        + '</p>';
    document.getElementById('instructions').innerHTML = msg;
    if (window.innerWidth > 768) {
        document.getElementById('title-instructions').style.display = 'block';
    }

    syncInstructions();
}

function aStar(neighbors, gScore, fScore){
    //toExplore = [départ]
    var toExplore=[startNode.id];

    //cameFrom = {}
    var cameFrom={};

    //Compteurs et chrono
    var nodesExplored = 0;
    var t0_astart= performance.now();

    //Tant que toExplore n'est pas vide:
    while(toExplore.length>0){
        console.log('exploring', toExplore.length, 'nodes');
        //current = noeud avec le plus petit fScore dans toExplore
        var current = toExplore[0];

        for (var i=0; i<toExplore.length; i++){
            if (fScore[toExplore[i]]<fScore[current]){
                current= toExplore[i];
            }
        }

        //On compte chaque noeud traité
        nodesExplored++;

        //Si current == arrivée -> reconstruire le chemin avec cameFrom
        if (current === endNode.id){
            pathNodes=reconstructPath(cameFrom);

            // Résultat performance
            var t1_astar = performance.now();
            var duration = (t1_astar- t0_astart).toFixed(3);

            console.log('[PERF] - Résultats A*');
            console.log('[PERF] - Temps de calcul A* : ' + duration+ ' ms');
            console.log('[PERF] - Noeuds explorés : ' + nodesExplored + '/' + GRAPH.nodes.length);

            // Validation du chemin
            console.assert(pathNodes.length >=2, '[TEST] - Le chemin doit contenir au moins 2 noeuds');
            console.assert(pathNodes[0].id === startNode.id, '[TEST] - Premier noeud != départ');
            console.assert(pathNodes[pathNodes.length -1].id ===  endNode.id, '[TEST] - Dernier noeud != arrivée');
            console.log('[TEST] - Chemin valide :'+ startNode.label + '->' + endNode.label + '(' + pathNodes.length + ' noeuds');

            displayResult();
            return true;
        }

        //Retirer current de toExplore
        var indexCurrent = toExplore.indexOf(current);
        toExplore.splice(indexCurrent,1);

        //Pour chaque voisin de current:
        for (var i=0; i<neighbors[current].length; i++){
            var neighbor = neighbors[current][i];

            //current et neighbor sont des id, on doit retrouver les objets
            var currentNode = getNodeById(current);
            var neighborNode = getNodeById(neighbor);

            newG = gScore[current] + distance(currentNode,neighborNode);

            //Comme un node est voisin de plusieurs nodes, on va le retrouver plusieurs fois, donc on met a jour son gScore pour trouver le chemin le plus court pour l'atteindre
            //Si newG < gScore[neighbor]
            if (newG < gScore[neighbor]){
                cameFrom[neighbor]=current;
                gScore[neighbor]= newG;
                fScore[neighbor]= newG+ distance(neighborNode, endNode);

                //Si neighbor pas encore dans toExplore -> l'ajouter
                if (toExplore.indexOf(neighbor)==-1){
                        toExplore.push(neighbor);
                }
            }
        }
    }

    // Aucun chemin trouvé
    var t1_astar = performance.now();
    console.warn('[PERF] - Aucun chemin trouvé')

    return false;
}

function calcPath() {
    // Résumé des informations demandées
    console.log('[INFO] - Calcul du chemin demandé');
    console.log('[INFO] - Départ : ' + startNode.label +' (id=' + startNode.id + ', étage=' + startNode.floor + ')');
    console.log('[INFO] - Arrivée : ' + endNode.label   + ' (id=' + endNode.id   + ', étage=' + endNode.floor   + ')');
    console.log('[INFO] - Mode PMR : ' + (document.getElementById('pmr-mode').checked ? 'activé' : 'désactivé'));

    var neighbors = initNeighbors();
    var { gScore, fScore } = initScores();
    var found = aStar(neighbors, gScore, fScore);

    if (!found) {
        displayNoPath();
    }

    switchTab('map');
}

function distance (nodeA, nodeB){
    var dx = nodeA.x - nodeB.x;
    var dy = nodeA.y - nodeB.y;
    return Math.sqrt(dx*dx + dy*dy);
}

function generateInstructions(){
    var instructions=[];

    for (var i=1; i<pathNodes.length -1; i++){
        var prev = pathNodes[i-1];
        var curr = pathNodes[i];
        var next = pathNodes[i+1];

        //Changement d'étage
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

        //Vecteurs u et v
        var dx1= curr.x - prev.x;
        var dy1= curr.y - prev.y;
        var dx2= next.x - curr.x;
        var dy2= next.y - curr.y;

        //Angle avec atan2 (axe Y inversé en SVG donc on inverse le signe)
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

        //Fusionner les instructions consécutives identiques
        if (instructions.length===0 || instructions[instructions.length-1]!==instruction)
            instructions.push(instruction);
    }

    //Ajouter la destination finale
    if (pathNodes.length>0)
        instructions.push('Vous êtes arrivé à '+ endNode.label);

    return instructions;
}

function handleQRParams() {
    const params = new URLSearchParams(window.location.search);
    const start = params.get("start");

    if (start) {
        setStartFromQR(start);
    }
}

document.getElementById('btn-calc').addEventListener('click', calcPath);