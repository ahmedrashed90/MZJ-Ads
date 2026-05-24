(function(){
  'use strict';
  if(window.__mzjMobileResponsiveLoaded) return;
  window.__mzjMobileResponsiveLoaded = true;

  function pageTitle(){
    var active = document.querySelector('.nav-tabs a.active');
    if(active && active.textContent.trim()) return active.textContent.trim();
    var h = document.querySelector('.page-head h2, .mersal-inbox-head h2, .chat-title, h2, title');
    return h ? h.textContent.trim() : 'MZJ CRM';
  }

  function closeSidebar(){ document.body.classList.remove('mzj-sidebar-open'); }
  function openSidebar(){ document.body.classList.add('mzj-sidebar-open'); }

  function init(){
    if(document.getElementById('mzjMobileTopbar')) return;
    document.body.classList.add('mzj-mobile-ready');

    var topbar = document.createElement('div');
    topbar.id = 'mzjMobileTopbar';
    topbar.className = 'mzj-mobile-topbar';
    topbar.innerHTML = '<button type="button" class="mzj-mobile-menu-btn" aria-label="فتح القائمة" aria-expanded="false">☰</button><div class="mzj-mobile-title"></div><div class="mzj-mobile-spacer"></div>';

    var overlay = document.createElement('div');
    overlay.id = 'mzjMobileOverlay';
    overlay.className = 'mzj-mobile-overlay';

    document.body.prepend(overlay);
    document.body.prepend(topbar);

    var title = topbar.querySelector('.mzj-mobile-title');
    if(title) title.textContent = pageTitle();

    var btn = topbar.querySelector('.mzj-mobile-menu-btn');
    if(btn){
      btn.addEventListener('click', function(){
        var isOpen = document.body.classList.toggle('mzj-sidebar-open');
        btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });
    }
    overlay.addEventListener('click', closeSidebar);
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeSidebar(); });

    document.addEventListener('click', function(e){
      var link = e.target.closest && e.target.closest('.sidebar .nav-tabs a');
      if(link) closeSidebar();
    }, true);
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
