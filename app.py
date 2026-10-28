import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import os
import io
import tempfile
import math
import imageio
from datetime import datetime, timedelta

st.set_page_config(
    page_title="CropScan Demo",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "CropScan Offline Demo"
WIDTH, HEIGHT = 720, 404
FPS = 15
RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

DISEASE_CATALOG = [
    {"disease": "Tomato Late Blight", "crop": "Tomato", "pattern": "blight_necrotic", "note": "Water-soaked dark lesions; spreads fast in cool wet weather."},
    {"disease": "Tomato Early Blight", "crop": "Tomato", "pattern": "target_spot", "note": "Concentric brown spots on older leaves."},
    {"disease": "Tomato Septoria Leaf Spot", "crop": "Tomato", "pattern": "target_spot", "note": "Small circular spots with dark borders."},
    {"disease": "Tomato Bacterial Spot", "crop": "Tomato", "pattern": "spot_scorch", "note": "Dark angular lesions, often on fruit and leaves."},
    {"disease": "Tomato Mosaic Virus", "crop": "Tomato", "pattern": "yellow_viral", "note": "Mottled yellow/green foliage and distorted growth."},
    {"disease": "Tomato Yellow Leaf Curl Virus", "crop": "Tomato", "pattern": "yellow_viral", "note": "Upward curling, yellowing leaves; whitefly spread."},
    {"disease": "Tomato Powdery Mildew", "crop": "Tomato", "pattern": "powdery_mildew", "note": "White powdery patches on upper leaf surface."},
    {"disease": "Tomato Anthracnose", "crop": "Tomato", "pattern": "spot_scorch", "note": "Sunken dark spots on fruit and lesions on leaves."},
    {"disease": "Tomato Fusarium Wilt", "crop": "Tomato", "pattern": "wilt_yellow", "note": "One-sided yellowing/wilting; vascular browning."},
    {"disease": "Tomato Verticillium Wilt", "crop": "Tomato", "pattern": "wilt_yellow", "note": "V-shaped yellow leaf margins and drooping."},
    {"disease": "Potato Late Blight", "crop": "Potato", "pattern": "blight_necrotic", "note": "Dark blotches with pale green halo; rapid collapse."},
    {"disease": "Potato Early Blight", "crop": "Potato", "pattern": "target_spot", "note": "Target-like brown spots on lower leaves."},
    {"disease": "Potato Common Scab", "crop": "Potato", "pattern": "spot_scorch", "note": "Rough corky lesions mainly on tubers."},
    {"disease": "Potato Blackleg", "crop": "Potato", "pattern": "blight_necrotic", "note": "Black rot at stem base and wilting."},
    {"disease": "Potato Virus Y", "crop": "Potato", "pattern": "yellow_viral", "note": "Mosaic, vein banding, leaf distortion."},
    {"disease": "Wheat Stem Rust", "crop": "Wheat", "pattern": "rust", "note": "Orange-brown pustules mainly on stems."},
    {"disease": "Wheat Leaf Rust", "crop": "Wheat", "pattern": "rust", "note": "Small orange pustules scattered on leaves."},
    {"disease": "Wheat Stripe Rust", "crop": "Wheat", "pattern": "rust", "note": "Yellow-orange stripes along leaf veins."},
    {"disease": "Wheat Powdery Mildew", "crop": "Wheat", "pattern": "powdery_mildew", "note": "White fungal growth on leaves and sheaths."},
    {"disease": "Wheat Septoria Tritici Blotch", "crop": "Wheat", "pattern": "target_spot", "note": "Tan blotches with dark fruiting bodies."},
    {"disease": "Wheat Fusarium Head Blight", "crop": "Wheat", "pattern": "blight_necrotic", "note": "Bleached spikelets and pink/orange mould."},
    {"disease": "Wheat Tan Spot", "crop": "Wheat", "pattern": "target_spot", "note": "Lens-shaped tan spots with dark borders."},
    {"disease": "Rice Blast", "crop": "Rice", "pattern": "blight_necrotic", "note": "Spindle-shaped lesions with grey centres."},
    {"disease": "Rice Bacterial Blight", "crop": "Rice", "pattern": "blight_necrotic", "note": "Water-soaked leaf margins turning straw-coloured."},
    {"disease": "Rice Sheath Blight", "crop": "Rice", "pattern": "blight_necrotic", "note": "Oval grey-green lesions on sheaths near waterline."},
    {"disease": "Rice Brown Spot", "crop": "Rice", "pattern": "target_spot", "note": "Brown oval spots, common in nutrient-poor soils."},
    {"disease": "Rice Tungro", "crop": "Rice", "pattern": "yellow_viral", "note": "Yellow-orange leaves and stunting; spread by planthoppers."},
    {"disease": "Corn Northern Leaf Blight", "crop": "Corn", "pattern": "blight_necrotic", "note": "Long cigar-shaped grey-green lesions."},
    {"disease": "Corn Gray Leaf Spot", "crop": "Corn", "pattern": "spot_scorch", "note": "Rectangular grey spots between veins."},
    {"disease": "Corn Common Rust", "crop": "Corn", "pattern": "rust", "note": "Cinnamon-brown pustules on both leaf surfaces."},
    {"disease": "Cotton Angular Leaf Spot", "crop": "Cotton", "pattern": "target_spot", "note": "Angular brown spots limited by leaf veins."},
    {"disease": "Cotton Bacterial Blight", "crop": "Cotton", "pattern": "spot_scorch", "note": "Water-soaked angular lesions turning dark."},
    {"disease": "Soybean Rust", "crop": "Soybean", "pattern": "rust", "note": "Tan/brown pustules mostly on lower leaf surface."},
    {"disease": "Soybean Sudden Death Syndrome", "crop": "Soybean", "pattern": "wilt_yellow", "note": "Yellow patches between veins with green midrib."},
    {"disease": "Apple Scab", "crop": "Apple", "pattern": "spot_scorch", "note": "Olive-green to black velvety spots."},
    {"disease": "Apple Fire Blight", "crop": "Apple", "pattern": "blight_necrotic", "note": "Blackened shoots, cankers, bacterial ooze."},
    {"disease": "Grape Downy Mildew", "crop": "Grape", "pattern": "powdery_mildew", "note": "Oil-spot lesions and white downy growth underside."},
    {"disease": "Grape Powdery Mildew", "crop": "Grape", "pattern": "powdery_mildew", "note": "Grey-white powder on leaves and berries."},
    {"disease": "Banana Black Sigatoka", "crop": "Banana", "pattern": "blight_necrotic", "note": "Dark streaks and necrotic leaf tissue."},
    {"disease": "Banana Panama Wilt", "crop": "Banana", "pattern": "wilt_yellow", "note": "Yellowing, splitting leaf stalks, vascular discolouration."},
]

CROP_OPTIONS = ["Auto"] + sorted({item["crop"] for item in DISEASE_CATALOG})

PATTERN_ADVICE = {
    "en": {
        "healthy": "No urgent action. Keep scouting weekly and maintain balanced nutrition.",
        "powdery_mildew": "Improve airflow, avoid overhead irrigation late in the day, and apply a recommended fungicide if spread continues.",
        "rust": "Scout weekly. Remove severely infected debris and apply an approved rust fungicide when pustules are active.",
        "blight_necrotic": "Act quickly. Remove infected material, avoid wetting foliage, and consult local extension for an appropriate treatment.",
        "target_spot": "Prune lower infected leaves, rotate crops, and treat early spots before rain spreads spores.",
        "spot_scorch": "Sanitize tools, remove diseased tissue, and use certified seed/transplants to reduce carryover.",
        "yellow_viral": "Manage insect vectors, remove highly infected plants, and use resistant varieties where available.",
        "wilt_yellow": "Check soil drainage and vascular symptoms. Confirm with a lab if possible; remove severely wilted plants to reduce spread.",
        "ood": "Retake the photo with steady hand, good light, and the full leaf in frame. If uncertain, ask an agronomist.",
    },
    "es": {
        "healthy": "Sin acción urgente. Sigue revisando semanalmente y mantiene una nutrición balanceada.",
        "powdery_mildew": "Mejora la ventilación, evita riego por aspersión al final del día y aplica un fungicida recomendado si continúa avanzando.",
        "rust": "Revisa semanalmente. Retira restos muy infectados y aplica un fungicida aprobado contra roya si hay pústulas activas.",
        "blight_necrotic": "Actúa rápido. Retira material infectado, evita mojar el follaje y consulta con extensión local para un tratamiento adecuado.",
        "target_spot": "Poda hojas inferiores infectadas, rota cultivos y trata manchas tempranas antes de la lluvia.",
        "spot_scorch": "Desinfecta herramientas, retira tejido enfermo y usa semilla o plántulas certificadas.",
        "yellow_viral": "Controla insectos vectores, retira plantas muy infectadas y usa variedades resistentes si están disponibles.",
        "wilt_yellow": "Revisa drenaje del suelo y síntomas vasculares. Confirma en laboratorio si es posible; retira plantas muy marchitas.",
        "ood": "Toma otra foto con buena luz, mano firme y la hoja completa en el encuadre. Si hay duda, consulta a un agrónomo.",
    },
    "hi": {
        "healthy": "तुरंत कार्रवाई की जरूरत नहीं। साप्ताहिक निगरानी जारी रखें और संतुलित पोषण बनाए रखें।",
        "powdery_mildew": "हवा का प्रवाह बेहतर करें, देर शाम ऊपर से सिंचाई टालें और फैलने पर अनुशंसित फफूंदनाशक का उपयोग करें।",
        "rust": "साप्ताहिक जांच करें। अधिक संक्रमित अवशेष हटाएं और सक्रिय पुस्टुल होने पर स्वीकृत रस्ट फफूंदनाशक डालें।",
        "blight_necrotic": "जल्दी कार्रवाई करें। संक्रमित पौधा हटाएं, पत्तों को गीला न करें और स्थानीय कृषि विस्तार अधिकारी से उपचार लें।",
        "target_spot": "नीचे की संक्रमित पत्तियां काटें, फसल चक्र अपनाएं और बारिश से पहले धब्बों का उपचार करें।",
        "spot_scorch": "औजारों को साफ करें, रोगग्रस्त ऊतक हटाएं और प्रमाणित बीज/पौधे उपयोग करें।",
        "yellow_viral": "कीट वाहकों को नियंत्रित करें, गंभीर संक्रमित पौधे हटाएं और उपलब्ध हो तो प्रतिरोधी किस्में लगाएं।",
        "wilt_yellow": "मिट्टी की जल निकासी और तना वाहिकीय लक्षण जांचें। संभव हो तो लैब से पुष्टि करें; गंभीर मुरझाए पौधे हटाएं।",
        "ood": "अच्छी रोशनी, स्थिर फोन और पूरी पत्ती फ्रेम में लेकर फिर से फोटो लें। अनिश्चितता हो तो विशेषज्ञ से पूछें।",
    },
}

SEVERITY_TRANSLATIONS = {
    "en": {"Low": "Low", "Moderate": "Moderate", "High": "High", "Critical": "Critical", "Unknown": "Unknown"},
    "es": {"Low": "Baja", "Moderate": "Moderada", "High": "Alta", "Critical": "Crítica", "Unknown": "Desconocida"},
    "hi": {"Low": "कम", "Moderate": "मध्यम", "High": "अधिक", "Critical": "गंभीर", "Unknown": "अज्ञात"},
}

LANG_CODE = {"English": "en", "Español": "es", "हिन्दी": "hi"}

DEMO_CLIPS = [
    {"crop": "Tomato", "disease": "Late Blight", "pattern": "blight_necrotic", "severity": "High", "frames": 15, "conf": 0.93},
    {"crop": "Wheat", "disease": "Stripe Rust", "pattern": "rust", "severity": "Moderate", "frames": 14, "conf": 0.89},
    {"crop": "Tomato", "disease": "Powdery Mildew", "pattern": "powdery_mildew", "severity": "Moderate", "frames": 14, "conf": 0.91},
    {"crop": "Corn", "disease": "Northern Leaf Blight", "pattern": "blight_necrotic", "severity": "Critical", "frames": 14, "conf": 0.87},
    {"crop": "Rice", "disease": "Tungro", "pattern": "yellow_viral", "severity": "High", "frames": 13, "conf": 0.83},
    {"crop": "Apple", "disease": "Scab", "pattern": "spot_scorch", "severity": "Moderate", "frames": 13, "conf": 0.85},
    {"crop": "Potato", "disease": "Early Blight", "pattern": "target_spot", "severity": "Low", "frames": 12, "conf": 0.81},
    {"crop": "Unknown", "disease": "Not a leaf / unclear", "pattern": "ood", "severity": "Unknown", "frames": 13, "conf": 0.34},
]

CLIP_BOUNDS = []
_acc = 0
for _clip in DEMO_CLIPS:
    _start = _acc
    _acc += int(_clip["frames"])
    CLIP_BOUNDS.append((_start, _acc, _clip))
TOTAL_FRAMES = _acc

_FONT_CACHE = {}


def load_font(size=16):
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]

    candidates = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "arial.ttf",
    ]
    font = None
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            break
        except Exception:
            continue

    if font is None:
        font = ImageFont.load_default()

    _FONT_CACHE[size] = font
    return font


