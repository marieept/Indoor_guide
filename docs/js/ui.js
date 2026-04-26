// UI logic : graph loading, search, node selection and PMR mode

// Graph data loaded from graph.json
let GRAPH={nodes:[], edges:[]};

// Floor plan images indexed by floor number
var FLOOR_IMAGES = {};

// Initial zoom scale depending on screen size
var scale;
if (window.innerWidth <= 768) {
    scale = 0.1;
} else {
    scale = 0.2;
}

var pmrMode = false;

var startNode = null;
var endNode = null;

// Stores the nodes of the calculated path
var pathNodes= [];

// Current displayed floor
var currentFloor=0;

const container = document.getElementById('map-svg-container');
const img = document.getElementById('plan-img');
const wrapper =  document.getElementById('map-wrapper');

// Load config and graph data
var t0_load = performance.now();

fetch('assets/config_web.json')
    .then(r => r.json())
    .then(config => {
        // Store floor plan images indexed by floor number
        config.etages.forEach(floor => {
            FLOOR_IMAGES[floor.floor] = floor.svg;
        });
        // Display the ground floor by default
        img.src = FLOOR_IMAGES[0];
        return fetch('assets/graph.json');
    })
    .then(r => r.json())
    .then(data => {
        // Performance and validation logs
        var t1_load = performance.now();
        console.log('[PERF] - Chargement du graphe : ' + (t1_load - t0_load).toFixed(2) +' ms'
            + ' avec ' + data.nodes.length + ' noeuds et ' + data.edges.length+ ' arêtes');

        console.assert(data.nodes.length>0, '[TEST] - Le graphe ne contient aucun noeud');
        console.assert(data.edges.length >0, '[TEST] - Le graphe ne contient aucune arête');
        console.log('[TEST] - Structure du graphe OK');

        var nb_rooms = data.nodes.filter(n => n.type === 'room').length;
        var nb_transitions = data.nodes.filter(n => n.type === 'stair' || n.type === 'elevator').length;
        console.log('[INFO] - Salles : ' + nb_rooms + ' / Transitions : ' + nb_transitions);

        GRAPH = data;
        initMap();
        // Read the "start" parameter from the URL to set the start node automatically
        handleQRParams();
    })

function displaySuggestions(query, type){
    // Display search suggestions
    // Only shows rooms, filtered by PMR mode if enabled
    // Uses alias for search but displays the full label after
    var suggBox = document.getElementById('suggestions-' + type);
    suggBox.innerHTML='';

    if (query==='') {
        suggBox.style.border = 'none';
        return;
    }

    // Object to avoid showing duplicate aliases
    let seenAliases = {};

    for (let i=0; i<GRAPH.nodes.length; i++){
        let n = GRAPH.nodes[i];

        if (n.type !== 'room') continue;
        if (pmrMode && n.pmr === false) continue;

        // Compare with alias, fallback to label if no alias
        let alias = n.alias || n.label;

        if (alias.toLowerCase().includes(query.toLowerCase())){
            // Only keep one suggestion per alias
            if (!seenAliases[alias]){
                var div = document.createElement('div');
                div.textContent = alias;

                // Attach the node to the div so it can be retrieved on click
                div.node = n;
                div.type = type;

                div.addEventListener('click', onSuggestionClick);
                suggBox.appendChild(div);
                suggBox.style.border = "1px solid lightgray";

                seenAliases[alias] = true;
            }
        }
    }
}

function onSearchStart(){
    // Called when the user types in the start search box
    var query = document.getElementById('search-start').value;
    startNode=null;
    document.getElementById('lbl-start').textContent='-';
    displaySuggestions(query, 'start');
}

function onSearchEnd(){
    // Called when the user types in the end search box
    var query = document.getElementById('search-end').value;
    endNode=null;
    document.getElementById('lbl-end').textContent='-';
    displaySuggestions(query, 'end');
}

