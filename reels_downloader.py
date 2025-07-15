import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel
import os
import threading
import yt_dlp
import requests
from PIL import Image, ImageTk
import io

ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_path

download_folder = None
format_map = {}


def select_folder():
    global download_folder
    folder = filedialog.askdirectory()
    if folder:
        download_folder = folder
        folder_label.config(text=f"📁 {download_folder}")


def format_duration(seconds):
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins} dakika {secs} saniye"


def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extractaudio': False,
        'format': 'best',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def prepare_video():
    raw = url_text.get("1.0", "end").strip()
    urls = [u.strip() for u in raw.replace(",", "\n").split("\n") if u.strip()]
    if not urls:
        messagebox.showerror("Hata", "Lütfen bir bağlantı girin.")
        return

    url = urls[0]
    status_label.config(text="🔍 Video bilgisi alınıyor...")
    download_button.config(state="disabled")
    root.update_idletasks()

    def worker():
        try:
            info = get_video_info(url)
            open_popup(info, url)
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            status_label.config(text="❌ Bilgi alınamadı.")
        finally:
            download_button.config(state="normal")

    threading.Thread(target=worker).start()


def open_popup(info, url):
    popup = Toplevel(root)
    popup.title("Video Seçimi")
    popup.geometry("440x500")

    if info.get("thumbnail"):
        try:
            r = requests.get(info['thumbnail'])
            img = Image.open(io.BytesIO(r.content))
            img.thumbnail((380, 210))
            photo = ImageTk.PhotoImage(img)
            thumb_label = tk.Label(popup, image=photo)
            thumb_label.image = photo
            thumb_label.pack(pady=5)
        except:
            pass

    tk.Label(popup, text="🎨 " + info.get("title", ""), wraplength=400).pack()
    tk.Label(popup, text="⏱ Süre: " + format_duration(info.get("duration", 0))).pack(pady=2)
    tk.Label(popup, text="📥 Kalite Seçin:").pack()

    quality_combo = ttk.Combobox(popup, state="readonly", width=52)
    quality_combo.pack(pady=5)

    global format_map
    format_map = {}
    options = []

    target_resolutions = [2160, 1080, 720, 480, 360]

    available_formats = {}
    best_audio = None

    try:
        for fmt in info.get('formats', []):
            if not fmt:
                continue
            acodec = fmt.get("acodec", "none")
            vcodec = fmt.get("vcodec", "none")
            ext = fmt.get("ext", "")

            # Sadece ses formatları
            if acodec != "none" and vcodec == "none":
                if ext in ["m4a", "aac", "mp3"] or not best_audio:
                    best_audio = fmt
                    if ext == "m4a":
                        break

        for fmt in info.get('formats', []):
            if not fmt:
                continue

            vcodec = fmt.get("vcodec", "none")
            acodec = fmt.get("acodec", "none")
            height = fmt.get("height", 0)
            ext = fmt.get("ext", "")
            format_id = fmt.get("format_id", "")

            if vcodec != "none" and height and format_id:
                if height not in available_formats or ext == "mp4":
                    size = fmt.get("filesize") or fmt.get("filesize_approx", 0)
                    size_mb = f"{round(size / (1024 * 1024), 2)} MB" if size else "?.?? MB"

                    available_formats[height] = {
                        'format_id': format_id,
                        'ext': ext,
                        'has_audio': acodec != "none",
                        'size': size_mb,
                        'format': fmt
                    }

    except Exception as e:
        print(f"Format parsing error: {e}")

    options = []
    for resolution in target_resolutions:
        if resolution in available_formats:
            fmt_info = available_formats[resolution]
            if fmt_info['has_audio']:
                label = f"{resolution}p - Sesli - {fmt_info['size']}"
                format_map[label] = fmt_info['format_id']
            else:
                if best_audio:
                    combined_id = f"{fmt_info['format_id']}+{best_audio['format_id']}"
                    label = f"{resolution}p - Sesli (Birleştirilecek) - {fmt_info['size']}"
                    format_map[label] = combined_id
                else:
                    label = f"{resolution}p - Sessiz - {fmt_info['size']}"
                    format_map[label] = fmt_info['format_id']
            options.append(label)
        else:
            closest_resolution = None
            min_diff = float('inf')

            for available_res in available_formats.keys():
                if available_res <= resolution:
                    diff = resolution - available_res
                    if diff < min_diff:
                        min_diff = diff
                        closest_resolution = available_res

            if closest_resolution:
                fmt_info = available_formats[closest_resolution]
                if fmt_info['has_audio']:
                    label = f"{resolution}p (Mevcut: {closest_resolution}p) - Sesli - {fmt_info['size']}"
                    format_map[label] = fmt_info['format_id']
                else:
                    if best_audio:
                        combined_id = f"{fmt_info['format_id']}+{best_audio['format_id']}"
                        label = f"{resolution}p (Mevcut: {closest_resolution}p) - Sesli (Birleştirilecek) - {fmt_info['size']}"
                        format_map[label] = combined_id
                    else:
                        label = f"{resolution}p (Mevcut: {closest_resolution}p) - Sessiz - {fmt_info['size']}"
                        format_map[label] = fmt_info['format_id']
                options.append(label)
            else:
                fallback_label = f"{resolution}p - Mevcut Değil"
                fallback_format = f"best[height<={resolution}][ext=mp4]/best[height<={resolution}]/best"
                format_map[fallback_label] = fallback_format
                options.append(fallback_label)

    if not options:
        options = ["En İyi Kalite (mp4)"]
        format_map["En İyi Kalite (mp4)"] = "best"

    quality_combo["values"] = options
    quality_combo.current(0)

    def start_download():
        if not download_folder:
            messagebox.showerror("Hata", "Lütfen klasör seçin.")
            return

        selection = quality_combo.get()
        format_selector = format_map.get(selection, "best")
        chosen_format = format_choice.get()

        status_label.config(text="⬇️ İndirme başlatıldı...")
        download_button.config(state="disabled")
        progress_bar.start()

        def run():
            try:
                ydl_opts = {
                    'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                    'format': format_selector,
                    'merge_output_format': 'mp4',
                    'postprocessors': [],
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0'
                    },
                    'force_ipv4': True,
                }

                if chosen_format == "mp3":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    })

                elif "+" in format_selector:
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                status_label.config(text="✅ İndirme tamamlandı!", foreground="green")

            except Exception as e:
                status_label.config(text="❌ İndirme hatası!", foreground="red")
                messagebox.showerror("İndirme Hatası", str(e))
            finally:
                progress_bar.stop()
                download_button.config(state="normal")
                popup.destroy()

        threading.Thread(target=run).start()

    tk.Label(popup, text="🎵 Format Seçimi:").pack(pady=(10, 0))
    format_choice = tk.StringVar(value="mp4")
    mp4_radio = ttk.Radiobutton(popup, text="MP4 (Video)", variable=format_choice, value="mp4")
    mp3_radio = ttk.Radiobutton(popup, text="MP3 (Ses)", variable=format_choice, value="mp3")
    mp4_radio.pack()
    mp3_radio.pack()


    def start_download():
        if not download_folder:
            messagebox.showerror("Hata", "Lütfen klasör seçin.")
            return

        selection = quality_combo.get()
        format_selector = format_map.get(selection, "best")
        chosen_format = format_choice.get()

        popup.destroy()
        status_label.config(text="⬇️ İndirme başlatıldı...")
        download_button.config(state="disabled")
        progress_bar.start()

        def run():
            try:
                ydl_opts = {
                    'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                    'format': format_selector,
                    'merge_output_format': 'mp4',
                    'postprocessors': [],
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0'
                    },
                    'force_ipv4': True,

                }
                if "instagram.com" in url:
                    ydl_opts["format"] = "http_mp4_720_url/http_mp4_360_url/best"
                elif "tiktok.com" in url:
                    ydl_opts["format"] = "mp4"
                elif "twitter.com" in url or "x.com" in url:
                    ydl_opts["format"] = "bestvideo+bestaudio/best"

                if chosen_format == "mp3":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    })

                elif "+" in format_selector:
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                status_label.config(text="✅ İndirme tamamlandı!", foreground="green")

            except Exception as e:
                status_label.config(text="❌ İndirme hatası!", foreground="red")
                messagebox.showerror("İndirme Hatası", str(e))
            finally:
                progress_bar.stop()
                download_button.config(state="normal")

        threading.Thread(target=run).start()

    tk.Button(popup, text="📥 İndir", command=start_download).pack(pady=10)