def softmax(values):
    arr = np.asarray(values, dtype=float)
    arr = arr - np.max(arr)
    exp = np.exp(arr)
    return exp / np.sum(exp)


def locate_clip(frame_idx):
    for start, end, clip in CLIP_BOUNDS:
        if start <= frame_idx < end:
            local = frame_idx - start
            total = end - start
            return clip, local, total, (local + 1) / float(total)

    start, end, clip = CLIP_BOUNDS[-1]
    return clip, end - start - 1, end - start, 1.0


def rotate_point(x, y, angle_rad, cx, cy):
    xr = x * math.cos(angle_rad) - y * math.sin(angle_rad)
    yr = x * math.sin(angle_rad) + y * math.cos(angle_rad)
    return int(cx + xr), int(cy + yr)


def ellipse_points(cx, cy, rx, ry, angle_deg, steps=72):
    angle = math.radians(angle_deg)
    pts = []
    for i in range(steps):
        t = 2.0 * math.pi * i / float(steps)
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        pts.append(rotate_point(x, y, angle, cx, cy))
    return pts


def random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.82):
    angle = math.radians(angle_deg)
    theta = rng.uniform(0.0, 2.0 * math.pi)
    rad = math.sqrt(rng.uniform(0.0, margin * margin))
    x = rx * rad * math.cos(theta)
    y = ry * rad * math.sin(theta)
    return rotate_point(x, y, angle, cx, cy)


