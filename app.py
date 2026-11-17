import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import subprocess
import wave
import gc
import os

st.set_page_config(page_title="WA Status CMD Coder", page_icon="💻", layout="centered")

st.title("💻 WA Status CMD Programmer")
st.markdown("Tampilan bersih, tulisan besar jelas terbaca di HP, dan muncul seperti ketikan CMD programmer.")

# --- PILIHAN TEMA KONTRAS TINGGI ---
THEMES = {
    "Hacker Hijau (Hitam Pekat - Hijau Neon)": {
        "bg": (0, 0, 0), "win": (8, 14, 8), "border": (0, 200, 60),
        "cmd": (0, 255, 75), "text": (220, 255, 225), "muted": (0, 140, 45)
    },
    "Dark Midnight (Hitam - Biru Es Dingin)": {
        "bg": (4, 6, 10), "win": (10, 15, 24), "border": (70, 140, 220),
        "cmd": (95, 185, 255), "text": (235, 245, 255), "muted": (75, 110, 150)
    },
    "CMD Klasik (Hitam - Putih Bersih)": {
        "bg": (0, 0, 0), "win": (14, 14, 14), "border": (130, 130, 130),
        "cmd": (255, 255, 255), "text": (235, 235, 235), "muted": (120, 120, 120)
    },
    "Cyberpunk (Ungu Gelap - Pink/Cyan)": {
        "bg": (14, 5, 26), "win": (24, 10, 44), "border": (255, 42, 109),
        "cmd": (255, 65, 130), "text": (110, 245, 255), "muted": (160, 70, 140)
    },
    "Amber Retro (Hitam - Emas Hangat)": {
        "bg": (8, 5, 0), "win": (18, 12, 2), "border": (220, 145, 20),
        "cmd": (255, 185, 35), "text": (255, 225, 140), "muted": (150, 95, 15)
    }
}

col_a, col_b = st.columns(2)
with col_a:
    theme_name = st.selectbox("Pilih Warna Tema:", list(THEMES.keys()))
with col_b:
    ending_mode = st.selectbox(
        "Status Akhir (Ending):",
        [
            "Auto-Deteksi dari Kata",
            "SESSION PAUSED (Kuning)",
            "SUCCESS / REPAIRED (Hijau)",
            "SYSTEM ERROR (Merah)"
        ]
    )

th = THEMES[theme_name]

default_words = """Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program."""

user_words = st.text_area(
    "Ganti Kata-Kata di Sini (Tiap baris diketik berurutan):",
    value=default_words,
    height=180
)

with st.expander("⚙️ Pengaturan Tambahan (Kecepatan & Suara)"):
    typing_speed = st.slider("Kecepatan Ketik", 10, 26, 16)
    font_size = st.slider("Ukuran Huruf", 18, 28, 22)
    use_sound = st.checkbox("Suara Ketikan Keyboard + Piano Pelan", value=True)

fps = 20

