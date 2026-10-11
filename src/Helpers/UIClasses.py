import os
import time
import tkinter as tk
import customtkinter as ui
from tkinter import filedialog
from PIL import Image, ImageTk
from Helpers.effects import EFFECTS, compute_state, blend_states, state_key, render_state

FONT = ("Segoe UI", 14, "bold")
BG = "#202020"
FIELD = "#2b2b2b"
FIELD_HOVER = "#3a3a3a"
BORDER = "#5b5a5c"
ACCENT = "#2370FF"
MUTED = "#8a8a8a"


def normal_font(size=13):
    return ui.CTkFont(family=FONT[0], size=size)


class Button(ui.CTkButton):
    def __init__(self, master, **kwargs):
        defaults = dict(
            corner_radius=7,
            fg_color="#52525b",
            hover_color="#5B5A5C",
            text_color="white",
            font=ui.CTkFont(family=FONT[0], size=FONT[1], weight=FONT[2]),
            height=36,
        )
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class AccentButton(Button):
    def __init__(self, master, **kwargs):
        defaults = dict(
            fg_color=FIELD,
            hover_color=FIELD_HOVER,
            border_width=1,
            border_color=ACCENT,
            height=28,
            font=normal_font(),
        )
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class IconButton(ui.CTkButton):
    def __init__(self, master, text="", **kwargs):
        defaults = dict(
            width=28,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color=FIELD_HOVER,
            text_color="white",
            font=normal_font(16),
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, **defaults)


class CheckBox(ui.CTkCheckBox):
    def __init__(self, master, text="", **kwargs):
        defaults = dict(
            corner_radius=6,
            checkbox_width=22,
            checkbox_height=22,
            border_width=2,
            fg_color=ACCENT,
            hover_color=FIELD_HOVER,
            border_color="#52525b",
            checkmark_color=BG,
            text_color="white",
            font=normal_font(),
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, **defaults)

    @property
    def checked(self) -> bool:
        return bool(self.get())

    @checked.setter
    def checked(self, value: bool):
        self.select() if value else self.deselect()


class Label(ui.CTkLabel):
    def __init__(self, master, text="", **kwargs):
        defaults = dict(
            text_color="white",
            font=normal_font(),
            anchor="w",
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, **defaults)


class Group(ui.CTkFrame):
    def __init__(self, master, title="", width=400, height=200, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=height, **kwargs)
        self.pack_propagate(False)
        self.body = ui.CTkFrame(
            self,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            corner_radius=6,
        )
        self.body.pack(fill="both", expand=True, pady=(9, 0))
        self.title = ui.CTkLabel(
            self,
            text=f" {title} ",
            fg_color=BG,
            text_color="white",
            font=normal_font(),
            height=18,
            corner_radius=0,
        )
        self.title.place(x=8, y=0)


class Entry(ui.CTkFrame):
    def __init__(self, master, text="", clearable=True, width=300, text_color="white", **kwargs):
        super().__init__(
            master,
            fg_color=FIELD,
            corner_radius=6,
            border_width=1,
            border_color=BORDER,
            width=width,
            height=30,
            **kwargs,
        )
        self.pack_propagate(False)
        self.var = ui.StringVar(value=text)
        self.entry = ui.CTkEntry(
            self,
            textvariable=self.var,
            fg_color=FIELD,
            border_width=0,
            text_color=text_color,
            font=normal_font(),
            height=26,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)
        if clearable:
            self.clear_button = ui.CTkButton(
                self,
                text="✕",
                width=20,
                height=20,
                corner_radius=10,
                fg_color="#d0d0d0",
                hover_color="white",
                text_color=BG,
                font=ui.CTkFont(family=FONT[0], size=11, weight="bold"),
                command=self.clear,
            )
            self.clear_button.pack(side="right", padx=5)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def clear(self):
        self.var.set("")


