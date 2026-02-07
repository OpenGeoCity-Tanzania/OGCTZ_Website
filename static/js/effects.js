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
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe all elements with scroll-animation class
    document.querySelectorAll('[data-scroll-animate]').forEach(el => {
      observer.observe(el);
    });

    // Also animate common elements
    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(el => {
      if (!el.closest('[data-no-animate]')) {
        observer.observe(el);
      }
    });

    document.querySelectorAll('p, ul, ol').forEach(el => {
      if (!el.closest('[data-no-animate]')) {
        observer.observe(el);
      }
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
    const cards = document.querySelectorAll('[data-card], .card, article');
    
    cards.forEach(card => {
      card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px) scale(1.01)';
        this.style.boxShadow = '0 20px 40px rgba(0,0,0,0.15)';
      });

      card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
        this.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
      });

      card.style.transition = 'all 0.3s cubic-bezier(0.23, 1, 0.320, 1)';
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

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new InteractiveEffects();
  });
} else {
  new InteractiveEffects();
}

// Utility for fade-in on load
window.addEventListener('load', () => {
  document.body.style.opacity = '1';
});
