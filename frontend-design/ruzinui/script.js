(() => {
  const nav = document.getElementById('nav');
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });

  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
  });

  navLinks.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => navLinks.classList.remove('open'));
  });

  const revealEls = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );
  revealEls.forEach((el) => observer.observe(el));

  document.querySelectorAll('.hero .reveal').forEach((el) => {
    requestAnimationFrame(() => el.classList.add('visible'));
  });

  const form = document.getElementById('contactForm');
  const formNote = document.getElementById('formNote');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    formNote.textContent = '感谢您的咨询！我们的团队将在 24 小时内与您联系。';
    form.reset();
    setTimeout(() => { formNote.textContent = ''; }, 5000);
  });

  document.querySelectorAll('.glass-panel').forEach((panel) => {
    panel.addEventListener('mousemove', (e) => {
      const rect = panel.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width - 0.5) * 8;
      const y = ((e.clientY - rect.top) / rect.height - 0.5) * 8;
      panel.style.transform = `translate(${x}px, ${y}px)`;
    });
    panel.addEventListener('mouseleave', () => {
      panel.style.transform = '';
    });
  });
})();
