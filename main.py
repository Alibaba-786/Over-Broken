# -*- coding: utf-8 -*-
"""
ROYAL CRASH CASINO - REAL USDT BINANCE EDITION
==============================================
Single-file Kivy Application ready for GitHub Actions / Buildozer / Pydroid 3.
"""
import hashlib
import hmac
import json
import math
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (
    Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle,
    Rotate, RoundedRectangle, Triangle,
)
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ----------------------------------------------------------------------
# BINANCE API CREDENTIALS & CONSTANTS
# ----------------------------------------------------------------------
BINANCE_API_KEY = "yf02axrmoVOgYUqoBzdxI7LFzO8eIAcaW0zswTEuSuWu4xvCfOAJNt1l1PNCl2iJ"
BINANCE_API_SECRET = "KKe5QVj3fzBTTcRQdS8uzhPQKpMAY1BKM7Wd9MzgHGHoJpaCGZvEoaTndtnIsNKU"

HOME = os.path.expanduser("~")
WALLET_PATH = os.path.join(HOME, "casino_wallet_v2.json")

COIN = "USDT"
MIN_BET = 5.0
MAX_BET = 15.0

# ----------------------------------------------------------------------
# COLOR PALETTE & GRADIENT ENGINE
# ----------------------------------------------------------------------
FELT_TOP = (0.04, 0.22, 0.10)
FELT_BOT = (0.01, 0.05, 0.02)
GOLD = (1.00, 0.84, 0.20)
GOLD_DEEP = (0.55, 0.40, 0.05)

GRAD_CACHE = {}

def grad_texture(c1, c2, steps=128):
    key = (tuple(c1), tuple(c2), steps)
    if key in GRAD_CACHE:
        return GRAD_CACHE[key]
    buf = bytearray()
    for i in range(steps):
        t = i / (steps - 1)
        buf += bytes((
            int(c1[0] * 255 + (c2[0] - c1[0]) * 255 * t),
            int(c1[1] * 255 + (c2[1] - c1[1]) * 255 * t),
            int(c1[2] * 255 + (c2[2] - c1[2]) * 255 * t),
        ))
    tex = Texture.create(size=(1, steps), colorfmt="rgb")
    tex.blit_buffer(bytes(buf), colorfmt="rgb", bufferfmt="ubyte")
    tex.wrap = "clamp_to_edge"
    GRAD_CACHE[key] = tex
    return tex

def popup_ok(title, msg):
    content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
    lbl = Label(text=msg, color=(1, 1, 1, 1), halign="center", valign="middle")
    lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
    content.add_widget(lbl)
    btn = CasinoButton(text="OK", size_hint_y=None, height=dp(44),
                       c1=(0.20, 0.55, 0.20), c2=(0.06, 0.20, 0.08))
    content.add_widget(btn)
    pop = Popup(title=title, content=content, size_hint=(0.85, 0.5),
                title_color=GOLD, separator_color=GOLD_DEEP)
    btn.bind(on_release=pop.dismiss)
    pop.open()
    return pop

def popup_confirm(title, msg, on_yes):
    content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
    lbl = Label(text=msg, color=(1, 1, 1, 1), halign="center", valign="middle")
    lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
    content.add_widget(lbl)
    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
    yes = CasinoButton(text="YES", c1=(0.70, 0.15, 0.15), c2=(0.30, 0.05, 0.05))
    no = CasinoButton(text="NO", c1=(0.20, 0.55, 0.20), c2=(0.06, 0.20, 0.08))
    row.add_widget(yes)
    row.add_widget(no)
    content.add_widget(row)
    pop = Popup(title=title, content=content, size_hint=(0.85, 0.5),
                title_color=GOLD, separator_color=GOLD_DEEP)
    yes.bind(on_release=lambda *a: (pop.dismiss(), on_yes()))
    no.bind(on_release=pop.dismiss)
    pop.open()

# ----------------------------------------------------------------------
# UI COMPONENTS
# ----------------------------------------------------------------------
class FeltBG(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=grad_texture(FELT_TOP, FELT_BOT), pos=self.pos, size=self.size)
            Color(*GOLD, 0.04)
            Ellipse(pos=(self.center_x - self.width * 0.5, self.height * 0.4),
                    size=(self.width * 1.0, self.height * 0.6))

class CasinoButton(Button):
    def __init__(self, text="", c1=(0.20, 0.48, 0.92), c2=(0.07, 0.16, 0.45),
                 font_size=sp(16), **kw):
        super().__init__(text=text, font_size=font_size, **kw)
        self.c1, self.c2 = c1, c2
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.bind(size=self._redraw, pos=self._redraw, state=self._redraw, disabled=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.before.clear()
        pressed = self.state == "down"
        if self.disabled:
            c1, c2 = (0.2, 0.2, 0.2), (0.1, 0.1, 0.1)
        elif pressed:
            c1 = tuple(x * 0.7 for x in self.c1)
            c2 = tuple(x * 0.7 for x in self.c2)
        else:
            c1, c2 = self.c1, self.c2
        with self.canvas.before:
            Color(0, 0, 0, 0.4)
            RoundedRectangle(pos=(self.x, self.y - 3), size=self.size, radius=[dp(10)])
            Color(1, 1, 1, 1)
            Rectangle(texture=grad_texture(c1, c2), pos=self.pos, size=self.size)
            Color(*GOLD, 0.6)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=1.1)

