import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import tempfile
import subprocess
import wave
import gc
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

typing_speed = st.sidebar.slider("Kecepatan Ketik (Karakter/Detik)", min_value=12, max_value=28, value=18)
rain_intensity = st.sidebar.slider("Intensitas Hujan Malam", min_value=0, max_value=60, value=28)
end_duration = st.sidebar.slider("Durasi Penutup (Detik)", min_value=0.8, max_value=2.0, value=1.1, step=0.1)

audio_mode = st.sidebar.selectbox(
    "Musik Latar",
    [
        "Piano Ambient + Hujan Malam (Otomatis)",
        "Hanya Piano Ambient Tenang",
        "Tanpa Suara (Super Cepat)"
    ]
)

fps = 20  # 20 FPS sangat ringan di server gratis namun tetap mulus untuk ketikan teks

# --- INPUT UTAMA ---
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

# --- GENERATOR KODE OTOMATIS ---
def generate_auto_code(raw_text, style, outcome):
    lines = [l.strip() for l in raw_text.strip().split('\n') if l.strip()]
    if not lines:
        return [], ""

    climax_line = lines[0]
    code_entries = []

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

    else:
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

@st.cache_resource
def get_font(size, bold=False):
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
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

def get_rain_data(width, height, count):
    if count <= 0:
        return None
    rng = np.random.default_rng(101)
    return (
        rng.integers(0, width, size=count),
        rng.integers(0, height, size=count),
        rng.integers(14, 24, size=count),
        rng.integers(14, 32, size=count)
    )

def draw_night_rain(draw, height, frame_idx, rain_data, color):
    if rain_data is None:
        return
    xs, y_offsets, speeds, lengths = rain_data
    for i in range(len(xs)):
        x = int(xs[i])
        y = int((y_offsets[i] + frame_idx * speeds[i]) % height)
        l = int(lengths[i])
        draw.line([(x, y), (x - 1, y + l)], fill=color, width=1)

# --- AUDIO PIANO AMBIENT RINGAN (22050 Hz HEMAT MEMORI) ---
def generate_cinematic_piano_wav(duration, wav_path, include_rain=True, mute=False):
    sample_rate = 22050
    total_samples = max(sample_rate, int(duration * sample_rate))
    audio = np.zeros(total_samples, dtype=np.float32)

    if not mute:
        if include_rain:
            rng = np.random.default_rng(7)
            white = rng.normal(0, 1, total_samples).astype(np.float32)
            kernel = np.ones(12, dtype=np.float32) / 12.0
            rain = np.convolve(white, kernel, mode='same')
            rain /= (np.max(np.abs(rain)) + 1e-6)
            audio += rain * 0.14

        notes_sequence = [
            (0.0, 220.00, 2.8), (0.9, 329.63, 2.5), (1.8, 493.88, 2.8), (2.8, 523.25, 3.0),
            (4.2, 174.61, 3.0), (5.1, 261.63, 2.6), (6.0, 440.00, 3.0), (7.5, 130.81, 3.2),
            (8.4, 392.00, 2.8), (9.5, 493.88, 3.2), (11.0, 196.00, 3.2), (12.0, 329.63, 3.5),
            (13.5, 220.00, 4.0)
        ]

        for start_t, freq, note_dur in notes_sequence:
            if start_t >= duration:
                break
            start_idx = int(start_t * sample_rate)
            end_idx = min(total_samples, int((start_t + note_dur) * sample_rate))
            if end_idx <= start_idx:
                continue
            local_t = np.linspace(0, (end_idx - start_idx) / sample_rate, end_idx - start_idx, dtype=np.float32)
            env = np.minimum(1.0, local_t / 0.04) * np.exp(-local_t * 1.15)
            tone = (
                np.sin(2 * np.pi * freq * local_t) * 0.65
                + np.sin(2 * np.pi * (freq * 2) * local_t) * 0.22 * np.exp(-local_t * 1.8)
            )
            audio[start_idx:end_idx] += tone * env * 0.35

        fade_in = min(total_samples, int(0.5 * sample_rate))
        fade_out = min(total_samples, int(0.8 * sample_rate))
        audio[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)
        audio[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)

        max_v = np.max(np.abs(audio))
        if max_v > 0:
            audio = (audio / max_v) * 0.82

    pcm16 = np.int16(np.clip(audio, -1.0, 1.0) * 32767)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())

