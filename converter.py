import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

QUALITY_DEFAULT = 92
SUBSAMPLING_H2V2 = 2  # 0=4:4:4, 1=4:2:2, 2=4:2:0(H2V2)

def is_jpg(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in (".jpg", ".jpeg")

def convert_one(path: str, quality: int = QUALITY_DEFAULT, progressive: bool = False):
    try:
        with Image.open(path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")

            tmp_path = path + ".__tmp__.jpg"
            save_kwargs = dict(
                format="JPEG",
                quality=quality,
                subsampling=SUBSAMPLING_H2V2,  # 핵심: H2V2 강제
                optimize=True,
            )
            if progressive:
                save_kwargs["progressive"] = True

            im.save(
    tmp_path,
    dpi=(300, 300),
    **save_kwargs
)


        os.replace(tmp_path, path)
        return True, "OK"
    except Exception as e:
        try:
            tmp = path + ".__tmp__.jpg"
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False, f"{type(e).__name__}: {e}"

def collect_jpgs_from_folder(folder: str):
    files = []
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and is_jpg(p):
            files.append(p)
    files.sort()
    return files

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JPG H2V2 변환기")
        self.geometry("520x360")
        self.resizable(False, False)

        self.selected_files = []

        tk.Label(
            self,
            text="JPG를 H2V2(4:2:0) 형식으로 변환합니다.\n(원본 파일을 덮어씁니다)",
            justify="left",
        ).pack(pady=12)

        opt = tk.Frame(self); opt.pack(pady=6)

        tk.Label(opt, text="품질(quality):").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self.quality_var = tk.IntVar(value=QUALITY_DEFAULT)
        tk.Entry(opt, textvariable=self.quality_var, width=6).grid(row=0, column=1, sticky="w", padx=6, pady=4)

        self.progressive_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opt, text="Progressive JPEG(점진 로딩)", variable=self.progressive_var).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=6, pady=4
        )

        btn = tk.Frame(self); btn.pack(pady=10)
        tk.Button(btn, text="파일 선택", width=14, command=self.pick_files).grid(row=0, column=0, padx=8)
        tk.Button(btn, text="폴더 선택", width=14, command=self.pick_folder).grid(row=0, column=1, padx=8)
        tk.Button(btn, text="변환 시작", width=14, command=self.run_convert).grid(row=0, column=2, padx=8)

        self.list_box = tk.Listbox(self, width=78, height=10)
        self.list_box.pack(pady=8)

        self.status_var = tk.StringVar(value="대기 중")
        tk.Label(self, textvariable=self.status_var, anchor="w").pack(fill="x", padx=12, pady=6)

    def pick_files(self):
        paths = filedialog.askopenfilenames(
            title="JPG 파일 선택",
            filetypes=[("JPEG files", "*.jpg *.jpeg"), ("All files", "*.*")]
        )
        if not paths:
            return
        self.selected_files = [p for p in paths if is_jpg(p)]
        self.refresh_list()

    def pick_folder(self):
        folder = filedialog.askdirectory(title="JPG가 있는 폴더 선택")
        if not folder:
            return
        self.selected_files = collect_jpgs_from_folder(folder)
        self.refresh_list()

    def refresh_list(self):
        self.list_box.delete(0, tk.END)
        for p in self.selected_files:
            self.list_box.insert(tk.END, os.path.basename(p))
        self.status_var.set(f"선택된 파일: {len(self.selected_files)}개")

    def run_convert(self):
        if not self.selected_files:
            messagebox.showwarning("알림", "먼저 JPG 파일 또는 폴더를 선택하세요.")
            return

        try:
            q = int(self.quality_var.get())
            if not (1 <= q <= 100):
                raise ValueError
        except Exception:
            messagebox.showerror("오류", "품질(quality)은 1~100 사이 숫자여야 합니다.")
            return

        prog = bool(self.progressive_var.get())

        if not messagebox.askokcancel("확인", "원본 JPG 파일을 덮어씁니다.\n계속 진행할까요?"):
            return

        ok_count = 0
        fail_count = 0
        failed = []

        total = len(self.selected_files)
        for idx, path in enumerate(self.selected_files, start=1):
            self.status_var.set(f"변환 중... ({idx}/{total}) {os.path.basename(path)}")
            self.update_idletasks()

            ok, msg = convert_one(path, quality=q, progressive=prog)
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                failed.append((path, msg))

        if fail_count == 0:
            messagebox.showinfo("완료", f"변환 완료!\n성공: {ok_count}개\n실패: {fail_count}개")
        else:
            preview = "\n".join([f"- {os.path.basename(p)}: {m}" for p, m in failed[:8]])
            if len(failed) > 8:
                preview += f"\n... 외 {len(failed)-8}개"
            messagebox.showwarning("완료(일부 실패)", f"성공: {ok_count}개\n실패: {fail_count}개\n\n실패 내역:\n{preview}")

        self.status_var.set("대기 중")

if __name__ == "__main__":
    try:
        App().mainloop()
    except KeyboardInterrupt:
        sys.exit(0)

