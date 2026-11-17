import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import tempfile
import subprocess
import wave
import re
import gc
import os

st.set_page_config(page_title="Cinematic Coder Video - WA Status", page_icon="✨", layout="centered")

st.title("✨ Cinematic Dark Coder Video Generator")
st.markdown("Desain **Glassmorphism + Radial Glow + Textured Background** ala video estetik TikTok/Reels/Status WA.")

# --- 5 TEMA VISUAL DENGAN LATAR BELAKANG & EFEK BERBEDA ---
THEMES = {
    "1. Midnight Ocean (Gradien Biru Dalam + Cyan Glow)": {
        "bg_top": (4, 10, 22), "bg_bot": (10, 26, 48), "glow": (20, 110, 190),
        "bg_fx": "dots",
        "card": (11, 17, 28), "header": (16, 24, 38), "border": (56, 152, 236),
        "kw": (255, 118, 188), "fn": (96, 215, 255), "var": (145, 245, 255),
        "str": (152, 245, 175), "cmt": (95, 130, 170), "norm": (238, 244, 255)
    },
    "2. Cyberpunk Tokyo (Gradien Ungu + Cyber Grid + Pink/Cyan)": {
        "bg_top": (14, 5, 28), "bg_bot": (38, 10, 58), "glow": (210, 35, 115),
        "bg_fx": "grid",
        "card": (20, 10, 36), "header": (30, 14, 52), "border": (255, 55, 130),
        "kw": (255, 65, 140), "fn": (255, 225, 95), "var": (35, 230, 245),
        "str": (255, 175, 230), "cmt": (145, 95, 185), "norm": (245, 238, 255)
    },
    "3. Matrix Rain (Hitam Pekat + Hujan Kode Hijau)": {
        "bg_top": (1, 6, 3), "bg_bot": (4, 20, 9), "glow": (0, 175, 65),
        "bg_fx": "matrix",
        "card": (5, 14, 8), "header": (8, 22, 12), "border": (0, 220, 85),
        "kw": (0, 255, 125), "fn": (150, 255, 180), "var": (65, 240, 120),
        "str": (215, 255, 225), "cmt": (45, 135, 70), "norm": (195, 252, 210)
    },
    "4. Sunset Crimson (Gradien Merah Gelap + Emas Hangat)": {
        "bg_top": (18, 6, 10), "bg_bot": (46, 15, 18), "glow": (215, 85, 45),
        "bg_fx": "dots",
        "card": (24, 11, 14), "header": (34, 16, 20), "border": (245, 135, 65),
        "kw": (255, 95, 110), "fn": (255, 205, 85), "var": (255, 165, 115),
        "str": (255, 235, 155), "cmt": (155, 100, 95), "norm": (252, 240, 235)
    },
    "5. MacBook Pro Titanium (Minimalis Mewah + Soft Ambient)": {
        "bg_top": (14, 15, 19), "bg_bot": (26, 29, 36), "glow": (95, 115, 155),
        "bg_fx": "clean",
        "card": (22, 24, 30), "header": (30, 33, 41), "border": (95, 105, 125),
        "kw": (255, 121, 198), "fn": (139, 233, 253), "var": (189, 147, 249),
        "str": (241, 250, 140), "cmt": (115, 125, 150), "norm": (248, 248, 242)
    }
}

col1, col2, col3 = st.columns(3)
with col1:
    theme_name = st.selectbox("Pilih Tema Estetik:", list(THEMES.keys()))
with col2:
    lang_mode = st.selectbox("Bahasa Kode:", ["JavaScript / TS", "Python", "C++"])
with col3:
    ending_mode = st.selectbox("Hasil Akhir:", ["Auto-Deteksi", "ERROR", "PAUSED", "SUCCESS"])

th = THEMES[theme_name]

default_words = """Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program."""

user_words = st.text_area(
    "Ganti Kata-Kata di Sini:",
    value=default_words,
    height=175
)

with st.expander("⚙️ Pengaturan Kecepatan & Audio"):
    typing_speed = st.slider("Kecepatan Ketik", 12, 28, 18)
    use_sound = st.checkbox("Suara Ketikan Mechanical + Piano Pelan", value=True)

fps = 20