def irregular_polygon(x, y, radius, rng, sides=9):
    pts = []
    for i in range(sides):
        a = 2.0 * math.pi * i / float(sides) + rng.normal(0.0, 0.18)
        r = radius * rng.uniform(0.55, 1.35)
        pts.append((int(x + r * math.cos(a)), int(y + r * math.sin(a))))
    return pts


def add_symptoms(od, cx, cy, rx, ry, angle_deg, pattern, progress, rng):
    if pattern == "healthy" or pattern == "ood":
        return

    if pattern == "rust":
        count = int(35 + progress * 110)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.88)
            r = int(rng.integers(2, 5))
            od.ellipse([x - r, y - r, x + r, y + r], fill=(205, 112, 38, 235), outline=(130, 60, 20, 180))

    elif pattern == "powdery_mildew":
        count = int(8 + progress * 22)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.86)
            w = int(rng.integers(18, 46))
            h = int(rng.integers(12, 30))
            a = int(rng.integers(-40, 40))
            pts = ellipse_points(x, y, w, h, a, 24)
            od.polygon(pts, fill=(246, 246, 246, 145))

    elif pattern == "blight_necrotic":
        count = int(4 + progress * 12)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.75)
            radius = int(rng.integers(16, 42)) * (0.7 + 0.6 * progress)
            halo = irregular_polygon(x, y, int(radius * 1.35), rng)
            od.polygon(halo, fill=(174, 160, 45, 95))
            lesion = irregular_polygon(x, y, int(radius), rng)
            od.polygon(lesion, fill=(62, 38, 24, 215), outline=(28, 18, 12, 230))

    elif pattern == "target_spot":
        count = int(6 + progress * 20)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.84)
            r = int(rng.integers(7, 18))
            od.ellipse([x - r, y - r, x + r, y + r], fill=(120, 78, 42, 190), outline=(70, 42, 22, 220))
            r2 = max(2, int(r * 0.62))
            od.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(185, 150, 95, 190))
            r3 = max(1, int(r * 0.32))
            od.ellipse([x - r3, y - r3, x + r3, y + r3], fill=(90, 55, 30, 210))

    elif pattern == "spot_scorch":
        count = int(8 + progress * 28)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.86)
            r = int(rng.integers(3, 11))
            pts = irregular_polygon(x, y, r, rng, sides=7)
            od.polygon(pts, fill=(35, 25, 20, 220), outline=(15, 10, 8, 235))

    elif pattern == "yellow_viral":
        count = int(12 + progress * 35)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.88)
            w = int(rng.integers(10, 34))
            h = int(rng.integers(8, 24))
            a = int(rng.integers(-60, 60))
            pts = ellipse_points(x, y, w, h, a, 20)
            color = (225, 215, 65, 135) if rng.random() > 0.45 else (165, 205, 70, 115)
            od.polygon(pts, fill=color)

    elif pattern == "wilt_yellow":
        count = int(8 + progress * 22)
        for _ in range(count):
            x, y = random_leaf_point(cx, cy, rx, ry, angle_deg, rng, margin=0.86)
            w = int(rng.integers(18, 55))
            h = int(rng.integers(10, 28))
            a = angle_deg + int(rng.integers(-15, 15))
            pts = ellipse_points(x, y, w, h, a, 20)
            od.polygon(pts, fill=(218, 196, 72, 130))

        for _ in range(int(2 + progress * 5)):
            x_local = rx * rng.uniform(0.55, 0.95)
            y_local = rng.uniform(-ry * 0.2, ry * 0.2)
            x, y = rotate_point(x_local, y_local, math.radians(angle_deg), cx, cy)
            od.polygon(irregular_polygon(x, y, int(rng.integers(8, 20)), rng), fill=(88, 58, 34, 185))


