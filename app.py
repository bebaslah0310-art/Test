import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioClip
import tempfile
import os

st.set_page_config(page_title="WA Status System Terminal", page_icon="💻", layout="centered")

st.title("💻 WA Status System Terminal Generator")
st.markdown("Cukup tulis **kata-kata biasa**, sistem otomatis mengubahnya menjadi skrip terminal programmer.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("🎨 Tema & Gaya Visual")

THEMES = {
    "Hacker Matrix (Hitam - Hijau Neon)": {
        "canvas": (5, 8, 5), "bg": (10, 14, 10), "cmd": (0, 255, 65),
        "out": (165, 235, 175), "header": (20, 30, 20), "border": (0, 200, 50),
        "grid": (12, 24, 12), "success_bg": (0, 65, 25), "success_fg": (50, 255, 110)
    },
    "Tokyo Night (Biru Malam - Neon)": {
        "canvas": (15, 16, 24), "bg": (26, 27, 38), "cmd": (122, 162, 247),
        "out": (158, 206, 106), "header": (36, 40, 59), "border": (187, 154, 247),
        "grid": (22, 24, 36), "success_bg": (35, 75, 50), "success_fg": (158, 206, 106)
    },
    "Dracula Pro (Ungu Gelap - Pink/Cyan)": {
        "canvas": (24, 25, 34), "bg": (40, 42, 54), "cmd": (255, 121, 198),
        "out": (139, 233, 253), "header": (52, 55, 70), "border": (189, 147, 249),
        "grid": (32, 34, 46), "success_bg": (30, 80, 55), "success_fg": (80, 250, 123)
    },
    "Synthwave '84 (Retro Ungu - Kuning/Pink)": {
        "canvas": (20, 12, 36), "bg": (38, 20, 71), "cmd": (254, 222, 93),
        "out": (255, 126, 219), "header": (54, 28, 99), "border": (54, 249, 246),
        "grid": (32, 18, 56), "success_bg": (15, 85, 85), "success_fg": (54, 249, 246)
    },
    "Monokai Pro (Abu Gelap - Kuning/Oranye)": {
        "canvas": (25, 24, 26), "bg": (45, 42, 46), "cmd": (255, 216, 102),
        "out": (169, 220, 118), "header": (64, 60, 65), "border": (252, 152, 103),
        "grid": (35, 33, 36), "success_bg": (45, 75, 35), "success_fg": (169, 220, 118)
    },
    "Nord Frost (Biru Arktik - Es)": {
        "canvas": (29, 33, 41), "bg": (46, 52, 64), "cmd": (136, 192, 208),
        "out": (216, 222, 233), "header": (59, 66, 82), "border": (129, 161, 193),
        "grid": (36, 41, 51), "success_bg": (45, 80, 65), "success_fg": (163, 190, 140)
    },
    "macOS Zsh Clean (Hitam - Putih/Hijau)": {
        "canvas": (18, 18, 20), "bg": (28, 28, 30), "cmd": (50, 215, 75),
        "out": (242, 242, 247), "header": (44, 44, 46), "border": (99, 99, 102),
        "grid": (24, 24, 26), "success_bg": (20, 75, 35), "success_fg": (50, 215, 75)
    },
    "Amber Mainframe CRT (Hitam - Emas)": {
        "canvas": (12, 8, 2), "bg": (20, 14, 4), "cmd": (255, 185, 35),
        "out": (215, 140, 25), "header": (38, 26, 8), "border": (220, 145, 20),
        "grid": (26, 18, 5), "success_bg": (75, 50, 5), "success_fg": (255, 210, 60)
    }
}

theme_name = st.sidebar.selectbox("Pilih Tema Terminal", list(THEMES.keys()), index=1)
colors = THEMES[theme_name]

bg_pattern = st.sidebar.selectbox("Efek Background Layar", ["Tech Grid Halus", "Polos Minimalis", "Scanline Monitor CRT"])
window_mode = st.sidebar.selectbox("Ukuran Window Terminal", ["Tall (Memanjang 9:16)", "Compact (Pas di Tengah)"])

st.sidebar.header("⚙️ Pengaturan Kecepatan")
font_size = st.sidebar.slider("Ukuran Font", min_value=22, max_value=38, value=26)
typing_speed = st.sidebar.slider("Kecepatan Ketik (Karakter/Detik)", min_value=12, max_value=28, value=18)
end_hold = st.sidebar.slider("Durasi Tahan Ending (Detik)", min_value=0.8, max_value=2.5, value=1.4, step=0.1)
add_sound = st.sidebar.checkbox("Suara Mechanical Keyboard + Audio Ending", value=True)

fps = 30

# --- INPUT UTAMA ---
default_quote = """REST MODE ACTIVATED.

Analyzing reality...

Not everything is real.

Some things are just well-written illusions.

Some promises are nothing but empty code.

So, stop trying to understand everything.

Take a break.

Let the world run its own program.

SESSION PAUSED..."""

st.subheader("1. Tulis Kata-Kata Anda")
raw_quotes = st.text_area(
    "Ketik kalimat biasa (tiap baris baru akan diketik berurutan):",
    value=default_quote,
    height=230
)

col1, col2 = st.columns(2)
with col1:
    ending_choice = st.selectbox(
        "2. Hasil Akhir (Ending):",
        [
            "Auto-Deteksi dari Kata-Kata",
            "PAUSED / STANDBY (Kuning)",
            "SUCCESS (Hijau)",
            "ERROR (Merah)"
        ]
    )
with col2:
    script_style = st.selectbox(
        "3. Gaya Pembungkus Sistem:",
        [
            "Clean Terminal (Langsung Ketik Teks)",
            "Diagnostik & Perbaikan (repair.sh)",
            "Eksekusi Pikiran (mindset.exe)",
            "Server Status (systemctl)"
        ]
    )

# --- FUNGSI DETEKSI SENTIMEN ---
def detect_outcome(text, choice):
    if choice.startswith("PAUSED"):
        return "paused"
    if choice.startswith("SUCCESS"):
        return "success"
    if choice.startswith("ERROR"):
        return "error"

    low = text.lower()
    paused_words = ["pause", "paused", "rest mode", "break", "standby", "sleep", "istirahat", "jeda", "berhenti sejenak"]
    error_words = ["error", "fail", "failed", "fatal", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit", "mati"]

    if any(w in low for w in paused_words):
        return "paused"
    if any(w in low for w in error_words):
        return "error"
    return "success"

# --- KONVERSI KATA BIASA MENJADI SKENARIO TERMINAL OTOMATIS ---
def build_terminal_script(quotes_text, outcome, style):
    raw_lines = [l.strip() for l in quotes_text.strip().split('\n') if l.strip()]
    if not raw_lines:
        return ""

    if style == "Clean Terminal (Langsung Ketik Teks)":
        formatted = []
        for idx, l in enumerate(raw_lines):
            low = l.lower()
            # Baris status sistem seperti "Analyzing reality..." atau "REST MODE..." muncul sebagai log sistem
            if idx == 0 and l.isupper():
                formatted.append(f"[SYS] {l}")
            elif low.endswith("...") and ("analyzing" in low or "loading" in low or "scanning" in low):
                formatted.append(l)
                formatted.append("[LOADING]")
            elif idx == len(raw_lines) - 1 and l.isupper():
                formatted.append(f"[STATE] {l}")
            else:
                formatted.append(f"> {l}")
        return "\n".join(formatted)

    script_blocks = []
    if style == "Diagnostik & Perbaikan (repair.sh)":
        script_blocks.append("$ ./system_check.sh --run")
        script_blocks.append("[LOADING]")
        for l in raw_lines:
            script_blocks.append(f"> {l}")
    elif style == "Eksekusi Pikiran (mindset.exe)":
        script_blocks.append("$ run mindset.exe --compile")
        script_blocks.append("[LOADING]")
        for l in raw_lines:
            script_blocks.append(f"> {l}")
    elif style == "Server Status (systemctl)":
        script_blocks.append("$ systemctl status reality.service")
        for l in raw_lines:
            script_blocks.append(f"> {l}")
        script_blocks.append("[LOADING]")

    return "\n".join(script_blocks)

# --- FUNGSI LOAD FONT ---
def get_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

# --- FUNGSI WRAP PER BARIS ---
def wrap_single_line(line, font, max_width, draw):
    if not line:
        return [""]
    words = line.split(' ')
    wrapped = []
    current = ""
    for word in words:
        test = current + (" " if current else "") + word
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                wrapped.append(current)
            while draw.textbbox((0, 0), word, font=font)[2] > max_width:
                for i in range(1, len(word)):
                    if draw.textbbox((0, 0), word[:i], font=font)[2] > max_width:
                        wrapped.append(word[:i-1])
                        word = word[i-1:]
                        break
            current = word
    if current:
        wrapped.append(current)
    return wrapped

# --- RENDER FRAME TERMINAL ---
def render_terminal_frame(
    history_lines, active_cmd_text, show_cursor, font, colors,
    title, mode, pattern, banner_text=None, banner_type="success", width=720, height=1280
):
    img = Image.new("RGB", (width, height), color=colors["canvas"])
    draw = ImageDraw.Draw(img)

    if pattern == "Tech Grid Halus":
        step = 36
        for x in range(0, width, step):
            draw.line([(x, 0), (x, height)], fill=colors["grid"], width=1)
        for y in range(0, height, step):
            draw.line([(0, y), (width, y)], fill=colors["grid"], width=1)
    elif pattern == "Scanline Monitor CRT":
        for y in range(0, height, 4):
            draw.line([(0, y), (width, y)], fill=colors["grid"], width=2)

    margin_x = 36
    margin_y = 135 if mode == "Tall (Memanjang 9:16)" else 220
    win_w = width - (margin_x * 2)
    win_h = height - (margin_y * 2)

    draw.rectangle([margin_x + 8, margin_y + 10, margin_x + win_w + 8, margin_y + win_h + 10], fill=(0, 0, 0))

    if banner_text:
        if banner_type == "error":
            active_border = (255, 65, 75)
        elif banner_type == "paused":
            active_border = (255, 195, 45)
        else:
            active_border = colors["success_fg"]
    else:
        active_border = colors["border"]

    draw.rectangle([margin_x, margin_y, margin_x + win_w, margin_y + win_h], fill=colors["bg"], outline=active_border, width=2)

    header_h = 46
    draw.rectangle([margin_x, margin_y, margin_x + win_w, margin_y + header_h], fill=colors["header"])
    btn_y = margin_y + 23
    draw.ellipse([margin_x + 18, btn_y - 7, margin_x + 32, btn_y + 7], fill=(255, 95, 86))
    draw.ellipse([margin_x + 44, btn_y - 7, margin_x + 58, btn_y + 7], fill=(255, 189, 46))
    draw.ellipse([margin_x + 70, btn_y - 7, margin_x + 84, btn_y + 7], fill=(39, 201, 63))

    title_font = get_font(16)
    draw.text((margin_x + 102, margin_y + 14), title, fill=(200, 200, 200), font=title_font)

    banner_space = 82 if banner_text else 0
    max_text_width = win_w - 44
    line_height = int(font_size * 1.38)
    max_visible_lines = (win_h - header_h - 40 - banner_space) // line_height

    rendered_entries = []
    for line_text, line_kind in history_lines:
        if line_kind == "muted":
            color = colors["border"]
        elif line_kind == "cmd":
            color = colors["cmd"]
        elif line_kind == "err_out":
            color = (255, 85, 95)
        elif line_kind == "warn_out":
            color = (255, 195, 45)
        elif line_kind == "ok_out":
            color = colors["success_fg"]
        else:
            color = colors["out"]

        for w_line in wrap_single_line(line_text, font, max_text_width, draw):
            rendered_entries.append((w_line, color))

    if banner_text is None:
        if active_cmd_text is not None:
            cursor_char = "█" if show_cursor else " "
            wrapped_active = wrap_single_line(active_cmd_text + cursor_char, font, max_text_width, draw)
            for w_line in wrapped_active:
                rendered_entries.append((w_line, colors["cmd"]))
        else:
            prompt_cursor = "$ █" if show_cursor else "$ "
            rendered_entries.append((prompt_cursor, colors["cmd"]))

    visible_entries = rendered_entries[-max_visible_lines:]

    curr_y = margin_y + header_h + 20
    text_x = margin_x + 22
    for text_line, line_color in visible_entries:
        draw.text((text_x, curr_y), text_line, fill=line_color, font=font)
        curr_y += line_height

    if banner_text:
        box_margin = 20
        box_h = 56
        box_y1 = margin_y + win_h - box_h - 18
        box_y2 = box_y1 + box_h
        box_x1 = margin_x + box_margin
        box_x2 = margin_x + win_w - box_margin

        if banner_type == "error":
            b_bg = (75, 12, 18)
            b_fg = (255, 75, 85)
        elif banner_type == "paused":
            b_bg = (68, 50, 10)
            b_fg = (255, 200, 50)
        else:
            b_bg = colors["success_bg"]
            b_fg = colors["success_fg"]

        draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=b_bg, outline=b_fg, width=2)

        banner_font_size = 21
        b_font = get_font(banner_font_size)
        while draw.textbbox((0, 0), banner_text, font=b_font)[2] > (box_x2 - box_x1 - 24) and banner_font_size > 13:
            banner_font_size -= 1
            b_font = get_font(banner_font_size)

        bbox = draw.textbbox((0, 0), banner_text, font=b_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = box_x1 + ((box_x2 - box_x1) - tw) // 2
        ty = box_y1 + ((box_y2 - box_y1) - th) // 2 - 2
        draw.text((tx, ty), banner_text, fill=b_fg, font=b_font)

    return np.array(img)

# --- GENERATOR SUARA KEYBOARD + ENDING AUDIO ---
def build_synchronized_audio(total_frames, fps, sound_events):
    sample_rate = 44100
    total_samples = int((total_frames / fps) * sample_rate) + sample_rate
    audio_buffer = np.zeros(total_samples, dtype=np.float32)

    rng = np.random.default_rng(42)

    key_len = int(0.022 * sample_rate)
    t_key = np.linspace(0, 0.022, key_len)
    noise_key = rng.normal(0, 1, key_len)
    key_sound = (noise_key * np.exp(-t_key * 220) * 0.45) + (np.sin(2 * np.pi * 240 * t_key) * np.exp(-t_key * 180) * 0.35)

    ent_len = int(0.040 * sample_rate)
    t_ent = np.linspace(0, 0.040, ent_len)
    noise_ent = rng.normal(0, 1, ent_len)
    enter_sound = (noise_ent * np.exp(-t_ent * 140) * 0.55) + (np.sin(2 * np.pi * 150 * t_ent) * np.exp(-t_ent * 110) * 0.5)

    # Chime Sukses (C6 -> G6)
    chime_len = int(0.28 * sample_rate)
    t_ch = np.linspace(0, 0.28, chime_len)
    part1 = np.where(t_ch < 0.11, np.sin(2 * np.pi * 1046.5 * t_ch) * np.exp(-t_ch * 12), 0)
    part2 = np.where(t_ch >= 0.11, np.sin(2 * np.pi * 1567.98 * (t_ch - 0.11)) * np.exp(-(t_ch - 0.11) * 10), 0)
    chime_sound = (part1 + part2) * 0.55

    # Nada Standby / Paused (G5 -> D5 lembut)
    pause_len = int(0.32 * sample_rate)
    t_pa = np.linspace(0, 0.32, pause_len)
    p1 = np.where(t_pa < 0.14, np.sin(2 * np.pi * 783.99 * t_pa) * np.exp(-t_pa * 10), 0)
    p2 = np.where(t_pa >= 0.14, np.sin(2 * np.pi * 587.33 * (t_pa - 0.14)) * np.exp(-(t_pa - 0.14) * 8), 0)
    pause_sound = (p1 + p2) * 0.50

    # Error Buzzer
    err_len = int(0.32 * sample_rate)
    t_er = np.linspace(0, 0.32, err_len)
    beep1 = np.where(t_er < 0.13, np.sign(np.sin(2 * np.pi * 190 * t_er)) * np.exp(-t_er * 10), 0)
    beep2 = np.where((t_er >= 0.16) & (t_er < 0.32), np.sign(np.sin(2 * np.pi * 145 * (t_er - 0.16))) * np.exp(-(t_er - 0.16) * 8), 0)
    error_sound = (beep1 + beep2) * 0.35

    for frame_idx, ev_type in sound_events:
        start_sample = int((frame_idx / fps) * sample_rate)
        if ev_type == "enter":
            snd = enter_sound
        elif ev_type == "success":
            snd = chime_sound
        elif ev_type == "paused":
            snd = pause_sound
        elif ev_type == "error":
            snd = error_sound
        else:
            snd = key_sound

        end_sample = min(start_sample + len(snd), total_samples)
        if start_sample < total_samples:
            audio_buffer[start_sample:end_sample] += snd[:end_sample - start_sample]

    max_val = np.max(np.abs(audio_buffer))
    if max_val > 0:
        audio_buffer = (audio_buffer / max_val) * 0.85

    duration = total_frames / fps
    def make_frame(t):
        t_arr = np.atleast_1d(t)
        indices = np.clip((t_arr * sample_rate).astype(int), 0, total_samples - 1)
        vals = audio_buffer[indices]
        return np.column_stack([vals, vals]) if vals.ndim == 1 else vals

    return AudioClip(make_frame, duration=duration, fps=sample_rate)

# --- PROSES GENERATE VIDEO ---
if st.button("🎬 Generate Video Status WA", type="primary", use_container_width=True):
    if not raw_quotes.strip():
        st.warning("Tulis minimal 1 baris kata-kata terlebih dahulu!")
    else:
        outcome = detect_outcome(raw_quotes, ending_choice)
        generated_script = build_terminal_script(raw_quotes, outcome, script_style)

        with st.spinner("Merender video terminal..."):
            width, height = 720, 1280
            font = get_font(font_size)

            frames = []
            sound_events = []
            history_lines = [("Kernel 6.8.0-sys #1 SMP [tty1]", "muted")]

            frames_per_char = max(1, round(fps / typing_speed))
            window_title = "root@reality:~# bash rest_mode.sh"

            def add_frame(active_cmd, cursor_on, banner=None):
                frames.append(
                    render_terminal_frame(
                        history_lines, active_cmd, cursor_on, font, colors,
                        window_title, window_mode, bg_pattern, banner, outcome, width, height
                    )
                )

            for f in range(int(fps * 0.2)):
                add_frame("", True)

            for line in generated_script.split('\n'):
                stripped = line.strip()
                is_command = stripped.startswith("$") or stripped.startswith(">")

                if is_command:
                    for char_idx in range(1, len(line) + 1):
                        partial_cmd = line[:char_idx]
                        if line[char_idx - 1] != " ":
                            sound_events.append((len(frames), "key"))
                        for _ in range(frames_per_char):
                            add_frame(partial_cmd, True)

                    for _ in range(2):
                        add_frame(line, True)

                    sound_events.append((len(frames), "enter"))
                    history_lines.append((line, "cmd"))

                    for f in range(int(fps * 0.22)):
                        add_frame(None, (f // 4) % 2 == 0)

                elif stripped == "[LOADING]":
                    for step in range(1, 11):
                        bar = "█" * (step * 2) + "░" * ((10 - step) * 2)
                        prog_text = f"[{bar}] {step * 10}%"
                        temp_history = history_lines + [(prog_text, "out")]
                        for _ in range(2):
                            frames.append(
                                render_terminal_frame(
                                    temp_history, None, False, font, colors,
                                    window_title, window_mode, bg_pattern, None, outcome, width, height
                                )
                            )
                    history_lines.append(("[████████████████████] 100%", "out"))

                else:
                    low_line = stripped.lower()
                    if any(tag in low_line for tag in ["[error]", "[fatal]", "[failed]"]):
                        kind = "err_out"
                    elif any(tag in low_line for tag in ["[sys]", "[state]"]):
                        kind = "warn_out"
                    elif any(tag in low_line for tag in ["[ok]", "[success]", "[active]"]):
                        kind = "ok_out"
                    else:
                        kind = "out"

                    history_lines.append((line, kind))
                    for _ in range(int(fps * 0.22)):
                        add_frame(None, False)

            # Banner Akhir sesuai konteks
            if outcome == "error":
                final_banner = "✖ CRITICAL ERROR // SYSTEM HALTED"
                sound_events.append((len(frames), "error"))
            elif outcome == "paused":
                final_banner = "⏸ SESSION PAUSED // REST MODE ACTIVE"
                sound_events.append((len(frames), "paused"))
            else:
                final_banner = "✔ SYSTEM REPAIRED // ALL SERVICES OK"
                sound_events.append((len(frames), "success"))

            end_frames = max(15, int(fps * end_hold))
            for f in range(end_frames):
                show_b = final_banner if (f >= 6 or f % 2 == 0) else None
                add_frame(None, False, banner=show_b)

            clip = ImageSequenceClip(frames, fps=fps)

            if add_sound and sound_events:
                audio_clip = build_synchronized_audio(len(frames), fps, sound_events)
                clip = clip.set_audio(audio_clip)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_path = temp_file.name
            temp_file.close()

            clip.write_videofile(
                temp_path,
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                verbose=False,
                logger=None
            )

            st.success(f"✅ Video selesai! (Ending: **{outcome.upper()}**)")
            st.video(temp_path)

            with open(temp_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download Video MP4",
                    data=file,
                    file_name=f"status_wa_{outcome}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
