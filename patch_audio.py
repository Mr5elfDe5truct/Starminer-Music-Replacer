import os
import struct
import subprocess
import shutil

# Paths
tool_dir = os.path.dirname(os.path.abspath(__file__))
original_assets_dir = os.path.join(tool_dir, "OriginalAssets")
input_audio_dir = os.path.join(tool_dir, "InputAudio")
staged_dir = os.path.join(tool_dir, "Staged")
response_path = os.path.join(tool_dir, "response.txt")

# Auto-detect FFmpeg
ffmpeg_path = os.path.join(tool_dir, "Engine", "Binaries", "Win64", "ffmpeg.exe")
if not os.path.exists(ffmpeg_path):
    ffmpeg_path = os.path.join(tool_dir, "bin", "ffmpeg.exe")
if not os.path.exists(ffmpeg_path):
    ffmpeg_path = os.path.join(tool_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_path):
    ffmpeg_path = r"C:\Program Files\StoryVox\FFmpeg\ffmpeg.exe" # default fallback
if not os.path.exists(ffmpeg_path):
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        ffmpeg_path = which_ffmpeg


# Ensure directories exist
os.makedirs(input_audio_dir, exist_ok=True)
os.makedirs(staged_dir, exist_ok=True)

# Clean Staged directory from previous run
if os.path.exists(staged_dir):
    shutil.rmtree(staged_dir)
os.makedirs(staged_dir, exist_ok=True)

# Mount point staged subdir
soundwaves_staged_dir = os.path.join(staged_dir, "ILLSpace", "Content", "Audio", "Music", "SoundWaves")
os.makedirs(soundwaves_staged_dir, exist_ok=True)

# Mappings: Input Audio Name -> (Target Assets list, Original Duration template)
# If the user places a file (e.g. MainMenu.wav or MainMenu.mp3 or MainMenu.ogg),
# it will override all related menu SoundWaves.
mappings = {
    "MainMenu": (
        ["MainMenu", "MainMenu_edit", "illspace_theme", "SW_Passive_Output_Remaster_SM"],
        # Template dur: MainMenu: 114.75, MainMenu_edit: 148.0, illspace_theme: 127.756187, SW_Passive_Output_Remaster_SM: 507.112915
        [114.75, 148.0, 127.75618743896484, 507.1129150390625]
    ),
    "Adrift": (["Seagrave_-_Adrift"], [588.8]),
    "Breathless": (["Seagrave_-_Breathless"], [576.0]),
    "Dream_Chamber": (["Seagrave_-_Dream_Chamber"], [569.6]),
    "Dust": (["Seagrave_-_Dust"], [576.0])
}

