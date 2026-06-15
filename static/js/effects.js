// Modern Interactive Effects Library
// Includes hover effects, scroll animations, smooth scrolling, and more

class InteractiveEffects {
  constructor() {
    this.init();
  }

  init() {
    this.setupSmoothScroll();
    this.setupScrollAnimations();
    this.setupButtonEffects();
    this.setupCardHoverEffects();
    this.setupParallaxEffect();
    this.setupScrollProgress();
    this.setupCursorEffect();
  }

  // 1. Smooth Scrolling
  setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });

    // Smooth scroll on page load
    if (window.location.hash) {
      setTimeout(() => {
        const element = document.querySelector(window.location.hash);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    }
  }

  // 2. Scroll-triggered Animations (Intersection Observer)
  setupScrollAnimations() {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // If reduced motion, immediately reveal everything and bail
    if (reducedMotion) {
      document.querySelectorAll('[data-scroll-animate]').forEach(el => {
        el.classList.add('is-visible', 'animate-in');
      });
      return;
    }

    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -60px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible', 'animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe all elements with scroll-animation class
    document.querySelectorAll('[data-scroll-animate]').forEach(el => {
      observer.observe(el);
    });
  }

  // 3. Button Ripple Effect & Hover Effects
  setupButtonEffects() {
    document.querySelectorAll('button, a[class*="btn"], a[class*="cta"]').forEach(btn => {
      // Ripple effect on click
      btn.addEventListener('click', (e) => {
        const ripple = document.createElement('span');
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');

        // Remove existing ripple
        btn.querySelectorAll('.ripple').forEach(r => r.remove());
        btn.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
      });

      // Add lift effect on hover
      if (!btn.classList.contains('no-lift-effect')) {
        btn.addEventListener('mouseenter', () => {
          btn.style.transform = 'translateY(-2px)';
        });
        btn.addEventListener('mouseleave', () => {
          btn.style.transform = 'translateY(0)';
        });
      }
    });
  }

  // 4. Card Hover Effects
  setupCardHoverEffects() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const cards = document.querySelectorAll('[data-card], .card, article');
    
    cards.forEach(card => {
      // Skip cards that already use the CSS hover-lift class
      if (card.classList.contains('hover-lift')) return;

      card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-4px)';
        this.style.boxShadow = '0 16px 36px rgba(0,0,0,0.12)';
      });

      card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '';
      });

      card.style.transition = 'transform 0.22s ease-out, box-shadow 0.22s ease-out';
    });
  }

  // 5. Parallax Effect on Scroll
  setupParallaxEffect() {
    const parallaxElements = document.querySelectorAll('[data-parallax]');
    
    if (parallaxElements.length === 0) return;

    window.addEventListener('scroll', () => {
      parallaxElements.forEach(element => {
        const scrollPosition = window.pageYOffset;
        const speed = element.getAttribute('data-parallax') || 0.5;
        element.style.transform = `translateY(${scrollPosition * speed}px)`;
      });
    }, { passive: true });
  }

  // 6. Scroll Progress Bar
  setupScrollProgress() {
    let progressBar = document.getElementById('scroll-progress');
    
    if (!progressBar) {
      progressBar = document.createElement('div');
      progressBar.id = 'scroll-progress';
      progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(to right, #0ea5e9, #10b981);
        z-index: 9999;
        transition: width 0.1s ease;
      `;
      document.body.appendChild(progressBar);
    }

    window.addEventListener('scroll', () => {
      const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = (window.pageYOffset / windowHeight) * 100;
      progressBar.style.width = scrolled + '%';
    }, { passive: true });
  }

  // 7. Cursor Glow Effect
  setupCursorEffect() {
    const cursor = document.createElement('div');
    cursor.id = 'glow-cursor';
    cursor.style.cssText = `
      position: fixed;
      width: 20px;
      height: 20px;
      border: 2px solid rgba(14, 165, 233, 0.5);
      border-radius: 50%;
      pointer-events: none;
      z-index: 9998;
      mix-blend-mode: screen;
      opacity: 0;
      transition: opacity 0.3s ease;
    `;
    document.body.appendChild(cursor);

    let mouseX = 0;
    let mouseY = 0;
    let cursorX = 0;
    let cursorY = 0;

    document.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      cursor.style.opacity = '1';
    });

    document.addEventListener('mouseleave', () => {
      cursor.style.opacity = '0';
    });

    const animate = () => {
      cursorX += (mouseX - cursorX) * 0.3;
      cursorY += (mouseY - cursorY) * 0.3;

      cursor.style.left = (cursorX - 10) + 'px';
      cursor.style.top = (cursorY - 10) + 'px';

      requestAnimationFrame(animate);
    };

    animate();
  }

  // Utility: Add animation class to element
  static animateElement(element, animationName) {
    element.style.animation = `${animationName} 0.6s ease-out forwards`;
  }

  // Utility: Create staggered animations
  static staggerElements(elements, delayMs = 100) {
    elements.forEach((el, index) => {
      el.style.animationDelay = `${index * delayMs}ms`;
      el.classList.add('animate-in');
    });
  }
}

// 8. Typewriter Effect
function setupTypewriter() {
  const el = document.getElementById('typewriter-text');
  if (!el) return;

  const phrases = [
    'Geospatial Innovation',
    'Smart Urban Planning',
    'Data-Driven Decisions',
    'Resilient Communities',
    'Spatial Intelligence',
  ];

  let phraseIndex = 0;
  let charIndex = 0;
  let isDeleting = false;

  function type() {
    const current = phrases[phraseIndex];
    if (isDeleting) {
      el.textContent = current.substring(0, charIndex - 1);
      charIndex--;
    } else {
      el.textContent = current.substring(0, charIndex + 1);
      charIndex++;
    }

    let delay = isDeleting ? 50 : 100;

    if (!isDeleting && charIndex === current.length) {
      delay = 2000;
      isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
      isDeleting = false;
      phraseIndex = (phraseIndex + 1) % phrases.length;
      delay = 400;
    }

    setTimeout(type, delay);
  }

  setTimeout(type, 800);
}

// 9. Animated Counters — easeOutExpo + comma formatting
function setupCounters() {
  const counters = document.querySelectorAll('.counter');
  if (counters.length === 0) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function easeOutExpo(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  function formatNumber(n, target) {
    if (target >= 10000) return n.toLocaleString();
    if (target >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
    return Math.floor(n).toString();
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseInt(el.getAttribute('data-target'), 10);
      const suffix = el.getAttribute('data-suffix') || '';

      if (reducedMotion) {
        el.textContent = formatNumber(target, target) + suffix;
        observer.unobserve(el);
        return;
      }

      const duration = 2000;
      const startTime = performance.now();

      function tick(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = easeOutExpo(progress);
        const current = eased * target;
        el.textContent = formatNumber(current, target) + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      }

      requestAnimationFrame(tick);
      observer.unobserve(el);
    });
  }, { threshold: 0.3 });

  counters.forEach(c => observer.observe(c));
}

// 10. Heading underline draw on scroll
function setupHeadingUnderlines() {
  const headings = document.querySelectorAll('.heading-underline');
  if (!headings.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.6 });

  headings.forEach(h => observer.observe(h));
}

// 11. Card shimmer on scroll reveal
function setupCardShimmer() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('card-shimmer');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('[data-card]').forEach(c => observer.observe(c));
}

// 12. Page progress bar on navigation
function setupPageProgressBar() {
  const bar = document.createElement('div');
  bar.id = 'page-progress-bar';
  document.body.prepend(bar);

  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto') || href.startsWith('http') || link.target === '_blank') return;

    link.addEventListener('click', (e) => {
      bar.style.width = '0%';
      bar.style.opacity = '1';
      // Animate to 80% quickly, rest completes on load
      requestAnimationFrame(() => {
        bar.style.transition = 'width 0.4s ease-out';
        bar.style.width = '80%';
      });
    });
  });

  window.addEventListener('load', () => {
    bar.style.width = '100%';
    setTimeout(() => { bar.style.opacity = '0'; }, 300);
    setTimeout(() => { bar.style.width = '0%'; bar.style.transition = 'none'; }, 700);
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new InteractiveEffects();
    setupTypewriter();
    setupCounters();
    setupHeadingUnderlines();
    setupCardShimmer();
    setupPageProgressBar();
  });
} else {
  new InteractiveEffects();
  setupTypewriter();
  setupCounters();
  setupHeadingUnderlines();
  setupCardShimmer();
  setupPageProgressBar();
}

// Utility for fade-in on load
window.addEventListener('load', () => {
  document.body.style.opacity = '1';
});
