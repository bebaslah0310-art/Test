import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioClip, AudioFileClip, CompositeAudioClip
import tempfile
import os

st.set_page_config(page_title="Dark Programmer Cinematic - WA Status", page_icon="🌧️", layout="centered")

st.title("🌧️ Dark Programmer Cinematic Generator")
st.markdown("Konsep malam, hujan halus, terminal dingin, klimaks tipografi penuh, dan melodi piano ambient tenang.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("🎬 Pengaturan Sinematik")

cinematic_palette = st.sidebar.selectbox(
    "Nuansa Warna Dingin",
    [
        "Midnight Rain (Hitam Pekat - Biru Es)",
        "Cold Slate (Abu Malam - Cyan Dingin)",
        "Obsidian Frost (Gelap - Perak/Biru)"
    ]
)

PALETTES = {
    "Midnight Rain (Hitam Pekat - Biru Es)": {
        "bg": (5, 7, 11), "win": (10, 14, 22), "primary": (165, 215, 255),
        "accent": (95, 175, 255), "muted": (70, 95, 125), "rain": (45, 70, 100)
    },
    "Cold Slate (Abu Malam - Cyan Dingin)": {
        "bg": (8, 10, 14), "win": (15, 19, 26), "primary": (190, 235, 245),
        "accent": (80, 210, 225), "muted": (80, 105, 115), "rain": (40, 75, 85)
    },
    "Obsidian Frost (Gelap - Perak/Biru)": {
        "bg": (6, 6, 9), "win": (13, 14, 20), "primary": (215, 225, 240),
        "accent": (125, 155, 235), "muted": (85, 92, 115), "rain": (50, 58, 80)
    }
}
pal = PALETTES[cinematic_palette]

typing_speed = st.sidebar.slider("Kecepatan Ketik Perlahan (Karakter/Detik)", min_value=8, max_value=20, value=13)
rain_intensity = st.sidebar.slider("Intensitas Hujan Malam", min_value=0, max_value=80, value=35)
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
    uploaded_audio = st.sidebar.file_uploader("Pilih file audio piano:", type=["mp3", "wav"])

fps = 30

# --- INPUT TEKS ---
default_text = """SYSTEM:// CORE_TERMINAL
REST MODE ACTIVATED.
Analyzing reality...
Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program.
SESSION PAUSED...
No more attempts. No more explanations."""

st.subheader("Naskah Terminal")
user_text = st.text_area(
    "Edit teks sesuai kebutuhan (baris ke-4 otomatis menjadi klimaks layar penuh):",
    value=default_text,
    height=260
)

climax_line_input = st.text_input(
    "Teks Klimaks Layar Penuh:",
    value="NOT EVERYTHING IS REAL."
)

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
            cur = w
    if cur:
        lines.append(cur)
    return lines

# --- EFEK HUJAN MALAM HALUS ---
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
def generate_cinematic_piano_audio(duration, include_rain=True):
    sample_rate = 44100
    total_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, total_samples, dtype=np.float32)
    audio = np.zeros(total_samples, dtype=np.float32)

    # 1. Atmosfer Hujan Malam Lembut (Filtered Brown/Pink-ish Noise)
    if include_rain:
        rng = np.random.default_rng(7)
        white = rng.normal(0, 1, total_samples).astype(np.float32)
        # Moving average sederhana untuk meredam frekuensi tinggi agar terdengar seperti rintik hujan jauh
        kernel = np.ones(18, dtype=np.float32) / 18.0
        rain = np.convolve(white, kernel, mode='same')
        rain = rain / (np.max(np.abs(rain)) + 1e-6)
        audio += rain * 0.14

    # 2. Melodi Piano Ambient Minor Pelan (Am - F - C - G)
    # Frekuensi nada piano lembut (Hz)
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
        (13.5, 220.00, 4.0),  # A3 (resolve pelan)
    ]

    for start_t, freq, note_dur in notes_sequence:
        if start_t >= duration:
            break
        start_idx = int(start_t * sample_rate)
        end_idx = min(total_samples, int((start_t + note_dur) * sample_rate))
        local_t = np.linspace(0, (end_idx - start_idx) / sample_rate, end_idx - start_idx, dtype=np.float32)

        # Envelope piano: attack lembut (40ms) + decay panjang hangat
        attack = np.minimum(1.0, local_t / 0.04)
        decay = np.exp(-local_t * 1.15)
        env = attack * decay

        # Harmonik piano hangat (fundamental + oktaf lembut + fifth tipis)
        tone = (
            np.sin(2 * np.pi * freq * local_t) * 0.65
            + np.sin(2 * np.pi * (freq * 2) * local_t) * 0.22 * np.exp(-local_t * 1.8)
            + np.sin(2 * np.pi * (freq * 3) * local_t) * 0.08 * np.exp(-local_t * 2.5)
        )
        audio[start_idx:end_idx] += tone * env * 0.35

    # Fade in 0.8s & Fade out 1.5s agar transisi sinematik mulus
    fade_in_samples = min(total_samples, int(0.8 * sample_rate))
    fade_out_samples = min(total_samples, int(1.5 * sample_rate))
    audio[:fade_in_samples] *= np.linspace(0, 1, fade_in_samples, dtype=np.float32)
    audio[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples, dtype=np.float32)

    max_v = np.max(np.abs(audio))
    if max_v > 0:
        audio = (audio / max_v) * 0.82

    def make_frame(ts):
        ts_arr = np.atleast_1d(ts)
        idx = np.clip((ts_arr * sample_rate).astype(int), 0, total_samples - 1)
        v = audio[idx]
        return np.column_stack([v, v]) if v.ndim == 1 else v

    return AudioClip(make_frame, duration=duration, fps=sample_rate)

