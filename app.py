"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         PharmaAcademy AI  ·  Farmasötik Teknoloji Çalışma Platformu        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Kurulum:                                                                    ║
║    pip install streamlit plotly numpy pypdf python-dotenv                   ║
║                                                                              ║
║  Çalıştır:                                                                   ║
║    streamlit run app.py                                                      ║
║                                                                              ║
║  Modüller:                                                                   ║
║    A · Stratejik Analiz  — PDF not analizi + hoca stratejisi haritası       ║
║    B · Kavrayış Atölyesi — İnteraktif DLVO simülatörü + referans derinliği  ║
║    C · Akıllı Quiz       — Analitik sorular + seviyeye göre geri bildirim   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ── Standart kütüphaneler ─────────────────────────────────────────────────────
import re
import math
import random
import collections
from io import BytesIO

# ── Üçüncü taraf kütüphaneler ────────────────────────────────────────────────
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ── Opsiyonel PDF kütüphanesi (hata yönetimi ile) ────────────────────────────
try:
    from pypdf import PdfReader
    PYPDF_OK = True
except ImportError:
    try:
        import PyPDF2 as _pypdf2_compat           # eski isim desteği
        PdfReader = _pypdf2_compat.PdfFileReader
        PYPDF_OK = True
    except ImportError:
        PYPDF_OK = False


# ══════════════════════════════════════════════════════════════════════════════
# 1.  RENK PALETİ  ·  Oxford Mavisi + Amber Altın + Fildişi
# ══════════════════════════════════════════════════════════════════════════════

OX        = "#002147"   # Oxford Mavi — birincil marka rengi
OX_MID    = "#1A3A5C"   # Orta Oxford — hover, ikincil yüzeyler
OX_LIGHT  = "#E4EEF7"   # Açık Oxford — hafif arka planlar
AMBER     = "#FFBF00"   # Amber Altın — vurgu, uyarı, referans bloğu
AMBER_LT  = "#FFF8CC"   # Açık Amber — bilgi kutusu arka planı
IVORY     = "#F8F9FA"   # Fildişi — sayfa arka planı
IVORY2    = "#EEF0F2"   # Koyu fildişi — kart arka planı
WHITE     = "#FFFFFF"
BORDER    = "#D1D9E0"   # Kenarlık
TEXT      = "#0D1117"   # Birincil metin
TEXT2     = "#374151"   # İkincil metin
TEXT3     = "#6B7280"   # Gri metin / açıklama
SUCCESS   = "#166534"   # Yeşil — doğru cevap
SUCCESS_BG= "#DCFCE7"
ERROR     = "#991B1B"   # Kırmızı — yanlış cevap
ERROR_BG  = "#FEE2E2"
WARN      = "#92400E"   # Turuncu — uyarı
WARN_BG   = "#FEF3C7"

# Grafik renkleri
G_EDL   = "#C0392B"     # EDL itme eğrisi
G_VDW   = "#1565C0"     # VdW çekim eğrisi
G_TOTAL = "#1B5E20"     # Toplam enerji eğrisi


# ══════════════════════════════════════════════════════════════════════════════
# 2.  GLOBAL CSS  ·  Oxford Akademik Kimliği
# ══════════════════════════════════════════════════════════════════════════════

