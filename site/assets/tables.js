/**
 * Shared table enhancements script — preset buttons, active-filter chips, sortable headers.
 *
 * For tables with a data-presets attribute (JSON array of preset objects):
 *   - Creates preset buttons and active-filter-chips display
 * For all .dense-table elements:
 *   - Makes <thead th> elements sortable (click to sort asc/desc)
 *   - Displays sort state
 */
(function() {

  // --- Preset + chip logic for tables with data-presets ---
  var presetTables = Array.from(document.querySelectorAll('table[data-presets]'));

  presetTables.forEach(function(table) {
    var tableId = table.id;
    if (!tableId) return;

    var presets = [];
    try {
      presets = JSON.parse(table.getAttribute('data-presets'));
    } catch (e) {
      return;
    }

    var controls = Array.from(document.querySelectorAll('[data-table="' + tableId + '"]'));
    var cards = table.closest('.card');

    function ensureContainers() {
      if (!cards) return;
      if (!cards.querySelector('.active-filter-chips')) {
        var chips = document.createElement('p');
        chips.className = 'small active-filter-chips';
        cards.parentNode.insertBefore(chips, cards);
      }
      if (presets.length && !cards.parentNode.querySelector('[data-presets-for="' + tableId + '"]')) {
        var wrap = document.createElement('section');
        wrap.className = 'card';
        wrap.setAttribute('data-presets-for', tableId);

        var h3 = document.createElement('h3');
        h3.textContent = 'Quick presets';
        wrap.appendChild(h3);

        var row = document.createElement('div');
        row.className = 'preset-row';

        presets.forEach(function(p, idx) {
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.setAttribute('data-preset-index', idx);
          btn.textContent = p.label;
          row.appendChild(btn);
        });

        var clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.setAttribute('data-preset-clear', '1');
        clearBtn.textContent = 'Clear presets';
        row.appendChild(clearBtn);

        wrap.appendChild(row);

        var sortState = document.createElement('p');
        sortState.className = 'small';
        sortState.setAttribute('data-sort-state-for', tableId);
        sortState.textContent = 'Sort: none';
        wrap.appendChild(sortState);

        cards.parentNode.insertBefore(wrap, cards);

        wrap.querySelectorAll('[data-preset-index]').forEach(function(btn) {
          btn.addEventListener('click', function() {
            var p = presets[Number(btn.getAttribute('data-preset-index'))] || {};
            controls.forEach(function(c) {
              var key = c.dataset.filter;
              if (key === 'search') return;
              c.value = (p.filters && p.filters[key]) || '';
            });
            controls.forEach(function(c) { c.dispatchEvent(new Event('change', { bubbles: true })); });
          });
        });

        clearBtn.addEventListener('click', function() {
          controls.forEach(function(c) { c.value = ''; c.dispatchEvent(new Event('change', { bubbles: true })); });
        });
      }
    }

    function renderChips() {
      var chips = document.querySelector('.active-filter-chips');
      if (!chips) return;
      var active = [];
      controls.forEach(function(c) {
        var key = c.dataset.filter;
        var value = (c.value || '').trim();
        if (!value) return;
        active.push(key + ': ' + value);
      });
      chips.textContent = active.length ? ('Active filters - ' + active.join(' | ')) : 'Active filters - none';
    }

    ensureContainers();
    renderChips();
    controls.forEach(function(c) { c.addEventListener('input', renderChips); c.addEventListener('change', renderChips); });
  });

  // --- Sortable headers for all .dense-table elements ---
  var denseTables = Array.from(document.querySelectorAll('.dense-table'));

  denseTables.forEach(function(table) {
    var tableId = table.id || '';
    var stateEl = document.querySelector('[data-sort-state-for="' + tableId + '"]');
    var headers = Array.from(table.querySelectorAll('thead th'));

    headers.forEach(function(th, idx) {
      th.classList.add('sortable-th');
      th.setAttribute('aria-sort', 'none');
      th.addEventListener('click', function() {
        var dir = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';
        headers.forEach(function(h) { delete h.dataset.sortDir; h.setAttribute('aria-sort', 'none'); });
        th.dataset.sortDir = dir;
        th.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : 'descending');
        var rows = Array.from(table.querySelectorAll('tbody tr'));
        rows.sort(function(a, b) {
          var av = (a.children[idx] && a.children[idx].innerText || '').trim();
          var bv = (b.children[idx] && b.children[idx].innerText || '').trim();
          var an = parseFloat(av.replace(/[^0-9.+-]/g, ''));
          var bn = parseFloat(bv.replace(/[^0-9.+-]/g, ''));
          var cmp = (!isNaN(an) && !isNaN(bn)) ? (an - bn) : av.localeCompare(bv);
          return dir === 'asc' ? cmp : -cmp;
        });
        var body = table.querySelector('tbody');
        rows.forEach(function(r) { body.appendChild(r); });
        if (stateEl) stateEl.textContent = 'Sort: ' + th.innerText.trim() + ' (' + dir + ')';
      });
    });
  });

})();