def short_advice(pattern, severity):
    if pattern == "ood":
        return "Unclear image: steady phone, avoid glare, capture full leaf, or ask expert."

    mapping = {
        "healthy": "Healthy leaf detected. Keep routine scouting.",
        "powdery_mildew": "Powdery growth: improve airflow and consider fungicide if spreading.",
        "rust": "Rust pustules: scout weekly and treat active infections.",
        "blight_necrotic": "Necrotic blight: remove debris, avoid wet foliage, urgent scout.",
        "target_spot": "Target spots: prune lower leaves and monitor after rain.",
        "spot_scorch": "Dark spots: sanitize tools and remove affected tissue.",
        "yellow_viral": "Yellow mosaic: manage vectors and remove severe plants.",
        "wilt_yellow": "Yellow wilt: check drainage and confirm diagnosis before treating.",
    }
    return mapping.get(pattern, "Monitor and retake in 48 hours.")


def draw_hud(img, clip, frame_idx, progress):
    draw = ImageDraw.Draw(img, "RGBA")
    font = load_font(15)
    font_small = load_font(12)

    draw.rectangle([0, 0, WIDTH, 40], fill=(0, 0, 0, 150))
    draw.text((10, 10), "● REC", fill=(255, 90, 90, 255), font=font)

    ts = datetime.now() + timedelta(seconds=frame_idx / float(FPS))
    draw.text((75, 12), ts.strftime("%Y-%m-%d %H:%M:%S"), fill=(240, 240, 240, 255), font=font_small)
    draw.text((WIDTH - 145, 12), f"SIM {frame_idx + 1}/{TOTAL_FRAMES}", fill=(190, 255, 200, 255), font=font_small)

    panel_x = WIDTH - 255
    draw.rectangle([panel_x, 48, WIDTH - 12, 154], fill=(0, 0, 0, 135), outline=(90, 220, 130, 190), width=2)

    draw.text((panel_x + 12, 56), "Crop", fill=(170, 230, 180, 255), font=font_small)
    draw.text((panel_x + 12, 72), clip["crop"][:22], fill=(255, 255, 255, 255), font=font)

    label = "OOD / UNCLEAR" if clip["pattern"] == "ood" else clip["disease"]
    if len(label) > 26:
        label = label[:25] + "…"

    draw.text((panel_x + 12, 94), "Prediction", fill=(170, 230, 180, 255), font=font_small)
    draw.text((panel_x + 12, 110), label, fill=(255, 255, 255, 255), font=font)

    conf_color = (255, 220, 100, 255) if clip["conf"] >= 0.65 else (255, 140, 120, 255)
    draw.text((panel_x + 12, 130), f"Conf {clip['conf']:.2f} • Sev {clip['severity']}", fill=conf_color, font=font_small)

    advice = short_advice(clip["pattern"], clip["severity"])
    if len(advice) > 92:
        advice = advice[:91] + "…"

    draw.rectangle([0, HEIGHT - 38, WIDTH, HEIGHT], fill=(0, 0, 0, 150))
    draw.text((10, HEIGHT - 29), advice, fill=(225, 255, 225, 255), font=font_small)


def render_demo_frame(frame_idx):
    clip, local_idx, local_total, progress = locate_clip(frame_idx)
    rng = np.random.default_rng(9173 + int(frame_idx))

    ys = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, 1.0, WIDTH, dtype=np.float32)[None, :]

    bg = np.empty((HEIGHT, WIDTH, 3), dtype=np.float32)
    bg[..., 0] = 22 + 38 * ys + 10 * xs
    bg[..., 1] = 48 + 55 * (1 - ys) + 8 * xs
    bg[..., 2] = 18 + 28 * ys + 6 * xs

    noise = rng.normal(0.0, 3.0, (HEIGHT, WIDTH, 1)).astype(np.float32)
    bg = np.clip(bg + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(bg, "RGB").convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    shake_x = int(10 * math.sin(frame_idx / 4.2) + rng.normal(0, 2))
    shake_y = int(6 * math.cos(frame_idx / 5.7) + rng.normal(0, 2))

    cx = WIDTH // 2 + shake_x
    cy = HEIGHT // 2 + shake_y + 8
    rx, ry = 230, 124
    angle = -18 + 6 * math.sin(frame_idx / 8.0)
    angle_rad = math.radians(angle)

    stem_start = rotate_point(int(-rx * 1.25), int(ry * 0.55), angle_rad, cx, cy)
    stem_end = rotate_point(int(rx * 1.25), int(-ry * 0.55), angle_rad, cx, cy)
    od.line([stem_start, stem_end], fill=(48, 92, 42, 255), width=9)

    leaf_pts = ellipse_points(cx, cy, rx, ry, angle, 96)
    leaf_fill = (40, 92, 46, 215) if clip["pattern"] == "ood" else (52, 132, 58, 255)
    od.polygon(leaf_pts, fill=leaf_fill, outline=(22, 68, 28, 255))

    mid_start = rotate_point(int(-rx * 0.92), 0, angle_rad, cx, cy)
    mid_end = rotate_point(int(rx * 0.92), 0, angle_rad, cx, cy)
    od.line([mid_start, mid_end], fill=(30, 88, 36, 210), width=4)

    for frac in np.linspace(-0.78, 0.78, 11):
        x_local = float(frac) * rx
        y_amp = ry * 0.58 * math.sqrt(max(0.0, 1.0 - float(frac) * float(frac)))
        center = rotate_point(int(x_local), 0, angle_rad, cx, cy)
        top = rotate_point(int(x_local), int(-y_amp), angle_rad, cx, cy)
        bottom = rotate_point(int(x_local), int(y_amp), angle_rad, cx, cy)
        od.line([center, top], fill=(34, 96, 40, 155), width=2)
        od.line([center, bottom], fill=(34, 96, 40, 155), width=2)

    add_symptoms(od, cx, cy, rx, ry, angle, clip["pattern"], progress, rng)

    if clip["pattern"] == "powdery_mildew":
        overlay = overlay.filter(ImageFilter.GaussianBlur(1.1))

    img = Image.alpha_composite(img, overlay)

    if clip["pattern"] == "ood" or frame_idx % 27 == 11:
        blur_radius = 3.4 if clip["pattern"] == "ood" else 1.2
        img = img.filter(ImageFilter.GaussianBlur(blur_radius))

        glare = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glare)
        gx = int(WIDTH * (0.18 + 0.64 * abs(math.sin(frame_idx / 9.0))))
        alpha = 155 if clip["pattern"] == "ood" else 80
        gd.ellipse([gx - 190, -90, gx + 190, 230], fill=(255, 255, 255, alpha))
        img = Image.alpha_composite(img, glare)

    draw_hud(img, clip, frame_idx, progress)
    return np.array(img.convert("RGB"))


