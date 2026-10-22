(() => {
  const root = document.documentElement;
  const lang = root.lang === 'en' ? 'en' : 'sv';
  const t = {
    sv: {
      openMenu: 'Öppna menyn', closeMenu: 'Stäng menyn',
      toDark: 'Byt till mörkt läge', toLight: 'Byt till ljust läge',
      sending: 'Skickar...', submit: 'Skicka förfrågan',
      noEndpoint: 'Kontaktformuläret saknar data-endpoint. Inget skickades.',
      plan: (name) => `Vi är intresserade av paketet ${name}.`,
      locale: 'sv-SE',
    },
    en: {
      openMenu: 'Open menu', closeMenu: 'Close menu',
      toDark: 'Switch to dark mode', toLight: 'Switch to light mode',
      sending: 'Sending...', submit: 'Send request',
      noEndpoint: 'The contact form has no data-endpoint. Nothing was sent.',
      plan: (name) => `We are interested in the ${name} package.`,
      locale: 'en-GB',
    },
  }[lang];

  const header = document.querySelector('[data-header]');
  const toggle = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('[data-mobile-menu]');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Theme: follows the system until the visitor picks one, then remembered
  const themeBtn = document.querySelector('[data-theme-toggle]');
  const themeIcon = document.querySelector('[data-theme-icon]');
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => (root.getAttribute('data-theme') || (systemDark.matches ? 'dark' : 'light')) === 'dark';
  const syncThemeUi = () => {
    const dark = isDark();
    if (themeIcon) themeIcon.className = `ph-light ${dark ? 'ph-sun' : 'ph-moon'}`;
    if (themeBtn) themeBtn.setAttribute('aria-label', dark ? t.toLight : t.toDark);
    document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute('content', dark ? '#070B16' : '#F5F6F9'));
  };
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const next = isDark() ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* storage unavailable */ }
      syncThemeUi();
    });
  }
  systemDark.addEventListener('change', syncThemeUi);
  syncThemeUi();

  // Header gets a solid background once the page has scrolled past the top
  const sentinel = document.querySelector('.top-sentinel');
  if (sentinel && 'IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      header.classList.toggle('is-scrolled', !entry.isIntersecting);
    }).observe(sentinel);
  }

  // Mobile menu
  const setMenu = (open) => {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.sr-only').textContent = open ? t.closeMenu : t.openMenu;
    menu.hidden = !open;
    header.classList.toggle('is-open', open);
    document.body.classList.toggle('menu-open', open);
  };
  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !menu.hidden) { setMenu(false); toggle.focus(); }
  });
  window.matchMedia('(min-width: 961px)').addEventListener('change', (e) => { if (e.matches) setMenu(false); });

  if ('IntersectionObserver' in window) {
    // Reveal on scroll
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

    // Highlight the nav link for the section in view
    const navLinks = [...document.querySelectorAll('.nav-list a[href^="#"]')];
    const sections = navLinks.map((a) => document.querySelector(a.getAttribute('href'))).filter(Boolean);
    const inView = new Set();
    const navIo = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) inView.add(entry.target.id); else inView.delete(entry.target.id);
      });
      navLinks.forEach((a) => a.classList.toggle('is-active', inView.has(a.getAttribute('href').slice(1))));
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach((s) => navIo.observe(s));

    // Sticky mobile CTA: visible after the hero, hidden while the contact form is on screen
    const mobileCta = document.querySelector('[data-mobile-cta]');
    const hero = document.querySelector('.hero, .page-hero');
    const contact = document.querySelector('.site-footer');
    if (mobileCta && hero && contact) {
      let pastHero = false; let atContact = false;
      const update = () => {
        const show = pastHero && !atContact;
        mobileCta.classList.toggle('is-visible', show);
        mobileCta.setAttribute('aria-hidden', String(!show));
        mobileCta.querySelector('a').tabIndex = show ? 0 : -1;
      };
      new IntersectionObserver(([e]) => { pastHero = !e.isIntersecting; update(); }).observe(hero);
      new IntersectionObserver(([e]) => { atContact = e.isIntersecting; update(); }).observe(contact);
    }

    // Count-up for the example report numbers
    if (!reduce) {
      const cio = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          const end = +el.dataset.count;
          const t0 = performance.now();
          const tick = (now) => {
            const p = Math.min((now - t0) / 1400, 1);
            el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3))).toLocaleString(t.locale);
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
          cio.unobserve(el);
        });
      }, { threshold: 0.6 });
      document.querySelectorAll('[data-count]').forEach((el) => { el.textContent = '0'; cio.observe(el); });
    }
  } else {
    document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-in'));
  }

  // Contact form
  const form = document.querySelector('[data-form]');
  if (form) {
    const success = document.querySelector('[data-form-success]');
    const formError = form.querySelector('[data-form-error]');
    const submit = form.querySelector('[data-submit]');
    const submitLabel = form.querySelector('[data-submit-label]');
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

    const validateField = (input) => {
      const error = document.getElementById(input.getAttribute('aria-describedby'));
      let ok;
      if (input.type === 'checkbox') {
        ok = input.checked;
      } else {
        const value = input.value.trim();
        ok = value.length > 0;
        if (ok && input.type === 'email') ok = emailPattern.test(value);
      }
      input.setAttribute('aria-invalid', String(!ok));
      if (error) error.hidden = ok;
      return ok;
    };

    const required = [...form.querySelectorAll('[required]')];
    required.forEach((input) => {
      input.addEventListener('blur', () => { if (input.type !== 'checkbox' && input.value.trim()) validateField(input); });
      input.addEventListener(input.type === 'checkbox' ? 'change' : 'input', () => {
        if (input.getAttribute('aria-invalid') === 'true') validateField(input);
      });
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      formError.hidden = true;
      const invalid = required.filter((input) => !validateField(input));
      if (invalid.length) { invalid[0].focus(); return; }

      submit.disabled = true;
      submitLabel.textContent = t.sending;

      try {
        const honeypot = form.querySelector('[name="_gotcha"]');
        // Set data-endpoint on the form (e.g. a Formspree URL) to send real submissions.
        const endpoint = form.dataset.endpoint;
        if (honeypot && honeypot.value) {
          // Bot filled the hidden field: pretend success, send nothing
        } else if (endpoint) {
          const res = await fetch(endpoint, {
            method: 'POST',
            headers: { Accept: 'application/json' },
            body: new FormData(form),
          });
          if (!res.ok) throw new Error(`Status ${res.status}`);
        } else {
          console.warn(t.noEndpoint);
          await new Promise((r) => setTimeout(r, 600));
        }
        form.hidden = true;
        success.hidden = false;
        success.focus();
      } catch (err) {
        formError.hidden = false;
        submit.disabled = false;
        submitLabel.textContent = t.submit;
      }
    });
  }

  // Partner/client logos: use the image file if it exists, otherwise keep the name as text
  document.querySelectorAll('[data-logo]').forEach((el) => {
    const img = new Image();
    img.alt = el.textContent.trim();
    img.onload = () => { el.textContent = ''; el.appendChild(img); };
    img.src = el.dataset.logo;
  });

  // Package buttons prefill the contact form message
  document.querySelectorAll('[data-plan]').forEach((btn) => btn.addEventListener('click', () => {
    const msg = document.getElementById('f-msg');
    if (msg && !msg.value) msg.value = t.plan(btn.dataset.plan);
  }));

  // Team photos: show the photo once the file exists, otherwise keep the placeholder
  document.querySelectorAll('[data-photo]').forEach((fig) => {
    const img = new Image();
    img.alt = (fig.closest('.person')?.querySelector('.person-name')?.textContent || '').trim();
    img.onload = () => { fig.innerHTML = ''; fig.appendChild(img); };
    img.src = fig.dataset.photo;
  });

  // Contact page: prefill the chosen package from ?paket= / ?package=
  const params = new URLSearchParams(location.search);
  const pkg = params.get('paket') || params.get('package');
  const msgField = document.getElementById('f-msg');
  if (pkg && msgField && !msgField.value) msgField.value = t.plan(pkg);
  // ?behov= / ?needs= (or a chosen package) preselects the matching choice
  const need = params.get('behov') || params.get('needs') || (pkg ? (lang === 'en' ? 'Websites' : 'Hemsidor') : null);
  if (need) document.querySelectorAll('.choice input').forEach((i) => { if (i.value === need) i.checked = true; });

  const year = document.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();
})();
