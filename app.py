import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import tempfile
import subprocess
import wave
import re
import gc
import os

st.set_page_config(page_title="Programmer Desk Code Generator", page_icon="🖥️", layout="centered")

st.title("🖥️ Programmer Desk Code Generator")
st.markdown("Tulis kalimat biasa → otomatis diubah menjadi **kode pemrograman asli** (*syntax highlighting*) di layar monitor setup malam hari.")

# --- PILIHAN SETUP BACKGROUND, BAHASA KODE & ENDING ---
col1, col2, col3 = st.columns(3)
with col1:
    setup_theme = st.selectbox(
        "1. Suasana Meja:",
        [
            "Cyberpunk City Night",
            "Warm Lo-Fi Midnight",
            "Matrix Hacker Room",
            "Upload Gambar Meja Sendiri"
        ]
    )
with col2:
    lang_mode = st.selectbox(
        "2. Bahasa Kode:",
        ["JavaScript / TS", "Python", "C++"]
    )
with col3:
    ending_mode = st.selectbox(
        "3. Hasil Akhir:",
        ["Auto-Deteksi", "ERROR", "PAUSED", "SUCCESS"]
    )

uploaded_bg = None
if setup_theme == "Upload Gambar Meja Sendiri":
    uploaded_bg = st.file_uploader("Upload gambar/foto meja komputer (JPG/PNG/GIF):", type=["jpg", "jpeg", "png", "gif"])

default_words = """Not everything is real.
Some things are just well-written illusions.
Some promises are nothing but empty code.
So, stop trying to understand everything.
Take a break.
Let the world run its own program."""

user_words = st.text_area(
    "4. Tulis Kata-Kata Biasa (Otomatis Diterjemahkan Jadi Kode):",
    value=default_words,
    height=165
)

with st.expander("⚙️ Pengaturan Kecepatan & Suara"):
    typing_speed = st.slider("Kecepatan Ngoding (Karakter/Detik)", 14, 32, 22)
    use_sound = st.checkbox("Suara Ketikan Mechanical + Ambient Malam", value=True)

fps = 20

THEMES = {
    "Cyberpunk City Night": {
        "sky_top": (4, 10, 24), "sky_bot": (10, 28, 52), "city_glow": (15, 115, 175),
        "lamp_glow": (255, 180, 95), "kbd_led": (35, 165, 255),
        "term_cmd": (75, 215, 245), "term_bar": (55, 245, 120),
        "kw": (255, 105, 180), "fn": (95, 210, 255), "var": (145, 245, 255),
        "str": (155, 250, 175), "cmt": (95, 130, 170), "norm": (235, 242, 255)
    },
    "Warm Lo-Fi Midnight": {
        "sky_top": (8, 8, 16), "sky_bot": (22, 18, 34), "city_glow": (95, 65, 145),
        "lamp_glow": (255, 165, 70), "kbd_led": (255, 155, 65),
        "term_cmd": (110, 235, 255), "term_bar": (255, 195, 85),
        "kw": (255, 121, 198), "fn": (255, 215, 105), "var": (139, 233, 253),
        "str": (185, 250, 155), "cmt": (125, 120, 155), "norm": (245, 245, 250)
    },
    "Matrix Hacker Room": {
        "sky_top": (1, 6, 3), "sky_bot": (4, 18, 8), "city_glow": (0, 130, 50),
        "lamp_glow": (40, 220, 100), "kbd_led": (0, 255, 85),
        "term_cmd": (0, 255, 95), "term_bar": (120, 255, 145),
        "kw": (0, 255, 125), "fn": (155, 255, 180), "var": (65, 240, 120),
        "str": (215, 255, 225), "cmt": (45, 135, 70), "norm": (195, 252, 210)
    }
}

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

