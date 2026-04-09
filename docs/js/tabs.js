function switchTab(tab) {
    var panels = ['search', 'map', 'instructions'];

    for (var i = 0; i < panels.length; i++) {
        document.getElementById('panel-' + panels[i]).classList.remove('active');
        document.getElementById('tab-' + panels[i]).classList.remove('active');
    }

    document.getElementById('panel-' + tab).classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');
}

function syncInstructions() {
    var content = document.getElementById('instructions').innerHTML;
    document.getElementById('mobile-instructions-content').innerHTML = content;
}