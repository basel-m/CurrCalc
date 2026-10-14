"""
Currency Calculator - a tiny Windows 11 style currency converter.
Type things like:  10SAR + 15USD + 27JOD   and pick the output currency.
Requires only Python 3.9+ (standard library, no pip installs).

Version history
  1.0.0  First version: live conversion, rates API, history, dark/light
  1.0.1  Parser fixes (invisible characters, clearer errors)
  1.1.0  Alt+P currency list panel
  1.2.0  Click/double-click rows, in-app theme, searchable output picker, text fitting
  1.3.0  Layout fixes, recent currencies, A-Z order, button swap
  1.4.0  Smooth scrolling, scrollbar in picker, history scrolling
  1.5.0  Settings menu (theme, codes, about), horizontal-swipe fix
  1.6.0  Pin on top, paste cleanup, breakdown + multi-currency lines, rate-change arrows,
         "100 USD to SAR" mode, history dates/delete, copy menus, remembers window position
  1.6.1  Rounded boxes, search placeholder inside the box, history sideways-scroll fixes
         (swipe, drag), currency symbols ($ € £ ¥ ...) accepted in expressions
  1.6.2  Removed all history sideways-scroll code (it crashed the app)
  1.6.3  Popups open while pinned, one-off note on its own line, Italian lira (ITL),
         output-currency box sizing fix
  1.6.4  Rounded Pin button and settings controls, rounded popup windows (Windows 11)
  1.6.5  Settings popup no longer jumps in from the corner, third "Show in" button fits,
         settings stay open while picking a "Show in" currency
  1.6.6  Smoother popup opening (no flash), "Show in" list closes on a second click
  1.7.0  Clear button, switch "Show in" slots on/off, gold & silver (gram / troy oz) with live prices
  1.7.1  Clear button moved above the box, settings no longer flash when changing "Show in",
         gold/silver show price + up/down ticker only
"""

VERSION = "1.7.1"
import json
import os
import re
import threading
import time
import unicodedata
from datetime import date, timedelta
import urllib.request
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

APP = "CurrencyCalc"
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP)
RATES_FILE = os.path.join(DATA_DIR, "rates.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
REFRESH_SECONDS = 6 * 3600
FAVORITES = ["USD", "SAR", "JOD", "EUR", "GBP", "AED", "KWD", "EGP", "QAR", "BHD", "OMR", "CAD", "AUD", "JPY", "CHF", "INR", "TRY"]
THREE_DEC = {"JOD", "KWD", "BHD", "OMR", "TND", "LYD", "IQD"}
ZERO_DEC = {"JPY", "KRW", "VND", "CLP", "ISK", "UGX", "ITL"}
GRAM_PER_OZ = 31.1034768                       # grams in one troy ounce
METALS = ["XAU", "AUG", "XAG", "AGG"]          # gold oz, gold gram, silver oz, silver gram (shown first)
UNIT_LABEL = {"XAU": "oz gold", "AUG": "g gold", "XAG": "oz silver", "AGG": "g silver"}
METAL_PHRASE = UNIT_LABEL                      # what a click in the list types into the calculator
CHG_ALIAS = {"ITL": "EUR", "AUG": "XAU", "AGG": "XAG"}   # these follow another code's daily change
METALS_SECONDS = 300                           # refresh gold/silver every 5 minutes

THEMES = {
    "light": dict(bg="#f3f3f3", fg="#1a1a1a", card="#ffffff", sub="#5f5f5f", accent="#0067c0", border="#d9d9d9", sel="#cce4f7", up="#15803d", down="#c62828"),
    "dark": dict(bg="#202020", fg="#ffffff", card="#2b2b2b", sub="#a0a0a0", accent="#60cdff", border="#3d3d3d", sel="#3d3d3d", up="#4ade80", down="#f87171"),
}

THEME_LABEL = {"auto": "Theme: Auto", "light": "Theme: Light", "dark": "Theme: Dark"}
SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "﷼": "SAR", "₺": "TRY", "₩": "KRW", "₽": "RUB"}
SYM = "[$€£¥₹﷼₺₩₽]"
PANEL_W = 380
ROW_H = 52
PICK_H = 30
NAMES = {l[:3]: l[4:] for l in """
AED United Arab Emirates dirham
AFN Afghan afghani
ALL Albanian lek
AMD Armenian dram
ANG Netherlands Antillean guilder
AOA Angolan kwanza
ARS Argentine peso
AUD Australian dollar
AWG Aruban florin
AZN Azerbaijani manat
BAM Bosnia-Herzegovina mark
BBD Barbadian dollar
BDT Bangladeshi taka
BGN Bulgarian lev
BHD Bahraini dinar
BIF Burundian franc
BMD Bermudian dollar
BND Brunei dollar
BOB Bolivian boliviano
BRL Brazilian real
BSD Bahamian dollar
BTN Bhutanese ngultrum
BWP Botswana pula
BYN Belarusian ruble
BZD Belize dollar
CAD Canadian dollar
CDF Congolese franc
CHF Swiss franc
CLP Chilean peso
CNY Chinese yuan
COP Colombian peso
CRC Costa Rican colon
CUP Cuban peso
CVE Cape Verdean escudo
CZK Czech koruna
DJF Djiboutian franc
DKK Danish krone
DOP Dominican peso
DZD Algerian dinar
EGP Egyptian pound
ERN Eritrean nakfa
ETB Ethiopian birr
EUR Euro
FJD Fijian dollar
FKP Falkland Islands pound
FOK Faroese krona
GBP British pound
GEL Georgian lari
GGP Guernsey pound
GHS Ghanaian cedi
GIP Gibraltar pound
GMD Gambian dalasi
GNF Guinean franc
GTQ Guatemalan quetzal
GYD Guyanese dollar
HKD Hong Kong dollar
HNL Honduran lempira
HRK Croatian kuna
HTG Haitian gourde
HUF Hungarian forint
IDR Indonesian rupiah
ILS Israeli shekel
IMP Manx pound
INR Indian rupee
IQD Iraqi dinar
IRR Iranian rial
ISK Icelandic krona
ITL Italian lira (obsolete)
JEP Jersey pound
JMD Jamaican dollar
JOD Jordanian dinar
JPY Japanese yen
KES Kenyan shilling
KGS Kyrgyzstani som
KHR Cambodian riel
KID Kiribati dollar
KMF Comorian franc
KRW South Korean won
KWD Kuwaiti dinar
KYD Cayman Islands dollar
KZT Kazakhstani tenge
LAK Lao kip
LBP Lebanese pound
LKR Sri Lankan rupee
LRD Liberian dollar
LSL Lesotho loti
LYD Libyan dinar
MAD Moroccan dirham
MDL Moldovan leu
MGA Malagasy ariary
MKD Macedonian denar
MMK Myanmar kyat
MNT Mongolian tugrik
MOP Macanese pataca
MRU Mauritanian ouguiya
MUR Mauritian rupee
MVR Maldivian rufiyaa
MWK Malawian kwacha
MXN Mexican peso
MYR Malaysian ringgit
MZN Mozambican metical
NAD Namibian dollar
NGN Nigerian naira
NIO Nicaraguan cordoba
NOK Norwegian krone
NPR Nepalese rupee
NZD New Zealand dollar
OMR Omani rial
PAB Panamanian balboa
PEN Peruvian sol
PGK Papua New Guinean kina
PHP Philippine peso
PKR Pakistani rupee
PLN Polish zloty
PYG Paraguayan guarani
QAR Qatari riyal
RON Romanian leu
RSD Serbian dinar
RUB Russian ruble
RWF Rwandan franc
SAR Saudi riyal
SBD Solomon Islands dollar
SCR Seychellois rupee
SDG Sudanese pound
SEK Swedish krona
SGD Singapore dollar
SHP Saint Helena pound
SLE Sierra Leonean leone
SLL Sierra Leonean leone (old)
SOS Somali shilling
SRD Surinamese dollar
SSP South Sudanese pound
STN Sao Tome dobra
SYP Syrian pound
SZL Eswatini lilangeni
THB Thai baht
TJS Tajikistani somoni
TMT Turkmenistani manat
TND Tunisian dinar
TOP Tongan paanga
TRY Turkish lira
TTD Trinidad and Tobago dollar
TVD Tuvaluan dollar
TWD New Taiwan dollar
TZS Tanzanian shilling
UAH Ukrainian hryvnia
UGX Ugandan shilling
USD US dollar
UYU Uruguayan peso
UZS Uzbekistani som
VES Venezuelan bolivar
VND Vietnamese dong
VUV Vanuatu vatu
WST Samoan tala
XAF Central African CFA franc
XCD East Caribbean dollar
XCG Caribbean guilder
XDR Special Drawing Rights
XOF West African CFA franc
XPF CFP franc
YER Yemeni rial
ZAR South African rand
ZMW Zambian kwacha
ZWG Zimbabwe Gold
ZWL Zimbabwean dollar
XAU Gold (troy ounce)
AUG Gold (gram)
XAG Silver (troy ounce)
AGG Silver (gram)
""".strip().splitlines()}