class ComboBox(ui.CTkFrame):
    ITEM_HOVER = "#3d3d3d"
    ITEM_SELECTED = "#333333"
    KEY_COLOR = "#010101"

    def __init__(self, master, values=None, width=300, command=None, **kwargs):
        super().__init__(
            master,
            fg_color=FIELD,
            corner_radius=6,
            border_width=1,
            border_color=BORDER,
            width=width,
            height=30,
            **kwargs,
        )
        self.pack_propagate(False)
        self.values = list(values or [""])
        self.command = command
        self.popup = None
        self.value = self.values[0]

        self.arrow = tk.Canvas(self, width=14, height=10, bg=FIELD, highlightthickness=0, bd=0)
        self.arrow.create_line(2, 3, 7, 8, 12, 3, fill="white", width=2, capstyle="round", joinstyle="round")
        self.arrow.pack(side="right", padx=(0, 10))

        self.label = ui.CTkLabel(self, text=self.value, anchor="w", text_color="white", font=normal_font())
        self.label.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=2)

        for widget in (self, self.label, self.arrow):
            widget.bind("<Button-1>", self.toggle)
            widget.bind("<Enter>", self._hover_on)
            widget.bind("<Leave>", self._hover_off)

        root = self.winfo_toplevel()
        root.bind("<Button-1>", self._on_root_click, add="+")
        root.bind("<Configure>", self._on_root_configure, add="+")

    def _set_bg(self, color):
        self.configure(fg_color=color)
        self.arrow.configure(bg=color)

    def _hover_on(self, event=None):
        self._set_bg(FIELD_HOVER)

    def _hover_off(self, event=None):
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if widget is None or not str(widget).startswith(str(self)):
            self._set_bg(FIELD)

    def _on_root_click(self, event):
        if self.popup is not None and not str(event.widget).startswith(str(self)):
            self.close()

    def _on_root_configure(self, event):
        if self.popup is not None and event.widget is self.winfo_toplevel():
            self.close()

    def toggle(self, event=None):
        if self.popup is not None:
            self.close()
        else:
            self.open()

    def open(self):
        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.configure(bg=self.KEY_COLOR)
        try:
            self.popup.attributes("-transparentcolor", self.KEY_COLOR)
        except tk.TclError:
            self.popup.configure(bg=BG)

        body = ui.CTkFrame(
            self.popup,
            fg_color=FIELD,
            border_width=1,
            border_color=BORDER,
            corner_radius=8,
        )
        body.pack(fill="both", expand=True)

        for i, value in enumerate(self.values):
            selected = value == self.value
            ui.CTkButton(
                body,
                text=value,
                anchor="w",
                height=26,
                corner_radius=5,
                fg_color=self.ITEM_SELECTED if selected else "transparent",
                hover_color=self.ITEM_HOVER,
                text_color=ACCENT if selected else "white",
                font=normal_font(),
                command=lambda v=value: self.choose(v),
            ).pack(
                fill="x",
                padx=4,
                pady=(4 if i == 0 else 1, 4 if i == len(self.values) - 1 else 0),
            )

        self.popup.update_idletasks()
        width = self.winfo_width()
        height = body.winfo_reqheight()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 1
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

    def close(self):
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None
        self._hover_off()

    def choose(self, value):
        self.set(value)
        self.close()
        if self.command:
            self.command(value)

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        self.label.configure(text=value)

    def set_values(self, values):
        self.values = list(values)
        if self.value not in self.values and self.values:
            self.set(self.values[0])