function onSuggestionClick(){
    // Called when the user clicks on a suggestion
    var n = this.node;
    var type = this.type;

    // Reset de path if one already exists
    if (pathNodes.length > 0){
        pathNodes = [];
        document.getElementById('instructions').innerHTML = '';
        document.getElementById('title-instructions').style.display = 'none';
    }

    // Set the selected node as start or end
    if (type==='start'){
        startNode = n;
        document.getElementById('lbl-start').textContent= n.label;
        document.getElementById('search-start').value = n.label;
    }else{
        endNode = n;
        document.getElementById('lbl-end').textContent = n.label;
        document.getElementById('search-end').value = n.label;
    }
    
    // Hide the suggestion box
    document.getElementById('suggestions-'+type).innerHTML='';
    document.getElementById('suggestions-'+type).innerHTML='';
    document.getElementById('suggestions-'+ type).style.border= 'none';

    // Enable the calculate button if both nodes are selected
    if (startNode !==null && endNode!==null){
        document.getElementById('btn-calc').disabled= false;
        document.getElementById('btn-calc-map').disabled = false;
    }else{
        document.getElementById('btn-calc').disabled=true;
        document.getElementById('btn-calc-map').disabled = true;
    }

    drawPoints();
}

function onCircleClick(){
    // Called when the user clicks on a room circle on the map
    // First click : start node, Second click : end node, Third click : reset and start node
    var n = this.node;

    if (startNode===null){
        startNode = n;
    }else if(endNode===null){
        endNode= n;
    }else{
        startNode=n;
        endNode=null;
        pathNodes=[];
        document.getElementById('instructions').innerHTML='';
        document.getElementById('title-instructions').style.display='none';
    }

    // Update the UI labels
    if (startNode !== null) {
        document.getElementById('lbl-start').textContent = startNode.label;
        document.getElementById('search-start').value = startNode.label;
    } else {
        document.getElementById('lbl-start').textContent = '—';
    }

    if (endNode !== null) {
        document.getElementById('lbl-end').textContent = endNode.label;
        document.getElementById('search-end').value = endNode.label;
    } else {
        document.getElementById('lbl-end').textContent = '—';
    }

    // Enable the calculate button if both nodes are selected
    if (startNode !==null && endNode!==null){
        document.getElementById('btn-calc').disabled= false;
        document.getElementById('btn-calc-map').disabled = false;
    }else{
        document.getElementById('btn-calc').disabled=true;
        document.getElementById('btn-calc-map').disabled = true;
    }

    drawPoints();
}

function onPMRChange(){
    // Called whent he user activate PMR mode
    pmrMode = document.getElementById('pmr-mode').checked;
    
    // Reset selected nodes if they are not PMR accessible
    if (pmrMode){
        if (startNode !== null && startNode.pmr === false){
            startNode = null;
            document.getElementById('lbl-start').textContent = '—';
            document.getElementById('search-start').value = '';
        }
        if (endNode !== null && endNode.pmr === false){
            endNode = null;
            document.getElementById('lbl-end').textContent = '—';
            document.getElementById('search-end').value = '';
        }
    }

    // Enable or disable the calculate button
    if (startNode !== null && endNode !== null){
        document.getElementById('btn-calc').disabled = false;
        document.getElementById('btn-calc-map').disabled = false;
    } else {
        document.getElementById('btn-calc').disabled = true;
        document.getElementById('btn-calc-map').disabled = true;
    }

    drawPoints();
}

function resetAll() {
    // Reset all selections and clear the map and instructions
    startNode = null;
    endNode = null;
    pathNodes = [];

    document.getElementById('search-start').value = '';
    document.getElementById('search-end').value = '';
    document.getElementById('lbl-start').textContent = '—';
    document.getElementById('lbl-end').textContent = '—';
    document.getElementById('btn-calc').disabled = true;
    document.getElementById('title-instructions').style.display = 'none';
    document.getElementById('instructions').innerHTML = '';
    document.getElementById('warning').style.display = 'none';

    drawPoints();
}

function enableCalcButton() {
    // Enable the calculate button when called after a QR code sets the start node
    if (typeof startNode !== "undefined" && typeof endNode !== "undefined" && startNode && endNode) {
        document.getElementById("btn-calc").disabled = false;
        document.getElementById("btn-calc-map").disabled = false;
    }
}

// Events listeners
document.getElementById('search-start').addEventListener('input', onSearchStart);
document.getElementById('search-end').addEventListener('input', onSearchEnd);
document.getElementById('pmr-mode').addEventListener('change', onPMRChange);