// NordenMedia v3: interactive features (calculator, FAQ search,
// booking demo, report months, live destinations).
(() => {
  const en = document.documentElement.lang === 'en';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const locale = en ? 'en-GB' : 'sv-SE';
  const fmt = (n) => Math.round(n).toLocaleString(locale);
  const L = en ? {
    log: (s, t) => [
      `Booking received: ${s}, tomorrow ${t}`,
      'Confirmation emailed to the customer',
      `Reminder scheduled for today at ${t}`,
      'Customer saved in the customer register',
      'Added to the list for follow-up mailings',
    ],
    months: { jul: 'July 2026', aug: 'August 2026', sep: 'September 2026' },
    pct: (v) => `${v}%`, count: (v) => `+${v}`,
  } : {
    log: (s, t) => [
      `Bokning mottagen: ${s}, i morgon ${t}`,
      'Bekräftelse mejlad till kunden',
      `Påminnelse schemalagd i dag kl. ${t}`,
      'Kunden sparad i kundregistret',
      'Tillagd i listan för uppföljande utskick',
    ],
    months: { jul: 'Juli 2026', aug: 'Augusti 2026', sep: 'September 2026' },
    pct: (v) => `${v} %`, count: (v) => `${v} st`,
  };

  // Animate a number from its current value to a target
  const tween = (el, to, ms = 600) => {
    const from = parseFloat((el.textContent || '0').replace(/[^\d.-]/g, '')) || 0;
    if (reduce || from === to) { el.textContent = fmt(to); return; }
    const t0 = performance.now();
    const step = (now) => {
      const p = Math.min((now - t0) / ms, 1);
      el.textContent = fmt(from + (to - from) * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const plural = (scope, n) => scope.querySelectorAll('[data-plural]').forEach((w) => {
    const [one, many] = w.dataset.plural.split('|');
    w.textContent = n === 1 ? one : many;
  });
  const press = (group, btn) => group.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));

  // ---------- Header floats over the dark hero until the hero has scrolled past ----------
  const darkHero = document.querySelector('[data-hero-dark]');
  const siteHeader = document.querySelector('[data-header]');
  if (darkHero && siteHeader && 'IntersectionObserver' in window) {
    const update = () => siteHeader.classList.toggle('is-over-hero', darkHero.getBoundingClientRect().bottom > siteHeader.offsetHeight);
    new IntersectionObserver(update, { threshold: Array.from({ length: 41 }, (_, i) => i / 40) }).observe(darkHero);
    update();
  }

  // ---------- 2. Calculator ----------
  const calc = document.querySelector('[data-calc]');
  if (calc) {
    const val = (k) => +calc.querySelector(`[data-in="${k}"]`).value;
    const update = () => {
      calc.querySelectorAll('[data-in]').forEach((input) => {
        calc.querySelector(`[data-out="${input.dataset.in}"]`).textContent = input.value;
        const pct = ((input.value - input.min) / (input.max - input.min)) * 100;
        input.style.setProperty('--fill', `${pct}%`);
      });
      const hours = val('manual') * 46 + val('admin') * 12; // 46 working weeks a year
      tween(calc.querySelector('[data-res="hours"]'), hours, 400);
      tween(calc.querySelector('[data-res="days"]'), Math.round(hours / 8), 400);
      tween(calc.querySelector('[data-res="invoices"]'), val('vendors') * 12, 400); // one invoice a month per supplier
    };
    calc.addEventListener('input', update);
    update();
  }

  // ---------- 3. FAQ search ----------
  const search = document.querySelector('[data-faq-search]');
  if (search) {
    const items = [...document.querySelectorAll('.faq details')];
    const empty = document.querySelector('[data-faq-empty]');
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      let hits = 0;
      items.forEach((d) => {
        const match = !q || d.textContent.toLowerCase().includes(q);
        d.hidden = !match;
        if (match) hits++;
        if (q && match && q.length > 2) d.open = true;
        if (!q) d.open = false;
      });
      empty.hidden = hits > 0;
    });
  }

  // ---------- 5. Booking demo ----------
  const demo = document.querySelector('[data-demo]');
  if (demo) {
    const log = demo.querySelector('[data-demo-log]');
    const empty = demo.querySelector('[data-demo-empty]');
    const book = demo.querySelector('[data-demo-book]');
    const reset = demo.querySelector('[data-demo-reset]');
    const steps = [...document.querySelectorAll('.flow-step')];
    const icons = ['ph-calendar-check', 'ph-envelope-simple', 'ph-bell-simple', 'ph-address-book', 'ph-paper-plane-tilt'];
    let timers = [];
    demo.querySelectorAll('.demo-opts').forEach((g) => g.addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (b && !book.disabled) press(g, b);
    }));
    const clear = () => {
      timers.forEach(clearTimeout); timers = [];
      log.innerHTML = '';
      steps.forEach((s) => s.classList.remove('is-active', 'is-done'));
    };
    book.addEventListener('click', () => {
      clear();
      // Nothing is preselected; an unanswered choice falls back to its first option.
      const [svc, time] = [...demo.querySelectorAll('.demo-opts')].map((g) => {
        const picked = g.querySelector('[aria-pressed="true"]') || g.querySelector('button');
        press(g, picked);
        return picked.textContent;
      });
      empty.hidden = true;
      book.disabled = true;
      demo.classList.add('is-running');
      L.log(svc, time).forEach((text, i) => {
        timers.push(setTimeout(() => {
          const li = document.createElement('li');
          li.innerHTML = `<i class="ph-light ${icons[i]}" aria-hidden="true"></i><span></span>`;
          li.querySelector('span').textContent = text;
          log.appendChild(li);
          steps.forEach((s, j) => { s.classList.toggle('is-active', j === i); s.classList.toggle('is-done', j < i); });
          if (i === 4) {
            timers.push(setTimeout(() => {
              steps.forEach((s) => { s.classList.remove('is-active'); s.classList.add('is-done'); });
              book.hidden = true; reset.hidden = false; demo.classList.remove('is-running');
            }, 700));
          }
        }, reduce ? 0 : i * 750 + 200));
      });
    });
    reset.addEventListener('click', () => {
      clear();
      empty.hidden = false; book.hidden = false; book.disabled = false; reset.hidden = true;
      book.focus();
    });
  }

  // ---------- 7. Report months ----------
  const tabs = document.querySelector('.report-tabs');
  if (tabs) {
    const data = {
      jul: { visits: 1040, inq: 27, book: 38, dv: 19, di: 3, db: 6 },
      aug: { visits: 1146, inq: 31, book: 43, dv: 10, di: 4, db: 5 },
      sep: { visits: 1284, inq: 37, book: 52, dv: 12, di: 6, db: 9 },
    };
    const bars = [...document.querySelectorAll('.bars li')];
    const barMonth = { jul: 3, aug: 4, sep: 5 };
    tabs.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-month]');
      if (!btn) return;
      press(tabs, btn);
      const m = btn.dataset.month, d = data[m];
      document.querySelector('[data-report-month]').textContent = L.months[m];
      ['visits', 'inq', 'book'].forEach((k) => tween(document.querySelector(`[data-kpi="${k}"]`), d[k], 500));
      document.querySelector('[data-kpi-delta="visits"]').textContent = L.pct(d.dv);
      document.querySelector('[data-kpi-delta="inq"]').textContent = L.count(d.di);
      document.querySelector('[data-kpi-delta="book"]').textContent = L.count(d.db);
      bars.forEach((b, i) => b.classList.toggle('is-current', i === barMonth[m]));
      const note = document.querySelector('.report-note');
      if (note) note.hidden = m !== 'sep';
    });
  }

  // ---------- 8. Live destinations ----------
  const dest = document.querySelector('[data-dest]');
  if (dest) {
    const svg = dest.querySelector('.dest-svg');
    const node = dest.querySelector('.dest-node');
    const targets = [...dest.querySelectorAll('.dest-target')];
    const count = document.querySelector('[data-dest-count]');
    const NS = 'http://www.w3.org/2000/svg';
    const draw = () => {
      const box = dest.getBoundingClientRect();
      svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
      svg.innerHTML = '';
      const n = node.getBoundingClientRect();
      const stacked = window.matchMedia('(max-width: 760px)').matches;
      const sx = stacked ? n.left + n.width / 2 - box.left : n.right - box.left;
      const sy = stacked ? n.bottom - box.top : n.top + n.height / 2 - box.top;
      targets.forEach((t) => {
        const r = t.getBoundingClientRect();
        const tx = stacked ? r.left + 24 - box.left : r.left - box.left;
        const ty = stacked ? r.top - box.top + r.height / 2 : r.top + r.height / 2 - box.top;
        const path = document.createElementNS(NS, 'path');
        const d = stacked
          ? `M${sx},${sy} C${sx},${ty} ${tx - 40},${ty} ${tx},${ty}`
          : `M${sx},${sy} C${sx + (tx - sx) * 0.5},${sy} ${sx + (tx - sx) * 0.5},${ty} ${tx},${ty}`;
        path.setAttribute('d', d);
        path.setAttribute('class', t.getAttribute('aria-pressed') === 'true' ? 'dest-path is-on' : 'dest-path');
        svg.appendChild(path);
      });
    };
    const update = () => {
      const n = targets.filter((t) => t.getAttribute('aria-pressed') === 'true').length;
      tween(count, n, 300);
      plural(count.parentElement, n);
      draw();
    };
    targets.forEach((t) => t.addEventListener('click', () => {
      const on = t.getAttribute('aria-pressed') === 'true';
      const active = targets.filter((x) => x.getAttribute('aria-pressed') === 'true').length;
      if (on && active === 1) return; // keep at least one destination
      t.setAttribute('aria-pressed', String(!on));
      update();
    }));
    new ResizeObserver(draw).observe(dest);
    update();
  }
})();
