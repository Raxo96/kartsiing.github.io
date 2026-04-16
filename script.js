// Position change indicators
(function() {
    var rows = document.querySelectorAll('tbody tr');
    var numRaces = document.querySelectorAll('thead th').length - 3;
    var drivers = [];

    rows.forEach(function(row) {
        var cells = row.querySelectorAll('td');
        var name = cells[1].textContent.trim();
        var prevTotal = 0;
        for (var i = 2; i < 2 + numRaces - 1; i++) {
            var v = cells[i].textContent.trim();
            prevTotal += (v === '-' ? 0 : parseInt(v));
        }
        drivers.push({ name: name, prevTotal: prevTotal, row: row });
    });

    var sorted = drivers.slice().sort(function(a, b) {
        return b.prevTotal - a.prevTotal || a.name.localeCompare(b.name);
    });

    var prevRanks = {};
    sorted.forEach(function(d, i) { prevRanks[d.name] = i + 1; });

    drivers.forEach(function(d, i) {
        var currentPos = i + 1;
        var prevPos = prevRanks[d.name];
        var diff = prevPos - currentPos;
        var cell = d.row.querySelector('.driver-name');
        var span = document.createElement('span');
        span.className = 'pos-change ';
        if (diff > 0) {
            span.className += 'pos-up';
            span.textContent = '▲' + diff;
        } else if (diff < 0) {
            span.className += 'pos-down';
            span.textContent = '▼' + Math.abs(diff);
        } else {
            span.className += 'pos-same';
            span.textContent = '—';
        }
        cell.appendChild(span);
    });
})();

// Dark mode toggle
function toggleTheme() {
    var b = document.body, btn = document.querySelector('.theme-toggle');
    b.classList.toggle('dark');
    var dark = b.classList.contains('dark');
    btn.textContent = dark ? '☀️' : '🌙';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
}

if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark');
    document.querySelector('.theme-toggle').textContent = '☀️';
}
