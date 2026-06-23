from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
import pyotp
import time

# Цветовая палитра
BG_DARK = (0.04, 0.02, 0.08, 1)
PANEL = (0.18, 0.08, 0.28, 0.55)
ACCENT = (0.55, 0.25, 0.75, 1)
ACCENT_DARK = (0.35, 0.15, 0.5, 1)
TEXT_LIGHT = (0.92, 0.88, 1, 1)
CODE_COLOR = (0.95, 0.55, 0.95, 1)


class RootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Сплошная тёмно-фиолетовая подложка
        with self.canvas.before:
            Color(*BG_DARK)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Едва видное фоновое изображение
        self.bg_image = Image(
            source="background.jpg",
            allow_stretch=True,
            keep_ratio=False,
            opacity=0.16,
            size_hint=(1, 1),
        )
        self.add_widget(self.bg_image)

        # Контент сверху — по центру, размер по содержимому
        self.content = TOTPContent()
        self.add_widget(self.content)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class TOTPContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(12), **kwargs)
        self.totp = None

        self.size_hint = (0.92, 0.75)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        title = Label(
            text="TOTP Generator",
            font_size=26,
            bold=True,
            color=TEXT_LIGHT,
            size_hint=(1, None),
            height=50,
        )
        self.add_widget(title)

        # Строка: поле ключа + кнопка "Вставить"
        input_row = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=55, spacing=10
        )
        self.secret_input = TextInput(
            hint_text="Введи секретный ключ 2FA",
            multiline=False,
            password=True,
            size_hint=(0.7, 1),
            background_color=(0.12, 0.06, 0.18, 0.85),
            foreground_color=TEXT_LIGHT,
            hint_text_color=(0.6, 0.5, 0.7, 1),
            cursor_color=ACCENT,
            padding=[15, 15, 15, 15],
        )
        input_row.add_widget(self.secret_input)

        self.paste_button = Button(
            text="Вставить",
            size_hint=(0.3, 1),
            background_normal="",
            background_color=ACCENT_DARK,
            color=TEXT_LIGHT,
            font_size=14,
        )
        self.paste_button.bind(on_press=self.paste_secret)
        input_row.add_widget(self.paste_button)

        self.add_widget(input_row)

        self.start_button = Button(
            text="Старт",
            size_hint=(1, None),
            height=60,
            background_normal="",
            background_color=ACCENT,
            color=(1, 1, 1, 1),
            bold=True,
            font_size=18,
        )
        self.start_button.bind(on_press=self.start)
        self.add_widget(self.start_button)

        # Карточка под кодом
        self.card = FloatLayout(size_hint=(1, 1))
        with self.card.canvas.before:
            Color(*PANEL)
            self.card_rect = RoundedRectangle(pos=self.card.pos, size=self.card.size, radius=[20])
        self.card.bind(pos=self._update_card, size=self._update_card)

        self.code_label = Label(
            text="",
            font_size=52,
            bold=True,
            color=CODE_COLOR,
            size_hint=(1, 0.7),
            pos_hint={"x": 0, "top": 1},
        )
        self.card.add_widget(self.code_label)

        self.timer_label = Label(
            text="",
            font_size=16,
            color=(0.75, 0.65, 0.85, 1),
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0},
        )
        self.card.add_widget(self.timer_label)

        self.add_widget(self.card)

        # Строка: "Скопировать код" + "Очистить ключ"
        action_row = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=50, spacing=10
        )
        self.copy_button = Button(
            text="Скопировать код",
            size_hint=(0.5, 1),
            background_normal="",
            background_color=ACCENT_DARK,
            color=TEXT_LIGHT,
            font_size=14,
        )
        self.copy_button.bind(on_press=self.copy_code)
        action_row.add_widget(self.copy_button)

        self.clear_button = Button(
            text="Очистить ключ",
            size_hint=(0.5, 1),
            background_normal="",
            background_color=ACCENT_DARK,
            color=TEXT_LIGHT,
            font_size=14,
        )
        self.clear_button.bind(on_press=self.clear)
        action_row.add_widget(self.clear_button)

        self.add_widget(action_row)

    def _update_card(self, *args):
        self.card_rect.pos = self.card.pos
        self.card_rect.size = self.card.size

    def start(self, instance):
        secret = self.secret_input.text.strip().replace(" ", "")
        if not secret:
            return
        try:
            self.totp = pyotp.TOTP(secret)
        except Exception:
            self.code_label.text = "Неверный ключ"
            return
        Clock.unschedule(self.update)
        Clock.schedule_interval(self.update, 1)
        self.update(0)

    def update(self, dt):
        if not self.totp:
            return
        code = self.totp.now()
        remaining = self.totp.interval - (int(time.time()) % self.totp.interval)
        self.code_label.text = code
        self.timer_label.text = f"Обновится через {remaining} сек"

    def paste_secret(self, instance):
        text = Clipboard.paste()
        if text:
            self.secret_input.text = text.strip().replace(" ", "")

    def copy_code(self, instance):
        if not self.code_label.text or self.code_label.text == "Неверный ключ":
            return
        Clipboard.copy(self.code_label.text)
        original = instance.text
        instance.text = "Скопировано!"
        Clock.schedule_once(lambda dt: setattr(instance, "text", original), 1)

    def clear(self, instance):
        # Ничего не сохранялось на диск — просто чистим память
        Clock.unschedule(self.update)
        self.secret_input.text = ""
        self.code_label.text = ""
        self.timer_label.text = ""
        self.totp = None


