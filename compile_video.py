import os
import cv2
import glob

FRAMES_DIR = r"c:\Users\mmpat\Downloads\portfolio\frames"
OUTPUT_VIDEO_PATH = r"c:\Users\mmpat\Downloads\portfolio\agent_cinematic.mp4"

def compile_video():
    frame_files = sorted(glob.glob(os.path.join(FRAMES_DIR, "*.webp")))
    if not frame_files:
        print("No frames found!")
        return

    print(f"Found {len(frame_files)} frames. Compiling MP4 video...")
    
    # Read first frame to get size
    first_frame = cv2.imread(frame_files[0])
    height, width, _ = first_frame.shape
    
    # Try different codecs
    codecs_to_try = [
        ('avc1', '.mp4'),
        ('mp4v', '.mp4'),
        ('MJPG', '.avi'),
        ('WMV2', '.wmv')
    ]
    
    out = None
    success = False
    
    for fourcc_str, ext in codecs_to_try:
        try:
            target_path = OUTPUT_VIDEO_PATH if ext == '.mp4' else OUTPUT_VIDEO_PATH.replace('.mp4', ext)
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            out = cv2.VideoWriter(target_path, fourcc, 60.0, (width, height))
            
            if not out.isOpened():
                print(f"Codec {fourcc_str} failed to open.")
                continue
                
            print(f"Writing video with codec {fourcc_str} to {target_path}...")
            for f in frame_files:
                frame_img = cv2.imread(f)
                out.write(frame_img)
                
            out.release()
            out = None
            
            if os.path.exists(target_path) and os.path.getsize(target_path) > 100000:
                print(f"SUCCESS: Generated {target_path} ({os.path.getsize(target_path)} bytes)")
                success = True
                break
        except Exception as e:
            print(f"Codec {fourcc_str} error: {e}")
            if out:
                out.release()

if __name__ == '__main__':
    compile_video()
