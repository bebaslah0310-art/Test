import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import subprocess
import wave
import re
import gc
import os

st.set_page_config(page_title="WA Status Real Code Generator", page_icon="⚡", layout="centered")

st.title("⚡ WA Status Real Code Generator")
st.markdown("Tulis kalimat biasa → sistem otomatis merangkainya menjadi **struktur kode pemrograman dinamis** (variabel, fungsi, `if/else`, dan eksekusi log) yang unik sesuai isi teks Anda.")

# --- TEMA WARNA KONTRAS TINGGI ---
THEMES = {
    "Midnight Cyan (Hitam Pekat - Biru/Cyan Neon)": {
        "bg": (5, 7, 12), "card": (11, 15, 24), "border": (45, 85, 140),
        "kw": (255, 110, 180), "fn": (90, 200, 255), "var": (130, 240, 255),
        "str": (160, 255, 175), "cmt": (95, 125, 165), "norm": (235, 242, 255)
    },
    "Hacker Matrix (Hitam - Hijau Terminal)": {
        "bg": (0, 5, 2), "card": (5, 14, 7), "border": (0, 185, 65),
        "kw": (0, 255, 120), "fn": (140, 255, 170), "var": (50, 235, 110),
        "str": (215, 255, 220), "cmt": (40, 135, 65), "norm": (180, 250, 195)
    },
    "Cyberpunk Neon (Ungu Gelap - Pink/Kuning)": {
        "bg": (14, 6, 28), "card": (24, 11, 46), "border": (255, 42, 109),
        "kw": (255, 42, 109), "fn": (254, 222, 93), "var": (5, 217, 232),
        "str": (255, 175, 225), "cmt": (150, 95, 190), "norm": (245, 235, 255)
    },
    "Monokai Contrast (Hitam Abu - Oranye/Kuning/Hijau)": {
        "bg": (16, 16, 18), "card": (26, 26, 30), "border": (110, 105, 95),
        "kw": (249, 38, 114), "fn": (166, 226, 46), "var": (102, 217, 239),
        "str": (230, 219, 116), "cmt": (125, 120, 110), "norm": (248, 248, 242)
    }
}

col1, col2, col3 = st.columns(3)
with col1:
    theme_name = st.selectbox("Tema Warna:", list(THEMES.keys()))
with col2:
    lang_mode = st.selectbox("Bahasa Kode:", ["JavaScript / TS", "Python", "C++"])
with col3:
    ending_mode = st.selectbox("Hasil Akhir:", ["Auto-Deteksi", "PAUSED", "SUCCESS", "ERROR"])

th = THEMES[theme_name]

default_words = """Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program."""

user_words = st.text_area(
    "Ganti Kata-Kata di Sini (Nama variabel & logika kode otomatis menyesuaikan isi teks):",
    value=default_words,
    height=175
)

with st.expander("⚙️ Pengaturan Kecepatan & Audio"):
    typing_speed = st.slider("Kecepatan Ketik", 12, 28, 18)
    use_sound = st.checkbox("Suara Ketikan Mechanical + Piano Pelan", value=True)

fps = 20

def extract_slug(text, fallback="state"):
    # Ambil 1-2 kata penting dari kalimat untuk dijadikan nama variabel/fungsi dinamis
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    stop = {"the", "and", "for", "are", "but", "not", "you", "all", "just", "some", "that", "with", "yang", "dan", "ini", "itu", "untuk", "dari"}
    filtered = [w for w in words if w not in stop]
    if not filtered:
        return fallback
    if len(filtered) == 1:
        return filtered[0]
    return f"{filtered[0]}_{filtered[1]}"