@st.cache_resource(show_spinner="Generating live demo video...")
def build_demo_video():
    fd, mp4_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    errors = []

    try:
        writer = imageio.get_writer(
            mp4_path,
            format="mp4",
            mode="I",
            fps=FPS,
            codec="libx264",
            pixelformat="yuv420p",
            output_params=["-movflags", "+faststart"],
        )
        for i in range(TOTAL_FRAMES):
            writer.append_data(render_demo_frame(i))
        writer.close()

        if not os.path.exists(mp4_path) or os.path.getsize(mp4_path) == 0:
            raise RuntimeError("Empty MP4 file produced by imageio.")

        with open(mp4_path, "rb") as f:
            data = f.read()
        os.unlink(mp4_path)
        return data, "video/mp4", ""
    except Exception as exc:
        errors.append(str(exc))

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(mp4_path, fourcc, FPS, (WIDTH, HEIGHT))
        if not writer.isOpened():
            raise RuntimeError("OpenCV mp4v writer could not open.")

        for i in range(TOTAL_FRAMES):
            writer.write(cv2.cvtColor(render_demo_frame(i), cv2.COLOR_RGB2BGR))
        writer.release()

        if not os.path.exists(mp4_path) or os.path.getsize(mp4_path) == 0:
            raise RuntimeError("Empty MP4 file produced by OpenCV.")

        with open(mp4_path, "rb") as f:
            data = f.read()
        os.unlink(mp4_path)
        return data, "video/mp4", " | ".join(errors)
    except Exception as exc:
        errors.append(str(exc))

    fd2, avi_path = tempfile.mkstemp(suffix=".avi")
    os.close(fd2)

    try:
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(avi_path, fourcc, FPS, (WIDTH, HEIGHT))
        if not writer.isOpened():
            raise RuntimeError("OpenCV MJPG writer could not open.")

        for i in range(TOTAL_FRAMES):
            writer.write(cv2.cvtColor(render_demo_frame(i), cv2.COLOR_RGB2BGR))
        writer.release()

        if not os.path.exists(avi_path) or os.path.getsize(avi_path) == 0:
            raise RuntimeError("Empty AVI file produced by OpenCV.")

        with open(avi_path, "rb") as f:
            data = f.read()

        os.unlink(avi_path)
        if os.path.exists(mp4_path):
            os.unlink(mp4_path)

        return data, "video/x-msvideo", " | ".join(errors)
    except Exception as exc:
        errors.append(str(exc))
        if os.path.exists(mp4_path):
            os.unlink(mp4_path)
        if os.path.exists(avi_path):
            os.unlink(avi_path)
        return None, "video/mp4", " | ".join(errors)


@st.cache_resource(show_spinner=False)
def demo_preview_images():
    indices = (0, 18, 42, 66, 90)
    return [Image.fromarray(render_demo_frame(i)).convert("RGB") for i in indices if i < TOTAL_FRAMES]


@st.cache_data(show_spinner=False)
def build_demo_dataset():
    rows = []
    now = datetime.now()
    farms = ["North Ridge", "River Plot", "Sunrise Cooperative", "Hill Side", "Canal Block"]

    for i in range(36):
        clip = DEMO_CLIPS[i % len(DEMO_CLIPS)]
        rng = np.random.default_rng(7000 + i)
        conf = float(np.clip(clip["conf"] + rng.normal(0, 0.035), 0.22, 0.99))
        severity = clip["severity"]

        if clip["pattern"] == "ood":
            status = "Ask expert"
        elif conf < 0.62:
            status = "Low confidence"
        elif severity in ("High", "Critical"):
            status = "Treat now"
        elif severity == "Moderate":
            status = "Monitor"
        else:
            status = "Healthy"

        if status == "Treat now":
            action = "Apply advised treatment and re-scout in 48h"
        elif status == "Monitor":
            action = "Recheck after 3 days"
        elif status == "Ask expert":
            action = "Send photo to agronomist"
        elif status == "Low confidence":
            action = "Retake photo in better light"
        else:
            action = "No action"

        rows.append(
            {
                "time": (now - timedelta(minutes=36 - i * 2)).strftime("%H:%M"),
                "farm": farms[i % len(farms)],
                "crop": clip["crop"],
                "prediction": clip["disease"],
                "severity": severity,
                "confidence": round(conf, 3),
                "status": status,
                "action": action,
            }
        )

    return rows


