/**
 * Shared mobile detail drawer script.
 *
 * For each .dense-table:
 *   - Creates a single drawer element appended to document.body
 *   - Reads column labels from <thead th> elements
 *   - On click of a tbody row (at mobile widths), shows the drawer with cell values labeled
 */
(function() {
  var denseTables = Array.from(document.querySelectorAll('.dense-table'));
  if (!denseTables.length) return;

  // Create one shared drawer element
  var drawer = document.createElement('div');
  drawer.className = 'mobile-drawer';

  var backdrop = document.createElement('div');
  backdrop.className = 'mobile-drawer-backdrop';
  drawer.appendChild(backdrop);

  var panel = document.createElement('div');
  panel.className = 'mobile-drawer-panel';

  var closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'mobile-drawer-close';
  closeBtn.setAttribute('aria-label', 'Close details');
  closeBtn.textContent = 'Close';
  panel.appendChild(closeBtn);

  var body = document.createElement('div');
  body.className = 'mobile-drawer-body';
  panel.appendChild(body);

  drawer.appendChild(panel);
  document.body.appendChild(drawer);

  function closeDrawer() {
    drawer.classList.remove('open');
  }

  backdrop.addEventListener('click', closeDrawer);
  closeBtn.addEventListener('click', closeDrawer);

  var media = window.matchMedia('(max-width: 900px)');

  denseTables.forEach(function(table) {
    // Read labels from thead
    var labels = [];
    var ths = Array.from(table.querySelectorAll('thead th'));
    ths.forEach(function(th) {
      labels.push(th.textContent.trim());
    });

    table.addEventListener('click', function(evt) {
      if (!media.matches) return;
      if (evt.target.closest('a')) return;
      var row = evt.target.closest('tbody tr');
      if (!row) return;
      if (row.classList.contains('hidden-row') || row.classList.contains('hidden-peer')) return;

      var cells = Array.from(row.children);
      // Clear previous content
      while (body.firstChild) {
        body.removeChild(body.firstChild);
      }
      cells.forEach(function(cell, idx) {
        var label = labels[idx] || ('Column ' + (idx + 1));
        var value = (cell.innerText || '').trim();
        if (!value) return;

        var item = document.createElement('div');
        item.className = 'mobile-drawer-item';

        var h4 = document.createElement('h4');
        h4.textContent = label;
        item.appendChild(h4);

        var p = document.createElement('p');
        p.textContent = value;
        item.appendChild(p);

        body.appendChild(item);
      });
      drawer.classList.add('open');
    });
  });
})();
