import os
import threading
import flet as ft
import yt_dlp

DEFAULT_DIR = "/storage/emulated/0/Download/course"

QUALITY_OPTIONS = {
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
    "أفضل جودة متاحة": "bestvideo+bestaudio/best",
}


def main(page: ft.Page):
    page.title = "محمّل يوتيوب + ترجمة"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 16
    page.rtl = True  # واجهة من اليمين لليسار

    url_field = ft.TextField(label="رابط الفيديو / البلاي ليست", text_align=ft.TextAlign.RIGHT)

    quality_dd = ft.Dropdown(
        label="الجودة",
        options=[ft.dropdown.Option(k) for k in QUALITY_OPTIONS.keys()],
        value=list(QUALITY_OPTIONS.keys())[0],
    )

    sub_lang_field = ft.TextField(
        label="لغة/لغات الترجمة (مثال: en,ar)", value="en", text_align=ft.TextAlign.RIGHT
    )

    auto_subs_switch = ft.Switch(label="تضمين الترجمة الآلية إذا لم توجد ترجمة رسمية", value=True)

    path_field = ft.TextField(label="مجلد الحفظ", value=DEFAULT_DIR, text_align=ft.TextAlign.RIGHT)

    log_box = ft.Text(value="", selectable=True, size=12, font_family="monospace")
    log_container = ft.Container(
        content=ft.Column([log_box], scroll=ft.ScrollMode.AUTO),
        height=260,
        bgcolor="#111111",
        padding=10,
        border_radius=8,
    )

    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
    status_text = ft.Text("", size=12)

    download_btn = ft.ElevatedButton(content=ft.Text("⬇ ابدأ التحميل"), width=400)

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
            status_text.value = "تمت معالجة ملف، جارٍ الدمج/الحفظ..."
            page.update()

    def run_download(url, fmt, sub_langs, want_auto_subs, save_dir):
        try:
            os.makedirs(save_dir, exist_ok=True)
            ydl_opts = {
                "format": fmt,
                "outtmpl": os.path.join(save_dir, "video %(playlist_index)s/%(title)s.%(ext)s"),
                "writesubtitles": True,
                "writeautomaticsub": want_auto_subs,
                "subtitleslangs": [s.strip() for s in sub_langs.split(",") if s.strip()],
                "subtitlesformat": "srt",
                "sleep_interval_requests": 2,
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
            args=(url, fmt, sub_langs, auto_subs_switch.value, save_dir),
            daemon=True,
        ).start()

    download_btn.on_click = start_download

    page.add(
        ft.Column(
            [
                ft.Text("محمّل يوتيوب مع الترجمة", size=22, weight=ft.FontWeight.BOLD),
                url_field,
                quality_dd,
                sub_lang_field,
                auto_subs_switch,
                path_field,
                ft.Row([download_btn, progress_ring]),
                status_text,
                ft.Text("السجل:", size=14, weight=ft.FontWeight.BOLD),
                log_container,
            ],
            spacing=12,
        )
    )


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