class TOTPApp(App):
    def build(self):
        Window.clearcolor = BG_DARK
        Window.softinput_mode = "below_target"
        return RootLayout()


if __name__ == "__main__":
    TOTPApp().run()
        self.start_button = Button(
            text="Старт",
            size_hint=(1, None),
            height=60,
            background_normal="",
            background_color=ACCENT,
            color=(1, 1, 1, 1),
            bold=True,
            font_size=18,
        )
        self.start_button.bind(on_press=self.start)
        self.add_widget(self.start_button)

        # Карточка под кодом
        self.card = FloatLayout(size_hint=(1, None), height=160)
        with self.card.canvas.before:
            Color(*PANEL)
            self.card_rect = RoundedRectangle(pos=self.card.pos, size=self.card.size, radius=[20])
        self.card.bind(pos=self._update_card, size=self._update_card)

        self.code_label = Label(
            text="",
            font_size=52,
            bold=True,
            color=CODE_COLOR,
            size_hint=(1, 0.7),
            pos_hint={"x": 0, "top": 1},
        )
        self.card.add_widget(self.code_label)

        self.timer_label = Label(
            text="",
            font_size=16,
            color=(0.75, 0.65, 0.85, 1),
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0},
        )
        self.card.add_widget(self.timer_label)

        self.add_widget(self.card)

        # Строка: "Скопировать код" + "Очистить ключ"
        action_row = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=50, spacing=10
        )
        self.copy_button = Button(
            text="Скопировать код",
            size_hint=(0.5, 1),
            background_normal="",
            background_color=ACCENT_DARK,
            color=TEXT_LIGHT,
            font_size=14,
        )
        self.copy_button.bind(on_press=self.copy_code)
        action_row.add_widget(self.copy_button)

        self.clear_button = Button(
            text="Очистить ключ",
            size_hint=(0.5, 1),
            background_normal="",
            background_color=ACCENT_DARK,
            color=TEXT_LIGHT,
            font_size=14,
        )
        self.clear_button.bind(on_press=self.clear)
        action_row.add_widget(self.clear_button)

        self.add_widget(action_row)

    def _update_card(self, *args):
        self.card_rect.pos = self.card.pos
        self.card_rect.size = self.card.size

    def start(self, instance):
        secret = self.secret_input.text.strip().replace(" ", "")
        if not secret:
            return
        try:
            self.totp = pyotp.TOTP(secret)
        except Exception:
            self.code_label.text = "Неверный ключ"
            return
        Clock.unschedule(self.update)
        Clock.schedule_interval(self.update, 1)
        self.update(0)

    def update(self, dt):
        if not self.totp:
            return
        code = self.totp.now()
        remaining = self.totp.interval - (int(time.time()) % self.totp.interval)
        self.code_label.text = code
        self.timer_label.text = f"Обновится через {remaining} сек"

    def paste_secret(self, instance):
        text = Clipboard.paste()
        if text:
            self.secret_input.text = text.strip().replace(" ", "")

    def copy_code(self, instance):
        if not self.code_label.text or self.code_label.text == "Неверный ключ":
            return
        Clipboard.copy(self.code_label.text)
        original = instance.text
        instance.text = "Скопировано!"
        Clock.schedule_once(lambda dt: setattr(instance, "text", original), 1)

    def clear(self, instance):
        # Ничего не сохранялось на диск — просто чистим память
        Clock.unschedule(self.update)
        self.secret_input.text = ""
        self.code_label.text = ""
        self.timer_label.text = ""
        self.totp = None


class TOTPApp(App):
    def build(self):
        Window.clearcolor = BG_DARK
        return RootLayout()


if __name__ == "__main__":
    TOTPApp().run()
