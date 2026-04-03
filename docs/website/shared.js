/* shared.js */

// Copy helper
function copyText(text) {
  navigator.clipboard.writeText(text).catch(() => {});
  const t = document.getElementById('toast');
  if (t) {
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
  }
}

// Code block copy buttons
document.querySelectorAll('.code-copy').forEach((btn) => {
  btn.addEventListener('click', () => {
    const code = btn.closest('.code-block')?.querySelector('code');
    if (code) copyText(code.innerText);
  });
});

// Install copy
const installBox = document.querySelector('.hero-install');
if (installBox) {
  installBox.addEventListener('click', () => copyText('pip install hallx'));
}

// Tabs
document.querySelectorAll('.tab-list').forEach((list) => {
  list.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const group = btn.dataset.group;
      const target = btn.dataset.tab;
      list.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll(`.tab-pane[data-group="${group}"]`).forEach((p) => {
        p.classList.toggle('active', p.dataset.tab === target);
      });
    });
  });
});

// FAQ
document.querySelectorAll('.faq-q').forEach((q) => {
  q.addEventListener('click', () => {
    const item = q.closest('.faq-item');
    const open = item.classList.contains('open');
    document.querySelectorAll('.faq-item.open').forEach((i) => i.classList.remove('open'));
    if (!open) item.classList.add('open');
  });
});

// Mobile nav
function initMobileNav() {
  document.querySelectorAll('nav.main-nav').forEach((nav) => {
    const inner = nav.querySelector('.nav-inner');
    const links = inner?.querySelector('.nav-links');
    const actions = inner?.querySelector('.nav-actions');
    if (!inner || !links || !actions || inner.querySelector('.nav-toggle')) return;

    const toggle = document.createElement('button');
    toggle.className = 'nav-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-label', 'Toggle navigation menu');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg><span>Menu</span>';
    inner.appendChild(toggle);

    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';
    mobileMenu.setAttribute('hidden', '');
    mobileMenu.innerHTML = '<ul class="mobile-nav-links">' + links.innerHTML + '</ul><div class="mobile-nav-actions">' + actions.innerHTML + '</div>';
    nav.appendChild(mobileMenu);

    const setOpen = (open) => {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
      if (open) mobileMenu.removeAttribute('hidden');
      else mobileMenu.setAttribute('hidden', '');
    };

    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      setOpen(!nav.classList.contains('open'));
    });

    mobileMenu.addEventListener('click', (e) => {
      if (e.target.closest('a')) setOpen(false);
    });

    document.addEventListener('click', (e) => {
      if (!nav.contains(e.target) && nav.classList.contains('open')) setOpen(false);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('open')) setOpen(false);
    });
  });
}

// Sidebar/nav active link
function setSidebarActive() {
  const current = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar ul li a, .nav-links a, .mobile-nav-links a').forEach((a) => {
    const href = a.getAttribute('href');
    if (href === current || (current === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });
}

initMobileNav();
setSidebarActive();

// Documentation language links (from repo docs folder)
async function loadDocLanguages() {
  const host = document.querySelector('[data-doc-langs]');
  if (!host) return;

  const langName = {
    en: 'English',
    ta: 'Tamil',
    ml: 'Malayalam',
    hi: 'Hindi',
    kn: 'Kannada',
    de: 'German',
    ja: 'Japanese',
    zh: 'Chinese',
  };
  const repoRoot = 'https://github.com/dhanushk-offl/hallx/blob/master/docs/';

  let items = [];
  try {
    const res = await fetch('https://api.github.com/repos/dhanushk-offl/hallx/contents/docs');
    if (res.ok) {
      const data = await res.json();
      items = (Array.isArray(data) ? data : [])
        .map((f) => f?.name || '')
        .filter((name) => /^README\.[a-z]{2}\.md$/i.test(name))
        .map((name) => {
          const code = name.slice(7, 9).toLowerCase();
          return {
            code,
            label: langName[code] || code.toUpperCase(),
            url: repoRoot + name,
          };
        });
    }
  } catch {}

  if (!items.length) {
    items = [
      { code: 'en', label: 'English', url: repoRoot + 'README.en.md' },
      { code: 'ta', label: 'Tamil', url: repoRoot + 'README.ta.md' },
      { code: 'ml', label: 'Malayalam', url: repoRoot + 'README.ml.md' },
      { code: 'hi', label: 'Hindi', url: repoRoot + 'README.hi.md' },
      { code: 'kn', label: 'Kannada', url: repoRoot + 'README.kn.md' },
      { code: 'de', label: 'German', url: repoRoot + 'README.de.md' },
      { code: 'ja', label: 'Japanese', url: repoRoot + 'README.ja.md' },
      { code: 'zh', label: 'Chinese', url: repoRoot + 'README.zh.md' },
    ];
  }

  items.sort((a, b) => {
    if (a.code === 'en') return -1;
    if (b.code === 'en') return 1;
    return a.label.localeCompare(b.label);
  });

  host.innerHTML = items
    .map((x) => `<a href="${x.url}" target="_blank" rel="noopener">${x.label}</a>`)
    .join('<span class="dot">·</span>');
}

