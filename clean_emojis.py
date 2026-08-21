import os
import sys
import unicodedata

WORKSPACE_DIR = "."

def is_emoji(char):
    cp = ord(char)
    # Emoji ranges
    if (0x1F300 <= cp <= 0x1F9FF) or (0x1FA00 <= cp <= 0x1FAFF) or (0x2600 <= cp <= 0x27BF) or (0x1F1E6 <= cp <= 0x1F1FF) or (0x1F600 <= cp <= 0x1F64F) or (0x1F680 <= cp <= 0x1F6FF):
        return True
    # Variation selectors (FE0F, FE0E)
    if cp in (0xFE0F, 0xFE0E):
        return True
    # Unicodedata category So (Symbol, Other)
    if unicodedata.category(char) == 'So':
        return True
    return False

def clean_file(filepath):
    # Jangan bersihkan file utilitas pembersih ini sendiri
    if os.path.basename(filepath) == "clean_emojis.py":
        return False
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            print(f"Gagal membaca {filepath}: {e}")
            return False
            
    # Filter content character by character
    new_content = "".join(c for c in content if not is_emoji(c))
    
    if new_content != content:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Berhasil membersihkan emoji dari: {os.path.basename(filepath)}")
            return True
        except Exception as e:
            print(f"Gagal menulis {filepath}: {e}")
            return False
    return False

def main():
    print("==================================================")
    print(" MEMULAI MEMBERSIHKAN EMOJI DI SEMUA MODUL BOT")
    print("==================================================")
    
    cleaned_count = 0
    # List all files in the directory
    for filename in os.listdir(WORKSPACE_DIR):
        if filename.endswith(".py"):
            filepath = os.path.join(WORKSPACE_DIR, filename)
            if clean_file(filepath):
                cleaned_count += 1
                
    print("==================================================")
    print(f"SELESAI! Berhasil membersihkan {cleaned_count} file Python.")
    print("==================================================")

if __name__ == "__main__":
    main()