def build_programmer_desk_scene(w, h, theme_key, custom_file=None):
    mon_screen = (60, 332, 480, 620)

    if custom_file is not None:
        img = Image.open(custom_file).convert("RGB")
        bg_blur = img.resize((w, h)).filter(ImageFilter.GaussianBlur(radius=18))
        bg_arr = (np.array(bg_blur, dtype=np.float32) * 0.45).astype(np.uint8)
        canvas = Image.fromarray(bg_arr)

        scale = min(w / img.width, (h * 0.72) / img.height)
        nw, nh = int(img.width * scale), int(img.height * scale)
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        ox = (w - nw) // 2
        oy = (h - nh) // 2
        canvas.paste(resized, (ox, oy))

        sx1 = ox + int(nw * 0.14)
        sy1 = oy + int(nh * 0.31)
        sx2 = ox + int(nw * 0.86)
        sy2 = oy + int(nh * 0.67)
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle([sx1, sy1, sx2, sy2], radius=8, fill=(5, 8, 12))
        return canvas, (sx1, sy1, sx2, sy2)

    th = THEMES[theme_key]
    y_grad = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    s_top = np.array(th["sky_top"], dtype=np.float32)
    s_bot = np.array(th["sky_bot"], dtype=np.float32)
    arr = np.broadcast_to(s_top * (1 - y_grad) + s_bot * y_grad, (h, w, 3)).copy()

    yy, xx = np.ogrid[:h, :w]
    city_d = ((xx - w * 0.5) / (w * 0.38)) ** 2 + ((yy - h * 0.25) / (h * 0.22)) ** 2
    arr += np.exp(-city_d * 2.0)[:, :, None] * np.array(th["city_glow"], dtype=np.float32) * 0.65

    lamp_d = ((xx - w * 0.88) / (w * 0.25)) ** 2 + ((yy - h * 0.52) / (h * 0.22)) ** 2
    arr += np.exp(-lamp_d * 2.4)[:, :, None] * np.array(th["lamp_glow"], dtype=np.float32) * 0.45

    kbd_d = ((xx - w * 0.5) / (w * 0.42)) ** 2 + ((yy - h * 0.78) / (h * 0.10)) ** 2
    arr += np.exp(-kbd_d * 2.5)[:, :, None] * np.array(th["kbd_led"], dtype=np.float32) * 0.50

    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(base)

    win_x1, win_y1, win_x2, win_y2 = 135, 35, 405, 335
    draw.rectangle([win_x1, win_y1, win_x2, win_y2], fill=(6, 14, 28), outline=(18, 24, 34), width=6)
    rng = np.random.default_rng(2026)
    b_x = win_x1 + 8
    while b_x < win_x2 - 20:
        bw = int(rng.integers(24, 42))
        bh = int(rng.integers(110, 230))
        by = win_y2 - bh
        draw.rectangle([b_x, by, min(win_x2 - 4, b_x + bw), win_y2], fill=(10, 22, 40))
        for wy in range(by + 10, win_y2 - 12, 14):
            for wx in range(b_x + 5, min(win_x2 - 8, b_x + bw - 5), 9):
                if rng.random() > 0.55:
                    draw.rectangle([wx, wy, wx + 3, wy + 5], fill=th["city_glow"])
        b_x += bw + 6

    draw.line([(w // 2, win_y1), (w // 2, win_y2)], fill=(14, 18, 26), width=6)

    f_post = get_font(12, bold=True)
    f_post_sm = get_font(9)
    draw.rectangle([26, 75, 118, 215], fill=(10, 14, 22), outline=(45, 65, 90), width=3)
    draw.text((46, 92), "KEEP", fill=(180, 215, 240), font=f_post)
    draw.text((44, 110), "CALM", fill=(180, 215, 240), font=f_post)
    draw.text((54, 128), "AND", fill=(110, 140, 165), font=f_post_sm)
    draw.text((38, 144), "CODE ON", fill=(180, 215, 240), font=f_post)
    draw.text((52, 166), "</>", fill=th["term_cmd"], font=f_post)

    draw.rectangle([422, 95, 514, 215], fill=(10, 14, 22), outline=(45, 65, 90), width=3)
    draw.text((442, 122), "TRUST", fill=(180, 215, 240), font=f_post)
    draw.text((440, 142), "PROCESS", fill=th["term_bar"], font=f_post_sm)
    draw.text((454, 165), "{ }", fill=(180, 215, 240), font=f_post)

    draw.polygon([(0, 670), (w, 670), (w, h), (0, h)], fill=(18, 13, 11))
    draw.line([(0, 670), (w, 670)], fill=(45, 34, 28), width=3)
    draw.rectangle([245, 626, 295, 686], fill=(22, 26, 34))
    draw.polygon([(195, 686), (345, 686), (365, 700), (175, 700)], fill=(30, 35, 45))

    mx1, my1, mx2, my2 = 48, 320, 492, 632
    draw.rounded_rectangle([mx1, my1, mx2, my2], radius=14, fill=(16, 20, 28), outline=(55, 70, 92), width=3)
    sx1, sy1, sx2, sy2 = mon_screen
    draw.rounded_rectangle([sx1, sy1, sx2, sy2], radius=8, fill=(4, 7, 11))

    draw.rounded_rectangle([30, 630, 106, 710], radius=10, fill=(14, 16, 20), outline=(40, 48, 60), width=2)
    draw.arc([96, 646, 122, 692], start=270, end=90, fill=(40, 48, 60), width=5)
    draw.text((50, 660), "</>", fill=th["kbd_led"], font=get_font(15, bold=True))

    draw.polygon([(475, 485), (535, 515), (515, 545), (460, 510)], fill=(25, 30, 38))
    draw.ellipse([485, 518, 520, 542], fill=th["lamp_glow"])
    draw.rounded_rectangle([442, 622, 502, 668], radius=14, fill=(32, 38, 48), outline=(70, 85, 105), width=2)
    draw.rounded_rectangle([450, 632, 494, 656], radius=8, fill=(8, 12, 18))
    draw.ellipse([456, 638, 468, 650], fill=th["term_cmd"])
    draw.ellipse([476, 638, 488, 650], fill=th["term_cmd"])
    draw.rounded_rectangle([452, 670, 492, 700], radius=8, fill=(28, 34, 44))

    draw.polygon([(115, 728), (425, 728), (455, 818), (85, 818)], fill=(14, 17, 23), outline=(45, 60, 80), width=2)
    for row_i in range(4):
        ky = 738 + row_i * 18
        margin = (3 - row_i) * 6
        kx = 124 + margin
        while kx < 416 - margin:
            kw = 38 if (row_i == 3 and 210 < kx < 290) else 16
            draw.rounded_rectangle([kx, ky, kx + kw, ky + 12], radius=2, fill=(22, 28, 38), outline=th["kbd_led"], width=1)
            kx += kw + 4

    return base, mon_screen

def detect_outcome(text, choice):
    if choice != "Auto-Deteksi":
        return choice.lower()
    low = text.lower()
    if any(w in low for w in ["error", "fail", "crash", "gagal", "rusak", "hancur", "hilang", "putus", "kecewa", "sakit"]):
        return "error"
    if any(w in low for w in ["pause", "rest", "break", "world run", "stop", "istirahat", "jeda"]):
        return "paused"
    return "success"

def extract_slug(text, fallback="process"):
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    stop = {"the", "and", "for", "are", "but", "not", "you", "all", "just", "some", "that", "with", "yang", "dan", "ini", "itu"}
    f = [w for w in words if w not in stop]
    return f"{f[0]}_{f[1]}" if len(f) >= 2 else (f[0] if f else fallback)

# --- KONVERSI KALIMAT MENJADI TOKEN KODE ASLI (SYNTAX HIGHLIGHTING) ---
def build_code_tokens(raw_text, lang, outcome):
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    if not lines:
        return [], "script.js", {}

    main_fn = extract_slug(lines[0], "reality_check")
    code_rows = []
    err_var = extract_slug(lines[-1], "promise_state")

    if lang == "JavaScript / TS":
        ext = "js"
        code_rows.append([("async function", "kw"), (" ", "norm"), (f"{main_fn}", "fn"), ("() {", "norm")])
        for idx, line in enumerate(lines):
            clean = line.replace('"', "'")
            vname = extract_slug(line, f"var_{idx}")
            low = line.lower()

            if idx == 0:
                code_rows.append([("  const", "kw"), (f" {vname} ", "var"), ("= ", "norm"), ("false", "kw"), (";", "norm")])
                code_rows.append([("  // ", "cmt"), (clean, "cmt")])
            elif any(w in low for w in ["if", "not", "bukan", "jangan", "stop", "no"]):
                code_rows.append([("  if", "kw"), (" (!", "norm"), (vname, "var"), (") ", "norm"), ("warn", "fn"), (f'("{clean}")', "str"), (";", "norm")])
            elif idx == len(lines) - 1:
                code_rows.append([("  await", "kw"), (" ", "norm"), ("world", "var"), (".", "norm"), ("run", "fn"), (f'("{clean}")', "str"), (";", "norm")])
            else:
                code_rows.append([("  let", "kw"), (f" {vname} ", "var"), ("= ", "norm"), (f'"{clean}"', "str"), (";", "norm")])

        err_line_num = len(code_rows) + 1
        if outcome == "error":
            code_rows.append([("  throw new", "kw"), (" ", "norm"), ("Error", "fn"), (f'("{err_var}_null")', "str"), (";", "norm")])
        elif outcome == "paused":
            code_rows.append([("  return", "kw"), (" ", "norm"), ('"SESSION_PAUSED"', "str"), (";", "norm")])
        else:
            code_rows.append([("  return", "kw"), (" ", "norm"), ('"SYSTEM_OK"', "str"), (";", "norm")])
        code_rows.append([("}", "norm")])

        err_info = {
            "err_line": err_line_num,
            "line1": f"✖ Error: {err_var}_null (Line {err_line_num:02d})",
            "line2": f"at {main_fn} ({main_fn}.{ext}:{err_line_num}:9)",
            "line3": f"Cause: \"{lines[-1]}\""
        }

    elif lang == "Python":
        ext = "py"
        code_rows.append([("def", "kw"), (" ", "norm"), (f"{main_fn}", "fn"), ("():", "norm")])
        for idx, line in enumerate(lines):
            clean = line.replace('"', "'")
            vname = extract_slug(line, f"node_{idx}")
            low = line.lower()

            if idx == 0:
                code_rows.append([(f"    {vname} ", "var"), ("= ", "norm"), ("False", "kw")])
                code_rows.append([("    # ", "cmt"), (clean, "cmt")])
            elif any(w in low for w in ["if", "not", "bukan", "jangan", "stop", "no"]):
                code_rows.append([("    if not", "kw"), (f" {vname}: ", "var"), ("log", "fn"), (f'("{clean}")', "str")])
            elif idx == len(lines) - 1:
                code_rows.append([("    ", "norm"), ("world", "var"), (".", "norm"), ("execute", "fn"), (f'("{clean}")', "str")])
            else:
                code_rows.append([(f"    {vname} ", "var"), ("= ", "norm"), (f'"{clean}"', "str")])

        err_line_num = len(code_rows) + 1
        if outcome == "error":
            code_rows.append([("    raise", "kw"), (" ", "norm"), ("RuntimeError", "fn"), (f'("{err_var}")', "str")])
        elif outcome == "paused":
            code_rows.append([("    return", "kw"), (" ", "norm"), ('"SESSION_PAUSED"', "str")])
        else:
            code_rows.append([("    return", "kw"), (" ", "norm"), ('"SYSTEM_OK"', "str")])

        err_info = {
            "err_line": err_line_num,
            "line1": f"✖ RuntimeError: {err_var} (Line {err_line_num:02d})",
            "line2": f"File \"{main_fn}.{ext}\", line {err_line_num}, in {main_fn}",
            "line3": f"Cause: \"{lines[-1]}\""
        }

    else:  # C++
        ext = "cpp"
        code_rows.append([("int", "kw"), (" ", "norm"), (f"{main_fn}", "fn"), ("() {", "norm")])
        for idx, line in enumerate(lines):
            clean = line.replace('"', "'")
            vname = extract_slug(line, f"ptr_{idx}")
            if idx == 0:
                code_rows.append([("    bool", "kw"), (f" {vname} ", "var"), ("= ", "norm"), ("false", "kw"), (";", "norm")])
                code_rows.append([("    // ", "cmt"), (clean, "cmt")])
            elif idx == len(lines) - 1:
                code_rows.append([("    ", "norm"), ("sys_run", "fn"), (f'("{clean}")', "str"), (";", "norm")])
            else:
                code_rows.append([("    auto", "kw"), (f" {vname} ", "var"), ("= ", "norm"), (f'"{clean}"', "str"), (";", "norm")])

        err_line_num = len(code_rows) + 1
        if outcome == "error":
            code_rows.append([("    assert", "fn"), (f"({err_var} != nullptr);", "norm")])
        elif outcome == "paused":
            code_rows.append([("    return", "kw"), (" SESSION_PAUSED;", "var")])
        else:
            code_rows.append([("    return", "kw"), (" EXIT_SUCCESS;", "var")])
        code_rows.append([("}", "norm")])

        err_info = {
            "err_line": err_line_num,
            "line1": f"✖ SEGFAULT at {main_fn}.{ext} (Line {err_line_num:02d})",
            "line2": f"Assertion `{err_var} != nullptr` failed",
            "line3": f"Cause: \"{lines[-1]}\""
        }

    return code_rows, f"{main_fn}.{ext}", err_info

# --- RENDERER FRAME MONITOR (CODE EDITOR + AUTO-SCROLL + NEON GLOW) ---
def render_monitor_frame(
    base_scene, mon_rect, phase, progress_pct,
    boot_lines, completed_rows, active_row, active_chars, cursor_on,
    outcome, error_info, file_label, th, w=540, h=960
):
    img = base_scene.copy()
    sx1, sy1, sx2, sy2 = mon_rect
    sw = sx2 - sx1
    sh = sy2 - sy1

    scr_layer = Image.new("RGB", (sw, sh), (5, 8, 13))
    s_draw = ImageDraw.Draw(scr_layer)

    if phase == "ending" and outcome == "error":
        s_draw.rectangle([0, 0, sw, sh], fill=(24, 5, 9))
        s_draw.rounded_rectangle([1, 1, sw - 2, sh - 2], radius=8, outline=(255, 65, 75), width=2)

    f_boot = get_font(14, bold=True)
    f_pct = get_font(16, bold=True)
    f_tab = get_font(11, bold=True)
    f_code = get_font(13)
    f_num = get_font(11)
    f_err_title = get_font(11, bold=True)
    f_err_sub = get_font(10)

    if phase == "boot":
        cy = 34
        for bl in boot_lines:
            s_draw.text((22, cy), bl, fill=th["term_cmd"], font=f_boot)
            cy += 30

        bar_y = cy + 16
        pct_txt = f"[ {progress_pct:3d}% ]"
        s_draw.text((22, bar_y), pct_txt, fill=th["term_bar"], font=f_pct)

        bx1, bx2 = 118, sw - 24
        by1, by2 = bar_y - 2, bar_y + 20
        s_draw.rounded_rectangle([bx1, by1, bx2, by2], radius=4, outline=(190, 210, 225), width=2)
        fill_w = int((bx2 - bx1 - 6) * (progress_pct / 100.0))
        if fill_w > 0:
            s_draw.rounded_rectangle([bx1 + 3, by1 + 3, bx1 + 3 + fill_w, by2 - 3], radius=2, fill=th["term_bar"])

    else:
        # 1. Header Tab Editor di bagian paling atas layar monitor
        hdr_h = 24
        s_draw.rectangle([0, 0, sw, hdr_h], fill=(12, 18, 28))
        s_draw.line([(0, hdr_h), (sw, hdr_h)], fill=(35, 50, 72), width=1)
        s_draw.ellipse([10, 8, 17, 15], fill=(255, 95, 86))
        s_draw.ellipse([22, 8, 29, 15], fill=(255, 189, 46))
        s_draw.ellipse([34, 8, 41, 15], fill=(39, 201, 63))
        s_draw.text((50, 5), f"{file_label}  •  UTF-8", fill=th["term_cmd"], font=f_tab)

        # 2. Susun baris visual ter-wrap agar nomor baris dan token tetap utuh saat AUTO-SCROLL
        gutter_x = 10
        code_x = 34
        max_code_w = sw - code_x - 10
        line_h = 19

        # Kumpulkan baris-baris yang akan digambar: (line_num_or_None, [(char, color), ...], is_err_row, draw_cursor)
        visual_lines = []

        def process_token_row(row_tokens, line_num, char_limit=None, show_cur=False):
            is_err = (phase == "ending" and outcome == "error" and error_info.get("err_line") == line_num)
            cur_chars = []
            cur_w = 0
            counted = 0
            first_subline = True

            for tok_txt, tok_role in row_tokens:
                if char_limit is not None:
                    rem = char_limit - counted
                    if rem <= 0:
                        break
                    piece = tok_txt[:rem]
                else:
                    piece = tok_txt

                col = (255, 105, 115) if is_err else th.get(tok_role, th["norm"])
                for ch in piece:
                    cw = s_draw.textbbox((0, 0), ch, font=f_code)[2]
                    if cur_w + cw > max_code_w and cur_chars:
                        visual_lines.append((line_num if first_subline else None, cur_chars, is_err, False))
                        first_subline = False
                        cur_chars = [(" ", col), (" ", col)]  # indentasi wrap
                        cur_w = cw * 2
                    cur_chars.append((ch, col))
                    cur_w += cw
                    counted += 1

            visual_lines.append((line_num if first_subline else None, cur_chars, is_err, show_cur))

        for idx, r_tok in enumerate(completed_rows):
            process_token_row(r_tok, idx + 1)

        if active_row is not None:
            process_token_row(active_row, len(completed_rows) + 1, char_limit=active_chars, show_cur=True)

        # Hitung ruang vertikal yang tersedia di atas kotak status bawah
        footer_reserve = 78 if (phase == "ending" and outcome == "error") else (48 if phase == "ending" else 12)
        avail_h = sh - (hdr_h + 6) - footer_reserve
        max_vis = max(1, avail_h // line_h)

        # AUTO-SCROLL: ambil baris terbawah yang muat di layar monitor
        vis_slice = visual_lines[-max_vis:]

        cy = hdr_h + 6
        for l_num, char_list, is_err, has_cur in vis_slice:
            if is_err:
                s_draw.rectangle([2, cy - 1, sw - 2, cy + line_h - 1], fill=(75, 14, 22))
            if l_num is not None:
                num_col = (255, 95, 105) if is_err else th["cmt"]
                s_draw.text((gutter_x, cy + 1), f"{l_num:02d}", fill=num_col, font=f_num)

            cx = code_x
            for ch, c_col in char_list:
                s_draw.text((cx, cy), ch, fill=c_col, font=f_code)
                cx += s_draw.textbbox((0, 0), ch, font=f_code)[2]

            if has_cur and cursor_on:
                s_draw.rectangle([cx + 1, cy + 2, cx + 8, cy + 15], fill=th["fn"])
            cy += line_h

        # 3. Kotak Log Error / Status Rapi di Bawah Layar Monitor
        if phase == "ending":
            if outcome == "error":
                by1, by2 = sh - 72, sh - 8
                s_draw.rounded_rectangle([10, by1, sw - 10, by2], radius=6, fill=(58, 10, 16), outline=(255, 75, 85), width=2)
                s_draw.text((18, by1 + 5), error_info["line1"], fill=(255, 95, 105), font=f_err_title)
                s_draw.text((18, by1 + 23), error_info["line2"], fill=(255, 200, 110), font=f_err_sub)

                cause_txt = error_info["line3"]
                while s_draw.textbbox((0, 0), cause_txt, font=f_err_sub)[2] > (sw - 38) and len(cause_txt) > 10:
                    cause_txt = cause_txt[:-4] + "..."
                s_draw.text((18, by1 + 40), cause_txt, fill=(240, 215, 215), font=f_err_sub)

            elif outcome == "paused":
                by1, by2 = sh - 44, sh - 8
                s_draw.rounded_rectangle([10, by1, sw - 10, by2], radius=6, fill=(55, 42, 8), outline=(255, 200, 50), width=2)
                s_draw.text((20, by1 + 10), f"[||] SESSION PAUSED • LINE {error_info['err_line']:02d}", fill=(255, 210, 70), font=f_err_title)
            else:
                by1, by2 = sh - 44, sh - 8
                s_draw.rounded_rectangle([10, by1, sw - 10, by2], radius=6, fill=(10, 55, 25), outline=(65, 255, 130), width=2)
                s_draw.text((20, by1 + 10), "[100%] SYSTEM REPAIRED • EXIT 0", fill=(75, 255, 140), font=f_err_title)

    # Efek Neon Text Glow pada layar monitor
    glow = scr_layer.filter(ImageFilter.GaussianBlur(radius=3))
    scr_glowed = Image.fromarray(
        np.clip(np.array(scr_layer, dtype=np.int16) + (np.array(glow, dtype=np.int16) * 0.55).astype(np.int16), 0, 255).astype(np.uint8)
    )

    img.paste(scr_glowed, (sx1, sy1))
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
        code_rows, file_label, error_info = build_code_tokens(user_words, lang_mode, outcome)
        slug = file_label.split(".")[0]
        th_active = THEMES.get(setup_theme, THEMES["Cyberpunk City Night"])

        with st.spinner("Merender setup meja malam & kode pemrograman..."):
            w, h = 540, 960
            base_scene, mon_rect = build_programmer_desk_scene(w, h, setup_theme, custom_file=uploaded_bg)
            f_per_char = max(1, round(fps / typing_speed))

            boot_steps = [
                f"$ booting {file_label}...",
                "$ initializing compiler...",
                "$ loading source..."
            ]
            boot_frames = int(fps * 1.4)

            key_frames = []
            sim_f = boot_frames
            for idx, r_tok in enumerate(code_rows):
                full_s = "".join(t[0] for t in r_tok)
                if idx == 0:
                    sim_f += int(fps * 0.25)
                else:
                    for ci in range(1, len(full_s) + 1):
                        if full_s[ci - 1] != " ":
                            key_frames.append(sim_f)
                        sim_f += f_per_char
                    sim_f += int(fps * 0.15)

            end_frames = int(fps * 1.5)
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
                # 1. Fase Booting & Progress Bar 0% -> 100%
                for bf in range(boot_frames):
                    pct = min(100, int((bf / max(1, boot_frames - 1)) * 100))
                    visible_boots = boot_steps[: 1 + min(2, int((bf / boot_frames) * 3))]
                    proc.stdin.write(
                        render_monitor_frame(
                            base_scene, mon_rect, "boot", pct,
                            visible_boots, [], None, 0, False, outcome, error_info, file_label, th_active, w, h
                        )
                    )

                # 2. Fase Ngoding Sintaks Asli di Layar Monitor
                completed = []
                for idx, r_tok in enumerate(code_rows):
                    full_s = "".join(t[0] for t in r_tok)
                    if idx == 0:
                        completed.append(r_tok)
                        for _ in range(int(fps * 0.25)):
                            proc.stdin.write(
                                render_monitor_frame(
                                    base_scene, mon_rect, "typing", 100,
                                    [], completed, None, 0, False, outcome, error_info, file_label, th_active, w, h
                                )
                            )
                    else:
                        for ci in range(1, len(full_s) + 1):
                            for _ in range(f_per_char):
                                proc.stdin.write(
                                    render_monitor_frame(
                                        base_scene, mon_rect, "typing", 100,
                                        [], completed, r_tok, ci, True, outcome, error_info, file_label, th_active, w, h
                                    )
                                )
                        completed.append(r_tok)
                        for _ in range(int(fps * 0.15)):
                            proc.stdin.write(
                                render_monitor_frame(
                                    base_scene, mon_rect, "typing", 100,
                                    [], completed, None, 0, False, outcome, error_info, file_label, th_active, w, h
                                )
                            )

                # 3. Fase Ending (Highlight Baris Error Merah + Stack Trace Rapi)
                for _ in range(end_frames):
                    proc.stdin.write(
                        render_monitor_frame(
                            base_scene, mon_rect, "ending", 100,
                            [], completed, None, 0, False, outcome, error_info, file_label, th_active, w, h
                        )
                    )

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
    st.success(f"✅ Video **{st.session_state['last_file']}** siap! (Status: **{st.session_state['last_outcome'].upper()}**)")
    st.video(st.session_state["last_mp4"])
    with open(st.session_state["last_mp4"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video MP4",
            data=f.read(),
            file_name=f"coder_{st.session_state['last_file']}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
