import os
import math
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import cv2

# Configuration
INPUT_IMAGE_PATH = r"c:\Users\mmpat\Downloads\portfolio\ChatGPT Image Aug 14, 2026, 07_46_09 PM.png"
OUTPUT_VIDEO_PATH = r"c:\Users\mmpat\Downloads\portfolio\agent_cinematic.mp4"
FRAMES_DIR = r"c:\Users\mmpat\Downloads\portfolio\frames"
NUM_FRAMES = 180  # 3 seconds at 60 FPS
FPS = 60
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_in_out_quint(t):
    return 16 * math.pow(t, 5) if t < 0.5 else 1 - math.pow(-2 * t + 2, 5) / 2

def create_particle_system(num_particles, width, height):
    particles = []
    np.random.seed(42)
    for _ in range(num_particles):
        particles.append({
            'x': np.random.uniform(0, width),
            'y': np.random.uniform(0, height),
            'size': np.random.uniform(2.5, 12),
            'speed_y': np.random.uniform(-1.2, -0.4),
            'speed_x': np.random.uniform(-0.5, 0.5),
            'alpha': np.random.uniform(0.2, 0.8),
            'depth': np.random.uniform(0.4, 1.4), # Parallax scale
            'hue_shift': np.random.uniform(0, 35)
        })
    return particles