class SpinBox(ui.CTkFrame):
    def __init__(self, master, value=0, minimum=0, maximum=100, step=1, width=300, command=None, **kwargs):
        super().__init__(
            master,
            fg_color=FIELD,
            corner_radius=6,
            border_width=1,
            border_color=BORDER,
            width=width,
            height=30,
            **kwargs,
        )
        self.pack_propagate(False)
        self.minimum = minimum
        self.maximum = maximum
        self.increment = step
        self.command = command
        self.var = ui.StringVar(value=str(value))
        self.down_button = ui.CTkButton(
            self,
            text="▾",
            width=22,
            height=22,
            corner_radius=4,
            fg_color="transparent",
            hover_color=FIELD_HOVER,
            text_color="white",
            font=ui.CTkFont(size=16),
            command=lambda: self.change(-1),
        )
        self.up_button = ui.CTkButton(
            self,
            text="▴",
            width=22,
            height=22,
            corner_radius=4,
            fg_color="transparent",
            hover_color=FIELD_HOVER,
            text_color="white",
            font=ui.CTkFont(size=16),
            command=lambda: self.change(1),
        )
        self.down_button.pack(side="right", padx=(0, 4))
        self.up_button.pack(side="right")
        self.entry = ui.CTkEntry(
            self,
            textvariable=self.var,
            fg_color=FIELD,
            border_width=0,
            text_color="white",
            font=normal_font(),
            height=26,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)
        self.entry.bind("<FocusOut>", lambda e: self.set(self.get()))
        self.entry.bind("<Return>", lambda e: self.set(self.get()))
        self.set(value)

    def get(self):
        try:
            return int(self.var.get())
        except ValueError:
            return self.minimum

    def set(self, value):
        value = max(self.minimum, min(self.maximum, int(value)))
        self.var.set(str(value))

    def change(self, direction):
        self.set(self.get() + direction * self.increment)
        if self.command:
            self.command(self.get())


class Slider(ui.CTkFrame):
    def __init__(self, master, value=50, minimum=0, maximum=100, suffix="%", width=300, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=24, **kwargs)
        self.pack_propagate(False)
        self.suffix = suffix
        self.command = command
        self.label = ui.CTkLabel(
            self,
            text="",
            width=48,
            anchor="e",
            text_color="white",
            font=normal_font(),
        )
        self.label.pack(side="right")
        self.slider = ui.CTkSlider(
            self,
            from_=minimum,
            to=maximum,
            number_of_steps=maximum - minimum,
            fg_color=BORDER,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color="white",
            command=self.changed,
        )
        self.slider.pack(side="left", fill="x", expand=True)
        self.set(value)

    def changed(self, value):
        self.label.configure(text=f"{int(value)}{self.suffix}")
        if self.command:
            self.command(int(value))

    def get(self):
        return int(self.slider.get())

    def set(self, value):
        self.slider.set(value)
        self.label.configure(text=f"{int(value)}{self.suffix}")


class AssetManager(ui.CTkFrame):
    THUMB = 44
    ROW_BG = "#333333"
    DELETE_HOVER = "#7a2d2d"

    def __init__(self, master, width=410, height=170, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=height, **kwargs)
        self.pack_propagate(False)
        self.command = command
        self.rows = {}

        bar = ui.CTkFrame(self, fg_color="transparent")
        bar.pack(side="bottom", fill="x", pady=(4, 0))
        self.import_button = IconButton(bar, text="📁", command=self.browse)
        self.import_button.pack(side="left")
        self.counter = ui.CTkLabel(bar, text="0 assets", text_color=MUTED, font=normal_font(12))
        self.counter.pack(side="left", padx=6)

        self.area = ui.CTkScrollableFrame(self, fg_color=FIELD, corner_radius=6)
        self.area.pack(side="top", fill="both", expand=True)

        self.empty = ui.CTkLabel(self.area, text="No assets imported", text_color=MUTED, font=normal_font())
        self.empty.pack(pady=30)

    def browse(self):
        paths = filedialog.askopenfilenames(
            title="Import PNG",
            filetypes=[("PNG images", "*.png")],
        )
        for path in paths:
            self.add(path, notify=False)
        if paths and self.command:
            self.command(self.get())

    def _thumbnail(self, path):
        size = self.THUMB
        try:
            img = Image.open(path).convert("RGBA")
        except Exception:
            return None
        img.thumbnail((size, size))
        tile = Image.new("RGBA", (size, size), (31, 31, 31, 255))
        tile.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
        return ui.CTkImage(light_image=tile, dark_image=tile, size=(size, size))

    @staticmethod
    def _short(path, limit=42):
        if len(path) <= limit:
            return path
        return path[:12] + "…" + path[-(limit - 13):]

    def add(self, path, notify=True):
        path = os.path.normpath(path)
        if path in self.rows or not os.path.isfile(path):
            return

        self.empty.pack_forget()

        row = ui.CTkFrame(self.area, fg_color=self.ROW_BG, corner_radius=6)
        row.pack(fill="x", pady=(0, 4))

        thumb = ui.CTkLabel(row, text="", image=self._thumbnail(path), width=self.THUMB, height=self.THUMB)
        thumb.pack(side="left", padx=6, pady=6)

        delete = ui.CTkButton(
            row,
            text="✕",
            width=26,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=self.DELETE_HOVER,
            text_color="white",
            font=normal_font(13),
            command=lambda p=path: self.remove(p),
        )
        delete.pack(side="right", padx=6)

        info = ui.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ui.CTkLabel(
            info,
            text=os.path.basename(path),
            anchor="w",
            text_color="white",
            font=ui.CTkFont(family=FONT[0], size=13, weight="bold"),
        ).pack(fill="x")
        ui.CTkLabel(
            info,
            text=self._short(path),
            anchor="w",
            text_color=MUTED,
            font=normal_font(11),
        ).pack(fill="x")

        self.rows[path] = row
        self._refresh(notify)

    def remove(self, path, notify=True):
        row = self.rows.pop(path, None)
        if row is not None:
            row.destroy()
        self._refresh(notify)

    def clear(self):
        for path in list(self.rows):
            self.remove(path, notify=False)
        self._refresh(True)

    def _refresh(self, notify=True):
        count = len(self.rows)
        self.counter.configure(text=f"{count} asset{'s' if count != 1 else ''}")
        if count == 0:
            self.empty.pack(pady=30)
        if notify and self.command:
            self.command(self.get())

    def get(self):
        return list(self.rows)