def simulate_batch(n=20, threshold=0.62):
    rng = np.random.default_rng(int(datetime.now().timestamp() * 1000) % 1000000)
    rows = []
    now = datetime.now()
    farms = ["North Ridge", "River Plot", "Sunrise Cooperative", "Hill Side", "Canal Block"]

    for i in range(n):
        clip = DEMO_CLIPS[int(rng.integers(0, len(DEMO_CLIPS)))]
        conf = float(np.clip(clip["conf"] + rng.normal(0, 0.06), 0.18, 0.99))
        severity = clip["severity"]

        if clip["pattern"] == "ood":
            status = "Ask expert"
        elif conf < threshold:
            status = "Low confidence"
        elif severity in ("High", "Critical"):
            status = "Treat now"
        elif severity == "Moderate":
            status = "Monitor"
        else:
            status = "Healthy"

        if status == "Treat now":
            action = "Apply advised treatment and re-scout in 48h"
        elif status == "Monitor":
            action = "Recheck after 3 days"
        elif status == "Ask expert":
            action = "Send photo to agronomist"
        elif status == "Low confidence":
            action = "Retake photo in better light"
        else:
            action = "No action"

        rows.append(
            {
                "time": (now - timedelta(minutes=n - i)).strftime("%H:%M"),
                "farm": farms[int(rng.integers(0, len(farms)))],
                "crop": clip["crop"],
                "prediction": clip["disease"],
                "severity": severity,
                "confidence": round(conf, 3),
                "status": status,
                "action": action,
            }
        )

    return rows


def to_rgb(pil_image):
    if pil_image.mode == "RGB":
        return pil_image

    if pil_image.mode in ("RGBA", "LA", "P"):
        rgba = pil_image.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg

    return pil_image.convert("RGB")


def extract_features(rgb_array):
    img = rgb_array.astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    total = float(h.size)

    green_mask = (h >= 35) & (h <= 85) & (s >= 40) & (v >= 40)
    yellow_mask = (h >= 20) & (h < 35) & (s >= 45) & (v >= 70)
    orange_mask = (h >= 8) & (h < 20) & (s >= 80) & (v >= 80)
    brown_mask = (((h >= 0) & (h < 22)) | (h >= 170)) & (s >= 35) & (v >= 25) & (v <= 175)
    black_mask = (v < 50) & (s < 120)
    white_mask = (s < 45) & (v >= 185)
    highlight_mask = (v >= 245) & (s < 80)
    leaf_union = green_mask | yellow_mask | orange_mask | brown_mask

    lesion_mask = (brown_mask | black_mask | orange_mask).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    lesion_clean = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(lesion_clean, connectivity=8)
    spot_count = 0
    large_spot_ratio = 0.0

    if num_labels > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        valid = areas[(areas >= 8) & (areas <= total * 0.22)]
        spot_count = int(len(valid))
        if len(valid) > 0:
            large_spot_ratio = float(np.max(valid) / total)

    return {
        "green_ratio": float(np.sum(green_mask) / total),
        "yellow_ratio": float(np.sum(yellow_mask) / total),
        "orange_ratio": float(np.sum(orange_mask) / total),
        "brown_ratio": float(np.sum(brown_mask) / total),
        "black_ratio": float(np.sum(black_mask) / total),
        "white_ratio": float(np.sum(white_mask) / total),
        "highlight_ratio": float(np.sum(highlight_mask) / total),
        "leaf_ratio": float(np.sum(leaf_union) / total),
        "brightness": float(np.mean(v)),
        "texture_std": float(np.std(gray)),
        "sharpness": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "spot_count": spot_count,
        "large_spot_ratio": large_spot_ratio,
    }


def pattern_scores(f):
    sharp_norm = min(f["sharpness"] / 250.0, 1.0)
    spot_norm = min(f["spot_count"] / 80.0, 1.0)
    affected = f["brown_ratio"] + f["black_ratio"] + f["orange_ratio"]
    texture = min(f["texture_std"] / 70.0, 1.0)
    large = min(f["large_spot_ratio"] / 0.08, 1.0)

    return {
        "healthy": f["green_ratio"] * 1.8 + sharp_norm * 0.25 - affected * 1.6 - f["white_ratio"] * 0.9 - f["yellow_ratio"] * 0.5,
        "powdery_mildew": f["white_ratio"] * 2.8 + f["green_ratio"] * 0.25 - affected * 0.25 + texture * 0.15,
        "rust": f["orange_ratio"] * 2.3 + f["brown_ratio"] * 1.1 + spot_norm * 1.2 + texture * 0.2 - f["white_ratio"] * 0.2,
        "blight_necrotic": f["brown_ratio"] * 1.7 + f["black_ratio"] * 1.5 + large * 1.3 + affected * 0.4 - f["green_ratio"] * 0.35,
        "target_spot": f["brown_ratio"] * 1.2 + f["black_ratio"] * 0.8 + spot_norm * 1.4 + large * 0.5 - f["white_ratio"] * 0.2,
        "spot_scorch": f["black_ratio"] * 1.5 + f["brown_ratio"] * 1.0 + spot_norm * 0.9 + large * 0.4,
        "yellow_viral": f["yellow_ratio"] * 1.8 + texture * 0.8 + spot_norm * 0.2 - f["brown_ratio"] * 0.25,
        "wilt_yellow": f["yellow_ratio"] * 1.3 + f["brown_ratio"] * 0.8 + (1.0 - f["green_ratio"]) * 0.5 - f["white_ratio"] * 0.2,
    }


def ood_decision(f):
    reasons = []

    if f["sharpness"] < 32:
        reasons.append("blurry")
    if f["brightness"] < 42:
        reasons.append("too dark")
    if f["highlight_ratio"] > 0.20:
        reasons.append("glare")
    if f["leaf_ratio"] < 0.16:
        reasons.append("not enough leaf")

    if f["leaf_ratio"] < 0.12 or f["sharpness"] < 20 or f["highlight_ratio"] > 0.28:
        return True, ", ".join(reasons) if reasons else "poor image quality"

    if len(reasons) >= 2:
        return True, ", ".join(reasons)

    return False, ""