# --- RENDERER TIAP BABAK SINEMATIK ---
def render_boot_frame(frame_idx, progress_alpha, pal, rain_count, w=720, h=1280):
    img = Image.new("RGB", (w, h), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, w, h, frame_idx, rain_count // 2, pal["rain"])

    font_boot = get_font(26, bold=True)
    font_sub = get_font(18, bold=False)

    text_main = "SYSTEM BOOTING..."
    c_main = tuple(int(c * progress_alpha) for c in pal["accent"])
    c_sub = tuple(int(c * progress_alpha) for c in pal["muted"])

    bbox = draw.textbbox((0, 0), text_main, font=font_boot)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, h // 2 - 20), text_main, fill=c_main, font=font_boot)

    sub_text = "[ cold_kernel :: midnight_session ]"
    sbbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    stw = sbbox[2] - sbbox[0]
    draw.text(((w - stw) // 2, h // 2 + 24), sub_text, fill=c_sub, font=font_sub)

    return np.array(img)

def render_terminal_stage(frame_idx, history, active_line, cursor_on, pal, rain_count, w=720, h=1280):
    img = Image.new("RGB", (w, h), color=pal["bg"])
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, w, h, frame_idx, rain_count, pal["rain"])

    mx, my = 42, 180
    ww, wh = w - (mx * 2), h - (my * 2)

    # Window terminal minimalis gelap
    draw.rectangle([mx, my, mx + ww, my + wh], fill=pal["win"], outline=pal["muted"], width=1)
    draw.line([(mx, my + 44), (mx + ww, my + 44)], fill=pal["muted"], width=1)

    hdr_font = get_font(16)
    draw.text((mx + 20, my + 14), "SYSTEM:// CORE_TERMINAL  [02:14 AM]", fill=pal["muted"], font=hdr_font)

    body_font = get_font(25)
    max_tw = ww - 48
    line_h = 38
    curr_y = my + 72

    for text_item, kind in history:
        col = pal["accent"] if kind == "sys" else pal["primary"]
        for wl in wrap_text(text_item, body_font, max_tw, draw):
            draw.text((mx + 24, curr_y), wl, fill=col, font=body_font)
            curr_y += line_h
        curr_y += 8

    if active_line is not None:
        disp = active_line + ("_" if cursor_on else " ")
        for wl in wrap_text(disp, body_font, max_tw, draw):
            draw.text((mx + 24, curr_y), wl, fill=pal["primary"], font=body_font)
            curr_y += line_h

    return np.array(img)

def render_climax_frame(frame_idx, climax_text, intensity, pal, rain_count, w=720, h=1280):
    # Layar penuh dramatis untuk klimaks
    base = Image.new("RGB", (w, h), color=(3, 5, 9))
    draw = ImageDraw.Draw(base)
    draw_night_rain(draw, w, h, frame_idx, rain_count, pal["rain"])

    # Garis tipis sinematik atas & bawah
    line_col = tuple(int(c * intensity) for c in pal["muted"])
    draw.line([(90, h // 2 - 120), (w - 90, h // 2 - 120)], fill=line_col, width=1)
    draw.line([(90, h // 2 + 120), (w - 90, h // 2 + 120)], fill=line_col, width=1)

    c_font = get_font(38, bold=True)
    wrapped = wrap_text(climax_text.upper(), c_font, w - 110, draw)

    # Layer glow halus di belakang teks klimaks
    glow_layer = Image.new("RGB", (w, h), color=(0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)

    total_h = len(wrapped) * 52
    start_y = (h - total_h) // 2

    glow_col = tuple(int(c * 0.55 * intensity) for c in pal["accent"])
    text_col = tuple(int(c * intensity) for c in pal["primary"])

    for idx, line in enumerate(wrapped):
        bbox = g_draw.textbbox((0, 0), line, font=c_font)
        tw = bbox[2] - bbox[0]
        tx = (w - tw) // 2
        ty = start_y + idx * 52
        g_draw.text((tx, ty), line, fill=glow_col, font=c_font)

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
    combined = Image.fromarray(np.clip(np.array(base, dtype=np.int16) + np.array(glow_layer, dtype=np.int16), 0, 255).astype(np.uint8))

    final_draw = ImageDraw.Draw(combined)
    for idx, line in enumerate(wrapped):
        bbox = final_draw.textbbox((0, 0), line, font=c_font)
        tw = bbox[2] - bbox[0]
        tx = (w - tw) // 2
        ty = start_y + idx * 52
        final_draw.text((tx, ty), line, fill=text_col, font=c_font)

    return np.array(combined)

def render_ending_paused_frame(frame_idx, fade_alpha, pal, rain_count, w=720, h=1280):
    img = Image.new("RGB", (w, h), color=(3, 4, 7))
    draw = ImageDraw.Draw(img)
    draw_night_rain(draw, w, h, frame_idx, int(rain_count * fade_alpha), pal["rain"])

    p_font = get_font(32, bold=True)
    s_font = get_font(19, bold=False)

    main_col = tuple(int(c * fade_alpha) for c in pal["accent"])
    sub_col = tuple(int(c * fade_alpha) for c in pal["primary"])

    t1 = "SESSION PAUSED..."
    b1 = draw.textbbox((0, 0), t1, font=p_font)
    draw.text(((w - (b1[2] - b1[0])) // 2, h // 2 - 35), t1, fill=main_col, font=p_font)

    t2 = "No more attempts. No more explanations."
    b2 = draw.textbbox((0, 0), t2, font=s_font)
    draw.text(((w - (b2[2] - b2[0])) // 2, h // 2 + 18), t2, fill=sub_col, font=s_font)

    return np.array(img)

# --- TOMBOL GENERATE ---
if st.button("🎬 Render Video Dark Cinematic", type="primary", use_container_width=True):
    lines = [l.strip() for l in user_text.strip().split('\n') if l.strip()]
    if not lines:
        st.warning("Teks tidak boleh kosong.")
    else:
        with st.spinner("Merender adegan sinematik & menyusun audio piano ambient..."):
            w, h = 720, 1280
            frames = []
            frames_per_char = max(1, round(fps / typing_speed))

            # --- BABAK 1: PEMBUKAAN (SYSTEM BOOTING...) - 1.8 detik ---
            boot_total = int(fps * 1.8)
            for f in range(boot_total):
                alpha = min(1.0, f / (fps * 0.6))
                frames.append(render_boot_frame(len(frames), alpha, pal, rain_intensity, w, h))

            # --- BABAK 2: BAGIAN TENGAH (BARIS KODE & REFLEKSI) ---
            history = []
            climax_clean = climax_line_input.strip().lower().rstrip(".")

            for line in lines:
                low = line.lower().rstrip(".")

                # Lewati baris penutup akhir karena akan masuk ke Babak 4
                if "session paused" in low or "no more attempts" in low:
                    continue

                # Jika menyentuh kalimat klimaks -> masuk Babak 3 (Klimaks Layar Penuh)
                if climax_clean and climax_clean in low:
                    climax_frames = int(fps * 2.4)
                    for cf in range(climax_frames):
                        # Fade in cepat lalu tahan
                        inten = min(1.0, cf / (fps * 0.35))
                        frames.append(render_climax_frame(len(frames), line, inten, pal, rain_intensity, w, h))
                    history.append((line, "sys"))
                    continue

                # Baris status sistem muncul instan dengan jeda hening
                if line.startswith("SYSTEM://") or line.isupper() or line.endswith("..."):
                    history.append((line, "sys"))
                    for _ in range(int(fps * 0.55)):
                        frames.append(render_terminal_stage(len(frames), history, None, False, pal, rain_intensity, w, h))
                else:
                    # Kalimat reflektif diketik perlahan satu per satu
                    for ci in range(1, len(line) + 1):
                        sub = line[:ci]
                        for _ in range(frames_per_char):
                            frames.append(render_terminal_stage(len(frames), history, sub, True, pal, rain_intensity, w, h))
                    history.append((line, "msg"))
                    # Jeda emosional antar kalimat (0.45 detik)
                    for jf in range(int(fps * 0.45)):
                        frames.append(render_terminal_stage(len(frames), history, None, (jf // 6) % 2 == 0, pal, rain_intensity, w, h))

            # --- BABAK 4: PENUTUP (SESSION PAUSED... + FADE TO BLACK) - 3.2 detik ---
            end_total = int(fps * 3.2)
            for ef in range(end_total):
                # Tahan terang 1.8 detik, lalu perlahan gelap (fade out) 1.4 detik
                if ef < int(fps * 1.8):
                    alpha = 1.0
                else:
                    alpha = max(0.0, 1.0 - (ef - int(fps * 1.8)) / (fps * 1.4))
                frames.append(render_ending_paused_frame(len(frames), alpha, pal, rain_intensity, w, h))

            clip = ImageSequenceClip(frames, fps=fps)

            # Audio Latar
            if audio_mode == "Upload Musik Piano Sendiri (.mp3/.wav)" and uploaded_audio is not None:
                tmp_aud = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmp_aud.write(uploaded_audio.read())
                tmp_aud.close()
                user_aud_clip = AudioFileClip(tmp_aud.name).subclip(0, clip.duration)
                clip = clip.set_audio(user_aud_clip)
            else:
                with_rain = (audio_mode == "Piano Ambient + Hujan Malam (Otomatis)")
                piano_clip = generate_cinematic_piano_audio(clip.duration, include_rain=with_rain)
                clip = clip.set_audio(piano_clip)

            temp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            mp4_path = temp_mp4.name
            temp_mp4.close()

            clip.write_videofile(
                mp4_path,
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                verbose=False,
                logger=None
            )

            st.success("✅ Video Dark Programmer Cinematic siap!")
            st.video(mp4_path)

            with open(mp4_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Video Status WA (MP4)",
                    data=f,
                    file_name="rest_mode_cinematic.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