class LevelMeter(tk.Canvas):
    OPEN_COLOR = ACCENT
    CLOSED_COLOR = "#6b6b6b"

    def __init__(self, master, width=217, height=10, threshold=0.15, **kwargs):
        super().__init__(master, width=width, height=height, bg=BG, highlightthickness=0, bd=0, **kwargs)
        self.w = width
        self.h = height
        self.create_rectangle(0, 0, width, height, fill=BORDER, outline="")
        self.fill = self.create_rectangle(0, 0, 0, height, fill=self.CLOSED_COLOR, outline="")
        self.marker = self.create_rectangle(0, -2, 2, height + 2, fill="white", outline="")
        self.set_threshold(threshold)

    def set_level(self, level, is_open=False):
        level = max(0.0, min(1.0, level))
        self.coords(self.fill, 0, 0, self.w * level, self.h)
        self.itemconfigure(self.fill, fill=self.OPEN_COLOR if is_open else self.CLOSED_COLOR)

    def set_threshold(self, threshold):
        x = max(0, min(self.w - 2, self.w * threshold))
        self.coords(self.marker, x, 0, x + 2, self.h)


class AvatarPreview(ui.CTkFrame):
    BLEND_TIME = 0.12

    def __init__(self, master, width=296, height=368, on_frame=None, **kwargs):
        super().__init__(master, fg_color=FIELD, corner_radius=6, width=width, height=height, **kwargs)
        self.on_frame = on_frame
        self.pack_propagate(False)
        self.box = (width - 20, height - 20)
        self.bases = {}
        self.cache = {}
        self.photo = None
        self.mode = None
        self.last_state = None
        self.prev_state = None
        self.blend_start = 0.0
        self.last_key = None

        self.canvas = tk.Canvas(self, width=self.box[0], height=self.box[1], bg=FIELD, highlightthickness=0, bd=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", state="hidden")
        self.text_id = self.canvas.create_text(
            self.box[0] / 2, self.box[1] / 2, text="No image", fill=MUTED, font=(FONT[0], 11)
        )

    def show(self, path, effects=None, mode=None):
        effects = effects or []
        if not path:
            if self.last_key is not None:
                self.last_key = None
                self.canvas.itemconfigure(self.image_id, state="hidden")
                self.canvas.itemconfigure(self.text_id, state="normal")
            return

        base = self._base(path)
        if base is None:
            return

        now = time.monotonic()
        state = compute_state(effects, now)

        if mode != self.mode:
            self.prev_state = self.last_state
            self.blend_start = now
            self.mode = mode
        if self.prev_state is not None:
            a = (now - self.blend_start) / self.BLEND_TIME
            if a >= 1:
                self.prev_state = None
            else:
                a = a * a * (3 - 2 * a)
                state = blend_states(self.prev_state, state, a)
        self.last_state = state

        key = (path, state_key(state))
        if key == self.last_key:
            return
        self.last_key = key

        img = render_state(base, self.box, state, self.cache)
        if self.on_frame:
            self.on_frame(img)
        if self.photo is None:
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfigure(self.image_id, image=self.photo)
        else:
            self.photo.paste(img)
        self.canvas.itemconfigure(self.image_id, state="normal")
        self.canvas.itemconfigure(self.text_id, state="hidden")

    def _base(self, path):
        if path not in self.bases:
            try:
                img = Image.open(path).convert("RGBA")
            except Exception:
                return None
            r = min(self.box[0] * 0.8 / img.width, self.box[1] * 0.8 / img.height)
            img = img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)
            self.bases[path] = img
        return self.bases[path]


