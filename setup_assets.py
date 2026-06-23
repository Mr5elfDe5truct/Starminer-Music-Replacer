import os
import subprocess
import shutil

tool_dir = os.path.dirname(os.path.abspath(__file__))
original_assets_dir = os.path.join(tool_dir, "OriginalAssets")
crypto_path = os.path.join(tool_dir, "crypto.json")

# Default relative paths
default_game_dir = os.path.abspath(os.path.join(tool_dir, "..", "game"))
unrealpak_path = r"C:\Program Files\Epic Games\UE_4.27\Engine\Binaries\Win64\UnrealPak.exe"

assets = [
    "MainMenu",
    "MainMenu_edit",
    "illspace_theme",
    "SW_Passive_Output_Remaster_SM",
    "Seagrave_-_Adrift",
    "Seagrave_-_Breathless",
    "Seagrave_-_Dream_Chamber",
    "Seagrave_-_Dust"
]

def check_templates_exist():
    for asset in assets:
        for ext in [".uasset", ".uexp"]:
            path = os.path.join(original_assets_dir, asset + ext)
            if not os.path.exists(path):
                return False
    return True

def setup_original_templates():
    if check_templates_exist():
        print("Original asset templates are already present in OriginalAssets/.")
        return True
        
    print("Original assets not found. Extracting templates from game files...")
    
    # Try to locate game directory
    game_dir = default_game_dir
    if not os.path.exists(game_dir):
        # Prompt user or look elsewhere
        print(f"Error: Game directory not found at default location: {game_dir}")
        print("Please make sure the ModTool folder is placed next to the game folder.")
        return False
        
    pak_path = os.path.join(game_dir, "ILLSpace", "Content", "Paks", "pakchunk0-WindowsNoEditor.pak")
    if not os.path.exists(pak_path):
        print(f"Error: Game pak file not found at: {pak_path}")
        return False
        
    if not os.path.exists(crypto_path):
        # Try to copy from game folder if available
        game_crypto = os.path.join(game_dir, "crypto.json")
        if os.path.exists(game_crypto):
            shutil.copy2(game_crypto, crypto_path)
            print(f"Copied crypto.json from game folder.")
        else:
            print(f"Error: crypto.json not found in ModTool or Game directory!")
            return False
            
    # Search for UnrealPak
    real_unrealpak = unrealpak_path
    if not os.path.exists(real_unrealpak):
        # Check system path
        which = shutil.which("UnrealPak.exe")
        if which:
            real_unrealpak = which
        else:
            print("Error: UnrealPak.exe not found. Please edit setup_assets.py or install UE4.27.")
            return False

    # Extract original files
    temp_extract = os.path.join(tool_dir, "temp_extracted")
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract)
    os.makedirs(temp_extract, exist_ok=True)
    
    # Extract matching files
    # Filter only Music SoundWaves to speed up extraction
    cmd = [
        real_unrealpak,
        pak_path,
        "-Extract", temp_extract,
        "-Filter=ILLSpace/Content/Audio/Music/SoundWaves/*",
        f"-cryptokeys={crypto_path}"
    ]
    
    print(f"Running UnrealPak to extract templates...")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Extraction failed: {e.stderr.decode()}")
        if os.path.exists(temp_extract):
            shutil.rmtree(temp_extract)
        return False
        
    # Copy assets to OriginalAssets
    extracted_soundwaves = os.path.join(temp_extract, "ILLSpace", "Content", "Audio", "Music", "SoundWaves")
    if not os.path.exists(extracted_soundwaves):
        print("Error: Extracted files not found where expected!")
        shutil.rmtree(temp_extract)
        return False
        
    copied = 0
    for asset in assets:
        for ext in [".uasset", ".uexp"]:
            src = os.path.join(extracted_soundwaves, asset + ext)
            dst = os.path.join(original_assets_dir, asset + ext)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                copied += 1
                
    # Clean up temp extraction
    shutil.rmtree(temp_extract)
    print(f"Successfully extracted and copied {copied} original template files.")
    return True

if __name__ == "__main__":
    setup_original_templates()
