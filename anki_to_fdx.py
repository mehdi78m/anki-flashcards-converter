import csv
import html
import re
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "مبدل Anki به Flashcards Deluxe"


def clean_field(value):
    """پاک‌سازی HTML و تگ‌های صوتی/تصویری Anki."""
    if value is None:
        return ""

    value = value.replace("\ufeff", "")

    # حذف فایل‌های صوتی Anki
    value = re.sub(
        r"\[sound:[^\]]*\]",
        "",
        value,
        flags=re.IGNORECASE
    )

    # حذف تگ‌های تصویر
    value = re.sub(
        r"<img\b[^>]*>",
        "",
        value,
        flags=re.IGNORECASE
    )

    # تبدیل br به فاصله
    value = re.sub(
        r"<br\s*/?>",
        " ",
        value,
        flags=re.IGNORECASE
    )

    # حذف سایر تگ‌های HTML
    value = re.sub(
        r"</?[^>]+>",
        "",
        value
    )

    # تبدیل HTML entities مثل &nbsp;
    value = html.unescape(value)

    # حذف فاصله‌های ابتدا و انتها
    return value.strip()


def read_anki_file(input_file):
    """
    خواندن فایل Export شده از Anki.
    خروجی:
        [(word, english, persian), ...]
    """

    cards = []

    with open(
        input_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.reader(
            f,
            delimiter="\t",
            quotechar='"',
            doublequote=True
        )

        for row in reader:

            if not row:
                continue

            # خطوط Header انکی
            first = row[0].strip() if row else ""

            if first.startswith("#"):
                continue

            # حذف سطرهای کاملاً خالی
            if not any(cell.strip() for cell in row):
                continue

            # حداقل باید یک ستون داشته باشیم
            word = clean_field(row[0]) if len(row) >= 1 else ""
            english = clean_field(row[1]) if len(row) >= 2 else ""
            persian = clean_field(row[2]) if len(row) >= 3 else ""

            # اگر فایل از قبل دو ستونه باشد و ستون دوم | داشته باشد
            if len(row) == 2:
                if "|" in english:
                    parts = english.split("|", 1)
                    english = parts[0].strip()
                    persian = parts[1].strip()

            # کارت بدون Front قابل استفاده نیست
            if not word:
                continue

            cards.append(
                (word, english, persian)
            )

    return cards


def convert_anki_to_fdx(input_file, output_file):
    """
    تبدیل Export Anki به Basic Format مورد نیاز Flashcards Deluxe.
    
    خروجی:
        word<TAB>english|persian
    """

    cards = read_anki_file(input_file)

    converted = 0
    warnings = []

    with open(
        output_file,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        for index, (word, english, persian) in enumerate(cards, start=1):

            # اگر | داخل متن وجود داشته باشد ممکن است
            # ساختار Flashcards Deluxe را خراب کند.
            if "|" in english:
                warnings.append(
                    f"سطر {index}: علامت | در متن انگلیسی وجود داشت."
                )

            if "|" in persian:
                warnings.append(
                    f"سطر {index}: علامت | در متن فارسی وجود داشت."
                )

            # ساخت فرمت نهایی
            if persian:
                second_column = f"{english}|{persian}"
            else:
                second_column = english

            f.write(
                f"{word}\t{second_column}\n"
            )

            converted += 1

    return converted, warnings


def choose_input_file():
    file_path = filedialog.askopenfilename(
        title="انتخاب فایل Export شده از Anki",
        filetypes=[
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
    )

    if not file_path:
        return

    input_var.set(file_path)

    # تعیین خودکار فایل خروجی
    path = Path(file_path)

    output_path = path.with_name(
        path.stem + "_FlashcardsDeluxe.txt"
    )

    output_var.set(str(output_path))

    status_var.set(
        f"فایل انتخاب شد: {path.name}"
    )


def choose_output_file():
    file_path = filedialog.asksaveasfilename(
        title="انتخاب محل فایل خروجی",
        defaultextension=".txt",
        filetypes=[
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ],
        initialfile="FlashcardsDeluxe.txt"
    )

    if file_path:
        output_var.set(file_path)


def start_conversion():
    input_file = input_var.get().strip()
    output_file = output_var.get().strip()

    if not input_file:
        messagebox.showwarning(
            APP_TITLE,
            "ابتدا فایل Export شده از Anki را انتخاب کنید."
        )
        return

    if not output_file:
        messagebox.showwarning(
            APP_TITLE,
            "محل ذخیره فایل خروجی را انتخاب کنید."
        )
        return

    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        messagebox.showerror(
            APP_TITLE,
            "فایل ورودی پیدا نشد."
        )
        return

    try:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        count, warnings = convert_anki_to_fdx(
            input_path,
            output_path
        )

        status_var.set(
            f"تبدیل با موفقیت انجام شد — {count} کارت"
        )

        if warnings:
            messagebox.showwarning(
                APP_TITLE,
                f"{count} کارت تبدیل شد.\n\n"
                f"تعداد هشدارها: {len(warnings)}\n\n"
                "فایل خروجی ساخته شد، اما بعضی کارت‌ها "
                "دارای علامت | در متن بودند."
            )
        else:
            messagebox.showinfo(
                APP_TITLE,
                f"تبدیل با موفقیت انجام شد.\n\n"
                f"تعداد کارت‌ها: {count}\n\n"
                f"فایل خروجی:\n{output_path}"
            )

    except Exception as e:
        messagebox.showerror(
            APP_TITLE,
            "خطا هنگام تبدیل فایل:\n\n"
            + str(e)
        )

        status_var.set("خطا در تبدیل فایل")


def open_output_folder():
    output_file = output_var.get().strip()

    if not output_file:
        return

    path = Path(output_file)

    folder = path.parent

    if not folder.exists():
        folder = Path.cwd()

    try:
        import os
        os.startfile(folder)
    except Exception:
        messagebox.showinfo(
            APP_TITLE,
            f"محل فایل خروجی:\n{folder}"
        )


def main():
    global input_var
    global output_var
    global status_var

    root = tk.Tk()

    root.title(APP_TITLE)
    root.geometry("760x430")
    root.minsize(700, 390)

    # -------------------------
    # عنوان
    # -------------------------

    title = tk.Label(
        root,
        text="مبدل فایل Anki به Flashcards Deluxe",
        font=("Segoe UI", 18, "bold")
    )

    title.pack(
        pady=(25, 8)
    )

    subtitle = tk.Label(
        root,
        text="تبدیل Export متنی Anki به فرمت Basic",
        font=("Segoe UI", 11)
    )

    subtitle.pack(
        pady=(0, 20)
    )

    # -------------------------
    # متغیرها
    # -------------------------

    input_var = tk.StringVar()
    output_var = tk.StringVar()

    status_var = tk.StringVar(
        value="لطفاً فایل Export شده از Anki را انتخاب کنید."
    )

    # -------------------------
    # بخش ورودی
    # -------------------------

    input_frame = tk.Frame(root)

    input_frame.pack(
        fill="x",
        padx=35,
        pady=8
    )

    tk.Label(
        input_frame,
        text="فایل Anki:",
        width=15,
        anchor="e",
        font=("Segoe UI", 10)
    ).pack(
        side="left"
    )

    input_entry = tk.Entry(
        input_frame,
        textvariable=input_var,
        font=("Segoe UI", 10)
    )

    input_entry.pack(
        side="left",
        fill="x",
        expand=True,
        padx=10
    )

    tk.Button(
        input_frame,
        text="انتخاب فایل",
        width=14,
        command=choose_input_file
    ).pack(
        side="right"
    )

    # -------------------------
    # بخش خروجی
    # -------------------------

    output_frame = tk.Frame(root)

    output_frame.pack(
        fill="x",
        padx=35,
        pady=8
    )

    tk.Label(
        output_frame,
        text="فایل خروجی:",
        width=15,
        anchor="e",
        font=("Segoe UI", 10)
    ).pack(
        side="left"
    )

    output_entry = tk.Entry(
        output_frame,
        textvariable=output_var,
        font=("Segoe UI", 10)
    )

    output_entry.pack(
        side="left",
        fill="x",
        expand=True,
        padx=10
    )

    tk.Button(
        output_frame,
        text="انتخاب محل",
        width=14,
        command=choose_output_file
    ).pack(
        side="right"
    )

    # -------------------------
    # فرمت خروجی
    # -------------------------

    format_frame = tk.LabelFrame(
        root,
        text="فرمت خروجی",
        font=("Segoe UI", 10, "bold")
    )

    format_frame.pack(
        fill="x",
        padx=35,
        pady=20
    )

    format_text = (
        "کلمه<TAB>تعریف انگلیسی|ترجمه فارسی\n\n"
        "مثال:\n"
        "keen    sharp, intense, eager|تیز ، مشتاق ، شدید ، حساس"
    )

    tk.Label(
        format_frame,
        text=format_text,
        justify="left",
        anchor="w",
        font=("Consolas", 10)
    ).pack(
        padx=15,
        pady=12,
        anchor="w"
    )

    # -------------------------
    # دکمه‌ها
    # -------------------------

    button_frame = tk.Frame(root)

    button_frame.pack(
        pady=8
    )

    tk.Button(
        button_frame,
        text="تبدیل فایل",
        width=18,
        height=2,
        font=("Segoe UI", 11, "bold"),
        command=start_conversion
    ).pack(
        side="left",
        padx=8
    )

    tk.Button(
        button_frame,
        text="باز کردن پوشه خروجی",
        width=18,
        height=2,
        command=open_output_folder
    ).pack(
        side="left",
        padx=8
    )

    tk.Button(
        button_frame,
        text="خروج",
        width=12,
        height=2,
        command=root.destroy
    ).pack(
        side="left",
        padx=8
    )

    # -------------------------
    # وضعیت
    # -------------------------

    status = tk.Label(
        root,
        textvariable=status_var,
        font=("Segoe UI", 10),
        anchor="center"
    )

    status.pack(
        fill="x",
        padx=30,
        pady=(10, 15)
    )

    root.mainloop()


if __name__ == "__main__":

    # اگر برنامه با آرگومان اجرا شود،
    # حالت خط فرمان هم فعال خواهد بود.
    if len(sys.argv) >= 3:

        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])

        try:
            count, warnings = convert_anki_to_fdx(
                input_file,
                output_file
            )

            print(
                f"Conversion completed successfully: {count} cards"
            )

            if warnings:
                print(
                    f"Warnings: {len(warnings)}"
                )

        except Exception as e:
            print(
                f"ERROR: {e}"
            )
            sys.exit(1)

    else:
        main()
