import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import subprocess
import wave
import gc
import os

st.set_page_config(page_title="Authentic Programmer IDE - WA Status", page_icon="👨‍💻", layout="centered")

st.title("👨‍💻 Authentic Dark Programmer Video Generator")
st.markdown("Pilih **Gaya & Tema Visual** yang berbeda total: dari VS Code, Matrix Hacker CRT, Cyberpunk, hingga Neovim Zen.")

# --- SIDEBAR PENGATURAN ---
st.sidebar.header("🎨 Gaya & Tema Visual")

ide_theme = st.sidebar.selectbox(
    "Pilih Tema (Beda Gaya & Warna)",
    [
        "1. VS Code Dark+ (Biru Modern)",
        "2. Matrix Hacker CRT (Hitam - Hijau Neon)",
        "3. Cyberpunk Neon (Ungu Gelap - Pink/Cyan)",
        "4. Neovim Zen Mode (Minimalis Full Kode)",
        "5. Amber Mainframe (Hitam - Emas Retro)"
    ]
)

THEMES = {
    "1. VS Code Dark+ (Biru Modern)": {
        "style": "ide", "scanline": False,
        "bg": (18, 20, 26), "sidebar": (26, 29, 38), "tab": (38, 42, 54),
        "border": (55, 62, 80), "status_bar": (0, 122, 204), "status_txt": (255, 255, 255),
        "kw": (86, 156, 214), "ctrl": (197, 134, 192), "func": (220, 220, 170),
        "str": (206, 145, 120), "var": (156, 220, 254), "cmt": (106, 153, 85),
        "norm": (220, 225, 235), "term_ok": (78, 201, 176), "term_err": (244, 71, 71)
    },
    "2. Matrix Hacker CRT (Hitam - Hijau Neon)": {
        "style": "ide", "scanline": True,
        "bg": (2, 10, 4), "sidebar": (4, 18, 7), "tab": (8, 32, 12),
        "border": (0, 140, 45), "status_bar": (0, 180, 55), "status_txt": (0, 15, 5),
        "kw": (0, 255, 90), "ctrl": (120, 255, 150), "func": (0, 220, 75),
        "str": (180, 255, 195), "var": (50, 255, 110), "cmt": (25, 115, 45),
        "norm": (140, 240, 160), "term_ok": (0, 255, 90), "term_err": (255, 65, 65)
    },
    "3. Cyberpunk Neon (Ungu Gelap - Pink/Cyan)": {
        "style": "ide", "scanline": False,
        "bg": (24, 10, 42), "sidebar": (34, 14, 58), "tab": (52, 20, 85),
        "border": (140, 40, 180), "status_bar": (255, 42, 109), "status_txt": (255, 255, 255),
        "kw": (255, 42, 109), "ctrl": (5, 217, 232), "func": (254, 222, 93),
        "str": (5, 217, 232), "var": (255, 130, 220), "cmt": (135, 90, 175),
        "norm": (240, 230, 255), "term_ok": (5, 217, 232), "term_err": (255, 42, 109)
    },
    "4. Neovim Zen Mode (Minimalis Full Kode)": {
        "style": "zen", "scanline": False,
        "bg": (12, 14, 18), "sidebar": (18, 21, 28), "tab": (28, 32, 42),
        "border": (60, 70, 90), "status_bar": (122, 162, 247), "status_txt": (12, 14, 18),
        "kw": (187, 154, 247), "ctrl": (247, 118, 142), "func": (122, 162, 247),
        "str": (158, 206, 106), "var": (125, 207, 255), "cmt": (86, 95, 137),
        "norm": (215, 222, 240), "term_ok": (115, 218, 202), "term_err": (247, 118, 142)
    },
    "5. Amber Mainframe (Hitam - Emas Retro)": {
        "style": "ide", "scanline": True,
        "bg": (16, 10, 2), "sidebar": (26, 16, 4), "tab": (42, 26, 6),
        "border": (160, 100, 15), "status_bar": (235, 155, 20), "status_txt": (15, 10, 0),
        "kw": (255, 195, 50), "ctrl": (255, 140, 25), "func": (255, 225, 110),
        "str": (255, 210, 90), "var": (245, 175, 45), "cmt": (135, 85, 15),
        "norm": (240, 185, 65), "term_ok": (255, 215, 75), "term_err": (255, 75, 45)
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

    else:
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

# --- RENDERER FRAME (MENDUKUNG MODE IDE PENUH & NEOVIM ZEN MODE) ---
def render_ide_frame(
    completed_lines, active_tokens, active_char_count, cursor_on,
    terminal_lines, file_name, lang_label, th, w=540, h=960
):
    img = Image.new("RGB", (w, h), color=th["bg"])
    draw = ImageDraw.Draw(img)

    is_zen = (th["style"] == "zen")

    f_ui = get_font(11)
    f_tab = get_font(12, bold=True)
    f_code = get_font(16 if is_zen else 14)
    f_num = get_font(13 if is_zen else 12)

    top_h = 34
    status_h = 26
    term_h = 185

    if is_zen:
        # --- GAYA NEOVIM ZEN: FULL SCREEN CODE TANPA SIDEBAR ---
        draw.rectangle([0, 0, w, top_h], fill=th["sidebar"])
        draw.text((16, 10), f"NVIM v0.10  —  ~/dark-core/src/{file_name}", fill=th["cmt"], font=f_ui)

        ed_left = 0
        editor_top = top_h + 6
        editor_bottom = h - term_h - status_h
        gutter_x = 16
        text_start_x = 52
        line_h = 25
    else:
        # --- GAYA FULL IDE (ACTIVITY BAR + SIDEBAR EXPLORER + TAB) ---
        draw.rectangle([0, 0, w, top_h], fill=th["sidebar"])
        draw.ellipse([12, 11, 22, 21], fill=(255, 95, 86))
        draw.ellipse([28, 11, 38, 21], fill=(255, 189, 46))
        draw.ellipse([44, 11, 54, 21], fill=(39, 201, 63))

        title_str = f"dark-workspace — {file_name}"
        tbbox = draw.textbbox((0, 0), title_str, font=f_ui)
        draw.text(((w - (tbbox[2] - tbbox[0])) // 2, 10), title_str, fill=th["cmt"], font=f_ui)

        act_w = 34
        side_w = 112
        editor_top = top_h + 28
        editor_bottom = h - term_h - status_h

        draw.rectangle([0, top_h, act_w, h - status_h], fill=th["sidebar"])
        draw.line([(act_w, top_h), (act_w, h - status_h)], fill=th["border"], width=1)
        draw.rectangle([9, top_h + 14, 24, top_h + 30], outline=th["norm"], width=1)
        draw.ellipse([10, top_h + 46, 23, top_h + 59], outline=th["cmt"], width=1)

        draw.rectangle([act_w + 1, top_h, act_w + side_w, h - status_h], fill=th["sidebar"])
        draw.line([(act_w + side_w, top_h), (act_w + side_w, h - status_h)], fill=th["border"], width=1)

        draw.text((act_w + 10, top_h + 10), "EXPLORER", fill=th["cmt"], font=f_ui)
        draw.text((act_w + 10, top_h + 32), "▾ DARK-CORE", fill=th["norm"], font=f_ui)
        draw.text((act_w + 16, top_h + 52), "▾ src", fill=th["cmt"], font=f_ui)
        draw.rectangle([act_w + 1, top_h + 68, act_w + side_w - 1, top_h + 88], fill=th["tab"])
        draw.text((act_w + 22, top_h + 72), f"• {file_name}", fill=th["var"], font=f_ui)
        draw.text((act_w + 22, top_h + 94), "  config.json", fill=th["cmt"], font=f_ui)

        ed_left = act_w + side_w + 1
        draw.rectangle([ed_left, top_h, w, editor_top], fill=th["sidebar"])
        draw.rectangle([ed_left, top_h, ed_left + 135, editor_top], fill=th["bg"])
        draw.line([(ed_left, top_h), (ed_left + 135, top_h)], fill=th["status_bar"], width=2)
        draw.text((ed_left + 12, top_h + 7), f"{file_name}  ×", fill=th["norm"], font=f_tab)
        draw.text((ed_left + 12, editor_top + 6), f"src > {file_name} > processState()", fill=th["cmt"], font=f_ui)

        gutter_x = ed_left + 8
        text_start_x = ed_left + 36
        line_h = 22

    # --- AREA KODING ---
    code_start_y = editor_top + (16 if is_zen else 28)
    max_code_w = w - text_start_x - 14

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

            for ch in piece:
                ch_w = draw.textbbox((0, 0), ch, font=f_code)[2]
                if cur_x + ch_w > text_start_x + max_code_w:
                    cur_x = text_start_x + 16
                    cur_y += line_h
                draw.text((cur_x, cur_y), ch, fill=col, font=f_code)
                cur_x += ch_w
                chars_drawn += 1

        if show_cur and cursor_on:
            draw.rectangle([cur_x + 1, cur_y + 2, cur_x + 9, cur_y + (18 if is_zen else 16)], fill=th["var"])

        return cur_y + line_h

    cy = code_start_y
    ln = 1
    for t_line in completed_lines:
        if cy > editor_bottom - 22:
            break
        cy = draw_token_line(t_line, ln, cy)
        ln += 1

    if active_tokens is not None and cy <= editor_bottom - 22:
        cy = draw_token_line(active_tokens, ln, cy, max_chars=active_char_count, show_cur=True)

    # --- PANEL TERMINAL BAWAH ---
    term_top = editor_bottom
    draw.rectangle([ed_left, term_top, w, h - status_h], fill=th["sidebar"])
    draw.line([(ed_left, term_top), (w, term_top)], fill=th["border"], width=1)

    term_header = ":terminal  [zsh]" if is_zen else "PROBLEMS   OUTPUT   TERMINAL"
    draw.text((ed_left + 14, term_top + 7), term_header, fill=th["norm"], font=f_ui)
    if not is_zen:
        draw.line([(ed_left + 132, term_top + 22), (ed_left + 188, term_top + 22)], fill=th["status_bar"], width=2)

    ty = term_top + 32
    for t_txt, t_role in terminal_lines:
        t_col = th.get(t_role, th["norm"])
        words = t_txt.split(" ")
        cur_l = ""
        for wd in words:
            test = cur_l + (" " if cur_l else "") + wd
            if draw.textbbox((0, 0), test, font=f_ui)[2] <= (w - ed_left - 26):
                cur_l = test
            else:
                draw.text((ed_left + 14, ty), cur_l, fill=t_col, font=f_ui)
                ty += 18
                cur_l = wd
        if cur_l:
            draw.text((ed_left + 14, ty), cur_l, fill=t_col, font=f_ui)
            ty += 20

    # --- STATUS BAR BAWAH ---
    sb_top = h - status_h
    draw.rectangle([0, sb_top, w, h], fill=th["status_bar"])
    left_status = f" INSERT | ⎇ main  {file_name}" if is_zen else "⎇ main*   0 errors, 0 warnings"
    draw.text((10, sb_top + 6), left_status, fill=th["status_txt"], font=f_ui)
    right_info = f"Ln {ln}, Col {active_char_count + 1}   {lang_label}"
    rb = draw.textbbox((0, 0), right_info, font=f_ui)
    draw.text((w - (rb[2] - rb[0]) - 10, sb_top + 6), right_info, fill=th["status_txt"], font=f_ui)

    # --- EFEK CRT SCANLINE KHUSUS TEMA MATRIX & AMBER ---
    if th["scanline"]:
        arr = np.array(img, dtype=np.uint8)
        arr[::3, :, :] = (arr[::3, :, :] * 0.55).astype(np.uint8)
        return arr.tobytes()

    return img.tobytes()

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

        with st.spinner(f"Merender tema {ide_theme}..."):
            w, h = 540, 960
            frames_per_char = max(1, round(fps / typing_speed))

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
                for f in range(int(fps * 0.3)):
                    proc.stdin.write(render_ide_frame(completed, [], 0, (f // 4) % 2 == 0, [], file_name, lang_label, th, w, h))

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
