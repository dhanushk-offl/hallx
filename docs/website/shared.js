/* shared.js */

const HALLX_SITE = {
  name: 'hallx',
  author: 'Dhanush Kandhan',
  repoUrl: 'https://github.com/dhanushk-offl/hallx',
  discussionsUrl: 'https://github.com/dhanushk-offl/hallx/discussions',
  pypiUrl: 'https://pypi.org/project/hallx/',
  logoUrl: 'https://res.cloudinary.com/dwir71gi2/image/upload/v1774898674/Untitled_2_b5xwxj.png',
  defaultBaseUrl: 'https://dhanushk-offl.github.io/hallx/docs/website/',
  defaultOgImage: 'og-image.svg',
};

const PAGE_SEO = {
  'index.html': {
    title: 'hallx - LLM Hallucination Detection, Guardrails, and Risk Scoring for Python',
    description:
      'hallx is a lightweight Python library for LLM hallucination detection, grounding checks, schema validation, response consistency scoring, and production AI guardrails.',
    keywords: [
      'hallx',
      'hallx python',
      'hallx library',
      'llm hallucination detection',
      'llm guardrails python',
      'python ai guardrails',
      'response consistency scoring',
      'schema validation for llm output',
      'grounding checks for llm',
      'rag hallucination checker',
      'hallx alternatives',
      'openai guardrails alternative',
      'dhanush kandhan',
      'dhanush kandhan hallx',
    ],
    type: 'website',
    ogTitle: 'hallx',
    ogEyebrow: 'LLM Guardrails for Production',
    ogSubtitle:
      'Score schema validity, consistency, and grounding before your AI app takes action.',
  },
  'docs.html': {
    title: 'hallx Documentation - Python LLM Guardrails, Hallucination Scoring, and API Guide',
    description:
      'Read the hallx documentation for installation, quickstart usage, risk scoring, calibration, strict gating, provider adapters, and production integration patterns.',
    keywords: [
      'hallx docs',
      'hallx documentation',
      'hallx api',
      'python llm guardrails docs',
      'hallucination detection python docs',
      'llm grounding checks',
      'schema validation ai outputs',
      'hallx usage guide',
      'dhanush kandhan hallx docs',
    ],
    type: 'article',
    ogTitle: 'hallx Documentation',
    ogEyebrow: 'Usage Guide',
    ogSubtitle:
      'Install hallx, add it to your pipeline, and tune scoring for production AI workflows.',
  },
  'samples.html': {
    title: 'hallx Code Samples - Python Examples for LLM Hallucination Detection and Guardrails',
    description:
      'Explore runnable hallx code samples for sync checks, async adapters, retry logic, strict mode, and feedback calibration in Python AI applications.',
    keywords: [
      'hallx samples',
      'hallx examples',
      'python llm guardrails examples',
      'hallucination detection python example',
      'openai guardrails sample',
      'hallx code samples',
      'dhanush kandhan hallx examples',
    ],
    type: 'article',
    ogTitle: 'hallx Code Samples',
    ogEyebrow: 'Python Examples',
    ogSubtitle:
      'Copy production-minded examples for sync checks, adapters, retries, and calibration.',
  },
  'faq.html': {
    title: 'hallx FAQ - Search Visibility, Alternatives, and LLM Guardrail Questions',
    description:
      'Common questions about hallx, including how it works, LLM guardrail use cases, alternatives, calibration, and project details from creator Dhanush Kandhan.',
    keywords: [
      'hallx faq',
      'hallx alternatives',
      'llm guardrails alternatives',
      'hallucination detection library faq',
      'who built hallx',
      'dhanush kandhan',
      'dhanush kandhan hallx',
      'hallx project',
    ],
    type: 'article',
    ogTitle: 'hallx FAQ',
    ogEyebrow: 'Questions and Answers',
    ogSubtitle:
      'Understand how hallx works, where it fits, and how it compares with heavier alternatives.',
  },
};

function currentPageName() {
  return location.pathname.split('/').pop() || 'index.html';
}

function normalizeBaseUrl(url) {
  if (!url) return HALLX_SITE.defaultBaseUrl;
  return url.endsWith('/') ? url : url + '/';
}