root = tk.Tk()
root.title("Video Downloader")
root.geometry("540x420")
root.resizable(False, False)

tk.Label(root, text="🎞 Video Linkini Gir (YouTube/Instagram):").pack(pady=5)
url_text = tk.Text(root, height=3, width=62)
url_text.pack()

tk.Button(root, text="📁 Klasör Seç", command=select_folder).pack(pady=5)
folder_label = tk.Label(root, text="Klasör seçilmedi.", fg="gray")
folder_label.pack()

download_button = tk.Button(root, text="🔍 Videoyu Algıla", command=prepare_video)
download_button.pack(pady=10)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack(pady=5)
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="indeterminate", length=400)
progress_bar.pack(pady=5)


def update_ytdlp():
    status_label.config(text="🔄 yt-dlp güncelleniyor...")

    def update_worker():
        try:
            import subprocess
            result = subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                status_label.config(text="✅ yt-dlp güncellendi!", foreground="green")
            else:
                status_label.config(text="❌ Güncelleme başarısız!", foreground="red")
        except Exception as e:
            status_label.config(text="❌ Güncelleme hatası!", foreground="red")

    threading.Thread(target=update_worker).start()


tk.Button(root, text="yt-dlp Güncelle", command=update_ytdlp).pack(pady=5)

root.mainloop()