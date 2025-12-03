// Theme toggle and footer year
(function(){
  const YEAR = new Date().getFullYear();
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = YEAR;

  const KEY = 'theme';
  const saved = localStorage.getItem(KEY);
  // Default to light theme unless user explicitly saved a choice
  const theme = saved || 'light';
  document.documentElement.dataset.theme = theme;

  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(KEY, theme);
  }

  const btn = document.querySelector('.theme-toggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const current = document.documentElement.dataset.theme || 'light';
      apply(current === 'light' ? 'dark' : 'light');
    });
  }
})();

// Scroll position restoration
(function(){
  const SCROLL_KEY = 'scrollPos';
  
  // Відновлюємо позицію скролу після завантаження сторінки
  window.addEventListener('load', function() {
    const savedScroll = sessionStorage.getItem(SCROLL_KEY);
    if (savedScroll) {
      setTimeout(function() {
        window.scrollTo(0, parseInt(savedScroll, 10));
      }, 50);  // Невелика затримка для коректного відновлення
      sessionStorage.removeItem(SCROLL_KEY);
    }
  });
  
  // Зберігаємо позицію скролу перед переходом на іншу сторінку
  window.addEventListener('beforeunload', function() {
    sessionStorage.setItem(SCROLL_KEY, window.pageYOffset || document.documentElement.scrollTop);
  });
  
  // Зберігаємо позицію при кліку на посилання. Ігноруємо посилання, що відкриваються в новій вкладці
  document.addEventListener('click', function(e) {
    const a = e.target.closest('a');
    if (!a) return;
    if (a.target === '_blank' || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    sessionStorage.setItem(SCROLL_KEY, window.pageYOffset || document.documentElement.scrollTop);
  });
})();