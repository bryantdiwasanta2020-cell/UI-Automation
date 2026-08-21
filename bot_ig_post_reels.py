import sys
from bot_ig_post import bot_post_reels

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Argumen kurang!")
        print("Penggunaan: python bot_ig_post_reels.py <file_path_video> <caption_text> [device_id]")
        sys.exit(1)
        
    file_path = sys.argv[1]
    caption = sys.argv[2] if len(sys.argv) > 2 else ""
    device_id = sys.argv[3] if len(sys.argv) > 3 else "all"
    
    bot_post_reels(file_path, caption, device_id)