def main():
    print("Starting updated cinematic video rendering (with top headroom & sharpened motion)...")
    os.makedirs(FRAMES_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_IMAGE_PATH):
        raise FileNotFoundError(f"Input image not found at {INPUT_IMAGE_PATH}")
    
    raw_img = Image.open(INPUT_IMAGE_PATH).convert("RGBA")
    
    # Fit source image inside a canvas with extra top margin so the head is NEVER cut off
    # Scale image to slightly fit with top headroom
    headroom_shift = 55 # Shift image DOWN by 55 pixels to give clear headroom at top
    
    # Create canvas background matching the red backdrop color of the image edges
    # Sample background color from top corners of raw_img
    bg_color = raw_img.getpixel((10, 10))
    
    canvas_base = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), bg_color)
    
    # Resize raw_img to fit width
    scale_factor = TARGET_WIDTH / raw_img.width
    scaled_w = TARGET_WIDTH
    scaled_h = int(raw_img.height * scale_factor)
    
    resized_raw = raw_img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    
    # Paste resized image onto canvas shifted DOWN by headroom_shift
    paste_y = headroom_shift
    canvas_base.paste(resized_raw, (0, paste_y), resized_raw)
    
    base_img = canvas_base
    
    # Create soft subject focus mask
    mask = Image.new("L", (TARGET_WIDTH, TARGET_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    # Focus oval positioned over the subject's face & torso
    mask_draw.ellipse([TARGET_WIDTH * 0.22, TARGET_HEIGHT * 0.08, TARGET_WIDTH * 0.78, TARGET_HEIGHT * 0.98], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=75))
    
    bg_img = base_img.filter(ImageFilter.GaussianBlur(radius=18))
    fg_img = base_img
    
    particles = create_particle_system(75, TARGET_WIDTH, TARGET_HEIGHT)
    
    # Setup OpenCV VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, FPS, (TARGET_WIDTH, TARGET_HEIGHT))
    
    for frame_idx in range(NUM_FRAMES):
        progress = frame_idx / (NUM_FRAMES - 1)
        
        # Sharpened motion curves (crisp acceleration and defined stop beats)
        t_cycle = math.sin(progress * math.pi)
        eased_t = ease_in_out_quint(t_cycle)
        
        # 1. Sharpened Camera Motion Path (Zoom 1.0x to 1.14x, Crisp Pan & Tilt)
        zoom_scale = 1.0 + 0.14 * eased_t
        pan_x = math.sin(progress * math.pi * 2) * 28 * eased_t
        # Keep pan_y upward minimal so head stays perfectly in frame
        pan_y = (1.0 - math.cos(progress * math.pi * 2)) * 10 * eased_t
        
        # Background parallax layer
        bg_scale = zoom_scale * 1.05
        bg_w, bg_h = int(TARGET_WIDTH * bg_scale), int(TARGET_HEIGHT * bg_scale)
        bg_scaled = bg_img.resize((bg_w, bg_h), Image.Resampling.BILINEAR)
        
        bg_left = (bg_w - TARGET_WIDTH) // 2 + int(pan_x * 0.4)
        bg_top = (bg_h - TARGET_HEIGHT) // 2 + int(pan_y * 0.4)
        bg_cropped = bg_scaled.crop((bg_left, bg_top, bg_left + TARGET_WIDTH, bg_top + TARGET_HEIGHT))
        
        # Foreground (subject) layer - keep top aligned to preserve headroom
        fg_w, fg_h = int(TARGET_WIDTH * zoom_scale), int(TARGET_HEIGHT * zoom_scale)
        fg_scaled = fg_img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
        
        fg_left = (fg_w - TARGET_WIDTH) // 2 + int(pan_x)
        # Position top crop at 0 so top headroom is preserved during zoom
        fg_top = max(0, int(pan_y))
        fg_cropped = fg_scaled.crop((fg_left, fg_top, fg_left + TARGET_WIDTH, fg_top + TARGET_HEIGHT))
        
        # Composite subject over background using parallax mask
        frame = Image.composite(fg_cropped, bg_cropped, mask)
        
        # 2. Crisp Dynamic Light Sweep (Anamorphic lens flare sheen)
        light_layer = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
        light_draw = ImageDraw.Draw(light_layer)
        
        sweep_x = int(progress * TARGET_WIDTH * 1.6 - TARGET_WIDTH * 0.3)
        light_alpha = int(45 * math.sin(progress * math.pi))
        light_draw.polygon([
            (sweep_x, 0),
            (sweep_x + 300, 0),
            (sweep_x + 100, TARGET_HEIGHT),
            (sweep_x - 200, TARGET_HEIGHT)
        ], fill=(255, 215, 170, light_alpha))
        light_layer = light_layer.filter(ImageFilter.GaussianBlur(radius=45))
        frame = Image.alpha_composite(frame, light_layer)
        
        # 3. Atmospheric Floating Bokeh Particles
        particle_layer = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(particle_layer)
        
        for p in particles:
            px = (p['x'] + p['speed_x'] * frame_idx * p['depth'] + pan_x * p['depth']) % TARGET_WIDTH
            py = (p['y'] + p['speed_y'] * frame_idx * p['depth'] + pan_y * p['depth']) % TARGET_HEIGHT
            
            p_size = p['size'] * (0.85 + 0.35 * math.sin(frame_idx * 0.08 + p['x']))
            p_alpha = int(255 * p['alpha'] * (0.7 + 0.3 * math.sin(frame_idx * 0.1 + p['y'])))
            
            p_draw.ellipse([px - p_size, py - p_size, px + p_size, py + p_size],
                           fill=(255, int(220 - p['hue_shift']), int(170 - p['hue_shift']), p_alpha))
            
        particle_layer = particle_layer.filter(ImageFilter.GaussianBlur(radius=1.8))
        frame = Image.alpha_composite(frame, particle_layer)
        
        # 4. Sharpen Details & Enhance Contrast / Color Tone
        frame_rgb = frame.convert("RGB")
        
        # Apply UnsharpMask filter to sharpen facial features and motion crispness
        frame_rgb = frame_rgb.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=3))
        
        enhancer = ImageEnhance.Contrast(frame_rgb)
        frame_rgb = enhancer.enhance(1.10)
        color_enhancer = ImageEnhance.Color(frame_rgb)
        frame_rgb = color_enhancer.enhance(1.06)
        
        # Save individual WebP frame for web scroll scrubbing
        frame_filename = os.path.join(FRAMES_DIR, f"frame_{frame_idx:03d}.webp")
        frame_rgb.save(frame_filename, "WEBP", quality=92)
        
        # Write to MP4 video stream
        cv_frame = cv2.cvtColor(np.array(frame_rgb), cv2.COLOR_RGB2BGR)
        out_video.write(cv_frame)
        
        if (frame_idx + 1) % 30 == 0 or frame_idx == NUM_FRAMES - 1:
            print(f"Rendered {frame_idx + 1}/{NUM_FRAMES} frames...")
            
    out_video.release()
    print(f"Successfully re-rendered video with top headroom & sharp motion: {OUTPUT_VIDEO_PATH}")

if __name__ == "__main__":
    main()