def estimate_severity(f, pattern):
    if pattern == "powdery_mildew":
        affected = f["white_ratio"]
    elif pattern == "rust":
        affected = f["orange_ratio"] + f["brown_ratio"] + 0.01 * f["spot_count"]
    elif pattern in ("blight_necrotic", "spot_scorch"):
        affected = f["brown_ratio"] + f["black_ratio"] + f["large_spot_ratio"]
    elif pattern in ("yellow_viral", "wilt_yellow"):
        affected = f["yellow_ratio"] + 0.5 * f["brown_ratio"]
    elif pattern == "target_spot":
        affected = f["brown_ratio"] + f["black_ratio"] + 0.01 * f["spot_count"]
    else:
        affected = f["brown_ratio"] + f["black_ratio"] + f["yellow_ratio"] + f["white_ratio"]

    if affected < 0.04:
        return "Low"
    if affected < 0.12:
        return "Moderate"
    if affected < 0.25:
        return "High"
    return "Critical"


def make_saliency(arr, features, pattern):
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)

    green = (h >= 35) & (h <= 85) & (s >= 40) & (v >= 40)
    yellow = (h >= 20) & (h < 35) & (s >= 45) & (v >= 70)
    orange = (h >= 8) & (h < 20) & (s >= 80) & (v >= 80)
    brown = (((h >= 0) & (h < 22)) | (h >= 170)) & (s >= 35) & (v >= 25) & (v <= 175)
    black = (v < 50) & (s < 120)
    white = (s < 45) & (v >= 185)

    if pattern == "powdery_mildew":
        mask = white
    elif pattern == "rust":
        mask = orange | (brown & (v >= 60))
    elif pattern in ("blight_necrotic", "spot_scorch"):
        mask = brown | black
    elif pattern in ("yellow_viral", "wilt_yellow", "target_spot"):
        mask = yellow | (brown & (s >= 50))
    elif pattern == "ood":
        mask = ~(green | yellow | orange | brown)
    else:
        mask = green

    mask_uint8 = mask.astype(np.uint8) * 255
    mask_uint8 = cv2.GaussianBlur(mask_uint8, (0, 0), 2.5)

    heat = cv2.applyColorMap(mask_uint8, cv2.COLORMAP_JET)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(arr, 0.62, heat, 0.38, 0)

    return Image.fromarray(blended)


def classify_pil(pil_image, crop_choice="Auto", threshold=0.62):
    img = to_rgb(pil_image).resize((512, 512), RESAMPLE)
    arr = np.array(img)
    f = extract_features(arr)

    is_ood, reason = ood_decision(f)
    scores = pattern_scores(f)

    keys = list(scores.keys())
    vals = np.array([scores[k] for k in keys], dtype=float)
    probs = softmax(vals / 0.07)

    pattern_idx = int(np.argmax(probs))
    pattern_key = keys[pattern_idx]
    pattern_conf = float(probs[pattern_idx])

    candidates = []
    for entry in DISEASE_CATALOG:
        if crop_choice != "Auto" and entry["crop"] != crop_choice:
            continue
        candidates.append(entry)

    if not candidates:
        candidates = DISEASE_CATALOG[:]

    mean = float(np.mean(vals))
    std = float(np.std(vals)) + 1e-6

    scored = []
    for entry in candidates:
        base = float(scores[entry["pattern"]])
        crop_fit = 1.0 if crop_choice == "Auto" or entry["crop"] == crop_choice else 0.75
        z = (base - mean) / std
        conf = float(np.clip(0.18 + 0.74 * pattern_conf * crop_fit + 0.07 * z, 0.10, 0.98))
        scored.append(
            {
                "disease": entry["disease"],
                "crop": entry["crop"],
                "confidence": conf,
                "pattern": entry["pattern"],
                "note": entry["note"],
            }
        )

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    top = scored[:3]

    if is_ood:
        ood_conf = float(np.clip(0.16 + 0.28 * (1.0 - f["leaf_ratio"]), 0.08, 0.48))
        best = {
            "disease": "Not a leaf / unclear",
            "crop": crop_choice,
            "confidence": ood_conf,
            "pattern": "ood",
            "note": reason or "Image quality too low for reliable classification.",
        }
        top = [best] + top[:2]
        severity = "Unknown"
        status = "Ask expert"
    else:
        best = top[0]
        severity = estimate_severity(f, best["pattern"])

        if best["confidence"] < threshold:
            status = "Low confidence"
        elif severity in ("High", "Critical"):
            status = "Treat now"
        elif severity == "Moderate":
            status = "Monitor"
        else:
            status = "Healthy"

    saliency = make_saliency(arr, f, best["pattern"])

    return {
        "ood": is_ood,
        "ood_reason": reason,
        "best": best,
        "top": top,
        "severity": severity,
        "status": status,
        "features": f,
        "saliency": saliency,
        "original": img,
    }


def get_treatment(pattern, severity, lang_code):
    advice = PATTERN_ADVICE.get(lang_code, PATTERN_ADVICE["en"]).get(pattern, PATTERN_ADVICE["en"]["ood"])
    sev = SEVERITY_TRANSLATIONS.get(lang_code, SEVERITY_TRANSLATIONS["en"]).get(severity, severity)
    return f"**Severity:** {sev} — {advice}"


st.sidebar.title("⚙️ CropScan Controls")
st.sidebar.markdown("This demo runs locally and does not require an API key.")

crop_choice = st.sidebar.selectbox("Crop filter", CROP_OPTIONS, index=0)
threshold = st.sidebar.slider("Expert fallback confidence threshold", 0.30, 0.90, 0.62, 0.01)
lang_name = st.sidebar.selectbox("Advice language", list(LANG_CODE.keys()), index=0)
lang_code = LANG_CODE[lang_name]

st.sidebar.metric("Disease classes in catalog", len(DISEASE_CATALOG))
st.sidebar.metric("Demo video frames", TOTAL_FRAMES)
st.sidebar.caption("The classifier in this demo is a transparent rule-based proxy over colour, texture, spot, and blur features. Replace it with a trained on-device model for production use.")

st.title("🌿 CropScan — Phone Photo Plant Disease Demo")
st.caption("Working Streamlit demo with auto-generated live video, synthetic field telemetry, photo scanning, batch simulation, and multilingual treatment guidance. No API key required.")

