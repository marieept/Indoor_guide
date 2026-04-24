let GRAPH={nodes:[], edges:[]};

var FLOOR_IMAGES = {};

var scale;
if (window.innerWidth <= 768) {
    scale = 0.1;
} else {
    scale = 0.2;
}

var pmrMode = false;

var startNode = null;
var endNode = null;

//Variables pour stocker le chemin
var pathNodes= [];

//Variables pour l'étage actuel
var currentFloor=0;

const container = document.getElementById('map-svg-container');
const img = document.getElementById('plan-img');
const wrapper =  document.getElementById('map-wrapper');

var t0_load = performance.now();

fetch('assets/config_web.json')
    .then(r => r.json())
    .then(config => {
        config.etages.forEach(floor => {
            FLOOR_IMAGES[floor.floor] = floor.svg;
        });
        return fetch('assets/graph.json');
    })
    .then(r => r.json())
    .then(data => {
        // Performances et tests
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
        handleQRParams();
    })

document.getElementById('search-start').addEventListener('input', onSearchStart);
document.getElementById('search-end').addEventListener('input', onSearchEnd);

function onSearchStart(){
    var query = document.getElementById('search-start').value;
    startNode=null;
    document.getElementById('lbl-start').textContent='-';
    displaySuggestions(query, 'start');
}

function onSearchEnd(){
    var query = document.getElementById('search-end').value;
    endNode=null;
    document.getElementById('lbl-end').textContent='-';
    displaySuggestions(query, 'end');
}

function displaySuggestions(query, type){
    var suggBox = document.getElementById('suggestions-' + type);
    suggBox.innerHTML='';

    if (query==='') {
        suggBox.style.border = 'none';
        return;
    }

    // Créer un objet pour regrouper les alias
    let seenAliases = {};

    for (let i=0; i<GRAPH.nodes.length; i++){
        let n = GRAPH.nodes[i];

        if (n.type !== 'room') continue;
        if (pmrMode && n.pmr === false) continue;

        // On compare avec l'alias
        let alias = n.alias || n.label;

        if (alias.toLowerCase().includes(query.toLowerCase())){
            // On ne garde qu'un node par alias
            if (!seenAliases[alias]){
                var div = document.createElement('div');
                div.textContent = alias;

                // on stocke le node exact à utiliser pour le chemin
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

function onSuggestionClick(){
    var n = this.node;
    var type = this.type;

    // Réinitialiser le chemin si un chemin existe déjà
    if (pathNodes.length > 0){
        pathNodes = [];
        document.getElementById('instructions').innerHTML = '';
        document.getElementById('title-instructions').style.display = 'none';
    }

    if (type==='start'){
        startNode = n;
        document.getElementById('lbl-start').textContent= n.label;
        document.getElementById('search-start').value = n.label;
    }else{
        endNode = n;
        document.getElementById('lbl-end').textContent = n.label;
        document.getElementById('search-end').value = n.label;
    }
    
    //On cache les autres suggestions
    document.getElementById('suggestions-'+type).innerHTML='';
    document.getElementById('suggestions-'+type).innerHTML='';
    document.getElementById('suggestions-'+ type).style.border= 'none';

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
    pmrMode = document.getElementById('pmr-mode').checked;
    
    // Réinitialiser si les noeuds sélectionnés ne sont pas accessibles PMR
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

    if (startNode !== null && endNode !== null){
        document.getElementById('btn-calc').disabled = false;
        document.getElementById('btn-calc-map').disabled = false;
    } else {
        document.getElementById('btn-calc').disabled = true;
        document.getElementById('btn-calc-map').disabled = true;
    }

    drawPoints();
}

document.getElementById('pmr-mode').addEventListener('change', onPMRChange);

function resetAll() {
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

function getQueryParams(){
    const params = new URLSearchParams(window.location.search);
    return {
        start: params.get("start")
    };
}

window.addEventListener("load", () => {
    const { start, end } = getQueryParams();

    if (start) {
        setStartFromQR(start);
    }
});

function findNodeById(id) {
    return graph.nodes.find(n => n.id === id);
}

function enableCalcButton() {
    if (typeof startNode !== "undefined" && typeof endNode !== "undefined" && startNode && endNode) {
        document.getElementById("btn-calc").disabled = false;
        document.getElementById("btn-calc-map").disabled = false;
    }
}