# --- PRE-RENDER BACKGROUND ESTETIK SEKALI SAJA (SUPER CEPAT & HEMAT RAM) ---
def create_aesthetic_base(w, h, th):
    # 1. Buat Gradien Vertikal Halus dengan NumPy
    y_grad = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top_c = np.array(th["bg_top"], dtype=np.float32)
    bot_c = np.array(th["bg_bot"], dtype=np.float32)
    grad = top_c * (1.0 - y_grad) + bot_c * y_grad
    bg_arr = np.broadcast_to(grad, (h, w, 3)).copy()

    # 2. Tambahkan Radial Glow di tengah-atas belakang kartu kode
    yy, xx = np.ogrid[:h, :w]
    dist_sq = ((xx - w / 2.0) / (w * 0.65)) ** 2 + ((yy - h * 0.42) / (h * 0.45)) ** 2
    radial = np.exp(-dist_sq * 2.2)[:, :, None]
    glow_c = np.array(th["glow"], dtype=np.float32)
    bg_arr += radial * glow_c * 0.48

    # 3. Vignette gelap di keempat sudut agar fokus mata ke tengah
    vig_dist = ((xx - w / 2.0) / (w * 0.55)) ** 2 + ((yy - h / 2.0) / (h * 0.55)) ** 2
    vignette = np.clip(1.0 - vig_dist * 0.35, 0.45, 1.0)[:, :, None]
    bg_arr *= vignette

    base_img = Image.fromarray(np.clip(bg_arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(base_img)

    # 4. Efek Tekstur Background sesuai Tema
    fx = th["bg_fx"]
    b_col = tuple(min(255, int(c * 0.45)) for c in th["border"])

    if fx == "grid":
        step = 36
        for gx in range(0, w, step):
            draw.line([(gx, 0), (gx, h)], fill=b_col, width=1)
        for gy in range(0, h, step):
            draw.line([(0, gy), (w, gy)], fill=b_col, width=1)
    elif fx == "dots":
        rng = np.random.default_rng(99)
        for _ in range(55):
            dx = int(rng.integers(15, w - 15))
            dy = int(rng.integers(15, h - 15))
            r = int(rng.integers(1, 3))
            draw.ellipse([dx - r, dy - r, dx + r, dy + r], fill=b_col)
    elif fx == "matrix":
        f_mat = get_font(12)
        rng = np.random.default_rng(77)
        chars = "01アイウエオカキクケコXYZ"
        for col_x in range(12, w - 12, 26):
            start_y = int(rng.integers(10, 180))
            length = int(rng.integers(6, 18))
            for k in range(length):
                cy = start_y + k * 18
                if cy < h - 20:
                    ch = chars[int(rng.integers(0, len(chars)))]
                    fade = int(45 + (k / length) * 85)
                    draw.text((col_x, cy), ch, fill=(0, fade, int(fade * 0.4)), font=f_mat)

    # 5. Gambar Drop Shadow + Kartu Glassmorphism Rounded di atas Background
    mx, my = 24, 72
    ww, wh = w - (mx * 2), h - (my * 2)

    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([mx + 4, my + 10, mx + ww + 4, my + wh + 10], radius=18, fill=(0, 0, 0, 175))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))

    base_rgba = base_img.convert("RGBA")
    base_rgba = Image.alpha_composite(base_rgba, shadow)

    # Kartu semi-transparan gelap (Glass effect)
    card_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(card_layer)
    c_col = th["card"] + (232,)  # Sedikit transparan agar radial glow tembus halus
    h_col = th["header"] + (245,)
    c_draw.rounded_rectangle([mx, my, mx + ww, my + wh], radius=16, fill=c_col)
    # Header bar bagian atas kartu
    c_draw.rounded_rectangle([mx, my, mx + ww, my + 40], radius=16, fill=h_col)
    c_draw.rectangle([mx, my + 24, mx + ww, my + 40], fill=h_col)

    base_rgba = Image.alpha_composite(base_rgba, card_layer)
    return base_rgba.convert("RGB")