function getSiteBaseUrl() {
  const configured = document
    .querySelector('meta[name="site-base"]')
    ?.getAttribute('content')
    ?.trim();

  if (configured) return normalizeBaseUrl(configured);

  if (/^https?:$/i.test(location.protocol) && location.host) {
    const pathParts = location.pathname.split('/');
    pathParts.pop();
    return normalizeBaseUrl(location.origin + pathParts.join('/'));
  }

  return HALLX_SITE.defaultBaseUrl;
}

function absoluteUrl(pathname) {
  return new URL(pathname, getSiteBaseUrl()).toString();
}

function ensureMeta(attr, key) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  return el;
}

function ensureLink(rel) {
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', rel);
    document.head.appendChild(el);
  }
  return el;
}

function setMeta(attr, key, value) {
  ensureMeta(attr, key).setAttribute('content', value);
}

function removeStructuredData() {
  document
    .querySelectorAll('script[data-hallx-seo="true"]')
    .forEach((node) => node.remove());
}

function pushStructuredData(payload) {
  const script = document.createElement('script');
  script.type = 'application/ld+json';
  script.dataset.hallxSeo = 'true';
  script.textContent = JSON.stringify(payload);
  document.head.appendChild(script);
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function wrapWords(text, maxCharsPerLine, maxLines) {
  const words = String(text || '').split(/\s+/).filter(Boolean);
  const lines = [];
  let current = '';

  words.forEach((word) => {
    const next = current ? current + ' ' + word : word;
    if (next.length <= maxCharsPerLine || !current) {
      current = next;
      return;
    }

    lines.push(current);
    current = word;
  });

  if (current) lines.push(current);
  if (lines.length > maxLines) {
    const trimmed = lines.slice(0, maxLines);
    trimmed[maxLines - 1] = trimmed[maxLines - 1].replace(/[.,;:!?-]*$/, '') + '...';
    return trimmed;
  }

  return lines;
}

function buildOgSvg(config) {
  const title = escapeXml(config.title || 'hallx');
  const eyebrow = escapeXml(config.eyebrow || 'LLM Guardrails');
  const rawSubtitle =
    config.subtitle ||
      'Schema validation, grounding checks, and consistency scoring for production AI pipelines.';
  const subtitleLines = wrapWords(rawSubtitle, 45, 3).map(escapeXml);
  const footer = escapeXml(config.footer || 'Built by Dhanush Kandhan');
  const pageLabel = escapeXml(config.pageLabel || currentPageName());
  const subtitleMarkup = subtitleLines
    .map((line, index) => `<text x="126" y="${362 + index * 42}" fill="#475569" font-size="29" font-family="'Segoe UI', Arial, sans-serif" font-weight="500">${line}</text>`)
    .join('\n  ');

  return `
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="${title}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ecfeff" />
      <stop offset="55%" stop-color="#f8fafc" />
      <stop offset="100%" stop-color="#ccfbf1" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#14b8a6" />
      <stop offset="100%" stop-color="#0f766e" />
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#0f172a" flood-opacity="0.10" />
    </filter>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)" />
  <circle cx="1040" cy="118" r="160" fill="#99f6e4" opacity="0.28" />
  <circle cx="143" cy="560" r="180" fill="#14b8a6" opacity="0.10" />
  <path d="M0 494C150 435 308 444 454 483C600 522 728 591 897 568C1034 549 1128 471 1200 416V630H0Z" fill="#ffffff" opacity="0.75" />
  <g opacity="0.18">
    <path d="M92 0V630" stroke="#0f766e" stroke-width="1" />
    <path d="M244 0V630" stroke="#0f766e" stroke-width="1" />
    <path d="M396 0V630" stroke="#0f766e" stroke-width="1" />
    <path d="M548 0V630" stroke="#0f766e" stroke-width="1" />
    <path d="M700 0V630" stroke="#0f766e" stroke-width="1" />
    <path d="M852 0V630" stroke="#0f766e" stroke-width="1" />
    <path d="M1004 0V630" stroke="#0f766e" stroke-width="1" />
  </g>
  <g filter="url(#shadow)">
    <rect x="78" y="66" width="1044" height="498" rx="34" fill="#ffffff" />
    <rect x="78" y="66" width="1044" height="498" rx="34" fill="none" stroke="#d1fae5" />
  </g>
  <rect x="126" y="114" width="172" height="56" rx="28" fill="#ecfdf5" stroke="#99f6e4" />
  <circle cx="160" cy="142" r="18" fill="url(#accent)" />
  <path d="M151 151V133H158V140H169V133H176V151H169V144H158V151Z" fill="#ffffff" />
  <text x="191" y="148" fill="#0f766e" font-size="28" font-family="'Segoe UI', Arial, sans-serif" font-weight="700">hallx</text>
  <text x="126" y="222" fill="#0f766e" font-size="22" font-family="'Segoe UI', Arial, sans-serif" font-weight="700" letter-spacing="2">${eyebrow}</text>
  <text x="126" y="306" fill="#0f172a" font-size="58" font-family="'Segoe UI', Arial, sans-serif" font-weight="800">${title}</text>
  ${subtitleMarkup}
  <rect x="894" y="124" width="182" height="182" rx="28" fill="#f0fdfa" stroke="#99f6e4" />
  <rect x="928" y="158" width="114" height="18" rx="9" fill="#14b8a6" opacity="0.15" />
  <rect x="928" y="196" width="92" height="18" rx="9" fill="#14b8a6" opacity="0.22" />
  <rect x="928" y="234" width="120" height="18" rx="9" fill="#14b8a6" opacity="0.15" />
  <rect x="928" y="272" width="78" height="18" rx="9" fill="#14b8a6" opacity="0.22" />
  <rect x="126" y="494" width="240" height="34" rx="17" fill="#f8fafc" stroke="#e2e8f0" />
  <text x="146" y="516" fill="#475569" font-size="19" font-family="'Segoe UI', Arial, sans-serif" font-weight="600">${footer}</text>
  <rect x="904" y="486" width="172" height="40" rx="20" fill="#0f766e" />
  <text x="938" y="512" fill="#ecfeff" font-size="19" font-family="'Segoe UI', Arial, sans-serif" font-weight="700">${pageLabel}</text>
</svg>`.trim();
}

function svgToDataUri(svg) {
  return 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);
}

