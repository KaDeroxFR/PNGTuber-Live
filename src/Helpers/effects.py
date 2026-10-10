import math
import colorsys
from PIL import Image, ImageEnhance

EFFECTS = {}
NUMERIC = ("dx", "dy", "scale", "sx", "sy", "rot", "bright", "sat", "opacity", "hue")


def effect(name, params, animated=True):
    def wrap(fn):
        EFFECTS[name] = {"params": params, "animated": animated, "apply": fn}
        return fn
    return wrap


def _freq(p):
    return p.get("speed", 8) / 4.0


def _wave(t, p):
    return math.sin(2 * math.pi * _freq(p) * t)


def _hash(seed, i):
    v = math.sin(i * 127.1 + seed * 311.7) * 43758.5453
    return (v - math.floor(v)) * 2 - 1


def _noise(seed, x):
    i = math.floor(x)
    f = x - i
    f = f * f * (3 - 2 * f)
    return _hash(seed, i) * (1 - f) + _hash(seed, i + 1) * f


@effect("Shake", [("strength", "Strength", 1, 40, 8, "px"), ("speed", "Speed", 1, 40, 24, "")])
def _shake(st, t, p):
    x = t * p["speed"] * 0.6
    st["dx"] += _noise(1, x) * p["strength"]
    st["dy"] += _noise(2, x) * p["strength"]


@effect("Bounce", [("height", "Height", 1, 80, 25, "px"), ("speed", "Speed", 1, 40, 10, "")])
def _bounce(st, t, p):
    st["dy"] -= abs(math.sin(math.pi * _freq(p) * t)) * p["height"]


@effect("Float", [("height", "Height", 1, 60, 10, "px"), ("speed", "Speed", 1, 40, 4, "")])
def _float(st, t, p):
    st["dy"] += _wave(t, p) * p["height"]


@effect("Wobble", [("angle", "Angle", 1, 45, 8, "°"), ("speed", "Speed", 1, 40, 8, "")])
def _wobble(st, t, p):
    st["rot"] += _wave(t, p) * p["angle"]


@effect("Pulse", [("amount", "Amount", 1, 100, 10, "%"), ("speed", "Speed", 1, 40, 10, "")])
def _pulse(st, t, p):
    st["scale"] *= 1 + p["amount"] / 100 * (0.5 + 0.5 * _wave(t, p))


@effect("Squash & Stretch", [("amount", "Amount", 1, 50, 10, "%"), ("speed", "Speed", 1, 40, 10, "")])
def _squash(st, t, p):
    w = _wave(t, p) * p["amount"] / 100
    st["sx"] *= 1 - w
    st["sy"] *= 1 + w


@effect("Breathing", [("amount", "Amount", 1, 20, 3, "%"), ("speed", "Speed", 1, 40, 3, "")])
def _breathing(st, t, p):
    st["sy"] *= 1 + p["amount"] / 100 * _wave(t, p)


@effect("Flash", [("amount", "Amount", 1, 100, 40, "%"), ("speed", "Speed", 1, 40, 12, "")])
def _flash(st, t, p):
    st["bright"] *= 1 + p["amount"] / 100 * (0.5 + 0.5 * _wave(t, p))


@effect("Flicker", [("amount", "Amount", 1, 100, 60, "%"), ("speed", "Speed", 1, 40, 16, "")])
def _flicker(st, t, p):
    if _wave(t, p) > 0:
        st["opacity"] *= 1 - p["amount"] / 100


@effect("Hue cycle", [("speed", "Speed", 1, 40, 4, "")])
def _hue_cycle(st, t, p):
    st["hue"] += (_freq(p) * t % 1.0) * 256


@effect("Scale up", [("amount", "Amount", 1, 100, 15, "%")], animated=False)
def _scale_up(st, t, p):
    st["scale"] *= 1 + p["amount"] / 100


@effect("Tilt", [("angle", "Angle", -45, 45, 10, "°")], animated=False)
def _tilt(st, t, p):
    st["rot"] += p["angle"]