// Live GitHub + package stats
async function loadStats() {
  const setTextAll = (selector, value) => {
    document.querySelectorAll(selector).forEach((el) => {
      el.textContent = value;
    });
  };
  const formatCompact = (num) => (num >= 1000 ? (num / 1000).toFixed(1) + 'k' : String(num));
  const pypiCacheKey = 'hallx:pypistats:recent';

  async function fetchJsonWithFallbacks(targetUrl) {
    const requests = [
      {
        url: targetUrl,
        parse: async (res) => res.json(),
      },
      {
        url: 'https://api.allorigins.win/get?url=' + encodeURIComponent(targetUrl),
        parse: async (res) => {
          const data = await res.json();
          return JSON.parse(data.contents);
        },
      },
      {
        url: 'https://api.codetabs.com/v1/proxy?quest=' + encodeURIComponent(targetUrl),
        parse: async (res) => res.json(),
      },
      {
        url: 'https://cors.isomorphic-git.org/' + targetUrl,
        parse: async (res) => res.json(),
      },
    ];

    for (const request of requests) {
      try {
        const res = await fetch(request.url, { cache: 'no-store' });
        if (!res.ok) continue;
        return await request.parse(res);
      } catch {}
    }

    return null;
  }

  let versionTag = '';
  try {
    const gh = await fetch('https://api.github.com/repos/dhanushk-offl/hallx');
    if (gh.ok) {
      const d = await gh.json();
      const stars = d.stargazers_count ?? 0;
      setTextAll('[data-stat="stars"]', formatCompact(stars));
    }
  } catch {}

  try {
    const rel = await fetch('https://api.github.com/repos/dhanushk-offl/hallx/releases/latest');
    if (rel.ok) {
      const d = await rel.json();
      versionTag = (d?.tag_name || '').trim();
    }
  } catch {}

  if (!versionTag) {
    try {
      const tags = await fetch('https://api.github.com/repos/dhanushk-offl/hallx/tags?per_page=1');
      if (tags.ok) {
        const d = await tags.json();
        versionTag = (d?.[0]?.name || '').trim();
      }
    } catch {}
  }

  if (versionTag) {
    setTextAll('[data-stat="version"]', versionTag);
  }

  let monthlyDownloads = null;

  try {
    const d = await fetchJsonWithFallbacks('https://pypistats.org/api/packages/hallx/recent');
    if (typeof d?.data?.last_month === 'number') {
      monthlyDownloads = d.data.last_month;
      try {
        localStorage.setItem(
          pypiCacheKey,
          JSON.stringify({ last_month: monthlyDownloads, saved_at: Date.now() })
        );
      } catch {}
    }
  } catch {}

  if (monthlyDownloads === null) {
    try {
      const cached = JSON.parse(localStorage.getItem(pypiCacheKey) || 'null');
      if (typeof cached?.last_month === 'number') {
        monthlyDownloads = cached.last_month;
      }
    } catch {}
  }

  if (monthlyDownloads === null) {
    try {
      const d = await fetchJsonWithFallbacks('https://pypistats.org/api/packages/hallx/overall');
      const daily = Array.isArray(d?.data) ? d.data : [];
      if (daily.length) {
        const last30 = daily.slice(-30);
        monthlyDownloads = last30.reduce((acc, row) => acc + (Number(row?.downloads) || 0), 0);
      }
    } catch {}
  }

  if (monthlyDownloads !== null) {
    setTextAll('[data-stat="downloads"]', formatCompact(monthlyDownloads));
  }
}

loadStats();
loadDocLanguages();