function buildOgImageConfig(pageMeta) {
  return {
    title: pageMeta.ogTitle || pageMeta.title || HALLX_SITE.name,
    eyebrow: pageMeta.ogEyebrow || 'LLM Guardrails',
    subtitle: pageMeta.ogSubtitle || pageMeta.description,
    footer: `Built by ${HALLX_SITE.author}`,
    pageLabel: currentPageName().replace('.html', ''),
  };
}

function injectStructuredData(pageMeta) {
  const pageUrl = absoluteUrl(currentPageName());
  const imageUrl = absoluteUrl(HALLX_SITE.defaultOgImage);
  const softwareApp = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: HALLX_SITE.name,
    applicationCategory: 'DeveloperApplication',
    operatingSystem: 'Windows, macOS, Linux',
    softwareVersion: document.querySelector('[data-stat="version"]')?.textContent?.trim() || undefined,
    description: PAGE_SEO['index.html'].description,
    url: absoluteUrl('index.html'),
    image: imageUrl,
    author: {
      '@type': 'Person',
      name: HALLX_SITE.author,
      url: 'https://github.com/dhanushk-offl',
    },
    sameAs: [HALLX_SITE.repoUrl, HALLX_SITE.pypiUrl],
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
  };

  const website = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: HALLX_SITE.name,
    url: absoluteUrl('index.html'),
    description: PAGE_SEO['index.html'].description,
    publisher: {
      '@type': 'Person',
      name: HALLX_SITE.author,
    },
  };

  const webPage = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: pageMeta.title,
    url: pageUrl,
    description: pageMeta.description,
    isPartOf: {
      '@type': 'WebSite',
      name: HALLX_SITE.name,
      url: absoluteUrl('index.html'),
    },
    about: {
      '@type': 'SoftwareApplication',
      name: HALLX_SITE.name,
    },
    primaryImageOfPage: imageUrl,
    author: {
      '@type': 'Person',
      name: HALLX_SITE.author,
    },
  };

  pushStructuredData(softwareApp);
  pushStructuredData(website);
  pushStructuredData(webPage);

  if (currentPageName() === 'faq.html') {
    const questions = Array.from(document.querySelectorAll('.faq-item')).map((item) => {
      const question = item.querySelector('.faq-q')?.childNodes?.[0]?.textContent?.trim();
      const answer = item.querySelector('.faq-a-body')?.textContent?.replace(/\s+/g, ' ')?.trim();
      if (!question || !answer) return null;
      return {
        '@type': 'Question',
        name: question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: answer,
        },
      };
    }).filter(Boolean);

    if (questions.length) {
      pushStructuredData({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: questions,
      });
    }
  }

  if (currentPageName() === 'docs.html') {
    pushStructuredData({
      '@context': 'https://schema.org',
      '@type': 'TechArticle',
      headline: pageMeta.title,
      description: pageMeta.description,
      author: {
        '@type': 'Person',
        name: HALLX_SITE.author,
      },
      url: pageUrl,
      about: ['hallx', 'LLM guardrails', 'hallucination detection', 'Python'],
    });
  }
}