# --- RENDERER FRAME (540x960 PORTRAIT 9:16 HEMAT RAM) ---
def render_boot_bytes(frame_idx, alpha, pal, rain_data, w=540, h=960):
    img = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, h, frame_idx, rain_data, pal["rain"])

    font_boot = get_font(20, bold=True)
    font_sub = get_font(13, bold=False)

    text_main = "SYSTEM BOOTING..."
    c_main = tuple(int(c * alpha) for c in pal["accent"])
    c_sub = tuple(int(c * alpha) for c in pal["muted"])

    bbox = draw.textbbox((0, 0), text_main, font=font_boot)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, h // 2 - 16), text_main, fill=c_main, font=font_boot)

    sub_text = "[ core_terminal :: midnight_session ]"
    sbbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    draw.text(((w - (sbbox[2] - sbbox[0])) // 2, h // 2 + 18), sub_text, fill=c_sub, font=font_sub)

    return img.tobytes()

def render_terminal_bytes(frame_idx, history, active_line, active_role, cursor_on, file_tab, pal, rain_data, w=540, h=960):
    img = Image.new("RGB", (w, h), color=pal["bg"])
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, h, frame_idx, rain_data, pal["rain"])

    mx, my = 28, 130
    ww, wh = w - (mx * 2), h - (my * 2)

    draw.rectangle([mx, my, mx + ww, my + wh], fill=pal["win"], outline=pal["muted"], width=1)
    draw.line([(mx, my + 34), (mx + ww, my + 34)], fill=pal["muted"], width=1)

    hdr_font = get_font(12)
    draw.text((mx + 14, my + 10), f"SYSTEM:// {file_tab}  [02:14 AM]", fill=pal["muted"], font=hdr_font)

    body_font = get_font(17)
    num_font = get_font(14)
    max_tw = ww - 58
    line_h = 27
    curr_y = my + 52

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
                draw.text((mx + 12, curr_y + 2), f"{line_num:02d}", fill=pal["muted"], font=num_font)
            draw.text((mx + 42, curr_y), wl, fill=col, font=body_font)
            curr_y += line_h
        line_num += 1
        curr_y += 4

    if active_line is not None:
        col = role_colors.get(active_role, pal["primary"])
        disp = active_line + ("█" if cursor_on else " ")
        wrapped = wrap_text(disp, body_font, max_tw, draw)
        for idx, wl in enumerate(wrapped):
            if idx == 0:
                draw.text((mx + 12, curr_y + 2), f"{line_num:02d}", fill=pal["accent"], font=num_font)
            draw.text((mx + 42, curr_y), wl, fill=col, font=body_font)
            curr_y += line_h

    return img.tobytes()

def render_climax_bytes(frame_idx, climax_text, intensity, pal, rain_data, w=540, h=960):
    base = Image.new("RGB", (w, h), color=(3, 5, 9))
    draw = ImageDraw.Draw(base)
    draw_night_rain(draw, h, frame_idx, rain_data, pal["rain"])

    line_col = tuple(int(c * intensity) for c in pal["muted"])
    draw.line([(65, h // 2 - 85), (w - 65, h // 2 - 85)], fill=line_col, width=1)
    draw.line([(65, h // 2 + 85), (w - 65, h // 2 + 85)], fill=line_col, width=1)

    c_font = get_font(27, bold=True)
    wrapped = wrap_text(climax_text.upper(), c_font, w - 85, draw)

    glow_layer = Image.new("RGB", (w, h), color=(0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)

    total_h = len(wrapped) * 38
    start_y = (h - total_h) // 2

    glow_col = tuple(int(c * 0.55 * intensity) for c in pal["accent"])
    text_col = tuple(int(c * intensity) for c in pal["primary"])

    for idx, line in enumerate(wrapped):
        bbox = g_draw.textbbox((0, 0), line, font=c_font)
        tx = (w - (bbox[2] - bbox[0])) // 2
        ty = start_y + idx * 38
        g_draw.text((tx, ty), line, fill=glow_col, font=c_font)

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=6))
    combined = Image.fromarray(np.clip(np.array(base, dtype=np.int16) + np.array(glow_layer, dtype=np.int16), 0, 255).astype(np.uint8))

    final_draw = ImageDraw.Draw(combined)
    for idx, line in enumerate(wrapped):
        bbox = final_draw.textbbox((0, 0), line, font=c_font)
        tx = (w - (bbox[2] - bbox[0])) // 2
        ty = start_y + idx * 38
        final_draw.text((tx, ty), line, fill=text_col, font=c_font)

    return combined.tobytes()

def render_ending_bytes(frame_idx, fade_alpha, outcome, pal, rain_data, w=540, h=960):
    img = Image.new("RGB", (w, h), color=(3, 4, 7))
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, h, frame_idx, rain_data, tuple(int(c * fade_alpha) for c in pal["rain"]))

    p_font = get_font(23, bold=True)
    s_font = get_font(14, bold=False)

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
    draw.text(((w - (b1[2] - b1[0])) // 2, h // 2 - 24), title_txt, fill=main_col, font=p_font)

    b2 = draw.textbbox((0, 0), sub_txt, font=s_font)
    draw.text(((w - (b2[2] - b2[0])) // 2, h // 2 + 14), sub_txt, fill=sub_col, font=s_font)

    return img.tobytes()

# --- TOMBOL GENERATE ---
if st.button("🎬 Generate Video Coding Status WA", type="primary", use_container_width=True):
    if not user_words.strip():
        st.warning("Tulis minimal 1 baris kata-kata terlebih dahulu!")
    else:
        if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
            try:
                os.remove(st.session_state["last_mp4"])
            except Exception:
                pass

        outcome = detect_outcome(user_words, ending_mode)
        code_entries, climax_text = generate_auto_code(user_words, code_style, outcome)
        file_tab = code_style.split("(")[-1].rstrip(")")

        with st.spinner("Merender video mode hemat RAM..."):
            w, h = 540, 960
            frames_per_char = max(1, round(fps / typing_speed))
            rain_data = get_rain_data(w, h, rain_intensity)

            boot_frames = int(fps * 1.0)
            climax_frames = int(fps * 1.5) if climax_text else 0
            end_total = max(10, int(fps * end_duration))

            mid_frames = 0
            for idx, (code_line, _) in enumerate(code_entries):
                if idx == 0:
                    mid_frames += int(fps * 0.35)
                else:
                    mid_frames += len(code_line) * frames_per_char + int(fps * 0.2)
                if idx == 1 and climax_text:
                    mid_frames += climax_frames

            total_frames = boot_frames + mid_frames + end_total
            total_duration = max(1.0, total_frames / fps)

            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wav_path = wav_tmp.name
            wav_tmp.close()

            is_mute = (audio_mode == "Tanpa Suara (Super Cepat)")
            include_rain = (audio_mode == "Piano Ambient + Hujan Malam (Otomatis)")
            generate_cinematic_piano_wav(total_duration, wav_path, include_rain=include_rain, mute=is_mute)

            temp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            mp4_path = temp_mp4.name
            temp_mp4.close()

            # Flag -threads 1 & -preset ultrafast mencegah lonjakan RAM di Streamlit Cloud
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{w}x{h}",
                "-pix_fmt", "rgb24",
                "-r", str(fps),
                "-i", "-",
                "-i", wav_path,
                "-threads", "1",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                mp4_path
            ]

            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            frame_counter = 0

            try:
                for f in range(boot_frames):
                    alpha = min(1.0, f / (fps * 0.4))
                    proc.stdin.write(render_boot_bytes(frame_counter, alpha, pal, rain_data, w, h))
                    frame_counter += 1

                history = []
                for idx, (code_line, role) in enumerate(code_entries):
                    if idx == 0:
                        history.append((code_line, role))
                        for _ in range(int(fps * 0.35)):
                            proc.stdin.write(render_terminal_bytes(frame_counter, history, None, role, False, file_tab, pal, rain_data, w, h))
                            frame_counter += 1
                    else:
                        for ci in range(1, len(code_line) + 1):
                            sub = code_line[:ci]
                            for _ in range(frames_per_char):
                                proc.stdin.write(render_terminal_bytes(frame_counter, history, sub, role, True, file_tab, pal, rain_data, w, h))
                                frame_counter += 1
                        history.append((code_line, role))
                        for _ in range(int(fps * 0.2)):
                            proc.stdin.write(render_terminal_bytes(frame_counter, history, None, role, False, file_tab, pal, rain_data, w, h))
                            frame_counter += 1

                    if idx == 1 and climax_text:
                        for cf in range(climax_frames):
                            inten = min(1.0, cf / (fps * 0.25))
                            proc.stdin.write(render_climax_bytes(frame_counter, climax_text, inten, pal, rain_data, w, h))
                            frame_counter += 1

                hold_part = int(end_total * 0.55)
                fade_part = max(1, end_total - hold_part)
                for ef in range(end_total):
                    alpha = 1.0 if ef < hold_part else max(0.0, 1.0 - (ef - hold_part) / fade_part)
                    proc.stdin.write(render_ending_bytes(frame_counter, alpha, outcome, pal, rain_data, w, h))
                    frame_counter += 1

                proc.stdin.close()
                proc.wait()

            except Exception as e:
                proc.kill()
                st.error(f"Terjadi kesalahan: {e}")
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                gc.collect()

            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                st.session_state["last_mp4"] = mp4_path
                st.session_state["last_outcome"] = outcome
                st.session_state["last_tab"] = file_tab
            else:
                err_msg = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
                st.error(f"Gagal membuat MP4. Detail: {err_msg[-300:]}")

if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
    st.success(f"✅ Video siap! (Gaya: **{st.session_state['last_tab']}** | Ending: **{st.session_state['last_outcome'].upper()}**)")
    st.video(st.session_state["last_mp4"])

    with open(st.session_state["last_mp4"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video MP4 (Siap Upload Status WA)",
            data=f.read(),
            file_name=f"status_wa_coder_{st.session_state['last_outcome']}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
