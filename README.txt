========================================================
            Starminer Music Replacer Mod Tool
========================================================

This tool allows you to easily replace the menu music and in-game exploration music of Starminer with your own custom tracks (WAV, MP3, or OGG format).

It handles transcoding to standard Ogg Vorbis, patching the asset file headers (durations, sizes, and export tables) to match the game's unversioned C++ serialization, building the encrypted patch pak, and cleaning up overriding loose files automatically.

--------------------------------------------------------
PREREQUISITES
--------------------------------------------------------

1. **Python 3**: Ensure Python 3 is installed and added to your system environment variables (PATH).
2. **FFmpeg**: The tool uses FFmpeg to transcode WAV and MP3 inputs. It will look for `ffmpeg` in your system PATH, a local `ffmpeg.exe` placed in the tool's folder, or the default installer path.
3. **UnrealPak**: Requires `UnrealPak.exe` (part of Unreal Engine 4.27). The tool will look for it in the default Epic Games installation path (`C:\Program Files\Epic Games\UE_4.27\Engine\Binaries\Win64\UnrealPak.exe`) or you can copy `UnrealPak.exe` (and its dependencies `libogg.dll` and `libvorbis.dll` from the UE4 folder) directly into this ModTool folder.

--------------------------------------------------------
SETUP
--------------------------------------------------------

1. Clone or extract this repository. For ease of use, make sure the `ModTool` folder is placed directly inside the main game directory (next to the `game` folder).
2. The repository does not host copyrighted original game assets. On first run, `run_mod.bat` will automatically run `setup_assets.py` to extract the required uasset/uexp templates directly from your local game files using UnrealPak and the provided `crypto.json` decryption key.

--------------------------------------------------------
HOW TO USE IT
--------------------------------------------------------

1. Place your custom music files inside the "InputAudio" folder.
   The tool supports WAV, MP3, and OGG formats.

2. Rename your files according to the track you want to replace:

   * Main Menu Theme:
     Rename your file to "MainMenu" (e.g. MainMenu.wav, MainMenu.mp3, MainMenu.ogg)
     This will replace all main menu themes (MainMenu, MainMenu_edit, illspace_theme, and SW_Passive_Output_Remaster_SM).

   * Seagrave Exploration Tracks:
     - Rename to "Adrift" (e.g. Adrift.wav) to replace Seagrave - Adrift.
     - Rename to "Breathless" (e.g. Breathless.wav) to replace Seagrave - Breathless.
     - Rename to "Dream_Chamber" (e.g. Dream_Chamber.wav) to replace Seagrave - Dream Chamber.
     - Rename to "Dust" (e.g. Dust.wav) to replace Seagrave - Dust.

   Note: You do not need to replace all tracks. If you only place "MainMenu.wav", only the menu music will be replaced and other tracks will remain unchanged.

3. Run the "run_mod.bat" batch file.
   It will:
   - Extract the original templates from the game pak (on the first run).
   - Convert and transcode your audio.
   - Patch the original headers.
   - Package them into the game's patch pak (pakchunk0-WindowsNoEditor_P.pak).
   - Clean up overrides.

4. Launch Starminer and enjoy your custom music!
