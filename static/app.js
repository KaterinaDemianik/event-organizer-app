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