CSS = f"""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global sıfırlama ── */
html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, sans-serif !important;
    color: {TEXT};
    -webkit-font-smoothing: antialiased;
}}
.stApp {{ background: {IVORY} !important; }}

/* ══ Sidebar ══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
    background: {OX} !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(0,21,47,0.22) !important;
}}
[data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.65) !important; }}

/* Sidebar nav butonları */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important;
    color: rgba(255,191,0,0.80) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    padding: 12px 16px !important;
    text-align: left !important;
    width: 100% !important;
    margin-bottom: 3px !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,191,0,0.13) !important;
    color: {AMBER} !important;
    transform: translateX(4px) !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.12) !important;
    margin: 12px 0 !important;
}}

/* ══ Genel butonlar ════════════════════════════════════════════════════════ */
.stButton > button {{
    background: {OX} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(0,21,47,0.20) !important;
}}
.stButton > button:hover {{
    background: {OX_MID} !important;
    box-shadow: 0 5px 18px rgba(0,21,47,0.28) !important;
    transform: translateY(-1px) !important;
}}

/* ══ Slider ════════════════════════════════════════════════════════════════ */
[data-testid="stSlider"] > div > div > div > div {{
    background: {OX} !important;
}}

/* ══ Sekme (Tabs) ══════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background: {IVORY2};
    border-radius: 10px;
    padding: 4px;
    border: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {TEXT3} !important;
    padding: 9px 18px !important;
    border: none !important;
}}
.stTabs [aria-selected="true"] {{
    background: {OX} !important;
    color: {WHITE} !important;
    font-weight: 700 !important;
}}

/* ══ Input alanları ════════════════════════════════════════════════════════ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {{
    border: 1.5px solid {BORDER} !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    background: {WHITE} !important;
    transition: border-color 0.15s !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: {OX} !important;
    box-shadow: 0 0 0 3px rgba(0,33,71,0.08) !important;
}}

/* ══ Metrik kartlar ════════════════════════════════════════════════════════ */
[data-testid="metric-container"] {{
    background: {WHITE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
    border-top: 3px solid {OX} !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: {OX} !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: {TEXT3} !important;
}}

/* ══ Progress bar ══════════════════════════════════════════════════════════ */
.stProgress > div > div > div {{
    background: linear-gradient(90deg, {OX}, {AMBER}) !important;
    border-radius: 99px !important;
}}
.stProgress > div > div {{
    background: {IVORY2} !important;
    border-radius: 99px !important;
    height: 8px !important;
}}

/* ══ Expander ══════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader {{
    background: {IVORY2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    color: {OX} !important;
    padding: 12px 16px !important;
}}

/* ══ Özel HTML bileşenler ══════════════════════════════════════════════════ */

/* Sidebar logo */
.sb-logo {{
    padding: 28px 18px 22px;
    border-bottom: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 6px;
}}
.sb-title {{
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 19px !important;
    font-weight: 700 !important;
    color: {WHITE} !important;
    letter-spacing: -0.2px;
    line-height: 1.25;
}}
.sb-title-ai {{ color: {AMBER} !important; font-style: italic; }}
.sb-subtitle {{
    font-size: 10px !important;
    color: rgba(255,255,255,0.35) !important;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-top: 5px;
}}
.sb-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255,191,0,0.15);
    border: 1px solid rgba(255,191,0,0.35);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 12px !important;
    font-weight: 700 !important;
    color: {AMBER} !important;
    margin-top: 12px;
}}
.sb-sec {{
    font-size: 9px !important;
    font-weight: 700 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: rgba(255,255,255,0.28) !important;
    padding: 14px 4px 6px;
    display: block;
}}
.sb-item {{
    display: flex; align-items: center; gap: 8px;
    padding: 4px 4px;
    font-size: 12px !important;
    color: rgba(255,255,255,0.40) !important;
}}
.sb-dot {{
    width: 5px; height: 5px;
    background: rgba(255,191,0,0.40);
    border-radius: 50%;
    flex-shrink: 0;
}}

/* Sayfa hero başlık */
.hero {{
    background: {WHITE};
    border-radius: 16px;
    padding: 26px 30px;
    margin-bottom: 24px;
    border: 1px solid {BORDER};
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, {OX}, {AMBER});
}}
.hero-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 24px;
    font-weight: 700;
    color: {OX};
    letter-spacing: -0.4px;
    margin-bottom: 6px;
}}
.hero-sub {{
    font-size: 14px;
    color: {TEXT3};
    line-height: 1.55;
}}

/* Referans / derinlik kutusu (altın çerçeveli) */
.ref-box {{
    background: {AMBER_LT};
    border: 2px solid {AMBER};
    border-radius: 12px;
    padding: 18px 20px;
    margin: 16px 0;
    position: relative;
}}
.ref-box-header {{
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 10px;
}}
.ref-box-icon {{
    font-size: 20px;
    flex-shrink: 0;
}}
.ref-box-title {{
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: {WARN};
}}
.ref-box-source {{
    font-size: 10px;
    color: {TEXT3};
    margin-top: 2px;
    font-style: italic;
}}
.ref-box-body {{
    font-size: 14px;
    color: {TEXT2};
    line-height: 1.70;
}}

/* Kritik uyarı banner */
.critical-banner {{
    background: linear-gradient(135deg, {OX}, {OX_MID});
    border-radius: 10px;
    padding: 14px 18px;
    margin: 14px 0;
    display: flex; align-items: flex-start; gap: 12px;
    color: {WHITE};
}}
.critical-banner-icon {{ font-size: 20px; flex-shrink: 0; margin-top: 2px; }}
.critical-banner-text {{ font-size: 13px; line-height: 1.6; color: rgba(255,255,255,0.90) !important; }}
.critical-banner-text strong {{ color: {AMBER} !important; }}

/* Hoca stratejisi konu çubuğu */
.topic-bar-wrap {{ margin-bottom: 12px; }}
.topic-bar-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 5px;
}}
.topic-bar-name {{
    font-size: 13px; font-weight: 600; color: {OX};
}}
.topic-bar-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; font-weight: 700;
    background: {OX_LIGHT}; color: {OX};
    padding: 2px 9px; border-radius: 20px;
    border: 1px solid rgba(0,33,71,0.18);
}}
.topic-bar-track {{
    height: 8px; background: {IVORY2};
    border-radius: 99px; overflow: hidden;
}}
.topic-bar-fill {{
    height: 100%; border-radius: 99px;
    transition: width 0.6s ease;
}}
.topic-bar-label {{
    font-size: 11px; color: {TEXT3};
    margin-top: 3px; font-style: italic;
}}

/* Quiz kart */
.quiz-card {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 24px 26px;
    margin-bottom: 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    position: relative;
}}
.quiz-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, {OX}, {AMBER});
    border-radius: 14px 14px 0 0;
}}
.quiz-topic {{
    font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em;
    color: {AMBER}; margin-bottom: 10px;
    display: flex; align-items: center; gap: 6px;
}}
.quiz-topic::before {{
    content: '';
    width: 6px; height: 6px;
    background: {AMBER}; border-radius: 50%;
}}
.quiz-q {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 17px; font-weight: 600;
    color: {OX}; line-height: 1.55;
    margin-bottom: 6px;
}}
.quiz-formula {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    background: {IVORY2}; border: 1px solid {BORDER};
    border-left: 4px solid {OX};
    border-radius: 0 8px 8px 0;
    padding: 12px 16px; margin: 12px 0;
    color: {OX};
}}
.feedback-correct {{
    background: {SUCCESS_BG}; border-left: 4px solid {SUCCESS};
    border-radius: 0 10px 10px 0; padding: 14px 18px;
    font-size: 14px; color: {SUCCESS}; margin-top: 14px; line-height: 1.6;
}}
.feedback-wrong {{
    background: {ERROR_BG}; border-left: 4px solid {ERROR};
    border-radius: 0 10px 10px 0; padding: 14px 18px;
    font-size: 14px; color: {ERROR}; margin-top: 14px; line-height: 1.6;
}}

/* Profil kartı */
.profile-card {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 20px;
}}
.profile-card-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 16px; font-weight: 700; color: {OX};
    margin-bottom: 14px; padding-bottom: 10px;
    border-bottom: 1px solid {BORDER};
}}

/* DLVO kontrol paneli */
.ctrl-panel {{
    background: {WHITE}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 20px 18px; margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,21,47,0.05);
}}
.ctrl-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 15px; font-weight: 700; color: {OX};
    margin-bottom: 14px; padding-bottom: 10px;
    border-bottom: 1px solid {BORDER};
}}
.param-lbl {{
    font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em;
    color: {TEXT3}; margin-bottom: 4px;
}}
.param-val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 17px; font-weight: 700; color: {OX};
    background: {OX_LIGHT}; border-radius: 6px;
    padding: 5px 12px; display: inline-block;
    min-width: 80px; text-align: center; margin-bottom: 6px;
}}
.stability-badge {{
    border-radius: 20px; padding: 8px 18px;
    font-size: 13px; font-weight: 700;
    text-align: center; margin: 12px 0; letter-spacing: 0.03em;
}}
.s-stable   {{ background:{SUCCESS_BG}; color:{SUCCESS}; border:1.5px solid #4CAF50; }}
.s-moderate {{ background:{WARN_BG};    color:{WARN};    border:1.5px solid #F59E0B; }}
.s-unstable {{ background:{ERROR_BG};   color:{ERROR};   border:1.5px solid #EF4444; }}

/* Genel yardımcılar */
hr.ox {{ border: none; border-top: 1px solid {BORDER}; margin: 20px 0; }}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# 3.  KONSTANTlar — Farmasötik anahtar kelimeler (frekans analizi için)
# ══════════════════════════════════════════════════════════════════════════════

# Her konu grubu için anahtar kelimeler — PDF taramasında kullanılır
PHARMA_TOPICS: dict[str, list[str]] = {
    "DLVO Teorisi":             ["dlvo","derjaguin","landau","verwey","overbeek","çift tabaka","edl","zeta","debye","hamaker","van der waals","koagülasyon","flokülasyon","kolloidal","kolloid"],
    "Öğütme":                   ["öğütme","kick","rittinger","bond","partikül boyutu","değirmen","bilyalı","çekiçli","jet","kolloit","tane","ufalt","toz","mikronizasyon"],
    "Sterilizasyon":            ["sterilizasyon","steril","d değeri","f₀","f0","otoklav","kuru ısı","etilen oksit","filtrasyon","sal","bioburden","mikroorganizma","spor","bakteri","z değeri"],
    "Emülsiyon & HLB":          ["emülsiyon","hlb","emülgatör","tween","span","o/w","w/o","yağ","su","koalesans","kremalaşma","stabil","surfaktan","yüzey aktif"],
    "Süspansiyon":              ["süspansiyon","sedimantasyon","redispersiyon","flok","viskozite","kıvam","yoğunluk","çökelme","süspansiyon ajanı","zeta potansiyeli"],
    "Kolligatif Özellikler":    ["kolligatif","osmotik","donma noktası","kaynama","buhar basıncı","raoult","van hoff","van't hoff","mol kesri","molalite","molarite"],
    "Stabilite":                ["stabilite","stabil","bozunma","hidroliz","oksidasyon","foto","raf ömrü","arrhenius","aktivasyon enerjisi","t90","hızlandırılmış"],
    "Farmakokinetik":           ["farmakokinetik","auc","cmax","tmax","biyoyararlanım","yarı ömür","dağılım","metabolizma","atılım","absorpsiyon","bcs","permeabilite"],
    "Difüzyon":                 ["difüzyon","fick","difüzyon katsayısı","akı","konsantrasyon","membran","geçirgenlik","pasif","aktif taşıma"],
    "Reoloji":                  ["reoloji","viskozite","akış","newtoniyen","non-newtoniyen","plastik","psödoplastik","dilatan","tiksotropi","kayma"],
}

# Her konu için kısa referans açıklaması (Remington/Aulton tabanlı)
REFERENCE_DEPTH: dict[str, dict] = {
    "DLVO Teorisi": {
        "source": "Israelachvili, J.N. — Intermolecular and Surface Forces (3rd ed., 2011)",
        "content": (
            "DLVO teorisi elektrostatik itme (V_EDL) ve Van der Waals çekimini (V_VdW) "
            "birleştirir. Enerji bariyeri V_max > 15 kT olduğunda süspansiyon kinetik "
            "kararlılık kazanır. Debye uzunluğu κ⁻¹ = √(ε₀εᵣkT / 2NAe²I) ifadesiyle "
            "iyonik şiddet arttıkça azalır; bu da bariyeri çöktürür. "
            "Schulze–Hardy kuralına göre CCC ∝ ζ⁴/z⁶ (z: iyon değerliği)."
        ),
    },
    "Sterilizasyon": {
        "source": "Aulton, M.E. — Pharmaceutics: The Design and Manufacture of Medicines (5th ed.)",
        "content": (
            "D değeri: belirli T'de MO sayısını 1 log azaltmak için gereken süre. "
            "z değeri: D'yi 1 log değiştiren sıcaklık farkı. "
            "F₀ = D₁₂₁·log(N₀/N) — 121°C eşdeğer sterilizasyon süresi. "
            "SAL = 10⁻⁶ hedefi için 12D konsepti uygulanır (N₀=10⁶ → N=10⁻⁶). "
            "Otoklavda tipik F₀ ≥ 8 dk hedeflenir."
        ),
    },
    "Emülsiyon & HLB": {
        "source": "Remington — The Science and Practice of Pharmacy (22nd ed.)",
        "content": (
            "HLB (Griffin, 1949): HLB = Σ(wᵢ·HLBᵢ) / Σwᵢ. O/W emülsiyon: HLB 8–18; "
            "W/O: HLB 3–6. Tween 80 (HLB=15) + Span 80 (HLB=4.3) karışımı ayarlanabilir. "
            "Koalesans geri dönüşsüz faz birleşmesi iken flokülasyon reversible kümelenmedir. "
            "Steric stabilizasyon (PEG) DLVO bariyerine ek V_sterik katkısı sağlar."
        ),
    },
    "Öğütme": {
        "source": "Aulton, M.E. — Pharmaceutics (5th ed.) · Bölüm 9",
        "content": (
            "Kick: E = k·ln(D₁/D₂) — kaba öğütme. "
            "Rittinger: E = k·(S₂−S₁) — ince öğütme; yüzey artışıyla doğru orantı. "
            "Bond: E = C·(1/√D₂ − 1/√D₁) — orta boyut, endüstriyel ekipman seçimi. "
            "Çalışma indisi Wᵢ: %80'i 100 µm'den geçirmek için gereken enerji (kWh/t)."
        ),
    },
    "Stabilite": {
        "source": "ICH Q1A(R2) — Stability Testing of New Drug Substances and Products",
        "content": (
            "t₉₀ = 0.105/k (1. dereceden). Arrhenius: ln(k₂/k₁) = (Eₐ/R)·(1/T₁−1/T₂). "
            "Hızlandırılmış koşullar: 40°C/%75 RH (12 ay) → oda sıcaklığı tahmini. "
            "pH-hız profili: hidroliz genellikle asit/baz katalizi gösterir. "
            "Birincil paketleme materyali seçimi nem ve oksijen bariyerine göre yapılır."
        ),
    },
    "Farmakokinetik": {
        "source": "Shargel & Yu — Applied Biopharmaceutics & Pharmacokinetics (7th ed.)",
        "content": (
            "AUC = ∫C·dt (trapezoid yöntemi). F = AUC_oral/AUC_IV × D_IV/D_oral. "
            "BCS Sınıf I: yüksek çözünürlük + permeabilite → biyoyararlanım formülasyondan bağımsız. "
            "Sınıf II: çözünürlük sınırlayıcı → mikronizasyon, amorf form, nanosüspansiyon. "
            "Sınıf III: permeabilite sınırlayıcı → emici artırıcı gerekir."
        ),
    },
    "Kolligatif Özellikler": {
        "source": "Remington (22nd ed.) · Pharmaceutical Solutions",
        "content": (
            "Raoult: ΔP = P₁°·X₂. Donma: ΔTf = Kf·m·i (Kf_su=1.86 °C·kg/mol). "
            "Osmoz: π = MRTi (R=0.0821 L·atm/mol·K). "
            "İzotonisiteyi sağlamak için NaCl eşdeğeri yöntemi: ΔTf hedef = −0.52°C. "
            "Göz damlalarında izotonisi (290–310 mOsm/L) hasta konforu için kritiktir."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 4.  DLVO FİZİK MOTORu
# ══════════════════════════════════════════════════════════════════════════════

# Fizik sabitleri
_kB   = 1.380649e-23    # Boltzmann (J/K)
_T    = 298.15           # Sıcaklık (K)
_e    = 1.602e-19        # Elektron yükü (C)
_eps0 = 8.854e-12        # Boşluk permitivitesi (F/m)
_NA   = 6.022e23         # Avogadro
_epsr = 80.0             # Su bağıl permitivitesi

def debye_length(I_mM: float) -> float:
    """Debye uzunluğu κ⁻¹ (nm). I: iyonik şiddet (mM)."""
    I_SI = max(I_mM * 1e-3, 1e-9) * 1000   # mol/L → mol/m³
    kappa = math.sqrt(2 * _NA * _e**2 * I_SI / (_epsr * _eps0 * _kB * _T))
    return 1e9 / kappa

def v_edl(h_nm: float, zeta_mV: float, I_mM: float, a_nm: float = 200.0) -> float:
    """EDL itme enerjisi (kT). Derjaguin yaklaşımı, 1:1 elektrolit."""
    if h_nm <= 0:
        return 0.0
    kappa = 1.0 / (debye_length(I_mM) * 1e-9)
    h = h_nm * 1e-9
    a = a_nm * 1e-9
    zeta = zeta_mV * 1e-3
    gamma = math.tanh(_e * zeta / (4 * _kB * _T))
    V = (64 * math.pi * _epsr * _eps0 * a *
         (_kB * _T / _e)**2 * gamma**2 * math.exp(-kappa * h))
    return V / (_kB * _T)

def v_vdw(h_nm: float, a_nm: float = 200.0, A_J: float = 1.0e-20) -> float:
    """VdW çekim enerjisi (kT). Derjaguin, küre–küre."""
    h = max(h_nm, 0.1) * 1e-9
    a = a_nm * 1e-9
    return (-A_J * a / (6 * h)) / (_kB * _T)

def dlvo_arrays(h_arr: np.ndarray, zeta: float, I: float,
                a: float = 200.0, A: float = 1e-20):
    """Tüm h dizisi için (edl, vdw, total) kT dizileri döndür."""
    edl   = np.array([v_edl(h, zeta, I, a)  for h in h_arr])
    vdw   = np.array([v_vdw(h, a, A)         for h in h_arr])
    return edl, vdw, edl + vdw

def stability_info(zeta: float, I: float) -> tuple[str, str, str]:
    """Stabilite sınıfı, etiketi ve açıklaması."""
    h = np.linspace(0.5, 30, 400)
    _, _, total = dlvo_arrays(h, zeta, I)
    barrier = max(float(np.max(total)), 0.0)
    if barrier > 15:
        return "s-stable",   "✅ Kararlı",          f"Bariyer ≈ {barrier:.1f} kT — flokülasyon kinetik olarak engellenir."
    elif barrier > 5:
        return "s-moderate", "⚠️ Sınırda",          f"Bariyer ≈ {barrier:.1f} kT — yavaş flokülasyon olası."
    else:
        return "s-unstable", "🔴 Kararsız",         f"Bariyer ≈ {barrier:.1f} kT — hızlı koagülasyon beklenir."

def make_dlvo_figure(zeta: float, I: float, a: float, A: float) -> go.Figure:
    """İnteraktif DLVO enerji profili (Plotly)."""
    h = np.linspace(0.3, 40, 600)
    edl, vdw, total = dlvo_arrays(h, zeta, I, a, A)

    fig = go.Figure()
    # VdW çekim
    fig.add_trace(go.Scatter(x=h, y=vdw, name="V<sub>VdW</sub>",
        mode="lines", line=dict(color=G_VDW, width=2, dash="dot"),
        hovertemplate="h=%{x:.1f} nm · V=%{y:.1f} kT<extra>VdW</extra>"))
    # EDL itme
    fig.add_trace(go.Scatter(x=h, y=edl, name="V<sub>EDL</sub>",
        mode="lines", line=dict(color=G_EDL, width=2, dash="dash"),
        hovertemplate="h=%{x:.1f} nm · V=%{y:.1f} kT<extra>EDL</extra>"))
    # Toplam
    fig.add_trace(go.Scatter(x=h, y=total, name="V<sub>T</sub> — Toplam",
        mode="lines", line=dict(color=G_TOTAL, width=3),
        fill="tozeroy", fillcolor="rgba(27,94,32,0.07)",
        hovertemplate="h=%{x:.1f} nm · V=%{y:.1f} kT<extra>Toplam</extra>"))

    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.20)", width=1))

    # Bariyer etiketi
    mx = int(np.argmax(total))
    if total[mx] > 1:
        fig.add_annotation(
            x=h[mx], y=total[mx],
            text=f"Bariyer<br>{total[mx]:.1f} kT",
            showarrow=True, arrowhead=2, arrowwidth=1.5,
            arrowcolor=G_TOTAL, ax=45, ay=-40,
            font=dict(size=11, color=G_TOTAL, family="Inter"),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor=G_TOTAL, borderwidth=1, borderpad=4)

    kd = debye_length(I)
    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=56, r=20, t=50, b=56),
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="v", x=0.98, y=0.98,
                    xanchor="right", yanchor="top",
                    bgcolor="rgba(255,255,255,0.92)",
                    bordercolor=BORDER, borderwidth=1,
                    font=dict(size=12)),
        xaxis=dict(title="Mesafe h (nm)", range=[0, 40],
                   gridcolor="#F0EDE6", gridwidth=1,
                   tickfont=dict(family="JetBrains Mono", size=11),
                   showline=True, linecolor=BORDER, mirror=True),
        yaxis=dict(title="Etkileşim Enerjisi (kT)",
                   gridcolor="#F0EDE6", gridwidth=1,
                   tickfont=dict(family="JetBrains Mono", size=11),
                   showline=True, linecolor=BORDER, mirror=True),
        title=dict(
            text=f"DLVO Profili · ζ={zeta} mV · I={I} mM · κ⁻¹≈{kd:.1f} nm",
            font=dict(size=13, family="Playfair Display, Georgia", color=OX),
            x=0.5, xanchor="center"),
        hovermode="x unified",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 5.  PDF ANALİZ MOTORu  (Modül A)
# ══════════════════════════════════════════════════════════════════════════════

def extract_pdf_text(uploaded_file) -> str:
    """
    PyPDF ile PDF'ten düz metin çıkarır.
    Hata durumunda boş string döner; çağıran kod PYPDF_OK ile kontrol eder.
    """
    if not PYPDF_OK:
        return ""
    try:
        reader = PdfReader(uploaded_file)
        pages  = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                pages.append(txt)
        return "\n".join(pages)
    except Exception as exc:
        st.warning(f"PDF okuma hatası: {exc}")
        return ""

def analyse_topics(text: str) -> dict[str, dict]:
    """
    PDF metninde PHARMA_TOPICS anahtar kelimelerini tarar.
    Her konu için {'count': int, 'keywords': list, 'critical': bool} döner.
    """
    text_lower = text.lower()
    results: dict[str, dict] = {}

    for topic, keywords in PHARMA_TOPICS.items():
        found_kws = []
        total_hits = 0
        for kw in keywords:
            # Tam kelime eşleşmesi (Türkçe için basit boundary kontrolü)
            hits = len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower))
            if hits > 0:
                found_kws.append((kw, hits))
                total_hits += hits
        if total_hits > 0:
            results[topic] = {
                "count":    total_hits,
                "keywords": sorted(found_kws, key=lambda x: -x[1])[:5],
                "critical": total_hits >= 5,   # ≥5 atıf → kritik
            }
    # Sırala: atıf sayısına göre azalan
    return dict(sorted(results.items(), key=lambda x: -x[1]["count"]))

def bar_color(rank: int, total: int) -> str:
    """
    Sıralamaya göre renk: ilk %33 Oxford, orta %33 Amber, son kısım gri.
    """
    ratio = rank / max(total, 1)
    if ratio < 0.33:
        return OX
    elif ratio < 0.66:
        return AMBER
    else:
        return "#9CA3AF"

def render_topic_bar(topic: str, count: int, max_count: int,
                     rank: int, total: int, critical: bool) -> None:
    """Tek bir konu çubuğunu HTML olarak çizer."""
    pct   = int(count / max_count * 100)
    color = bar_color(rank, total)
    label = "🔴 KRİTİK — Sınavda çıkması yüksek olası" if critical \
            else "📌 Önemli — Destekleyici kavram"
    st.markdown(f"""
    <div class="topic-bar-wrap">
      <div class="topic-bar-header">
        <span class="topic-bar-name">{'⭐ ' if critical else ''}{topic}</span>
        <span class="topic-bar-count">{count} atıf</span>
      </div>
      <div class="topic-bar-track">
        <div class="topic-bar-fill" style="width:{pct}%;background:{color}"></div>
      </div>
      <div class="topic-bar-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 6.  QUIZ VERİSİ  (Modül C)
