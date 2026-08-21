import sys
from bot_ig_post import bot_post_story

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Argumen kurang!")
        print("Penggunaan: python bot_ig_post_story.py <file_path_media> [device_id]")
        sys.exit(1)
        
    file_path = sys.argv[1]
    device_id = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    bot_post_story(file_path, device_id)
