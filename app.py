import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioClip
import tempfile
import os

# Konfigurasi Halaman
st.set_page_config(page_title="WA Status Coder Generator", page_icon="💻", layout="centered")

st.title("💻 WA Status Programmer Generator")
st.markdown("Buat video status WhatsApp (9:16) dengan efek ketikan terminal CMD/Hacker.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("⚙️ Pengaturan Tampilan")

theme = st.sidebar.selectbox(
    "Tema Terminal",
    ["Matrix Green (Hitam - Hijau)", "Cyberpunk (Gelap - Cyan/Pink)", "Amber Retro (Hitam - Oranye)", "Ubuntu Terminal (Ungu - Putih)"]
)

# Definisi Warna Tema
THEMES = {
    "Matrix Green (Hitam - Hijau)": {"bg": (10, 12, 10), "text": (0, 255, 65), "header": (25, 30, 25), "prompt": (0, 180, 45)},
    "Cyberpunk (Gelap - Cyan/Pink)": {"bg": (13, 17, 23), "text": (0, 240, 255), "header": (22, 27, 34), "prompt": (255, 42, 109)},
    "Amber Retro (Hitam - Oranye)": {"bg": (15, 10, 5), "text": (255, 176, 0), "header": (30, 22, 15), "prompt": (200, 120, 0)},
    "Ubuntu Terminal (Ungu - Putih)": {"bg": (48, 10, 36), "text": (245, 245, 245), "header": (65, 20, 50), "prompt": (118, 215, 114)}
}
colors = THEMES[theme]

window_title = st.sidebar.text_input("Judul Window CMD", value="root@server:~# bash status.sh")
font_size = st.sidebar.slider("Ukuran Font", min_value=24, max_value=48, value=32)
fps = st.sidebar.selectbox("FPS Video", [24, 30], index=0)
typing_speed = st.sidebar.slider("Kecepatan Ketik (Karakter per Detik)", min_value=8, max_value=30, value=16)
add_sound = st.sidebar.checkbox("Tambahkan Efek Suara Ketikan (Beep/Click)", value=True)

# --- INPUT TEKS ---
default_text = """$ initializing system... [OK]
$ loading_mindset.sh

"Jangan pernah menyerah hanya karena error hari ini.

Kadang hidup butuh di-debug,
bukan di-uninstall."

$ status: tetap_semangat --force
$ exit 0_"""

user_text = st.text_area("Masukkan Teks / Kode yang Akan Diketik:", value=default_text, height=220)

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

# --- FUNGSI WRAP TEXT AGAR TIDAK KELUAR LAYAR ---
def wrap_text(text, font, max_width, draw):
    lines = []
    for paragraph in text.split('\n'):
        if paragraph == "":
            lines.append("")
            continue
        words = paragraph.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # Jika satu kata sangat panjang, potong paksa
                while draw.textbbox((0, 0), word, font=font)[2] > max_width:
                    for i in range(1, len(word)):
                        if draw.textbbox((0, 0), word[:i], font=font)[2] > max_width:
                            lines.append(word[:i-1])
                            word = word[i-1:]
                            break
                current_line = word
        if current_line:
            lines.append(current_line)
    return "\n".join(lines)

# --- FUNGSI RENDER FRAME ---
def render_frame(visible_text, show_cursor, font, colors, title, width=720, height=1280):
    img = Image.new("RGB", (width, height), color=colors["bg"])
    draw = ImageDraw.Draw(img)

    # Margin Window Terminal di tengah layar 9:16
    margin_x = 45
    margin_y = 220
    win_w = width - (margin_x * 2)
    win_h = height - (margin_y * 2)

    # Kotak Utama Terminal + Border Tipis
    draw.rectangle([margin_x, margin_y, margin_x + win_w, margin_y + win_h], fill=colors["bg"], outline=colors["prompt"], width=2)

    # Header Bar Terminal (macOS / Linux style)
    header_h = 50
    draw.rectangle([margin_x, margin_y, margin_x + win_w, margin_y + header_h], fill=colors["header"])
    
    # 3 Tombol Window (Merah, Kuning, Hijau)
    btn_y = margin_y + 25
    draw.ellipse([margin_x + 20, btn_y - 8, margin_x + 36, btn_y + 8], fill=(255, 95, 86))
    draw.ellipse([margin_x + 48, btn_y - 8, margin_x + 64, btn_y + 8], fill=(255, 189, 46))
    draw.ellipse([margin_x + 76, btn_y - 8, margin_x + 92, btn_y + 8], fill=(39, 201, 63))

    # Judul Window
    title_font = get_font(18)
    draw.text((margin_x + 115, margin_y + 15), title, fill=(180, 180, 180), font=title_font)

    # Render Teks + Kursor Blok
    display_text = visible_text + ("█" if show_cursor else " ")
    text_x = margin_x + 25
    text_y = margin_y + header_h + 30
    line_spacing = int(font_size * 0.35)

    draw.multiline_text((text_x, text_y), display_text, fill=colors["text"], font=font, spacing=line_spacing)

    return np.array(img)

# --- GENERATOR AUDIO SINTETIS KETIKAN ---
def generate_typing_audio(duration, char_timestamps):
    sample_rate = 44100
    def make_frame(t):
        # t bisa berupa array numpy
        t_arr = np.atleast_1d(t)
        out = np.zeros_like(t_arr)
        for ts in char_timestamps:
            # Suara klik pendek 15ms setiap karakter muncul
            mask = (t_arr >= ts) & (t_arr < ts + 0.015)
            if np.any(mask):
                local_t = t_arr[mask] - ts
                # Gelombang klik mekanikal (kombinasi frekuensi + decay cepat)
                click = np.sin(2 * np.pi * 800 * local_t) * np.exp(-local_t * 250) * 0.3
                out[mask] += click
        return np.column_stack([out, out]) if out.ndim == 1 else out

    return AudioClip(make_frame, duration=duration, fps=sample_rate)

# --- TOMBOL GENERATE ---
if st.button("🎬 Generate Video Status WA", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("Teks tidak boleh kosong!")
    else:
        with st.spinner("Sedang merender frame & menyusun video MP4..."):
            width, height = 720, 1280  # Resolusi HD 9:16 ideal untuk WA Status
            font = get_font(font_size)
            
            # Dummy draw untuk menghitung wrapping teks
            dummy_img = Image.new("RGB", (width, height))
            dummy_draw = ImageDraw.Draw(dummy_img)
            wrapped_text = wrap_text(user_text, font, width - 140, dummy_draw)

            frames = []
            char_timestamps = []
            
            total_chars = len(wrapped_text)
            frames_per_char = max(1, round(fps / typing_speed))
            
            current_time = 0.0
            dt = 1.0 / fps

            # 1. Fase Kursor Berkedip Awal (1 detik)
            for f in range(fps):
                cursor_on = (f // (fps // 3)) % 2 == 0
                frames.append(render_frame("", cursor_on, font, colors, window_title, width, height))
                current_time += dt

            # 2. Fase Mengetik Karakter demi Karakter
            for i in range(1, total_chars + 1):
                sub_text = wrapped_text[:i]
                last_char = wrapped_text[i - 1]
                
                if last_char not in [' ', '\n']:
                    char_timestamps.append(current_time)

                # Jeda ekstra sedikit jika menemui baris baru atau titik
                extra_hold = int(fps * 0.25) if last_char in ['\n', '.'] else 0
                hold_frames = frames_per_char + extra_hold

                for f in range(hold_frames):
                    cursor_on = True if f < frames_per_char else ((f // (fps // 3)) % 2 == 0)
                    frames.append(render_frame(sub_text, cursor_on, font, colors, window_title, width, height))
                    current_time += dt

            # 3. Fase Kursor Berkedip Akhir (2.5 detik agar enak dibaca di WA)
            end_frames = int(fps * 2.5)
            for f in range(end_frames):
                cursor_on = (f // (fps // 3)) % 2 == 0
                frames.append(render_frame(wrapped_text, cursor_on, font, colors, window_title, width, height))
                current_time += dt

            # Buat Clip Video
            clip = ImageSequenceClip(frames, fps=fps)

            if add_sound and char_timestamps:
                audio = generate_typing_audio(clip.duration, char_timestamps)
                clip = clip.set_audio(audio)

            # Simpan ke file sementara dengan codec standar WhatsApp (H.264 + AAC)
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

            st.success("✅ Video berhasil dibuat!")
            
            # Tampilkan Preview
            st.video(temp_path)

            # Tombol Download
            with open(temp_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download Video MP4 (Siap Upload WA)",
                    data=file,
                    file_name="status_wa_coder.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