function applySeoMetadata() {
  const pageMeta = PAGE_SEO[currentPageName()] || PAGE_SEO['index.html'];
  const currentUrl = absoluteUrl(currentPageName());
  const staticOgImage = absoluteUrl(HALLX_SITE.defaultOgImage);
  const dynamicOgUri = svgToDataUri(buildOgSvg(buildOgImageConfig(pageMeta)));

  document.title = pageMeta.title;
  ensureLink('canonical').setAttribute('href', currentUrl);

  setMeta('name', 'description', pageMeta.description);
  setMeta('name', 'keywords', pageMeta.keywords.join(', '));
  setMeta('name', 'author', HALLX_SITE.author);
  setMeta('name', 'creator', HALLX_SITE.author);
  setMeta('name', 'publisher', HALLX_SITE.author);
  setMeta('name', 'robots', 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1');
  setMeta('name', 'theme-color', '#0f766e');

  setMeta('property', 'og:site_name', HALLX_SITE.name);
  setMeta('property', 'og:type', pageMeta.type);
  setMeta('property', 'og:title', pageMeta.ogTitle || pageMeta.title);
  setMeta('property', 'og:description', pageMeta.description);
  setMeta('property', 'og:url', currentUrl);
  setMeta('property', 'og:image', staticOgImage);
  setMeta('property', 'og:image:secure_url', staticOgImage);
  setMeta('property', 'og:image:alt', `${pageMeta.ogTitle || pageMeta.title} - hallx`);
  setMeta('property', 'og:locale', 'en_US');

  setMeta('name', 'twitter:card', 'summary_large_image');
  setMeta('name', 'twitter:title', pageMeta.ogTitle || pageMeta.title);
  setMeta('name', 'twitter:description', pageMeta.description);
  setMeta('name', 'twitter:image', staticOgImage);

  setMeta('name', 'x-dynamic-og-image', dynamicOgUri);

  removeStructuredData();
  injectStructuredData(pageMeta);

  window.hallxOgImage = {
    svg: (config = {}) => buildOgSvg({ ...buildOgImageConfig(pageMeta), ...config }),
    dataUri: (config = {}) => svgToDataUri(buildOgSvg({ ...buildOgImageConfig(pageMeta), ...config })),
    fallbackUrl: staticOgImage,
  };
}

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
    toggle.innerHTML =
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg><span>Menu</span>';
    inner.appendChild(toggle);

    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';
    mobileMenu.setAttribute('hidden', '');
    mobileMenu.innerHTML =
      '<ul class="mobile-nav-links">' +
      links.innerHTML +
      '</ul><div class="mobile-nav-actions">' +
      actions.innerHTML +
      '</div>';
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
  const current = currentPageName();
  document.querySelectorAll('.sidebar ul li a, .nav-links a, .mobile-nav-links a').forEach((a) => {
    const href = a.getAttribute('href');
    if (href === current || (current === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });
}

initMobileNav();
setSidebarActive();
applySeoMetadata();

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
    .join('<span class="dot">.</span>');
}

// Live GitHub + package stats
async function loadStats() {
  const setTextAll = (selector, value) => {
    document.querySelectorAll(selector).forEach((el) => {
      el.textContent = value;
      el.classList.remove('loading-stat');
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
        url: 'https://api.allorigins.win/raw?url=' + encodeURIComponent(targetUrl),
        parse: async (res) => res.json(),
      },
      {
        url: 'https://api.codetabs.com/v1/proxy?quest=' + encodeURIComponent(targetUrl),
        parse: async (res) => res.json(),
      },
      {
        url: 'https://corsproxy.io/?url=' + encodeURIComponent(targetUrl),
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
