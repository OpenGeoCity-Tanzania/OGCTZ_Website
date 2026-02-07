// Water Bubble Background — interactive with cursor/touch
class WaterBubblesBackground {
  constructor() {
    this.canvas = document.getElementById('animated-bg-canvas');
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.bubbles = [];
    this.mouse = { x: -9999, y: -9999, down: false };
    this.options = {
      density: 0.00012, // bubbles per px^2
      minRadius: 6,
      maxRadius: 36,
      maxSpeed: 0.6,
      repulsion: 160,
      repulsionStrength: 0.18,
      drift: 0.02
    };

    this._resize();
    window.addEventListener('resize', () => this._resize());

    // Pointer interactions
    window.addEventListener('mousemove', e => { this.mouse.x = e.clientX; this.mouse.y = e.clientY; });
    window.addEventListener('pointerdown', () => this.mouse.down = true);
    window.addEventListener('pointerup', () => this.mouse.down = false);
    window.addEventListener('touchmove', e => {
      const t = e.touches[0]; if (t) { this.mouse.x = t.clientX; this.mouse.y = t.clientY; }
    }, { passive: true });
    window.addEventListener('touchend', () => { this.mouse.x = -9999; this.mouse.y = -9999; });

    this._populate();
    this._anim();
  }

  _resize() {
    const dpr = window.devicePixelRatio || 1;
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.canvas.style.width = this.width + 'px';
    this.canvas.style.height = this.height + 'px';
    this.canvas.width = Math.floor(this.width * dpr);
    this.canvas.height = Math.floor(this.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  _populate() {
    const area = this.width * this.height;
    const target = Math.max(12, Math.floor(area * this.options.density));
    this.bubbles.length = 0;
    for (let i = 0; i < target; i++) {
      this.bubbles.push(this._createBubble(true));
    }
  }

  _createBubble(randomPos = false) {
    const r = this.options.minRadius + Math.random() * (this.options.maxRadius - this.options.minRadius);
    return {
      x: randomPos ? Math.random() * this.width : this.width / 2,
      y: randomPos ? Math.random() * this.height : this.height / 2,
      vx: (Math.random() - 0.5) * this.options.maxSpeed,
      vy: (Math.random() - 0.5) * this.options.maxSpeed,
      r: r,
      baseR: r,
      phase: Math.random() * Math.PI * 2,
      hue: 200 + Math.random() * 60,
      alpha: 0.5 + Math.random() * 0.4
    };
  }

  _update(dt) {
    const repulsionSq = this.options.repulsion * this.options.repulsion;
    for (let b of this.bubbles) {
      // gentle buoyancy / drift
      b.vy -= (this.options.drift * (0.5 - Math.random())) * (dt * 0.06);

      // repulse from cursor
      const dx = b.x - this.mouse.x;
      const dy = b.y - this.mouse.y;
      const distSq = dx * dx + dy * dy;
      if (distSq < repulsionSq) {
        const dist = Math.sqrt(distSq) || 0.001;
        const force = (1 - dist / this.options.repulsion) * this.options.repulsionStrength;
        b.vx += (dx / dist) * force * (this.mouse.down ? 1.6 : 1);
        b.vy += (dy / dist) * force * (this.mouse.down ? 1.6 : 1);
      }

      // small pulsation to radius
      b.phase += 0.02 * (1 + Math.sin(b.phase * 0.5) * 0.5);
      b.r = b.baseR * (0.9 + 0.12 * Math.sin(b.phase));

      // integrate
      b.x += b.vx * dt;
      b.y += b.vy * dt;

      // soft bounds
      if (b.x < -b.r) b.x = this.width + b.r;
      if (b.x > this.width + b.r) b.x = -b.r;
      if (b.y < -b.r) b.y = this.height + b.r;
      if (b.y > this.height + b.r) b.y = -b.r;

      // gentle damping
      b.vx *= 0.995;
      b.vy *= 0.995;
    }
  }

  _draw() {
    const dark = document.documentElement.classList.contains('dark');
    // subtle backdrop to create a soft trail
    this.ctx.fillStyle = dark ? 'rgba(4,6,11,0.12)' : 'rgba(255,255,255,0.12)';
    this.ctx.fillRect(0, 0, this.width, this.height);

    for (let b of this.bubbles) {
      // bubble glow
      const grad = this.ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r * 2.8);
      const hue = Math.floor(b.hue);
      if (dark) {
        grad.addColorStop(0, `rgba(${100},${200},${220},${b.alpha})`);
        grad.addColorStop(0.6, `rgba(${100},${200},${220},${b.alpha * 0.08})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
      } else {
        grad.addColorStop(0, `rgba(${120},${170},${240},${b.alpha})`);
        grad.addColorStop(0.6, `rgba(${120},${170},${240},${b.alpha * 0.08})`);
        grad.addColorStop(1, 'rgba(255,255,255,0)');
      }
      this.ctx.fillStyle = grad;
      this.ctx.beginPath();
      this.ctx.arc(b.x, b.y, b.r * 2.6, 0, Math.PI * 2);
      this.ctx.fill();

      // bubble rim
      this.ctx.beginPath();
      this.ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
      this.ctx.fillStyle = dark ? `rgba(220,240,250,${0.08 + b.alpha * 0.15})` : `rgba(255,255,255,${0.16 + b.alpha * 0.15})`;
      this.ctx.fill();

      // small specular
      this.ctx.beginPath();
      this.ctx.arc(b.x - b.r * 0.45, b.y - b.r * 0.45, Math.max(1, b.r * 0.25), 0, Math.PI * 2);
      this.ctx.fillStyle = dark ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.9)';
      this.ctx.fill();
    }
  }

  _anim() {
    let last = performance.now();
    const loop = (t) => {
      const dt = Math.min(48, t - last) / 16.6667; // approx frames
      last = t;
      this._update(dt);
      this._draw();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new WaterBubblesBackground());
} else {
  new WaterBubblesBackground();
}