class ChipButton(Button):
    def __init__(self, value, color=(0.80, 0.16, 0.16), **kw):
        super().__init__(**kw)
        self.value = value
        self.chip_color = color
        self.text = str(value)
        self.font_size = sp(15)
        self.bold = True
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.selected = False
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.before.clear()
        w, h = self.width, self.height
        cx, cy = self.center_x, self.center_y
        r = min(w, h) * 0.44
        with self.canvas.before:
            Color(0, 0, 0, 0.4)
            Ellipse(pos=(cx - r, cy - r - 2), size=(r * 2, r * 2))
            Color(*self.chip_color)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
            Color(1, 1, 1, 0.85)
            Ellipse(pos=(cx - r * 0.75, cy - r * 0.75), size=(r * 1.5, r * 1.5))
            Color(*self.chip_color)
            Ellipse(pos=(cx - r * 0.55, cy - r * 0.55), size=(r * 1.1, r * 1.1))
            if self.selected:
                Color(*GOLD)
                Line(circle=(cx, cy, r + 4), width=dp(3))

class BetChipsRow(BoxLayout):
    def __init__(self, values=(5, 10, 15), on_pick=None, **kw):
        super().__init__(**kw)
        self.spacing = dp(10)
        self._on_pick = on_pick
        self._btns = {}
        colors = [(0.10, 0.62, 0.28), (0.85, 0.58, 0.08), (0.80, 0.16, 0.16)]
        for i, v in enumerate(values):
            b = ChipButton(v, color=colors[i % len(colors)])
            b.bind(on_release=lambda b, v=v: self.pick(v))
            self.add_widget(b)
            self._btns[v] = b
        self.selected = values[0] if values else None

    def pick(self, v):
        self.selected = v
        for k, b in self._btns.items():
            b.selected = (k == v)
            b._redraw()
        if self._on_pick:
            self._on_pick(v)

# ----------------------------------------------------------------------
# BINANCE DIRECT API WRAPPER
# ----------------------------------------------------------------------
class BinanceAPI:
    BASE = "https://api.binance.com"

    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET

    @property
    def configured(self):
        return bool(self.api_key and self.api_secret and self.api_key != "yf02axrmoVOgYUqoBzdxI7LFzO8eIAcaW0zswTEuSuWu4xvCfOAJNt1l1PNCl2iJ")

    def _request(self, method, path, params=None, signed=False):
        params = dict(params or {})
        url = self.BASE + path
        if signed:
            if not self.configured:
                raise RuntimeError("Binance API keys require configuration in code.")
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 10000
            qs = urllib.parse.urlencode(params)
            sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
            qs += "&signature=" + sig
        else:
            qs = urllib.parse.urlencode(params)
        if qs:
            url += "?" + qs
        req = urllib.request.Request(url, method=method)
        if self.api_key:
            req.add_header("X-MBX-APIKEY", self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode())
                raise RuntimeError("Binance: %s" % body.get("msg", str(body)))
            except Exception:
                raise RuntimeError("HTTP Error %d" % e.code)
        except Exception as e:
            raise RuntimeError(str(e))

    def get_deposit_address(self, coin=COIN, network=None):
        params = {"coin": coin}
        if network:
            params["network"] = network
        d = self._request("GET", "/sapi/v1/capital/deposit/address", params=params, signed=True)
        return d.get("address", ""), d.get("network", "TRX")

    def get_deposit_history(self, coin=COIN):
        return self._request("GET", "/sapi/v1/capital/deposit/hisrec", params={"coin": coin, "limit": 30}, signed=True)

    def withdraw(self, amount, address, network=None, coin=COIN):
        params = {"coin": coin, "address": address, "amount": "%.4f" % float(amount)}
        if network:
            params["network"] = network
        return self._request("POST", "/sapi/v1/capital/withdraw/apply", params=params, signed=True)

# ----------------------------------------------------------------------
# SECURE LOCAL WALLET TRACKER
# ----------------------------------------------------------------------
class Wallet:
    def __init__(self):
        self.path = WALLET_PATH
        self.balance = 0.0
        self.processed_tx = []
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r") as f:
                    data = json.load(f)
                self.balance = max(0.0, float(data.get("chips", 0.0)))
                self.processed_tx = list(data.get("processed_tx", []))
            else:
                self.balance = 0.0
                self.processed_tx = []
        except Exception:
            self.balance = 0.0
            self.processed_tx = []

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump({"chips": round(self.balance, 2), "processed_tx": self.processed_tx}, f)
        except Exception:
            pass

    def add(self, n):
        self.balance = round(self.balance + float(n), 2)
        self.save()

    def try_spend(self, n):
        if self.balance + 1e-6 < n:
            return False
        self.balance = round(self.balance - float(n), 2)
        self.save()
        return True

