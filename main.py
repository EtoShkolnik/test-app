from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import pyotp
import time


class TOTPLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=15, **kwargs)
        self.totp = None

        self.secret_input = TextInput(
            hint_text="Введи секретный ключ 2FA",
            multiline=False,
            size_hint=(1, None),
            height=50,
            password=True,
        )
        self.add_widget(self.secret_input)

        self.start_button = Button(text="Старт", size_hint=(1, None), height=60)
        self.start_button.bind(on_press=self.start)
        self.add_widget(self.start_button)

        self.code_label = Label(text="", font_size=48)
        self.add_widget(self.code_label)

        self.timer_label = Label(text="", font_size=20)
        self.add_widget(self.timer_label)

        self.clear_button = Button(text="Очистить ключ", size_hint=(1, None), height=50)
        self.clear_button.bind(on_press=self.clear)
        self.add_widget(self.clear_button)

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

    def clear(self, instance):
        # Ничего не сохранялось на диск — просто чистим память
        Clock.unschedule(self.update)
        self.secret_input.text = ""
        self.code_label.text = ""
        self.timer_label.text = ""
        self.totp = None


class TOTPApp(App):
    def build(self):
        return TOTPLayout()


if __name__ == "__main__":
    TOTPApp().run()