def fmt_rate(r):
    """Foreign units per $1 - up to 6 decimals, trailing zeros trimmed."""
    return f"{r:,.6f}".rstrip("0").rstrip(".") or "0"


def fmt_usd(r):
    """Value of 1 foreign unit in USD - 3 decimals."""
    v = 1 / r
    return "<$0.001" if v < 0.0005 else f"${v:,.3f}"


# ----------------------------------------------------------------- storage
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


# ------------------------------------------------------------------- rates
def _er_api(d):
    if d.get("result") != "success":
        raise ValueError("bad response")
    return {k.upper(): float(v) for k, v in d["rates"].items()}


def _fawaz(d):
    return {k.upper(): float(v) for k, v in d["usd"].items() if v}


SOURCES = [
    ("open.er-api.com", "https://open.er-api.com/v6/latest/USD", _er_api),
    ("fawazahmed0 currency-api", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json", _fawaz),
]


def add_legacy(rates):
    """Obsolete currencies with a fixed euro rate (APIs no longer list them)."""
    if rates and "EUR" in rates:
        rates.setdefault("ITL", rates["EUR"] * 1936.27)
    return rates


def fetch_metals():
    """Live spot prices from gold-api.com (USD per troy ounce) -> {'XAU': oz per USD, 'XAG': ...}."""
    out = {}
    for sym in ("XAU", "XAG"):
        try:
            req = urllib.request.Request(f"https://api.gold-api.com/price/{sym}", headers={"User-Agent": APP})
            with urllib.request.urlopen(req, timeout=6) as r:
                price = float(json.loads(r.read().decode("utf-8"))["price"])
            if price > 0:
                out[sym] = 1.0 / price
        except Exception:
            pass
    return out


def fetch_metal_prev():
    """Yesterday's gold/silver (oz per USD) from the daily currency-api files; {} if unavailable."""
    base = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@%s/v1/currencies/usd.json"
    for back in (1, 2):
        try:
            req = urllib.request.Request(base % (date.today() - timedelta(days=back)).isoformat(), headers={"User-Agent": APP})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = _fawaz(json.loads(r.read().decode("utf-8")))
            out = {k: data[k] for k in ("XAU", "XAG") if k in data}
            if out:
                return out
        except Exception:
            pass
    return {}


def add_metals(rates, m):
    """Add gold/silver as pseudo-currencies: ounces and grams per 1 USD."""
    for oz, g in (("XAU", "AUG"), ("XAG", "AGG")):
        if oz in m:
            rates[oz] = m[oz]
            rates[g] = m[oz] * GRAM_PER_OZ
    return rates


def merge_metals(rates, live, old=None):
    m = {k: rates[k] for k in ("XAU", "XAG") if k in rates}
    if old:
        m.update({k: old[k] for k in ("XAU", "XAG") if k in old and k not in m})
    m.update(live or {})
    return add_metals(rates, m)


def fetch_rates():
    """Returns (rates_dict_per_USD, source_name) or raises."""
    last = None
    for name, url, parser in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": APP})
            with urllib.request.urlopen(req, timeout=8) as r:
                rates = parser(json.loads(r.read().decode("utf-8")))
            rates["USD"] = 1.0
            return add_legacy(rates), name
        except Exception as e:
            last = e
    raise last or RuntimeError("no source")


# ------------------------------------------------------------------ engine
def fetch_changes():
    """% change of each currency vs USD since yesterday (positive = currency gained)."""
    base = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@%s/v1/currencies/usd.json"

    def get(v):
        req = urllib.request.Request(base % v, headers={"User-Agent": APP})
        with urllib.request.urlopen(req, timeout=8) as r:
            return _fawaz(json.loads(r.read().decode("utf-8")))

    cur, prev = get("latest"), get((date.today() - timedelta(days=1)).isoformat())
    return {c: (prev[c] / cur[c] - 1) * 100 for c in cur if c in prev and c in NAMES}


TOKEN = re.compile(
    r"(?P<a>\d[\d,]*\.?\d*|\.\d+)\s*(?P<ac>[A-Za-z]{3})\b"
    r"|\b(?P<bc>[A-Za-z]{3})\s*(?P<b>\d[\d,]*\.?\d*|\.\d+)"
)
NUMTOK = re.compile(r"\s*(?:(\d+\.?\d*|\.\d+)|([-+*/()])|(\S))")


def _calc(text):
    """Tiny arithmetic parser: numbers, + - * / and brackets."""
    toks = []
    for m in NUMTOK.finditer(text):
        if m.group(3):
            ch = m.group(3)
            raise ValueError(f"Can't read '{ch}' (U+{ord(ch):04X})")
        toks.append(m.group(1) or m.group(2))
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        t = peek()
        pos[0] += 1
        return t

    def expr():
        v = term()
        while peek() in ("+", "-"):
            v = v + term() if take() == "+" else v - term()
        return v

    def term():
        v = factor()
        while peek() in ("*", "/"):
            v = v * factor() if take() == "*" else v / factor()
        return v

    def factor():
        t = take()
        if t in ("+", "-"):
            v = factor()
            return -v if t == "-" else v
        if t == "(":
            v = expr()
            if take() != ")":
                raise ValueError("Missing )")
            return v
        if t is None or t in ("*", "/", ")"):
            raise ValueError("Incomplete expression")
        return float(t)

    v = expr()
    if pos[0] != len(toks):
        raise ValueError("Invalid expression")
    return v


def normalize(expr):
    """Make odd keyboard/locale characters plain ASCII."""
    expr = re.sub(f"({SYM})\\s*(\\d[\\d,]*\\.?\\d*|\\.\\d+)", lambda m: m.group(2) + SYMBOLS[m.group(1)], expr)
    expr = re.sub(f"(\\d[\\d,]*\\.?\\d*)\\s*({SYM})", lambda m: m.group(1) + SYMBOLS[m.group(2)], expr)
    expr = unicodedata.normalize("NFKC", expr)
    out = []
    for ch in expr:
        if unicodedata.category(ch) in ("Cf", "Cc"):   # invisible direction marks etc.
            continue
        if ch.isdigit():
            try:
                ch = str(unicodedata.digit(ch))
            except ValueError:
                pass
        elif ch in "\u066b":            # Arabic decimal separator
            ch = "."
        elif ch in "\u066c\u060c":      # Arabic thousands sep / comma
            ch = ","
        elif ch in "\u2212\u2013\u2014":   # fancy minus / dashes
            ch = "-"
        elif ch in "\u00d7":
            ch = "*"
        elif ch in "\u00f7":
            ch = "/"
        elif ch.isspace():
            ch = " "
        out.append(ch)
    return "".join(out)


SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "₩": "KRW", "₺": "TRY", "₽": "RUB",
           "₪": "ILS", "₦": "NGN", "₱": "PHP", "฿": "THB", "₫": "VND", "₴": "UAH", "﷼": "SAR"}
_SYM = "[" + "".join(re.escape(c) for c in SYMBOLS) + "]"
_NUM = r"(\d[\d,]*\.?\d*|\.\d+)"
SYM_BEFORE = re.compile("(" + _SYM + r")\s*" + _NUM)
SYM_AFTER = re.compile(_NUM + r"\s*(" + _SYM + ")")


def sym_fix(expr):
    """'$15 + 20€' -> '15 USD + 20 EUR'"""
    expr = expr.replace("US$", "$")
    expr = SYM_BEFORE.sub(lambda m: f"{m.group(2)} {SYMBOLS[m.group(1)]}", expr)
    return SYM_AFTER.sub(lambda m: f"{m.group(1)} {SYMBOLS[m.group(2)]}", expr)


_UNIT = r"(?:troy\s*)?(g|gr|gm|gms|gram|grams|oz|ozt|ounce|ounces)"
_MET = r"(gold|silver)"
M_NUM_UNIT = re.compile(_NUM + r"\s*" + _UNIT + r"\s*(?:of\s+)?" + _MET + r"\b", re.I)
M_MET_NUM = re.compile(r"\b" + _MET + r"\s*" + _NUM + r"\s*" + _UNIT + r"\b", re.I)
M_UNIT_MET = re.compile(r"\b" + _UNIT + r"\s+(?:of\s+)?" + _MET + r"\b", re.I)
M_MET_UNIT = re.compile(r"\b" + _MET + r"\s+" + _UNIT + r"\b", re.I)