# ══════════════════════════════════════════════════════════════════════════════

QUIZ_QUESTIONS: list[dict] = [
    # ── Temel Seviye ──────────────────────────────────────────────────────────
    {
        "level": "temel",
        "topic": "DLVO Teorisi",
        "text": "DLVO teorisinde enerji bariyerini ARTIRAN değişken hangisidir?",
        "options": ["İyonik şiddetin azalması", "İyonik şiddetin artması",
                    "Hamaker sabitinin artması", "Parçacık boyutunun azalması"],
        "correct": 0,
        "why": "İyonik şiddet azaldıkça Debye uzunluğu κ⁻¹ artar, EDL bariyeri genişler ve yükselir.",
        "formula": None,
    },
    {
        "level": "temel",
        "topic": "Sterilizasyon",
        "text": "D değeri neyi ifade eder?",
        "options": ["Mikroorganizma sayısını %90 azaltmak için gereken süre",
                    "Otoklav çalışma sıcaklığı (°C)",
                    "Toplam sterilizasyon süresi",
                    "SAL hedef değeri"],
        "correct": 0,
        "why": "D = Decimal Reduction Time — MO sayısını 1 log (×10) azaltan süre. D₁₂₁ tipik değer: 1–2 dk.",
        "formula": "D = t / log₁₀(N₀ / N)",
    },
    {
        "level": "temel",
        "topic": "Emülsiyon & HLB",
        "text": "HLB değeri 12 olan bir emülgatör hangi tip emülsiyon için uygundur?",
        "options": ["Yağ/Su (O/W)", "Su/Yağ (W/O)", "Katı emülsiyon", "Mikroemülsiyon"],
        "correct": 0,
        "why": "HLB 8–18: hidrofilik → O/W emülsiyon. HLB 3–6: lipofilik → W/O emülsiyon.",
        "formula": None,
    },
    {
        "level": "temel",
        "topic": "Kolligatif Özellikler",
        "text": "Su için kriyoskopik sabit Kf değeri kaçtır?",
        "options": ["1.86 °C·kg/mol", "0.52 °C·kg/mol", "3.14 °C·kg/mol", "0.99 °C·kg/mol"],
        "correct": 0,
        "why": "Kf_su = 1.86 °C·kg/mol, Kb_su = 0.52 °C·kg/mol. Bu sabitler su için sabittir.",
        "formula": "ΔTf = Kf · m · i",
    },
    # ── İleri Seviye ──────────────────────────────────────────────────────────
    {
        "level": "ileri",
        "topic": "DLVO Teorisi",
        "text": (
            "Fizyolojik serum (I ≈ 154 mM) içindeki bir nano-süspansiyonda "
            "zeta potansiyeli −35 mV olmasına rağmen flokülasyon gözlemleniyor. "
            "DLVO teorisi bağlamında bu durumun en olası açıklaması nedir?"
        ),
        "options": [
            "Yüksek iyonik şiddet Debye uzunluğunu dramatik şekilde azaltıp bariyeri çöküştürür",
            "Zeta potansiyeli yeterli yüksektir; flokülasyon başka bir mekanizmadan kaynaklanmaktadır",
            "Van der Waals kuvvetleri serum içinde sıfıra yaklaşır",
            "EDL bariyeri iyonik şiddetten bağımsızdır",
        ],
        "correct": 0,
        "why": (
            "I=154 mM'de κ⁻¹ ≈ 0.78 nm'e düşer (saf suda ~9.6 nm). "
            "Bu kadar ince bir EDL tabakası |ζ|=35 mV'da bile yetersiz bariyer oluşturur. "
            "Sterik stabilizasyon (PEG) bu durumda zorunludur."
        ),
        "formula": "κ⁻¹ = √(ε₀εᵣkT / 2NAe²I)",
    },
    {
        "level": "ileri",
        "topic": "Sterilizasyon",
        "text": (
            "N₀ = 10⁶ başlangıç MO yüküne sahip bir ürün için SAL = 10⁻⁶ hedefleniyor. "
            "D₁₂₁ = 1.5 dk ise gereken F₀ değeri kaçtır ve bu neden önemlidir?"
        ),
        "options": ["F₀ = 18 dk — 12 log azalma gerektirir", "F₀ = 9 dk — 6 log azalma yeterlidir",
                    "F₀ = 6 dk — D değeriyle doğru orantılıdır", "F₀ = 12 dk — sabit bir standarttır"],
        "correct": 0,
        "why": (
            "SAL=10⁻⁶ için N₀=10⁶ → N=10⁻⁶ → 12 log azalma. "
            "F₀ = D₁₂₁ × log(N₀/N) = 1.5 × 12 = 18 dk. "
            "Bu '12D konsepti' olarak bilinir ve en dirençli sporları hedefler."
        ),
        "formula": "F₀ = D₁₂₁ · log(N₀ / N)",
    },
    {
        "level": "ileri",
        "topic": "Farmakokinetik",
        "text": (
            "BCS Sınıf II bir ilaçta (düşük çözünürlük, yüksek permeabilite) "
            "oral biyoyararlanımı artırmak için en uygun formülasyon stratejisi nedir?"
        ),
        "options": [
            "Mikronizasyon veya amorf form oluşturma → çözünürlük artışı",
            "Emici artırıcı kullanımı → permeabilite artışı",
            "Tampon sistemi ile pH ayarı → çözünürlük artışı",
            "Yavaş salım granülü → absorpsiyon süresi uzatımı",
        ],
        "correct": 0,
        "why": (
            "Sınıf II'de permeabilite yüksek, çözünürlük düşük. "
            "Mikronizasyon (yüzey alanı ↑), amorf form (kristalin → amorf → yüksek termodinamik aktivite) "
            "veya nanosüspansiyon çözünürlüğü artırır. Emici artırıcılar Sınıf III içindir."
        ),
        "formula": "F = AUC_oral / AUC_IV × D_IV / D_oral",
    },
    {
        "level": "ileri",
        "topic": "Stabilite",
        "text": (
            "40°C'de ölçülen bozunma hız sabiti k₂ = 0.02 gün⁻¹ olan bir ilaç için "
            "25°C'deki t₉₀ değerini Arrhenius denklemiyle tahmin edebilmek için "
            "aşağıdakilerden hangisine ihtiyaç vardır?"
        ),
        "options": [
            "Aktivasyon enerjisi Eₐ veya ikinci bir sıcaklıkta k değeri",
            "Yalnızca k₂ değeri yeterlidir",
            "Yalnızca pH değeri",
            "Ürünün molekül ağırlığı",
        ],
        "correct": 0,
        "why": (
            "Arrhenius: ln(k₂/k₁) = (Eₐ/R)·(1/T₁ − 1/T₂). "
            "İki bilinmeyeni çözmek için iki denklem gerekir → iki farklı sıcaklıkta k veya Eₐ bilinmeli. "
            "Yalnızca bir k değeriyle tahmin yapılamaz."
        ),
        "formula": "ln(k₂/k₁) = (Eₐ/R) · (1/T₁ − 1/T₂)",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# 7.  OTURUM DURUMU BAŞLATICI
# ══════════════════════════════════════════════════════════════════════════════

def init_state() -> None:
    """Tüm oturum değişkenlerini varsayılan değerleriyle başlatır."""
    defaults = {
        # Navigasyon
        "active_module": "Ana Sayfa",
        # Kullanıcı profili
        "profile_name":  "",
        "profile_level": "Başlangıç",
        "exam_date":     "",
        "profile_saved": False,
        # Puan sistemi
        "score":         0,
        "correct":       0,
        "streak":        0,
        # Quiz durumu
        "quiz_set":      [],
        "quiz_idx":      0,
        "quiz_sel":      None,
        "quiz_answered": False,
        "quiz_filter":   "Tümü",
        # PDF analiz
        "pdf_text":      "",
        "pdf_name":      "",
        "pdf_topics":    {},
        "pdf_analyzed":  False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# 8.  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar() -> None:
    """Oxford Mavisi sidebar: logo, profil rozeti, modül butonları, konu listesi."""
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        name_disp  = st.session_state.profile_name or "Öğrenci"
        level_disp = st.session_state.profile_level
        st.markdown(f"""
        <div class="sb-logo">
            <div class="sb-title">
                PharmaAcademy <span class="sb-title-ai">AI</span>
            </div>
            <div class="sb-subtitle">Farmasötik Teknoloji · Oxford Estetiği</div>
            <div class="sb-badge">⚗️&nbsp; {name_disp} · {level_disp}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Puan rozeti ───────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="display:flex;gap:8px;padding:0 4px;margin:8px 0 4px">
            <div class="sb-badge" style="flex:1;justify-content:center">🏆 {st.session_state.score} puan</div>
            <div class="sb-badge" style="flex:1;justify-content:center">🔥 {st.session_state.streak} seri</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Modül butonları ────────────────────────────────────────────────────
        st.markdown('<span class="sb-sec">Modüller</span>', unsafe_allow_html=True)
        modules = [
            ("Ana Sayfa",              "🏛"),
            ("A · Stratejik Analiz",   "📄"),
            ("B · Kavrayış Atölyesi",  "⚗️"),
            ("C · Akıllı Quiz",        "🧪"),
            ("Profil & Ayarlar",       "👤"),
        ]
        active = st.session_state.active_module
        for mod, icon in modules:
            suffix = "  ◀" if mod == active else ""
            if st.button(f"{icon}  {mod}{suffix}", key=f"nav_{mod}", use_container_width=True):
                st.session_state.active_module = mod
                st.rerun()

        # ── Konu hızlı referansı ──────────────────────────────────────────────
        st.markdown('<span class="sb-sec">Konu Haritası</span>', unsafe_allow_html=True)
        topics_html = "".join(
            f'<div class="sb-item"><span class="sb-dot"></span>{t}</div>'
            for t in PHARMA_TOPICS
        )
        st.markdown(topics_html, unsafe_allow_html=True)

        # ── Versiyon bilgisi ──────────────────────────────────────────────────
        st.markdown("""
        <div style="padding:16px 4px 4px;font-size:10px;
                    color:rgba(255,255,255,0.22);line-height:1.7">
            PharmaAcademy AI v3.0<br>
            Plotly · PyPDF · NumPy<br>
            T=298 K · εᵣ=80 · 1:1 elektrolit
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 9.  ANA SAYFA
# ══════════════════════════════════════════════════════════════════════════════

def render_home() -> None:
    """Karşılama sayfası: hero, modül kartları, hızlı istatistikler."""
    name = st.session_state.profile_name or "Merhaba"
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">👋 {name} — Çalışmaya Hazır mısınız?</div>
        <div class="hero-sub">
            PharmaAcademy AI · Üç modüllü akademik çalışma ortamı ·
            PDF not analizi · İnteraktif DLVO simülatörü · Analitik quiz sistemi
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stat kartları
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("🏆 Puan",      st.session_state.score)
    with c2: st.metric("✅ Doğru",     st.session_state.correct)
    with c3: st.metric("🔥 Seri",      st.session_state.streak)
    with c4: st.metric("📚 Bölüm",     len(PHARMA_TOPICS))

    st.markdown("<hr class='ox'>", unsafe_allow_html=True)
    st.markdown("### Modüller")

    cols = st.columns(3)
    module_data = [
        ("A · Stratejik Analiz",  "📄", "#002147",
         "PDF ders notunuzu yükleyin — hocanızın hangi konulara ağırlık verdiğini ve sınav odaklarını tespit edin.",
         "A · Stratejik Analiz"),
        ("B · Kavrayış Atölyesi", "⚗️", "#1A3A5C",
         "DLVO enerji simülatörü · Zeta potansiyeli ve iyonik şiddeti değiştirin, fizik anlık yanıt versin.",
         "B · Kavrayış Atölyesi"),
        ("C · Akıllı Quiz",       "🧪", "#0D3B6E",
         "'Neden?' sorusunu soran analitik quiz · Seviyenize göre filtrele · Her sorudan sonra derinlemesine açıklama.",
         "C · Akıllı Quiz"),
    ]
    for (title, icon, color, desc, target), col in zip(module_data, cols):
        with col:
            st.markdown(f"""
            <div style="background:{WHITE};border:1px solid {BORDER};
                        border-radius:14px;padding:22px 20px;
                        border-top:4px solid {color};
                        box-shadow:0 2px 8px rgba(0,0,0,0.05);
                        height:100%">
                <div style="font-size:28px;margin-bottom:10px">{icon}</div>
                <div style="font-family:'Playfair Display',Georgia,serif;
                            font-size:16px;font-weight:700;
                            color:{OX};margin-bottom:8px">{title}</div>
                <div style="font-size:13px;color:{TEXT3};line-height:1.6">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button(f"Aç →", key=f"home_{target}", use_container_width=True):
                st.session_state.active_module = target
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 10.  MODÜL A — STRATEJİK ANALİZ (PDF Hoca Modu)
# ══════════════════════════════════════════════════════════════════════════════

def render_module_a() -> None:
    """
    PDF ders notu yükleme → konu frekans analizi → hoca stratejisi haritası
    → kritik konular için referans derinlik bloğu (altın çerçeveli).
    """
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">📄 Modül A — Stratejik Analiz</div>
        <div class="hero-sub">
            Ders notunuzu yükleyin · Hocenizin vurgu haritasını çıkarın ·
            Kritik konularda referans kaynaktan derinlik kazanın
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PDF yoksa kütüphane uyarısı ───────────────────────────────────────────
    if not PYPDF_OK:
        st.error(
            "⚠️ **PyPDF kütüphanesi bulunamadı.**\n\n"
            "Terminale şunu yazın:\n```\npip install pypdf\n```\n"
            "Sonra uygulamayı yeniden başlatın."
        )

    # ── Dosya yükleme alanı ────────────────────────────────────────────────────
    st.markdown("#### 📂 Ders Notunu Yükle")
    uploaded = st.file_uploader(
        "PDF formatında ders notu, slayt veya el notu yükleyin",
        type=["pdf"],
        help="Büyük PDF'lerde analiz 5–10 saniye sürebilir.",
        key="pdf_uploader",
    )

    if uploaded and PYPDF_OK:
        # Daha önce analiz edilmediyse veya yeni dosya yüklendiyse çalıştır
        if not st.session_state.pdf_analyzed or st.session_state.pdf_name != uploaded.name:
            with st.spinner("📖 PDF okunuyor ve analiz ediliyor…"):
                text = extract_pdf_text(uploaded)
                if text.strip():
                    topics = analyse_topics(text)
                    st.session_state.pdf_text     = text
                    st.session_state.pdf_name     = uploaded.name
                    st.session_state.pdf_topics   = topics
                    st.session_state.pdf_analyzed = True
                else:
                    st.error("PDF'ten metin çıkarılamadı. Taranmış (görüntü tabanlı) PDF olabilir.")
                    return

    # ── Analiz sonuçları ───────────────────────────────────────────────────────
    if st.session_state.pdf_analyzed and st.session_state.pdf_topics:
        topics  = st.session_state.pdf_topics
        fname   = st.session_state.pdf_name
        n_chars = len(st.session_state.pdf_text)
        n_words = len(st.session_state.pdf_text.split())

        # Özet bilgi satırı
        st.markdown(f"""
        <div style="background:{OX_LIGHT};border:1px solid {BORDER};
                    border-radius:10px;padding:14px 18px;margin-bottom:20px;
                    display:flex;gap:24px;flex-wrap:wrap">
            <div><span style="font-size:11px;color:{TEXT3};text-transform:uppercase;
                              letter-spacing:0.08em">Dosya</span><br>
                 <strong style="color:{OX}">{fname}</strong></div>
            <div><span style="font-size:11px;color:{TEXT3};text-transform:uppercase;
                              letter-spacing:0.08em">Karakter</span><br>
                 <strong style="color:{OX}">{n_chars:,}</strong></div>
            <div><span style="font-size:11px;color:{TEXT3};text-transform:uppercase;
                              letter-spacing:0.08em">Kelime</span><br>
                 <strong style="color:{OX}">{n_words:,}</strong></div>
            <div><span style="font-size:11px;color:{TEXT3};text-transform:uppercase;
                              letter-spacing:0.08em">Tespit Edilen Konu</span><br>
                 <strong style="color:{OX}">{len(topics)}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Hoca Stratejisi Haritası ──────────────────────────────────────────
        st.markdown("#### 🗺 Hoca Stratejisi Haritası")
        st.caption("Atıf sayısı = hocanın konuya verdiği önem skoru")

        if not topics:
            st.info("PDF'te farmasötik teknoloji anahtar kelimeleri tespit edilemedi.")
            return

        max_count = max(d["count"] for d in topics.values())

        for rank, (topic, data) in enumerate(topics.items()):
            render_topic_bar(
                topic     = topic,
                count     = data["count"],
                max_count = max_count,
                rank      = rank,
                total     = len(topics),
                critical  = data["critical"],
            )
            # Kritik konu → kritik uyarı banner
            if data["critical"]:
                top_kws = ", ".join(f"'{kw}' ({n}×)" for kw, n in data["keywords"][:3])
                st.markdown(f"""
                <div class="critical-banner">
                    <div class="critical-banner-icon">⚠️</div>
                    <div class="critical-banner-text">
                        <strong>KRİTİK KONU — {topic}</strong><br>
                        Hocanız bu notta bu konuya <strong>{data['count']} kez</strong> atıfta bulunmuş.
                        Öne çıkan terimler: {top_kws}.
                        Bu konu sınavda yüksek olasılıkla çıkacaktır.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Referans kaynağından derinlik kutusu (altın çerçeveli)
                if topic in REFERENCE_DEPTH:
                    ref = REFERENCE_DEPTH[topic]
                    st.markdown(f"""
                    <div class="ref-box">
                        <div class="ref-box-header">
                            <span class="ref-box-icon">📚</span>
                            <div>
                                <div class="ref-box-title">
                                    ⚠️ KRİTİK UYARI — Referans Kaynak Derinliği
                                </div>
                                <div class="ref-box-source">
                                    Kaynak: {ref['source']}
                                </div>
                            </div>
                        </div>
                        <div class="ref-box-body">
                            Bu konu ders notlarınızda özetlenmiş olabilir; ancak kavramsal bütünlük ve
                            sınav başarısı için referans kaynaktan ek derinlik ekliyorum:<br><br>
                            {ref['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Ham metin önizleme ────────────────────────────────────────────────
        with st.expander("📜 PDF Ham Metin Önizleme (ilk 1000 karakter)"):
            st.text(st.session_state.pdf_text[:1000] + "…")

        # ── Temizle butonu ───────────────────────────────────────────────────
        if st.button("🗑 Analizi Sıfırla", key="clear_pdf"):
            for k in ("pdf_text", "pdf_name", "pdf_topics", "pdf_analyzed"):
                st.session_state[k] = "" if isinstance(st.session_state[k], str) \
                                      else ({} if isinstance(st.session_state[k], dict) else False)
            st.rerun()

    elif not uploaded:
        # Henüz dosya yüklenmemişse yönlendirme kutusu
        st.markdown(f"""
        <div style="background:{WHITE};border:2px dashed {BORDER};border-radius:14px;
                    padding:40px;text-align:center;margin-top:10px">
            <div style="font-size:48px;margin-bottom:14px">📄</div>
            <div style="font-family:'Playfair Display',Georgia,serif;
                        font-size:18px;font-weight:700;color:{OX};margin-bottom:8px">
                PDF Ders Notunuzu Yükleyin
            </div>
            <div style="font-size:13px;color:{TEXT3};line-height:1.7">
                Sistem hocanızın hangi konulara ağırlık verdiğini analiz eder.<br>
                Kritik konularda Remington ve Aulton referansından ek derinlik sunar.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 11.  MODÜL B — KAVRAYIŞ ATÖLYESİ (İnteraktif DLVO + Referans Derinliği)
# ══════════════════════════════════════════════════════════════════════════════

def render_module_b() -> None:
    """
    DLVO interaktif simülatör (sol kolon) + referans kaynak derinliği (sağ üst)
    + Fick ve Stokes–Einstein ekstra simülasyonları (expander içinde).
    """
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">⚗️ Modül B — Kavrayış Atölyesi</div>
        <div class="hero-sub">
            İnteraktif simülasyonlar · DLVO enerji profili · Referans kaynak derinliği
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Üst Referans Uyarısı (altın kutu) ─────────────────────────────────────
    ref = REFERENCE_DEPTH["DLVO Teorisi"]
    st.markdown(f"""
    <div class="ref-box">
        <div class="ref-box-header">
            <span class="ref-box-icon">📚</span>
            <div>
                <div class="ref-box-title">⚠️ KRİTİK UYARI — Referans Kaynak Derinliği</div>
                <div class="ref-box-source">Kaynak: {ref['source']}</div>
            </div>
        </div>
        <div class="ref-box-body">
            DLVO teorisi ders notlarında özetlenmiş olsa da kavramsal bütünlük için
            referans kaynaktan ek derinlik sunuyorum:<br><br>
            {ref['content']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='ox'>", unsafe_allow_html=True)

    # ── İki kolonlu simülatör düzeni ─────────────────────────────────────────
    col_ctrl, col_graph = st.columns([2, 3], gap="large")

    with col_ctrl:
        st.markdown('<div class="ctrl-panel">', unsafe_allow_html=True)
        st.markdown('<div class="ctrl-title">🎛 DLVO Parametreleri</div>', unsafe_allow_html=True)

        # Zeta potansiyeli
        st.markdown('<div class="param-lbl">Zeta Potansiyeli |ζ| (mV)</div>', unsafe_allow_html=True)
        zeta = st.slider("zeta", 5, 80, 35, 1, label_visibility="collapsed",
                         help="|ζ| > 30 mV → genellikle kararlı süspansiyon")
        st.markdown(f'<div class="param-val">|ζ| = {zeta} mV</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        # İyonik şiddet
        st.markdown('<div class="param-lbl">İyonik Şiddet I (mM)</div>', unsafe_allow_html=True)
        ionic = st.slider("ionic", 1, 300, 10, 1, label_visibility="collapsed",
                          help="↑ I → ↓ Debye uzunluğu → ↓ EDL bariyeri")
        st.markdown(f'<div class="param-val">I = {ionic} mM</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        # Gelişmiş parametreler
        with st.expander("⚙️ Gelişmiş"):
            a_nm = st.number_input("Parçacık yarıçapı a (nm)", 10, 2000, 200, 10)
            A_20 = st.slider("Hamaker sabiti (×10⁻²⁰ J)", 0.5, 10.0, 1.0, 0.5)
            A_J  = A_20 * 1e-20

        st.markdown('</div>', unsafe_allow_html=True)

        # Türetilmiş büyüklükler
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        kd = debye_length(ionic)
        h_q = np.linspace(0.5, 30, 400)
        _, _, tot_q = dlvo_arrays(h_q, zeta, ionic, a_nm, A_J)
        barrier_q = max(float(np.max(tot_q)), 0.0)

        m1, m2 = st.columns(2)
        with m1: st.metric("κ⁻¹",          f"{kd:.1f} nm")
        with m2: st.metric("Bariyer",       f"{barrier_q:.1f} kT")
        m3, m4 = st.columns(2)
        with m3: st.metric("|ζ|≥30 mV?",   "✅" if abs(zeta) >= 30 else "❌")
        with m4: st.metric("Bariyer≥15 kT?","✅" if barrier_q >= 15 else "❌")

        # Stabilite rozeti
        s_cls, s_lbl, s_desc = stability_info(zeta, ionic)
        st.markdown(f'<div class="stability-badge {s_cls}">{s_lbl}</div>', unsafe_allow_html=True)
        st.caption(s_desc)

    with col_graph:
        # Grafik başlığı
        st.markdown(f"""
        <div style="background:{WHITE};border:1px solid {BORDER};border-radius:10px;
                    padding:14px 18px;margin-bottom:12px;border-left:4px solid {OX}">
            <div style="font-family:'Playfair Display',Georgia,serif;font-size:16px;
                        font-weight:700;color:{OX};margin-bottom:3px">
                DLVO Enerji Profili
            </div>
            <div style="font-size:12px;color:{TEXT3}">
                Sürgüleri değiştirin — grafik anlık güncellenir
            </div>
        </div>
        """, unsafe_allow_html=True)

        fig = make_dlvo_figure(zeta, ionic, a_nm, A_J)
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "toImageButtonOptions": {"format": "svg", "filename": "dlvo"},
        })

        # Anlık yorum
        if barrier_q >= 15:
            yorum = f"✅ Enerji bariyeri **{barrier_q:.1f} kT** ile yüksek — termal dalgalanmalar bariyeri aşamaz."
        elif barrier_q >= 5:
            yorum = f"⚠️ Bariyer **{barrier_q:.1f} kT** — sınırda kararlı; yavaş flokülasyon olası."
        else:
            yorum = f"🔴 Bariyer **{barrier_q:.1f} kT** — bariyersiz sistem; hızlı koagülasyon beklenir."
        st.info(yorum)

    # ── Ek Simülasyonlar ──────────────────────────────────────────────────────
    st.markdown("<hr class='ox'>", unsafe_allow_html=True)
    st.markdown("### ➕ Ek İnteraktif Simülasyonlar")

    with st.expander("📐 Öğütme Enerji Hesaplayıcı (Kick · Rittinger · Bond)"):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.markdown("**Kick** — kaba öğütme")
            k_k  = st.number_input("k katsayısı",  value=2.5,   key="kick_k")
            d1_k = st.number_input("D₁ (μm)",      value=500.0, key="kick_d1")
            d2_k = st.number_input("D₂ (μm)",      value=50.0,  key="kick_d2")
            if d2_k > 0 and d1_k > 0:
                e_k = k_k * math.log(d1_k / d2_k)
                st.metric("Enerji (göreceli)", f"{e_k:.4f}")
        with tc2:
            st.markdown("**Rittinger** — ince öğütme")
            k_r  = st.number_input("k sabiti",   value=1.8, key="rit_k")
            s1_r = st.number_input("S₁ (m²/g)", value=0.5, key="rit_s1")
            s2_r = st.number_input("S₂ (m²/g)", value=5.0, key="rit_s2")
            e_r  = k_r * (s2_r - s1_r)
            st.metric("Enerji (göreceli)", f"{e_r:.4f}")
        with tc3:
            st.markdown("**Bond** — orta öğütme")
            c_b  = st.number_input("C′ sabiti",  value=10.0,  key="bond_c")
            d1_b = st.number_input("D₁ (μm)",   value=1000.0,key="bond_d1")
            d2_b = st.number_input("D₂ (μm)",   value=100.0, key="bond_d2")
            if d1_b > 0 and d2_b > 0:
                e_b = c_b * (1/math.sqrt(d2_b) - 1/math.sqrt(d1_b))
                st.metric("Enerji (göreceli)", f"{e_b:.4f}")

    with st.expander("🔬 Sterilizasyon Hesaplayıcı (D · F₀ · t₉₀)"):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("**D Değeri**")
            t_d  = st.number_input("t (dk)",  value=10.0, key="d_t")
            n0_d = st.number_input("N₀ (MO)",value=1e6,  key="d_n0", format="%.0f")
            n_d  = st.number_input("N (MO)", value=100.0,key="d_n",  format="%.0f")
            if n_d > 0 and n0_d > n_d:
                d_val = t_d / math.log10(n0_d / n_d)
                st.metric("D değeri", f"{d_val:.3f} dk")
        with sc2:
            st.markdown("**F₀ Değeri**")
            d121   = st.number_input("D₁₂₁ (dk)",value=1.5,  key="f0_d")
            n0_f   = st.number_input("N₀",        value=1e6,  key="f0_n0", format="%.0f")
            n_f    = st.number_input("N (SAL)",   value=1e-6, key="f0_n",  format="%.2e")
            if n_f > 0 and n0_f > 0:
                f0_val = d121 * math.log10(n0_f / n_f)
                color_f0 = SUCCESS if f0_val >= 8 else ERROR
                st.metric("F₀",f"{f0_val:.2f} dk",
                          delta="✅ Yeterli" if f0_val >= 8 else "⚠️ Yetersiz")
        with sc3:
            st.markdown("**t₉₀ (Raf Ömrü)**")
            k_rate = st.number_input("k (gün⁻¹)", value=0.005, key="t90_k", format="%.4f")
            if k_rate > 0:
                t90_val = 0.105 / k_rate
                st.metric("t₉₀", f"{t90_val:.1f} gün ≈ {t90_val/30:.1f} ay")


# ══════════════════════════════════════════════════════════════════════════════
# 12.  MODÜL C — AKILLI QUIZ
# ══════════════════════════════════════════════════════════════════════════════

def init_quiz(level_filter: str) -> None:
    """Quiz setini seçilen seviyeye göre hazırlar, karıştırır."""
    if level_filter == "Tümü":
        pool = QUIZ_QUESTIONS.copy()
    else:
        pool = [q for q in QUIZ_QUESTIONS if q["level"] == level_filter]
    random.shuffle(pool)
    st.session_state.quiz_set      = pool
    st.session_state.quiz_idx      = 0
    st.session_state.quiz_sel      = None
    st.session_state.quiz_answered = False

def render_module_c() -> None:
    """Analitik quiz: seviye filtresi, soru kartı, geri bildirim, puan."""
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">🧪 Modül C — Akıllı Quiz</div>
        <div class="hero-sub">
            Seviyenize göre filtrelenmiş analitik sorular ·
            Her doğru cevap 10 puan · "Neden?" sorusuna cevap verin
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Üst kontroller
    col_f, col_new = st.columns([3, 1])
    with col_f:
        filter_opts = ["Tümü", "temel", "ileri"]
        new_filter  = st.selectbox("Seviye Filtresi", filter_opts,
                                   index=filter_opts.index(st.session_state.quiz_filter),
                                   key="quiz_filter_sel")
    with col_new:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🔀 Yeni Quiz", use_container_width=True):
            st.session_state.quiz_filter = new_filter
            init_quiz(new_filter)
            st.rerun()

    # Filtre değişti mi?
    if new_filter != st.session_state.quiz_filter:
        st.session_state.quiz_filter = new_filter
        init_quiz(new_filter)
        st.rerun()

    # İlk kez başlatma
    if not st.session_state.quiz_set:
        init_quiz(st.session_state.quiz_filter)

    idx      = st.session_state.quiz_idx
    quiz_set = st.session_state.quiz_set

    # ── Quiz bitti ────────────────────────────────────────────────────────────
    if idx >= len(quiz_set):
        pct = int(st.session_state.correct / max(len(quiz_set), 1) * 100)
        st.markdown(f"""
        <div style="background:{WHITE};border:1px solid {BORDER};border-radius:16px;
                    padding:40px;text-align:center;
                    box-shadow:0 4px 16px rgba(0,0,0,0.07)">
            <div style="font-size:52px;margin-bottom:14px">
                {'🎓' if pct >= 70 else '📚'}
            </div>
            <div style="font-family:'Playfair Display',Georgia,serif;
                        font-size:24px;font-weight:700;color:{OX};margin-bottom:8px">
                Quiz Tamamlandı
            </div>
            <div style="font-size:16px;color:{TEXT2};margin-bottom:6px">
                {st.session_state.correct} / {len(quiz_set)} doğru &nbsp;·&nbsp;
                %{pct} başarı &nbsp;·&nbsp;
                🏆 {st.session_state.score} toplam puan
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("Tekrar Başla", use_container_width=True):
            init_quiz(st.session_state.quiz_filter)
            st.rerun()
        return

    q = quiz_set[idx]
    total = len(quiz_set)

    # İlerleme çubuğu
    st.progress((idx + 1) / total,
                text=f"Soru {idx+1} / {total}  ·  🏆 {st.session_state.score} puan  ·  🔥 {st.session_state.streak} seri")

    # Soru kartı
    badge_color = OX if q["level"] == "ileri" else AMBER
    badge_text  = "İleri Seviye" if q["level"] == "ileri" else "Temel Seviye"
    st.markdown(f"""
    <div class="quiz-card">
        <div class="quiz-topic">
            <span style="background:{badge_color};color:white;padding:2px 9px;
                          border-radius:20px;font-size:10px;font-weight:700;
                          letter-spacing:0.08em">{badge_text}</span>
            &nbsp;&nbsp;{q['topic']}
        </div>
        <div class="quiz-q">{q['text']}</div>
        {'<div class="quiz-formula">' + q["formula"] + '</div>' if q.get("formula") else ""}
    </div>
    """, unsafe_allow_html=True)

    letters = ["A", "B", "C", "D"]

    # Cevap seçilmemişse seçenekleri göster
    if not st.session_state.quiz_answered:
        for i, opt in enumerate(q["options"]):
            if st.button(f"**{letters[i]}.** {opt}",
                         key=f"opt_{idx}_{i}", use_container_width=True):
                st.session_state.quiz_sel = i
                st.rerun()

        if st.session_state.quiz_sel is not None:
            if st.button("✅ Kontrol Et", type="primary", use_container_width=True):
                st.session_state.quiz_answered = True
                if st.session_state.quiz_sel == q["correct"]:
                    st.session_state.score   += 10
                    st.session_state.correct += 1
                    st.session_state.streak  += 1
                else:
                    st.session_state.streak = 0
                st.rerun()

    # Cevap verildiyse geri bildirim göster
    else:
        for i, opt in enumerate(q["options"]):
            if i == q["correct"]:
                st.success(f"**{letters[i]}.** {opt}")
            elif i == st.session_state.quiz_sel and i != q["correct"]:
                st.error(f"**{letters[i]}.** {opt}")
            else:
                st.markdown(f"&ensp;**{letters[i]}.** {opt}")

        # Doğru/yanlış geri bildirim
        if st.session_state.quiz_sel == q["correct"]:
            st.markdown(f"""
            <div class="feedback-correct">
                ✅ <strong>Doğru!</strong> — {q['why']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="feedback-wrong">
                ❌ <strong>Yanlış.</strong> Doğru cevap:
                <strong>{q['options'][q['correct']]}</strong><br>{q['why']}
            </div>
            """, unsafe_allow_html=True)

        # Konuya ait referans derinliği
        if q["topic"] in REFERENCE_DEPTH:
            ref = REFERENCE_DEPTH[q["topic"]]
            st.markdown(f"""
            <div class="ref-box" style="margin-top:14px">
                <div class="ref-box-header">
                    <span class="ref-box-icon">📚</span>
                    <div>
                        <div class="ref-box-title">Referans Derinliği — {q['topic']}</div>
                        <div class="ref-box-source">{ref['source']}</div>
                    </div>
                </div>
                <div class="ref-box-body">{ref['content']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Sonraki soru butonu
        col_n, col_ai = st.columns([2, 1])
        with col_n:
            if st.button("Sonraki Soru →", type="primary", use_container_width=True):
                st.session_state.quiz_idx      += 1
                st.session_state.quiz_sel       = None
                st.session_state.quiz_answered  = False
                st.rerun()
        with col_ai:
            if st.button("⚗️ Simülasyona Git", use_container_width=True):
                st.session_state.active_module = "B · Kavrayış Atölyesi"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 13.  PROFİL & AYARLAR
# ══════════════════════════════════════════════════════════════════════════════

def render_profile() -> None:
    """Kullanıcı profili: isim, seviye, sınav tarihi, istatistikler."""
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">👤 Profil & Ayarlar</div>
        <div class="hero-sub">
            Kişiselleştirilmiş çalışma ortamınızı yapılandırın
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_form, col_stats = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="profile-card-title">👤 Profil Bilgileri</div>', unsafe_allow_html=True)

        name  = st.text_input("Ad Soyad", value=st.session_state.profile_name,
                               placeholder="örn. Ayşe Kaya")
        level = st.selectbox("Çalışma Seviyesi",
                             ["Başlangıç", "Orta", "İleri"],
                             index=["Başlangıç", "Orta", "İleri"].index(
                                 st.session_state.profile_level))
        exam  = st.text_input("Sınav Tarihi (isteğe bağlı)",
                               value=st.session_state.exam_date,
                               placeholder="örn. 20 Ocak 2026")

        if st.button("💾 Profili Kaydet", use_container_width=True):
            st.session_state.profile_name  = name
            st.session_state.profile_level = level
            st.session_state.exam_date     = exam
            st.session_state.profile_saved = True
            st.success("✅ Profil kaydedildi!")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Sıfırlama
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("🔄 Puanları Sıfırla", use_container_width=True):
            st.session_state.score   = 0
            st.session_state.correct = 0
            st.session_state.streak  = 0
            st.rerun()

    with col_stats:
        st.markdown(f"""
        <div class="profile-card">
            <div class="profile-card-title">📊 Çalışma İstatistikleri</div>
        """, unsafe_allow_html=True)

        st.metric("🏆 Toplam Puan",     st.session_state.score)
        st.metric("✅ Doğru Cevap",     st.session_state.correct)
        st.metric("🔥 En İyi Seri",     st.session_state.streak)

        if st.session_state.exam_date:
            st.markdown(f"""
            <div style="background:{OX_LIGHT};border-radius:10px;
                        padding:14px 18px;margin-top:14px;
                        border-left:4px solid {OX}">
                <div style="font-size:11px;font-weight:700;
                            text-transform:uppercase;letter-spacing:0.10em;
                            color:{OX};margin-bottom:4px">Sınav Tarihi</div>
                <div style="font-family:'Playfair Display',Georgia,serif;
                            font-size:18px;font-weight:700;color:{OX}">
                    📅 {st.session_state.exam_date}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Teknik bilgi
    st.markdown("<hr class='ox'>", unsafe_allow_html=True)
    with st.expander("ℹ️ Teknik Bilgi & Kütüphaneler"):
        st.markdown(f"""
        | Bileşen | Durum |
        |---------|-------|
        | `pypdf` — PDF okuma | {'✅ Kurulu' if PYPDF_OK else '❌ Kurulmamış — `pip install pypdf`'} |
        | `numpy` — Sayısal hesap | ✅ Kurulu |
        | `plotly` — Grafikler | ✅ Kurulu |
        | `streamlit` — Arayüz | ✅ Kurulu |

        **DLVO Sabitleri:** kB = 1.381×10⁻²³ J/K · e = 1.602×10⁻¹⁹ C ·
        ε₀ = 8.854×10⁻¹² F/m · εᵣ = 80 (su) · T = 298.15 K · NA = 6.022×10²³
        """)


# ══════════════════════════════════════════════════════════════════════════════
# 14.  MAIN — Uygulama giriş noktası
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # ── Sayfa yapılandırması ──────────────────────────────────────────────────
    st.set_page_config(
        page_title = "PharmaAcademy AI",
        page_icon  = "⚗️",
        layout     = "wide",
        initial_sidebar_state = "expanded",
    )

    # CSS enjeksiyonu
    st.markdown(CSS, unsafe_allow_html=True)

    # Oturum durumunu başlat
    init_state()

    # Sidebar
    render_sidebar()

    # ── Aktif modülü yönlendir ────────────────────────────────────────────────
    module = st.session_state.active_module
    if module == "Ana Sayfa":
        render_home()
    elif module == "A · Stratejik Analiz":
        render_module_a()
    elif module == "B · Kavrayış Atölyesi":
        render_module_b()
    elif module == "C · Akıllı Quiz":
        render_module_c()
    elif module == "Profil & Ayarlar":
        render_profile()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;padding:28px 0 10px;
                font-size:11px;color:{TEXT3};border-top:1px solid {BORDER};
                margin-top:32px;font-family:'Inter',sans-serif">
        PharmaAcademy <em>AI</em> v3.0 · Oxford Estetiği ·
        Plotly · NumPy · PyPDF · Streamlit ·
        Tüm fizik hesaplamaları kT biriminde, T = 298 K, εᵣ = 80 varsayımıyla yapılmaktadır.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
