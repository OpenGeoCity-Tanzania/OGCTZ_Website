// Animated Science & Innovation Background
// Creates floating particles, nodes, and connecting lines

class AnimatedBackground {
  constructor() {
    this.canvas = document.getElementById('animated-bg-canvas');
    if (!this.canvas) return;
    
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.nodes = [];
    this.connectionDistance = 150;
    this.particleCount = 30;
    
    // Set canvas size
    this.resize();
    window.addEventListener('resize', () => this.resize());
    
    // Create particles and nodes
    this.createParticles();
    this.animate();
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  createParticles() {
    // Create main nodes (larger)
    for (let i = 0; i < 8; i++) {
      this.nodes.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 3 + 2,
        opacity: 0.6,
        type: 'node'
      });
    }

    // Create floating particles
    for (let i = 0; i < this.particleCount; i++) {
      this.particles.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 1.5 + 0.5,
        opacity: Math.random() * 0.5 + 0.3,
        type: 'particle',
        pulse: Math.random() * Math.PI * 2
      });
    }
  }

  update() {
    // Update nodes
    this.nodes.forEach(node => {
      node.x += node.vx;
      node.y += node.vy;

      // Bounce off walls
      if (node.x < 0 || node.x > this.canvas.width) node.vx *= -1;
      if (node.y < 0 || node.y > this.canvas.height) node.vy *= -1;

      // Keep in bounds
      node.x = Math.max(0, Math.min(this.canvas.width, node.x));
      node.y = Math.max(0, Math.min(this.canvas.height, node.y));
    });

    // Update particles
    this.particles.forEach(particle => {
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.pulse += 0.02;

      // Bounce off walls
      if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
      if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;

      // Keep in bounds
      particle.x = Math.max(0, Math.min(this.canvas.width, particle.x));
      particle.y = Math.max(0, Math.min(this.canvas.height, particle.y));
    });
  }

  draw() {
    // Clear canvas with slight trail effect (for motion blur)
    this.ctx.fillStyle = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'rgba(15, 23, 42, 0.02)' // Dark mode
      : 'rgba(255, 255, 255, 0.01)'; // Light mode
    
    // Check actual dark mode from document
    if (document.documentElement.classList.contains('dark')) {
      this.ctx.fillStyle = 'rgba(15, 23, 42, 0.02)';
    } else {
      this.ctx.fillStyle = 'rgba(255, 255, 255, 0.01)';
    }
    
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw connections between nodes
    this.drawConnections();

    // Draw nodes
    this.nodes.forEach(node => {
      this.drawNode(node);
    });

    // Draw particles
    this.particles.forEach(particle => {
      this.drawParticle(particle);
    });
  }

  drawConnections() {
    // Draw lines between close nodes
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const dx = this.nodes[i].x - this.nodes[j].x;
        const dy = this.nodes[i].y - this.nodes[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < this.connectionDistance) {
          const opacity = (1 - distance / this.connectionDistance) * 0.3;
          
          // Gradient line
          const gradient = this.ctx.createLinearGradient(
            this.nodes[i].x, this.nodes[i].y,
            this.nodes[j].x, this.nodes[j].y
          );
          
          if (document.documentElement.classList.contains('dark')) {
            gradient.addColorStop(0, `rgba(14, 165, 233, ${opacity})`);
            gradient.addColorStop(1, `rgba(16, 185, 129, ${opacity})`);
          } else {
            gradient.addColorStop(0, `rgba(14, 165, 233, ${opacity * 0.8})`);
            gradient.addColorStop(1, `rgba(16, 185, 129, ${opacity * 0.8})`);
          }
          
          this.ctx.strokeStyle = gradient;
          this.ctx.lineWidth = 1;
          this.ctx.beginPath();
          this.ctx.moveTo(this.nodes[i].x, this.nodes[i].y);
          this.ctx.lineTo(this.nodes[j].x, this.nodes[j].y);
          this.ctx.stroke();
        }
      }
    }
  }

  drawNode(node) {
    // Draw glowing core
    const gradient = this.ctx.createRadialGradient(
      node.x, node.y, 0,
      node.x, node.y, node.radius * 2
    );
    
    if (document.documentElement.classList.contains('dark')) {
      gradient.addColorStop(0, `rgba(14, 165, 233, ${node.opacity})`);
      gradient.addColorStop(1, `rgba(14, 165, 233, 0)`);
    } else {
      gradient.addColorStop(0, `rgba(14, 165, 233, ${node.opacity * 0.6})`);
      gradient.addColorStop(1, `rgba(14, 165, 233, 0)`);
    }
    
    this.ctx.fillStyle = gradient;
    this.ctx.beginPath();
    this.ctx.arc(node.x, node.y, node.radius * 2, 0, Math.PI * 2);
    this.ctx.fill();

    // Draw node center
    this.ctx.fillStyle = document.documentElement.classList.contains('dark')
      ? `rgba(14, 165, 233, ${node.opacity})`
      : `rgba(14, 165, 233, ${node.opacity * 0.7})`;
    this.ctx.beginPath();
    this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    this.ctx.fill();
  }

  drawParticle(particle) {
    // Pulsing particle
    const pulse = Math.sin(particle.pulse) * 0.5 + 1;
    const radius = particle.radius * pulse;
    
    // Outer glow
    const glowGradient = this.ctx.createRadialGradient(
      particle.x, particle.y, 0,
      particle.x, particle.y, radius * 1.5
    );
    
    if (document.documentElement.classList.contains('dark')) {
      glowGradient.addColorStop(0, `rgba(16, 185, 129, ${particle.opacity * 0.5})`);
      glowGradient.addColorStop(1, `rgba(16, 185, 129, 0)`);
    } else {
      glowGradient.addColorStop(0, `rgba(16, 185, 129, ${particle.opacity * 0.3})`);
      glowGradient.addColorStop(1, `rgba(16, 185, 129, 0)`);
    }
    
    this.ctx.fillStyle = glowGradient;
    this.ctx.beginPath();
    this.ctx.arc(particle.x, particle.y, radius * 1.5, 0, Math.PI * 2);
    this.ctx.fill();

    // Particle core
    this.ctx.fillStyle = document.documentElement.classList.contains('dark')
      ? `rgba(16, 185, 129, ${particle.opacity})`
      : `rgba(16, 185, 129, ${particle.opacity * 0.7})`;
    this.ctx.beginPath();
    this.ctx.arc(particle.x, particle.y, radius, 0, Math.PI * 2);
    this.ctx.fill();
  }

  animate() {
    this.update();
    this.draw();
    requestAnimationFrame(() => this.animate());
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new AnimatedBackground();
  });
} else {
  new AnimatedBackground();
}