tab_demo, tab_scan, tab_batch, tab_guide = st.tabs(["Live demo", "Scan photo", "Batch simulation", "Disease guide"])

with tab_demo:
    st.subheader("Auto-generated live simulation")

    video_bytes, video_format, video_error = build_demo_video()

    if video_bytes:
        try:
            st.video(video_bytes, format=video_format, loop=True, autoplay=True, muted=True)
        except TypeError:
            st.video(video_bytes, format=video_format, loop=True, autoplay=True)
        except Exception:
            st.video(io.BytesIO(video_bytes), format=video_format, loop=True, autoplay=True)

        ext = "mp4" if video_format == "video/mp4" else "avi"
        st.download_button(
            label="Download generated demo video",
            data=video_bytes,
            file_name=f"cropscan_live_demo.{ext}",
            mime=video_format,
        )

        if video_error:
            st.caption(f"Encoding compatibility note: {video_error}")
    else:
        st.error("Could not encode a video file on this machine. Showing generated demo frames instead.")
        st.image(demo_preview_images(), use_container_width=True)

    rows = build_demo_dataset()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Demo scans", len(rows))
    c2.metric("Alerts", sum(1 for r in rows if r["status"] in ("Treat now", "Ask expert", "Low confidence")))
    c3.metric("Average confidence", f"{float(np.mean([r['confidence'] for r in rows])):.2f}")
    c4.metric("Crop/disease classes", len(DISEASE_CATALOG))

    st.subheader("Live telemetry")
    st.dataframe(rows[:12], hide_index=True, use_container_width=True)

    st.subheader("Recent simulation log")
    for r in rows[:8]:
        st.markdown(f"- **{r['time']}** • {r['farm']} • {r['crop']} • {r['prediction']} • **{r['status']}**")

with tab_scan:
    st.subheader("Scan a leaf photo")

    source = st.radio("Input source", ["Upload photo", "Use camera"], horizontal=True)
    image = None

    if source == "Upload photo":
        uploaded = st.file_uploader("Upload a leaf photo", type=["jpg", "jpeg", "png", "webp"])
        if uploaded is not None:
            image = Image.open(uploaded)
    else:
        captured = st.camera_input("Capture a leaf photo")
        if captured is not None:
            image = Image.open(captured)

    if image is not None:
        with st.spinner("Analyzing leaf photo..."):
            result = classify_pil(image, crop_choice=crop_choice, threshold=threshold)

        left, right = st.columns(2)
        left.image(result["original"], caption="Processed input", use_container_width=True)
        right.image(result["saliency"], caption="Symptom saliency overlay", use_container_width=True)

        icon = "⚠️" if result["ood"] or result["status"] in ("Low confidence", "Ask expert") else "✅"
        st.markdown(f"### {icon} {result['best']['disease']}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Confidence", f"{result['best']['confidence']:.2f}")
        m2.metric("Severity", result["severity"])
        m3.metric("Status", result["status"])

        st.markdown(f"**Note:** {result['best']['note']}")
        st.markdown(get_treatment(result["best"]["pattern"], result["severity"], lang_code))

        if result["ood"]:
            st.warning("Out-of-distribution or poor-quality image detected. Recommended fallback: ask an expert or retake the photo.")

        st.subheader("Top candidates")
        st.dataframe(result["top"], hide_index=True, use_container_width=True)

        with st.expander("Visual features used by the demo classifier"):
            feature_items = [
                ("Green leaf ratio", "green_ratio"),
                ("Yellow ratio", "yellow_ratio"),
                ("Brown ratio", "brown_ratio"),
                ("Black ratio", "black_ratio"),
                ("White/powder ratio", "white_ratio"),
                ("Orange/rust ratio", "orange_ratio"),
                ("Leaf coverage", "leaf_ratio"),
                ("Glare/highlight ratio", "highlight_ratio"),
            ]

            for label, key in feature_items:
                val = float(result["features"][key])
                st.progress(min(1.0, max(0.0, val)), text=f"{label}: {val:.0%}")

            st.caption(
                f"Sharpness score: {result['features']['sharpness']:.1f} • "
                f"Brightness: {result['features']['brightness']:.1f} • "
                f"Spot count: {result['features']['spot_count']} • "
                f"Largest spot area ratio: {result['features']['large_spot_ratio']:.3f}"
            )
    else:
        st.info("Upload or capture a photo to test the classifier. Meanwhile, these are auto-generated demo frames.")
        st.image(demo_preview_images(), use_container_width=True)

with tab_batch:
    st.subheader("Virtual field-scan simulation")

    if "batch_results" not in st.session_state:
        st.session_state.batch_results = simulate_batch(20, threshold)

    if st.button("Run 20 new virtual scans"):
        st.session_state.batch_results = simulate_batch(20, threshold)

    batch_rows = st.session_state.batch_results

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Simulated scans", len(batch_rows))
    b2.metric("Treat-now alerts", sum(1 for r in batch_rows if r["status"] == "Treat now"))
    b3.metric("Expert fallbacks", sum(1 for r in batch_rows if r["status"] in ("Ask expert", "Low confidence")))
    b4.metric("Average confidence", f"{float(np.mean([r['confidence'] for r in batch_rows])):.2f}")

    st.dataframe(batch_rows, hide_index=True, use_container_width=True)

with tab_guide:
    st.subheader("Disease and treatment guide")

    query = st.text_input("Search by disease or crop", placeholder="Example: rust, tomato, wilt")
    filtered = [
        item
        for item in DISEASE_CATALOG
        if query.lower() in item["disease"].lower() or query.lower() in item["crop"].lower()
    ]

    st.caption(f"Showing {len(filtered)} of {len(DISEASE_CATALOG)} catalog entries.")
    st.dataframe(filtered, hide_index=True, use_container_width=True)

    for item in filtered[:12]:
        with st.expander(f"{item['disease']} — {item['crop']}"):
            st.write(item["note"])
            st.markdown(get_treatment(item["pattern"], "Moderate", lang_code))