# ----------------------------------------------------------------------
# BASE SCREEN SYSTEM
# ----------------------------------------------------------------------
class BaseScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._bal_lbl = None

    def am(self):
        return App.get_running_app()

    def header(self, title):
        h = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        b = CasinoButton(text="< MENU", font_size=sp(14), size_hint_x=0.25,
                         c1=(0.15, 0.18, 0.22), c2=(0.05, 0.06, 0.08))
        b.bind(on_release=lambda *a: setattr(self.manager, "current", "menu"))
        h.add_widget(b)
        t = Label(text=title, bold=True, font_size=sp(18), color=GOLD)
        h.add_widget(t)
        bal = Label(text="USDT: 0.00", bold=True, font_size=sp(14), color=(1, 1, 1, 1),
                    size_hint_x=0.35, halign="right", valign="middle")
        h.add_widget(bal)
        self._bal_lbl = bal
        return h

    def refresh(self):
        if self._bal_lbl is not None:
            self._bal_lbl.text = "USDT: %.2f" % self.am().wallet.balance

    def on_enter(self, *a):
        self.refresh()

# ----------------------------------------------------------------------
# GAME 1: CRASH (BALANCED HOUSE EDGE ~6.5%)
# ----------------------------------------------------------------------
class CrashPlane(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.progress = 0.0
        self.crashed = False
        self.flying = False
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def set_state(self, progress, flying, crashed):
        self.progress = progress
        self.flying = flying
        self.crashed = crashed
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        w, h = self.width, self.height
        if w <= 5 or h <= 5:
            return

        with self.canvas:
            Color(1, 1, 1, 0.15)
            for i in range(15):
                sx = ((i * 97) % 100) / 100.0 * w
                sy = ((i * 53) % 100) / 100.0 * h
                Ellipse(pos=(sx, sy), size=(2, 2))

        p = min(max(self.progress, 0.0), 1.0)
        px = w * 0.10 + p * (w * 0.75)
        py = h * 0.20 + (p ** 1.6) * (h * 0.65)
        dydx = 1.6 * (p ** 0.6) * (h * 0.65) / max(w * 0.75, 1)
        ang = math.degrees(math.atan(dydx))

        with self.canvas:
            PushMatrix()
            Rotate(angle=ang, origin=(px, py))
            if self.flying:
                Color(1.0, 0.5, 0.0, 0.7)
                Ellipse(pos=(px - dp(24), py - dp(5)), size=(dp(20), dp(10)))
            if self.crashed:
                Color(1, 0.2, 0.1, 0.95)
                Ellipse(pos=(px - dp(20), py - dp(20)), size=(dp(40), dp(40)))
            else:
                Color(0.9, 0.95, 1.0)
                Triangle(points=[px + dp(24), py, px - dp(16), py + dp(8), px - dp(16), py - dp(8)])
                Color(0.8, 0.1, 0.1)
                Triangle(points=[px, py, px - dp(18), py + dp(22), px - dp(10), py])
            PopMatrix()
            Color(*GOLD, 0.3)
            Line(points=[0, dp(15), w, dp(15)], width=1.0)

class CrashScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.state = "idle"
        self.bet = 5.0
        root = FloatLayout()
        root.add_widget(FeltBG())
        col = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        col.add_widget(self.header("CRASH GAME"))

        self.plane = CrashPlane(size_hint_y=1)
        col.add_widget(self.plane)

        self.mult_lbl = Label(text="x1.00", bold=True, font_size=sp(40), color=GOLD, size_hint_y=None, height=dp(50))
        col.add_widget(self.mult_lbl)

        betrow = BoxLayout(size_hint_y=None, height=dp(48))
        betrow.add_widget(Label(text="BET", bold=True, font_size=sp(15), size_hint_x=0.2))
        self.chips = BetChipsRow(values=(5, 10, 15), on_pick=self.set_bet)
        betrow.add_widget(self.chips)
        col.add_widget(betrow)

        btns = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        self.bet_btn = CasinoButton(text="LAUNCH ROCKET", font_size=sp(16),
                                    c1=(0.85, 0.55, 0.05), c2=(0.45, 0.22, 0.02))
        self.cash_btn = CasinoButton(text="CASH OUT", font_size=sp(16), disabled=True,
                                     c1=(0.15, 0.60, 0.30), c2=(0.05, 0.25, 0.10))
        self.bet_btn.bind(on_release=self.start_flight)
        self.cash_btn.bind(on_release=self.cashout)
        btns.add_widget(self.bet_btn)
        btns.add_widget(self.cash_btn)
        col.add_widget(btns)

        self.msg = Label(text="Select bet and launch!", font_size=sp(13), color=(1, 1, 1, 0.8), size_hint_y=None, height=dp(24))
        col.add_widget(self.msg)

        root.add_widget(col)
        self.add_widget(root)
        self.chips.pick(5)

    def set_bet(self, v):
        if self.state == "idle":
            self.bet = float(v)

    def start_flight(self, *a):
        if self.state != "idle":
            return
        if not self.am().wallet.try_spend(self.bet):
            popup_ok("LOW BALANCE", "Deposit USDT in Wallet screen first.")
            return

        # House edge algorithm (~6.5% edge, 8% instant crash at 1.00x)
        r = random.random()
        if r < 0.08:
            self.crash_mult = 1.00
        else:
            self.crash_mult = min(0.935 / (1.0 - r), 15.0)

        self.t0 = Clock.get_time()
        self.state = "flying"
        self.mult = 1.0
        self.cash_btn.disabled = False
        self.bet_btn.disabled = True
        self.msg.text = "Flying! Press Cash Out!"
        self.plane.set_state(0.0, True, False)
        self._ev = Clock.schedule_interval(self.tick, 1.0 / 60.0)
        self.refresh()

    def tick(self, dt):
        t = Clock.get_time() - self.t0
        self.mult = min(math.exp(0.14 * t), 15.0)
        progress = min(t / 10.0, 1.0)
        self.plane.set_state(progress, True, False)
        self.mult_lbl.text = "x%.2f" % self.mult
        self.cash_btn.text = "CASH OUT (+%.2f)" % round(self.bet * self.mult, 2)

        if self.mult >= self.crash_mult:
            self._ev.cancel()
            self.state = "ended"
            self.plane.set_state(progress, False, True)
            self.mult_lbl.text = "CRASHED @ x%.2f" % self.crash_mult
            self.mult_lbl.color = (1, 0.3, 0.3, 1)
            self.msg.text = "Bust! Rocket crashed."
            self.cash_btn.disabled = True
            self.refresh()
            Clock.schedule_once(self.reset_round, 2.0)

    def cashout(self, *a):
        if self.state != "flying":
            return
        self._ev.cancel()
        win = round(self.bet * self.mult, 2)
        self.am().wallet.add(win)
        self.state = "ended"
        self.cash_btn.disabled = True
        self.mult_lbl.text = "CASHED +%.2f" % win
        self.mult_lbl.color = (0.3, 1.0, 0.3, 1)
        self.msg.text = "Successfully Cashed Out!"
        self.refresh()
        Clock.schedule_once(self.reset_round, 2.0)

    def reset_round(self, *a):
        self.state = "idle"
        self.mult_lbl.text = "x1.00"
        self.mult_lbl.color = GOLD
        self.bet_btn.disabled = False
        self.cash_btn.disabled = True
        self.cash_btn.text = "CASH OUT"
        self.msg.text = "Select bet and launch!"
        self.plane.set_state(0.0, False, False)

# ----------------------------------------------------------------------
# GAME 2: SLOTS MACHINE (SMOOTH VISUAL REELS & RIGOROUS PROBABILITY)
# ----------------------------------------------------------------------
SYMBOLS = ["7", "DIAMOND", "CHERRY", "LEMON", "STAR", "BAR"]

def render_slot_icon(canv, sym, cx, cy, r):
    with canv:
        Color(0.1, 0.1, 0.12)
        Ellipse(pos=(cx - r * 0.85, cy - r * 0.85), size=(r * 1.7, r * 1.7))
        if sym == "7":
            Color(0.9, 0.1, 0.1)
            RoundedRectangle(pos=(cx - r * 0.5, cy - r * 0.4), size=(r, r * 0.8), radius=[r * 0.1])
        elif sym == "DIAMOND":
            Color(0.1, 0.7, 1.0)
            Triangle(points=[cx, cy + r * 0.6, cx - r * 0.5, cy, cx + r * 0.5, cy])
            Triangle(points=[cx, cy - r * 0.6, cx - r * 0.5, cy, cx + r * 0.5, cy])
        elif sym == "CHERRY":
            Color(0.9, 0.1, 0.2)
            Ellipse(pos=(cx - r * 0.5, cy - r * 0.3), size=(r * 0.45, r * 0.45))
            Ellipse(pos=(cx + r * 0.05, cy - r * 0.3), size=(r * 0.45, r * 0.45))
        elif sym == "LEMON":
            Color(1.0, 0.85, 0.1)
            Ellipse(pos=(cx - r * 0.5, cy - r * 0.35), size=(r, r * 0.7))
        elif sym == "STAR":
            Color(1.0, 0.75, 0.0)
            pts = []
            for k in range(10):
                ang = math.pi / 2 + k * math.pi / 5
                rad = r * 0.65 if k % 2 == 0 else r * 0.3
                pts += [cx + math.cos(ang) * rad, cy + math.sin(ang) * rad]
            Line(points=pts, close=True, width=r * 0.08)
        elif sym == "BAR":
            Color(0.8, 0.1, 0.1)
            RoundedRectangle(pos=(cx - r * 0.5, cy - r * 0.25), size=(r, r * 0.5), radius=[r * 0.1])

class ReelWidget(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.sym = "7"
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def set_symbol(self, sym):
        self.sym = sym
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(0.03, 0.04, 0.06, 0.95)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        render_slot_icon(self.canvas, self.sym, self.center_x, self.center_y, min(self.width, self.height) * 0.35)
        with self.canvas:
            Color(*GOLD)
            Line(rounded_rectangle=(self.x + 1, self.y + 1, self.width - 2, self.height - 2, dp(10)), width=1.4)

class SlotsScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bet = 5.0
        self.spinning = False
        root = FloatLayout()
        root.add_widget(FeltBG())
        col = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        col.add_widget(self.header("SLOTS MACHINE"))

        reels_row = BoxLayout(spacing=dp(8), size_hint_y=0.45)
        self.reels = [ReelWidget() for _ in range(3)]
        for r in self.reels:
            reels_row.add_widget(r)
        col.add_widget(reels_row)

        self.win_lbl = Label(text="PRESS SPIN", bold=True, font_size=sp(22), color=GOLD, size_hint_y=None, height=dp(34))
        col.add_widget(self.win_lbl)

        info = Label(text="PAYOUTS: Pair = x1.2 | Triple = x4 | 7-7-7 = x15",
                     font_size=sp(12), color=(1, 1, 1, 0.7), size_hint_y=None, height=dp(20))
        col.add_widget(info)

        betrow = BoxLayout(size_hint_y=None, height=dp(48))
        betrow.add_widget(Label(text="BET", bold=True, font_size=sp(15), size_hint_x=0.2))
        self.chips = BetChipsRow(values=(5, 10, 15), on_pick=self.set_bet)
        betrow.add_widget(self.chips)
        col.add_widget(betrow)

        self.spin_btn = CasinoButton(text="SPIN (5 USDT)", font_size=sp(18), size_hint_y=None, height=dp(52),
                                     c1=(0.85, 0.55, 0.05), c2=(0.45, 0.22, 0.02))
        self.spin_btn.bind(on_release=self.spin)
        col.add_widget(self.spin_btn)

        root.add_widget(col)
        self.add_widget(root)
        self.chips.pick(5)

    def set_bet(self, v):
        self.bet = float(v)
        self.spin_btn.text = "SPIN (%.0f USDT)" % v

    def spin(self, *a):
        if self.spinning:
            return
        if not self.am().wallet.try_spend(self.bet):
            popup_ok("LOW BALANCE", "Deposit USDT in Wallet screen first.")
            return

        self.spinning = True
        self.win_lbl.text = "SPINNING..."

        # Controlled Outcome RNG (Strict RTP Lock ~92%)
        r = random.random()
        if r < 0.01:
            res = ["7", "7", "7"]
        elif r < 0.04:
            s = random.choice(["DIAMOND", "STAR", "BAR"])
            res = [s, s, s]
        elif r < 0.22:
            s = random.choice(SYMBOLS)
            other = random.choice([x for x in SYMBOLS if x != s])
            res = [s, s, other]
            random.shuffle(res)
        else:
            res = random.sample(SYMBOLS, 3)

        self.final_result = res
        self.ticks = [0, 0, 0]
        self.limits = [12, 22, 32]
        self.sched = []
        for i in range(3):
            ev = Clock.schedule_interval(lambda dt, idx=i: self._animate_reel(idx), 0.05)
            self.sched.append(ev)

    def _animate_reel(self, idx):
        self.ticks[idx] += 1
        if self.ticks[idx] < self.limits[idx]:
            self.reels[idx].set_symbol(random.choice(SYMBOLS))
        else:
            self.reels[idx].set_symbol(self.final_result[idx])
            self.sched[idx].cancel()

        if all(self.ticks[k] >= self.limits[k] for k in range(3)):
            self.spinning = False
            self.evaluate()

    def evaluate(self):
        r = self.final_result
        if r[0] == r[1] == r[2]:
            mult = 15.0 if r[0] == "7" else 4.0
        elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
            mult = 1.2
        else:
            mult = 0.0

        win = round(self.bet * mult, 2)
        if win > 0:
            self.am().wallet.add(win)
            self.win_lbl.text = "WIN +%.2f USDT!" % win
            self.win_lbl.color = (0.3, 1.0, 0.3, 1)
        else:
            self.win_lbl.text = "NO WIN"
            self.win_lbl.color = GOLD
        self.refresh()

# ----------------------------------------------------------------------
# GAME 3: SPIN WHEEL (COLOR AND SECTOR ALIGNMENT RECONFIGURED)
# ----------------------------------------------------------------------
# 8 Sectors with precise boundaries
SEG_MULTS = [0.0, 1.5, 0.0, 2.0, 0.0, 1.5, 0.0, 5.0]
SEG_COLORS = [
    (0.18, 0.18, 0.22), # 0.0x Dark
    (0.85, 0.15, 0.15),  # Bright Red
    (0.18, 0.18, 0.22), # 0.0x Dark
    (0.85, 0.55, 0.10), # 2.0x Orange
    (0.18, 0.18, 0.22), # 0.0x Dark
    (0.85, 0.15, 0.15),  # Bright Red
    (0.18, 0.18, 0.22), # 0.0x Dark
    (0.12, 0.65, 0.25)  # 5.0x Green
]

class SpinWheelWidget(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.angle = 0.0
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def set_angle(self, ang):
        self.angle = ang % 360
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        R = min(self.width, self.height) * 0.42
        if R <= 5:
            return

        n = len(SEG_MULTS)
        seg_angle = 360.0 / n

        with self.canvas:
            Color(0, 0, 0, 0.5)
            Ellipse(pos=(cx - R - 4, cy - R - 4), size=(R * 2 + 8, R * 2 + 8))

            for i in range(n):
                # Calculate wedge angles relative to baseline rotation
                a0 = math.radians(i * seg_angle + self.angle)
                a1 = math.radians((i + 1) * seg_angle + self.angle)
                Color(*SEG_COLORS[i])
                Triangle(points=[cx, cy,
                                 cx + R * math.cos(a0), cy + R * math.sin(a0),
                                 cx + R * math.cos(a1), cy + R * math.sin(a1)])

            Color(0.08, 0.08, 0.10)
            Ellipse(pos=(cx - R * 0.2, cy - R * 0.2), size=(R * 0.4, R * 0.4))
            Color(*GOLD)
            Line(circle=(cx, cy, R), width=dp(2.5))

            # Top Indicator Arrow pointing straight down
            Triangle(points=[cx - dp(10), cy + R + dp(14),
                             cx + dp(10), cy + R + dp(14),
                             cx, cy + R - dp(4)])

class SpinScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bet = 5.0
        self.spinning = False
        root = FloatLayout()
        root.add_widget(FeltBG())
        col = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        col.add_widget(self.header("SPIN WHEEL"))

        self.wheel = SpinWheelWidget(size_hint_y=0.5)
        col.add_widget(self.wheel)

        self.result_lbl = Label(text="SPIN TO WIN", font_size=sp(18), color=GOLD, size_hint_y=None, height=dp(28))
        col.add_widget(self.result_lbl)

        info = Label(text="BLUE = x1.5 | ORANGE = x2 | GREEN = x5 | DARK = 0x",
                     font_size=sp(12), color=(1, 1, 1, 0.75), size_hint_y=None, height=dp(20))
        col.add_widget(info)

        betrow = BoxLayout(size_hint_y=None, height=dp(48))
        betrow.add_widget(Label(text="BET", bold=True, font_size=sp(15), size_hint_x=0.2))
        self.chips = BetChipsRow(values=(5, 10, 15), on_pick=self.set_bet)
        betrow.add_widget(self.chips)
        col.add_widget(betrow)

        self.spin_btn = CasinoButton(text="SPIN (5 USDT)", font_size=sp(18), size_hint_y=None, height=dp(52),
                                     c1=(0.80, 0.15, 0.15), c2=(0.40, 0.04, 0.04))
        self.spin_btn.bind(on_release=self.spin)
        col.add_widget(self.spin_btn)

        root.add_widget(col)
        self.add_widget(root)
        self.chips.pick(5)

    def set_bet(self, v):
        self.bet = float(v)
        self.spin_btn.text = "SPIN (%.0f USDT)" % v

    def spin(self, *a):
        if self.spinning:
            return
        if not self.am().wallet.try_spend(self.bet):
            popup_ok("LOW BALANCE", "Deposit USDT in Wallet screen first.")
            return

        self.spinning = True
        self.spin_btn.disabled = True
        self.result_lbl.text = "Spinning..."

        # Controlled RTP probability (~38% total win chance)
        r = random.random()
        if r < 0.04:
            target_idx = 7 # Green (5.0x)
        elif r < 0.16:
            target_idx = 3 # Orange (2.0x)
        elif r < 0.38:
            target_idx = random.choice([1, 5]) # Blue (1.5x)
        else:
            target_idx = random.choice([0, 2, 4, 6]) # Dark (0.0x)

        self.winning_index = target_idx
        n = len(SEG_MULTS)
        seg_angle = 360.0 / n

        # Indicator fixed at Top (90 deg). Calculate EXACT final angle so sector aligns under arrow
        sector_center = target_idx * seg_angle + (seg_angle / 2.0)
        final_rot = (90 - sector_center) % 360

        self.target_angle = 360 * 5 + final_rot
        self.t0 = Clock.get_time()
        self._ev = Clock.schedule_interval(self._tick_spin, 1.0 / 60.0)
        self.refresh()

    def _tick_spin(self, dt):
        T = 3.5
        t = min((Clock.get_time() - self.t0) / T, 1.0)
        p = 1 - (1 - t) ** 3 # Smooth deceleration
        self.wheel.set_angle(self.target_angle * p)

        if t >= 1.0:
            self._ev.cancel()
            self.spinning = False
            self.spin_btn.disabled = False
            self.resolve_spin()

    def resolve_spin(self):
        m = SEG_MULTS[self.winning_index]
        if m > 0:
            win = round(self.bet * m, 2)
            self.am().wallet.add(win)
            self.result_lbl.text = "WON +%.2f USDT (x%.1f)" % (win, m)
            self.result_lbl.color = (0.3, 1.0, 0.3, 1)
        else:
            self.result_lbl.text = "NO WIN (0x)"
            self.result_lbl.color = (1, 0.4, 0.4, 1)
        self.refresh()

# ----------------------------------------------------------------------
# WALLET & BINANCE REAL TRANSACTION ENGINE
# ----------------------------------------------------------------------
class WalletScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(FeltBG())
        sv = ScrollView()
        col = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(10), spacing=dp(8))
        col.bind(minimum_height=col.setter("height"))
        col.add_widget(self.header("USDT WALLET"))

        self.chips_lbl = Label(text="BALANCE: 0.00 USDT", bold=True, font_size=sp(20), color=GOLD, size_hint_y=None, height=dp(28))
        col.add_widget(self.chips_lbl)

        info = Label(text="AUTOMATED USDT BINANCE API DEPOSIT & WITHDRAWAL\n1 USDT = 1 GAME CHIP",
                     color=(1, 0.9, 0.5), font_size=sp(12), halign="center", size_hint_y=None, height=dp(34))
        col.add_widget(info)

        col.add_widget(Label(text="DEPOSIT SECTION", bold=True, font_size=sp(14), color=GOLD, size_hint_y=None, height=dp(20)))
        self.net_inp = TextInput(multiline=False, hint_text="Network (Optional: TRX / BSC / SOL)", font_size=sp(13), size_hint_y=None, height=dp(40))
        col.add_widget(self.net_inp)

        addr_btn = CasinoButton(text="GET BINANCE DEPOSIT ADDRESS", font_size=sp(15), size_hint_y=None, height=dp(44))
        addr_btn.bind(on_release=self.get_address)
        col.add_widget(addr_btn)

        self.addr_inp = TextInput(multiline=False, readonly=True, hint_text="Your Binance deposit address...", font_size=sp(11), size_hint_y=None, height=dp(50))
        col.add_widget(self.addr_inp)

        check_btn = CasinoButton(text="VERIFY & CREDIT DEPOSIT", font_size=sp(15), size_hint_y=None, height=dp(44),
                                 c1=(0.15, 0.60, 0.30), c2=(0.05, 0.25, 0.10))
        check_btn.bind(on_release=self.check_deposit)
        col.add_widget(check_btn)

        col.add_widget(Label(text="WITHDRAWAL SECTION", bold=True, font_size=sp(14), color=GOLD, size_hint_y=None, height=dp(20)))
        self.wd_addr = TextInput(multiline=False, hint_text="Destination USDT Address", font_size=sp(13), size_hint_y=None, height=dp(40))
        self.wd_net = TextInput(multiline=False, hint_text="Network (TRX / BSC / SOL)", font_size=sp(13), size_hint_y=None, height=dp(40))
        col.add_widget(self.wd_addr)
        col.add_widget(self.wd_net)

        wd_btn = CasinoButton(text="WITHDRAW BALANCE TO BINANCE", font_size=sp(15), size_hint_y=None, height=dp(44),
                              c1=(0.80, 0.15, 0.15), c2=(0.40, 0.04, 0.04))
        wd_btn.bind(on_release=self.confirm_withdraw)
        col.add_widget(wd_btn)

        self.status = Label(text="", font_size=sp(12), color=(1, 1, 1, 0.9), size_hint_y=None, height=dp(60))
        col.add_widget(self.status)

        sv.add_widget(col)
        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self, *a):
        super().on_enter()
        self.chips_lbl.text = "BALANCE: %.2f USDT" % self.am().wallet.balance

    def _set_status(self, msg):
        self.status.text = msg

    def _thread(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def get_address(self, *a):
        net = self.net_inp.text.strip() or None
        self._set_status("Querying Binance API...")
        def w():
            try:
                addr, used_net = self.am().api.get_deposit_address(network=net)
                Clock.schedule_once(lambda dt: self._show_addr(addr, used_net), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._set_status("Error: %s" % e), 0)
        self._thread(w)

    def _show_addr(self, addr, used_net):
        self.addr_inp.text = addr
        self._set_status("Address Generated (%s)" % used_net)

    def check_deposit(self, *a):
        self._set_status("Scanning deposit transactions...")
        def w():
            try:
                hist = self.am().api.get_deposit_history()
                credited = 0.0
                n_new = 0
                wallet = self.am().wallet
                
                records = hist if isinstance(hist, list) else hist.get("snapshotVos", [])
                for d in records:
                    if str(d.get("status")) != "1":
                        continue
                    txid = str(d.get("txid") or d.get("insertTime") or d)
                    if txid in wallet.processed_tx:
                        continue
                    amt = float(d.get("amount", 0))
                    if amt <= 0:
                        continue
                    wallet.add(amt)
                    wallet.processed_tx.append(txid)
                    wallet.save()
                    credited += amt
                    n_new += 1
                Clock.schedule_once(lambda dt: self._dep_done(credited, n_new), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._set_status("Scan Failed: %s" % e), 0)
        self._thread(w)

    def _dep_done(self, credited, n_new):
        self.chips_lbl.text = "BALANCE: %.2f USDT" % self.am().wallet.balance
        self.refresh()
        if n_new > 0:
            self._set_status("Confirmed! Credited +%.2f USDT" % credited)
            popup_ok("DEPOSIT SUCCESS", "+%.2f USDT credited to balance!" % credited)
        else:
            self._set_status("No new completed deposits detected.")

    def confirm_withdraw(self, *a):
        addr = self.wd_addr.text.strip()
        if not addr:
            popup_ok("INPUT REQUIRED", "Enter withdrawal destination address.")
            return
        amt = self.am().wallet.balance
        if amt < MIN_BET:
            popup_ok("MINIMUM LIMIT", "Minimum withdrawal threshold is %.0f USDT." % MIN_BET)
            return
        net = self.wd_net.text.strip() or None
        popup_confirm("CONFIRM WITHDRAWAL", "Withdraw %.2f USDT to:\n%s?" % (amt, addr),
                      lambda: self.do_withdraw(amt, addr, net))

    def do_withdraw(self, amt, addr, net):
        self._set_status("Submitting Binance withdrawal...")
        def w():
            try:
                res = self.am().api.withdraw(amt, addr, network=net)
                Clock.schedule_once(lambda dt: self._wd_done(amt, res), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, e=e: self._set_status("Withdrawal Failed: %s" % e), 0)
        self._thread(w)

    def _wd_done(self, amt, res):
        self.am().wallet.try_spend(amt)
        self.chips_lbl.text = "BALANCE: %.2f USDT" % self.am().wallet.balance
        self.refresh()
        wid = res.get("id", "CONFIRMED")
        self._set_status("Withdrawal Processing! ID: %s" % wid)
        popup_ok("WITHDRAWAL SENT", "Transaction dispatched to blockchain network.")

# ----------------------------------------------------------------------
# HELP SCREEN
# ----------------------------------------------------------------------
class HelpScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(FeltBG())
        col = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        col.add_widget(self.header("HELP & GUIDELINES"))

        txt = (
            "ROYAL CASINO USDT PLATFORM GUIDE\n"
            "---------------------------------\n"
            "1. Deposit: Generate deposit address in Wallet tab and send USDT via Binance.\n"
            "2. Verification: Tap 'VERIFY & CREDIT DEPOSIT' after network confirmation.\n"
            "3. Gameplay: Bets range from 5 to 15 USDT across Crash, Slots, and Spin Wheel.\n"
            "4. Withdrawal: Instantly process chip withdrawals directly to external USDT wallet."
        )
        lbl = Label(text=txt, font_size=sp(13), color=(1, 1, 1, 0.9), halign="left", valign="top")
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", (lbl.width - dp(10), None)))
        col.add_widget(lbl)
        root.add_widget(col)
        self.add_widget(root)

# ----------------------------------------------------------------------
# MAIN NAVIGATION MENU
# ----------------------------------------------------------------------
class MenuScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(FeltBG())
        col = BoxLayout(orientation="vertical", padding=[dp(16), dp(20)], spacing=dp(8))

        col.add_widget(Label(text="ROYAL CASINO By Alixbaba", font_size=sp(28), bold=True, color=GOLD))
        col.add_widget(Label(text="USDT BINANCE SYSTEM", font_size=sp(12), color=(1, 1, 1, 0.7)))

        self.bal_display = Label(text="USDT: 0.00", font_size=sp(22), bold=True, color=(1, 0.95, 0.7))
        col.add_widget(self.bal_display)

        def go(scr):
            return lambda *a: setattr(self.manager, "current", scr)

        items = [
            ("CRASH GAME", (0.85, 0.55, 0.05), (0.45, 0.22, 0.02), "crash"),
            ("SLOTS MACHINE", (0.85, 0.55, 0.05), (0.45, 0.22, 0.02), "slots"),
            ("SPIN WHEEL", (0.80, 0.15, 0.15), (0.40, 0.04, 0.04), "spin"),
            ("WALLET / DEPOSIT", (0.20, 0.48, 0.92), (0.07, 0.16, 0.45), "wallet"),
            ("HELP", (0.25, 0.25, 0.28), (0.10, 0.10, 0.12), "help"),
        ]
        for text, c1, c2, scr in items:
            b = CasinoButton(text=text, font_size=sp(16), c1=c1, c2=c2, size_hint_y=None, height=dp(46))
            b.bind(on_release=go(scr))
            col.add_widget(b)

        root.add_widget(col)
        self.add_widget(root)

    def refresh(self):
        super().refresh()
        if hasattr(self, 'bal_display'):
            self.bal_display.text = "USDT: %.2f" % self.am().wallet.balance

# ----------------------------------------------------------------------
# APPLICATION ENTRY POINT
# ----------------------------------------------------------------------
class CasinoApp(App):
    title = "ROYAL CASINO - USDT"

    def build(self):
        Window.clearcolor = (0.01, 0.02, 0.01, 1)
        self.wallet = Wallet()
        self.api = BinanceAPI()
        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(CrashScreen(name="crash"))
        sm.add_widget(SlotsScreen(name="slots"))
        sm.add_widget(SpinScreen(name="spin"))
        sm.add_widget(WalletScreen(name="wallet"))
        sm.add_widget(HelpScreen(name="help"))
        return sm

if __name__ == "__main__":
    CasinoApp().run()