def extract_slug(text, fallback="state"):
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
    if any(w in low for w in ["error", "fail", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit"]):
        return "error"
    if any(w in low for w in ["pause", "rest", "break", "world run", "stop", "istirahat", "jeda"]):
        return "paused"
    return "success"

def build_dynamic_code_tokens(raw_text, lang, outcome):
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    if not lines:
        return [], [], "empty", None

    main_fn = extract_slug(lines[0], "check_reality")
    code_rows = []
    error_line_num = 1
    error_var_name = extract_slug(lines[-1], "promise_state")
    error_reason = lines[-1].replace('"', "'")

    if lang == "JavaScript / TS":
        ext = "js"
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

        error_line_num = len(code_rows) + 1
        if outcome == "paused":
            code_rows.append([("  return", "kw"), (" ", "norm"), ('"SESSION_PAUSED"', "str"), (";", "norm")])
        elif outcome == "error":
            code_rows.append([("  throw new", "kw"), (" ", "norm"), ("Error", "fn"), (f'("{error_var_name}_FAILED")', "str"), (";", "norm")])
        else:
            code_rows.append([("  return", "kw"), (" ", "norm"), ('"SYSTEM_OK"', "str"), (";", "norm")])
        code_rows.append([("}", "norm")])

        if outcome == "error":
            exec_logs = [
                (f"$ node {main_fn}.{ext}", "norm"),
                (f"Error: {error_var_name}_FAILED (NullPromise)", "err"),
                (f"  at {main_fn} ({main_fn}.{ext}:{error_line_num}:9)", "err"),
                (f"  Cause -> \"{error_reason[:40]}\"", "warn")
            ]
        elif outcome == "paused":
            exec_logs = [
                (f"$ node {main_fn}.{ext}", "norm"),
                (f"> Executing {main_fn}()...", "cmt"),
                (f"[WARN] Process suspended at line {error_line_num}", "warn")
            ]
        else:
            exec_logs = [
                (f"$ node {main_fn}.{ext}", "norm"),
                (f"> Executing {main_fn}()...", "cmt"),
                ("[OK] Resolved cleanly (0 errors)", "ok")
            ]

    elif lang == "Python":
        ext = "py"
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

        error_line_num = len(code_rows) + 1
        if outcome == "paused":
            code_rows.append([("    return", "kw"), (" ", "norm"), ('"SESSION_PAUSED"', "str")])
        elif outcome == "error":
            code_rows.append([("    raise", "kw"), (" ", "norm"), ("RuntimeError", "fn"), (f'("{error_var_name}")', "str")])
        else:
            code_rows.append([("    return", "kw"), (" ", "norm"), ('"REPAIRED"', "str")])

        if outcome == "error":
            exec_logs = [
                (f"$ python3 {main_fn}.{ext}", "norm"),
                (f"File \"{main_fn}.{ext}\", line {error_line_num}, in {main_fn}", "err"),
                (f"RuntimeError: {error_var_name} -> EmptyPromise", "err"),
                (f"Detail: \"{error_reason[:40]}\"", "warn")
            ]
        elif outcome == "paused":
            exec_logs = [
                (f"$ python3 {main_fn}.{ext}", "norm"),
                (f"> Running {main_fn}()...", "cmt"),
                (f"[PAUSED] Thread halted at line {error_line_num}", "warn")
            ]
        else:
            exec_logs = [
                (f"$ python3 {main_fn}.{ext}", "norm"),
                (f"> Running {main_fn}()...", "cmt"),
                ("[OK] Completed with 0 exceptions", "ok")
            ]

    else:
        ext = "cpp"
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

        error_line_num = len(code_rows) + 1
        if outcome == "paused":
            code_rows.append([("    return", "kw"), (" SESSION_PAUSED;", "var")])
        elif outcome == "error":
            code_rows.append([("    assert", "fn"), (f"({error_var_name} != nullptr);", "norm")])
        else:
            code_rows.append([("    return", "kw"), (" EXIT_SUCCESS;", "var")])
        code_rows.append([("}", "norm")])

        if outcome == "error":
            exec_logs = [
                (f"$ ./{main_fn} --run", "norm"),
                (f"SEGFAULT at {main_fn}.{ext}:line {error_line_num}", "err"),
                (f"Assertion `{error_var_name} != nullptr` failed", "err"),
                (f"Dump: \"{error_reason[:40]}\"", "warn")
            ]
        elif outcome == "paused":
            exec_logs = [
                (f"$ ./{main_fn} --run", "norm"),
                ("> Linking runtime modules...", "cmt"),
                (f"[SUSPEND] SIGSTOP received at line {error_line_num}", "warn")
            ]
        else:
            exec_logs = [
                (f"$ ./{main_fn} --run", "norm"),
                ("> Linking runtime modules...", "cmt"),
                ("[SUCCESS] Binary exited cleanly (0)", "ok")
            ]

    err_line_to_highlight = error_line_num if outcome == "error" else None
    return code_rows, exec_logs, f"{main_fn}.{ext}", err_line_to_highlight

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

# --- RENDERER FRAME DI ATAS PRE-RENDERED BASE ---
def render_code_frame(
    base_bg, completed_rows, active_row, active_chars, cursor_on,
    exec_logs, outcome, show_final_status, file_label, err_line_num, th, w=540, h=960
):
    img = base_bg.copy()
    draw = ImageDraw.Draw(img)

    mx, my = 24, 72
    ww, wh = w - (mx * 2), h - (my * 2)

    border_col = th["border"]
    if show_final_status:
        if outcome == "error":
            border_col = (255, 65, 80)
        elif outcome == "paused":
            border_col = (255, 195, 45)
        else:
            border_col = (60, 245, 135)

    # Garis border luar rounded glowing
    draw.rounded_rectangle([mx, my, mx + ww, my + wh], radius=16, outline=border_col, width=2)

    # Tombol window macOS + Nama File
    hh = 40
    draw.line([(mx + 1, my + hh), (mx + ww - 1, my + hh)], fill=tuple(int(c * 0.4) for c in th["border"]), width=1)
    draw.ellipse([mx + 16, my + 14, mx + 26, my + 24], fill=(255, 95, 86))
    draw.ellipse([mx + 32, my + 14, mx + 42, my + 24], fill=(255, 189, 46))
    draw.ellipse([mx + 48, my + 14, mx + 58, my + 24], fill=(39, 201, 63))

    f_hdr = get_font(13, bold=True)
    draw.text((mx + 74, my + 12), file_label, fill=th["norm"], font=f_hdr)

    f_code = get_font(16)
    f_num = get_font(13)

    gutter_x = mx + 14
    code_x = mx + 46
    max_code_w = ww - 60
    line_h = 24
    max_y = my + wh - 205

    def draw_tokens(row_tokens, line_num, y_pos, char_limit=None, draw_cursor=False):
        is_err_row = (show_final_status and err_line_num == line_num)
        if is_err_row:
            draw.rectangle([mx + 3, y_pos - 2, mx + ww - 3, y_pos + line_h], fill=(80, 15, 22))
            draw.text((gutter_x, y_pos + 2), f"{line_num:2d}", fill=(255, 90, 100), font=f_num)
        else:
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

            col = (255, 120, 130) if is_err_row else th.get(role, th["norm"])
            for ch in piece:
                cw = draw.textbbox((0, 0), ch, font=f_code)[2]
                if cx + cw > code_x + max_code_w:
                    cx = code_x + 18
                    cy += line_h
                    if is_err_row:
                        draw.rectangle([mx + 3, cy - 2, mx + ww - 3, cy + line_h], fill=(80, 15, 22))
                draw.text((cx, cy), ch, fill=col, font=f_code)
                cx += cw
                count += 1

        if draw_cursor and cursor_on:
            draw.rectangle([cx + 1, cy + 2, cx + 10, cy + 18], fill=th["fn"])

        return cy + line_h

    curr_y = my + hh + 16
    ln = 1
    for r_tokens in completed_rows:
        if curr_y > max_y:
            break
        curr_y = draw_tokens(r_tokens, ln, curr_y)
        ln += 1

    if active_row is not None and curr_y <= max_y:
        curr_y = draw_tokens(active_row, ln, curr_y, char_limit=active_chars, draw_cursor=True)

    # Panel Terminal Log Bawah
    out_top = my + wh - 190
    draw.line([(mx + 14, out_top), (mx + ww - 14, out_top)], fill=tuple(int(c * 0.45) for c in th["border"]), width=1)

    f_out = get_font(13)
    log_colors = {
        "norm": th["norm"],
        "cmt": th["cmt"],
        "err": (255, 85, 95),
        "warn": (255, 205, 70),
        "ok": (75, 245, 140)
    }

    oy = out_top + 10
    for log_txt, log_kind in exec_logs:
        l_col = log_colors.get(log_kind, th["cmt"])
        words = log_txt.split(" ")
        cur_l = ""
        for wd in words:
            test = cur_l + (" " if cur_l else "") + wd
            if draw.textbbox((0, 0), test, font=f_out)[2] <= (ww - 36):
                cur_l = test
            else:
                draw.text((mx + 16, oy), cur_l, fill=l_col, font=f_out)
                oy += 17
                cur_l = "  " + wd
        if cur_l:
            draw.text((mx + 16, oy), cur_l, fill=l_col, font=f_out)
            oy += 19

    if show_final_status:
        bx1, bx2 = mx + 16, mx + ww - 16
        by2 = my + wh - 14
        by1 = by2 - 42

        if outcome == "error":
            bg_b, fg_b, status_lbl = (75, 14, 22), (255, 80, 90), f"✖ ERROR AT LINE {err_line_num} // EXIT 1"
        elif outcome == "paused":
            bg_b, fg_b, status_lbl = (60, 44, 10), (255, 205, 55), "⏸ EXIT CODE 0 // SESSION PAUSED"
        else:
            bg_b, fg_b, status_lbl = (12, 60, 28), (65, 255, 130), "✔ EXIT CODE 0 // SYSTEM REPAIRED"

        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=10, fill=bg_b, outline=fg_b, width=2)
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

if st.button("🎬 Generate Video Estetik", type="primary", use_container_width=True):
    if not user_words.strip():
        st.warning("Teks tidak boleh kosong!")
    else:
        if "last_mp4" in st.session_state and os.path.exists(st.session_state["last_mp4"]):
            try:
                os.remove(st.session_state["last_mp4"])
            except Exception:
                pass

        outcome = detect_outcome(user_words, ending_mode)
        code_rows, exec_logs, file_label, err_line_num = build_dynamic_code_tokens(user_words, lang_mode, outcome)

        with st.spinner("Merender background glow & animasi kode..."):
            w, h = 540, 960
            base_bg = create_aesthetic_base(w, h, th)
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

            run_frames = len(exec_logs) * int(fps * 0.35) + int(fps * 1.2)
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
                    proc.stdin.write(render_code_frame(base_bg, completed, [], 0, (f // 4) % 2 == 0, [], outcome, False, file_label, err_line_num, th, w, h))

                for idx, r_tokens in enumerate(code_rows):
                    full_s = "".join(t[0] for t in r_tokens)
                    if idx == 0:
                        completed.append(r_tokens)
                        for _ in range(int(fps * 0.25)):
                            proc.stdin.write(render_code_frame(base_bg, completed, None, 0, False, [], outcome, False, file_label, err_line_num, th, w, h))
                    else:
                        for ci in range(1, len(full_s) + 1):
                            for _ in range(f_per_char):
                                proc.stdin.write(render_code_frame(base_bg, completed, r_tokens, ci, True, [], outcome, False, file_label, err_line_num, th, w, h))
                        completed.append(r_tokens)
                        for _ in range(int(fps * 0.15)):
                            proc.stdin.write(render_code_frame(base_bg, completed, None, 0, False, [], outcome, False, file_label, err_line_num, th, w, h))

                shown_logs = []
                for l_idx, l_entry in enumerate(exec_logs):
                    shown_logs.append(l_entry)
                    is_last = (l_idx == len(exec_logs) - 1)
                    hold = int(fps * 1.2) if is_last else int(fps * 0.35)
                    for _ in range(hold):
                        proc.stdin.write(render_code_frame(base_bg, completed, None, 0, False, shown_logs, outcome, is_last, file_label, err_line_num, th, w, h))

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
    st.success(f"✅ Video **{st.session_state['last_file']}** siap!")
    st.video(st.session_state["last_mp4"])
    with open(st.session_state["last_mp4"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video MP4",
            data=f.read(),
            file_name=f"aesthetic_{st.session_state['last_file']}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
