// ===== Theme Toggle =====
function toggleTheme() {
  const isDark = document.body.classList.toggle('dark');
  localStorage.setItem('paper-theme', isDark ? 'dark' : 'light');
}
// Restore theme preference
const savedTheme = localStorage.getItem('paper-theme');
if (savedTheme === 'dark') document.body.classList.add('dark');

// ===== Language Toggle =====
function setLang(lang) {
  document.body.classList.toggle('en', lang === 'en');
  document.getElementById('btn-zh').classList.toggle('active', lang === 'zh');
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');
  localStorage.setItem('paper-lang', lang);
}
// Restore language preference
const savedLang = localStorage.getItem('paper-lang');
if (savedLang === 'en') setLang('en');

// ===== TOC Toggle (Mobile) =====
function toggleTOC() {
  document.getElementById('toc').classList.toggle('open');
}
// Close TOC when clicking a link (mobile)
document.querySelectorAll('.toc-sidebar a').forEach(a => {
  a.addEventListener('click', () => {
    document.getElementById('toc').classList.remove('open');
  });
});

// ===== Active TOC Highlight =====
const sections = document.querySelectorAll('section[id], .subsection[id]');
const tocLinks = document.querySelectorAll('.toc-sidebar a');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      tocLinks.forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === '#' + entry.target.id);
      });
    }
  });
}, { rootMargin: '-20% 0px -70% 0px' });
sections.forEach(s => observer.observe(s));

// ===== Fade-in on Scroll =====
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach(el => fadeObserver.observe(el));

// ===== Image Placeholder -> Real Image Replacement =====
// imageMap should be defined before this script as: const imageMap = { ... };
if (typeof imageMap !== 'undefined') {
  Object.entries(imageMap).forEach(([id, src]) => {
    const el = document.getElementById(id);
    if (el) {
      const img = new Image();
      img.onload = () => {
        // Label can be bilingual (recommended: two spans with lang-zh/lang-en)
        // or legacy single-text (fallback: same text for both languages)
        const labelEl = el.querySelector('.ph-label');
        const labelZhSpan = el.querySelector('.ph-label [lang-zh]');
        const labelEnSpan = el.querySelector('.ph-label [lang-en]');
        const fallbackLabel = labelEl ? labelEl.textContent.trim() : '';
        const labelZh = labelZhSpan ? labelZhSpan.textContent.trim() : fallbackLabel;
        const labelEn = labelEnSpan ? labelEnSpan.textContent.trim() : fallbackLabel;
        const captionZh = el.querySelector('.ph-caption[lang-zh]');
        const captionEn = el.querySelector('.ph-caption[lang-en]');
        const zhText = captionZh ? captionZh.textContent : '';
        const enText = captionEn ? captionEn.textContent : '';
        el.outerHTML = `<figure style="margin:0;">
          <img class="fig-img" src="${src}" alt="${labelEn || labelZh}" loading="lazy"
               style="width:100%;border-radius:var(--radius);border:1px solid var(--border);">
          <figcaption style="font-size:12.5px;color:var(--text-secondary);margin-top:8px;line-height:1.5;">
            <strong><span lang-zh>${labelZh}</span><span lang-en>${labelEn}</span></strong><br>
            <span lang-zh>${zhText}</span>
            <span lang-en>${enText}</span>
          </figcaption>
        </figure>`;
      };
      img.src = src;
    }
  });
}