class PopupMenu:
    KEY_COLOR = "#010101"

    def __init__(self, anchor, command, width=190):
        self.anchor = anchor
        self.command = command
        self.width = width
        self.popup = None
        root = anchor.winfo_toplevel()
        root.bind("<Button-1>", self._on_root_click, add="+")
        root.bind("<Configure>", self._on_root_configure, add="+")

    def is_open(self):
        return self.popup is not None

    def _on_root_click(self, event):
        if self.popup is not None and not str(event.widget).startswith(str(self.anchor)):
            self.close()

    def _on_root_configure(self, event):
        if self.popup is not None and event.widget is self.anchor.winfo_toplevel():
            self.close()

    def open(self, values):
        self.close()
        self.popup = tk.Toplevel(self.anchor)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.configure(bg=self.KEY_COLOR)
        try:
            self.popup.attributes("-transparentcolor", self.KEY_COLOR)
        except tk.TclError:
            self.popup.configure(bg=BG)

        body = ui.CTkFrame(self.popup, fg_color=FIELD, border_width=1, border_color=BORDER, corner_radius=8)
        body.pack(fill="both", expand=True)

        if len(values) > 8:
            container = ui.CTkScrollableFrame(body, fg_color="transparent", corner_radius=0, height=8 * 28)
            container.pack(fill="both", expand=True, padx=2, pady=4)
        else:
            container = ui.CTkFrame(body, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=2, pady=4)

        if not values:
            ui.CTkLabel(container, text="All effects added", text_color=MUTED, font=normal_font()).pack(padx=10, pady=4)
        for value in values:
            ui.CTkButton(
                container,
                text=value,
                anchor="w",
                height=26,
                corner_radius=5,
                fg_color="transparent",
                hover_color="#3d3d3d",
                text_color="white",
                font=normal_font(),
                command=lambda v=value: self.pick(v),
            ).pack(fill="x", padx=4, pady=1)

        self.popup.update_idletasks()
        height = body.winfo_reqheight()
        x = self.anchor.winfo_rootx() + self.anchor.winfo_width() - self.width
        y = self.anchor.winfo_rooty() + self.anchor.winfo_height() + 2
        if y + height > self.popup.winfo_screenheight() - 40:
            y = self.anchor.winfo_rooty() - height - 2
        self.popup.geometry(f"{self.width}x{height}+{x}+{y}")

    def pick(self, value):
        self.close()
        self.command(value)

    def close(self):
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None