def detect_outcome(text, choice):
    if choice != "Auto-Deteksi":
        return choice.lower()
    low = text.lower()
    if any(w in low for w in ["pause", "rest", "break", "world run", "stop", "istirahat", "jeda"]):
        return "paused"
    if any(w in low for w in ["error", "fail", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit"]):
        return "error"
    return "success"

# --- GENERATOR KODE DINAMIS BERBASIS ISI TEKS ---
def build_dynamic_code_tokens(raw_text, lang, outcome):
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    if not lines:
        return [], []

    main_fn = extract_slug(lines[0], "check_reality")
    code_rows = []  # list of list of (token_text, color_key)

    if lang == "JavaScript / TS":
        code_rows.append([("async function", "kw"), (" ", "norm"), (f"{main_fn}", "fn"), ("() {", "norm")])
        for idx, line in enumerate(lines):
            clean = line.replace('"', "'")
            var_name = extract_slug(line, f"step_{idx}")
            low = line.lower()

            if idx == 0:
                code_rows.append([("  const", "kw"), (f" {var_name} ", "var"), ("= ", "norm"), ("false", "kw"), (";", "norm")])
                code_rows.append([("  // ", "cmt"), (clean, "cmt")])
            elif any(w in low for w in ["if", "not", "bukan", "jangan", "stop", "no"]):
                code_rows.append([("  if", "kw"), (" (!", "norm"), (var_name, "var"), (") {", "norm")])
                code_rows.append([("    ", "norm"), ("log", "fn"), (f'("{clean}")', "str"), (";", "norm")])
                code_rows.append([("  }", "norm")])
            elif idx == len(lines) - 1:
                code_rows.append([("  await", "kw"), (" ", "norm"), ("system", "var"), (".", "norm"), ("run", "fn"), (f'("{clean}")', "str"), (";", "norm")])
            else:
                code_rows.append([("  let", "kw"), (f" {var_name} ", "var"), ("= ", "norm"), (f'"{clean}"', "str"), (";", "norm")])

        if outcome == "paused":
            code_rows.append([("  return", "kw"), (" ", "norm"), ('"SESSION_PAUSED"', "str"), (";", "norm")])
        elif outcome == "error":
            code_rows.append([("  throw new", "kw"), (" ", "norm"), ("Error", "fn"), ('("SYSTEM_CRASH")', "str"), (";", "norm")])
        else:
            code_rows.append([("  return", "kw"), (" ", "norm"), ('"SYSTEM_OK"', "str"), (";", "norm")])
        code_rows.append([("}", "norm")])

        exec_logs = [f"$ node {main_fn}.js", f"> Executing {main_fn}()..."]

    elif lang == "Python":
        code_rows.append([("def", "kw"), (" ", "norm"), (f"{main_fn}", "fn"), ("():", "norm")])
        for idx, line in enumerate(lines):
            clean = line.replace('"', "'")
            var_name = extract_slug(line, f"node_{idx}")
            low = line.lower()

            if idx == 0:
                code_rows.append([(f"    {var_name} ", "var"), ("= ", "norm"), ("False", "kw")])
                code_rows.append([("    # ", "cmt"), (clean, "cmt")])
            elif any(w in low for w in ["if", "not", "bukan", "jangan", "stop", "no"]):
                code_rows.append([("    if not", "kw"), (f" {var_name}:", "var")])
                code_rows.append([("        ", "norm"), ("emit", "fn"), (f'("{clean}")', "str")])
            elif idx == len(lines) - 1:
                code_rows.append([("    ", "norm"), ("world", "var"), (".", "norm"), ("execute", "fn"), (f'("{clean}")', "str")])
            else:
                code_rows.append([(f"    {var_name} ", "var"), ("= ", "norm"), (f'"{clean}"', "str")])

        if outcome == "paused":
            code_rows.append([("    return", "kw"), (" ", "norm"), ('"SESSION_PAUSED"', "str")])
        elif outcome == "error":
            code_rows.append([("    raise", "kw"), (" ", "norm"), ("SystemError", "fn"), ('("HALTED")', "str")])
        else:
            code_rows.append([("    return", "kw"), (" ", "norm"), ('"REPAIRED"', "str")])

        exec_logs = [f"$ python3 {main_fn}.py", f"> Running {main_fn}()..."]

    else:  # C++
        code_rows.append([("int", "kw"), (" ", "norm"), (f"{main_fn}", "fn"), ("() {", "norm")])
        for idx, line in enumerate(lines):
            clean = line.replace('"', "'")
            var_name = extract_slug(line, f"ptr_{idx}")
            if idx == 0:
                code_rows.append([("    bool", "kw"), (f" {var_name} ", "var"), ("= ", "norm"), ("false", "kw"), (";", "norm")])
                code_rows.append([("    // ", "cmt"), (clean, "cmt")])
            elif idx == len(lines) - 1:
                code_rows.append([("    ", "norm"), ("kernel_exec", "fn"), (f'("{clean}")', "str"), (";", "norm")])
            else:
                code_rows.append([("    auto", "kw"), (f" {var_name} ", "var"), ("= ", "norm"), (f'"{clean}"', "str"), (";", "norm")])

        if outcome == "paused":
            code_rows.append([("    return", "kw"), (" SESSION_PAUSED;", "var")])
        elif outcome == "error":
            code_rows.append([("    return", "kw"), (" EXIT_FAILURE;", "var")])
        else:
            code_rows.append([("    return", "kw"), (" EXIT_SUCCESS;", "var")])
        code_rows.append([("}", "norm")])

        exec_logs = [f"$ ./{main_fn} --run", "> Linking runtime modules..."]

    return code_rows, exec_logs, main_fn

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

# --- RENDERER FRAME KODE FULL SCREEN BERSIH (540x960) ---
def render_code_frame(
    completed_rows, active_row, active_chars, cursor_on,
    exec_logs, outcome, show_final_status, file_label, th, w=540, h=960
):
    img = Image.new("RGB", (w, h), color=th["bg"])
    draw = ImageDraw.Draw(img)

    # Kartu editor besar di tengah layar tanpa sidebar yang bikin sempit
    mx, my = 22, 75
    ww, wh = w - (mx * 2), h - (my * 2)

    border_col = th["border"]
    if show_final_status:
        if outcome == "error":
            border_col = (255, 65, 75)
        elif outcome == "paused":
            border_col = (255, 195, 45)
        else:
            border_col = (60, 245, 130)

    draw.rectangle([mx, my, mx + ww, my + wh], fill=th["card"], outline=border_col, width=2)

    # Top bar minimalis nama file
    hh = 36
    draw.line([(mx, my + hh), (mx + ww, my + hh)], fill=th["border"], width=1)
    draw.ellipse([mx + 14, my + 12, mx + 24, my + 22], fill=(255, 95, 86))
    draw.ellipse([mx + 30, my + 12, mx + 40, my + 22], fill=(255, 189, 46))
    draw.ellipse([mx + 46, my + 12, mx + 56, my + 22], fill=(39, 201, 63))

    f_hdr = get_font(13, bold=True)
    draw.text((mx + 70, my + 10), file_label, fill=th["cmt"], font=f_hdr)

    f_code = get_font(17)
    f_num = get_font(13)

    gutter_x = mx + 12
    code_x = mx + 44
    max_code_w = ww - 58
    line_h = 25
    max_y = my + wh - 165  # Sisakan area bawah untuk output eksekusi

    def draw_tokens(row_tokens, line_num, y_pos, char_limit=None, draw_cursor=False):
        draw.text((gutter_x, y_pos + 2), f"{line_num:2d}", fill=th["cmt"], font=f_num)
        cx = code_x
        cy = y_pos
        count = 0

        for txt, role in row_tokens:
            if char_limit is not None:
                rem = char_limit - count
                if rem <= 0:
                    break
                piece = txt[:rem]
            else:
                piece = txt

            col = th.get(role, th["norm"])
            for ch in piece:
                cw = draw.textbbox((0, 0), ch, font=f_code)[2]
                if cx + cw > code_x + max_code_w:
                    cx = code_x + 18
                    cy += line_h
                draw.text((cx, cy), ch, fill=col, font=f_code)
                cx += cw
                count += 1

        if draw_cursor and cursor_on:
            draw.rectangle([cx + 1, cy + 2, cx + 10, cy + 19], fill=th["fn"])

        return cy + line_h

    curr_y = my + hh + 18
    ln = 1
    for r_tokens in completed_rows:
        if curr_y > max_y:
            break
        curr_y = draw_tokens(r_tokens, ln, curr_y)
        ln += 1

    if active_row is not None and curr_y <= max_y:
        curr_y = draw_tokens(active_row, ln, curr_y, char_limit=active_chars, draw_cursor=True)

    # --- AREA OUTPUT EKSEKUSI DI BAGIAN BAWAH KARTU ---
    out_top = my + wh - 150
    draw.line([(mx + 14, out_top), (mx + ww - 14, out_top)], fill=th["border"], width=1)

    f_out = get_font(14)
    oy = out_top + 12
    for log_txt in exec_logs:
        draw.text((mx + 18, oy), log_txt, fill=th["cmt"], font=f_out)
        oy += 22

    if show_final_status:
        bx1, bx2 = mx + 16, mx + ww - 16
        by2 = my + wh - 14
        by1 = by2 - 44

        if outcome == "error":
            bg_b, fg_b, status_lbl = (65, 12, 18), (255, 75, 85), "✖ EXIT CODE 1 // SYSTEM ERROR"
        elif outcome == "paused":
            bg_b, fg_b, status_lbl = (55, 42, 8), (255, 200, 50), "⏸ EXIT CODE 0 // SESSION PAUSED"
        else:
            bg_b, fg_b, status_lbl = (10, 55, 25), (60, 255, 120), "✔ EXIT CODE 0 // SYSTEM REPAIRED"

        draw.rectangle([bx1, by1, bx2, by2], fill=bg_b, outline=fg_b, width=2)
        f_st = get_font(15, bold=True)
        bb = draw.textbbox((0, 0), status_lbl, font=f_st)
        tx = bx1 + ((bx2 - bx1) - (bb[2] - bb[0])) // 2
        ty = by1 + ((by2 - by1) - (bb[3] - bb[1])) // 2 - 2
        draw.text((tx, ty), status_lbl, fill=fg_b, font=f_st)

    return img.tobytes()

def build_audio_wav(duration, wav_path, key_frames, fps, enable_sound=True):
    sr = 22050
    total_samples = max(sr, int(duration * sr))
    audio = np.zeros(total_samples, dtype=np.float32)

    if enable_sound:
        rng = np.random.default_rng(42)
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

if st.button("🎬 Generate Video Kode Programmer", type="primary", use_container_width=True):
    if not user_words.strip():
        st.warning("Teks tidak boleh kosong!")
    else:
        if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
            try:
                os.remove(st.session_state["last_mp4"])
            except Exception:
                pass

        outcome = detect_outcome(user_words, ending_mode)
        code_rows, exec_logs, fn_name = build_dynamic_code_tokens(user_words, lang_mode, outcome)
        ext = "js" if lang_mode == "JavaScript / TS" else ("py" if lang_mode == "Python" else "cpp")
        file_label = f"{fn_name}.{ext}"

        with st.spinner("Menyusun logika kode & merender video..."):
            w, h = 540, 960
            f_per_char = max(1, round(fps / typing_speed))

            key_frames = []
            sim_f = int(fps * 0.25)
            for idx, r_tokens in enumerate(code_rows):
                full_s = "".join(t[0] for t in r_tokens)
                if idx == 0:
                    sim_f += int(fps * 0.25)
                else:
                    for ci in range(1, len(full_s) + 1):
                        if full_s[ci - 1] != " ":
                            key_frames.append(sim_f)
                        sim_f += f_per_char
                    sim_f += int(fps * 0.15)

            run_frames = len(exec_logs) * int(fps * 0.35) + int(fps * 1.1)
            total_frames = sim_f + run_frames
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
                    proc.stdin.write(render_code_frame(completed, [], 0, (f // 4) % 2 == 0, [], outcome, False, file_label, th, w, h))

                for idx, r_tokens in enumerate(code_rows):
                    full_s = "".join(t[0] for t in r_tokens)
                    if idx == 0:
                        completed.append(r_tokens)
                        for _ in range(int(fps * 0.25)):
                            proc.stdin.write(render_code_frame(completed, None, 0, False, [], outcome, False, file_label, th, w, h))
                    else:
                        for ci in range(1, len(full_s) + 1):
                            for _ in range(f_per_char):
                                proc.stdin.write(render_code_frame(completed, r_tokens, ci, True, [], outcome, False, file_label, th, w, h))
                        completed.append(r_tokens)
                        for _ in range(int(fps * 0.15)):
                            proc.stdin.write(render_code_frame(completed, None, 0, False, [], outcome, False, file_label, th, w, h))

                shown_logs = []
                for l_idx, l_txt in enumerate(exec_logs):
                    shown_logs.append(l_txt)
                    is_last = (l_idx == len(exec_logs) - 1)
                    hold = int(fps * 1.1) if is_last else int(fps * 0.35)
                    for _ in range(hold):
                        proc.stdin.write(render_code_frame(completed, None, 0, False, shown_logs, outcome, is_last, file_label, th, w, h))

                proc.stdin.close()
                proc.wait()
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                gc.collect()

            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                st.session_state["last_mp4"] = mp4_path
                st.session_state["last_file"] = file_label
                st.session_state["last_outcome"] = outcome

if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
    st.success(f"✅ Video kode **{st.session_state['last_file']}** siap!")
    st.video(st.session_state["last_mp4"])
    with open(st.session_state["last_mp4"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video MP4",
            data=f.read(),
            file_name=f"code_{st.session_state['last_file']}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
