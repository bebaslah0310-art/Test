import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import tempfile
import subprocess
import wave
import os

st.set_page_config(page_title="Dark Programmer Cinematic - WA Status", page_icon="💻", layout="centered")

st.title("💻 Dark Programmer Cinematic Generator")
st.markdown("Cukup tulis **kata-kata biasa**—sistem otomatis mengubahnya menjadi baris koding, efek ketikan, dan musik piano malam.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("🎨 Nuansa & Visual")

cinematic_palette = st.sidebar.selectbox(
    "Tema Warna Malam",
    [
        "Midnight Rain (Hitam Pekat - Biru Es)",
        "Cold Slate (Abu Malam - Cyan Dingin)",
        "Obsidian Frost (Gelap - Perak/Biru)",
        "Matrix Night (Hitam - Hijau Terminal)"
    ]
)

PALETTES = {
    "Midnight Rain (Hitam Pekat - Biru Es)": {
        "bg": (5, 7, 11), "win": (10, 14, 22), "primary": (175, 220, 255),
        "accent": (95, 175, 255), "keyword": (198, 120, 221), "string": (152, 195, 121),
        "muted": (75, 100, 130), "rain": (45, 70, 100)
    },
    "Cold Slate (Abu Malam - Cyan Dingin)": {
        "bg": (8, 10, 14), "win": (15, 19, 26), "primary": (195, 238, 248),
        "accent": (80, 210, 225), "keyword": (255, 121, 198), "string": (139, 233, 253),
        "muted": (80, 105, 115), "rain": (40, 75, 85)
    },
    "Obsidian Frost (Gelap - Perak/Biru)": {
        "bg": (6, 6, 9), "win": (13, 14, 20), "primary": (215, 225, 240),
        "accent": (125, 155, 235), "keyword": (187, 154, 247), "string": (158, 206, 106),
        "muted": (85, 92, 115), "rain": (50, 58, 80)
    },
    "Matrix Night (Hitam - Hijau Terminal)": {
        "bg": (4, 8, 5), "win": (9, 15, 11), "primary": (165, 245, 185),
        "accent": (0, 255, 90), "keyword": (0, 210, 120), "string": (120, 255, 150),
        "muted": (45, 95, 60), "rain": (25, 65, 35)
    }
}
pal = PALETTES[cinematic_palette]

typing_speed = st.sidebar.slider("Kecepatan Ketik (Karakter/Detik)", min_value=10, max_value=26, value=16)
rain_intensity = st.sidebar.slider("Intensitas Hujan Malam", min_value=0, max_value=80, value=35)
end_duration = st.sidebar.slider("Durasi Penutup (Detik)", min_value=0.8, max_value=2.2, value=1.2, step=0.1)

audio_mode = st.sidebar.selectbox(
    "Musik Latar",
    [
        "Piano Ambient + Hujan Malam (Otomatis)",
        "Hanya Piano Ambient Tenang",
        "Upload Musik Piano Sendiri (.mp3/.wav)"
    ]
)

uploaded_audio = None
if audio_mode == "Upload Musik Piano Sendiri (.mp3/.wav)":
    uploaded_audio = st.sidebar.file_uploader("Pilih file audio:", type=["mp3", "wav"])

fps = 30

# --- INPUT UTAMA: HANYA GANTI KATA-KATA ---
default_words = """Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program."""

st.subheader("1. Cukup Ganti Kata-Kata di Bawah Ini")
user_words = st.text_area(
    "Tulis kalimat biasa (setiap baris otomatis diubah menjadi baris kode):",
    value=default_words,
    height=180
)

col1, col2 = st.columns(2)
with col1:
    code_style = st.selectbox(
        "2. Gaya Koding Otomatis:",
        [
            "JavaScript / Node.js (life.js)",
            "Python Script (reality.py)",
            "Linux / Bash Terminal (system.sh)",
            "C++ Kernel (core.cpp)"
        ]
    )
with col2:
    ending_mode = st.selectbox(
        "3. Status Penutup (Ending):",
        [
            "Auto-Deteksi dari Kata-Kata",
            "SESSION PAUSED (Rest Mode)",
            "SYSTEM REPAIRED (Success)",
            "FATAL ERROR (Crash)"
        ]
    )

# --- GENERATOR KODE OTOMATIS DARI KATA BIASA ---
def generate_auto_code(raw_text, style, outcome):
    lines = [l.strip() for l in raw_text.strip().split('\n') if l.strip()]
    if not lines:
        return [], ""

    # Tentukan kalimat klimaks otomatis (baris pertama atau baris terpanjang yang bermakna)
    climax_line = lines[0]

    code_entries = []  # tuple: (text, color_role)
    # color_role: 'sys' (accent), 'kw' (keyword), 'str' (string), 'norm' (primary)

    if style == "JavaScript / Node.js (life.js)":
        code_entries.append(("const reality = checkState();", "kw"))
        for idx, l in enumerate(lines):
            safe_str = l.replace('"', "'")
            if idx == 0:
                code_entries.append((f'console.warn("{safe_str}");', "str"))
            elif idx == len(lines) - 1:
                code_entries.append((f'return execute("{safe_str}");', "kw"))
            else:
                code_entries.append((f'let note_{idx} = "{safe_str}";', "norm"))
        if outcome == "error":
            code_entries.append(('throw new Error("SYSTEM_OVERLOAD");', "err"))
        elif outcome == "paused":
            code_entries.append(('process.emit("SESSION_PAUSED");', "sys"))
        else:
            code_entries.append(('console.log("STATUS: 100% OK");', "sys"))

    elif style == "Python Script (reality.py)":
        code_entries.append(("import mind, reality", "kw"))
        for idx, l in enumerate(lines):
            safe_str = l.replace('"', "'")
            if idx == 0:
                code_entries.append((f'assert not illusion, "{safe_str}"', "str"))
            elif idx == len(lines) - 1:
                code_entries.append((f'mind.run("{safe_str}")', "kw"))
            else:
                code_entries.append((f'log_{idx} = "{safe_str}"', "norm"))
        if outcome == "error":
            code_entries.append(('raise RuntimeError("HALTED")', "err"))
        elif outcome == "paused":
            code_entries.append(('sys.exit("SESSION PAUSED...")', "sys"))
        else:
            code_entries.append(('print("[OK] SYSTEM REPAIRED")', "sys"))

    elif style == "C++ Kernel (core.cpp)":
        code_entries.append(("#include <reality.h>", "kw"))
        code_entries.append(("void main() {", "kw"))
        for idx, l in enumerate(lines):
            safe_str = l.replace('"', "'")
            code_entries.append((f'  std::cout << "{safe_str}";', "norm" if idx > 0 else "str"))
        if outcome == "error":
            code_entries.append(('  return EXIT_FAILURE;', "err"))
        elif outcome == "paused":
            code_entries.append(('  sleep(SESSION_PAUSED);', "sys"))
        else:
            code_entries.append(('  return EXIT_SUCCESS;', "sys"))
        code_entries.append(("}", "kw"))

    else:  # Linux / Bash Terminal
        code_entries.append(("$ ./analyze_reality.sh", "sys"))
        for idx, l in enumerate(lines):
            code_entries.append((f'> {l}', "str" if idx == 0 else "norm"))
        if outcome == "error":
            code_entries.append(("[FATAL] Process terminated.", "err"))
        elif outcome == "paused":
            code_entries.append(("[STATE] SESSION PAUSED...", "sys"))
        else:
            code_entries.append(("[OK] All services operational.", "sys"))

    return code_entries, climax_line

def detect_outcome(text, choice):
    if choice.startswith("SESSION PAUSED"):
        return "paused"
    if choice.startswith("SYSTEM REPAIRED"):
        return "success"
    if choice.startswith("FATAL ERROR"):
        return "error"

    low = text.lower()
    paused_kw = ["pause", "rest", "break", "world run", "stop trying", "istirahat", "jeda", "berhenti"]
    error_kw = ["error", "fail", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit", "mati"]

    if any(w in low for w in paused_kw):
        return "paused"
    if any(w in low for w in error_kw):
        return "error"
    return "success"

# --- LOAD FONT ---
def get_font(size, bold=False):
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "arialbd.ttf"
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "arial.ttf"
        ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap_text(text, font, max_w, draw):
    words = text.split(' ')
    lines, cur = [], ""
    for w in words:
        test = cur + (" " if cur else "") + w
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            while draw.textbbox((0, 0), w, font=font)[2] > max_w:
                for i in range(1, len(w)):
                    if draw.textbbox((0, 0), w[:i], font=font)[2] > max_w:
                        lines.append(w[:i-1])
                        w = w[i-1:]
                        break
            cur = w
    if cur:
        lines.append(cur)
    return lines

# --- EFEK HUJAN MALAM ---
def draw_night_rain(draw, width, height, frame_idx, count, color):
    if count <= 0:
        return
    rng = np.random.default_rng(101)
    xs = rng.integers(0, width, size=count)
    y_offsets = rng.integers(0, height, size=count)
    speeds = rng.integers(14, 26, size=count)
    lengths = rng.integers(18, 42, size=count)

    for i in range(count):
        x = int(xs[i])
        y = int((y_offsets[i] + frame_idx * speeds[i]) % height)
        l = int(lengths[i])
        draw.line([(x, y), (x - 2, y + l)], fill=color, width=1)

# --- GENERATOR AUDIO PIANO AMBIENT + HUJAN MALAM ---
def generate_cinematic_piano_array(duration, include_rain=True, sample_rate=44100):
    total_samples = int(duration * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)

    if include_rain:
        rng = np.random.default_rng(7)
        white = rng.normal(0, 1, total_samples).astype(np.float32)
        kernel = np.ones(18, dtype=np.float32) / 18.0
        rain = np.convolve(white, kernel, mode='same')
        rain = rain / (np.max(np.abs(rain)) + 1e-6)
        audio += rain * 0.14

    notes_sequence = [
        (0.0, 220.00, 2.8),   # A3
        (0.9, 329.63, 2.5),   # E4
        (1.8, 493.88, 2.8),   # B4
        (2.8, 523.25, 3.0),   # C5
        (4.2, 174.61, 3.0),   # F3
        (5.1, 261.63, 2.6),   # C4
        (6.0, 440.00, 3.0),   # A4
        (7.5, 130.81, 3.2),   # C3
        (8.4, 392.00, 2.8),   # G4
        (9.5, 493.88, 3.2),   # B4
        (11.0, 196.00, 3.2),  # G3
        (12.0, 329.63, 3.5),  # E4
        (13.5, 220.00, 4.0),  # A3
    ]

    for start_t, freq, note_dur in notes_sequence:
        if start_t >= duration:
            break
        start_idx = int(start_t * sample_rate)
        end_idx = min(total_samples, int((start_t + note_dur) * sample_rate))
        local_t = np.linspace(0, (end_idx - start_idx) / sample_rate, end_idx - start_idx, dtype=np.float32)

        attack = np.minimum(1.0, local_t / 0.04)
        decay = np.exp(-local_t * 1.15)
        env = attack * decay

        tone = (
            np.sin(2 * np.pi * freq * local_t) * 0.65
            + np.sin(2 * np.pi * (freq * 2) * local_t) * 0.22 * np.exp(-local_t * 1.8)
            + np.sin(2 * np.pi * (freq * 3) * local_t) * 0.08 * np.exp(-local_t * 2.5)
        )
        audio[start_idx:end_idx] += tone * env * 0.35

    fade_in = min(total_samples, int(0.6 * sample_rate))
    fade_out = min(total_samples, int(0.9 * sample_rate))
    audio[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)
    audio[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)

    max_v = np.max(np.abs(audio))
    if max_v > 0:
        audio = (audio / max_v) * 0.82
    return audio

# --- RENDERER FRAME ---
def render_boot_frame(frame_idx, alpha, pal, rain_count, w=720, h=1280):
    img = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, w, h, frame_idx, rain_count // 2, pal["rain"])

    font_boot = get_font(26, bold=True)
    font_sub = get_font(17, bold=False)

    text_main = "SYSTEM BOOTING..."
    c_main = tuple(int(c * alpha) for c in pal["accent"])
    c_sub = tuple(int(c * alpha) for c in pal["muted"])

    bbox = draw.textbbox((0, 0), text_main, font=font_boot)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, h // 2 - 20), text_main, fill=c_main, font=font_boot)

    sub_text = "[ core_terminal :: midnight_session ]"
    sbbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    draw.text(((w - (sbbox[2] - sbbox[0])) // 2, h // 2 + 22), sub_text, fill=c_sub, font=font_sub)

    return np.array(img)

def render_terminal_stage(frame_idx, history, active_line, active_role, cursor_on, file_tab, pal, rain_count, w=720, h=1280):
    img = Image.new("RGB", (w, h), color=pal["bg"])
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, w, h, frame_idx, rain_count, pal["rain"])

    mx, my = 38, 175
    ww, wh = w - (mx * 2), h - (my * 2)

    draw.rectangle([mx, my, mx + ww, my + wh], fill=pal["win"], outline=pal["muted"], width=1)
    draw.line([(mx, my + 44), (mx + ww, my + 44)], fill=pal["muted"], width=1)

    hdr_font = get_font(16)
    draw.text((mx + 20, my + 14), f"SYSTEM:// {file_tab}  [02:14 AM]", fill=pal["muted"], font=hdr_font)

    body_font = get_font(23)
    num_font = get_font(19)
    max_tw = ww - 78
    line_h = 36
    curr_y = my + 68

    role_colors = {
        "sys": pal["accent"],
        "kw": pal["keyword"],
        "str": pal["string"],
        "err": (255, 85, 95),
        "norm": pal["primary"]
    }

    line_num = 1
    for text_item, role in history:
        col = role_colors.get(role, pal["primary"])
        wrapped = wrap_text(text_item, body_font, max_tw, draw)
        for idx, wl in enumerate(wrapped):
            if idx == 0:
                draw.text((mx + 16, curr_y + 3), f"{line_num:02d}", fill=pal["muted"], font=num_font)
            draw.text((mx + 56, curr_y), wl, fill=col, font=body_font)
            curr_y += line_h
        line_num += 1
        curr_y += 6

    if active_line is not None:
        col = role_colors.get(active_role, pal["primary"])
        disp = active_line + ("█" if cursor_on else " ")
        wrapped = wrap_text(disp, body_font, max_tw, draw)
        for idx, wl in enumerate(wrapped):
            if idx == 0:
                draw.text((mx + 16, curr_y + 3), f"{line_num:02d}", fill=pal["accent"], font=num_font)
            draw.text((mx + 56, curr_y), wl, fill=col, font=body_font)
            curr_y += line_h

    return np.array(img)

def render_climax_frame(frame_idx, climax_text, intensity, pal, rain_count, w=720, h=1280):
    base = Image.new("RGB", (w, h), color=(3, 5, 9))
    draw = ImageDraw.Draw(base)
    draw_night_rain(draw, w, h, frame_idx, rain_count, pal["rain"])

    line_col = tuple(int(c * intensity) for c in pal["muted"])
    draw.line([(85, h // 2 - 115), (w - 85, h // 2 - 115)], fill=line_col, width=1)
    draw.line([(85, h // 2 + 115), (w - 85, h // 2 + 115)], fill=line_col, width=1)

    c_font = get_font(36, bold=True)
    wrapped = wrap_text(climax_text.upper(), c_font, w - 110, draw)

    glow_layer = Image.new("RGB", (w, h), color=(0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)

    total_h = len(wrapped) * 50
    start_y = (h - total_h) // 2

    glow_col = tuple(int(c * 0.55 * intensity) for c in pal["accent"])
    text_col = tuple(int(c * intensity) for c in pal["primary"])

    for idx, line in enumerate(wrapped):
        bbox = g_draw.textbbox((0, 0), line, font=c_font)
        tx = (w - (bbox[2] - bbox[0])) // 2
        ty = start_y + idx * 50
        g_draw.text((tx, ty), line, fill=glow_col, font=c_font)

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
    combined = Image.fromarray(np.clip(np.array(base, dtype=np.int16) + np.array(glow_layer, dtype=np.int16), 0, 255).astype(np.uint8))

    final_draw = ImageDraw.Draw(combined)
    for idx, line in enumerate(wrapped):
        bbox = final_draw.textbbox((0, 0), line, font=c_font)
        tx = (w - (bbox[2] - bbox[0])) // 2
        ty = start_y + idx * 50
        final_draw.text((tx, ty), line, fill=text_col, font=c_font)

    return np.array(combined)

def render_ending_frame(frame_idx, fade_alpha, outcome, pal, rain_count, w=720, h=1280):
    img = Image.new("RGB", (w, h), color=(3, 4, 7))
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, w, h, frame_idx, int(rain_count * fade_alpha), pal["rain"])

    p_font = get_font(30, bold=True)
    s_font = get_font(18, bold=False)

    if outcome == "error":
        title_txt = "CRITICAL ERROR // HALTED"
        sub_txt = "Process terminated unexpectedly."
        base_col = (255, 75, 85)
    elif outcome == "paused":
        title_txt = "SESSION PAUSED..."
        sub_txt = "No more attempts. No more explanations."
        base_col = pal["accent"]
    else:
        title_txt = "SYSTEM REPAIRED // OK"
        sub_txt = "All processes running smoothly."
        base_col = pal["string"]

    main_col = tuple(int(c * fade_alpha) for c in base_col)
    sub_col = tuple(int(c * fade_alpha) for c in pal["primary"])

    b1 = draw.textbbox((0, 0), title_txt, font=p_font)
    draw.text(((w - (b1[2] - b1[0])) // 2, h // 2 - 30), title_txt, fill=main_col, font=p_font)

    b2 = draw.textbbox((0, 0), sub_txt, font=s_font)
    draw.text(((w - (b2[2] - b2[0])) // 2, h // 2 + 18), sub_txt, fill=sub_col, font=s_font)

    return np.array(img)

# --- EXPORT MP4 LANGSUNG VIA FFMPEG (BEBAS WARNING) ---
def export_video_direct_ffmpeg(frames, output_mp4_path, fps, audio_mode, uploaded_audio_file, include_rain):
    h, w, _ = frames[0].shape
    duration = len(frames) / fps

    wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav_path = wav_tmp.name
    wav_tmp.close()

    if audio_mode == "Upload Musik Piano Sendiri (.mp3/.wav)" and uploaded_audio_file is not None:
        in_aud = tempfile.NamedTemporaryFile(delete=False, suffix=".audio")
        in_aud.write(uploaded_audio_file.read())
        in_aud.close()
        subprocess.run(
            ["ffmpeg", "-y", "-i", in_aud.name, "-t", str(duration), "-ar", "44100", "-ac", "2", wav_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        os.remove(in_aud.name)
    else:
        audio_arr = generate_cinematic_piano_array(duration, include_rain=include_rain, sample_rate=44100)
        pcm16 = np.int16(np.clip(audio_arr, -1.0, 1.0) * 32767)
        stereo = np.column_stack([pcm16, pcm16])
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(stereo.tobytes())

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4_path
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for fr in frames:
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()

    if os.path.exists(wav_path):
        os.remove(wav_path)

# --- TOMBOL GENERATE ---
if st.button("🎬 Generate Video Coding Status WA", type="primary", use_container_width=True):
    if not user_words.strip():
        st.warning("Tulis minimal 1 baris kata-kata terlebih dahulu!")
    else:
        outcome = detect_outcome(user_words, ending_mode)
        code_entries, climax_text = generate_auto_code(user_words, code_style, outcome)
        file_tab = code_style.split("(")[-1].rstrip(")")

        with st.spinner("Menyusun baris kode, animasi hujan malam & audio piano..."):
            w, h = 720, 1280
            frames = []
            frames_per_char = max(1, round(fps / typing_speed))

            # 1. Pembukaan singkat (1.2 detik)
            boot_frames = int(fps * 1.2)
            for f in range(boot_frames):
                alpha = min(1.0, f / (fps * 0.45))
                frames.append(render_boot_frame(len(frames), alpha, pal, rain_intensity, w, h))

            # 2. Bagian Tengah: Baris koding muncul & diketik
            history = []
            for idx, (code_line, role) in enumerate(code_entries):
                # Baris pertama & terakhir sistem muncul cepat, isi kode diketik huruf demi huruf
                if idx == 0:
                    history.append((code_line, role))
                    for _ in range(int(fps * 0.35)):
                        frames.append(render_terminal_stage(len(frames), history, None, role, False, file_tab, pal, rain_intensity, w, h))
                else:
                    for ci in range(1, len(code_line) + 1):
                        sub = code_line[:ci]
                        for _ in range(frames_per_char):
                            frames.append(render_terminal_stage(len(frames), history, sub, role, True, file_tab, pal, rain_intensity, w, h))
                    history.append((code_line, role))
                    for _ in range(int(fps * 0.2)):
                        frames.append(render_terminal_stage(len(frames), history, None, role, False, file_tab, pal, rain_intensity, w, h))

                # Tampilkan layar klimaks tepat setelah baris pesan pertama selesai diketik
                if idx == 1 and climax_text:
                    climax_frames = int(fps * 1.7)
                    for cf in range(climax_frames):
                        inten = min(1.0, cf / (fps * 0.25))
                        frames.append(render_climax_frame(len(frames), climax_text, inten, pal, rain_intensity, w, h))

            # 3. Penutup Padat & Cepat (sesuai slider, default 1.2 detik)
            end_total = max(12, int(fps * end_duration))
            hold_part = int(end_total * 0.55)
            fade_part = max(1, end_total - hold_part)

            for ef in range(end_total):
                if ef < hold_part:
                    alpha = 1.0
                else:
                    alpha = max(0.0, 1.0 - (ef - hold_part) / fade_part)
                frames.append(render_ending_frame(len(frames), alpha, outcome, pal, rain_intensity, w, h))

            temp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            mp4_path = temp_mp4.name
            temp_mp4.close()

            include_rain = (audio_mode == "Piano Ambient + Hujan Malam (Otomatis)")
            export_video_direct_ffmpeg(frames, mp4_path, fps, audio_mode, uploaded_audio, include_rain)

            st.success(f"✅ Video selesai! (Gaya: **{file_tab}** | Ending: **{outcome.upper()}**)")
            st.video(mp4_path)

            with open(mp4_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Video MP4 (Siap Upload Status WA)",
                    data=f,
                    file_name=f"status_wa_coder_{outcome}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