class EffectStack(ui.CTkFrame):
    ROW_BG = "#333333"

    def __init__(self, master, title="", width=408, height=160, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=height, **kwargs)
        self.pack_propagate(False)
        self.command = command
        self.cards = []

        header = ui.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x")
        ui.CTkLabel(
            header,
            text=title,
            text_color="white",
            font=ui.CTkFont(family=FONT[0], size=13, weight="bold"),
        ).pack(side="left")
        self.add_button = IconButton(
            header, text="+", fg_color=FIELD, border_width=1, border_color=BORDER,
            font=normal_font(18), command=self._toggle_menu,
        )
        self.add_button.pack(side="right")

        self.area = ui.CTkScrollableFrame(self, fg_color=FIELD, corner_radius=6)
        self.area.pack(side="top", fill="both", expand=True, pady=(4, 0))
        self.empty = ui.CTkLabel(self.area, text="None", text_color=MUTED, font=normal_font())
        self.empty.pack(pady=14)

        self.menu = PopupMenu(self.add_button, self.add)

    def _toggle_menu(self):
        if self.menu.is_open():
            self.menu.close()
        else:
            used = self.names()
            self.menu.open([n for n in EFFECTS if n not in used])

    def _changed(self, _=None):
        if self.command:
            self.command(self.get())

    def names(self):
        return [c["name"] for c in self.cards]

    def add(self, name, values=None):
        if name not in EFFECTS or name in self.names():
            return
        values = values or {}
        self.empty.pack_forget()

        card = ui.CTkFrame(self.area, fg_color=self.ROW_BG, corner_radius=6)
        card.pack(fill="x", pady=(0, 4))

        top = ui.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(4, 0))
        ui.CTkLabel(
            top, text=name, anchor="w", text_color="white",
            font=ui.CTkFont(family=FONT[0], size=13, weight="bold"),
        ).pack(side="left")
        ui.CTkButton(
            top, text="✕", width=22, height=22, corner_radius=6,
            fg_color="transparent", hover_color="#7a2d2d", text_color="white",
            font=normal_font(12), command=lambda n=name: self.remove(n),
        ).pack(side="right")

        sliders = {}
        for key, label, lo, hi, default, suffix in EFFECTS[name]["params"]:
            row = ui.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=(0, 4))
            ui.CTkLabel(row, text=label, width=80, anchor="w", text_color=MUTED, font=normal_font(12)).pack(side="left")
            slider = Slider(row, value=values.get(key, default), minimum=lo, maximum=hi,
                            suffix=suffix, width=240, command=self._changed)
            slider.pack(side="left", fill="x", expand=True)
            sliders[key] = slider

        self.cards.append({"name": name, "frame": card, "sliders": sliders})
        self._changed()

    def remove(self, name):
        for card in self.cards:
            if card["name"] == name:
                card["frame"].destroy()
                self.cards.remove(card)
                break
        if not self.cards:
            self.empty.pack(pady=14)
        self._changed()

    def clear(self):
        for card in self.cards:
            card["frame"].destroy()
        self.cards = []
        self.empty.pack(pady=14)
        self._changed()

    def get(self):
        return [(c["name"], {k: s.get() for k, s in c["sliders"].items()}) for c in self.cards]

    def set(self, data):
        self.clear()
        for name, values in data:
            self.add(name, values)
class ToggleButton(Button):
    OFF_COLOR = "#52525b"
    OFF_HOVER = "#5B5A5C"
    ON_COLOR = "#dc2626"
    ON_HOVER = "#b91c1c"

    def __init__(
        self,
        master,
        text_off="Start",
        text_on="Stop",
        command_off=None,
        command_on=None,
        state=False,
        **kwargs,
    ):
        self.text_off = text_off
        self.text_on = text_on
        self.command_off = command_off
        self.command_on = command_on
        self.active = bool(state)
        super().__init__(master, text=text_off, command=self._toggle, **kwargs)
        self._refresh_look()

    def _refresh_look(self):
        if self.active:
            self.configure(text=self.text_on, fg_color=self.ON_COLOR, hover_color=self.ON_HOVER)
        else:
            self.configure(text=self.text_off, fg_color=self.OFF_COLOR, hover_color=self.OFF_HOVER)

    def _toggle(self):
        self.set(not self.active, run=True)

    def set(self, value, run=False):
        self.active = bool(value)
        self._refresh_look()
        if run:
            callback = self.command_on if self.active else self.command_off
            if callback:
                callback()

    def get(self):
        return self.active