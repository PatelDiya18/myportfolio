// Diya Patel Portfolio - 60 FPS Canvas (Right-Aligned Portrait) & Scroll Engine
const TOTAL_FRAMES = 180;
const canvas = document.getElementById('cinematic-canvas');
const ctx = canvas.getContext('2d');

const frameCounter = document.getElementById('frame-counter');
const progressBar = document.getElementById('scrub-progress');
const progressText = document.getElementById('scrub-percentage');

const toggleAutoplayBtn = document.getElementById('toggle-autoplay');

// Preloaded frame sequence
const frames = [];
let loadedFramesCount = 0;

// Scroll & Lerp Physics
let targetFrame = 0;
let currentFrame = 0;
const lerpFactor = 0.12;

let isAutoplay = false;
let autoplayFrame = 0;

// Preload User Frame Sequence
function initFrames() {
  for (let i = 0; i < TOTAL_FRAMES; i++) {
    const img = new Image();
    const formattedIndex = String(i).padStart(3, '0');
    img.src = `user_frames_webp/frame_${formattedIndex}.webp`;
    
    img.onload = () => {
      loadedFramesCount++;
      if (loadedFramesCount === 1 && currentFrame === 0) {
        renderFrame(0);
      }
    };
    
    frames.push(img);
  }
}

// Canvas Scaling & Right Alignment for Full Portrait Visibility
function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = window.innerWidth * dpr;
  canvas.height = window.innerHeight * dpr;
  
  const frameIdx = Math.round(currentFrame);
  if (frames[frameIdx] && frames[frameIdx].complete) {
    renderFrame(frameIdx);
  }
}

window.addEventListener('resize', resizeCanvas);

// Render Specific Frame Right-Aligned
function renderFrame(index) {
  const img = frames[index];
  if (!img || !img.complete) return;

  const cWidth = canvas.width;
  const cHeight = canvas.height;

  ctx.clearRect(0, 0, cWidth, cHeight);

  const imgRatio = img.width / img.height;
  const canvasRatio = cWidth / cHeight;

  let drawW, drawH, drawX, drawY;

  if (canvasRatio > imgRatio) {
    drawW = cWidth;
    drawH = cWidth / imgRatio;
    drawX = 0;
    drawY = (cHeight - drawH) / 2;
  } else {
    drawH = cHeight;
    drawW = cHeight * imgRatio;
    // Right-align image so her whole portrait is fully visible on the right side
    drawX = cWidth - drawW;
    drawY = 0;
  }

  ctx.drawImage(img, drawX, drawY, drawW, drawH);
}

// Calculate Scroll Progress
function updateScrollProgress() {
  if (isAutoplay) return;

  const scrollTop = window.scrollY || document.documentElement.scrollTop;
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  
  const scrollFraction = Math.max(0, Math.min(1, scrollTop / maxScroll));
  targetFrame = scrollFraction * (TOTAL_FRAMES - 1);

  // Update UI indicators
  const percent = Math.round(scrollFraction * 100);
  if (progressBar) progressBar.style.width = `${percent}%`;
  if (progressText) progressText.innerText = `${percent}%`;
}

window.addEventListener('scroll', updateScrollProgress);

// Animation Loop (60 FPS Lerp Inertia)
function animate() {
  if (isAutoplay) {
    autoplayFrame = (autoplayFrame + 0.5) % TOTAL_FRAMES;
    currentFrame = autoplayFrame;
  } else {
    currentFrame += (targetFrame - currentFrame) * lerpFactor;
  }

  const frameIdx = Math.max(0, Math.min(TOTAL_FRAMES - 1, Math.round(currentFrame)));
  renderFrame(frameIdx);

  if (frameCounter) {
    const formattedIndex = String(frameIdx + 1).padStart(3, '0');
    frameCounter.innerText = `FRAME ${formattedIndex} / ${TOTAL_FRAMES}`;
  }

  requestAnimationFrame(animate);
}

// Intersection Observer for Section Entrance Animations
const observerOptions = {
  threshold: 0.15,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, observerOptions);

document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));

// Auto-Play Control
if (toggleAutoplayBtn) {
  toggleAutoplayBtn.addEventListener('click', () => {
    isAutoplay = !isAutoplay;
    if (isAutoplay) {
      autoplayFrame = currentFrame;
      toggleAutoplayBtn.innerHTML = `<i data-lucide="pause"></i> Pause`;
      toggleAutoplayBtn.style.borderColor = `var(--primary-red)`;
      toggleAutoplayBtn.style.color = `#fff`;
    } else {
      toggleAutoplayBtn.innerHTML = `<i data-lucide="play"></i> Auto-Play`;
      toggleAutoplayBtn.style.borderColor = `var(--border-glass)`;
      toggleAutoplayBtn.style.color = `var(--text-muted)`;
      updateScrollProgress();
    }
    if (window.lucide) lucide.createIcons();
  });
}

// Initialize Application
resizeCanvas();
initFrames();
requestAnimationFrame(animate);