def _mcode(metal, unit):
    gram = unit.lower().startswith("g")
    return {("gold", False): "XAU", ("gold", True): "AUG", ("silver", False): "XAG", ("silver", True): "AGG"}[(metal.lower(), gram)]


def metal_fix(expr):
    """'5g gold + 2 oz silver' -> '5 AUG + 2 XAG';  'to gold g' -> 'to AUG'"""
    expr = M_NUM_UNIT.sub(lambda m: f"{m.group(1)} {_mcode(m.group(3), m.group(2))}", expr)
    expr = M_MET_NUM.sub(lambda m: f"{m.group(2)} {_mcode(m.group(1), m.group(3))}", expr)
    expr = M_UNIT_MET.sub(lambda m: _mcode(m.group(2), m.group(1)), expr)
    return M_MET_UNIT.sub(lambda m: _mcode(m.group(1), m.group(2)), expr)


def evaluate(expr, out, rates, parts=None):
    """Evaluate an expression with currency amounts; result is in `out`.
    Returns None for empty input; raises ValueError with a friendly message."""
    expr = metal_fix(normalize(sym_fix(expr))).strip()
    if not expr:
        return None
    if not rates:
        raise ValueError("No exchange rates yet - press Refresh")

    def sub(m):
        code = (m.group("ac") or m.group("bc")).upper()
        amount = float((m.group("a") or m.group("b")).replace(",", ""))
        if code not in rates:
            raise ValueError(f"Unknown currency: {code}")
        conv = amount / rates[code] * rates[out]
        if parts is not None:
            parts.append((amount, code, conv))
        return "(%.10f)" % conv

    expr = TOKEN.sub(sub, expr).replace(",", "")
    try:
        return _calc(expr)
    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero")


TARGET = re.compile(r"^(.*?)(?:\s+(?:to|in|into|as)\s+|\s*(?:->|→|=>)\s*)([A-Za-z]{3})\s*$", re.I)


def split_target(text):
    """'100 USD to SAR' -> ('100 USD', 'SAR')."""
    m = TARGET.match(text.strip())
    return (m.group(1), m.group(2).upper()) if m else (text, None)


def fmt_amt(a):
    return f"{a:,.4f}".rstrip("0").rstrip(".")


def fmt(value, code):
    d = 4 if code in ("XAU", "XAG") else 3 if code in THREE_DEC or code in ("AUG", "AGG") else 0 if code in ZERO_DEC else 2
    return f"{value:,.{d}f} {UNIT_LABEL.get(code, code)}"


# --------------------------------------------------------------------- app
def system_theme():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return "light" if winreg.QueryValueEx(k, "AppsUseLightTheme")[0] else "dark"
    except Exception:
        return "light"


def round_window(win):
    """Windows 11: round the corners of a borderless popup window (silently does nothing elsewhere)."""
    try:
        import ctypes
        win.update_idletasks()
        u32 = ctypes.windll.user32
        u32.GetParent.restype = ctypes.c_void_p
        u32.GetParent.argtypes = [ctypes.c_void_p]
        hwnd = u32.GetParent(win.winfo_id()) or win.winfo_id()
        val = ctypes.c_int(2)                       # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), 33, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass


def reveal(win):
    """Show a popup that was built invisibly (alpha 0) once it has been drawn and rounded."""
    try:
        win.update()
        round_window(win)
        win.attributes("-alpha", 1.0)
    except tk.TclError:
        pass


class Round(tk.Canvas):
    """A canvas that paints a rounded box and hosts a child frame (.inner) inside it."""

    def __init__(self, master, auto=True, fitw=False, radius=10, pad=3):
        super().__init__(master, width=1, height=10, highlightthickness=0, bd=0)
        self.auto, self.fitw, self.rad, self.pad = auto, fitw, radius, pad
        self.fill = self.edge = "#808080"
        self.inner = tk.Frame(self)
        self.win = self.create_window(pad, pad, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._canvas_cfg)
        if auto:
            self.inner.bind("<Configure>", self._inner_cfg)

    def colors(self, bg, fill, edge):
        self.configure(bg=bg)
        self.inner.configure(bg=fill)
        self.fill, self.edge = fill, edge
        self._draw()

    def sync(self):
        self.inner.update_idletasks()
        kw = {"height": self.inner.winfo_reqheight() + 2 * self.pad}
        if self.fitw:
            kw["width"] = self.inner.winfo_reqwidth() + 2 * self.pad
        self.configure(**kw)

    def _inner_cfg(self, _=None):
        kw = {"height": self.inner.winfo_reqheight() + 2 * self.pad}
        if self.fitw:
            kw["width"] = self.inner.winfo_reqwidth() + 2 * self.pad
        self.configure(**kw)

    def _canvas_cfg(self, e):
        kw = {}
        if not self.fitw:
            kw["width"] = max(e.width - 2 * self.pad, 1)
        if not self.auto:
            kw["height"] = max(e.height - 2 * self.pad, 1)
        if kw:
            self.itemconfigure(self.win, **kw)
        self._draw()

    def _draw(self):
        self.delete("bg")
        w, h, r = self.winfo_width() - 1, self.winfo_height() - 1, self.rad
        if w < 2 * r or h < 2 * r:
            return
        pts = [r, 0, r, 0, w - r, 0, w - r, 0, w, 0, w, r, w, r, w, h - r, w, h - r, w, h, w - r, h, w - r, h,
               r, h, r, h, 0, h, 0, h - r, 0, h - r, 0, r, 0, r, 0, 0]
        self.create_polygon(pts, smooth=True, fill=self.fill, outline=self.edge, tags="bg")
        self.tag_lower("bg")


