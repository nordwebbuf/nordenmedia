// Norrsund Hem: cart counter, shoppable room, booking and newsletter forms, scroll reveal.
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // ---------- Sticky nav gets a hairline once the page scrolls ----------
  const nav = $('[data-nav]');
  const sentinel = document.createElement('div');
  sentinel.setAttribute('aria-hidden', 'true');
  sentinel.style.cssText = 'position:absolute;top:0;height:1px;width:1px';
  document.body.prepend(sentinel);
  new IntersectionObserver(([e]) => nav.classList.toggle('is-stuck', !e.isIntersecting)).observe(sentinel);

  // ---------- Mobile menu ----------
  const menuBtn = $('[data-menu-btn]');
  const mobileNav = $('[data-mobile-nav]');
  const setMenu = (open) => {
    mobileNav.hidden = !open;
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? 'Stäng menyn' : 'Öppna menyn');
    menuBtn.querySelector('i').className = `ph-light ${open ? 'ph-x' : 'ph-list'}`;
  };
  menuBtn.addEventListener('click', () => setMenu(mobileNav.hidden));
  $$('a', mobileNav).forEach((a) => a.addEventListener('click', () => setMenu(false)));

  // ---------- Cart (demo: counts items and confirms with a toast) ----------
  let count = 0;
  const countEl = $('[data-cart-count]');
  const cartBtn = $('[data-cart-btn]');
  const toast = $('[data-toast]');
  let toastTimer;
  const showToast = (html) => {
    toast.innerHTML = html;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 2600);
  };
  const addToCart = (name, btn) => {
    count += 1;
    countEl.textContent = count;
    countEl.hidden = false;
    countEl.classList.remove('is-bump'); void countEl.offsetWidth; countEl.classList.add('is-bump');
    cartBtn.setAttribute('aria-label', `Varukorg, ${count} ${count === 1 ? 'vara' : 'varor'}`);
    showToast(`<i class="ph-light ph-check-circle" aria-hidden="true"></i><span>${name} ligger i varukorgen</span>`);
    if (btn) {
      const label = btn.textContent;
      btn.classList.add('is-added');
      btn.textContent = 'Tillagd';
      setTimeout(() => { btn.classList.remove('is-added'); btn.textContent = label; }, 1800);
    }
  };
  $$('[data-add]').forEach((b) => b.addEventListener('click', () => addToCart(b.dataset.add, b)));

  // ---------- Shoppable room ----------
  const ITEMS = [
    { name: 'Soffa Brasa, tresits', price: '14 995 kr' },
    { name: 'Soffbord Stubbe, ek', price: '3 495 kr' },
    { name: 'Kuddfodral Linne, 2-pack', price: '449 kr' },
  ];
  const room = $('[data-room]');
  const card = $('[data-spot-card]');
  const spots = $$('[data-spot]', room);
  let active = null;
  const closeCard = () => { card.hidden = true; spots.forEach((s) => s.setAttribute('aria-expanded', 'false')); active = null; };
  spots.forEach((spot) => spot.addEventListener('click', (e) => {
    e.stopPropagation();
    const i = +spot.dataset.spot;
    if (active === i) { closeCard(); return; }
    active = i;
    spots.forEach((s) => s.setAttribute('aria-expanded', String(s === spot)));
    $('[data-spot-name]', card).textContent = ITEMS[i].name;
    $('[data-spot-price]', card).textContent = ITEMS[i].price;
    card.hidden = false;
    // place the card next to the spot, inside the image
    const r = room.getBoundingClientRect();
    const sx = spot.offsetLeft, sy = spot.offsetTop;
    const w = card.offsetWidth, h = card.offsetHeight;
    const left = sx + 28 + w > r.width ? sx - 28 - w : sx + 28;
    const top = Math.min(Math.max(12, sy - h / 2), r.height - h - 12);
    card.style.left = `${left}px`;
    card.style.top = `${top}px`;
  }));
  $('[data-spot-add]', card).addEventListener('click', (e) => { e.stopPropagation(); addToCart(ITEMS[active].name); closeCard(); });
  card.addEventListener('click', (e) => e.stopPropagation());
  document.addEventListener('click', closeCard);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !card.hidden) closeCard(); });

  // ---------- Booking form (demo: validates, then shows the confirmation) ----------
  const booking = $('[data-booking]');
  const done = $('[data-booking-done]');
  booking.addEventListener('submit', (e) => {
    e.preventDefault();
    let ok = true;
    $$('input[required]', booking).forEach((input) => {
      const valid = input.type === 'email' ? /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim()) : input.value.trim().length > 1;
      input.setAttribute('aria-invalid', String(!valid));
      input.closest('.field').querySelector('.err').hidden = valid;
      if (!valid && ok) { input.focus(); ok = false; }
    });
    if (!ok) return;
    booking.hidden = true;
    done.hidden = false;
    done.focus();
  });
  $$('input', booking).forEach((i) => i.addEventListener('input', () => {
    if (i.getAttribute('aria-invalid') === 'true') { i.setAttribute('aria-invalid', 'false'); i.closest('.field').querySelector('.err').hidden = true; }
  }));

  // ---------- Newsletter (demo) ----------
  const news = $('[data-news]');
  const msg = $('[data-news-msg]');
  news.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = $('input', news);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim())) { msg.textContent = 'Skriv en giltig e-postadress.'; input.focus(); return; }
    msg.textContent = 'Tack! Rabattkoden är på väg till din inkorg. (Demo, inget skickas.)';
    input.value = '';
  });

  // ---------- Scroll reveal ----------
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
  $$('.reveal').forEach((el) => io.observe(el));
})();