def get_audio_duration_and_transcode(input_path, target_ogg_path):
    """
    Transcode input audio to standard OGG Vorbis (44100 Hz stereo) and return new duration.
    """
    print(f"  Transcoding {os.path.basename(input_path)} -> OGG Vorbis...")
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        "-c:a", "libvorbis",
        "-q:a", "4",
        "-ar", "44100",
        "-ac", "2",
        target_ogg_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Get duration of the new OGG file
    cmd_dur = [ffmpeg_path, "-i", target_ogg_path]
    res = subprocess.run(cmd_dur, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stderr = res.stderr.decode()
    duration = None
    for line in stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            duration = h * 3600 + m * 60 + s
            break
    return duration

def patch_and_stage(asset_name, ogg_path, new_duration, orig_duration):
    """
    Patch original uasset/uexp headers and stage them.
    """
    uasset_src = os.path.join(original_assets_dir, asset_name + ".uasset")
    uexp_src = os.path.join(original_assets_dir, asset_name + ".uexp")
    
    if not os.path.exists(uasset_src) or not os.path.exists(uexp_src):
        print(f"  Warning: Template for {asset_name} not found in OriginalAssets/!")
        return False
        
    with open(uasset_src, "rb") as f:
        uasset_data = bytearray(f.read())
    with open(uexp_src, "rb") as f:
        uexp_data = bytearray(f.read())
    with open(ogg_path, "rb") as f:
        new_ogg_data = f.read()
        
    new_ogg_size = len(new_ogg_data)
    payload_offset = uexp_data.find(b"OggS")
    if payload_offset == -1:
        print(f"  Error: Could not find OggS in {asset_name}.uexp!")
        return False
        
    # Find duration float in header
    orig_dur_bytes = struct.pack("<f", orig_duration)
    dur_idx = uexp_data.find(orig_dur_bytes, 0, payload_offset)
    if dur_idx == -1:
        # Fuzzy match
        found = False
        for i in range(payload_offset - 3):
            val, = struct.unpack("<f", uexp_data[i:i+4])
            if abs(val - orig_duration) < 0.5:
                dur_idx = i
                found = True
                break
        if not found:
            print(f"  Error: Could not find duration float in {asset_name}.uexp header!")
            return False
            
    # Update duration
    uexp_data[dur_idx:dur_idx+4] = struct.pack("<f", new_duration)
    
    # Update bulk data sizes
    bulk_data_flags_offset = payload_offset - 20
    uexp_data[bulk_data_flags_offset+4 : bulk_data_flags_offset+8] = struct.pack("<I", new_ogg_size)
    uexp_data[bulk_data_flags_offset+8 : bulk_data_flags_offset+12] = struct.pack("<I", new_ogg_size)
    
    # Reconstruct uexp
    orig_guid = uexp_data[len(uexp_data)-20 : len(uexp_data)-4]
    package_tag = b"\xC1\x83\x2A\x9E"
    new_uexp_data = uexp_data[:payload_offset] + new_ogg_data + orig_guid + package_tag
    
    # Update export size in uasset
    orig_export_size = len(uexp_data) - 4
    new_export_size = len(new_uexp_data) - 4
    
    orig_exp_size_bytes = struct.pack("<q", orig_export_size)
    new_exp_size_bytes = struct.pack("<q", new_export_size)
    
    exp_idx = uasset_data.find(orig_exp_size_bytes)
    if exp_idx == -1:
        print(f"  Error: Could not find export size in {asset_name}.uasset!")
        return False
    uasset_data[exp_idx:exp_idx+8] = new_exp_size_bytes
    
    # Save staged files
    staged_uasset_path = os.path.join(soundwaves_staged_dir, asset_name + ".uasset")
    staged_uexp_path = os.path.join(soundwaves_staged_dir, asset_name + ".uexp")
    
    with open(staged_uasset_path, "wb") as f:
        f.write(uasset_data)
    with open(staged_uexp_path, "wb") as f:
        f.write(new_uexp_data)
        
    print(f"  Staged patched {asset_name} (new size: {len(new_uexp_data)} bytes)")
    return True

# Scan InputAudio directory
supported_exts = [".wav", ".mp3", ".ogg"]
staged_files_count = 0

for input_name, (targets, orig_durations) in mappings.items():
    # Find if user provided an input audio file
    input_file = None
    for ext in supported_exts:
        test_path = os.path.join(input_audio_dir, input_name + ext)
        if os.path.exists(test_path):
            input_file = test_path
            break
            
    if not input_file:
        continue
        
    print(f"\nProcessing custom track: {os.path.basename(input_file)}")
    
    # Transcode to temp OGG
    temp_ogg = os.path.join(tool_dir, f"temp_{input_name}.ogg")
    try:
        new_duration = get_audio_duration_and_transcode(input_file, temp_ogg)
    except Exception as e:
        print(f"  Error transcoding: {e}")
        if os.path.exists(temp_ogg):
            os.remove(temp_ogg)
        continue
        
    # Patch and stage for all target assets
    for idx, target in enumerate(targets):
        orig_dur = orig_durations[idx]
        if patch_and_stage(target, temp_ogg, new_duration, orig_dur):
            staged_files_count += 2
            
    # Clean temp OGG
    if os.path.exists(temp_ogg):
        os.remove(temp_ogg)

if staged_files_count == 0:
    print("\nNo custom music found in InputAudio/! Please place files like MainMenu.wav or Breathless.wav there.")
    exit(1)

# Write dummy.txt at Staged/ root to force ../../../ mount
dummy_path = os.path.join(staged_dir, "dummy.txt")
with open(dummy_path, "w") as f:
    f.write("dummy")

# Generate response.txt mapping staged files to relative VFS paths
lines = []
for root, dirs, files in os.walk(staged_dir):
    for file in files:
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, staged_dir)
        vfs_path = "../../../" + rel_path.replace("\\", "/")
        lines.append(f'"{full_path}" "{vfs_path}"')

with open(response_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"\nStaged {staged_files_count} audio files. Generated response.txt.")
