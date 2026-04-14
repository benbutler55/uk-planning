/**
 * Shared filter script — discovers filterable tables from the DOM.
 *
 * For each unique table id referenced by [data-table] controls:
 *   - Finds the table element, its rows, associated controls, and count element
 *   - Determines filter fields from data attributes on the first <tbody tr>
 *   - Reads shared filters from a data-shared-filters attribute on the <table>
 *   - Applies initial filters from URL params and localStorage shared state
 *   - Runs filter on input/change events
 *   - Persists shared filters to localStorage and URL params
 */
(function() {
  var sharedKey = 'uk-planning-shared-filters-v1';

  function loadSharedState() {
    try {
      return JSON.parse(localStorage.getItem(sharedKey) || '{}');
    } catch (e) {
      return {};
    }
  }

  // Collect all unique table ids referenced by filter controls
  var allControls = Array.from(document.querySelectorAll('[data-table]'));
  var tableIds = [];
  var seen = {};
  allControls.forEach(function(c) {
    var tid = c.getAttribute('data-table');
    if (tid && !seen[tid]) {
      seen[tid] = true;
      tableIds.push(tid);
    }
  });

  tableIds.forEach(function(tableId) {
    var table = document.getElementById(tableId);
    if (!table) return;

    var rows = Array.from(table.querySelectorAll('tbody tr'));
    var controls = Array.from(document.querySelectorAll('[data-table="' + tableId + '"]'));
    var countEl = document.querySelector('[data-filter-count-for="' + tableId + '"]');

    // Determine filter fields from data attributes on the first tbody row
    var fields = [];
    var firstRow = table.querySelector('tbody tr');
    if (firstRow) {
      var attrs = firstRow.attributes;
      for (var i = 0; i < attrs.length; i++) {
        var name = attrs[i].name;
        if (name.indexOf('data-') === 0) {
          fields.push(name.substring(5));
        }
      }
    }

    // Read shared filters from data-shared-filters attribute on the table
    var sharedFilters = [];
    var sharedAttr = table.getAttribute('data-shared-filters');
    if (sharedAttr) {
      try {
        sharedFilters = JSON.parse(sharedAttr);
      } catch (e) {
        sharedFilters = sharedAttr.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
      }
    }

    function applyInitialSharedFilters() {
      var params = new URLSearchParams(window.location.search);
      if (!Array.from(params.keys()).length && window.location.hash) {
        params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
      }
      var stored = loadSharedState();
      controls.forEach(function(control) {
        var key = control.dataset.filter;
        var fromUrl = (params.get(key) || '').toLowerCase().trim();
        var fromStore = sharedFilters.indexOf(key) !== -1 ? (stored[key] || '').toLowerCase().trim() : '';
        var next = fromUrl || fromStore;
        if (!next) return;
        var hasOption = Array.from(control.options || []).some(function(opt) {
          return (opt.value || '').toLowerCase() === next;
        });
        if (hasOption) {
          control.value = next;
        } else if (control.dataset.filter === 'search') {
          control.value = next;
        }
      });
    }

    function persistSharedFilters() {
      if (!sharedFilters.length) return;
      var params = new URLSearchParams(window.location.search);
      var stored = loadSharedState();
      controls.forEach(function(control) {
        var key = control.dataset.filter;
        if (sharedFilters.indexOf(key) === -1) return;
        var value = (control.value || '').toLowerCase().trim();
        if (value) {
          stored[key] = value;
          params.set(key, value);
        } else {
          delete stored[key];
          params.delete(key);
        }
      });
      localStorage.setItem(sharedKey, JSON.stringify(stored));
      var query = params.toString();
      history.replaceState(null, '', window.location.pathname + (query ? ('?' + query) : ''));
    }

    applyInitialSharedFilters();

    function update() {
      var visible = 0;
      var sc = controls.find(function(c) { return c.dataset.filter === 'search'; });
      var st = sc ? sc.value.toLowerCase().trim() : '';
      var sel = {};
      controls.forEach(function(c) {
        if (c.dataset.filter !== 'search' && c.value) sel[c.dataset.filter] = c.value.toLowerCase();
      });
      rows.forEach(function(row) {
        var show = true;
        for (var f in sel) { if ((row.dataset[f] || '') !== sel[f]) show = false; }
        if (show && st) {
          var blob = fields.map(function(f) { return row.dataset[f] || ''; }).join(' ');
          if (blob.indexOf(st) === -1) show = false;
        }
        row.classList.toggle('hidden-row', !show);
        if (show) visible++;
      });
      if (countEl) countEl.textContent = visible + ' of ' + rows.length + ' rows shown';
      persistSharedFilters();
    }

    controls.forEach(function(c) {
      c.addEventListener('input', update);
      c.addEventListener('change', update);
    });
    update();
  });
})();
