import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioClip
import tempfile
import os

st.set_page_config(page_title="WA Status System Terminal", page_icon="💻", layout="centered")

st.title("💻 WA Status System Terminal Generator")
st.markdown("Simulasi eksekusi skrip CMD/Linux: perintah diketik manual, output sistem muncul instan, dengan suara *mechanical keyboard* presisi.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("⚙️ Pengaturan Terminal")

theme = st.sidebar.selectbox(
    "Tema Terminal",
    [
        "Kali Linux / Matrix (Hitam - Hijau)",
        "Windows CMD Classic (Hitam - Putih/Abu)",
        "Cyberpunk Dark (Gelap - Cyan/Pink)",
        "Amber Mainframe (Hitam - Oranye)"
    ]
)

THEMES = {
    "Kali Linux / Matrix (Hitam - Hijau)": {
        "bg": (10, 12, 10),
        "cmd": (0, 255, 65),       # Warna ketikan perintah
        "out": (180, 235, 190),    # Warna output sistem
        "header": (25, 30, 25),
        "border": (0, 180, 45)
    },
    "Windows CMD Classic (Hitam - Putih/Abu)": {
        "bg": (12, 12, 12),
        "cmd": (255, 255, 255),
        "out": (204, 204, 204),
        "header": (35, 35, 35),
        "border": (100, 100, 100)
    },
    "Cyberpunk Dark (Gelap - Cyan/Pink)": {
        "bg": (13, 17, 23),
        "cmd": (255, 42, 109),
        "out": (0, 240, 255),
        "header": (22, 27, 34),
        "border": (0, 240, 255)
    },
    "Amber Mainframe (Hitam - Oranye)": {
        "bg": (15, 10, 5),
        "cmd": (255, 190, 30),
        "out": (220, 140, 20),
        "header": (30, 22, 15),
        "border": (200, 120, 0)
    }
}
colors = THEMES[theme]

window_title = st.sidebar.text_input("Judul Window Terminal", value="Administrator: Command Prompt - system.exe")
font_size = st.sidebar.slider("Ukuran Font", min_value=22, max_value=42, value=28)
fps = 30  # Dikunci di 30 FPS agar sinkronisasi audio-frame maksimal
typing_speed = st.sidebar.slider("Kecepatan Ketik Perintah (Karakter/Detik)", min_value=8, max_value=25, value=14)
add_sound = st.sidebar.checkbox("Suara Mechanical Keyboard + Enter", value=True)

# --- PANDUAN FORMAT ---
with st.expander("📖 Cara Kerja Format Teks (Klik untuk baca)", expanded=False):
    st.markdown("""
    * **Awali baris dengan `$` atau `>`** : Sistem akan **mengetiknya huruf demi huruf** seolah-olah programmer sedang mengetik perintah (disertai suara ketikan).
    * **Baris TANPA `$` atau `>`** : Dianggap sebagai **respon/output sistem**, sehingga langsung muncul seketika setelah tombol *Enter* ditekan.
    * **Gunakan `[LOADING]`** : Otomatis memunculkan animasi progress bar `[██████████] 100%`.
    """)

default_script = """$ ./check_mindset.sh --user=me
[INFO] Memindai status mental...
[LOADING]
[OK] Fokus terverifikasi.

$ echo "Catatan Hari Ini:"
> Error di tengah jalan itu wajar.
> Yang penting jangan stop prosesnya,
> cukup debug lalu compile ulang.

$ systemctl restart semangat.service
[SUCCESS] Service berjalan normal (PID 2026).
$ exit"""

user_script = st.text_area("Masukkan Skenario Terminal:", value=default_script, height=260)

# --- FUNGSI LOAD FONT ---
def get_font(size):
    font_paths = [
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
            # Potong paksa jika 1 kata melebihi lebar layar
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
def render_terminal_frame(history_lines, active_cmd_text, show_cursor, font, colors, title, width=720, height=1280):
    img = Image.new("RGB", (width, height), color=colors["bg"])
    draw = ImageDraw.Draw(img)

    margin_x = 40
    margin_y = 200
    win_w = width - (margin_x * 2)
    win_h = height - (margin_y * 2)

    # Frame Window Terminal
    draw.rectangle([margin_x, margin_y, margin_x + win_w, margin_y + win_h], fill=colors["bg"], outline=colors["border"], width=2)

    # Header Bar
    header_h = 48
    draw.rectangle([margin_x, margin_y, margin_x + win_w, margin_y + header_h], fill=colors["header"])
    btn_y = margin_y + 24
    draw.ellipse([margin_x + 20, btn_y - 7, margin_x + 34, btn_y + 7], fill=(255, 95, 86))
    draw.ellipse([margin_x + 46, btn_y - 7, margin_x + 60, btn_y + 7], fill=(255, 189, 46))
    draw.ellipse([margin_x + 72, btn_y - 7, margin_x + 86, btn_y + 7], fill=(39, 201, 63))

    title_font = get_font(17)
    draw.text((margin_x + 105, margin_y + 14), title, fill=(190, 190, 190), font=title_font)

    # Gabungkan semua baris untuk ditampilkan (dengan auto-scroll jika penuh)
    max_text_width = win_w - 50
    line_height = int(font_size * 1.38)
    max_visible_lines = (win_h - header_h - 50) // line_height

    rendered_entries = []  # list of (text, color)
    for line_text, is_cmd in history_lines:
        color = colors["cmd"] if is_cmd else colors["out"]
        for w_line in wrap_single_line(line_text, font, max_text_width, draw):
            rendered_entries.append((w_line, color))

    if active_cmd_text is not None:
        cursor_char = "█" if show_cursor else " "
        wrapped_active = wrap_single_line(active_cmd_text + cursor_char, font, max_text_width, draw)
        for idx, w_line in enumerate(wrapped_active):
            rendered_entries.append((w_line, colors["cmd"]))
    else:
        # Kursor idle di baris baru
        if show_cursor:
            rendered_entries.append(("█", colors["cmd"]))

    # Ambil baris terakhir jika melebihi tinggi window (efek terminal scroll ke atas)
    visible_entries = rendered_entries[-max_visible_lines:]

    curr_y = margin_y + header_h + 25
    text_x = margin_x + 25
    for text_line, line_color in visible_entries:
        draw.text((text_x, curr_y), text_line, fill=line_color, font=font)
        curr_y += line_height

    return np.array(img)

# --- GENERATOR SUARA KEYBOARD MEKANIKAL SINKRON ---
def build_synchronized_audio(total_frames, fps, sound_events):
    """
    sound_events: list of tuple (frame_index, event_type)
    event_type: 'key' (suara ketik ringan) atau 'enter' (suara tombol enter lebih berat)
    """
    sample_rate = 44100
    total_samples = int((total_frames / fps) * sample_rate) + sample_rate
    audio_buffer = np.zeros(total_samples, dtype=np.float32)

    rng = np.random.default_rng(42)

    # Pre-generate sampel suara 1x ketikan (22ms)
    key_len = int(0.022 * sample_rate)
    t_key = np.linspace(0, 0.022, key_len)
    noise_key = rng.normal(0, 1, key_len)
    # Kombinasi transient klik mekanikal + body thock
    key_sound = (noise_key * np.exp(-t_key * 220) * 0.45) + (np.sin(2 * np.pi * 240 * t_key) * np.exp(-t_key * 180) * 0.35)

    # Pre-generate sampel suara tombol ENTER (40ms, lebih dalam)
    ent_len = int(0.040 * sample_rate)
    t_ent = np.linspace(0, 0.040, ent_len)
    noise_ent = rng.normal(0, 1, ent_len)
    enter_sound = (noise_ent * np.exp(-t_ent * 140) * 0.55) + (np.sin(2 * np.pi * 150 * t_ent) * np.exp(-t_ent * 110) * 0.5)

    for frame_idx, ev_type in sound_events:
        start_sample = int((frame_idx / fps) * sample_rate)
        snd = enter_sound if ev_type == "enter" else key_sound
        end_sample = min(start_sample + len(snd), total_samples)
        if start_sample < total_samples:
            audio_buffer[start_sample:end_sample] += snd[:end_sample - start_sample]

    # Normalisasi agar tidak clipping/pecah
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
if st.button("🎬 Generate Video System Terminal", type="primary", use_container_width=True):
    if not user_script.strip():
        st.warning("Teks skenario tidak boleh kosong!")
    else:
        with st.spinner("Merender urutan eksekusi sistem & sinkronisasi audio..."):
            width, height = 720, 1280
            font = get_font(font_size)

            frames = []
            sound_events = []  # Menyimpan (nomor_frame, tipe_suara)
            history_lines = [] # Menyimpan baris yang sudah selesai dieksekusi

            frames_per_char = max(1, round(fps / typing_speed))

            def add_frame(active_cmd, cursor_on):
                frames.append(
                    render_terminal_frame(
                        history_lines, active_cmd, cursor_on, font, colors, window_title, width, height
                    )
                )

            # 1. Kursor siap di awal (0.6 detik)
            for f in range(int(fps * 0.6)):
                add_frame("", (f // 5) % 2 == 0)

            raw_lines = user_script.split('\n')

            for line in raw_lines:
                stripped = line.strip()

                # Baris kosong -> langsung tambah spasi antar blok
                if stripped == "":
                    history_lines.append(("", False))
                    for _ in range(3):
                        add_frame(None, True)
                    continue

                # CEK APAKAH PERINTAH (diawali $ atau >) ATAU OUTPUT SISTEM
                is_command = stripped.startswith("$") or stripped.startswith(">")

                if is_command:
                    # Ketik huruf demi huruf
                    for char_idx in range(1, len(line) + 1):
                        partial_cmd = line[:char_idx]
                        last_char = line[char_idx - 1]

                        # Trigger suara tepat di frame pertama karakter ini muncul
                        if last_char != " ":
                            sound_events.append((len(frames), "key"))

                        for _ in range(frames_per_char):
                            add_frame(partial_cmd, True)

                    # Jeda sesaat sebelum menekan Enter + Bunyi tombol ENTER
                    for _ in range(3):
                        add_frame(line, True)

                    sound_events.append((len(frames), "enter"))
                    history_lines.append((line, True))

                    # Jeda eksekusi sistem setelah Enter ditekan (0.35 detik)
                    for f in range(int(fps * 0.35)):
                        add_frame(None, (f // 4) % 2 == 0)

                elif stripped == "[LOADING]":
                    # Animasi progress bar sistem 0% -> 100%
                    steps = 10
                    for step in range(1, steps + 1):
                        bar = "█" * (step * 2) + "░" * ((steps - step) * 2)
                        pct = step * 10
                        prog_text = f"[{bar}] {pct}%"
                        temp_history = history_lines + [(prog_text, False)]
                        for _ in range(2):
                            frames.append(
                                render_terminal_frame(
                                    temp_history, None, False, font, colors, window_title, width, height
                                )
                            )
                    history_lines.append(("[████████████████████] 100%", False))

                else:
                    # OUTPUT SISTEM: Muncul instan 1 baris penuh seketika!
                    history_lines.append((line, False))
                    # Tahan 0.22 detik agar terbaca seperti log terminal yang mengalir cepat
                    for _ in range(int(fps * 0.22)):
                        add_frame(None, False)

            # 3. Kursor berkedip di akhir video (2.5 detik)
            for f in range(int(fps * 2.5)):
                add_frame(None, (f // 6) % 2 == 0)

            # Gabungkan frame menjadi video
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

            st.success("✅ Video selesai dirender dengan audio-visual tersinkronisasi!")
            st.video(temp_path)

            with open(temp_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download Video MP4 (Siap Upload WA)",
                    data=file,
                    file_name="status_wa_system.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