@effect("Blackout", [("amount", "Darkness", 1, 100, 60, "%")], animated=False)
def _blackout(st, t, p):
    st["bright"] *= 1 - p["amount"] / 100


@effect("Fade", [("amount", "Amount", 1, 100, 40, "%")], animated=False)
def _fade(st, t, p):
    st["opacity"] *= 1 - p["amount"] / 100


@effect("Grayscale", [("amount", "Amount", 1, 100, 100, "%")], animated=False)
def _grayscale(st, t, p):
    st["sat"] *= 1 - p["amount"] / 100


@effect("Brighten", [("amount", "Amount", 1, 100, 30, "%")], animated=False)
def _brighten(st, t, p):
    st["bright"] *= 1 + p["amount"] / 100


@effect("Tint", [("hue", "Color", 0, 360, 0, "°"), ("strength", "Strength", 1, 100, 40, "%")], animated=False)
def _tint(st, t, p):
    r, g, b = colorsys.hsv_to_rgb(p["hue"] / 360, 1, 1)
    st["tints"].append(((int(r * 255), int(g * 255), int(b * 255)), p["strength"] / 100))


def _state():
    return dict(dx=0.0, dy=0.0, scale=1.0, sx=1.0, sy=1.0, rot=0.0,
                bright=1.0, sat=1.0, opacity=1.0, hue=0.0, tints=[])


def compute_state(effects, t):
    st = _state()
    for name, params in effects:
        spec = EFFECTS.get(name)
        if spec:
            spec["apply"](st, t, params)
    return st


def blend_states(a, b, k):
    out = {key: a[key] + (b[key] - a[key]) * k for key in NUMERIC}
    out["tints"] = b["tints"]
    return out


def state_key(st):
    return (
        tuple(round(st[key], 2) for key in NUMERIC),
        tuple((c, round(s, 2)) for c, s in st["tints"]),
    )


def _adjust(base, st):
    rgb = base.convert("RGB")
    alpha = base.getchannel("A")

    shift = round(st["hue"]) % 256
    if shift:
        h, s, v = rgb.convert("HSV").split()
        h = h.point([(i + shift) % 256 for i in range(256)])
        rgb = Image.merge("HSV", (h, s, v)).convert("RGB")
    if abs(st["sat"] - 1) > 1e-3:
        rgb = ImageEnhance.Color(rgb).enhance(max(0.0, st["sat"]))
    if abs(st["bright"] - 1) > 1e-3:
        rgb = ImageEnhance.Brightness(rgb).enhance(max(0.0, st["bright"]))
    for color, k in st["tints"]:
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, color), k)
    if st["opacity"] < 0.999:
        op = max(0.0, st["opacity"])
        alpha = alpha.point([int(i * op) for i in range(256)])

    rgb.putalpha(alpha)
    return rgb


def render_state(base, box, st, cache):
    key = (
        id(base),
        round(st["hue"]) % 256,
        round(st["sat"], 2),
        round(st["bright"], 2),
        round(st["opacity"], 2),
        tuple((c, round(s, 2)) for c, s in st["tints"]),
    )
    img = cache.get(key)
    if img is None:
        img = _adjust(base, st)
        if len(cache) > 150:
            cache.clear()
        cache[key] = img

    sx = max(0.01, st["scale"] * st["sx"])
    sy = max(0.01, st["scale"] * st["sy"])
    theta = math.radians(st["rot"])
    cs, sn = math.cos(theta), math.sin(theta)
    w, h = img.size
    ox = box[0] / 2 + st["dx"]
    oy = box[1] / 2 + st["dy"]

    coeffs = (
        cs / sx, -sn / sx, w / 2 + (-cs * ox + sn * oy) / sx,
        sn / sy, cs / sy, h / 2 + (-sn * ox - cs * oy) / sy,
    )
    return img.transform(box, Image.AFFINE, coeffs, resample=Image.BICUBIC)