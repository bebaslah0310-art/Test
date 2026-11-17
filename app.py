import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import tempfile
import subprocess
import wave
import gc
import os

st.set_page_config(page_title="Authentic Programmer IDE - WA Status", page_icon="👨‍💻", layout="centered")

st.title("👨‍💻 Authentic Dark Programmer Video Generator")
st.markdown("Tulis kalimat biasa → sistem menyusunnya menjadi **struktur koding IDE asli** lengkap dengan *syntax highlighting* dan eksekusi terminal di bagian bawah.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("🖥️ Tampilan IDE & Warna")

ide_theme = st.sidebar.selectbox(
    "Tema IDE Developer",
    [
        "VS Code Dark+ (Klasik Biru/Kuning/Hijau)",
        "Tokyo Night Storm (Ungu/Cyan/Biru Malam)",
        "Dracula Official (Pink/Ungu/Hijau Neon)",
        "GitHub Dark Dimmed (Abu Gelap/Oranye/Biru)"
    ]
)

THEMES = {
    "VS Code Dark+ (Klasik Biru/Kuning/Hijau)": {
        "bg": (20, 20, 20), "sidebar": (28, 28, 28), "tab": (37, 37, 38),
        "border": (55, 55, 58), "status_bar": (0, 122, 204), "status_txt": (255, 255, 255),
        "kw": (86, 156, 214), "ctrl": (197, 134, 192), "func": (220, 220, 170),
        "str": (206, 145, 120), "var": (156, 220, 254), "cmt": (106, 153, 85),
        "norm": (212, 212, 212), "term_ok": (78, 201, 176), "term_err": (244, 71, 71)
    },
    "Tokyo Night Storm (Ungu/Cyan/Biru Malam)": {
        "bg": (22, 24, 33), "sidebar": (18, 20, 28), "tab": (31, 35, 53),
        "border": (48, 55, 82), "status_bar": (61, 89, 161), "status_txt": (220, 230, 255),
        "kw": (187, 154, 247), "ctrl": (247, 118, 142), "func": (122, 162, 247),
        "str": (158, 206, 106), "var": (125, 207, 255), "cmt": (86, 95, 137),
        "norm": (192, 202, 245), "term_ok": (115, 218, 202), "term_err": (247, 118, 142)
    },
    "Dracula Official (Pink/Ungu/Hijau Neon)": {
        "bg": (30, 31, 41), "sidebar": (25, 26, 33), "tab": (40, 42, 54),
        "border": (68, 71, 90), "status_bar": (98, 114, 164), "status_txt": (248, 248, 242),
        "kw": (255, 121, 198), "ctrl": (189, 147, 249), "func": (80, 250, 123),
        "str": (241, 250, 140), "var": (139, 233, 253), "cmt": (98, 114, 164),
        "norm": (248, 248, 242), "term_ok": (80, 250, 123), "term_err": (255, 85, 85)
    },
    "GitHub Dark Dimmed (Abu Gelap/Oranye/Biru)": {
        "bg": (24, 28, 34), "sidebar": (19, 23, 28), "tab": (34, 39, 46),
        "border": (55, 62, 71), "status_bar": (49, 109, 202), "status_txt": (240, 246, 252),
        "kw": (244, 112, 103), "ctrl": (220, 168, 255), "func": (108, 182, 255),
        "str": (150, 208, 255), "var": (246, 157, 80), "cmt": (118, 131, 144),
        "norm": (173, 186, 199), "term_ok": (87, 171, 90), "term_err": (229, 83, 75)
    }
}
th = THEMES[ide_theme]

typing_speed = st.sidebar.slider("Kecepatan Ngoding (Karakter/Detik)", min_value=14, max_value=32, value=22)
end_duration = st.sidebar.slider("Durasi Tahan Akhir (Detik)", min_value=0.8, max_value=2.0, value=1.2, step=0.1)
audio_mode = st.sidebar.selectbox(
    "Audio Latar",
    [
        "Suara Ketik Mechanical + Piano Malam",
        "Hanya Piano Ambient Tenang",
        "Hanya Suara Ketikan Keyboard",
        "Tanpa Suara"
    ]
)

fps = 20

# --- INPUT UTAMA ---
default_words = """Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program."""

st.subheader("1. Tulis Kata-Kata Anda (Otomatis Jadi Logika Kode)")
user_words = st.text_area(
    "Masukkan kalimat biasa:",
    value=default_words,
    height=175
)

col1, col2 = st.columns(2)
with col1:
    lang_choice = st.selectbox(
        "2. Bahasa Pemrograman:",
        [
            "TypeScript (mindset.ts)",
            "Python (reality.py)",
            "C++ (kernel.cpp)"
        ]
    )
with col2:
    ending_mode = st.selectbox(
        "3. Hasil Eksekusi Terminal:",
        [
            "Auto-Deteksi dari Kata-Kata",
            "SESSION PAUSED (Standby)",
            "BUILD SUCCESS (Exit 0)",
            "RUNTIME ERROR (Exit 1)"
        ]
    )

def detect_outcome(text, choice):
    if choice.startswith("SESSION PAUSED"):
        return "paused"
    if choice.startswith("BUILD SUCCESS"):
        return "success"
    if choice.startswith("RUNTIME ERROR"):
        return "error"

    low = text.lower()
    if any(w in low for w in ["pause", "rest", "break", "world run", "stop trying", "istirahat", "jeda"]):
        return "paused"
    if any(w in low for w in ["error", "fail", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit"]):
        return "error"
    return "success"

# --- KONVERSI KALIMAT KE TOKEN KODE ASLI (SYNTAX HIGHLIGHTING PER KATA) ---
# Setiap baris berupa list of tuple: [(teks_token, tipe_warna), ...]
def build_structured_code(raw_text, lang, outcome):
    lines = [l.strip() for l in raw_text.strip().split('\n') if l.strip()]
    if not lines:
        return [], []

    code_lines = []
    term_logs = []

    if lang.startswith("TypeScript"):
        code_lines.append([("import", "ctrl"), (" { ", "norm"), ("Reality", "var"), (", ", "norm"), ("Mind", "var"), (" } ", "norm"), ("from", "ctrl"), (" '@core/life'", "str"), (";", "norm")])
        code_lines.append([("", "norm")])
        code_lines.append([("async function", "kw"), (" ", "norm"), ("processState", "func"), ("() {", "norm")])
        code_lines.append([("  // Analyzing current reality...", "cmt")])

        for i, txt in enumerate(lines):
            s = txt.replace('"', "'")
            if i == 0:
                code_lines.append([("  const", "kw"), (" isReal ", "var"), ("= ", "norm"), ("false", "kw"), ("; ", "norm"), (f"// {s}", "cmt")])
            elif i == 1:
                code_lines.append([("  if", "ctrl"), (" (!isReal) ", "norm"), ("throw", "ctrl"), (f' "{s}"', "str"), (";", "norm")])
            elif i == len(lines) - 1:
                code_lines.append([("  await", "ctrl"), (" ", "norm"), ("World", "var"), (".", "norm"), ("runOwnProgram", "func"), (f'("{s}")', "str"), (";", "norm")])
            elif "break" in txt.lower() or "stop" in txt.lower():
                code_lines.append([("  ", "norm"), ("Mind", "var"), (".", "norm"), ("takeBreak", "func"), (f'("{s}")', "str"), (";", "norm")])
            else:
                code_lines.append([("  let", "kw"), (f" illusion_{i} ", "var"), ("= ", "norm"), (f'"{s}"', "str"), (";", "norm")])

        if outcome == "paused":
            code_lines.append([("  return", "ctrl"), (" ", "norm"), ("Status", "var"), (".", "norm"), ("SESSION_PAUSED", "func"), (";", "norm")])
        elif outcome == "error":
            code_lines.append([("  return", "ctrl"), (" ", "norm"), ("Status", "var"), (".", "norm"), ("FATAL_CRASH", "term_err"), (";", "norm")])
        else:
            code_lines.append([("  return", "ctrl"), (" ", "norm"), ("Status", "var"), (".", "norm"), ("SYSTEM_REPAIRED", "term_ok"), (";", "norm")])
        code_lines.append([("}", "norm")])

        term_logs.append(("$ ts-node src/mindset.ts", "norm"))
        term_logs.append(("[INFO] Compiling 1 module...", "cmt"))
        if outcome == "paused":
            term_logs.append(("[WARN] SESSION PAUSED... (Rest Mode Active)", "var"))
        elif outcome == "error":
            term_logs.append(("[ERR!] UnhandledException: Process Halted (Exit 1)", "term_err"))
        else:
            term_logs.append(("[DONE] SYSTEM REPAIRED // Exit Code 0", "term_ok"))

    elif lang.startswith("Python"):
        code_lines.append([("import", "ctrl"), (" sys, time", "norm")])
        code_lines.append([("from", "ctrl"), (" core ", "norm"), ("import", "ctrl"), (" Reality, Mind", "var")])
        code_lines.append([("", "norm")])
        code_lines.append([("def", "kw"), (" ", "norm"), ("sync_mindset", "func"), ("() -> ", "norm"), ("None", "kw"), (":", "norm")])
        code_lines.append([("    # Analyzing reality...", "cmt")])

        for i, txt in enumerate(lines):
            s = txt.replace('"', "'")
            if i == 0:
                code_lines.append([("    reality ", "var"), ("= ", "norm"), ("False", "kw"), (f"  # {s}", "cmt")])
            elif i == 1:
                code_lines.append([("    if not", "ctrl"), (" reality: ", "norm"), ("print", "func"), (f'("{s}")', "str")])
            elif i == len(lines) - 1:
                code_lines.append([("    Mind", "var"), (".", "norm"), ("let_world_run", "func"), (f'("{s}")', "str")])
            else:
                code_lines.append([("    msg_", "var"), (f"{i} ", "var"), ("= ", "norm"), (f'"{s}"', "str")])

        if outcome == "paused":
            code_lines.append([("    sys", "var"), (".", "norm"), ("exit", "func"), ('("SESSION PAUSED...")', "str")])
        elif outcome == "error":
            code_lines.append([("    raise", "ctrl"), (" ", "norm"), ("RuntimeError", "term_err"), ('("SYSTEM_ERROR")', "str")])
        else:
            code_lines.append([("    return", "ctrl"), (" ", "norm"), ('"SYSTEM REPAIRED"', "term_ok")])

        term_logs.append(("$ python3 reality.py", "norm"))
        term_logs.append(("[SYS] Executing sync_mindset()...", "cmt"))
        if outcome == "paused":
            term_logs.append(("[STATE] SESSION PAUSED... (Standby)", "var"))
        elif outcome == "error":
            term_logs.append(("[FATAL] Traceback: Process aborted (Code 1)", "term_err"))
        else:
            term_logs.append(("[OK] Execution finished cleanly (Code 0)", "term_ok"))

    else:  # C++
        code_lines.append([("#include", "ctrl"), (" <iostream>", "str")])
        code_lines.append([("#include", "ctrl"), (" <reality.hpp>", "str")])
        code_lines.append([("", "norm")])
        code_lines.append([("int", "kw"), (" ", "norm"), ("main", "func"), ("() {", "norm")])
        code_lines.append([("    // REST MODE ACTIVATED", "cmt")])
        for i, txt in enumerate(lines):
            s = txt.replace('"', "'")
            if i == 0:
                code_lines.append([("    bool", "kw"), (" is_real ", "var"), ("= ", "norm"), ("false", "kw"), (f"; // {s}", "cmt")])
            else:
                code_lines.append([("    std::cout << ", "norm"), (f'"{s}"', "str"), (" << std::endl;", "norm")])
        if outcome == "paused":
            code_lines.append([("    System::", "var"), ("pauseSession", "func"), ("();", "norm")])
        elif outcome == "error":
            code_lines.append([("    return", "ctrl"), (" EXIT_FAILURE;", "term_err")])
        else:
            code_lines.append([("    return", "ctrl"), (" EXIT_SUCCESS;", "term_ok")])
        code_lines.append([("}", "norm")])

        term_logs.append(("$ g++ kernel.cpp -o core && ./core", "norm"))
        if outcome == "paused":
            term_logs.append(("[HALT] SESSION PAUSED... Waiting interrupt.", "var"))
        elif outcome == "error":
            term_logs.append(("[SEGFAULT] Core dumped (Exit 139)", "term_err"))
        else:
            term_logs.append(("[SUCCESS] Binary exited with code 0.", "term_ok"))

    return code_lines, term_logs

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

# --- RENDERER FRAME IDE AUTHENTIC (540x960) ---
def render_ide_frame(
    completed_lines, active_tokens, active_char_count, cursor_on,
    terminal_lines, file_name, lang_label, th, w=540, h=960
):
    img = Image.new("RGB", (w, h), color=th["bg"])
    draw = ImageDraw.Draw(img)

    # 1. Top Window Bar (macOS / Linux IDE Header)
    top_h = 34
    draw.rectangle([0, 0, w, top_h], fill=th["sidebar"])
    draw.ellipse([12, 11, 22, 21], fill=(255, 95, 86))
    draw.ellipse([28, 11, 38, 21], fill=(255, 189, 46))
    draw.ellipse([44, 11, 54, 21], fill=(39, 201, 63))

    f_ui = get_font(11)
    f_tab = get_font(12, bold=True)
    f_code = get_font(14)
    f_num = get_font(12)

    title_str = f"dark-workspace — {file_name}"
    tbbox = draw.textbbox((0, 0), title_str, font=f_ui)
    draw.text(((w - (tbbox[2] - tbbox[0])) // 2, 10), title_str, fill=th["cmt"], font=f_ui)

    # 2. Activity Bar (Kiri) + File Explorer Sidebar
    act_w = 34
    side_w = 112
    term_h = 195
    status_h = 24
    editor_top = top_h + 28
    editor_bottom = h - term_h - status_h

    draw.rectangle([0, top_h, act_w, h - status_h], fill=th["sidebar"])
    draw.line([(act_w, top_h), (act_w, h - status_h)], fill=th["border"], width=1)

    # Ikon minimal di Activity Bar
    draw.rectangle([9, top_h + 14, 24, top_h + 30], outline=th["norm"], width=1)
    draw.ellipse([10, top_h + 46, 23, top_h + 59], outline=th["cmt"], width=1)
    draw.line([(10, top_h + 78), (24, top_h + 78)], fill=th["cmt"], width=2)
    draw.line([(10, top_h + 84), (20, top_h + 84)], fill=th["cmt"], width=2)

    # Sidebar File Tree
    draw.rectangle([act_w + 1, top_h, act_w + side_w, h - status_h], fill=th["sidebar"])
    draw.line([(act_w + side_w, top_h), (act_w + side_w, h - status_h)], fill=th["border"], width=1)

    draw.text((act_w + 10, top_h + 10), "EXPLORER", fill=th["cmt"], font=f_ui)
    draw.text((act_w + 10, top_h + 32), "▾ DARK-CORE", fill=th["norm"], font=f_ui)
    draw.text((act_w + 16, top_h + 52), "▾ src", fill=th["cmt"], font=f_ui)
    # Highlight file aktif
    draw.rectangle([act_w + 1, top_h + 68, act_w + side_w - 1, top_h + 88], fill=th["tab"])
    draw.text((act_w + 22, top_h + 72), f"• {file_name}", fill=th["var"], font=f_ui)
    draw.text((act_w + 22, top_h + 94), "  config.json", fill=th["cmt"], font=f_ui)
    draw.text((act_w + 16, top_h + 114), "  .gitignore", fill=th["cmt"], font=f_ui)

    # 3. Editor Tab Bar
    ed_left = act_w + side_w + 1
    draw.rectangle([ed_left, top_h, w, editor_top], fill=th["sidebar"])
    draw.rectangle([ed_left, top_h, ed_left + 135, editor_top], fill=th["bg"])
    draw.line([(ed_left, top_h), (ed_left + 135, top_h)], fill=th["status_bar"], width=2)
    draw.text((ed_left + 12, top_h + 7), f"{file_name}  ×", fill=th["norm"], font=f_tab)

    # Breadcrumb path
    draw.text((ed_left + 12, editor_top + 6), f"src > {file_name} > processState()", fill=th["cmt"], font=f_ui)

    # 4. Area Koding (Syntax Highlighting Token-by-Token + Word Wrap)
    code_start_y = editor_top + 28
    gutter_x = ed_left + 8
    text_start_x = ed_left + 36
    max_code_w = w - text_start_x - 10
    line_h = 22

    def draw_token_line(line_tokens, line_num, start_y, max_chars=None, show_cur=False):
        draw.text((gutter_x, start_y + 1), f"{line_num:2d}", fill=th["cmt"], font=f_num)
        cur_x = text_start_x
        cur_y = start_y
        chars_drawn = 0

        for tok_txt, tok_role in line_tokens:
            if max_chars is not None:
                rem = max_chars - chars_drawn
                if rem <= 0:
                    break
                piece = tok_txt[:rem]
            else:
                piece = tok_txt

            col = th.get(tok_role, th["norm"])

            # Render per karakter agar wrap presisi di area editor sempit
            for ch in piece:
                ch_w = draw.textbbox((0, 0), ch, font=f_code)[2]
                if cur_x + ch_w > text_start_x + max_code_w:
                    cur_x = text_start_x + 14  # indentasi wrap
                    cur_y += line_h
                draw.text((cur_x, cur_y), ch, fill=col, font=f_code)
                cur_x += ch_w
                chars_drawn += 1

        if show_cur and cursor_on:
            draw.rectangle([cur_x + 1, cur_y + 2, cur_x + 8, cur_y + 16], fill=th["var"])

        return cur_y + line_h

    cy = code_start_y
    ln = 1
    for t_line in completed_lines:
        if cy > editor_bottom - 20:
            break
        cy = draw_token_line(t_line, ln, cy)
        ln += 1

    if active_tokens is not None and cy <= editor_bottom - 20:
        cy = draw_token_line(active_tokens, ln, cy, max_chars=active_char_count, show_cur=True)

    # 5. Panel Terminal Bawah (Split Screen)
    term_top = editor_bottom
    draw.rectangle([ed_left, term_top, w, h - status_h], fill=th["sidebar"])
    draw.line([(ed_left, term_top), (w, term_top)], fill=th["border"], width=1)

    draw.text((ed_left + 12, term_top + 7), "PROBLEMS   OUTPUT   TERMINAL", fill=th["norm"], font=f_ui)
    draw.line([(ed_left + 132, term_top + 22), (ed_left + 188, term_top + 22)], fill=th["status_bar"], width=2)

    ty = term_top + 32
    for t_txt, t_role in terminal_lines:
        t_col = th.get(t_role, th["norm"])
        # Wrap sederhana jika log terminal panjang
        words = t_txt.split(" ")
        cur_l = ""
        for wd in words:
            test = cur_l + (" " if cur_l else "") + wd
            if draw.textbbox((0, 0), test, font=f_ui)[2] <= (w - ed_left - 24):
                cur_l = test
            else:
                draw.text((ed_left + 12, ty), cur_l, fill=t_col, font=f_ui)
                ty += 18
                cur_l = wd
        if cur_l:
            draw.text((ed_left + 12, ty), cur_l, fill=t_col, font=f_ui)
            ty += 20

    # 6. Status Bar Bawah IDE
    sb_top = h - status_h
    draw.rectangle([0, sb_top, w, h], fill=th["status_bar"])
    draw.text((10, sb_top + 5), f"⎇ main*   0 errors, 0 warnings", fill=th["status_txt"], font=f_ui)
    right_info = f"Ln {ln}, Col {active_char_count + 1}   UTF-8   {lang_label}"
    rb = draw.textbbox((0, 0), right_info, font=f_ui)
    draw.text((w - (rb[2] - rb[0]) - 10, sb_top + 5), right_info, fill=th["status_txt"], font=f_ui)

    return img.tobytes()

# --- GENERATOR AUDIO: SUARA KETIK MECHANICAL + PIANO MALAM ---
def generate_ide_audio_wav(duration, wav_path, key_frames, fps, use_keys=True, use_piano=True):
    sample_rate = 22050
    total_samples = max(sample_rate, int(duration * sample_rate))
    audio = np.zeros(total_samples, dtype=np.float32)
    rng = np.random.default_rng(42)

    if use_piano:
        notes = [
            (0.0, 220.00, 2.8), (1.0, 329.63, 2.5), (2.0, 493.88, 2.8),
            (3.2, 174.61, 3.0), (4.2, 261.63, 2.6), (5.2, 440.00, 3.0),
            (6.5, 130.81, 3.2), (7.5, 392.00, 2.8), (8.8, 196.00, 3.2),
            (10.0, 220.00, 3.8)
        ]
        for st_t, freq, dur in notes:
            if st_t >= duration:
                break
            s_idx = int(st_t * sample_rate)
            e_idx = min(total_samples, int((st_t + dur) * sample_rate))
            if e_idx <= s_idx:
                continue
            lt = np.linspace(0, (e_idx - s_idx) / sample_rate, e_idx - s_idx, dtype=np.float32)
            env = np.minimum(1.0, lt / 0.04) * np.exp(-lt * 1.15)
            tone = np.sin(2 * np.pi * freq * lt) * 0.65 + np.sin(2 * np.pi * freq * 2 * lt) * 0.2 * np.exp(-lt * 1.8)
            audio[s_idx:e_idx] += tone * env * 0.28

    if use_keys and key_frames:
        k_len = int(0.020 * sample_rate)
        tk = np.linspace(0, 0.020, k_len, dtype=np.float32)
        key_snd = (rng.normal(0, 1, k_len).astype(np.float32) * np.exp(-tk * 230) * 0.35) + (
            np.sin(2 * np.pi * 220 * tk) * np.exp(-tk * 190) * 0.25
        )
        for kf in key_frames:
            s_idx = int((kf / fps) * sample_rate)
            e_idx = min(total_samples, s_idx + k_len)
            if s_idx < total_samples:
                audio[s_idx:e_idx] += key_snd[:e_idx - s_idx]

    fade_out = min(total_samples, int(0.6 * sample_rate))
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

# --- TOMBOL GENERATE ---
if st.button("🎬 Generate Video Coding IDE", type="primary", use_container_width=True):
    if not user_words.strip():
        st.warning("Tulis minimal 1 baris kata-kata terlebih dahulu!")
    else:
        if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
            try:
                os.remove(st.session_state["last_mp4"])
            except Exception:
                pass

        outcome = detect_outcome(user_words, ending_mode)
        code_lines, term_logs = build_structured_code(user_words, lang_choice, outcome)
        file_name = lang_choice.split("(")[-1].rstrip(")")
        lang_label = lang_choice.split(" (")[0]

        with st.spinner("Menyusun kode di IDE & menjalankan terminal..."):
            w, h = 540, 960
            frames_per_char = max(1, round(fps / typing_speed))

            # Hitung frame & catat posisi ketikan suara
            key_frames = []
            sim_frame = int(fps * 0.3)

            for idx, tokens in enumerate(code_lines):
                full_str = "".join(t[0] for t in tokens)
                if idx < 2:
                    sim_frame += int(fps * 0.15)
                elif full_str.strip() == "":
                    sim_frame += 2
                else:
                    for ci in range(1, len(full_str) + 1):
                        if full_str[ci - 1] != " ":
                            key_frames.append(sim_frame)
                        sim_frame += frames_per_char
                    sim_frame += int(fps * 0.15)

            term_total_frames = len(term_logs) * int(fps * 0.35) + max(10, int(fps * end_duration))
            total_frames = sim_frame + term_total_frames
            total_duration = max(1.0, total_frames / fps)

            wav_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wav_path = wav_tmp.name
            wav_tmp.close()

            use_keys = "Ketik" in audio_mode
            use_piano = "Piano" in audio_mode
            generate_ide_audio_wav(total_duration, wav_path, key_frames, fps, use_keys=use_keys, use_piano=use_piano)

            temp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            mp4_path = temp_mp4.name
            temp_mp4.close()

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
                # 1. Pembukaan singkat kursor siap di IDE
                for f in range(int(fps * 0.3)):
                    proc.stdin.write(render_ide_frame(completed, [], 0, (f // 4) % 2 == 0, [], file_name, lang_label, th, w, h))

                # 2. Proses mengetik baris demi baris dengan syntax highlighting
                for idx, tokens in enumerate(code_lines):
                    full_str = "".join(t[0] for t in tokens)
                    if idx < 2:
                        completed.append(tokens)
                        for _ in range(int(fps * 0.15)):
                            proc.stdin.write(render_ide_frame(completed, None, 0, False, [], file_name, lang_label, th, w, h))
                    elif full_str.strip() == "":
                        completed.append(tokens)
                        for _ in range(2):
                            proc.stdin.write(render_ide_frame(completed, None, 0, False, [], file_name, lang_label, th, w, h))
                    else:
                        for ci in range(1, len(full_str) + 1):
                            for _ in range(frames_per_char):
                                proc.stdin.write(render_ide_frame(completed, tokens, ci, True, [], file_name, lang_label, th, w, h))
                        completed.append(tokens)
                        for _ in range(int(fps * 0.15)):
                            proc.stdin.write(render_ide_frame(completed, None, 0, False, [], file_name, lang_label, th, w, h))

                # 3. Eksekusi Terminal di Panel Bawah (muncul bertahap)
                shown_term = []
                for t_idx, t_entry in enumerate(term_logs):
                    shown_term.append(t_entry)
                    hold = max(10, int(fps * end_duration)) if t_idx == len(term_logs) - 1 else int(fps * 0.35)
                    for hf in range(hold):
                        proc.stdin.write(render_ide_frame(completed, None, 0, (hf // 5) % 2 == 0, shown_term, file_name, lang_label, th, w, h))

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
                st.session_state["last_tab"] = file_name
            else:
                err_msg = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
                st.error(f"Gagal membuat MP4. Detail: {err_msg[-300:]}")

if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
    st.success(f"✅ Video IDE siap! (File: **{st.session_state['last_tab']}** | Hasil: **{st.session_state['last_outcome'].upper()}**)")
    st.video(st.session_state["last_mp4"])

    with open(st.session_state["last_mp4"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video MP4 (Siap Upload Status WA)",
            data=f.read(),
            file_name=f"status_wa_ide_{st.session_state['last_outcome']}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
