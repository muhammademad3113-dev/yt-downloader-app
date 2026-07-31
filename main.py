import os
import threading
import flet as ft
import yt_dlp

DEFAULT_DIR = "/storage/emulated/0/Download/course"

QUALITY_OPTIONS = {
    "أعلى جودة متوفرة بصوت (غالباً 720p)": "best[acodec!=none][vcodec!=none][ext=mp4]/best[acodec!=none][vcodec!=none]",
    "720p (بصوت)": "best[height<=720][acodec!=none][vcodec!=none][ext=mp4]/best[height<=720][acodec!=none][vcodec!=none]",
    "480p (بصوت)": "best[height<=480][acodec!=none][vcodec!=none][ext=mp4]/best[height<=480][acodec!=none][vcodec!=none]",
    "360p (بصوت، أضمن جودة)": "best[height<=360][acodec!=none][vcodec!=none][ext=mp4]/best[height<=360][acodec!=none][vcodec!=none]",
}

THEME_COLORS = {
    "بنفسجي زاهي": "#673AB7",
    "تركواز": "#009688",
    "برتقالي ناري": "#FF5722",
    "وردي فاقع": "#E91E63",
    "أزرق سماوي": "#2196F3",
}


def main(page: ft.Page):
    page.title = "محمّل الفيديوهات + الترجمة"
    page.padding = 0
    page.rtl = True
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=THEME_COLORS["بنفسجي زاهي"])

    state = {
        "accent": "بنفسجي زاهي",
        "dark_mode": True,
    }

    url_field = ft.TextField(
        label="رابط الفيديو / البلاي ليست",
        hint_text="يوتيوب، تيك توك، إنستجرام...",
        text_align=ft.TextAlign.RIGHT,
        border_radius=12,
        filled=True,
    )

    quality_dd = ft.Dropdown(
        label="الجودة",
        options=[ft.dropdown.Option(k) for k in QUALITY_OPTIONS.keys()],
        value=list(QUALITY_OPTIONS.keys())[0],
        border_radius=12,
        filled=True,
    )

    sub_lang_field = ft.TextField(
        label="لغة/لغات الترجمة (مثال: en,ar)",
        value="en",
        text_align=ft.TextAlign.RIGHT,
        border_radius=12,
        filled=True,
    )

    subtitle_note = ft.Text(
        "ملاحظة: الترجمة متاحة غالباً على يوتيوب فقط. تيك توك وإنستجرام عادة لا يوفرون ملفات ترجمة.",
        size=11,
        italic=True,
        color="#BDBDBD",
    )

    auto_subs_switch = ft.Switch(label="تضمين الترجمة الآلية إذا لم توجد ترجمة رسمية", value=True)

    playlist_folders_switch = ft.Switch(
        label="عند تحميل بلاي ليست: كل فيديو في مجلد منفصل (video 1, video 2...)",
        value=True,
    )

    path_field = ft.TextField(
        label="مجلد الحفظ",
        value=DEFAULT_DIR,
        text_align=ft.TextAlign.RIGHT,
        border_radius=12,
        filled=True,
    )

    log_box = ft.Text(value="", selectable=True, size=12, font_family="monospace")
    log_container = ft.Container(
        content=ft.Column([log_box], scroll=ft.ScrollMode.AUTO),
        height=230,
        bgcolor="#111111",
        padding=10,
        border_radius=12,
    )

    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
    status_text = ft.Text("", size=12, weight=ft.FontWeight.BOLD)

    download_btn = ft.ElevatedButton(
        content=ft.Row(
            [ft.Text('⬇', size=18), ft.Text("ابدأ التحميل", size=16)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        width=400,
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    def append_log(line: str):
        log_box.value += line
        page.update()

    def progress_hook(d):
        if d.get("status") == "downloading":
            pct = d.get("_percent_str", "").strip()
            speed = d.get("_speed_str", "").strip()
            status_text.value = f"جاري التحميل... {pct}  |  {speed}"
            page.update()
        elif d.get("status") == "finished":
            status_text.value = "تمت معالجة ملف، جارٍ الحفظ..."
            page.update()

    def run_download(url, fmt, sub_langs, want_auto_subs, save_dir, use_playlist_folders):
        try:
            os.makedirs(save_dir, exist_ok=True)

            is_playlist = False
            if use_playlist_folders:
                try:
                    probe_opts = {
                        "quiet": True,
                        "skip_download": True,
                        "extract_flat": True,
                        "logger": _YdlLogger(append_log),
                    }
                    with yt_dlp.YoutubeDL(probe_opts) as probe:
                        info = probe.extract_info(url, download=False)
                    is_playlist = bool(info and info.get("entries"))
                except Exception:
                    is_playlist = False

            if is_playlist:
                outtmpl = os.path.join(save_dir, "video %(playlist_autonumber)s", "%(title)s.%(ext)s")
            else:
                outtmpl = os.path.join(save_dir, "%(title)s.%(ext)s")

            ydl_opts = {
                "format": fmt,
                "outtmpl": outtmpl,
                "writesubtitles": True,
                "writeautomaticsub": want_auto_subs,
                "subtitleslangs": [s.strip() for s in sub_langs.split(",") if s.strip()],
                "subtitlesformat": "srt",
                "sleep_interval_requests": 3,
                "sleep_interval_subtitles": 8,
                "ignoreerrors": "only_download",
                "progress_hooks": [progress_hook],
                "logger": _YdlLogger(append_log),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            append_log("\n[DONE] تم الانتهاء بنجاح ✅\n")
            status_text.value = "تم الانتهاء بنجاح ✅"
        except Exception as e:
            append_log(f"\n[ERROR] {e}\n")
            status_text.value = "حدث خطأ ❌"
        finally:
            progress_ring.visible = False
            download_btn.disabled = False
            page.update()

    def start_download(e):
        url = url_field.value.strip()
        if not url:
            url_field.error_text = "من فضلك أدخل رابط صحيح"
            page.update()
            return
        url_field.error_text = None

        fmt = QUALITY_OPTIONS.get(quality_dd.value, list(QUALITY_OPTIONS.values())[0])
        sub_langs = sub_lang_field.value.strip() or "en"
        save_dir = path_field.value.strip() or DEFAULT_DIR

        log_box.value = ""
        status_text.value = "بدء التحميل..."
        progress_ring.visible = True
        download_btn.disabled = True
        page.update()

        threading.Thread(
            target=run_download,
            args=(url, fmt, sub_langs, auto_subs_switch.value, save_dir, playlist_folders_switch.value),
            daemon=True,
        ).start()

    download_btn.on_click = start_download

    download_tab_content = ft.Container(
        padding=16,
        content=ft.Column(
            [
                ft.Card(
                    elevation=4,
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            [
                                url_field,
                                quality_dd,
                                sub_lang_field,
                                subtitle_note,
                                auto_subs_switch,
                                playlist_folders_switch,
                                path_field,
                            ],
                            spacing=12,
                        ),
                    ),
                ),
                ft.Row([download_btn, progress_ring], alignment=ft.MainAxisAlignment.CENTER),
                status_text,
                ft.Text("السجل:", size=14, weight=ft.FontWeight.BOLD),
                log_container,
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    def apply_theme(color_name):
        state["accent"] = color_name
        page.theme = ft.Theme(color_scheme_seed=THEME_COLORS[color_name])
        page.update()

    def on_color_change(e):
        apply_theme(e.control.value)

    color_radio = ft.RadioGroup(
        value=state["accent"],
        on_change=on_color_change,
        content=ft.Column(
            [ft.Radio(value=name, label=name) for name in THEME_COLORS.keys()],
            spacing=4,
        ),
    )

    def on_dark_mode_change(e):
        page.theme_mode = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
        page.update()

    dark_mode_switch = ft.Switch(label="الوضع الليلي (Dark Mode)", value=True, on_change=on_dark_mode_change)

    default_quality_dd = ft.Dropdown(
        label="الجودة الافتراضية",
        options=[ft.dropdown.Option(k) for k in QUALITY_OPTIONS.keys()],
        value=quality_dd.value,
        border_radius=12,
        filled=True,
    )

    default_lang_field = ft.TextField(
        label="لغة الترجمة الافتراضية",
        value="en",
        text_align=ft.TextAlign.RIGHT,
        border_radius=12,
        filled=True,
    )

    default_path_field = ft.TextField(
        label="مجلد الحفظ الافتراضي",
        value=DEFAULT_DIR,
        text_align=ft.TextAlign.RIGHT,
        border_radius=12,
        filled=True,
    )

    save_settings_msg = ft.Text("", size=12, color="#66BB6A")

    def save_settings(e):
        quality_dd.value = default_quality_dd.value
        sub_lang_field.value = default_lang_field.value
        path_field.value = default_path_field.value
        save_settings_msg.value = "✅ تم حفظ الإعدادات وتطبيقها على تبويب التحميل"
        page.update()

    save_settings_btn = ft.ElevatedButton(
        content=ft.Row(
            [ft.Text('💾', size=16), ft.Text("حفظ الإعدادات")],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        on_click=save_settings,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    settings_tab_content = ft.Container(
        padding=16,
        content=ft.Column(
            [
                ft.Card(
                    elevation=4,
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            [
                                ft.Text("مظهر التطبيق", size=16, weight=ft.FontWeight.BOLD),
                                dark_mode_switch,
                                ft.Text("لون التطبيق", size=14, weight=ft.FontWeight.W_600),
                                color_radio,
                            ],
                            spacing=10,
                        ),
                    ),
                ),
                ft.Card(
                    elevation=4,
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            [
                                ft.Text("القيم الافتراضية للتحميل", size=16, weight=ft.FontWeight.BOLD),
                                default_quality_dd,
                                default_lang_field,
                                default_path_field,
                                save_settings_btn,
                                save_settings_msg,
                            ],
                            spacing=10,
                        ),
                    ),
                ),
                ft.Card(
                    elevation=4,
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            [
                                ft.Text("المنصات المدعومة", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("✔ يوتيوب (فيديو + ترجمة)", size=13),
                                ft.Text("✔ تيك توك (فيديو فقط، بدون ترجمة عادة)", size=13),
                                ft.Text("✔ إنستجرام (فيديو/ريلز فقط، بدون ترجمة عادة)", size=13),
                                ft.Text(
                                    "المنصات المدعومة تعتمد على مكتبة yt-dlp، وقد تتغيّر مع تحديثات المواقع.",
                                    size=11,
                                    italic=True,
                                    color="#BDBDBD",
                                ),
                            ],
                            spacing=6,
                        ),
                    ),
                ),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(tab_content=ft.Text("⬇ تحميل"), content=download_tab_content),
            ft.Tab(tab_content=ft.Text("⚙ إعدادات"), content=settings_tab_content),
        ],
        expand=True,
    )

    page.appbar = ft.AppBar(
        title=ft.Text("محمّل الفيديوهات مع الترجمة"),
        center_title=False,
        bgcolor="#1E1E1E",
    )

    page.add(tabs)


class _YdlLogger:
    """يمرر رسائل yt-dlp إلى صندوق السجل بدل الطرفية"""

    def __init__(self, append_fn):
        self.append_fn = append_fn

    def debug(self, msg):
        if msg.startswith("[debug]"):
            return
        self.append_fn(msg + "\n")

    def info(self, msg):
        self.append_fn(msg + "\n")

    def warning(self, msg):
        self.append_fn("[WARN] " + msg + "\n")

    def error(self, msg):
        self.append_fn("[ERROR] " + msg + "\n")


if __name__ == "__main__":
    ft.app(target=main)