class App:
    def __init__(self, root):
        self.root = root
        root.title("Currency Calculator")
        root.minsize(400, 460)
        self.panel_open = False
        self.panel_shift = 0
        self._draw_job = None
        self._click_job = None
        self._was_open = False
        self.settings_win = None
        self._set_was_open = False
        self.pick_slot = None
        self._slot_was_open = False
        self.metals_time, self._m_result, self._mfetch, self._cc_on = 0, None, False, False
        self.min_w, self.min_h = 400, 460
        self._rows = []
        self.picker = None
        self.pick_cb = None
        self._extra_on = False
        self._extra_key = None
        self.codes = list(FAVORITES)

        cache = load_json(RATES_FILE, {})
        self.rates = add_legacy(cache.get("rates") or None)
        self.rates_time = cache.get("time", 0)
        self.source = cache.get("source", "cache")
        self.change = cache.get("change") or {}
        self.change_date = cache.get("change_date", "")
        self.history = load_json(HISTORY_FILE, [])
        self.settings = load_json(SETTINGS_FILE, {"out": "USD"})
        self.settings.setdefault("recent", [self.settings.get("out", "USD")])
        self.settings.setdefault("also", ["USD", "SAR", "JOD"])
        self.settings.setdefault("also_on", [True, True, True])
        self.metal_prev = cache.get("metal_prev") or {}
        self.metal_prev_date = cache.get("metal_prev_date", "")
        self.metal_base = cache.get("metal_base") or {}
        self.update_metal_change()
        root.attributes("-topmost", bool(self.settings.get("topmost", False)))
        self.place_window()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.theme = None
        self._fetch_result = None
        self._fetching = False
        self.last_ok = None

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._build()
        self.apply_theme(self.effective_theme())
        self.refill_currencies()
        self.refresh_history()
        self.update_status()

        if not self.rates or time.time() - self.rates_time > REFRESH_SECONDS:
            self.start_fetch()
        root.after(3000, self.watch_theme)
        root.after(300, self.poll_fetch)
        root.after(60000, self.tick)
        self.update_minsize()
        self.entry.focus_set()

    # ---- UI
    def _build(self):
        self.main = tk.Frame(self.root)
        self.main.pack(side="left", fill="both", expand=True)
        r = self.main
        self.f_entry = tkfont.Font(family="Segoe UI", size=16)
        self.f_result = tkfont.Font(family="Segoe UI Semibold", size=24)
        self.top = tk.Frame(r)
        self.top.pack(fill="x", padx=16, pady=(14, 6))
        self.lbl_to = tk.Label(self.top, text="Convert to", font=("Segoe UI", 10))
        self.lbl_to.pack(side="left")
        self.out_var = tk.StringVar(value=self.settings.get("out", "USD"))
        self.out_box = Round(self.top, fitw=True)
        self.out_box.pack(side="left", padx=8)
        self.out_btn = tk.Button(self.out_box.inner, text="", font=("Segoe UI", 11), relief="flat", bd=0,
                                 padx=10, pady=3, cursor="hand2", command=self.open_picker)
        self.out_btn.pack()
        self.out_box.sync()
        self.out_btn.bind("<ButtonPress-1>", self._btn_press, add="+")
        self.out_var.trace_add("write", lambda *_: (self.out_btn.configure(text=f"{self.out_var.get()}   ▾"), self.out_box.sync()))
        self.out_var.set(self.out_var.get())
        self.btn_cc = tk.Button(self.top, text="Clear", relief="flat", font=("Segoe UI", 9), cursor="hand2",
                                command=self.clear_expr, bd=0, padx=8, pady=3)
        self.btn_cc.pack(side="right")
        self.btn_settings = tk.Button(self.top, text="⚙ Settings", relief="flat", font=("Segoe UI", 9), cursor="hand2",
                                      command=self.open_settings, bd=0, padx=8, pady=3)
        self.btn_settings.pack(side="right")
        self.btn_settings.bind("<ButtonPress-1>", self._set_press, add="+")
        self.pin_box = Round(self.top, fitw=True, radius=8)
        self.pin_box.pack(side="right", padx=(0, 4))
        self.btn_pin = tk.Button(self.pin_box.inner, text="Pin", relief="flat", font=("Segoe UI", 9), cursor="hand2",
                                 command=self.toggle_pin, bd=0, padx=6, pady=2)
        self.btn_pin.pack()
        self.pin_box.sync()

        self.card = Round(r)
        self.card.pack(fill="x", padx=16, pady=6)
        self.expr_var = tk.StringVar()
        self.expr_var.trace_add("write", lambda *_: self.recalc())
        self.erow = tk.Frame(self.card.inner)
        self.erow.pack(fill="x", padx=6, pady=(12, 4))
        self.entry = tk.Entry(self.erow, textvariable=self.expr_var, font=self.f_entry, relief="flat", bd=0)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Escape>", lambda e: self.clear_expr())
        self.entry.bind("<Configure>", lambda e: self.fit_fonts())
        self.entry.bind("<Return>", self.commit)
        self.entry.bind("<<Paste>>", self.on_paste)
        self.result = tk.Label(self.card.inner, text="0", anchor="e", font=self.f_result, cursor="hand2")
        self.result.pack(fill="x", padx=12, pady=(2, 2))
        self.result.bind("<Button-1>", self.copy_result)
        self.result.bind("<Button-3>", self.result_menu)
        self.extra = tk.Label(self.card.inner, text="", anchor="e", justify="right", font=("Segoe UI", 9))
        self.msg = tk.Label(self.card.inner, text="e.g.  10SAR + 15USD + 27JOD", anchor="e", justify="right", font=("Segoe UI", 9))
        self.msg.pack(fill="x", padx=12, pady=(0, 10))

        self.bottom = tk.Frame(r)
        self.bottom.pack(side="bottom", fill="x", padx=16, pady=(2, 10))
        self.status = tk.Label(self.bottom, text="", anchor="w", font=("Segoe UI", 8))
        self.status.pack(side="left", fill="x", expand=True)
        self.btn_refresh = tk.Button(self.bottom, text="⟳ Refresh", relief="flat", font=("Segoe UI", 8), cursor="hand2",
                                     command=self.start_fetch, bd=0, padx=6, pady=1)
        self.btn_refresh.pack(side="right")

        hdr = tk.Frame(r)
        hdr.pack(fill="x", padx=16, pady=(10, 2))
        self.lbl_hist = tk.Label(hdr, text="History", font=("Segoe UI Semibold", 10))
        self.lbl_hist.pack(side="left")
        self.btn_clear = tk.Button(hdr, text="Clear", relief="flat", font=("Segoe UI", 9), cursor="hand2", command=self.clear_history, bd=0, padx=8, pady=2)
        self.btn_clear.pack(side="right")
        self.hist_frame = Round(r, auto=False)
        self.hist_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        self.listbox = tk.Listbox(self.hist_frame.inner, font=("Segoe UI", 10), relief="flat", bd=0, activestyle="none", highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        self.listbox.bind("<Double-Button-1>", self.reuse_history)
        self.listbox.bind("<Button-3>", self.hist_menu)
        self.listbox.bind("<Delete>", self.delete_history)


        self._build_panel()

    def apply_theme(self, name):
        self.theme = name
        t = THEMES[name]
        self.root.configure(bg=t["bg"])
        for w in (self.top, self.lbl_to, self.status, self.bottom):
            w.configure(bg=t["bg"])
        self.lbl_to.configure(fg=t["fg"])
        self.status.configure(fg=t["sub"])
        for w in (self.btn_refresh, self.btn_clear, self.btn_settings, self.btn_cc):
            w.configure(bg=t["bg"], fg=t["accent"], activebackground=t["sel"], activeforeground=t["accent"])
        for w in (self.card, self.hist_frame):
            w.colors(t["bg"], t["card"], t["border"])
        self.entry.configure(bg=t["card"], fg=t["fg"], insertbackground=t["fg"], disabledbackground=t["card"])
        self.erow.configure(bg=t["card"])
        self.result.configure(bg=t["card"], fg=t["fg"])
        self.msg.configure(bg=t["card"], fg=t["sub"])
        self.extra.configure(bg=t["card"], fg=t["sub"])
        self.listbox.configure(bg=t["card"], fg=t["fg"], selectbackground=t["sel"], selectforeground=t["fg"])
        self.lbl_hist.master.configure(bg=t["bg"])
        self.lbl_hist.configure(bg=t["bg"], fg=t["fg"])
        self.style.configure("TCombobox", fieldbackground=t["card"], background=t["card"], foreground=t["fg"],
                             arrowcolor=t["fg"], bordercolor=t["border"], lightcolor=t["card"], darkcolor=t["card"])
        self.style.map("TCombobox", fieldbackground=[("readonly", t["card"])], foreground=[("readonly", t["fg"])],
                       selectbackground=[("readonly", t["card"])], selectforeground=[("readonly", t["fg"])])
        self.root.option_add("*TCombobox*Listbox.background", t["card"])
        self.root.option_add("*TCombobox*Listbox.foreground", t["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", t["bg"] if name == "dark" else "#ffffff")
        self.main.configure(bg=t["bg"])
        self.update_pin()
        self.out_btn.configure(bg=t["card"], fg=t["fg"], activebackground=t["sel"], activeforeground=t["fg"],
                               highlightthickness=0)
        self.out_box.colors(t["bg"], t["card"], t["border"])
        self.theme_panel(t)
        self.titlebar(name == "dark")

    def titlebar(self, dark):
        try:
            import ctypes
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            val = ctypes.c_int(1 if dark else 0)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), ctypes.sizeof(val))
        except Exception:
            pass

    def watch_theme(self):
        cur = self.effective_theme()
        if cur != self.theme:
            self.apply_theme(cur)
        self.root.after(3000, self.watch_theme)

    # ---- rates
    def refill_currencies(self):
        self.codes = ([m for m in METALS if m in self.rates] + sorted(c for c in self.rates if c in NAMES and c not in METALS)) if self.rates else sorted(FAVORITES)

    def start_fetch(self):
        if self._fetching:
            return
        self._fetching = True
        self.status.configure(text="Updating rates…")

        def work():
            try:
                r, name = fetch_rates()
                res = ("ok", merge_metals(r, fetch_metals(), self.rates), name)
                chg, cd, today = None, None, date.today().isoformat()
                if self.change_date != today:
                    try:
                        chg, cd = fetch_changes(), today
                    except Exception:
                        pass
                mp = fetch_metal_prev() if self.metal_prev_date != date.today().isoformat() else None
                self._fetch_result = res + (chg, cd, mp)
            except Exception as e:
                self._fetch_result = ("err", str(e))

        threading.Thread(target=work, daemon=True).start()

    def update_metal_change(self):
        """Up/down % for gold and silver: vs yesterday, or (if that isn't available) vs the first price seen in the last 24 h."""
        if not self.rates:
            return
        now = time.time()
        if now - self.metal_base.get("ts", 0) > 86400:
            self.metal_base = {"ts": now}
        for sym in ("XAU", "XAG"):
            if sym in self.rates and sym not in self.metal_base:
                self.metal_base[sym] = self.rates[sym]
            rate, ref = self.rates.get(sym), self.metal_prev.get(sym) or self.metal_base.get(sym)
            if rate and ref:
                self.change[sym] = (ref / rate - 1) * 100

    def _save_rates(self):
        save_json(RATES_FILE, {"rates": self.rates, "time": self.rates_time, "source": self.source,
                               "change": self.change, "change_date": self.change_date,
                               "metal_prev": self.metal_prev, "metal_prev_date": self.metal_prev_date,
                               "metal_base": self.metal_base})

    def start_metals(self):
        if self._mfetch:
            return
        self._mfetch = True

        def work():
            self._m_result = fetch_metals()

        threading.Thread(target=work, daemon=True).start()

    def poll_fetch(self):
        mres, self._m_result = self._m_result, None
        if mres is not None:
            self._mfetch, self.metals_time = False, time.time()
            if mres and self.rates:
                add_metals(self.rates, mres)
                self.update_metal_change()
                self._save_rates()
                self.recalc()
                self.draw_list()
        res, self._fetch_result = self._fetch_result, None
        if res:
            self._fetching = False
            if res[0] == "ok":
                self.rates, self.source, self.rates_time = res[1], res[2], time.time()
                self.metals_time = self.rates_time
                if res[3]:
                    self.change, self.change_date = res[3], res[4]
                if res[5]:
                    self.metal_prev, self.metal_prev_date = res[5], date.today().isoformat()
                self.update_metal_change()
                self._save_rates()
                self.refill_currencies()
                self.recalc()
                self.draw_list()
                self.update_status()
            else:
                self.update_status(offline=True)
        self.root.after(300, self.poll_fetch)

    def tick(self):
        if time.time() - self.rates_time > REFRESH_SECONDS:
            self.start_fetch()
        elif self.rates and not self._fetching and time.time() - self.metals_time > METALS_SECONDS:
            self.start_metals()
        self.update_status()
        self.root.after(60000, self.tick)

    def update_status(self, offline=False):
        if not self.rates:
            self.status.configure(text="No rates yet - connect to the internet and press Refresh")
            return
        mins = int((time.time() - self.rates_time) / 60)
        age = "just now" if mins < 1 else f"{mins} min ago" if mins < 90 else f"{mins // 60} h ago"
        prefix = "Offline - using cached rates from " if offline else "Rates updated "
        self.status.configure(text=f"{prefix}{age} · {self.source}")

    # ---- currency list panel (Alt+P)
    def _build_panel(self):
        self.panel = tk.Frame(self.root, width=PANEL_W)
        self.panel.pack_propagate(False)
        self.sep = tk.Frame(self.root, width=1)
        self.f_code = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.f_name = tkfont.Font(family="Segoe UI", size=9)
        self.f_rate = tkfont.Font(family="Segoe UI", size=10)
        self.p_hdr = tk.Frame(self.panel)
        self.p_hdr.pack(fill="x", padx=14, pady=(14, 4))
        self.p_title = tk.Label(self.p_hdr, text="Currencies", font=("Segoe UI Semibold", 12))
        self.p_title.pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.draw_list())
        self.search_wrap = Round(self.panel)
        self.search_wrap.pack(fill="x", padx=14, pady=4)
        self.search = tk.Entry(self.search_wrap.inner, textvariable=self.search_var, font=("Segoe UI", 10), relief="flat", bd=0)
        self.search.pack(fill="x", padx=8, pady=6)
        self.ph = tk.Label(self.search_wrap.inner, text="Search by code or name", font=("Segoe UI", 10), anchor="w", cursor="xterm")
        self.ph.place(x=10, rely=0.5, anchor="w")
        self.ph.bind("<Button-1>", lambda e: self.search.focus_set())
        self.search_var.trace_add("write", lambda *_: self.ph.place_forget() if self.search_var.get()
                                  else self.ph.place(x=10, rely=0.5, anchor="w"))
        self.p_cap = tk.Frame(self.panel)
        self.p_cap.pack(fill="x", padx=14, pady=(6, 2))
        self.cap_r = tk.Label(self.p_cap, text="per $1  /  value in $  ·  ▲▼ vs yesterday", font=("Segoe UI", 8))
        self.cap_r.pack(side="right")
        self.p_body = tk.Frame(self.panel)
        self.p_body.pack(fill="both", expand=True, pady=(0, 8))
        self.vsb = ttk.Scrollbar(self.p_body, orient="vertical")
        self.vsb.pack(side="right", fill="y")
        self.canvas = tk.Canvas(self.p_body, highlightthickness=0, bd=0, yscrollincrement=26, yscrollcommand=self.vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.configure(command=self.canvas.yview)
        self.canvas.bind("<Configure>", self._schedule_draw)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda e: (self.canvas.unbind_all("<MouseWheel>"), self.canvas.delete("hl")))
        self.canvas.configure(cursor="hand2")
        self.canvas.bind("<Button-1>", self._row_click)
        self.canvas.bind("<Double-Button-1>", self._row_double)
        self.canvas.bind("<Motion>", self._row_hover)
        self.root.bind("<Alt-p>", self.toggle_panel)
        self.root.bind("<Alt-P>", self.toggle_panel)

    def theme_panel(self, t):
        for w in (self.panel, self.p_hdr, self.p_cap, self.p_body):
            w.configure(bg=t["bg"])
        self.sep.configure(bg=t["border"])
        self.p_title.configure(bg=t["bg"], fg=t["fg"])
        for w in (self.cap_r,):
            w.configure(bg=t["bg"], fg=t["sub"])
        self.search_wrap.colors(t["bg"], t["card"], t["border"])
        self.ph.configure(bg=t["card"], fg=t["sub"])
        self.search.configure(bg=t["card"], fg=t["fg"], insertbackground=t["fg"])
        self.canvas.configure(bg=t["bg"])
        self.style.configure("Vertical.TScrollbar", background=t["border"], troughcolor=t["bg"], bordercolor=t["bg"],
                             arrowcolor=t["fg"], lightcolor=t["border"], darkcolor=t["border"])
        self.draw_list()

    def toggle_panel(self, _=None):
        m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", self.root.geometry())
        w, h, x, y = map(int, m.groups())
        if not self.panel_open:
            self.panel.pack(side="right", fill="y")
            self.sep.pack(side="right", fill="y")
            self.root.minsize(self.min_w + PANEL_W, self.min_h)
            self.root.geometry(f"{w + PANEL_W}x{h}+{x}+{y}")
            self.panel_open = True
            self.draw_list()
            self.search.focus_set()
        else:
            self.panel.pack_forget()
            self.sep.pack_forget()
            self.root.minsize(self.min_w, self.min_h)
            self.root.geometry(f"{max(w - PANEL_W, self.min_w)}x{h}+{x}+{y}")
            self.panel_open = False
            self.entry.focus_set()
        return "break"

    def _row_at(self, e):
        i = int(self.canvas.canvasy(e.y) // ROW_H)
        return self._rows[i] if 0 <= i < len(self._rows) else None

    def _row_click(self, e):          # single click: insert code (after a short wait, in case it is a double-click)
        code = self._row_at(e)
        if code:
            if self._click_job:
                self.root.after_cancel(self._click_job)
            self._click_job = self.root.after(300, lambda: self.insert_code(code))

    def _row_double(self, e):         # double click: use as output currency
        if self._click_job:
            self.root.after_cancel(self._click_job)
            self._click_job = None
        code = self._row_at(e)
        if code:
            self.out_var.set(code)
            self.on_out_change()
            self.msg.configure(text=f"Converting to {code}")

    def _row_hover(self, e):
        c = self.canvas
        c.delete("hl")
        i = int(c.canvasy(e.y) // ROW_H)
        if 0 <= i < len(self._rows) and self._rows[i]:
            c.create_rectangle(4, i * ROW_H, c.winfo_width() - 4, (i + 1) * ROW_H - 1,
                               fill=THEMES[self.theme]["sel"], outline="", tags="hl")
            c.tag_lower("hl")

    def insert_code(self, code):
        self._click_job = None
        code = METAL_PHRASE.get(code, code)
        before = self.entry.get()[:self.entry.index("insert")]
        self.entry.insert("insert", (" " if before[-1:].isalpha() else "") + code)
        self.entry.focus_set()

    def _wheel(self, e):
        self._smooth(self.canvas, e, ROW_H)

    def _smooth(self, c, e, step):
        """Pixel-accurate wheel/trackpad scrolling (step = pixels per mouse-wheel notch)."""
        c._acc = getattr(c, "_acc", 0.0) - e.delta * step / 120.0
        px = int(c._acc)
        if not px:
            return
        c._acc -= px
        try:
            h = float(str(c.cget("scrollregion")).replace("(", " ").replace(")", " ").replace(",", " ").split()[3])
        except Exception:
            return
        if h > 0:
            c.yview_moveto(max(0.0, c.yview()[0] * h + px) / h)

    def _schedule_draw(self, _=None):
        if self._draw_job:
            self.root.after_cancel(self._draw_job)
        self._draw_job = self.root.after(40, self.draw_list)

    def _fit(self, text, maxw):
        if self.f_name.measure(text) <= maxw:
            return text
        while text and self.f_name.measure(text + "…") > maxw:
            text = text[:-1]
        return text + "…"

    def draw_list(self):
        if not self.panel_open:
            return
        c, t = self.canvas, THEMES[self.theme]
        c.delete("all")
        self._rows = []
        w = max(c.winfo_width(), 200)
        if not self.rates:
            c.create_text(w / 2, 40, text="No rates yet - press Refresh", fill=t["sub"], font=self.f_name)
            return
        q = self.search_var.get().strip().lower()
        metals = [k for k in METALS if k in self.rates]
        others = sorted(k for k in self.rates if k in NAMES and k not in METALS)
        if q:
            seq = [k for k in metals + others if q in k.lower() or q in NAMES[k].lower()]
        else:
            seq = []
            if metals:
                seq += [("Gold & silver", "type  5g gold  ·  2oz silver  ·  100 USD to gold g")] + metals + [("Currencies", "")]
            seq += others
        y = 0
        for code in seq:
            if isinstance(code, tuple):                       # section heading
                self._rows.append(None)
                c.create_text(14, y + (22 if code[1] else 34), anchor="w", text=code[0].upper(), font=("Segoe UI", 8, "bold"), fill=t["sub"])
                if code[1]:
                    c.create_text(14, y + 38, anchor="w", text=code[1], font=self.f_name, fill=t["sub"])
                y += ROW_H
                continue
            name = NAMES[code]
            self._rows.append(code)
            rate = self.rates[code]
            txt = fmt_usd(rate) if code in METALS else f"{fmt_rate(rate)} / {fmt_usd(rate)}"
            rw = self.f_rate.measure(txt)
            c.create_text(14, y + 8, anchor="nw", text=code, font=self.f_code, fill=t["fg"])
            c.create_text(14, y + 29, anchor="nw", text=self._fit(name, w - 14 - rw - 30), font=self.f_name, fill=t["sub"])
            chg = self.change.get(CHG_ALIAS.get(code, code))
            if chg is None or code == "USD":
                c.create_text(w - 14, y + ROW_H // 2, anchor="e", text=txt, font=self.f_rate, fill=t["fg"])
            else:
                c.create_text(w - 14, y + 18, anchor="e", text=txt, font=self.f_rate, fill=t["fg"])
                if abs(chg) < 0.005:
                    note, col = "•  0.00%", t["sub"]
                else:
                    note, col = ("▲ " if chg > 0 else "▼ ") + f"{abs(chg):.2f}%", t["up" if chg > 0 else "down"]
                c.create_text(w - 14, y + 37, anchor="e", text=note, font=self.f_name, fill=col)
            c.create_line(14, y + ROW_H - 1, w - 14, y + ROW_H - 1, fill=t["border"])
            y += ROW_H
        c.configure(scrollregion=(0, 0, w, max(y, 1)))
    def update_minsize(self):
        self.root.update_idletasks()
        self.min_w = max(self.top.winfo_reqwidth() + 32, 380)
        self.min_h = self.top.winfo_reqheight() + self.card.inner.winfo_reqheight() + 60 + self.bottom.winfo_reqheight() + 170
        self.root.minsize(self.min_w + (PANEL_W if self.panel_open else 0), self.min_h)

    # ---- theme mode (auto / light / dark)
    def mode(self):
        return self.settings.get("theme", "auto")

    def effective_theme(self):
        m = self.mode()
        return system_theme() if m == "auto" else m

    def set_theme(self, m):
        self.settings["theme"] = m
        save_json(SETTINGS_FILE, self.settings)
        self.apply_theme(self.effective_theme())

    # ---- settings popup (theme, currency codes, about)
    def _set_press(self, _=None):
        self._set_was_open = self.settings_win is not None

    def open_settings(self, _=None):
        if self._set_was_open:
            self._set_was_open = False
            return self.close_settings()
        if self.settings_win:
            return self.close_settings()
        t = THEMES[self.theme]
        pw = self.settings_win = tk.Toplevel(self.root)
        pw.withdraw()
        pw.overrideredirect(True)
        pw.attributes("-topmost", True)
        pw.attributes("-alpha", 0.0)
        pw.configure(bg=t["border"])
        inner = self._set_inner = tk.Frame(pw, bg=t["card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        self._build_settings(inner, t)
        pw.update_idletasks()
        w = max(260, pw.winfo_reqwidth())
        x = self.btn_settings.winfo_rootx() + self.btn_settings.winfo_width() - w
        y = self.btn_settings.winfo_rooty() + self.btn_settings.winfo_height() + 2
        pw.geometry(f"{w}x{pw.winfo_reqheight()}+{x}+{y}")
        pw.deiconify()
        pw.bind("<FocusOut>", lambda e: self.root.after(150, self._settings_check))
        pw.bind("<Escape>", lambda e: self.close_settings())
        pw.focus_force()
        reveal(pw)

    def _build_settings(self, inner, t):

        def label(text, size=9, bold=False, color=None, pady=(0, 0)):
            tk.Label(inner, text=text, anchor="w", bg=t["card"], fg=color or t["fg"],
                     font=("Segoe UI", size, "bold" if bold else "normal")).pack(fill="x", padx=14, pady=pady)

        def rule():
            tk.Frame(inner, height=1, bg=t["border"]).pack(fill="x", padx=14, pady=10)

        def rbtn(parent, text, cmd, fill, fg, active, fitw=False, anchor="center", font=("Segoe UI", 9), padx=0, pady=3):
            box = Round(parent, fitw=fitw, radius=8, pad=3)
            b = tk.Button(box.inner, text=text, command=cmd, anchor=anchor, relief="flat", bd=0, cursor="hand2",
                          font=font, padx=padx, pady=pady, bg=fill, fg=fg, activebackground=active, activeforeground=fg)
            b.pack() if fitw else b.pack(fill="both", expand=True)
            box.colors(t["card"], fill, fill)
            box.sync()
            return box, b

        label("Theme", 9, True, t["sub"], (12, 6))
        seg = tk.Frame(inner, bg=t["card"])
        seg.pack(fill="x", padx=14)
        on_fg = "#000000" if self.theme == "dark" else "#ffffff"
        for m, txt in (("auto", "Auto"), ("light", "Light"), ("dark", "Dark")):
            on = self.mode() == m
            box, _b = rbtn(seg, txt, lambda m=m: self._settings_theme(m), t["accent"] if on else t["sel"],
                           on_fg if on else t["fg"], t["accent"] if on else t["border"])
            box.pack(side="left", fill="x", expand=True, padx=(0, 4))
        rule()
        def row(text, cmd):
            box, b = rbtn(inner, text, cmd, t["card"], t["fg"], t["sel"], anchor="w", font=("Segoe UI", 10), padx=3, pady=3)
            box.pack(fill="x", padx=8)

            def hover(on):
                c = t["sel"] if on else t["card"]
                box.colors(t["card"], c, c)
                b.configure(bg=c)
            b.bind("<Enter>", lambda e: hover(True))
            b.bind("<Leave>", lambda e: hover(False))

        label("Result display", 9, True, t["sub"], (0, 2))
        for key, txt in (("show_breakdown", "Breakdown line"), ("show_also", "Total in other currencies")):
            row(("✓  " if self.settings.get(key, True) else "☐  ") + txt, lambda k=key: self._settings_toggle(k))
        slots = tk.Frame(inner, bg=t["card"])
        slots.pack(fill="x", padx=14, pady=(2, 0))
        tk.Label(slots, text="Show in:", bg=t["card"], fg=t["sub"], font=("Segoe UI", 9)).pack(side="left")
        flags = self.settings.get("also_on", [True, True, True])
        for i, code in enumerate(self.settings["also"]):
            on = flags[i] if i < len(flags) else True
            tg = tk.Button(slots, text="✓" if on else "☐", relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 10),
                           padx=2, pady=0, bg=t["card"], fg=t["accent"] if on else t["sub"], activebackground=t["card"],
                           activeforeground=t["fg"], command=lambda i=i: self._slot_toggle(i))
            tg.pack(side="left", padx=(8, 0))
            box, b = rbtn(slots, code, None, t["sel"], t["fg"] if on else t["sub"], t["border"], fitw=True,
                          font=("Segoe UI", 9, "bold"), padx=6, pady=2)
            b.configure(command=lambda i=i, b=b: self._slot_pick(i, b))
            b.bind("<ButtonPress-1>", lambda e, i=i: self._slot_press(i), add="+")
            box.pack(side="left", padx=(2, 0))
        tk.Label(inner, text="Tick to show  ·  click a code to change it", bg=t["card"], fg=t["sub"],
                 font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=14, pady=(2, 0))
        rule()
        row(f"{'Hide' if self.panel_open else 'Show'} currency codes   (Alt+P)", self._settings_codes)
        rule()
        label("About", 9, True, t["sub"])
        label("Currency Calculator", 10, False, None, (4, 0))
        label(f"Version {VERSION}", 9, False, t["sub"], (0, 12))

    def _refresh_settings(self):
        """Rebuild the settings contents in place (the popup stays open, so nothing flashes)."""
        pw = self.settings_win
        if not pw:
            return
        t = THEMES[self.theme]
        pw.configure(bg=t["border"])
        old = self._set_inner
        new = tk.Frame(pw, bg=t["card"])
        self._build_settings(new, t)
        new.pack(fill="both", expand=True, padx=1, pady=1)
        old.destroy()
        self._set_inner = new
        pw.update_idletasks()
        w = max(260, pw.winfo_reqwidth())
        x = self.btn_settings.winfo_rootx() + self.btn_settings.winfo_width() - w
        y = self.btn_settings.winfo_rooty() + self.btn_settings.winfo_height() + 2
        pw.geometry(f"{w}x{pw.winfo_reqheight()}+{x}+{y}")

    def _settings_theme(self, m):
        self.set_theme(m)
        self._refresh_settings()      # rebuild in place so the popup itself picks up the new colours

    def _settings_toggle(self, key):
        self.settings[key] = not self.settings.get(key, True)
        save_json(SETTINGS_FILE, self.settings)
        self._refresh_settings()
        self.recalc()

    def _slot_press(self, i):
        self._slot_was_open = self.picker is not None and self.pick_slot == i

    def _slot_pick(self, i, btn):
        if self._slot_was_open:           # this click is the second one on the same button: just close the list
            self._slot_was_open = False
            return self.close_picker()
        self.pick_slot = i
        at = (btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height() + 2)
        self.open_picker(at=at, on_pick=lambda code: self._set_slot(i, code))

    def _set_slot(self, i, code):
        also = list(self.settings["also"])
        also[i] = code
        self.settings["also"] = also
        save_json(SETTINGS_FILE, self.settings)
        self.recalc()
        self.root.after(60, self._refresh_settings)

    def _slot_toggle(self, i):
        on = list(self.settings.get("also_on", [True, True, True]))
        while len(on) < 3:
            on.append(True)
        on[i] = not on[i]
        self.settings["also_on"] = on
        save_json(SETTINGS_FILE, self.settings)
        self.recalc()
        self._refresh_settings()

    def _reopen_settings(self):
        self.close_settings()
        self.open_settings()          # rebuild so the button shows the new currency

    def _settings_codes(self):
        self.close_settings()
        self.toggle_panel()

    def _settings_check(self):
        if self.settings_win and not self.picker:
            w = self.root.focus_get()
            if w is None or not str(w).startswith(str(self.settings_win)):
                self.close_settings()

    def close_settings(self):
        if self.settings_win:
            self.settings_win.destroy()
            self.settings_win = None
            self.entry.focus_set()

    # ---- shrink long text so it always fits
    def fit_fonts(self):
        self.extra.configure(wraplength=max(self.result.winfo_width() - 12, 120))
        for font, text, widget, hi, lo in ((self.f_entry, self.expr_var.get(), self.entry, 16, 10),
                                           (self.f_result, self.result.cget("text"), self.result, 24, 12)):
            avail = widget.winfo_width() - 16
            size = hi
            font.configure(size=size)
            while size > lo and avail > 0 and font.measure(text) > avail:
                size -= 1
                font.configure(size=size)

    # ---- searchable output-currency picker
    def _btn_press(self, _=None):
        self._was_open = self.picker is not None

    def open_picker(self, _=None, at=None, on_pick=None):
        if at is None:
            if self._was_open:        # this click is the one that should close it
                self._was_open = False
                return self.close_picker()
            if self.picker:
                return self.close_picker()
            self.pick_slot = None
        elif self.picker:
            self.close_picker()
        self.pick_cb = on_pick
        t = THEMES[self.theme]
        pw = self.picker = tk.Toplevel(self.root)
        pw.overrideredirect(True)
        pw.attributes("-topmost", True)
        pw.attributes("-alpha", 0.0)
        pw.configure(bg=t["border"])
        x, y = at or (self.out_btn.winfo_rootx(), self.out_btn.winfo_rooty() + self.out_btn.winfo_height() + 2)
        x = max(0, min(x, self.root.winfo_screenwidth() - 310))
        pw.geometry(f"300x290+{x}+{y}")
        inner = tk.Frame(pw, bg=t["card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        self.pick_var = tk.StringVar()
        ent = tk.Entry(inner, textvariable=self.pick_var, font=("Segoe UI", 11), relief="flat", bd=0,
                       bg=t["card"], fg=t["fg"], insertbackground=t["fg"])
        ent.pack(fill="x", padx=10, pady=(10, 6))
        body = tk.Frame(inner, bg=t["card"])
        body.pack(fill="both", expand=True, padx=(6, 0), pady=(0, 6))
        vsb = ttk.Scrollbar(body, orient="vertical")
        vsb.pack(side="right", fill="y")
        c = self.pick_canvas = tk.Canvas(body, bg=t["card"], highlightthickness=0, bd=0, cursor="hand2",
                                         yscrollcommand=vsb.set)
        c.pack(side="left", fill="both", expand=True)
        vsb.configure(command=c.yview)
        self.pick_rows, self.pick_sel = [], None
        self.pick_var.trace_add("write", lambda *_: self._pick_filter())
        ent.bind("<Down>", lambda e: self._pick_move(1))
        ent.bind("<Up>", lambda e: self._pick_move(-1))
        ent.bind("<Return>", lambda e: self._pick_choose())
        ent.bind("<Escape>", lambda e: self.close_picker())
        c.bind("<Configure>", lambda e: self._pick_draw())
        c.bind("<Button-1>", lambda e: self._pick_choose(self._pick_index(e)))
        c.bind("<Motion>", self._pick_hover)
        pw.bind("<MouseWheel>", lambda e: self._smooth(c, e, PICK_H * 2))
        pw.bind("<FocusOut>", lambda e: self.root.after(150, self._pick_check))
        self._pick_filter()
        pw.focus_force()
        reveal(pw)
        ent.focus_set()

    def _pick_filter(self):
        q = self.pick_var.get().strip().lower()
        if q:
            rows = [(c, NAMES.get(c, "")) for c in self.codes if q in c.lower() or q in NAMES.get(c, "").lower()]
        else:
            rows = []
            recent = [c for c in self.settings.get("recent", []) if c in self.codes]
            if recent:
                rows.append((None, "Recent"))
                rows += [(c, NAMES.get(c, "")) for c in recent]
            rows.append((None, "All currencies"))
            rows += [(c, NAMES.get(c, "")) for c in self.codes]
        self.pick_rows = rows
        self.pick_sel = next((i for i, r in enumerate(rows) if r[0]), None)
        self.pick_canvas.yview_moveto(0)
        self._pick_draw()

    def _pick_draw(self):
        c, t = self.pick_canvas, THEMES[self.theme]
        c.delete("all")
        for i, (code, label) in enumerate(self.pick_rows):
            y = i * PICK_H
            if code is None:
                c.create_text(12, y + PICK_H - 6, anchor="sw", text=label, font=("Segoe UI", 8, "bold"), fill=t["sub"])
            else:
                c.create_text(12, y + PICK_H // 2, anchor="w", text=code, font=("Segoe UI", 10, "bold"), fill=t["fg"])
                c.create_text(64, y + PICK_H // 2, anchor="w", text=label, font=("Segoe UI", 9), fill=t["sub"])
        c.configure(scrollregion=(0, 0, max(c.winfo_width(), 100), max(len(self.pick_rows) * PICK_H, 1)))
        self._pick_mark()

    def _pick_mark(self):
        c = self.pick_canvas
        c.delete("sel")
        if self.pick_sel is not None:
            c.create_rectangle(2, self.pick_sel * PICK_H, max(c.winfo_width(), 100) - 2, (self.pick_sel + 1) * PICK_H,
                               fill=THEMES[self.theme]["sel"], outline="", tags="sel")
            c.tag_lower("sel")

    def _pick_index(self, e):
        i = int(self.pick_canvas.canvasy(e.y) // PICK_H)
        return i if 0 <= i < len(self.pick_rows) else None

    def _pick_hover(self, e):
        i = self._pick_index(e)
        if i is not None and self.pick_rows[i][0] is not None and i != self.pick_sel:
            self.pick_sel = i
            self._pick_mark()

    def _pick_see(self, i):
        c = self.pick_canvas
        h = float(len(self.pick_rows) * PICK_H)
        top, bot = c.yview()[0] * h, c.yview()[1] * h
        y0, y1 = i * PICK_H, (i + 1) * PICK_H
        if y0 < top:
            c.yview_moveto(y0 / h)
        elif y1 > bot:
            c.yview_moveto((y1 - (bot - top)) / h)

    def _pick_move(self, d):
        rows = self.pick_rows
        j = (-1 if self.pick_sel is None else self.pick_sel) + d
        while 0 <= j < len(rows) and rows[j][0] is None:
            j += d
        if 0 <= j < len(rows):
            self.pick_sel = j
            self._pick_mark()
            self._pick_see(j - 1 if j > 0 and rows[j - 1][0] is None else j)
        return "break"

    def _pick_choose(self, i=None):
        if i is None:
            i = self.pick_sel
        if i is None or not (0 <= i < len(self.pick_rows)):
            return
        code = self.pick_rows[i][0]
        if code is None:              # clicked a section heading
            return
        cb = self.pick_cb
        if cb:
            cb(code)
        else:
            self.out_var.set(code)
            self.on_out_change()
        self.close_picker()

    def _pick_check(self):
        if self.picker:
            w = self.root.focus_get()
            if w is None or not str(w).startswith(str(self.picker)):
                self.close_picker()

    def close_picker(self):
        if self.picker:
            self.picker.destroy()
            self.picker = None
            if self.settings_win:
                self.settings_win.focus_force()      # back to the settings popup that opened the picker
            else:
                self.entry.focus_set()

    # ---- calculation
    def on_out_change(self, _=None):
        code = self.out_var.get()
        self.settings["out"] = code
        self.settings["recent"] = ([code] + [c for c in self.settings.get("recent", []) if c != code])[:5]
        save_json(SETTINGS_FILE, self.settings)
        self.recalc()

    def clear_expr(self):
        self.expr_var.set("")
        self.entry.focus_set()

    def recalc(self):
        self.root.after_idle(self.fit_fonts)
        body, tgt = split_target(metal_fix(self.expr_var.get()))
        out = tgt or self.out_var.get()
        self.cur_out = out
        parts = []
        try:
            if tgt and self.rates and tgt not in self.rates:
                raise ValueError(f"Unknown currency: {tgt}")
            v = evaluate(body, out, self.rates, parts)
        except ValueError as e:
            self.last_ok = None
            self.msg.configure(text=str(e))
            return self._extra("")
        if v is None:
            self.last_ok = None
            self.result.configure(text="0")
            self.msg.configure(text="e.g.  10SAR + 15USD + 27JOD   or   100 USD to SAR")
            return self._extra("")
        self.last_ok = fmt(v, out)
        self.result.configure(text=self.last_ok)
        self.msg.configure(text=(f"One-off conversion to {out}\n" if tgt else "") + "Click result to copy · Enter to save")
        lines = []
        if self.settings.get("show_breakdown", True) and parts and (len(parts) > 1 or parts[0][1] != out):
            lines.append("  ·  ".join(f"{fmt_amt(a)} {UNIT_LABEL.get(c, c)} = {fmt(x, out)}" for a, c, x in parts))
        if self.settings.get("show_also", True):
            tot = []
            flags = self.settings.get("also_on", [True, True, True])
            for k, c in enumerate(self.settings.get("also", [])):
                if k < len(flags) and not flags[k]:
                    continue
                if c != out and c in (self.rates or {}):
                    try:
                        tot.append(fmt(evaluate(body, c, self.rates), c))
                    except ValueError:
                        pass
            if tot:
                lines.append("≈ " + "  ·  ".join(tot))
        self._extra("\n".join(lines))

    def _extra(self, text):
        if text:
            self.extra.configure(text=text)
            if not self._extra_on:
                self.extra.pack(fill="x", padx=12, before=self.msg)
                self._extra_on = True
        elif self._extra_on:
            self.extra.pack_forget()
            self._extra_on = False
        key = (self._extra_on, text.count("\n"))
        if key != self._extra_key:
            self._extra_key = key
            self.root.after_idle(self.update_minsize)

    def copy_result(self, _=None):
        if self.last_ok:
            self.copy_text(self.last_ok.split(" ", 1)[0].replace(",", ""))

    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.msg.configure(text="Copied!")

    def _menu(self):
        t = THEMES[self.theme]
        return tk.Menu(self.root, tearoff=0, bg=t["card"], fg=t["fg"], activebackground=t["sel"],
                       activeforeground=t["fg"], bd=0, relief="flat")

    def result_menu(self, e):
        if not self.last_ok:
            return
        m, full = self._menu(), self.last_ok
        m.add_command(label="Copy number", command=lambda: self.copy_text(full.split(" ", 1)[0].replace(",", "")))
        m.add_command(label="Copy with currency", command=lambda: self.copy_text(full))
        m.add_command(label="Copy expression and result",
                      command=lambda: self.copy_text(f"{self.expr_var.get().strip()} = {full}"))
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def on_paste(self, _=None):
        try:
            txt = self.root.clipboard_get()
        except tk.TclError:
            return "break"
        txt = re.sub(r"\s+", " ", " + ".join(l.strip() for l in txt.splitlines() if l.strip()))
        try:
            self.entry.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        self.entry.insert("insert", txt)
        return "break"

    # ---- pin / window
    def toggle_pin(self):
        on = not self.settings.get("topmost", False)
        self.settings["topmost"] = on
        save_json(SETTINGS_FILE, self.settings)
        self.root.attributes("-topmost", on)
        self.update_pin()
        self.msg.configure(text="Always on top: " + ("on" if on else "off"))

    def update_pin(self):
        t = THEMES[self.theme]
        if self.settings.get("topmost", False):
            fg = "#000000" if self.theme == "dark" else "#ffffff"
            self.pin_box.colors(t["bg"], t["accent"], t["accent"])
            self.btn_pin.configure(bg=t["accent"], fg=fg, activebackground=t["accent"], activeforeground=fg)
        else:
            self.pin_box.colors(t["bg"], t["bg"], t["bg"])
            self.btn_pin.configure(bg=t["bg"], fg=t["fg"], activebackground=t["sel"], activeforeground=t["fg"])

    def place_window(self):
        r = self.root
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        g = self.settings.get("geom")
        if isinstance(g, list) and len(g) == 4:
            w, h, x, y = g
            if 300 <= w <= sw and 300 <= h <= sh and -w + 120 < x < sw - 120 and 0 <= y < sh - 80:
                return r.geometry(f"{w}x{h}+{x}+{y}")
        w, h = 430, 600
        r.geometry(f"{w}x{h}+{(sw - w) // 2}+{max((sh - h) // 2 - 20, 0)}")

    def on_close(self):
        try:
            w, h, x, y = map(int, re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", self.root.geometry()).groups())
            self.settings["geom"] = [w - (PANEL_W if self.panel_open else 0), h, x, y]
            save_json(SETTINGS_FILE, self.settings)
        except Exception:
            pass
        self.root.destroy()

    # ---- history
    def commit(self, _=None):
        if not self.last_ok:
            return
        item = {"expr": self.expr_var.get().strip(), "out": self.cur_out, "result": self.last_ok, "t": self.rates_time}
        if not self.history or self.history[0] != item:
            self.history.insert(0, item)
            del self.history[100:]
            save_json(HISTORY_FILE, self.history)
            self.refresh_history()

    def refresh_history(self):
        self.listbox.delete(0, "end")
        for h in self.history:
            when = time.strftime("   ·  rates %b %d, %H:%M", time.localtime(h["t"])) if h.get("t") else ""
            self.listbox.insert("end", f"{h['expr']}  =  {h['result']}{when}")

    def reuse_history(self, _=None):
        sel = self.listbox.curselection()
        if sel:
            h = self.history[sel[0]]
            if not split_target(h["expr"])[1]:
                self.out_var.set(h["out"])
                self.on_out_change()
            self.expr_var.set(h["expr"])
            self.entry.focus_set()
            self.entry.icursor("end")

    def hist_menu(self, e):
        i = self.listbox.nearest(e.y)
        bb = self.listbox.bbox(i)
        if not (0 <= i < len(self.history)) or not bb or e.y > bb[1] + bb[3]:
            return
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(i)
        h, m = self.history[i], self._menu()
        m.add_command(label="Copy expression and result", command=lambda: self.copy_text(f"{h['expr']} = {h['result']}"))
        m.add_command(label="Copy result", command=lambda: self.copy_text(h["result"]))
        m.add_separator()
        m.add_command(label="Delete entry", command=lambda: self.delete_history(i))
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def delete_history(self, i=None):
        if not isinstance(i, int):
            sel = self.listbox.curselection()
            i = sel[0] if sel else None
        if i is not None and 0 <= i < len(self.history):
            del self.history[i]
            save_json(HISTORY_FILE, self.history)
            self.refresh_history()
            if self.history:
                self.listbox.selection_set(min(i, len(self.history) - 1))

    def clear_history(self):
        self.history = []
        save_json(HISTORY_FILE, self.history)
        self.refresh_history()


def main():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