def detect_outcome(text, choice):
    if choice.startswith("SESSION PAUSED"):
        return "paused"
    if choice.startswith("SUCCESS"):
        return "success"
    if choice.startswith("SYSTEM ERROR"):
        return "error"

    low = text.lower()
    if any(w in low for w in ["pause", "rest", "break", "world run", "stop", "istirahat", "jeda"]):
        return "paused"
    if any(w in low for w in ["error", "fail", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit"]):
        return "error"
    return "success"

@st.cache_resource
def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap_line(text, font, max_w, draw):
    words = text.split(" ")
    res, cur = [], ""
    for w in words:
        test = cur + (" " if cur else "") + w
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                res.append(cur)
            cur = w
    if cur:
        res.append(cur)
    return res

# --- RENDER FRAME CMD BERSIH & JELAS (540x960) ---
def render_cmd_frame(completed_lines, active_text, cursor_on, outcome, show_end_badge, th, f_size, w=540, h=960):
    img = Image.new("RGB", (w, h), color=th["bg"])
    draw = ImageDraw.Draw(img)

    # Kotak CMD besar & lega di tengah layar HP
    mx, my = 26, 120
    ww, wh = w - (mx * 2), h - (my * 2)

    border_col = th["border"]
    if show_end_badge:
        if outcome == "error":
            border_col = (255, 65, 75)
        elif outcome == "paused":
            border_col = (255, 195, 45)
        else:
            border_col = (50, 240, 110)

    draw.rectangle([mx, my, mx + ww, my + wh], fill=th["win"], outline=border_col, width=2)

    # Header bar sederhana ala CMD
    hh = 36
    draw.line([(mx, my + hh), (mx + ww, my + hh)], fill=th["muted"], width=1)
    draw.ellipse([mx + 14, my + 12, mx + 24, my + 22], fill=(255, 95, 86))
    draw.ellipse([mx + 30, my + 12, mx + 40, my + 22], fill=(255, 189, 46))
    draw.ellipse([mx + 46, my + 12, mx + 56, my + 22], fill=(39, 201, 63))

    f_hdr = get_font(12)
    draw.text((mx + 70, my + 11), "C:\\SYSTEM\\mindset.exe", fill=th["muted"], font=f_hdr)

    f_body = get_font(f_size)
    max_tw = ww - 40
    line_h = int(f_size * 1.42)
    curr_y = my + hh + 24

    # Render baris yang sudah selesai diketik
    for item_text, is_sys in completed_lines:
        col = th["cmd"] if is_sys else th["text"]
        for wl in wrap_line(item_text, f_body, max_tw, draw):
            if curr_y < my + wh - 90:
                draw.text((mx + 20, curr_y), wl, fill=col, font=f_body)
                curr_y += line_h
        curr_y += 6

    # Render baris yang sedang diketik
    if active_text is not None:
        disp = active_text + ("█" if cursor_on else " ")
        for wl in wrap_line(disp, f_body, max_tw, draw):
            if curr_y < my + wh - 90:
                draw.text((mx + 20, curr_y), wl, fill=th["text"], font=f_body)
                curr_y += line_h

    # Kotak Status Akhir di bagian bawah window
    if show_end_badge:
        bx1, bx2 = mx + 18, mx + ww - 18
        by2 = my + wh - 18
        by1 = by2 - 46

        if outcome == "error":
            bg_b, fg_b, lbl = (65, 12, 18), (255, 75, 85), "[!] SYSTEM ERROR // HALTED"
        elif outcome == "paused":
            bg_b, fg_b, lbl = (55, 42, 8), (255, 200, 50), "[||] SESSION PAUSED..."
        else:
            bg_b, fg_b, lbl = (10, 55, 25), (60, 255, 120), "[OK] SYSTEM REPAIRED"

        draw.rectangle([bx1, by1, bx2, by2], fill=bg_b, outline=fg_b, width=2)
        f_badge = get_font(16, bold=True)
        bb = draw.textbbox((0, 0), lbl, font=f_badge)
        tx = bx1 + ((bx2 - bx1) - (bb[2] - bb[0])) // 2
        ty = by1 + ((by2 - by1) - (bb[3] - bb[1])) // 2 - 2
        draw.text((tx, ty), lbl, fill=fg_b, font=f_badge)

    return img.tobytes()

def build_audio_wav(duration, wav_path, key_frames, fps, enable_sound=True):
    sr = 22050
    total_samples = max(sr, int(duration * sr))
    audio = np.zeros(total_samples, dtype=np.float32)

    if enable_sound:
        rng = np.random.default_rng(42)
        # Piano ambient lembut
        notes = [
            (0.0, 220.00, 2.8), (1.1, 329.63, 2.5), (2.2, 493.88, 2.8),
            (3.5, 174.61, 3.0), (4.6, 261.63, 2.6), (5.8, 440.00, 3.0),
            (7.2, 130.81, 3.2), (8.4, 392.00, 2.8), (9.8, 220.00, 3.5)
        ]
        for st_t, freq, dur in notes:
            if st_t >= duration:
                break
            s_i = int(st_t * sr)
            e_i = min(total_samples, int((st_t + dur) * sr))
            if e_i <= s_i:
                continue
            lt = np.linspace(0, (e_i - s_i) / sr, e_i - s_i, dtype=np.float32)
            env = np.minimum(1.0, lt / 0.04) * np.exp(-lt * 1.15)
            tone = np.sin(2 * np.pi * freq * lt) * 0.65 + np.sin(2 * np.pi * freq * 2 * lt) * 0.2 * np.exp(-lt * 1.8)
            audio[s_i:e_i] += tone * env * 0.25

        # Suara ketikan sinkron
        k_len = int(0.020 * sr)
        tk = np.linspace(0, 0.020, k_len, dtype=np.float32)
        key_snd = (rng.normal(0, 1, k_len).astype(np.float32) * np.exp(-tk * 230) * 0.35) + (
            np.sin(2 * np.pi * 220 * tk) * np.exp(-tk * 190) * 0.25
        )
        for kf in key_frames:
            s_i = int((kf / fps) * sr)
            e_i = min(total_samples, s_i + k_len)
            if s_i < total_samples:
                audio[s_i:e_i] += key_snd[:e_i - s_i]

        fade_out = min(total_samples, int(0.5 * sr))
        audio[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)

        max_v = np.max(np.abs(audio))
        if max_v > 0:
            audio = (audio / max_v) * 0.82

    pcm16 = np.int16(np.clip(audio, -1.0, 1.0) * 32767)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())

if st.button("🎬 Generate Video CMD Status WA", type="primary", use_container_width=True):
    raw_lines = [l.strip() for l in user_words.strip().split("\n") if l.strip()]
    if not raw_lines:
        st.warning("Teks tidak boleh kosong!")
    else:
        if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
            try:
                os.remove(st.session_state["last_mp4"])
            except Exception:
                pass

        outcome = detect_outcome(user_words, ending_mode)
        # Bungkus otomatis dengan perintah CMD awal + kalimat Anda
        script_items = [("C:\\> run mindset.sh --init", True)] + [(f"> {l}", False) for l in raw_lines]

        with st.spinner("Membuat video CMD..."):
            w, h = 540, 960
            f_per_char = max(1, round(fps / typing_speed))

            key_frames = []
            sim_f = int(fps * 0.25)
            for idx, (txt, is_sys) in enumerate(script_items):
                if is_sys:
                    sim_f += int(fps * 0.3)
                else:
                    for ci in range(1, len(txt) + 1):
                        if txt[ci - 1] != " ":
                            key_frames.append(sim_f)
                        sim_f += f_per_char
                    sim_f += int(fps * 0.2)

            end_frames = int(fps * 1.1)
            total_frames = sim_f + end_frames
            total_dur = max(1.0, total_frames / fps)

            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wav_path = wav_tmp.name
            wav_tmp.close()
            build_audio_wav(total_dur, wav_path, key_frames, fps, enable_sound=use_sound)

            mp4_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            mp4_path = mp4_tmp.name
            mp4_tmp.close()

            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps),
                "-i", "-", "-i", wav_path,
                "-threads", "1", "-c:v", "libx264", "-preset", "ultrafast",
                "-crf", "23", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest", mp4_path
            ]

            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                completed = []
                for f in range(int(fps * 0.25)):
                    proc.stdin.write(render_cmd_frame(completed, "> ", (f // 4) % 2 == 0, outcome, False, th, font_size, w, h))

                for txt, is_sys in script_items:
                    if is_sys:
                        completed.append((txt, True))
                        for _ in range(int(fps * 0.3)):
                            proc.stdin.write(render_cmd_frame(completed, None, False, outcome, False, th, font_size, w, h))
                    else:
                        for ci in range(1, len(txt) + 1):
                            for _ in range(f_per_char):
                                proc.stdin.write(render_cmd_frame(completed, txt[:ci], True, outcome, False, th, font_size, w, h))
                        completed.append((txt, False))
                        for _ in range(int(fps * 0.2)):
                            proc.stdin.write(render_cmd_frame(completed, None, False, outcome, False, th, font_size, w, h))

                # Ending langsung muncul & selesai dalam 1.1 detik
                for _ in range(end_frames):
                    proc.stdin.write(render_cmd_frame(completed, None, False, outcome, True, th, font_size, w, h))

                proc.stdin.close()
                proc.wait()
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                gc.collect()

            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                st.session_state["last_mp4"] = mp4_path
                st.session_state["last_outcome"] = outcome

if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
    st.success("✅ Video selesai dibuat!")
    st.video(st.session_state["last_mp4"])
    with open(st.session_state["last_mp4"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video MP4",
            data=f.read(),
            file_name=f"status_wa_cmd_{st.session_state['last_outcome']}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
