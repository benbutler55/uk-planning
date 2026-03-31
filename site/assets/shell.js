(function() {
  var key = 'uk-planning-view-mode-v1';
  var shell = document.querySelector('.layout');
  if (!shell) return;
  var toggle = document.getElementById('view-mode-toggle');
  var plainToggle = document.getElementById('plain-language-toggle');
  var defaultMode = localStorage.getItem(key) || 'guided';
  shell.dataset.viewMode = defaultMode;
  if (toggle) toggle.value = defaultMode;
  var plain = localStorage.getItem('uk-planning-plain-language-v1') || 'off';
  if (plainToggle) plainToggle.checked = plain === 'on';
  shell.dataset.plainLanguage = plain;

  function persist() {
    var mode = toggle ? toggle.value : shell.dataset.viewMode || 'guided';
    shell.dataset.viewMode = mode;
    localStorage.setItem(key, mode);
    var p = plainToggle && plainToggle.checked ? 'on' : 'off';
    shell.dataset.plainLanguage = p;
    localStorage.setItem('uk-planning-plain-language-v1', p);
  }

  if (toggle) toggle.addEventListener('change', persist);
  if (plainToggle) plainToggle.addEventListener('change', persist);

  document.addEventListener('click', function(evt) {
    var copyBtn = evt.target.closest('[data-copy-view]');
    if (!copyBtn) return;
    var text = window.location.href;
    var done = function(ok) {
      copyBtn.textContent = ok ? 'Copied' : 'Copy failed';
      setTimeout(function() { copyBtn.textContent = 'Copy this view'; }, 1200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function() { done(true); }).catch(function() { done(false); });
    } else {
      done(false);
    }
  });

  function logEvent(name, meta) {
    try {
      var evtKey = 'uk-planning-ux-events-v1';
      var events = JSON.parse(localStorage.getItem(evtKey) || '[]');
      events.push({
        ts: new Date().toISOString(),
        page: window.location.pathname.replace(/^\//, ''),
        name: name,
        meta: meta || {},
      });
      localStorage.setItem(evtKey, JSON.stringify(events.slice(-400)));
    } catch (e) {}
  }

  logEvent('page_view', { mode: shell.dataset.viewMode, plain_language: shell.dataset.plainLanguage });
  document.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', function() {
      logEvent('link_click', { href: a.getAttribute('href') || '' });
    });
  });

  /* Collapsible shell utilities */
  var utilSection = document.querySelector('.shell-utilities');
  if (utilSection) {
    var utilBody = utilSection.querySelector('.utility-body');
    var utilToggle = utilSection.querySelector('.utility-toggle');
    if (utilToggle && utilBody) {
      utilToggle.addEventListener('click', function() {
        var expanded = utilBody.style.display !== 'none';
        utilBody.style.display = expanded ? 'none' : 'block';
        utilToggle.setAttribute('aria-expanded', String(!expanded));
        utilToggle.textContent = expanded ? 'Settings & trust info' : 'Hide settings';
        localStorage.setItem('uk-planning-util-open-v1', expanded ? 'closed' : 'open');
      });
      var saved = localStorage.getItem('uk-planning-util-open-v1');
      if (saved !== 'open') {
        utilBody.style.display = 'none';
        utilToggle.setAttribute('aria-expanded', 'false');
        utilToggle.textContent = 'Settings & trust info';
      }
    }
  }

  /* Back to top button */
  var topBtn = document.getElementById('back-to-top');
  if (topBtn) {
    window.addEventListener('scroll', function() {
      topBtn.style.display = window.scrollY > 400 ? 'flex' : 'none';
    });
    topBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* Mobile nav hamburger */
  var hamburger = document.querySelector('.nav-hamburger');
  var navPanel = document.querySelector('.nav-panel');
  if (hamburger && navPanel) {
    hamburger.addEventListener('click', function() {
      var open = navPanel.classList.toggle('nav-panel--open');
      hamburger.setAttribute('aria-expanded', String(open));
      hamburger.textContent = open ? '\u2715' : '\u2630';
    });
  }

  /* Mobile table tap hint */
  document.querySelectorAll('.dense-table').forEach(function(table) {
    if (window.matchMedia('(max-width: 900px)').matches) {
      table.querySelectorAll('tbody tr').forEach(function(row) {
        if (!row.classList.contains('hidden-row')) {
          row.style.cursor = 'pointer';
        }
      });
    }
  });

  /* Cell truncation expand */
  document.addEventListener('click', function(evt) {
    var cell = evt.target.closest('.cell-truncate');
    if (cell) {
      cell.classList.toggle('cell-expanded');
    }
  });
})();

/* Comparison history */
(function() {
  var HISTORY_KEY = 'uk-planning-compare-history-v1';
  var MAX_ENTRIES = 10;

  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function saveHistory(entries) {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)));
  }

  function recordComparison() {
    var params = new URLSearchParams(window.location.search);
    if (!params.get('a') && !params.get('b') && window.location.hash) {
      params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    }
    var a = (params.get('a') || '').trim();
    var b = (params.get('b') || '').trim();
    if (!a || !b) return;
    var history = loadHistory();
    // Remove duplicate
    history = history.filter(function(entry) {
      return !(entry.a === a && entry.b === b);
    });
    history.unshift({ a: a, b: b, ts: new Date().toISOString() });
    saveHistory(history);
  }

  function renderHistory() {
    var container = document.getElementById('compare-history');
    if (!container) return;
    var history = loadHistory();
    // Clear existing content safely
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    if (!history.length) {
      var empty = document.createElement('p');
      empty.className = 'small';
      empty.textContent = 'No recent comparisons yet.';
      container.appendChild(empty);
      return;
    }
    var list = document.createElement('ul');
    history.forEach(function(entry) {
      var li = document.createElement('li');
      var link = document.createElement('a');
      link.href = 'compare.html?a=' + encodeURIComponent(entry.a) + '&b=' + encodeURIComponent(entry.b);
      link.textContent = entry.a + ' vs ' + entry.b;
      li.appendChild(link);
      if (entry.ts) {
        var ts = document.createElement('span');
        ts.className = 'small';
        ts.textContent = ' (' + entry.ts.substring(0, 10) + ')';
        li.appendChild(ts);
      }
      list.appendChild(li);
    });
    container.appendChild(list);
    var clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.textContent = 'Clear history';
    clearBtn.addEventListener('click', function() {
      localStorage.removeItem(HISTORY_KEY);
      renderHistory();
    });
    container.appendChild(clearBtn);
  }

  // Record if on compare page with both params
  if (window.location.pathname.indexOf('compare.html') !== -1) {
    recordComparison();
  }

  // Render if container exists
  renderHistory();
})();
