# capex_piloto_80kw.py
# Dashboard CAPEX Piloto Eólico 80 kW (versión mejorada)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
import base64
import plotly.io as pio
import re
import unicodedata
import math
import html
import textwrap
import requests
import plotly.graph_objects as go
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        PageBreak,
    )
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ModuleNotFoundError:
    REPORTLAB_AVAILABLE = False


# =========================
# CONFIGURACIÓN GLOBAL
# =========================
st.set_page_config(
    page_title="CAPEX Piloto Eólico 80 kW",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CAT_COLOR_MAP = {
    "Desarrollo Tecnológico": "#7FA8A4",            # verde agua mate
    "Componentes Mecánicos": "#4F5D6F",             # azul grafito
    "Sistema Eléctrico y Control": "#D9A766",       # mostaza suave
    "Obras Civiles": "#D7605E",                     # coral apagado
    "Montaje y Logística": "#A9A7A4",               # gris cemento
    "Ensayos y Certificación": "#C98C70",           # terracota suave
    "Contingencias y Administración": "#7B8794",    # gris acero
}

PX_COLORS = [
    "#7FA8A4",
    "#4F5D6F",
    "#D9A766",
    "#D7605E",
    "#A9A7A4",
    "#C98C70",
    "#7B8794",
]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PX_COLORS

DIRECTION_ROLE_COLOR_MAP = {
    "Ingeniero Eléctrico": "#4F5D6F",
    "Ingeniero Mecánico": "#D7605E",
    "Ingeniero de Desarrollo Tecnológico": "#D9A766",
    "Líder de Ingeniería y Proyecto": "#7FA8A4",
}
HUMAN_CAPITAL_SUMMARY_COLOR = "#4F5D6F"

CAPEX_CLP_DEFAULT = 480_000_000
CAPEX_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSlNd3zXc1zV6TUQHnhXlfZtv7QVOv0mBfR_HH69Ht-0qi2aDtCfw5ouLDGIoPH_knhSAtyT2DYE-Qo/"
    "pub?gid=467592026&single=true&output=csv"
)
HITOS_OWNER_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSlNd3zXc1zV6TUQHnhXlfZtv7QVOv0mBfR_HH69Ht-0qi2aDtCfw5ouLDGIoPH_knhSAtyT2DYE-Qo/"
    "pub?gid=1007478838&single=true&output=csv"
)
RIESGO_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSlNd3zXc1zV6TUQHnhXlfZtv7QVOv0mBfR_HH69Ht-0qi2aDtCfw5ouLDGIoPH_knhSAtyT2DYE-Qo/"
    "pub?gid=1912427793&single=true&output=csv"
)
VALORIZACION_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQfQcSn40boiOyRvYeX1j5SO2O9w3WoA6DkOEMxxf85v-WiWXuMC-uyBWb3-ff82pUfk1cSaBnmrcqU/"
    "pub?gid=1756066076&single=true&output=csv"
)
EERRV2_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQfQcSn40boiOyRvYeX1j5SO2O9w3WoA6DkOEMxxf85v-WiWXuMC-uyBWb3-ff82pUfk1cSaBnmrcqU/"
    "pub?gid=372370214&single=true&output=csv"
)

_HERO_CANDIDATES = [
    (Path(__file__).parent / "assets" / "hero_vawt.jpg").resolve(),
    (Path(__file__).parent / "hero_vawt.jpg").resolve(),
]


def _hero_path():
    for candidate in _HERO_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def render_inputs_main_hero() -> None:
    path = _hero_path()
    hero_bg_css = ""
    if path:
        suffix = path.suffix.lower()
        mime = "image/jpeg"
        if suffix == ".png":
            mime = "image/png"
        elif suffix == ".webp":
            mime = "image/webp"
        encoded = base64.b64encode(path.read_bytes()).decode()
        hero_bg_css = f"background-image:url('data:{mime};base64,{encoded}');"

    st.markdown(
        f"""
        <style>
        .inputs-main-hero-shell{{
            margin:4px 0 24px 0;
            min-height:210px;
            border-radius:30px;
            position:relative;
            overflow:hidden;
            padding:24px 30px 22px 30px;
            border:1px solid rgba(191,219,254,.42);
            box-shadow:0 22px 42px rgba(15,23,42,.12);
            background:#eff6ff;
        }}
        .inputs-main-hero-shell::before{{
            content:"";
            position:absolute;
            inset:0;
            background-size:cover;
            background-position:center 30%;
            opacity:.96;
            z-index:0;
            {hero_bg_css}
        }}
        .inputs-main-hero-shell::after{{
            content:"";
            position:absolute;
            inset:0;
            z-index:1;
            background:
                linear-gradient(180deg, rgba(255,255,255,.84) 0%, rgba(255,255,255,.62) 28%, rgba(15,23,42,.20) 100%),
                linear-gradient(90deg, rgba(255,255,255,.22) 0%, rgba(255,255,255,.02) 34%, rgba(15,23,42,.14) 100%);
        }}
        .inputs-main-hero-content{{
            position:relative;
            z-index:2;
            max-width:1200px;
        }}
        .inputs-main-hero-top{{
            display:flex;
            align-items:flex-start;
            gap:16px;
        }}
        .inputs-main-hero-ico{{
            width:56px;
            height:56px;
            border-radius:18px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:34px;
            background:linear-gradient(180deg,#eff6ff 0%,#dbeafe 100%);
            border:1px solid rgba(96,165,250,.26);
            box-shadow:0 10px 24px rgba(59,130,246,.12);
            flex:0 0 auto;
            margin-top:4px;
        }}
        .inputs-main-hero-title{{
            font-size: clamp(34px, 4.6vw, 58px);
            line-height:1.02;
            font-weight:900;
            letter-spacing:-0.03em;
            color:#111827;
            margin:0;
            text-shadow:0 1px 0 rgba(255,255,255,.30);
        }}
        .inputs-main-hero-sub{{
            font-size:15px;
            line-height:1.65;
            color:#4b5563;
            max-width:1080px;
            margin:14px 0 0 0;
        }}
        @media (max-width: 900px){{
            .inputs-main-hero-shell{{
                min-height:160px;
                border-radius:24px;
                padding:18px 18px 16px 18px;
            }}
            .inputs-main-hero-top{{
                gap:12px;
            }}
            .inputs-main-hero-ico{{
                width:46px;
                height:46px;
                font-size:28px;
                border-radius:14px;
            }}
        }}
        </style>
        <div class="inputs-main-hero-shell">
          <div class="inputs-main-hero-content">
            <div class="inputs-main-hero-top">
              <div class="inputs-main-hero-ico">📊</div>
              <div>
                <h1 class="inputs-main-hero-title">Arquitectura de Inversión y Creación de Valor</h1>
                <p class="inputs-main-hero-sub">
                  Panel interactivo para analizar la estructura de inversión del piloto de turbina eólica vertical híbrida.
                  Diseñado para uso en directorio, comité técnico y seguimiento de proyecto.
                </p>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
DASHBOARD_FINANCIERO_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQmVzOg9X7VfxAmOImXHuMvyH4dQmxbFL3DIBqOubi32jKLncgqBEBwnl6j0dXWsm5FkRAcrY4y8BD2/"
    "pub?gid=1417148670&single=true&output=csv"
)
RESTANTE_PILOTO_10KW_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQmVzOg9X7VfxAmOImXHuMvyH4dQmxbFL3DIBqOubi32jKLncgqBEBwnl6j0dXWsm5FkRAcrY4y8BD2/"
    "pub?gid=1167653476&single=true&output=csv"
)
INGENIERIA_PILOTO_10KW_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQOu_diukhhZWDV7kIcU9Ewto4lo_xQdSEZ0FMi2oto-Jb4r2e7aRNCBKF3qoVVk_4XsimMFx7eASkt/"
    "pub?gid=1868833924&single=true&output=csv"
)
INGENIERIA_PILOTO_10KW_CACHE_VERSION = 3
INGENIERIA_PILOTO_10KW_ALLOWED_MONTHS = {"dic", "abr", "may"}
BULLET_CONTEXTO_10KW_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQfQcSn40boiOyRvYeX1j5SO2O9w3WoA6DkOEMxxf85v-WiWXuMC-uyBWb3-ff82pUfk1cSaBnmrcqU/"
    "pub?gid=632353264&single=true&output=csv"
)
KNOWHOW_RESUMEN_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQmVzOg9X7VfxAmOImXHuMvyH4dQmxbFL3DIBqOubi32jKLncgqBEBwnl6j0dXWsm5FkRAcrY4y8BD2/"
    "pub?gid=584994007&single=true&output=csv"
)
GANTT_PROJECT_CSV_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQOu_diukhhZWDV7kIcU9Ewto4lo_xQdSEZ0FMi2oto-Jb4r2e7aRNCBKF3qoVVk_4XsimMFx7eASkt/"
    "pub?gid=0&single=true&output=csv"
)
FIN_PALETTE_SM = {
    "Suministro": "#7FA8A4",
    "I+D": "#4F5D6F",
    "Montaje": "#D9A766",
}
FIN_GRID = "rgba(148,163,184,.25)"
GANTT_DATE_COL_START = "Inicio (AAAA-MM-DD)"
GANTT_DATE_COL_END_PLAN = "Fin plan (AAAA-MM-DD)"
GANTT_DATE_COL_END_REAL = "Fin real"
ASPAS_FRP_GANTT_PHASE_OPTION = "Fabricación ASPAS frp"
GANTT_PROJECT_SOURCE_VERSION = 2
GANTT_COLUMN_ALIASES = {
    "LÃ\xadnea": "Línea",
    "MÃ©todo": "Método",
    "UbicaciÃ³n": "Ubicación",
    "MitigaciÃ³n breve": "Mitigación breve",
}
REMOTE_FETCH_TTL_SECONDS = 3600
REMOTE_CONNECT_TIMEOUT_SECONDS = 5
REMOTE_READ_TIMEOUT_SECONDS = 20

# =========================
# FUNCIONES
# =========================
@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def fetch_remote_file_bytes(url: str, refresh_nonce: int = 0) -> bytes:
    response = requests.get(
        url,
        timeout=(REMOTE_CONNECT_TIMEOUT_SECONDS, REMOTE_READ_TIMEOUT_SECONDS),
        headers={"User-Agent": "streamlit-render-capex-dashboard/1.0"},
    )
    response.raise_for_status()
    return response.content


def read_remote_csv(url: str, *, refresh_nonce: int = 0, **kwargs) -> pd.DataFrame:
    return pd.read_csv(BytesIO(fetch_remote_file_bytes(url, refresh_nonce=refresh_nonce)), **kwargs)


def read_remote_excel(url: str, *, refresh_nonce: int = 0, **kwargs) -> pd.DataFrame:
    return pd.read_excel(BytesIO(fetch_remote_file_bytes(url, refresh_nonce=refresh_nonce)), **kwargs)


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_capex_raw_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df_raw = read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    return df_raw


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_capex_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    """
    Carga el CSV de CAPEX y lo normaliza.
    Soporta dos formatos:
    - Versión CON encabezados: 'ITEM', 'Categoría', 'Participación (%)', 'Monto USD', 'Bullet técnico',
      y opcionalmente 'Mes_inicio', 'Mes_termino', 'Dependencia'.
    - Versión SIN encabezados (formato antiguo): toma las primeras 5 columnas como Item/Categoria/Participacion/Monto/Bullet.
    """
    df_raw = load_capex_raw_data(url, refresh_nonce=refresh_nonce).copy()

    has_named_header = set(["ITEM", "Categoría", "Participación (%)", "Monto USD"]).issubset(
        set(df_raw.columns)
    )

    if has_named_header:
        # --- Formato nuevo, con encabezados ---
        df = pd.DataFrame()
        df["Item"] = df_raw["ITEM"].astype(str).str.strip()
        df["Categoria"] = df_raw["Categoría"].astype(str).str.strip()
        df["Participacion_raw"] = df_raw["Participación (%)"]
        df["Monto_USD_raw"] = df_raw["Monto USD"]
        if "Bullet técnico" in df_raw.columns:
            df["Bullet"] = df_raw["Bullet técnico"].astype(str).str.strip()
        else:
            df["Bullet"] = ""

        # Columnas de calendario para la línea de tiempo (opcionales)
        if "Mes_inicio" in df_raw.columns:
            df["Mes_inicio"] = pd.to_numeric(df_raw["Mes_inicio"], errors="coerce")
        if "Mes_termino" in df_raw.columns:
            df["Mes_termino"] = pd.to_numeric(df_raw["Mes_termino"], errors="coerce")
        if "Dependencia" in df_raw.columns:
            df["Dependencia"] = df_raw["Dependencia"].astype(str).str.strip()

    else:
        # --- Formato antiguo (sin encabezados) ---
        df = df_raw.iloc[:, :5].copy()
        df.columns = ["Item", "Categoria", "Participacion_raw", "Monto_USD_raw", "Bullet"]

    # Limpieza de texto base
    for col in ["Item", "Categoria", "Bullet"]:
        df[col] = df[col].astype(str).str.strip()

    # Parseo de porcentaje
    def parse_pct(x: str) -> float:
        if pd.isna(x):
            return 0.0
        raw = str(x).strip()
        if not raw:
            return 0.0
        has_pct = "%" in raw
        normalized = raw.replace("%", "").replace(",", ".").replace(" ", "")
        try:
            val = float(normalized)
        except ValueError:
            return 0.0
        if has_pct or val >= 1.0:
            val /= 100.0
        return min(max(val, 0.0), 1.0)

    df["Participacion_pct"] = df["Participacion_raw"].apply(parse_pct)

    # Parseo de dinero en USD
    def parse_money(x: str) -> float:
        if pd.isna(x):
            return 0.0
        x = str(x).strip()
        x = x.replace(".", "").replace(" ", "")
        x = x.replace(",", ".")
        try:
            return float(x)
        except ValueError:
            return 0.0

    df["Monto_USD"] = df["Monto_USD_raw"].apply(parse_money)

    return df


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_capex_total_real_clp(url: str, refresh_nonce: int = 0) -> float | None:
    """
    Intenta obtener un total real en CLP directamente desde la hoja publicada de CAPEX.
    Se usa para KPIs que deben reflejar cambios del archivo fuente sin depender del
    total fijo del sidebar.
    """
    try:
        df_raw = load_capex_raw_data(url, refresh_nonce=refresh_nonce).copy()
    except Exception:
        return None

    if df_raw.empty:
        return None

    item_col = find_best_column(df_raw, ["item", "concepto", "descripcion"])
    if item_col:
        df_raw = df_raw[df_raw[item_col].astype(str).str.strip().ne("")].copy()

    candidate_names = [
        "montoclp",
        "montoenclp",
        "montototalclp",
        "costoclp",
        "costototalclp",
        "inversionclp",
        "presupuestoclp",
        "valorclp",
        "montochile",
        "pesoschilenos",
    ]

    selected_col = find_best_column(df_raw, candidate_names)
    if not selected_col:
        for col in df_raw.columns:
            norm = normalize_key(col)
            if "clp" not in norm:
                continue
            if any(token in norm for token in ["usd", "anticipo", "entrega", "sat", "mes", "porcentaje", "pct"]):
                continue
            selected_col = col
            break

    if not selected_col:
        return None

    total_clp = df_raw[selected_col].apply(parse_money_clp_robusto).sum()
    return float(total_clp) if np.isfinite(total_clp) and total_clp > 0 else None


def parse_money_clp_robusto(x: str) -> float:
    """Convierte montos CLP escritos con separadores latinos o mixtos a float."""
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if not s:
        return 0.0

    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]

    s = (s.replace("$", "")
           .replace("CLP", "")
           .replace(" ", "")
           .replace("\u00a0", ""))
    s = re.sub(r"[^0-9,.\-]", "", s)

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        if s.count(".") > 1:
            s = s.replace(".", "")
        elif "." in s:
            left, right = s.split(".")
            if len(right) == 3 and left.isdigit():
                s = left + right

    try:
        val = float(s)
        return -val if neg else val
    except ValueError:
        return 0.0


def build_google_sheet_xlsx_candidates(url: str) -> list[str]:
    """Genera candidatos de URL XLSX a partir de una URL publicada de Google Sheets."""
    parsed = urlparse(url)
    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    candidates = []

    if "docs.google.com" not in parsed.netloc:
        return [url]

    query_xlsx = dict(query_pairs)
    query_xlsx["output"] = "xlsx"
    candidates.append(urlunparse(parsed._replace(query=urlencode(query_xlsx))))

    query_pub = {"output": "xlsx"}
    candidates.append(urlunparse(parsed._replace(query=urlencode(query_pub))))

    if "/pub" in parsed.path:
        candidates.append(urlunparse(parsed._replace(path=parsed.path.replace("/pub", "/pub", 1), query="output=xlsx")))

    deduped = []
    for cand in candidates:
        if cand not in deduped:
            deduped.append(cand)
    return deduped


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_director_general_data(sheet_source_url: str, sheet_name: str = "Director General Técnico", refresh_nonce: int = 0) -> pd.DataFrame:
    """Carga la hoja de Dirección Técnica desde el mismo Google Sheet publicado."""
    last_error = None
    cargo_display_map = {
        "Director General Técnico": "Líder de Ingeniería y Proyecto",
        "Ingeniero Proyecto (PMO)": "Ingeniero de Desarrollo Tecnológico",
    }
    for candidate_url in build_google_sheet_xlsx_candidates(sheet_source_url):
        try:
            df_raw = read_remote_excel(candidate_url, refresh_nonce=refresh_nonce, sheet_name=sheet_name, dtype=str)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            cols_map = {str(c).strip().lower(): c for c in df_raw.columns}
            cargo_col = cols_map.get("cargo")
            meses_col = cols_map.get("meses")
            costo_col = cols_map.get("costo empresa mensual")
            total_col = cols_map.get("total")
            inicio_col = (
                cols_map.get("mes_inicio")
                or cols_map.get("mes inicio")
                or cols_map.get("inicio")
                or cols_map.get("mes de inicio")
                or cols_map.get("inicio mes")
            )

            if not all([cargo_col, meses_col, costo_col, total_col]):
                continue

            df = pd.DataFrame({
                "Cargo": df_raw[cargo_col].astype(str).str.strip(),
                "Meses": pd.to_numeric(df_raw[meses_col], errors="coerce"),
                "Costo empresa mensual": df_raw[costo_col].apply(parse_money_clp_robusto),
                "Total": df_raw[total_col].apply(parse_money_clp_robusto),
                "Mes_inicio": pd.to_numeric(df_raw[inicio_col], errors="coerce") if inicio_col else 1,
            })
            df = df[df["Cargo"].notna() & (df["Cargo"] != "") & (df["Cargo"].str.lower() != "nan")].copy()
            df["Cargo"] = df["Cargo"].replace(cargo_display_map)
            df = df[(df["Meses"].notna()) | (df["Total"] > 0)].copy()
            df["Mes_inicio"] = df["Mes_inicio"].fillna(1).clip(lower=1)
            return df.reset_index(drop=True)
        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"No se pudo leer la hoja '{sheet_name}' desde la publicación de Google Sheets. Último error: {last_error}"
    )


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_valorizacion_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df = read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].where(df[col].notna(), np.nan)
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else np.nan)
            df[col] = df[col].replace({"": np.nan, "nan": np.nan, "None": np.nan})
    return df


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_valorizacion_raw_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    return read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str, header=None)


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_knowhow_resumen_raw_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    return read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str, header=None)


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_eerrv2_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    return read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str, header=None)


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_restante_piloto_10kw_raw_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    return read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str, header=None)


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_bullet_contexto_10kw_raw_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    return read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str, header=None)


def build_restante_piloto_10kw_view(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df_raw = load_restante_piloto_10kw_raw_data(url, refresh_nonce=refresh_nonce)
    if df_raw.empty or df_raw.shape[1] < 3:
        return pd.DataFrame(columns=["Columna A", "Columna B", "Columna C", "Valor B", "Valor C"])

    df_view = df_raw.iloc[:, :3].copy()
    df_view.columns = ["Columna A", "Columna B", "Columna C"]
    for col in df_view.columns:
        df_view[col] = df_view[col].apply(clean_sheet_cell)

    df_view = df_view[
        df_view[["Columna A", "Columna B", "Columna C"]]
        .apply(lambda row: any(str(v).strip() for v in row), axis=1)
    ].reset_index(drop=True)

    df_view["Valor B"] = df_view["Columna B"].apply(parse_model_number)
    df_view["Valor C"] = df_view["Columna C"].apply(parse_money_clp_robusto)

    if not df_view.empty:
        first_row = df_view.iloc[0]
        has_numeric_below = (df_view["Valor B"].iloc[1:] > 0).any() or (df_view["Valor C"].iloc[1:] > 0).any()
        if has_numeric_below and first_row["Valor B"] == 0 and first_row["Valor C"] == 0:
            df_view = df_view.iloc[1:].reset_index(drop=True)

    return df_view


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_ingenieria_piloto_10kw_data(
    url: str,
    refresh_nonce: int = 0,
    source_version: int = INGENIERIA_PILOTO_10KW_CACHE_VERSION,
) -> pd.DataFrame:
    df = read_remote_csv(url, refresh_nonce=refresh_nonce + source_version, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_ingenieria_schedule_date_col(col: str) -> int | None:
    label = str(col).strip().lower()
    match = re.fullmatch(r"(\d{1,2})-([a-záéíóúñ]+)", label)
    if not match:
        return None

    day = int(match.group(1))
    month = (
        match.group(2)
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    month_offsets = {"dic": 0, "ene": 31, "feb": 62, "mar": 90, "abr": 121, "may": 151}
    if month not in INGENIERIA_PILOTO_10KW_ALLOWED_MONTHS:
        return None
    if month not in month_offsets or day < 1 or day > 31:
        return None
    return month_offsets[month] + day


def empty_ingenieria_schedule_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "PIEZA",
            "Tarea",
            "Fecha",
            "Fecha_dt",
            "Fecha_orden",
            "Fecha_plot",
            "Carga",
            "Actividad",
            "_row_order",
            "Inicio_label",
            "Fin_label",
        ]
    )


def format_ingenieria_schedule_day(ts: pd.Timestamp) -> str:
    month_abbr = {
        1: "ene",
        2: "feb",
        3: "mar",
        4: "abr",
        5: "may",
        6: "jun",
        7: "jul",
        8: "ago",
        9: "sep",
        10: "oct",
        11: "nov",
        12: "dic",
    }
    return f"{int(ts.day)}-{month_abbr.get(int(ts.month), '')}"


def build_ingenieria_schedule_from_explicit_ranges(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw.empty:
        return empty_ingenieria_schedule_df()

    header_row_idx = None
    required_tokens = {"id", "piezafrente", "tareaentregable", "inicio", "fin"}
    header_scan_limit = min(len(df_raw), 18)
    for idx in range(header_scan_limit):
        row_tokens = {normalize_key(val) for val in df_raw.iloc[idx].fillna("").tolist() if normalize_key(val)}
        if required_tokens.issubset(row_tokens):
            header_row_idx = idx
            break

    if header_row_idx is None:
        return empty_ingenieria_schedule_df()

    df_matrix = df_raw.iloc[header_row_idx + 1 :].copy()
    df_matrix.columns = [str(col).strip() for col in df_raw.iloc[header_row_idx].tolist()]
    df_matrix = df_matrix.dropna(how="all").reset_index(drop=True)
    if df_matrix.empty:
        return empty_ingenieria_schedule_df()

    pieza_col = find_best_column(df_matrix, ["piezafrente", "piezafrente", "pieza", "frente"])
    tarea_col = find_best_column(df_matrix, ["tareaentregable", "tarea", "entregable"])
    inicio_col = find_best_column(df_matrix, ["inicio"])
    fin_col = find_best_column(df_matrix, ["fin"])
    id_col = find_best_column(df_matrix, ["id"])
    if not pieza_col or not tarea_col or not inicio_col or not fin_col:
        return empty_ingenieria_schedule_df()

    if id_col:
        df_matrix[id_col] = df_matrix[id_col].fillna("").astype(str).str.strip()
        df_matrix = df_matrix[df_matrix[id_col].str.fullmatch(r"\d+")].copy()

    df_matrix[pieza_col] = df_matrix[pieza_col].replace({"": np.nan, "nan": np.nan}).ffill()
    df_matrix[tarea_col] = df_matrix[tarea_col].fillna("").astype(str).str.strip()
    df_matrix = df_matrix[df_matrix[tarea_col] != ""].copy()
    if df_matrix.empty:
        return empty_ingenieria_schedule_df()

    df_matrix["_inicio_dt"] = pd.to_datetime(df_matrix[inicio_col], dayfirst=True, errors="coerce")
    df_matrix["_fin_dt"] = pd.to_datetime(df_matrix[fin_col], dayfirst=True, errors="coerce")
    df_matrix["_fin_dt"] = df_matrix["_fin_dt"].fillna(df_matrix["_inicio_dt"])
    df_matrix = df_matrix.dropna(subset=["_inicio_dt", "_fin_dt"]).copy()
    if df_matrix.empty:
        return empty_ingenieria_schedule_df()

    swapped_mask = df_matrix["_fin_dt"] < df_matrix["_inicio_dt"]
    if swapped_mask.any():
        df_matrix.loc[swapped_mask, ["_inicio_dt", "_fin_dt"]] = df_matrix.loc[
            swapped_mask, ["_fin_dt", "_inicio_dt"]
        ].to_numpy()

    df_matrix["_row_order"] = range(len(df_matrix))
    records = []
    for _, row in df_matrix.iterrows():
        start_dt = pd.Timestamp(row["_inicio_dt"]).normalize()
        end_dt = pd.Timestamp(row["_fin_dt"]).normalize()
        start_label = format_ingenieria_schedule_day(start_dt)
        end_label = format_ingenieria_schedule_day(end_dt)
        for day_dt in pd.date_range(start_dt, end_dt, freq="D"):
            fecha_label = format_ingenieria_schedule_day(pd.Timestamp(day_dt))
            records.append(
                {
                    "PIEZA": str(row[pieza_col]).strip() or "Sin pieza",
                    "Tarea": str(row[tarea_col]).strip() or "Sin tarea",
                    "Fecha": fecha_label,
                    "Fecha_dt": pd.Timestamp(day_dt).normalize(),
                    "Carga": 1.0,
                    "_row_order": int(row["_row_order"]),
                    "Inicio_label": start_label,
                    "Fin_label": end_label,
                }
            )

    if not records:
        return empty_ingenieria_schedule_df()

    df_long = pd.DataFrame.from_records(records)
    unique_dates = sorted(pd.to_datetime(df_long["Fecha_dt"].dropna().unique()).tolist())
    compressed_date_order = {
        pd.Timestamp(fecha_dt).normalize(): idx for idx, fecha_dt in enumerate(unique_dates, start=1)
    }
    df_long["Fecha_plot"] = df_long["Fecha_dt"].map(compressed_date_order)
    df_long["Fecha_orden"] = df_long["Fecha_plot"]
    df_long["Actividad"] = df_long["PIEZA"] + " | " + df_long["Tarea"]
    return df_long.sort_values(["Fecha_dt", "_row_order", "PIEZA", "Tarea"]).reset_index(drop=True)


def build_ingenieria_piloto_10kw_schedule(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df_raw = load_ingenieria_piloto_10kw_data(url, refresh_nonce=refresh_nonce).copy()
    if df_raw.empty:
        return empty_ingenieria_schedule_df()

    pieza_col = find_best_column(df_raw, ["pieza", "piezas"])
    tarea_col = find_best_column(df_raw, ["tarea", "tareas"])
    if not pieza_col or not tarea_col:
        return build_ingenieria_schedule_from_explicit_ranges(df_raw)

    date_col_orders = [
        (col, parsed_order)
        for col in df_raw.columns
        if col not in {pieza_col, tarea_col}
        for parsed_order in [parse_ingenieria_schedule_date_col(col)]
        if parsed_order is not None
    ]
    date_col_orders = sorted(date_col_orders, key=lambda item: item[1])
    date_cols = [col for col, _ in date_col_orders]
    if not date_cols:
        return build_ingenieria_schedule_from_explicit_ranges(df_raw)

    df_raw[pieza_col] = df_raw[pieza_col].replace({"": np.nan, "nan": np.nan}).ffill()
    df_raw[tarea_col] = df_raw[tarea_col].fillna("").astype(str).str.strip()
    df_raw = df_raw[df_raw[tarea_col] != ""].copy()
    df_raw["_row_order"] = range(len(df_raw))

    df_long = df_raw.melt(
        id_vars=[pieza_col, tarea_col, "_row_order"],
        value_vars=date_cols,
        var_name="Fecha",
        value_name="Carga_raw",
    )
    df_long["Carga"] = pd.to_numeric(df_long["Carga_raw"], errors="coerce")
    df_long = df_long.dropna(subset=["Carga"]).copy()
    df_long = df_long[df_long["Carga"] > 0].copy()
    if df_long.empty:
        return build_ingenieria_schedule_from_explicit_ranges(df_raw)

    fecha_order = dict(date_col_orders)
    df_long["Fecha_orden"] = df_long["Fecha"].map(fecha_order)
    active_dates = sorted(df_long["Fecha_orden"].dropna().unique().tolist())
    compressed_date_order = {fecha_orden: idx for idx, fecha_orden in enumerate(active_dates, start=1)}
    df_long["Fecha_plot"] = df_long["Fecha_orden"].map(compressed_date_order)
    df_long = df_long.rename(columns={pieza_col: "PIEZA", tarea_col: "Tarea"})
    df_long["PIEZA"] = df_long["PIEZA"].fillna("Sin pieza").astype(str).str.strip()
    df_long["Tarea"] = df_long["Tarea"].fillna("Sin tarea").astype(str).str.strip()
    df_long["Fecha_dt"] = pd.NaT
    df_long["Inicio_label"] = df_long["Fecha"]
    df_long["Fin_label"] = df_long["Fecha"]
    df_long["Actividad"] = df_long["PIEZA"] + " | " + df_long["Tarea"]
    return df_long.sort_values(["Fecha_orden", "PIEZA", "Tarea"]).reset_index(drop=True)


def build_ingenieria_schedule_summary(df_ing_schedule: pd.DataFrame) -> pd.DataFrame:
    if df_ing_schedule is None or df_ing_schedule.empty:
        return pd.DataFrame(
            columns=[
                "Pieza / frente",
                "Inicio",
                "Fin",
                "Duración calendario",
                "Tareas",
                "Días con actividad",
                "Tarea crítica / mayor duración",
            ]
        )

    df = df_ing_schedule.copy()
    has_real_dates = "Fecha_dt" in df.columns and df["Fecha_dt"].notna().any()

    task_summary = (
        df.groupby(["PIEZA", "Tarea"], as_index=False)
        .agg(
            Fecha_orden_inicio=("Fecha_orden", "min"),
            Fecha_orden_fin=("Fecha_orden", "max"),
            Dias_con_actividad=("Fecha_orden", "nunique"),
            _row_order=("_row_order", "min"),
        )
    )

    if has_real_dates:
        date_bounds = (
            df.groupby(["PIEZA", "Tarea"], as_index=False)
            .agg(
                Fecha_dt_inicio=("Fecha_dt", "min"),
                Fecha_dt_fin=("Fecha_dt", "max"),
            )
        )
        task_summary = task_summary.merge(date_bounds, on=["PIEZA", "Tarea"], how="left")
        task_summary["Duración_calendario"] = (
            (task_summary["Fecha_dt_fin"] - task_summary["Fecha_dt_inicio"]).dt.days + 1
        ).clip(lower=1)
    else:
        task_summary["Duración_calendario"] = (
            task_summary["Fecha_orden_fin"] - task_summary["Fecha_orden_inicio"] + 1
        ).clip(lower=1)

    task_summary = task_summary.sort_values(
        ["PIEZA", "Duración_calendario", "Dias_con_actividad", "_row_order"],
        ascending=[True, False, False, True],
    )
    critical_map = task_summary.drop_duplicates(subset=["PIEZA"]).set_index("PIEZA")["Tarea"].to_dict()

    pieza_summary = (
        df.groupby("PIEZA", as_index=False)
        .agg(
            Fecha_orden_inicio=("Fecha_orden", "min"),
            Fecha_orden_fin=("Fecha_orden", "max"),
            Tareas=("Tarea", "nunique"),
            Dias_con_actividad=("Fecha_orden", "nunique"),
        )
    )

    if has_real_dates:
        pieza_dates = (
            df.groupby("PIEZA", as_index=False)
            .agg(
                Fecha_dt_inicio=("Fecha_dt", "min"),
                Fecha_dt_fin=("Fecha_dt", "max"),
            )
        )
        pieza_summary = pieza_summary.merge(pieza_dates, on="PIEZA", how="left")
        pieza_summary["Duración calendario"] = (
            (pieza_summary["Fecha_dt_fin"] - pieza_summary["Fecha_dt_inicio"]).dt.days + 1
        ).clip(lower=1)
        pieza_summary["Inicio"] = pieza_summary["Fecha_dt_inicio"].dt.strftime("%d-%m-%Y")
        pieza_summary["Fin"] = pieza_summary["Fecha_dt_fin"].dt.strftime("%d-%m-%Y")
    else:
        fecha_ref = (
            df[["PIEZA", "Fecha_orden", "Fecha"]]
            .drop_duplicates()
            .sort_values(["PIEZA", "Fecha_orden"])
        )
        inicio_map = fecha_ref.drop_duplicates(subset=["PIEZA"]).set_index("PIEZA")["Fecha"].to_dict()
        fin_map = fecha_ref.drop_duplicates(subset=["PIEZA"], keep="last").set_index("PIEZA")["Fecha"].to_dict()
        pieza_summary["Duración calendario"] = (
            pieza_summary["Fecha_orden_fin"] - pieza_summary["Fecha_orden_inicio"] + 1
        ).clip(lower=1)
        pieza_summary["Inicio"] = pieza_summary["PIEZA"].map(inicio_map)
        pieza_summary["Fin"] = pieza_summary["PIEZA"].map(fin_map)

    pieza_summary["Tarea crítica / mayor duración"] = pieza_summary["PIEZA"].map(critical_map).fillna("Sin tarea")
    pieza_summary = pieza_summary.rename(
        columns={
            "PIEZA": "Pieza / frente",
            "Dias_con_actividad": "Días con actividad",
        }
    )
    pieza_summary = pieza_summary[
        [
            "Pieza / frente",
            "Inicio",
            "Fin",
            "Duración calendario",
            "Tareas",
            "Días con actividad",
            "Tarea crítica / mayor duración",
        ]
    ].copy()
    pieza_summary["Duración calendario"] = pieza_summary["Duración calendario"].astype(int)
    pieza_summary["Tareas"] = pieza_summary["Tareas"].astype(int)
    pieza_summary["Días con actividad"] = pieza_summary["Días con actividad"].astype(int)
    return pieza_summary.reset_index(drop=True)


def build_bullet_contexto_10kw_sections(url: str, refresh_nonce: int = 0) -> tuple[str, list[dict]]:
    df_raw = load_bullet_contexto_10kw_raw_data(url, refresh_nonce=refresh_nonce)
    if df_raw.empty:
        return "", []

    title = ""
    sections: list[dict] = []
    current_section: dict | None = None

    for _, row in df_raw.fillna("").iterrows():
        a_val = clean_sheet_cell(row.iloc[0]) if len(row) > 0 else ""
        b_val = clean_sheet_cell(row.iloc[1]) if len(row) > 1 else ""

        if not title and a_val:
            title = a_val

        if not b_val:
            continue

        if re.match(r"^\d+\.\s+", b_val):
            current_section = {"title": b_val, "bullets": []}
            sections.append(current_section)
        elif current_section is not None:
            current_section["bullets"].append(b_val)

    return title, sections


def normalize_key(text: str) -> str:
    s = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def find_best_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized_map = {normalize_key(col): col for col in df.columns}
    for candidate in candidates:
        if candidate in normalized_map:
            return normalized_map[candidate]
    return None


def build_valorizacion_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        serie = df[col]
        non_empty = serie.replace({"": np.nan, "nan": np.nan}).dropna()
        example = str(non_empty.iloc[0]) if not non_empty.empty else "-"
        rows.append(
            {
                "Campo": col,
                "Tipo visible": "Texto" if serie.dtype == object else str(serie.dtype),
                "Registros válidos": int(non_empty.shape[0]),
                "Vacíos": int(len(serie) - non_empty.shape[0]),
                "Ejemplo": example[:80],
            }
        )
    return pd.DataFrame(rows)


def clean_sheet_cell(value) -> str:
    if pd.isna(value):
        return ""
    txt = str(value).strip()
    txt = re.sub(r"\s*_\)$", "", txt)
    txt = txt.replace("_)","").strip()
    return txt


def format_compact_usd(value: float) -> str:
    value = float(value or 0.0)
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"US${value / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"US${value / 1_000:.1f}k"
    return format_usd(value)


def style_engineering_table(df: pd.DataFrame, header_color: str = "#2C5783", row_color: str = "#EAF6FF"):
    return (
        df.style
        .set_properties(**{
            "text-align": "center",
            "border": "1px solid rgba(203,213,225,.65)",
        })
        .set_properties(subset=[df.columns[0]], **{"text-align": "left"})
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", header_color),
                    ("color", "white"),
                    ("font-weight", "700"),
                    ("border", "1px solid rgba(203,213,225,.75)"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("padding", "8px 10px"),
                    ("font-size", "14px"),
                ],
            },
        ])
        .apply(
            lambda row: [
                f"background-color: {row_color if row.name % 2 == 0 else '#FFFFFF'}"
                for _ in row
            ],
            axis=1,
        )
    )


def render_engineering_html_table(df: pd.DataFrame, *, bold_labels: set[str] | None = None, height: int = 360) -> None:
    bold_labels = bold_labels or set()
    header_html = "".join(f"<th>{html.escape(str(col))}</th>" for col in df.columns)
    body_rows = []
    for idx, (_, row) in enumerate(df.iterrows()):
        row_class = "eng-html-row-alt" if idx % 2 == 0 else ""
        label = clean_sheet_cell(row.iloc[0]) if len(row) > 0 else ""
        emphasis_class = " eng-html-strong" if label in bold_labels else ""
        cells = "".join(
            f'<td class="{emphasis_class.strip()}">{html.escape(str("" if pd.isna(val) else val))}</td>'
            for val in row
        )
        body_rows.append(f'<tr class="{row_class}">{cells}</tr>')

    st.markdown(
        f"""
        <style>
        .eng-html-table-wrap {{
            max-height:{height}px;
            overflow:auto;
            border:1px solid rgba(203,213,225,.65);
            border-radius:14px;
            background:#ffffff;
        }}
        .eng-html-table {{
            width:100%;
            border-collapse:separate;
            border-spacing:0;
            font-size:12px;
            color:#334155;
        }}
        .eng-html-table th,
        .eng-html-table td {{
            padding:5px 8px;
            border-right:1px solid rgba(203,213,225,.65);
            border-bottom:1px solid rgba(203,213,225,.65);
            text-align:center;
            white-space:nowrap;
        }}
        .eng-html-table th:first-child,
        .eng-html-table td:first-child {{
            text-align:left;
        }}
        .eng-html-table th {{
            position:sticky;
            top:0;
            z-index:1;
            background:#ffffff;
            color:#7c8596;
            font-weight:700;
            font-size:11px;
        }}
        .eng-html-table th:last-child,
        .eng-html-table td:last-child {{
            border-right:none;
        }}
        .eng-html-table tr:last-child td {{
            border-bottom:none;
        }}
        .eng-html-row-alt td {{
            background:#EAF6FF;
        }}
        .eng-html-strong {{
            font-weight:900;
            color:#0f172a;
        }}
        </style>
        <div class="eng-html-table-wrap">
          <table class="eng-html-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>
              {''.join(body_rows)}
            </tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_model_number(value) -> float:
    if pd.isna(value):
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    s = s.replace("US$", "").replace("USD", "").replace("USS", "").replace("$", "").replace("x", "").replace("%", "")
    s = s.replace(" ", "").replace("\u00a0", "")
    s = re.sub(r"[^0-9,.\-]", "", s)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        if s.count(",") == 1 and len(s.split(",")[-1]) <= 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s:
        if s.count(".") > 1:
            s = s.replace(".", "")
        else:
            left, right = s.split(".")
            if len(right) == 3 and left.replace("-", "").isdigit():
                s = left + right
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_model_percent(value) -> float:
    if pd.isna(value):
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    if "%" not in s and parse_model_number(s) <= 1:
        return parse_model_number(s)
    return parse_model_number(s) / 100.0


def get_valorizacion_model_map(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    label_col = df.columns[0]
    value_col = find_best_column(df, ["unnamed6", "valor", "value", "monto", "total"]) or (df.columns[6] if len(df.columns) > 6 else df.columns[-1])
    comment_col = find_best_column(df, ["unnamed7", "comentario", "comment"]) or (df.columns[7] if len(df.columns) > 7 else None)

    model_df = pd.DataFrame(
        {
            "Label": df[label_col],
            "Value": df[value_col] if value_col in df.columns else np.nan,
            "Comment": df[comment_col] if comment_col and comment_col in df.columns else np.nan,
        }
    ).copy()
    model_df["Label"] = model_df["Label"].where(model_df["Label"].notna(), np.nan)
    model_df["Label"] = model_df["Label"].apply(lambda x: str(x).strip() if pd.notna(x) else np.nan)
    model_df["Label"] = model_df["Label"].replace({"": np.nan, "nan": np.nan})
    model_df = model_df.dropna(subset=["Label"]).reset_index(drop=True)
    model_map = {normalize_key(row["Label"]): row["Value"] for _, row in model_df.iterrows()}
    return model_df, model_map


def get_first_model_value(model_map: dict, candidates: list[str], default=0.0) -> float:
    for candidate in candidates:
        key = normalize_key(candidate)
        if key in model_map:
            return parse_model_number(model_map.get(key))
    return float(default)


@st.cache_data(show_spinner=False, ttl=120)
def build_eerrv2_payload(df_eerrv2: pd.DataFrame, model_items: tuple[tuple[str, str], ...], ebitda_unit_default: float) -> dict:
    payload = {
        "eerr_data": pd.DataFrame(),
        "cash_data": pd.DataFrame(),
        "kpi_map": {},
        "precio_venta_turbina": 0.0,
        "costo_estimado_turbina": 0.0,
        "ebitda_unitario_val": float(ebitda_unit_default or 0.0),
        "capex_inicial_eerr": 0.0,
        "chart_df": pd.DataFrame(columns=["Año", "Ingresos", "EBITDA", "Caja_neta", "Ingresos_MM", "EBITDA_MM", "Caja_MM"]),
    }
    if df_eerrv2 is None or df_eerrv2.empty or df_eerrv2.shape[0] < 3:
        return payload

    model_map = dict(model_items)

    eerr_headers = [clean_sheet_cell(v) for v in df_eerrv2.iloc[1, 1:8].tolist()]
    eerr_data = df_eerrv2.iloc[2:10, 1:8].copy()
    eerr_data.columns = eerr_headers
    for col in eerr_data.columns:
        eerr_data[col] = eerr_data[col].map(clean_sheet_cell)

    cash_headers = [clean_sheet_cell(v) for v in df_eerrv2.iloc[1, 1:8].tolist()]
    cash_data = df_eerrv2.iloc[12:23, 1:8].copy()
    cash_data.columns = cash_headers
    for col in cash_data.columns:
        cash_data[col] = cash_data[col].map(clean_sheet_cell)

    kpi_headers = [clean_sheet_cell(v) for v in df_eerrv2.iloc[1, 9:11].tolist()]
    kpi_data = df_eerrv2.iloc[2:10, 9:11].copy()
    kpi_data.columns = kpi_headers
    for col in kpi_data.columns:
        kpi_data[col] = kpi_data[col].map(clean_sheet_cell)
    kpi_map = {
        clean_sheet_cell(row[kpi_headers[0]]): clean_sheet_cell(row[kpi_headers[1]])
        for _, row in kpi_data.iterrows()
        if clean_sheet_cell(row[kpi_headers[0]])
    }

    precio_venta_turbina = get_first_model_value(
        model_map,
        ["Precio venta / turbina", "Precio venta/turbina", "Precio venta turbina"],
    )
    costo_estimado_turbina = get_first_model_value(
        model_map,
        ["Costo estimado / turbina", "Costo estimado/turbina", "Costo estimado turbina"],
    )
    ebitda_unitario_val = get_first_model_value(
        model_map,
        ["EBITDA unitario", "EBITDA unitario de referencia"],
        default=ebitda_unit_default,
    )
    capex_inicial_eerr = parse_model_number(clean_sheet_cell(df_eerrv2.iloc[14, 2])) if df_eerrv2.shape[0] > 14 and df_eerrv2.shape[1] > 2 else 0.0

    eerr_numeric = eerr_data.copy()
    series_cols = [c for c in eerr_numeric.columns if c != "Partida"]
    for col in series_cols:
        eerr_numeric[col] = eerr_numeric[col].map(parse_model_number)
    row_lookup = {normalize_key(clean_sheet_cell(r["Partida"])): r for _, r in eerr_numeric.iterrows()}

    cash_numeric = cash_data.copy()
    cash_series_cols = [c for c in cash_numeric.columns if c != "Partida"]
    for col in cash_series_cols:
        cash_numeric[col] = cash_numeric[col].map(parse_model_number)
    cash_row_lookup = {normalize_key(clean_sheet_cell(r["Partida"])): r for _, r in cash_numeric.iterrows()}

    years = [c for c in series_cols]
    chart_df = pd.DataFrame({"Año": years})
    ingresos_row = row_lookup.get(normalize_key("Ingresos (USD)"), {})
    ebitda_row = row_lookup.get(normalize_key("EBITDA (USD)"), {})
    caja_row = cash_row_lookup.get(normalize_key("Flujo de caja neto"))
    if not isinstance(caja_row, pd.Series):
        caja_row = cash_row_lookup.get(normalize_key("Flujo caja neto"), {})
    chart_df["Ingresos"] = [ingresos_row.get(y, 0.0) if isinstance(ingresos_row, pd.Series) else 0.0 for y in years]
    chart_df["EBITDA"] = [ebitda_row.get(y, 0.0) if isinstance(ebitda_row, pd.Series) else 0.0 for y in years]
    chart_df["Caja_neta"] = [caja_row.get(y, 0.0) if isinstance(caja_row, pd.Series) else 0.0 for y in years]
    chart_df["Ingresos_MM"] = chart_df["Ingresos"] / 1e6
    chart_df["EBITDA_MM"] = chart_df["EBITDA"] / 1e6
    chart_df["Caja_MM"] = chart_df["Caja_neta"] / 1e6

    payload.update(
        {
            "eerr_data": eerr_data,
            "cash_data": cash_data,
            "kpi_map": kpi_map,
            "precio_venta_turbina": precio_venta_turbina,
            "costo_estimado_turbina": costo_estimado_turbina,
            "ebitda_unitario_val": ebitda_unitario_val,
            "capex_inicial_eerr": capex_inicial_eerr,
            "chart_df": chart_df,
        }
    )
    return payload


def get_knowhow_resumen_payload() -> dict:
    payload = {
        "title": "Know-how técnico derivado de la pestaña Pruebas",
        "subtitle": "",
        "assumptions": [],
        "multipliers": [],
        "kpis": {},
        "family_df": pd.DataFrame(),
        "criteria": [],
    }
    try:
        df_raw = load_knowhow_resumen_raw_data(KNOWHOW_RESUMEN_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
    except Exception:
        return payload

    if df_raw is None or df_raw.empty:
        return payload

    def cell(r: int, c: int) -> str:
        if r >= len(df_raw.index) or c >= len(df_raw.columns):
            return ""
        return clean_sheet_cell(df_raw.iat[r, c])

    payload["title"] = cell(0, 0) or payload["title"]
    payload["subtitle"] = cell(1, 0)

    assumptions = []
    for r in range(4, min(len(df_raw.index), 12)):
        label = cell(r, 0)
        value = cell(r, 1)
        if label and normalize_key(label) != normalize_key("Resumen por familia de know-how"):
            assumptions.append({"label": label, "value": value})
    payload["assumptions"] = assumptions

    multipliers = []
    for r in range(4, min(len(df_raw.index), 12)):
        label = cell(r, 4)
        value = cell(r, 5)
        if label:
            multipliers.append({"label": label, "value": value})
    payload["multipliers"] = multipliers

    kpis = {}
    for r in range(4, min(len(df_raw.index), 12)):
        label = cell(r, 7)
        value = cell(r, 8)
        if label:
            kpis[label] = value
    payload["kpis"] = kpis

    header_idx = None
    for r in range(len(df_raw.index)):
        if normalize_key(cell(r, 0)) == normalize_key("Familia"):
            header_idx = r
            break

    family_rows = []
    if header_idx is not None:
        for r in range(header_idx + 1, len(df_raw.index)):
            familia = cell(r, 0)
            if not familia:
                break
            family_rows.append(
                {
                    "Familia": familia,
                    "# partidas": int(parse_model_number(cell(r, 1)) or 0),
                    "Monto origen (CLP)": float(parse_money_clp_robusto(cell(r, 2)) or 0.0),
                    "Horas modeladas": float(parse_model_number(cell(r, 3)) or 0.0),
                    "Valor modelado (CLP)": float(parse_money_clp_robusto(cell(r, 4)) or 0.0),
                    "% valor modelado": float(parse_model_percent(cell(r, 5)) or 0.0),
                }
            )
    if family_rows:
        family_df = pd.DataFrame(family_rows)
        family_df["Valor modelado (MM CLP)"] = family_df["Valor modelado (CLP)"] / 1_000_000.0
        family_df = family_df.sort_values("Valor modelado (CLP)", ascending=False).reset_index(drop=True)
        payload["family_df"] = family_df

    criteria_idx = None
    for r in range(len(df_raw.index)):
        if normalize_key(cell(r, 7)) == normalize_key("Criterio de revisión"):
            criteria_idx = r
            break
    criteria = []
    if criteria_idx is not None:
        for r in range(criteria_idx + 1, min(len(df_raw.index), criteria_idx + 6)):
            text = cell(r, 7)
            if text:
                criteria.append(text)
    payload["criteria"] = criteria
    return payload


def build_direccion_mensual(df_dir: pd.DataFrame, horizonte_meses: int = 15) -> pd.DataFrame:
    """Expande la hoja de dirección a una serie mensual respetando mes de inicio y duración."""
    if df_dir is None or df_dir.empty:
        return pd.DataFrame(columns=["Mes", "Cargo", "Pago_CLP"])

    rows = []
    for _, row in df_dir.iterrows():
        cargo = str(row.get("Cargo", "")).strip() or "Sin cargo"
        meses = int(pd.to_numeric(row.get("Meses"), errors="coerce") or 0)
        mes_inicio = int(pd.to_numeric(row.get("Mes_inicio"), errors="coerce") or 1)
        costo_mensual = float(pd.to_numeric(row.get("Costo empresa mensual"), errors="coerce") or 0.0)

        if meses <= 0 or costo_mensual <= 0:
            continue

        mes_fin = min(horizonte_meses, mes_inicio + meses - 1)
        for mes in range(mes_inicio, mes_fin + 1):
            rows.append({
                "Mes": mes,
                "Cargo": cargo,
                "Pago_CLP": costo_mensual,
            })

    return pd.DataFrame(rows)


def compute_capex_clp(df: pd.DataFrame, capex_total_clp: float):
    df = df.copy()
    total_usd = df["Monto_USD"].sum()
    tipo_cambio = capex_total_clp / total_usd if total_usd > 0 else np.nan
    df["Monto_CLP"] = df["Monto_USD"] * tipo_cambio
    return df, tipo_cambio, total_usd


def format_clp(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def format_usd(x: float) -> str:
    return f"US${x:,.0f}".replace(",", ".")


def parse_money_usd_robusto(x: str) -> float:
    """
    Convierte strings tipo:
      'US$9.090,91' -> 9090.91
      '9,090.91'    -> 9090.91
      '9090,91'     -> 9090.91
      'US$ 6.200'   -> 6200
    Regla: el separador decimal es el ÚLTIMO (',' o '.') que aparece.
    Todo lo demás se interpreta como separador de miles y se elimina.
    """
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if not s:
        return 0.0

    s = s.replace("US$", "").replace("$", "").replace(" ", "")
    s = re.sub(r"[^0-9\-,\.]", "", s)

    if s in ("", "-", ".", ","):
        return 0.0

    last_comma = s.rfind(",")
    last_dot = s.rfind(".")

    if last_comma == -1 and last_dot == -1:
        try:
            return float(s)
        except ValueError:
            return 0.0

    if "," in s and "." not in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and "," not in s:
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace(".", "")
    else:
        dec_sep = "," if last_comma > last_dot else "."
        if dec_sep == ",":
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_money_mixed_robusto(x) -> float:
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "null", "-", "s/n"}:
        return np.nan

    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]

    s = (
        s.replace("$", "")
        .replace("CLP", "")
        .replace("USD", "")
        .replace("US$", "")
        .replace(" ", "")
        .replace("\u00a0", "")
    )

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        if s.count(".") > 1:
            s = s.replace(".", "")
        elif "." in s:
            left, right = s.split(".")
            if len(right) == 3 and left.replace("-", "").isdigit():
                s = left + right

    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        num = float(s)
        return -num if neg else num
    except ValueError:
        return np.nan


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_dashboard_financiero_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df = read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {
        "Proveedor": "Provedor",
        "Descripcion": "Descripciónn",
        "Descripción": "Descripciónn",
        "Suministro/montaje": "Suministro / montaje",
        "Boleta/fac": "Boleta / fac",
        "Num OC": "N° OC",
        "Dif_T": "diF-T",
        "Porc DI-T": "% DI-T",
        "Dias de Proyecto": "Dias de proyecto",
    }
    for src, dst in rename_map.items():
        if src in df.columns and dst not in df.columns:
            df.rename(columns={src: dst}, inplace=True)

    expected_text = [
        "Etapa", "Estado de pago", "Provedor", "item", "Sub-item", "Descripciónn",
        "Suministro / montaje", "Material", "Uni", "Centro de costo", "Observación",
        "Factor de costo", "Estado de costo", "Justificación % e E.E",
        "Tributa la HIBRIDA", "Tributa la DARRIEUS", "N° OC", "Boleta / fac",
        "Situación factura", "Forma de pago",
    ]
    expected_nums = [
        "Monto", "Dif-1", "Dif-2", "diF-T", "% DI-T", "Dias de proyecto",
        "Descuento ec escala", "Precio final ec esc", "ID-elemento",
    ]

    for col in expected_text + expected_nums:
        if col not in df.columns:
            df[col] = np.nan

    for col in expected_nums:
        df[col] = df[col].apply(parse_money_mixed_robusto)

    return df


def render_inputs_financial_main_kpis(df_in: pd.DataFrame):
    import html

    monto_series = df_in.get("Monto", pd.Series(dtype=float))
    monto_total = float(monto_series.sum(skipna=True) or 0.0)
    monto_prom = float(monto_series.mean(skipna=True) or 0.0)
    n_items = int(monto_series.notna().sum())
    prov_col = "Provedor" if "Provedor" in df_in.columns else ("Proveedor" if "Proveedor" in df_in.columns else None)
    n_prov = int(df_in[prov_col].dropna().astype(str).str.strip().replace({"": np.nan, "nan": np.nan}).nunique()) if prov_col else 0
    capacidades_externo = 0.0
    know_how_fw = 0.0
    try:
        df_val_raw = load_valorizacion_raw_data(VALORIZACION_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
        if df_val_raw.shape[0] > 6 and df_val_raw.shape[1] > 6:
            capacidades_externo = float(parse_money_clp_robusto(clean_sheet_cell(df_val_raw.iloc[5, 6])) or 0.0)
    except Exception:
        capacidades_externo = 0.0
    knowhow_payload = get_knowhow_resumen_payload()
    know_how_fw = float(
        parse_money_clp_robusto(knowhow_payload.get("kpis", {}).get("Valor know-how modelado", ""))
        or 0.0
    )
    if know_how_fw <= 0:
        try:
            if df_val_raw.shape[0] > 6 and df_val_raw.shape[1] > 6:
                know_how_fw = float(parse_money_clp_robusto(clean_sheet_cell(df_val_raw.iloc[6, 6])) or 0.0)
        except Exception:
            know_how_fw = 0.0

    fin_nav_key = "inputs_financiero_asset_sel"
    if fin_nav_key not in st.session_state:
        st.session_state[fin_nav_key] = None

    summary_grid_template = "1.45fr 0.85fr 0.85fr" if capacidades_externo > 0 else "1fr 1fr"
    selector_widths = [1.45, 0.85, 0.85] if capacidades_externo > 0 else [1, 1]

    st.markdown(
        f"""
        <style>
        .inputs-fin-summary{{display:grid;grid-template-columns:{summary_grid_template};gap:16px;margin:10px 0 18px}}
        @media (max-width:1400px){{.inputs-fin-summary{{grid-template-columns:1fr;}}}}
        .inputs-fin-hero,
        .inputs-fin-side{{
            border-radius:20px;
            padding:18px 18px 16px 18px;
            background:linear-gradient(180deg,#f8fafc 0%,#ffffff 68%);
            border:1px solid rgba(148,163,184,.30);
            box-shadow:0 8px 18px rgba(15,23,42,.06);
        }}
        .inputs-fin-hero.active,
        .inputs-fin-side.active{{
            border:1px solid rgba(239,68,68,.32) !important;
            background:linear-gradient(180deg,#fff7f7 0%,#ffecec 100%) !important;
            box-shadow:0 10px 24px rgba(239,68,68,.08) !important;
        }}
        .inputs-fin-hero{{
            background:linear-gradient(90deg,#f4f1ed 0%,#ebe5de 42%,#ddd7cf 100%);
        }}
        .inputs-fin-blank{{
            background:linear-gradient(180deg,#f6f4f1 0%,#ffffff 68%) !important;
        }}
        .inputs-fin-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
        .inputs-fin-ico{{
            width:36px;height:36px;border-radius:999px;display:inline-flex;align-items:center;justify-content:center;
            background:#e7ece8;border:1px solid rgba(79,109,90,.24);font-size:22px
        }}
        .inputs-fin-h{{font-size:13px;font-weight:800;color:#0f172a;letter-spacing:.02em}}
        .inputs-fin-v{{font-size:28px;font-weight:900;color:#0f172a;line-height:1.05;margin-bottom:8px}}
        .inputs-fin-hero .inputs-fin-v{{font-size:36px}}
        .inputs-fin-sub{{display:flex;gap:8px;flex-wrap:wrap}}
        .inputs-fin-chip{{
            display:inline-block;font-size:12px;padding:5px 10px;border-radius:999px;
            border:1px solid rgba(107,114,128,.25);background:#ece9e4;color:#4b5563
        }}
        .inputs-fin-note{{font-size:13px;line-height:1.5;color:#475569;margin-top:6px}}
        .inputs-fin-hero.active .inputs-fin-h,
        .inputs-fin-side.active .inputs-fin-h,
        .inputs-fin-hero.active .inputs-fin-v,
        .inputs-fin-side.active .inputs-fin-v{{
            color:#b91c1c !important;
        }}
        .inputs-fin-hero.active .inputs-fin-note,
        .inputs-fin-side.active .inputs-fin-note{{
            color:#991b1b !important;
        }}
        .inputs-fin-hero.active .inputs-fin-chip,
        .inputs-fin-side.active .inputs-fin-chip{{
            border:1px solid rgba(239,68,68,.24) !important;
            background:#fff4f4 !important;
            color:#991b1b !important;
        }}
        .inputs-fin-hero.active .inputs-fin-ico,
        .inputs-fin-side.active .inputs-fin-ico{{
            border:1px solid rgba(239,68,68,.22) !important;
            background:#fff1f1 !important;
        }}
        .inputs-fin-selector-row{{
            display:grid;
            grid-template-columns:{summary_grid_template};
            gap:16px;
            margin:0 0 18px 0;
        }}
        @media (max-width:1400px){{.inputs-fin-selector-row{{grid-template-columns:1fr;}}}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    costo_active = st.session_state.get(fin_nav_key) == "costo_ejecutado"
    capacidades_active = st.session_state.get(fin_nav_key) == "capacidades_externas"
    knowhow_active = st.session_state.get(fin_nav_key) == "know_how_fw"

    capacidades_card_html = ""
    if capacidades_externo > 0:
        capacidades_card_html = f"""
      <div class="inputs-fin-side {'active' if capacidades_active else ''}">
        <div class="inputs-fin-row"><div class="inputs-fin-ico">🧠</div><div class="inputs-fin-h">Capacidades externo</div></div>
        <div class="inputs-fin-v">{html.escape(format_clp(capacidades_externo))}</div>
        <div class="inputs-fin-sub"><span class="inputs-fin-chip">Valorización FW · G6</span></div>
        <div class="inputs-fin-note">Capacidades complementarias valorizadas fuera del gasto ejecutado directo.</div>
      </div>
        """

    cards = f"""
    <div class="inputs-fin-summary">
      <div class="inputs-fin-hero inputs-fin-blank {'active' if costo_active else ''}">
        <div class="inputs-fin-row"><div class="inputs-fin-ico">💰</div><div class="inputs-fin-h">Costo Ejecutado</div></div>
        <div class="inputs-fin-v">{html.escape(format_clp(monto_total))}</div>
        <div class="inputs-fin-sub">
          <span class="inputs-fin-chip">Base: {n_items:,} ítems</span>
          <span class="inputs-fin-chip">Proveedores: {n_prov:,}</span>
        </div>
        <div class="inputs-fin-note">Inversión efectivamente ejecutada para construir y poner en forma operativa el activo tecnológico.</div>
      </div>
      {capacidades_card_html}
      <div class="inputs-fin-side inputs-fin-blank {'active' if knowhow_active else ''}">
        <div class="inputs-fin-row"><div class="inputs-fin-ico">⚙️</div><div class="inputs-fin-h">Know-how FW</div></div>
        <div class="inputs-fin-v">{html.escape(format_clp(know_how_fw))}</div>
        <div class="inputs-fin-sub"><span class="inputs-fin-chip">Valorización FW · G7</span></div>
        <div class="inputs-fin-note">Valor del conocimiento técnico incorporado en la arquitectura y desarrollo del activo.</div>
      </div>
    </div>
    """
    st.markdown(cards, unsafe_allow_html=True)

    selector_cards = [("costo_ejecutado", "Costo Ejecutado")]
    if capacidades_externo > 0:
        selector_cards.append(("capacidades_externas", "Capacidades externo"))
    selector_cards.append(("know_how_fw", "Know-how FW"))
    selector_cols = st.columns(selector_widths)
    for idx, (value, _label) in enumerate(selector_cards):
        is_active = st.session_state.get(fin_nav_key) == value
        with selector_cols[idx]:
            st.button(
                selector_button_label(_label, is_active),
                key=f"inputs_fin_asset_selector_{idx}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                on_click=lambda selected=value: st.session_state.__setitem__(fin_nav_key, selected),
            )
    return {
        "monto_total": monto_total,
        "capacidades_externo": capacidades_externo,
        "know_how_fw": know_how_fw,
        "selected": st.session_state.get(fin_nav_key),
    }


def render_inputs_knowhow_fw_detail():
    import html

    payload = get_knowhow_resumen_payload()
    family_df = payload.get("family_df", pd.DataFrame()).copy()
    if family_df.empty:
        st.info("La pestaña `KnowHow_Resumen` no contiene información suficiente para construir el detalle.")
        return

    kpis = payload.get("kpis", {})
    assumptions = payload.get("assumptions", [])
    multipliers = payload.get("multipliers", [])
    criteria = payload.get("criteria", [])

    knowhow_total = float(parse_money_clp_robusto(kpis.get("Valor know-how modelado", "")) or family_df["Valor modelado (CLP)"].sum())
    horas_modeladas = float(parse_model_number(kpis.get("Horas modeladas", "")) or family_df["Horas modeladas"].sum())
    n_partidas = int(parse_model_number(kpis.get("# partidas", "")) or family_df["# partidas"].sum())

    kk1, kk2, kk3 = st.columns(3)
    with kk1:
        kpi_card("Know-how modelado", format_clp(knowhow_total), "Valor técnico reconocido desde KnowHow_Resumen.")
    with kk2:
        kpi_card("Horas modeladas", f"{horas_modeladas:,.0f}".replace(",", "."), "Carga técnica valorizada en el modelo.")
    with kk3:
        kpi_card("Partidas atribuidas", f"{n_partidas:,.0f}".replace(",", "."), "Partidas trazadas a conocimiento técnico.")

    fig_knowhow = px.bar(
        family_df.sort_values("Valor modelado (CLP)", ascending=True),
        x="Valor modelado (MM CLP)",
        y="Familia",
        orientation="h",
        color="Familia",
        color_discrete_sequence=["#0F766E", "#2563EB", "#64748B", "#0EA5A4", "#2C5783", "#94A3B8"],
        text=family_df.sort_values("Valor modelado (CLP)", ascending=True)["% valor modelado"].map(lambda v: f"{v * 100:.1f}%"),
        title="Diseño de ingeniería valorizado por familia de know-how",
    )
    fig_knowhow.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        marker=dict(line=dict(color="rgba(255,255,255,0.9)", width=1.1)),
        customdata=np.stack(
            [
                family_df.sort_values("Valor modelado (CLP)", ascending=True)["# partidas"],
                family_df.sort_values("Valor modelado (CLP)", ascending=True)["Horas modeladas"],
                family_df.sort_values("Valor modelado (CLP)", ascending=True)["Monto origen (CLP)"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Valor modelado: %{x:.2f} MM CLP<br>"
            "Partidas: %{customdata[0]:.0f}<br>"
            "Horas modeladas: %{customdata[1]:.0f}<br>"
            "Monto origen: $%{customdata[2]:,.0f}<extra></extra>"
        ),
    )
    fig_knowhow.update_layout(
        showlegend=False,
        xaxis_title="Valor modelado (MM CLP)",
        yaxis_title="Familia técnica",
        margin=dict(l=10, r=10, t=58, b=20),
        height=420,
        bargap=0.24,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    apply_engineering_chart_typography(fig_knowhow, title_size=20, body_size=13, tick_size=12, legend_size=11)
    fig_knowhow.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.20)", zeroline=False, ticksuffix=" MM")
    fig_knowhow.update_yaxes(showgrid=False)

    col_left, col_right = st.columns([1.3, 0.9])
    with col_left:
        st.plotly_chart(fig_knowhow, use_container_width=True, key="inputs_knowhow_family_chart")
        table_df = family_df.copy()
        table_df["Monto origen (CLP)"] = table_df["Monto origen (CLP)"].apply(format_clp)
        table_df["Valor modelado (CLP)"] = table_df["Valor modelado (CLP)"].apply(format_clp)
        table_df["Horas modeladas"] = table_df["Horas modeladas"].map(lambda v: f"{v:,.0f}".replace(",", "."))
        table_df["% valor modelado"] = table_df["% valor modelado"].map(lambda v: f"{v * 100:.1f}%")
        st.markdown("#### Resumen por familia de know-how")
        st.dataframe(
            style_engineering_table(
                table_df[["Familia", "# partidas", "Monto origen (CLP)", "Horas modeladas", "Valor modelado (CLP)", "% valor modelado"]],
                header_color="#0F766E",
                row_color="#ECFDF5",
            ),
            hide_index=True,
            use_container_width=True,
            height=320,
        )
    with col_right:
        st.markdown("#### Supuestos editables")
        if assumptions:
            assump_df = pd.DataFrame(assumptions).rename(columns={"label": "Variable", "value": "Valor"})
            assump_df = assump_df[
                assump_df["Variable"].astype(str).str.strip().ne("")
                & assump_df["Valor"].astype(str).str.strip().ne("")
            ].reset_index(drop=True)
            st.dataframe(
                style_engineering_table(assump_df, header_color="#2C5783", row_color="#EAF6FF"),
                hide_index=True,
                use_container_width=True,
                height=206,
            )
            st.markdown(
                "<div style='margin-top:8px;color:#000000;font-size:14px;line-height:1.5;font-weight:700;'>"
                "* Variables base para valorizar la ingeniería del proyecto por etapa."
                "</div>",
                unsafe_allow_html=True,
            )
        st.markdown("#### Multiplicadores técnicos")
        if multipliers:
            mult_df = pd.DataFrame(multipliers).rename(columns={"label": "Familia", "value": "Multiplicador"})
            st.dataframe(
                style_engineering_table(mult_df, header_color="#475569", row_color="#F8FAFC"),
                hide_index=True,
                use_container_width=True,
                height=246,
            )
            st.markdown(
                "<div style='margin-top:8px;color:#000000;font-size:14px;line-height:1.5;font-weight:700;'>"
                "* Factores que ajustan el valor de la ingeniería según complejidad y madurez del desarrollo."
                "</div>",
                unsafe_allow_html=True,
            )
        if criteria:
            criteria_html = "".join(f"<li>{html.escape(text)}</li>" for text in criteria)
            st.markdown(
                f"""
                <div style="border-radius:18px;padding:16px 18px;background:linear-gradient(180deg,#fff7ed 0%,#fffbeb 100%);
                            border:1px solid rgba(245,158,11,.25);margin-top:8px;">
                  <div style="font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#92400e;margin-bottom:8px;">
                    Criterio de revisión
                  </div>
                  <ul style="margin:0 0 0 18px;padding:0;color:#7c2d12;line-height:1.55;">
                    {criteria_html}
                  </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )


def make_inputs_suministro_chart(df_in: pd.DataFrame):
    df = df_in.copy()
    if "Suministro / montaje" not in df.columns:
        return None, None
    base = df[
        df["Suministro / montaje"].notna()
        & (df["Suministro / montaje"].astype(str).str.strip() != "")
        & df["Monto"].notna()
    ].copy()
    if base.empty:
        return None, None

    base["Categoria"] = base["Suministro / montaje"].astype(str).str.strip()
    agg = (
        base.groupby("Categoria", as_index=False)
        .agg(Monto=("Monto", "sum"), Items=("Monto", "count"))
    )
    if agg.empty:
        return None, None

    total = float(agg["Monto"].sum() or 0.0)
    agg["% del total"] = np.where(total > 0, agg["Monto"] / total * 100.0, 0.0)
    agg["Monto_MM"] = agg["Monto"] / 1_000_000.0
    orden = ["Suministro", "I+D", "Montaje"]
    agg["__ord"] = agg["Categoria"].apply(lambda x: orden.index(x) if x in orden else 999)
    agg = agg.sort_values(["__ord", "Monto"], ascending=[True, False]).drop(columns="__ord")
    agg["label_pct"] = agg.apply(lambda r: f"{r['% del total']:.2f}% · {r['Monto_MM']:.1f} MM", axis=1)

    fig = px.bar(
        agg,
        x="Monto_MM",
        y="Categoria",
        orientation="h",
        color="Categoria",
        color_discrete_map=FIN_PALETTE_SM,
        text="label_pct",
        title="Distribución técnica por frente de ejecución",
    )
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        marker=dict(line=dict(color="rgba(255,255,255,0.85)", width=1.2)),
        hovertemplate=(
            "<b>%{y}</b><br>Monto: $%{customdata[2]:,.0f}<br>% del total: %{customdata[0]:.2f}%"
            "<br>N° ítems: %{customdata[1]}<extra></extra>"
        ),
        customdata=np.stack([agg["% del total"], agg["Items"], agg["Monto"]], axis=-1),
    )
    fig.update_layout(
        xaxis_title="Monto ejecutado (MM CLP)",
        yaxis_title="Frente técnico",
        margin=dict(l=12, r=12, t=64, b=18),
        legend_title="S/M",
        height=360,
        bargap=0.28,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#334155", size=13),
        title=dict(font=dict(size=22, color="#0f172a"), x=0.02),
    )
    fig.update_xaxes(
        ticksuffix=" MM",
        showgrid=True,
        gridcolor="rgba(148,163,184,0.22)",
        zeroline=False,
    )
    fig.update_yaxes(showgrid=False)
    return fig, agg


def apply_engineering_chart_typography(
    fig,
    *,
    title_size: int = 21,
    body_size: int = 13,
    tick_size: int = 12,
    legend_size: int = 12,
):
    layout_updates = {
        "font": dict(color="#334155", size=body_size),
        "legend": dict(font=dict(size=legend_size), title=dict(font=dict(size=legend_size, color="#475569"))),
        "hovermode": "x unified",
        "hoverlabel": dict(
            bgcolor="rgba(255,255,255,0.78)",
            bordercolor="rgba(148,163,184,0.22)",
            font=dict(size=max(body_size - 1, 11), color="#0f172a"),
        ),
    }
    title_text = None
    if hasattr(fig.layout, "title") and fig.layout.title is not None:
        title_text = getattr(fig.layout.title, "text", None)
    if title_text not in (None, "", "undefined"):
        layout_updates["title"] = dict(text=title_text, font=dict(size=title_size, color="#0f172a"), x=0.02)
    else:
        layout_updates["title"] = dict(text="", x=0.02)
    fig.update_layout(**layout_updates)
    fig.update_xaxes(
        title_font=dict(size=body_size, color="#475569"),
        tickfont=dict(size=tick_size, color="#64748B"),
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor="rgba(185,28,28,0.32)",
        spikethickness=1.4,
    )
    fig.update_yaxes(
        title_font=dict(size=body_size, color="#475569"),
        tickfont=dict(size=tick_size, color="#64748B"),
    )
    return fig


def render_inputs_donut_grid_legend(donut_df: pd.DataFrame, item_col: str, donut_palette: list[str]) -> None:
    if donut_df.empty or item_col not in donut_df.columns:
        return

    legend_items = []
    for idx, (_, row) in enumerate(donut_df.iterrows()):
        color = donut_palette[idx % len(donut_palette)]
        label = html.escape(str(row[item_col]))
        share = float(row.get("% del total", 0.0))
        legend_items.append(
            f'<div class="inputs-donut-legend-item">'
            f'<span class="inputs-donut-legend-dot" style="background:{color};"></span>'
            f'<div class="inputs-donut-legend-copy">'
            f'<span class="inputs-donut-legend-label">{label}</span>'
            f'<span class="inputs-donut-legend-share">{share:.1f}% del frente</span>'
            f'</div>'
            f'</div>'
        )

    if len(legend_items) == 7:
        legend_items.append('<div class="inputs-donut-legend-spacer" aria-hidden="true"></div>')

    legend_html = "".join(legend_items)
    st.markdown(
        f"""
        <style>
        .inputs-donut-legend-grid {{
            display:grid;
            grid-template-columns:repeat(4, minmax(0, 1fr));
            gap:12px 16px;
            margin:14px 6px 0 6px;
            align-items:stretch;
        }}
        .inputs-donut-legend-item {{
            display:flex;
            align-items:flex-start;
            gap:10px;
            min-width:0;
            padding:10px 12px;
            border:1px solid rgba(226,232,240,.95);
            border-radius:14px;
            background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
            box-shadow:0 4px 12px rgba(15,23,42,.04);
        }}
        .inputs-donut-legend-spacer {{
            visibility:hidden;
            pointer-events:none;
        }}
        .inputs-donut-legend-dot {{
            width:12px;
            height:12px;
            border-radius:999px;
            margin-top:4px;
            flex:0 0 auto;
            box-shadow:0 0 0 3px rgba(255,255,255,.95);
        }}
        .inputs-donut-legend-copy {{
            display:flex;
            flex-direction:column;
            gap:2px;
            min-width:0;
        }}
        .inputs-donut-legend-label {{
            font-size:0.91rem;
            line-height:1.25;
            font-weight:700;
            color:#475569;
            word-break:break-word;
        }}
        .inputs-donut-legend-share {{
            font-size:0.78rem;
            line-height:1.2;
            color:#94a3b8;
        }}
        @media (max-width: 900px) {{
            .inputs-donut-legend-grid {{
                grid-template-columns:repeat(2, minmax(0, 1fr));
            }}
        }}
        </style>
        <div class="inputs-donut-legend-grid">{legend_html}</div>
        """,
        unsafe_allow_html=True,
    )


def render_single_select_pills_compat(
    label: str,
    options: list[str],
    *,
    default: str,
    key: str,
    format_func=None,
):
    if hasattr(st, "pills"):
        return st.pills(
            label,
            options=options,
            default=default,
            selection_mode="single",
            key=key,
            format_func=format_func,
        )
    if key not in st.session_state or st.session_state[key] not in options:
        st.session_state[key] = default if default in options else options[0]
    return st.radio(
        label,
        options=options,
        horizontal=True,
        key=key,
        format_func=format_func,
    )


def render_inputs_sm_kpi_cards(tabla_sm: pd.DataFrame):
    if tabla_sm is None or tabla_sm.empty:
        return
    st.markdown(
        """
        <style>
        .inputs-smkpi-grid{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px;margin:0 0 12px}
        @media (max-width:1000px){.inputs-smkpi-grid{grid-template-columns:1fr;}}
        .inputs-smkpi-card{
            border-radius:16px;padding:12px 14px;background:linear-gradient(180deg,#f8fafc 0%,#ffffff 62%);
            border:1px solid rgba(148,163,184,.28);box-shadow:0 4px 10px rgba(15,23,42,.04)
        }
        .inputs-smkpi-title{font-size:13px;font-weight:800;color:#0f172a;margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}
        .inputs-smkpi-value{font-size:22px;font-weight:800;color:#0f172a;margin:2px 0 6px}
        .inputs-smkpi-row{font-size:12px;color:#475569;display:flex;gap:6px;flex-wrap:wrap}
        .inputs-smkpi-chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid rgba(148,163,184,.35);background:#f1f5f9;color:#0f172a}
        .inputs-smkpi-bar{position:relative;width:100%;height:6px;border-radius:999px;background:#eef2f7;margin-top:8px}
        .inputs-smkpi-bar>span{position:absolute;left:0;top:0;height:100%;border-radius:999px}
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(min(3, len(tabla_sm)))
    for idx, (_, row) in enumerate(tabla_sm.iterrows()):
        cat = str(row["Categoria"])
        color = FIN_PALETTE_SM.get(cat, "#0E9F6E")
        with cols[idx % len(cols)]:
            st.markdown(
                f"""
                <div class="inputs-smkpi-card">
                  <div class="inputs-smkpi-title">{cat}</div>
                  <div class="inputs-smkpi-value">{format_clp(float(row['Monto']))}</div>
                  <div class="inputs-smkpi-row">
                    <span class="inputs-smkpi-chip">% del total: {float(row['% del total']):.2f}%</span>
                    <span class="inputs-smkpi-chip">Ítems: {int(row['Items'])}</span>
                  </div>
                  <div class="inputs-smkpi-bar"><span style="width:{float(row['% del total']):.6f}%;background:{color};"></span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_inputs_cat_summary_pills(df2: pd.DataFrame, cat_col: str, key_prefix: str = "inputs_fin"):
    agg = (
        df2.groupby(cat_col, as_index=False)
        .agg(Monto=("Monto", "sum"), Items=("Monto", "count"))
    )
    if agg.empty:
        return
    total = float(agg["Monto"].sum() or 0.0)
    agg["pct"] = np.where(total > 0, agg["Monto"] / total * 100.0, 0.0)
    st.markdown(
        """
        <style>
        .inputs-pill-wrap{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 10px}
        .inputs-pill{
            display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;
            border:1px solid rgba(148,163,184,.35);background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.05);
            font-size:12px;color:#0f172a
        }
        .inputs-pill-dot{width:10px;height:10px;border-radius:999px}
        .inputs-pill-sub{opacity:.75}
        </style>
        """,
        unsafe_allow_html=True,
    )
    pills = []
    orden = ["Suministro", "I+D", "Montaje"]
    agg["__ord"] = agg[cat_col].apply(lambda x: orden.index(x) if x in orden else 999)
    agg = agg.sort_values(["__ord", "Monto"], ascending=[True, False]).drop(columns="__ord")
    for _, row in agg.iterrows():
        color = FIN_PALETTE_SM.get(str(row[cat_col]), "#334155")
        pills.append(
            f"""<div class="inputs-pill">
                  <span class="inputs-pill-dot" style="background:{color}"></span>
                  <strong>{row[cat_col]}</strong>
                  <span class="inputs-pill-sub">— {format_clp(float(row['Monto']))} ({float(row['pct']):.2f}%) · {int(row['Items'])} ítems</span>
                </div>"""
        )
    st.markdown(f'<div class="inputs-pill-wrap">{"".join(pills)}</div>', unsafe_allow_html=True)


def render_inputs_item_analytics(df_in: pd.DataFrame):
    df = df_in.copy()
    if "item" not in df.columns:
        st.info("La fuente no contiene columna `item` para construir el análisis por categoría.")
        return

    item_col = "item"
    subitem_col = "Sub-item" if "Sub-item" in df.columns else None
    cat_col = "Suministro / montaje" if "Suministro / montaje" in df.columns else None
    if cat_col is None:
        st.info("La fuente no contiene la columna `Suministro / montaje`.")
        return

    df = df[df["Monto"].notna()].copy()
    df[item_col] = df[item_col].astype(str).str.strip().replace({"": np.nan, "nan": np.nan}).fillna("(Vacío)")
    df[cat_col] = df[cat_col].astype(str).str.strip().replace({"": np.nan, "nan": np.nan}).fillna("(Sin categoría)")
    df[item_col] = df[item_col].replace(
        {
            "Dirección": "Capital Humano",
        }
    )

    st.markdown("### Desglose de Componentes de Inversión")
    cats_all = sorted(df[cat_col].dropna().astype(str).str.strip().unique().tolist())
    preferred_order = [cat for cat in ["Suministro", "I+D", "Montaje"] if cat in cats_all]
    if not preferred_order:
        preferred_order = cats_all[:3]
    selector_key = "inputs_fin_categoria_focus"
    if selector_key not in st.session_state or st.session_state[selector_key] not in preferred_order:
        st.session_state[selector_key] = preferred_order[0] if preferred_order else None
    selected_focus = st.session_state.get(selector_key)

    resumen_cat = (
        df[df[cat_col].isin(preferred_order)]
        .groupby(cat_col, as_index=False)
        .agg(Monto=("Monto", "sum"), Items=("Monto", "count"))
    )
    total_focus = float(resumen_cat["Monto"].sum() or 0.0)
    resumen_cat["pct"] = np.where(total_focus > 0, resumen_cat["Monto"] / total_focus * 100.0, 0.0)
    resumen_cat["__ord"] = resumen_cat[cat_col].apply(lambda x: preferred_order.index(x) if x in preferred_order else 999)
    resumen_cat = resumen_cat.sort_values(["__ord", "Monto"], ascending=[True, False]).drop(columns="__ord")

    st.markdown(
        """
        <style>
        .inputs-focus-grid{
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:12px;
            margin:0 0 14px 0;
        }
        @media (max-width:1000px){
            .inputs-focus-grid{grid-template-columns:1fr;}
        }
        .inputs-focus-card{
            border-radius:20px;
            padding:14px 16px;
            border:1px solid rgba(203,213,225,.72);
            background:linear-gradient(180deg,#ffffff 0%,#f6f4f1 100%);
            box-shadow:0 6px 18px rgba(15,23,42,.05);
            width:100%;
            text-align:left;
        }
        .inputs-focus-card.active{
            border:1px solid rgba(239,68,68,.28);
            background:linear-gradient(180deg,#fff7f7 0%,#ffecec 100%);
            box-shadow:0 10px 24px rgba(239,68,68,.08);
        }
        .inputs-focus-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.10em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:6px;
        }
        .inputs-focus-v{
            font-size:24px;
            font-weight:900;
            line-height:1.02;
            color:#0f172a;
            margin-bottom:6px;
        }
        .inputs-focus-s{
            font-size:13px;
            line-height:1.45;
            color:#475569;
            margin-bottom:10px;
        }
        .inputs-focus-chip{
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding:4px 9px;
            border-radius:999px;
            background:#ece9e4;
            border:1px solid rgba(107,114,128,.18);
            font-size:12px;
            color:#334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    focus_cols = st.columns(len(resumen_cat)) if len(resumen_cat) > 0 else []
    for col, (_, row) in zip(focus_cols, resumen_cat.iterrows()):
        cat = str(row[cat_col])
        is_active = selected_focus == cat
        color = FIN_PALETTE_SM.get(cat, "#64748B")
        with col:
            st.markdown(
                f"""
                <div class="inputs-focus-card {'active' if is_active else ''}">
                    <div class="inputs-focus-k">{html.escape(cat)}</div>
                    <div class="inputs-focus-v">{html.escape(format_clp(float(row['Monto'])))}</div>
                    <div class="inputs-focus-s">Participación de {float(row['pct']):.1f}% dentro del bloque S/M analizado.</div>
                    <span class="inputs-focus-chip"><span style="display:inline-block;width:10px;height:10px;border-radius:999px;background:{color};"></span>{int(row['Items'])} ítems</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                selector_button_label(cat, is_active, action_label=f"Ver {cat}"),
                key=f"inputs_fin_focus_{cat}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                on_click=lambda selected=cat: st.session_state.__setitem__(selector_key, selected),
            )

    df2 = df[df[cat_col] == selected_focus].copy() if selected_focus else df.iloc[0:0].copy()
    if df2.empty:
        st.info("No hay datos para la categoría seleccionada.")
        return

    resumen_item = (
        df2.groupby(item_col, as_index=False)
        .agg(Monto=("Monto", "sum"), Items=("Monto", "count"), Promedio=("Monto", "mean"))
    )
    resumen_item["% del total"] = np.where(
        float(resumen_item["Monto"].sum() or 0.0) > 0,
        resumen_item["Monto"] / float(resumen_item["Monto"].sum()) * 100.0,
        0.0,
    )
    resumen_item["Promedio"] = resumen_item["Promedio"].round(0)
    resumen_item = resumen_item.sort_values("Monto", ascending=False)
    tabla_show = resumen_item.copy()

    if tabla_show.empty:
        st.info("No hay ítems para mostrar.")
        return

    donut_df = tabla_show[[item_col, "Monto", "% del total"]].copy()
    if len(donut_df) > 7:
        top_df = donut_df.head(6).copy()
        other_df = donut_df.iloc[6:]
        donut_df = pd.concat(
            [
                top_df,
                pd.DataFrame(
                    {
                        item_col: ["Otros componentes"],
                        "Monto": [float(other_df["Monto"].sum())],
                        "% del total": [float(other_df["% del total"].sum())],
                    }
                ),
            ],
            ignore_index=True,
        )

    if not donut_df.empty:
        donut_df["label_wrapped"] = donut_df[item_col].apply(
            lambda v: "<br>".join(textwrap.wrap(str(v), width=18)) if len(str(v)) > 18 else str(v)
        )
        donut_df["Monto_MM"] = donut_df["Monto"] / 1_000_000

        donut_palette = [
            "#A9A7A4",
            "#D95F5C",
            "#D9A766",
            "#7FA8A4",
            "#4F5D6F",
            "#6F8F9F",
            "#E5E7EB",
        ]

        fig = px.pie(
            donut_df,
            names="label_wrapped",
            values="Monto",
            hole=0.68,
            color_discrete_sequence=donut_palette,
        )
        donut_df["share_text"] = donut_df["% del total"].apply(lambda v: f"{v:.1f}%")
        fig.update_traces(text=donut_df["share_text"])
        fig.update_traces(
            sort=False,
            textinfo="text",
            textposition="outside",
            texttemplate="%{text}",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Monto: $%{value:,.0f}<br>"
                "Participación del frente: %{percent:.1%}<extra></extra>"
            ),
            marker=dict(line=dict(color="rgba(255,255,255,0.96)", width=2.2)),
            pull=[0.04 if i == 0 else 0 for i in range(len(donut_df))],
        )
        fig.add_annotation(
            x=0.5,
            y=0.575,
            text=f"<span style='font-size:12px;color:#64748b;'>{html.escape(str(selected_focus or 'Frente'))}</span>",
            showarrow=False,
            xanchor="center",
            yanchor="middle",
        )
        fig.add_annotation(
            x=0.5,
            y=0.515,
            text=f"<span style='font-size:24px;color:#0f172a;'><b>{format_clp(float(tabla_show['Monto'].sum()))}</b></span>",
            showarrow=False,
            xanchor="center",
            yanchor="middle",
        )
        fig.update_layout(
            title=dict(
                text="Composición del frente seleccionado",
                x=0,
                xanchor="left",
                font=dict(size=22, color="#0f172a"),
            ),
            height=580,
            margin=dict(l=10, r=10, t=72, b=40),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        apply_engineering_chart_typography(fig, title_size=20, body_size=12, tick_size=11, legend_size=11)

        summary_rows = []
        for idx, (_, rec) in enumerate(tabla_show.head(5).iterrows(), start=1):
            summary_rows.append(
                f"""
                <div class="inputs-donut-insight-row">
                  <div class="inputs-donut-insight-rank">#{idx}</div>
                  <div class="inputs-donut-insight-main">
                    <div class="inputs-donut-insight-name">{html.escape(str(rec[item_col]))}</div>
                    <div class="inputs-donut-insight-sub">{float(rec['% del total']):.1f}% del frente · {format_clp(float(rec['Monto']))}</div>
                  </div>
                </div>
                """
            )

        concentration_top5 = float(tabla_show.head(5)["% del total"].sum() or 0.0)
        donut_cols = st.columns([1.2, 0.95], gap="large")
        with donut_cols[0]:
            st.plotly_chart(fig, use_container_width=True)
            render_inputs_donut_grid_legend(donut_df, item_col, donut_palette)
        with donut_cols[1]:
            st.markdown(
                f"""
                <style>
                .inputs-donut-insight-card {{
                    border:1px solid rgba(226,232,240,.9);
                    border-radius:22px;
                    background:linear-gradient(180deg,#ffffff 0%,#faf8f5 100%);
                    padding:18px 18px 14px 18px;
                    box-shadow:0 10px 24px rgba(15,23,42,.05);
                    min-height:420px;
                }}
                .inputs-donut-insight-kicker {{
                    font-size:11px;
                    letter-spacing:.08em;
                    text-transform:uppercase;
                    color:#64748b;
                    font-weight:700;
                    margin-bottom:6px;
                }}
                .inputs-donut-insight-title {{
                    font-size:18px;
                    line-height:1.15;
                    color:#0f172a;
                    font-weight:800;
                    margin-bottom:10px;
                }}
                .inputs-donut-insight-metric {{
                    border-radius:16px;
                    background:#fff;
                    border:1px solid rgba(226,232,240,.9);
                    padding:12px 14px;
                    margin-bottom:12px;
                }}
                .inputs-donut-insight-value {{
                    font-size:24px;
                    line-height:1.05;
                    color:#0f172a;
                    font-weight:900;
                }}
                .inputs-donut-insight-note {{
                    margin-top:4px;
                    font-size:12px;
                    color:#64748b;
                }}
                .inputs-donut-insight-row {{
                    display:grid;
                    grid-template-columns:44px minmax(0,1fr);
                    gap:10px;
                    align-items:start;
                    padding:10px 0;
                    border-top:1px solid rgba(226,232,240,.78);
                }}
                .inputs-donut-insight-row:first-of-type {{
                    border-top:none;
                    padding-top:0;
                }}
                .inputs-donut-insight-rank {{
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    min-height:34px;
                    border-radius:999px;
                    background:#E7EDF3;
                    color:#334155;
                    font-size:13px;
                    font-weight:800;
                }}
                .inputs-donut-insight-name {{
                    font-size:14px;
                    line-height:1.2;
                    color:#0f172a;
                    font-weight:800;
                    margin-bottom:2px;
                }}
                .inputs-donut-insight-sub {{
                    font-size:12px;
                    line-height:1.35;
                    color:#64748b;
                }}
                </style>
                <div class="inputs-donut-insight-card">
                  <div class="inputs-donut-insight-kicker">Lectura de composición</div>
                  <div class="inputs-donut-insight-title">El frente se concentra en pocos componentes dominantes</div>
                  <div class="inputs-donut-insight-metric">
                    <div class="inputs-donut-insight-value">{concentration_top5:.1f}%</div>
                    <div class="inputs-donut-insight-note">Participación acumulada del top 5 del frente seleccionado.</div>
                  </div>
                  {''.join(summary_rows)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_inputs_item_kpi_cards(tabla_show, item_col, selected_focus)


def render_inputs_item_kpi_cards(tabla_show: pd.DataFrame, item_col: str, selected_focus: str | None = None):
    top_1 = tabla_show.iloc[0]
    top_2 = tabla_show.iloc[1] if len(tabla_show) > 1 else None
    concentration = float(tabla_show.head(3)["% del total"].sum() or 0.0)
    accent_color = FIN_PALETTE_SM.get(str(selected_focus or "").strip(), "#7B8794")
    top_2_html = ""
    if top_2 is not None:
        top_2_html = (
            f"""
            <div class="inputs-item-summary-line">
              <span class="inputs-item-summary-label">Segundo componente</span>
              <span class="inputs-item-summary-text">{html.escape(str(top_2[item_col]))} · {format_clp(float(top_2['Monto']))}</span>
            </div>
            """
        )

    ranking_rows = []
    for rank, (_, rec) in enumerate(tabla_show.iterrows(), start=1):
        share = float(rec["% del total"])
        row_class = " inputs-item-board-top" if rank <= 3 else ""
        items_count = int(rec["Items"])
        item_label = "registro" if items_count == 1 else "registros"
        ranking_rows.append(
            f"""
            <div class="inputs-item-board-row{row_class}">
              <div class="inputs-item-board-rank">
                <span class="inputs-item-rank">#{rank}</span>
              </div>
              <div class="inputs-item-board-main">
                <div class="inputs-item-name-main">{html.escape(str(rec[item_col]))}</div>
                <div class="inputs-item-name-sub">{items_count} {item_label} · promedio {format_clp(float(rec["Promedio"]))}</div>
                <div class="inputs-item-share-wrap">
                  <div class="inputs-item-share-bar">
                    <span class="inputs-item-share-fill" style="width:{min(max(share, 0.0), 100.0):.2f}%; background:{accent_color};"></span>
                  </div>
                  <span class="inputs-item-share-label">{share:.2f}% del frente</span>
                </div>
              </div>
              <div class="inputs-item-board-amount">
                <div class="inputs-item-board-kicker">Monto ejecutado</div>
                <div class="inputs-item-board-value">{format_clp(float(rec["Monto"]))}</div>
                <div class="inputs-item-board-meta">{items_count} ítems</div>
              </div>
            </div>
            """
        )

    board_height = min(220 + len(tabla_show) * 64, 820)
    components.html(
        f"""
        <style>
        html, body {{
            margin:0;
            padding:0;
            font-family:"Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color:#334155;
            background:transparent;
        }}
        .inputs-item-board-wrap {{
            max-height:{board_height}px;
            overflow:auto;
            border:1px solid rgba(148,163,184,.20);
            border-radius:24px;
            background:linear-gradient(180deg,#ffffff 0%, #faf8f5 100%);
            box-shadow:0 10px 28px rgba(15,23,42,.05);
            margin-top:10px;
            padding:14px;
        }}
        .inputs-item-summary {{
            display:grid;
            grid-template-columns:minmax(0,1.35fr) minmax(220px,.75fr);
            gap:14px;
            padding:4px 4px 14px 4px;
            border-bottom:1px solid rgba(226,232,240,.85);
            margin-bottom:14px;
        }}
        .inputs-item-summary-title {{
            font-size:17px;
            font-weight:800;
            color:#0f172a;
            line-height:1.15;
            margin:0 0 8px 0;
            font-family:inherit;
        }}
        .inputs-item-summary-line {{
            display:flex;
            flex-wrap:wrap;
            gap:6px;
            margin-bottom:4px;
            font-size:13px;
            line-height:1.45;
            color:#475569;
            font-family:inherit;
        }}
        .inputs-item-summary-label {{
            color:#64748B;
            font-weight:700;
        }}
        .inputs-item-summary-text {{
            color:#334155;
            font-weight:600;
        }}
        .inputs-item-summary-kpis {{
            display:grid;
            grid-template-columns:1fr;
            gap:10px;
        }}
        .inputs-item-summary-kpi {{
            border-radius:16px;
            padding:12px 14px;
            border:1px solid rgba(226,232,240,.9);
            background:rgba(255,255,255,.88);
        }}
        .inputs-item-summary-kicker {{
            font-size:11px;
            text-transform:uppercase;
            letter-spacing:.08em;
            color:#64748B;
            font-weight:700;
            margin-bottom:4px;
            font-family:inherit;
        }}
        .inputs-item-summary-value {{
            font-size:22px;
            line-height:1.05;
            font-weight:900;
            color:#0f172a;
            font-family:inherit;
        }}
        .inputs-item-summary-note {{
            font-size:12px;
            line-height:1.35;
            color:#64748B;
            margin-top:4px;
            font-family:inherit;
        }}
        .inputs-item-board-row {{
            display:grid;
            grid-template-columns:72px minmax(0,1fr) minmax(180px,240px);
            gap:16px;
            align-items:center;
            padding:14px 16px;
            border-radius:16px;
            background:rgba(255,255,255,.84);
            border:1px solid rgba(226,232,240,.90);
            margin-bottom:8px;
        }}
        .inputs-item-board-row:last-child {{
            margin-bottom:0;
        }}
        .inputs-item-board-top {{
            background:linear-gradient(90deg, color-mix(in srgb, {accent_color} 14%, white) 0%, rgba(255,255,255,.98) 34%);
            border-color:color-mix(in srgb, {accent_color} 26%, white);
        }}
        .inputs-item-board-rank {{
            display:flex;
            justify-content:center;
        }}
        .inputs-item-rank {{
            display:inline-flex;
            min-width:48px;
            justify-content:center;
            padding:8px 12px;
            border-radius:999px;
            background:#E7EDF3;
            color:#334155;
            font-weight:800;
            font-family:inherit;
        }}
        .inputs-item-name-main {{
            font-size:16px;
            font-weight:800;
            color:#0f172a;
            line-height:1.25;
            font-family:inherit;
        }}
        .inputs-item-name-sub {{
            margin-top:3px;
            font-size:12px;
            color:#64748B;
            font-weight:700;
            font-family:inherit;
        }}
        .inputs-item-share-wrap {{
            display:flex;
            align-items:center;
            gap:10px;
            min-width:180px;
            margin-top:8px;
        }}
        .inputs-item-share-bar {{
            position:relative;
            width:100%;
            min-width:120px;
            height:8px;
            border-radius:999px;
            background:#E5E7EB;
            overflow:hidden;
        }}
        .inputs-item-share-fill {{
            display:block;
            height:100%;
            border-radius:999px;
        }}
        .inputs-item-share-label {{
            min-width:88px;
            text-align:left;
            font-weight:800;
            color:#334155;
            white-space:nowrap;
            font-family:inherit;
        }}
        .inputs-item-board-amount {{
            text-align:right;
        }}
        .inputs-item-board-kicker {{
            font-size:11px;
            text-transform:uppercase;
            letter-spacing:.08em;
            color:#94A3B8;
            font-weight:700;
            margin-bottom:4px;
            font-family:inherit;
        }}
        .inputs-item-board-value {{
            font-size:18px;
            font-weight:900;
            color:#0f172a;
            line-height:1.08;
            white-space:nowrap;
            font-family:inherit;
        }}
        .inputs-item-board-meta {{
            margin-top:4px;
            font-size:12px;
            font-weight:700;
            color:#64748B;
            font-family:inherit;
        }}
        @media (max-width:920px) {{
            .inputs-item-summary {{
                grid-template-columns:1fr;
            }}
            .inputs-item-board-row {{
                grid-template-columns:1fr;
                gap:10px;
            }}
            .inputs-item-board-rank {{
                justify-content:flex-start;
            }}
            .inputs-item-board-amount {{
                text-align:left;
            }}
            .inputs-item-share-wrap {{
                min-width:120px;
                gap:8px;
            }}
        }}
        </style>
        <div class="inputs-item-board-wrap">
          <div class="inputs-item-summary">
            <div>
              <div class="inputs-item-summary-title">Lectura del frente seleccionado</div>
              <div class="inputs-item-summary-line">
                <span class="inputs-item-summary-label">Mayor componente</span>
                <span class="inputs-item-summary-text">{html.escape(str(top_1[item_col]))} · {format_clp(float(top_1['Monto']))}</span>
              </div>
              {top_2_html}
            </div>
            <div class="inputs-item-summary-kpis">
              <div class="inputs-item-summary-kpi">
                <div class="inputs-item-summary-kicker">Concentración top 3</div>
                <div class="inputs-item-summary-value">{concentration:.2f}%</div>
                <div class="inputs-item-summary-note">Participación acumulada del frente analizado.</div>
              </div>
            </div>
          </div>
          {''.join(ranking_rows)}
        </div>
        """,
        height=board_height + 32,
        scrolling=True,
    )


def render_inputs_factor_chart(df_in: pd.DataFrame):
    if "Factor de costo" not in df_in.columns or "Suministro / montaje" not in df_in.columns:
        return
    fac_cat = (
        df_in.copy()
        .assign(
            Factor=df_in["Factor de costo"].fillna("Sin clasificar").astype(str).str.strip(),
            Categoria=df_in["Suministro / montaje"].fillna("(Sin categoría)").astype(str).str.strip(),
            Monto_num=df_in["Monto"],
            PrecioEsc=df_in["Precio final ec esc"] if "Precio final ec esc" in df_in.columns else np.nan,
        )
    )
    fac_cat = fac_cat[fac_cat["Factor"].str.lower() != "sin clasificar"].copy()
    fac_cat["Categoria"] = fac_cat["Categoria"].replace({"Suministro/montaje": "Montaje", "I + D": "I+D", "i+d": "I+D"})
    if fac_cat.empty:
        return

    agg_fc = (
        fac_cat.groupby(["Factor", "Categoria"], as_index=False)
        .agg(Monto=("Monto_num", "sum"), PrecioEsc=("PrecioEsc", "sum"), Items=("Monto_num", "count"))
    )
    if agg_fc.empty:
        return

    tot_por_factor = agg_fc.groupby("Factor")["Monto"].transform("sum")
    agg_fc["% dentro del Factor"] = np.where(tot_por_factor > 0, agg_fc["Monto"] / tot_por_factor * 100.0, 0.0)
    agg_fc["%_esc"] = np.where(agg_fc["Monto"] > 0, agg_fc["PrecioEsc"] / agg_fc["Monto"] * 100.0, np.nan)

    orden_factor = ["Necesario", "Evitable"]
    orden_cat = ["Suministro", "I+D", "Montaje"]
    agg_fc["__of"] = agg_fc["Factor"].apply(lambda x: orden_factor.index(x) if x in orden_factor else 999)
    agg_fc["__oc"] = agg_fc["Categoria"].apply(lambda x: orden_cat.index(x) if x in orden_cat else 999)
    agg_fc = agg_fc.sort_values(["__of", "__oc"]).drop(columns=["__of", "__oc"])
    agg_fc["Monto_MM"] = agg_fc["Monto"] / 1_000_000
    agg_fc["label"] = agg_fc.apply(lambda r: f"{r['Monto_MM']:.1f} MM · {float(r['% dentro del Factor']):.1f}%", axis=1)

    st.markdown(
        '<div class="eng-body-title" style="font-size:20px;font-weight:800;color:#0f172a;margin:0 0 6px 0;">Eficiencia del CAPEX Ejecutado</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:13px;font-weight:400;color:#64748b;margin:0 0 12px 0;">Separación entre gasto estructural necesario para replicar el piloto y gasto prescindible o no recurrente.</div>',
        unsafe_allow_html=True,
    )
    fig_fc = px.bar(
        agg_fc,
        x="Monto_MM",
        y="Factor",
        orientation="h",
        color="Categoria",
        color_discrete_map=FIN_PALETTE_SM,
        text="label",
    )
    fig_fc.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=12, color="#1f2937", family="Source Sans Pro, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"),
        customdata=np.stack([agg_fc["% dentro del Factor"], agg_fc["%_esc"], agg_fc["Items"]], axis=-1),
        hovertemplate=(
            "<b>%{y}</b> · %{trace.name}<br>"
            "Monto seg.: %{x:.1f} MM CLP<br>"
            "Participación en Factor: %{customdata[0]:.2f}%<br>"
            "%_esc seg.: %{customdata[1]:.2f}%<br>"
            "Ítems seg.: %{customdata[2]}<extra></extra>"
        ),
        marker_line_width=0,
    )
    fig_fc.update_layout(
        barmode="stack",
        margin=dict(l=130, r=34, t=26, b=56),
        height=330,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.52,
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            font=dict(size=11, color="#475569"),
        ),
    )
    apply_engineering_chart_typography(fig_fc, title_size=20, body_size=12, tick_size=11, legend_size=11)
    fig_fc.update_xaxes(
        title="Monto (MM CLP)",
        ticksuffix=" MM",
        gridcolor="rgba(148,163,184,0.16)",
        zeroline=False,
        tickfont=dict(size=11, color="#64748b"),
        title_font=dict(size=12, color="#64748b"),
    )
    fig_fc.update_yaxes(
        title=None,
        showgrid=False,
        tickfont=dict(size=13, color="#334155"),
        categoryorder="array",
        categoryarray=["Evitable", "Necesario"],
    )
    st.plotly_chart(fig_fc, use_container_width=True)


def gantt_infer_piloto(row):
    val = str(row.get("Piloto", "")).strip()
    if val:
        return val
    texto = " ".join([
        str(row.get("Fase", "")),
        str(row.get("Línea", "")),
        str(row.get("Tarea / Entregable", "")),
        str(row.get("Método", "")),
    ]).lower()
    if "55" in texto or "55kw" in texto or "55 k" in texto:
        return "Piloto 55 kW"
    return "Piloto 10 kW"


def gantt_normalize_linea(row: pd.Series) -> str:
    linea = str(row.get("Línea", "")).strip()
    if not linea:
        return ""
    if linea.lower() != "acople":
        return linea

    task = str(row.get("Tarea / Entregable", "")).strip().lower()
    texto = " ".join(
        [
            task,
            str(row.get("Método", "")).strip().lower(),
            str(row.get("Ubicación", "")).strip().lower(),
        ]
    )
    # Separa la línea antigua "Acople" en la taxonomía actual del archivo.
    if any(token in texto for token in ("viga-aspa", "vigas- aspas", "hexagonal", "circular", "extremo", "aspa")):
        return "Acople Externo"
    return "Acople Central"


def gantt_process_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "ID" in df.columns:
        df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    if "Línea" in df.columns:
        df["Línea"] = df.apply(gantt_normalize_linea, axis=1)
    for col in [GANTT_DATE_COL_START, GANTT_DATE_COL_END_PLAN, GANTT_DATE_COL_END_REAL]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            df[col] = pd.NaT
    if "%" in df.columns:
        df["%"] = pd.to_numeric(df["%"], errors="coerce")
        try:
            max_val = df["%"].max()
            if pd.notna(max_val) and max_val <= 1:
                df["%"] = df["%"] * 100
        except Exception:
            pass
        if "Estado" in df.columns:
            mask_done = df["Estado"].astype(str).str.contains("complet", case=False, na=False) & df["%"].isna()
            df.loc[mask_done, "%"] = 100
    df["Piloto"] = df.apply(gantt_infer_piloto, axis=1)
    return df


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_project_gantt_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df = read_remote_csv(url, refresh_nonce=refresh_nonce + GANTT_PROJECT_SOURCE_VERSION, encoding="utf-8-sig")
    df.columns = [GANTT_COLUMN_ALIASES.get(str(c).strip(), str(c).strip()) for c in df.columns]
    return gantt_process_df(df)


def build_gantt_phase_color_map(df: pd.DataFrame) -> dict[str, str]:
    if "Fase" not in df.columns:
        return {}
    fases = sorted(
        {
            str(val).strip()
            for val in df["Fase"].astype(str).tolist()
            if str(val).strip() and str(val).strip().lower() not in {"nan", "none"}
        }
    )
    return {fase: PX_COLORS[idx % len(PX_COLORS)] for idx, fase in enumerate(fases)}


def build_gantt_line_color_map(df: pd.DataFrame) -> dict[str, str]:
    if "Línea" not in df.columns:
        return {}
    preferred_colors = {
        "Acople Central": "#4fb5ad",
        "Acople Externo": "#0b3358",
        "Freno Mecánico": "#f5a623",
        "Freno Mecanico": "#f5a623",
    }
    lineas = sorted(
        {
            str(val).strip()
            for val in df["Línea"].astype(str).tolist()
            if str(val).strip() and str(val).strip().lower() not in {"nan", "none"}
        }
    )
    fallback = ["#4fb5ad", "#0b3358", "#f5a623", "#ef3b2d", "#45a16a", "#8b3ff4", "#64748b"]
    return {linea: preferred_colors.get(linea, fallback[idx % len(fallback)]) for idx, linea in enumerate(lineas)}


def format_gantt_task_label(label: str, max_chars: int = 42, max_lines: int = 2) -> str:
    clean = " ".join(str(label).split()).strip()
    if not clean:
        return ""
    wrapped = textwrap.wrap(clean, width=max_chars, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) <= max_lines:
        return "<br>".join(html.escape(part) for part in wrapped)
    clipped = wrapped[:max_lines]
    clipped[-1] = clipped[-1].rstrip(" .,;:") + "…"
    return "<br>".join(html.escape(part) for part in clipped)


def _gantt_status_color(status: str) -> str:
    status_l = str(status or "").strip().lower()
    if "curso" in status_l:
        return "#ef3b2d"
    if "complet" in status_l:
        return "#45a16a"
    if "plan" in status_l:
        return "#a7b1bd"
    if "pend" in status_l:
        return "#f5a623"
    if "recurrente" in status_l:
        return "#0b3358"
    return "#64748b"


def _gantt_summary(df: pd.DataFrame, date_mode: str = "Real") -> dict[str, object]:
    dfk = df.copy()
    dfk["_start"] = pd.to_datetime(dfk.get(GANTT_DATE_COL_START), errors="coerce")
    dfk["_end_plan"] = pd.to_datetime(dfk.get(GANTT_DATE_COL_END_PLAN), errors="coerce")
    dfk["_end_real"] = pd.to_datetime(dfk.get(GANTT_DATE_COL_END_REAL), errors="coerce")
    dfk["_start"] = dfk["_start"].fillna(dfk["_end_real"]).fillna(dfk["_end_plan"])
    dfk["_end"] = dfk["_end_real"] if date_mode == "Real" else dfk["_end_plan"]
    dfk["_end"] = dfk["_end"].fillna(dfk["_end_plan"]).fillna(dfk["_end_real"]).fillna(dfk["_start"])
    bad = dfk["_end"] <= dfk["_start"]
    dfk.loc[bad, "_end"] = dfk.loc[bad, "_start"] + pd.Timedelta(days=1)
    dfk = dfk[dfk["_start"].notna() & dfk["_end"].notna()].copy()

    if dfk.empty:
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "overdue_tasks": 0,
            "due_soon_tasks": 0,
            "active_lines": 0,
            "avg_duration": 0,
            "progress_pct": 0,
            "delay_value": "0 d",
            "delay_note": "Sin brecha positiva entre fin plan y fin real",
        }

    today_ts = pd.Timestamp.today().normalize()
    estado = dfk["Estado"].astype(str) if "Estado" in dfk.columns else pd.Series("", index=dfk.index)
    completed_mask = estado.str.contains("complet", case=False, na=False)
    completed_tasks = int(completed_mask.sum())
    in_progress_tasks = int(estado.str.contains("curso", case=False, na=False).sum())
    overdue_tasks = int(((dfk["_end"] < today_ts) & ~completed_mask).sum())
    due_soon_tasks = int(((dfk["_end"] >= today_ts) & (dfk["_end"] <= today_ts + pd.Timedelta(days=5)) & ~completed_mask).sum())
    active_lines = int(
        dfk["Línea"].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan}).dropna().nunique()
    ) if "Línea" in dfk.columns else 0
    avg_duration = int(round(((dfk["_end"] - dfk["_start"]).dt.days.clip(lower=1)).mean()))
    total_tasks = int(len(dfk))
    progress_pct = int(round(100 * completed_tasks / total_tasks)) if total_tasks else 0
    dfk["_delay_days"] = (dfk["_end_real"] - dfk["_end_plan"]).dt.days
    delay_value = "0 d"
    delay_note = "Sin brecha positiva entre fin plan y fin real"
    atraso_df = dfk[dfk["_delay_days"].fillna(0) > 0].copy()
    if not atraso_df.empty:
        atraso_row = atraso_df.sort_values(["_delay_days", "_end_real"], ascending=[False, False]).iloc[0]
        delay_value = f"{int(atraso_row['_delay_days'])} d"
        atraso_task_label = str(atraso_row.get("Tarea / Entregable", "")).strip() or "Tarea sin nombre"
        delay_note = f"Mayor atraso vs plan: {atraso_task_label[:58]}"

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "overdue_tasks": overdue_tasks,
        "due_soon_tasks": due_soon_tasks,
        "active_lines": active_lines,
        "avg_duration": avg_duration,
        "progress_pct": progress_pct,
        "delay_value": delay_value,
        "delay_note": delay_note,
    }


def render_inputs_gantt_design_css() -> None:
    st.markdown(
        """
        <style>
        .gantt-shell, .gantt-panel, .gantt-chart-card{
            border:1px solid rgba(226,232,240,.95);
            border-radius:18px;
            background:rgba(255,255,255,.96);
            box-shadow:0 12px 30px rgba(15,23,42,.07);
        }
        .gantt-shell{
            padding:14px 15px 13px 15px;
            margin:2px 0 13px 0;
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:14px;
        }
        .gantt-title-wrap{display:flex;align-items:center;gap:14px;min-width:0;}
        .gantt-title-icon{
            width:50px;height:50px;border-radius:14px;
            display:flex;align-items:center;justify-content:center;
            border:1px solid rgba(203,213,225,.78);
            color:#0b1328;background:#fbfdff;flex:0 0 auto;
        }
        .gantt-title{
            margin:0;color:#091329;font-size:24px;line-height:1.08;
            font-weight:900;letter-spacing:0;
        }
        .gantt-subtitle{margin:6px 0 0 0;color:#748198;font-size:12px;line-height:1.45;}
        .gantt-progress{
            min-width:266px;border:1px solid rgba(226,232,240,.95);border-radius:14px;
            padding:11px 13px;display:grid;grid-template-columns:46px 1fr 1px 1.1fr;
            gap:11px;align-items:center;background:#fff;
        }
        .gantt-donut{
            width:40px;height:40px;border-radius:50%;
            background:conic-gradient(#0f9d8a var(--pct), #e5e9ee 0);
            position:relative;
        }
        .gantt-donut::after{
            content:"";position:absolute;inset:6px;border-radius:50%;background:#fff;
        }
        .gantt-progress-k{font-size:10px;color:#0f172a;margin-bottom:3px;}
        .gantt-progress-v{font-size:24px;line-height:1;font-weight:900;color:#0f9485;}
        .gantt-divider{height:38px;background:#e5e7eb;}
        .gantt-alert{display:flex;align-items:center;gap:6px;color:#0f172a;font-size:10px;margin:3px 0;}
        .gantt-alert-dot{
            width:11px;height:11px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;
            color:white;font-size:8px;font-weight:900;background:#ef3b2d;
        }
        .gantt-alert-dot.soon{background:#ff7a1a;}
        .gantt-panel{padding:13px 16px 14px 16px;margin:0 0 14px 0;}
        .gantt-panel-title{
            color:#52657f;font-size:11px;font-weight:900;letter-spacing:.04em;text-transform:uppercase;
            margin:0 0 10px 0;
        }
        .gantt-kpi{
            border-radius:13px;padding:16px 13px 13px 13px;min-height:120px;
            background:linear-gradient(180deg,#ffffff 0%,#fbfcfe 100%);
            border:1px solid rgba(226,232,240,.95);
            box-shadow:0 10px 22px rgba(15,23,42,.06);
            border-top:4px solid var(--accent);
        }
        .gantt-kpi-top{display:flex;gap:11px;align-items:flex-start;margin-bottom:11px;}
        .gantt-kpi-ico{
            width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;
            background:color-mix(in srgb, var(--accent) 14%, #ffffff);
            color:var(--accent);font-size:22px;font-weight:800;flex:0 0 auto;
        }
        .gantt-kpi-label{font-size:8.5px;font-weight:900;letter-spacing:.04em;text-transform:uppercase;color:#16213a;margin-bottom:6px;}
        .gantt-kpi-value{font-size:22px;font-weight:900;line-height:1;color:#071125;}
        .gantt-kpi-note{font-size:11px;line-height:1.38;color:#0f172a;margin-top:8px;}
        .gantt-chart-card{padding:10px 11px 11px 11px;margin-top:13px;}
        .gantt-chart-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 8px 0;}
        .gantt-chart-title{font-size:15px;font-weight:900;color:#0f172a;margin:0;}
        .gantt-mini-legend{display:flex;gap:18px;align-items:center;justify-content:flex-end;flex-wrap:wrap;font-size:12px;color:#0f172a;}
        .gantt-mini-legend span{display:inline-flex;align-items:center;gap:7px;}
        .gantt-swatch{width:17px;height:9px;border-radius:2px;display:inline-block;}
        .gantt-toolbar{
            display:grid;grid-template-columns:1.4fr 1fr 1.4fr;align-items:center;gap:12px;
            margin:0 0 10px 0;
        }
        .gantt-chip-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0;}
        .gantt-chip{
            display:inline-flex;align-items:center;gap:6px;padding:6px 13px;border-radius:999px;
            background:#fbfdff;border:1px solid rgba(203,213,225,.9);font-size:11px;font-weight:800;color:#102039;
        }
        .gantt-chip-dot{width:9px;height:9px;border-radius:50%;display:inline-block;background:#94a3b8;flex:0 0 auto;}
        .gantt-range-row{display:flex;align-items:center;justify-content:center;gap:6px;}
        .gantt-range-btn{
            height:22px;padding:0 7px;border-radius:4px;border:1px solid #d7dee9;background:#fff;
            color:#52657f;font-size:10px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;
        }
        .gantt-range-btn.active{border-color:#38b2a6;color:#0f9485;background:#ecfffc;}
        .gantt-custom-legend{display:flex;gap:21px;align-items:center;justify-content:flex-end;font-size:10px;color:#0f172a;}
        .gantt-custom-legend span{display:inline-flex;align-items:center;gap:6px;white-space:nowrap;}
        .gantt-custom-wrap{
            border:1px solid #dde6f1;border-radius:10px;background:#fff;overflow:hidden;
            padding:13px 14px 18px 14px;
        }
        .gantt-custom-scroll{
            overflow-x:auto;
            overflow-y:visible;
            padding-bottom:2px;
        }
        .gantt-custom-title{font-size:12px;font-weight:900;color:#0f172a;margin:0 0 8px 0;}
        .gantt-grid{
            display:grid;grid-template-columns:336px minmax(608px, 1fr);position:relative;
            border-top:1px solid #dde6f1;
            min-width:944px;
        }
        .gantt-left-head{
            height:46px;border-right:1px solid #dde6f1;border-bottom:1px solid #dde6f1;
            display:flex;align-items:center;color:#71819a;font-size:10px;font-weight:900;text-transform:uppercase;
        }
        .gantt-time-head{
            height:46px;position:relative;border-bottom:1px solid #dde6f1;
            background:repeating-linear-gradient(to right, transparent 0, transparent calc(12.5% - 1px), #e5ebf3 calc(12.5% - 1px), #e5ebf3 12.5%);
        }
        .gantt-month-label{
            position:absolute;top:6px;height:14px;text-align:center;color:#71819a;font-size:10px;
            font-weight:900;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:clip;
        }
        .gantt-month-label.edge{transform:translateX(-100%);text-align:right;overflow:visible;}
        .gantt-week-label{position:absolute;bottom:7px;transform:translateX(-50%);color:#0f172a;font-size:10px;font-weight:700;}
        .gantt-task-row{display:contents;}
        .gantt-task-cell{
            min-height:34px;border-right:1px solid #dde6f1;border-bottom:1px solid #e7edf4;
            display:grid;grid-template-columns:16px 1fr;align-items:center;gap:8px;padding:5px 10px 5px 5px;
        }
        .gantt-task-dot{width:9px;height:9px;border-radius:50%;background:#94a3b8;justify-self:center;}
        .gantt-task-label{font-size:10.5px;line-height:1.25;color:#0f172a;font-weight:500;}
        .gantt-bar-cell{
            min-height:34px;position:relative;border-bottom:1px solid #e7edf4;
            background:repeating-linear-gradient(to right, transparent 0, transparent calc(12.5% - 1px), #e5ebf3 calc(12.5% - 1px), #e5ebf3 12.5%);
        }
        .gantt-bar{
            position:absolute;height:9px;top:50%;transform:translateY(-50%);border-radius:999px;
            box-shadow:inset 0 -1px 0 rgba(15,23,42,.10);
        }
        .gantt-bar::before{
            content:"";position:absolute;left:-2px;top:50%;width:6px;height:6px;border-radius:50%;
            transform:translateY(-50%);background:var(--bar-color);border:2px solid #fff;
        }
        .gantt-bar::after{
            content:"";position:absolute;right:-5px;top:50%;width:9px;height:9px;
            transform:translateY(-50%) rotate(45deg);background:var(--bar-color);border:1px solid #fff;
        }
        .gantt-end-date{
            position:absolute;top:50%;transform:translateY(-50%);font-size:10px;color:#334155;font-weight:500;white-space:nowrap;
        }
        .gantt-today-line{
            position:absolute;top:46px;bottom:0;width:0;border-left:1.5px dashed #111827;z-index:3;
        }
        .gantt-today-label{
            position:absolute;top:38px;transform:translateX(-50%);z-index:4;
            background:#374151;color:#fff;border-radius:4px;padding:5px 7px;font-size:10px;font-weight:800;
        }
        div[data-testid="stSelectbox"] label p, div[data-testid="stRadio"] label p{
            font-size:13px!important;color:#0f172a!important;font-weight:700!important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
            min-height:37px;border-radius:7px;border-color:#d5dde8;background:#fbfdff;
        }
        div[role="radiogroup"]{gap:18px;}
        @media (max-width: 980px){
            .gantt-shell{align-items:flex-start;flex-direction:column;}
            .gantt-progress{min-width:0;width:100%;grid-template-columns:58px 1fr;}
            .gantt-divider{display:none;}
            .gantt-title{font-size:19px;}
            .gantt-toolbar{grid-template-columns:1fr;}
            .gantt-custom-legend{justify-content:flex-start;}
            .gantt-grid{grid-template-columns:264px minmax(560px,1fr);}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_inputs_gantt_header(df: pd.DataFrame, date_mode: str = "Real") -> None:
    summary = _gantt_summary(df, date_mode=date_mode)
    progress = int(summary["progress_pct"])
    st.markdown(
        f"""
        <div class="gantt-shell">
          <div class="gantt-title-wrap">
            <div class="gantt-title-icon">
              <svg width="31" height="31" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z"/>
              </svg>
            </div>
            <div>
              <h2 class="gantt-title">Cronograma de Ejecución y Validación</h2>
              <p class="gantt-subtitle">Vista integrada del cronograma del proyecto antes del análisis financiero por categorías.</p>
            </div>
          </div>
          <div class="gantt-progress">
            <div class="gantt-donut" style="--pct:{progress}%;"></div>
            <div>
              <div class="gantt-progress-k">Avance del bloque</div>
              <div class="gantt-progress-v">{progress}%</div>
            </div>
            <div class="gantt-divider"></div>
            <div>
              <div class="gantt-alert"><span class="gantt-alert-dot">!</span><b>{int(summary["overdue_tasks"])}</b> tareas atrasadas</div>
              <div class="gantt-alert"><span class="gantt-alert-dot soon">!</span><b>{int(summary["due_soon_tasks"])}</b> vence pronto</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_inputs_gantt_kpis(df: pd.DataFrame, date_mode: str = "Real") -> None:
    if df.empty:
        return
    summary = _gantt_summary(df, date_mode=date_mode)

    cards = [
        ("ACTIVIDADES DEL BLOQUE", str(summary["total_tasks"]), "Filas visibles en el cronograma", "#0f9d8a", "☷"),
        ("AVANCE REAL", f'{summary["completed_tasks"]} · {summary["progress_pct"]}%', "Cierre del bloque filtrado", "#16a34a", "◔"),
        ("ACTIVIDADES CRÍTICAS", str(summary["overdue_tasks"]), "No completadas con fecha vencida", "#f97316", "◷"),
        ("PRÓXIMOS HITOS", str(summary["due_soon_tasks"]), "Tareas próximas a vencer (< 5 días)", "#8b3ff4", "▣"),
        ("BRECHA CRÍTICA", str(summary["delay_value"]), str(summary["delay_note"]), "#ef2424", "△"),
        ("PLAZO PROMEDIO", f'{summary["avg_duration"]} d', "Duración promedio por tarea", "#1267d8", "◔"),
    ]
    if summary["active_lines"]:
        cards.append(("FRENTES ACTIVOS", str(summary["active_lines"]), "Subfrentes activos del bloque", "#475569", "⌘"))

    cols = st.columns(len(cards))
    for col, (label, value, note, accent, icon) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="gantt-kpi" style="--accent:{accent};">
                    <div class="gantt-kpi-top">
                        <div class="gantt-kpi-ico">{html.escape(icon)}</div>
                        <div>
                            <div class="gantt-kpi-label">{html.escape(label)}</div>
                            <div class="gantt-kpi-value">{html.escape(value)}</div>
                        </div>
                    </div>
                    <div class="gantt-kpi-note">{html.escape(note)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_inputs_gantt_figure(
    df: pd.DataFrame,
    date_mode: str = "Real",
    color_by: str = "Estado",
    color_y_labels_by_phase: bool = False,
    color_y_labels_by_line: bool = False,
):
    dfp = df.copy()
    dfp["_start"] = pd.to_datetime(dfp.get(GANTT_DATE_COL_START), errors="coerce")
    dfp["_end_plan"] = pd.to_datetime(dfp.get(GANTT_DATE_COL_END_PLAN), errors="coerce")
    dfp["_end_real"] = pd.to_datetime(dfp.get(GANTT_DATE_COL_END_REAL), errors="coerce")

    dfp["_start"] = dfp["_start"].fillna(dfp["_end_real"]).fillna(dfp["_end_plan"])
    dfp["_end"] = dfp["_end_real"] if date_mode == "Real" else dfp["_end_plan"]
    dfp["_end"] = dfp["_end"].fillna(dfp["_end_plan"]).fillna(dfp["_end_real"]).fillna(dfp["_start"])
    bad = dfp["_end"] <= dfp["_start"]
    dfp.loc[bad, "_end"] = dfp.loc[bad, "_start"] + pd.Timedelta(days=1)
    dfp = dfp[dfp["_start"].notna() & dfp["_end"].notna()].copy()
    if dfp.empty:
        return go.Figure()

    dfp = dfp.sort_values(["_start", "_end", "ID"], ascending=[False, False, True])
    dfp["_task_label"] = dfp["Tarea / Entregable"].astype(str)
    y_labels = pd.unique(dfp["_task_label"].astype(str))
    display_label_map = {label: format_gantt_task_label(label) for label in y_labels}
    max_len = max((max((len(part) for part in str(display_label_map[label]).split("<br>")), default=12)) for label in y_labels) if len(y_labels) else 12
    rows = len(y_labels)
    left_margin = min(84 + max_len * 8, 500)
    # Altura realmente responsiva para que al filtrar estados no queden huecos verticales.
    height_px = min(max(260, 110 + 36 * rows), 1200)

    color_arg = color_by if color_by in dfp.columns else "Estado"
    color_map = None
    if color_by == "Estado" and "Estado" in dfp.columns:
        color_map = {val: _gantt_status_color(val) for val in dfp["Estado"].dropna().unique()}
    elif color_by == "Línea" and "Línea" in dfp.columns:
        color_map = build_gantt_line_color_map(dfp)
    elif color_by == "Piloto" and "Piloto" in dfp.columns:
        pilotos = dfp["Piloto"].dropna().unique()
        color_map = {p: PX_COLORS[i % len(PX_COLORS)] for i, p in enumerate(pilotos)}

    phase_color_map = build_gantt_phase_color_map(dfp)
    line_color_map = build_gantt_line_color_map(dfp)

    safe_pct = pd.to_numeric(dfp.get("%", 0), errors="coerce").fillna(0).astype(float)
    fig = go.Figure()
    shown_legends = set()
    for idx, row in dfp.iterrows():
        legend_name = str(row.get(color_arg, "")) if color_arg in row.index else ""
        legend_name = legend_name.strip() or "Sin categoría"
        color_value = color_map.get(legend_name, "#64748b") if color_map else "#64748b"
        estado_color_value = _gantt_status_color(str(row.get("Estado", ""))) if "Estado" in row.index else "#64748b"
        duration_days = max(int((row["_end"] - row["_start"]).days), 1)
        completion_pct = float(safe_pct.loc[idx]) if idx in safe_pct.index else 0.0
        task_name = str(row.get("Tarea / Entregable", ""))
        task_label = str(row.get("_task_label", task_name))
        phase_name = str(row.get("Fase", ""))
        line_name = str(row.get("Línea", ""))
        state_name = str(row.get("Estado", ""))
        task_id = row.get("ID", "")
        end_label = row["_end"].strftime("%d-%m-%Y") if pd.notna(row["_end"]) else ""

        fig.add_trace(
            go.Scatter(
                x=[row["_start"], row["_end"]],
                y=[task_label, task_label],
                mode="lines+markers+text",
                name=legend_name,
                legendgroup=legend_name,
                showlegend=legend_name not in shown_legends,
                line=dict(color=color_value, width=10),
                marker=dict(
                    size=[7, 12],
                    color=[color_value, color_value],
                    symbol=["circle", "diamond"],
                    line=dict(color=estado_color_value if color_by == "Línea" else "white", width=1.6 if color_by == "Línea" else 1.4),
                ),
                text=["", end_label],
                textposition="middle right",
                customdata=[[phase_name, state_name, task_id, duration_days, completion_pct, task_name, line_name]] * 2,
                hovertemplate="<b>%{y}</b><br>"
                              "Estado: %{customdata[1]} · Línea: %{customdata[6]} · ID: %{customdata[2]}<br>"
                              "Inicio: %{x|%Y-%m-%d}<br>"
                              "Fase: %{customdata[0]}<br>"
                              "Tarea: %{customdata[5]}<extra>Duración: %{customdata[3]} días · Avance: %{customdata[4]:.0f}%</extra>",
            )
        )
        shown_legends.add(legend_name)

    today_ts = pd.Timestamp.today().normalize()
    today_iso = today_ts.strftime("%Y-%m-%d")
    fig.add_shape(
        type="line",
        x0=today_iso, x1=today_iso, y0=0, y1=1, xref="x", yref="paper",
        line=dict(dash="dot", width=2, color="#1C1C1E"),
    )
    fig.add_annotation(
        x=today_iso, y=1.045, xref="x", yref="paper",
        text="Hoy", showarrow=False,
        font=dict(size=12, color="#ffffff"),
        bgcolor="#374151",
        borderpad=5,
    )

    if "Hito (S/N)" in dfp.columns:
        hitos = dfp[dfp["Hito (S/N)"].astype(str).str.upper().eq("S")].copy()
        if not hitos.empty:
            fig.add_trace(
                go.Scatter(
                    x=hitos["_end"],
                    y=hitos["_task_label"],
                    mode="markers",
                    marker=dict(size=10, symbol="diamond", line=dict(width=1, color="#1C1C1E")),
                    name="Hito",
                    hovertext=hitos["Tarea / Entregable"],
                    hoverinfo="text",
                )
            )

    fig.update_xaxes(
        rangeselector=dict(
            x=0.38,
            y=1.16,
            bgcolor="rgba(255,255,255,.96)",
            activecolor="#dff7f3",
            bordercolor="#d7dee9",
            borderwidth=1,
            font=dict(size=12, color="#52657f"),
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(step="year", stepmode="todate", label="YTD"),
                dict(count=1, step="year", stepmode="backward", label="1y"),
                dict(step="all", label="All"),
            ])
        ),
        rangeslider=dict(visible=False),
        showgrid=True,
        gridcolor="rgba(203,213,225,0.55)",
        linecolor="rgba(203,213,225,0.85)",
        tickfont=dict(size=12, color="#0f172a"),
    )
    fig.update_yaxes(
        autorange="reversed",
        automargin=True,
        showticklabels=True,
        gridcolor="rgba(226,232,240,0.95)",
        linecolor="rgba(203,213,225,0.85)",
        tickfont=dict(size=11.5, color="#0f172a"),
    )
    label_color_field = None
    label_color_map = None
    if color_y_labels_by_phase and "Fase" in dfp.columns:
        label_color_field = "Fase"
        label_color_map = phase_color_map
    elif color_y_labels_by_line and "Línea" in dfp.columns:
        label_color_field = "Línea"
        label_color_map = line_color_map

    if label_color_field and label_color_map:
        task_label_map = (
            dfp[["_task_label", label_color_field]]
            .drop_duplicates(subset=["_task_label"])
            .set_index("_task_label")[label_color_field]
            .to_dict()
        )
        fig.update_yaxes(showticklabels=False)
        left_margin = min(max(left_margin + 28, 260), 720)
        for task_label in y_labels:
            label_group_name = str(task_label_map.get(task_label, "")).strip()
            label_color = label_color_map.get(label_group_name, "#667085")
            fig.add_annotation(
                x=0,
                xref="paper",
                xanchor="right",
                xshift=-14,
                y=task_label,
                yref="y",
                text=display_label_map.get(task_label, html.escape(str(task_label))),
                showarrow=False,
                font=dict(size=10.5, color=label_color, family="Arial Black, Arial, sans-serif"),
                align="right",
            )
    fig.update_layout(
        height=height_px,
        margin=dict(l=left_margin, r=22, t=54, b=18),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(size=12, color="#0f172a"),
        ),
        xaxis_title=None,
        yaxis_title=None,
        hoverlabel=dict(bgcolor="#0f172a", font_size=12, font_color="#ffffff"),
    )
    return fig


def render_inputs_gantt_group_legend(color_map: dict[str, str]) -> None:
    if not color_map:
        return
    chips = []
    for label, color in color_map.items():
        chips.append(
            (
                f"<span style='display:inline-flex;align-items:center;gap:8px;padding:6px 10px;"
                f"border-radius:999px;background:#fbfdff;"
                f"border:1px solid rgba(148,163,184,.22);color:#334155;font-weight:700;'>"
                f"<span style='width:10px;height:10px;border-radius:999px;background:{color};"
                f"display:inline-block;box-shadow:0 0 0 2px rgba(255,255,255,.95);'></span>"
                f"{html.escape(label)}</span>"
            )
        )

    st.markdown(
        f"""
        <div style="
            margin: 10px 0 4px 0;
            padding: 8px 12px 2px 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px 12px;
            font-size: 0.92rem;
            line-height: 1.45;
        ">
            {''.join(chips)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_inputs_gantt_custom_chart(
    df: pd.DataFrame,
    date_mode: str,
    legend_color_map: dict[str, str] | None,
    title: str = "Cronograma",
) -> None:
    if df.empty:
        return

    dfc = df.copy()
    dfc["_start"] = pd.to_datetime(dfc.get(GANTT_DATE_COL_START), errors="coerce")
    dfc["_end_plan"] = pd.to_datetime(dfc.get(GANTT_DATE_COL_END_PLAN), errors="coerce")
    dfc["_end_real"] = pd.to_datetime(dfc.get(GANTT_DATE_COL_END_REAL), errors="coerce")
    dfc["_start"] = dfc["_start"].fillna(dfc["_end_real"]).fillna(dfc["_end_plan"])
    dfc["_end"] = dfc["_end_real"] if date_mode == "Real" else dfc["_end_plan"]
    dfc["_end"] = dfc["_end"].fillna(dfc["_end_plan"]).fillna(dfc["_end_real"]).fillna(dfc["_start"])
    bad = dfc["_end"] <= dfc["_start"]
    dfc.loc[bad, "_end"] = dfc.loc[bad, "_start"] + pd.Timedelta(days=1)
    dfc = dfc[dfc["_start"].notna() & dfc["_end"].notna()].copy()
    if dfc.empty:
        return

    today_ts = pd.Timestamp.today().normalize()
    days_since_tuesday = (today_ts.weekday() - 1) % 7
    tick_start = today_ts - pd.Timedelta(days=days_since_tuesday + 35)
    ticks = [tick_start + pd.Timedelta(days=7 * i) for i in range(9)]
    window_start = ticks[0]
    window_end = ticks[-1]
    window_days = max((window_end - window_start).days, 1)

    visible_df = dfc[(dfc["_end"] >= window_start) & (dfc["_start"] <= window_end)].copy()
    if visible_df.empty:
        visible_df = dfc.copy()
    if "ID" in visible_df.columns:
        visible_df = visible_df.sort_values(["ID", "_start", "_end"], ascending=[True, True, True])
    else:
        visible_df = visible_df.sort_values(["_start", "_end"], ascending=[True, True])
    dfc = visible_df.copy()

    def pct(date_value: pd.Timestamp) -> float:
        return max(0.0, min(100.0, ((date_value - window_start).days / window_days) * 100.0))

    month_names = {
        1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
        7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
    }
    month_labels = []
    cursor = pd.Timestamp(window_start.year, window_start.month, 1)
    while cursor <= window_end:
        next_month = cursor + pd.DateOffset(months=1)
        span_start = max(cursor, window_start)
        span_end = min(next_month, window_end + pd.Timedelta(days=1))
        if span_end > span_start:
            left = pct(span_start)
            width = max(0.0, pct(span_end) - left)
            is_edge = span_end >= window_end
            class_name = "gantt-month-label edge" if is_edge and width < 13 else "gantt-month-label"
            label_left = min(98.8, left + width) if "edge" in class_name else left
            label_width = width if "edge" not in class_name else min(18.0, width + 10.0)
            month_labels.append(
                f'<div class="{class_name}" style="left:{label_left:.4f}%;width:{label_width:.4f}%;">{month_names.get(cursor.month, "")} {cursor.year}</div>'
            )
        cursor = next_month

    week_labels = "".join(
        f'<div class="gantt-week-label" style="left:{min(98.6, pct(tick)):.4f}%;">{tick.day:02d}</div>'
        for tick in ticks
    )

    line_color_map = build_gantt_line_color_map(dfc)
    rows_html = []
    for _, row in dfc.iterrows():
        start = max(pd.Timestamp(row["_start"]).normalize(), window_start)
        end = min(pd.Timestamp(row["_end"]).normalize(), window_end)
        if end <= start:
            end = start + pd.Timedelta(days=1)
        left = pct(start)
        width = max(1.5, pct(end) - left)
        end_label = pd.Timestamp(row["_end"]).strftime("%d-%m-%Y")
        task = format_gantt_task_label(str(row.get("Tarea / Entregable", "")), max_chars=43, max_lines=2)
        line_name = str(row.get("Línea", "")).strip()
        line_color = line_color_map.get(line_name, "#64748b")
        bar_color = _gantt_status_color(str(row.get("Estado", "")))
        date_left = min(97.0, left + width + 1.0)
        rows_html.append(
            textwrap.dedent(
                f"""
                <div class="gantt-task-row">
                  <div class="gantt-task-cell">
                    <span class="gantt-task-dot" style="background-color:{line_color};"></span>
                    <div class="gantt-task-label">{task}</div>
                  </div>
                  <div class="gantt-bar-cell">
                    <span class="gantt-bar" style="--bar-color:{bar_color};background:{bar_color};left:{left:.4f}%;width:{width:.4f}%;"></span>
                    <span class="gantt-end-date" style="left:{date_left:.4f}%;">{html.escape(end_label)}</span>
                  </div>
                </div>
                """
            ).strip()
        )

    chip_source = line_color_map or legend_color_map
    chips_html = "".join(
        f'<span class="gantt-chip"><span class="gantt-chip-dot" style="background-color:{color};"></span>{html.escape(label)}</span>'
        for label, color in chip_source.items()
    )
    if not chips_html:
        chips_html = "".join(
            f'<span class="gantt-chip"><span class="gantt-chip-dot" style="background-color:{color};"></span>{html.escape(label)}</span>'
            for label, color in line_color_map.items()
        )

    today_left = pct(today_ts)
    rows_fragment = "\n".join(rows_html)
    chart_html = textwrap.dedent(
        f"""
        <div class="gantt-chart-card">
          <div class="gantt-toolbar">
            <div class="gantt-chip-row">{chips_html}</div>
            <div class="gantt-range-row">
              <span class="gantt-range-btn">1m</span>
              <span class="gantt-range-btn">3m</span>
              <span class="gantt-range-btn">6m</span>
              <span class="gantt-range-btn">YTD</span>
              <span class="gantt-range-btn">1y</span>
              <span class="gantt-range-btn active">All</span>
            </div>
            <div class="gantt-custom-legend">
              <span><i class="gantt-swatch" style="background:#ef3b2d;"></i>En curso</span>
              <span><i class="gantt-swatch" style="background:#45a16a;"></i>Completado</span>
              <span><i class="gantt-swatch" style="background:#a7b1bd;"></i>Plan</span>
            </div>
          </div>
          <div class="gantt-custom-wrap">
            <div class="gantt-custom-title">{html.escape(title)}</div>
            <div class="gantt-custom-scroll">
              <div class="gantt-grid">
                <div class="gantt-left-head">Tarea</div>
                <div class="gantt-time-head">{''.join(month_labels)}{week_labels}</div>
              <div class="gantt-today-label" style="left:calc(336px + (100% - 336px) * {today_left / 100:.6f});">Hoy</div>
              <div class="gantt-today-line" style="left:calc(336px + (100% - 336px) * {today_left / 100:.6f});"></div>
        {rows_fragment}
              </div>
            </div>
          </div>
        </div>
        """
    ).strip()
    st.markdown(chart_html, unsafe_allow_html=True)


def render_inputs_aspas_frp_schedule_chart() -> None:
    try:
        df_ing_schedule = build_ingenieria_piloto_10kw_schedule(
            INGENIERIA_PILOTO_10KW_CSV_URL_DEFAULT,
            refresh_nonce=data_refresh_nonce,
        )
    except Exception as exc:
        st.error(f"No se pudo construir el cronograma diario de ingeniería: {exc}")
        return

    if df_ing_schedule.empty:
        st.info("No hay actividades con fecha válida para construir el cronograma de ingeniería.")
        return

    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:18px 0 10px 0;">Cronograma fabricación ASPAS frp</div>',
        unsafe_allow_html=True,
    )
    tarea_order = (
        df_ing_schedule[["Tarea", "_row_order"]]
        .drop_duplicates()
        .sort_values("_row_order")
        ["Tarea"]
        .tolist()
    )
    fecha_ticks = (
        df_ing_schedule[["Fecha", "Fecha_orden", "Fecha_plot", "Fecha_dt"]]
        .drop_duplicates()
        .sort_values("Fecha_orden")
    )
    month_abbr = {
        1: "ene",
        2: "feb",
        3: "mar",
        4: "abr",
        5: "may",
        6: "jun",
        7: "jul",
        8: "ago",
        9: "sep",
        10: "oct",
        11: "nov",
        12: "dic",
    }
    today_ts = pd.Timestamp.now(tz="America/Santiago")
    today_label = f"{today_ts.day}-{month_abbr.get(today_ts.month, '')}"
    today_x = None
    if "Fecha_dt" in fecha_ticks.columns and fecha_ticks["Fecha_dt"].notna().any():
        today_match = fecha_ticks[fecha_ticks["Fecha_dt"].dt.normalize().eq(today_ts.tz_localize(None).normalize())]
    else:
        today_match = fecha_ticks[fecha_ticks["Fecha"].astype(str).str.lower().eq(today_label)]
    if not today_match.empty:
        today_x = float(today_match.iloc[0]["Fecha_plot"])
    tick_step = max(1, math.ceil(len(fecha_ticks) / 18))
    tick_df = fecha_ticks.iloc[::tick_step].copy()
    pieza_base_color_map = {
        "aspa 1": "#6B4F3A",
        "aspa 2": "#D7605E",
        "aspa 3": "#4F5D6F",
        "conectores": "#B8860B",
        "matriz 1": "#A9A7A4",
        "matriz 2": "#7FA8A4",
    }
    pieza_palette_fallback = ["#7FA8A4", "#D7605E", "#D9A766", "#C98C70", "#A9A7A4", "#4F5D6F"]
    pieza_order_seen = [str(pieza).strip() for pieza in df_ing_schedule["PIEZA"].dropna().drop_duplicates().tolist()]
    pieza_color_map = {}
    for idx, pieza in enumerate(pieza_order_seen):
        pieza_key = pieza.casefold()
        pieza_color_map[pieza] = pieza_base_color_map.get(
            pieza_key,
            pieza_palette_fallback[idx % len(pieza_palette_fallback)],
        )

    kpi_inicio = fecha_ticks.iloc[0]["Fecha"] if not fecha_ticks.empty else "-"
    kpi_termino = fecha_ticks.iloc[-1]["Fecha"] if not fecha_ticks.empty else "-"
    kpi_peak = int(df_ing_schedule.groupby("Fecha_orden").size().max() or 0)
    if "Fecha_dt" in df_ing_schedule.columns and df_ing_schedule["Fecha_dt"].notna().any():
        kpi_dias = int(
            df_ing_schedule.loc[
                df_ing_schedule["Fecha_dt"].dt.normalize().ge(today_ts.tz_localize(None).normalize()),
                "Fecha_dt",
            ].nunique()
            or 0
        )
    else:
        today_order = parse_ingenieria_schedule_date_col(today_label)
        kpi_dias = (
            int(df_ing_schedule.loc[df_ing_schedule["Fecha_orden"] >= today_order, "Fecha_orden"].nunique() or 0)
            if today_order is not None
            else 0
        )
    pro_kpi_cols = st.columns(4)
    with pro_kpi_cols[0]:
        kpi_card("Inicio plan", str(kpi_inicio), "Primera fecha con actividad.", variant="palette_teal", compact=True)
    with pro_kpi_cols[1]:
        kpi_card("Término plan", str(kpi_termino), "Última fecha con actividad.", variant="palette_ochre", compact=True)
    with pro_kpi_cols[2]:
        kpi_card("Máx. tareas/día", f"{kpi_peak}", "Mayor cantidad de celdas activas en una fecha.", variant="palette_coral", compact=True)
    with pro_kpi_cols[3]:
        kpi_card("Días restantes", f"{kpi_dias}", "Fechas con trabajo desde hoy.", variant="palette_slate", compact=True)

    preferred_legend_order = ["Aspa 1", "Aspa 2", "Aspa 3", "Conectores", "matriz 1", "matriz 2"]
    legend_order = [
        pieza for pieza in preferred_legend_order
        if pieza in pieza_order_seen
    ] + [
        pieza for pieza in pieza_order_seen
        if pieza not in preferred_legend_order
    ]
    legend_html = "".join(
        f"""
        <span style="display:inline-flex;align-items:center;gap:8px;margin:0 16px 8px 0;font-size:13.8px;color:#475569;font-weight:600;">
            <span style="width:11px;height:11px;border-radius:999px;background:{pieza_color_map.get(pieza, '#94A3B8')};display:inline-block;border:1px solid rgba(15,23,42,.14);"></span>
            <span>{html.escape(str(pieza))}</span>
        </span>
        """
        for pieza in legend_order
    )

    fig_ing_schedule = go.Figure()

    def hex_to_rgba(hex_color: str, alpha: float) -> str:
        value = str(hex_color).strip().lstrip("#")
        if len(value) != 6:
            return f"rgba(148,163,184,{alpha})"
        r, g, b = int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    for pieza, df_task in df_ing_schedule.groupby("PIEZA", sort=False):
        pieza_name = str(pieza)
        trace_color = pieza_color_map.get(pieza_name, "#94A3B8")
        df_task = df_task.sort_values(["Fecha_orden", "_row_order", "Tarea"])
        fig_ing_schedule.add_trace(
            go.Scatter(
                x=df_task["Fecha_plot"],
                y=df_task["Tarea"],
                mode="lines+markers",
                name=pieza_name,
                legendgroup=pieza_name,
                showlegend=True,
                line=dict(color=hex_to_rgba(trace_color, 0.30), width=0.85),
                marker=dict(size=8, color=trace_color, opacity=0.94, symbol="circle", line=dict(color="white", width=1.15)),
                customdata=df_task[["Fecha", "PIEZA", "Tarea", "Carga", "Inicio_label", "Fin_label"]],
                hovertemplate=(
                    "<b>%{customdata[1]}</b><br>"
                    "%{customdata[2]}<br>"
                    "Fecha: %{customdata[0]}<br>"
                    "Trabajo registrado en la hoja<br>"
                    "Inicio y término: %{customdata[4]} a %{customdata[5]}<extra></extra>"
                ),
            )
        )

    schedule_y_order = list(reversed(tarea_order))
    fig_ing_schedule.update_xaxes(
        tickmode="array",
        tickvals=tick_df["Fecha_plot"],
        ticktext=tick_df["Fecha"],
        title="Fecha",
        showgrid=True,
        gridcolor="rgba(148,163,184,0.12)",
        linecolor="rgba(148,163,184,0.22)",
        ticklen=3,
    )
    fig_ing_schedule.update_yaxes(
        categoryorder="array",
        categoryarray=schedule_y_order,
        tickmode="array",
        tickvals=schedule_y_order,
        ticktext=schedule_y_order,
        title="Tarea",
        automargin=True,
        gridcolor="rgba(148,163,184,0.08)",
    )
    if today_x is not None:
        fig_ing_schedule.add_vline(
            x=today_x,
            line=dict(color="rgba(185,28,28,0.62)", width=1.4, dash="dash"),
            annotation_text="Hoy",
            annotation_position="top",
            annotation_font=dict(size=11, color="#B91C1C"),
        )
    fig_ing_schedule.update_layout(
        height=max(306, min(576, 83 + 15.3 * len(tarea_order))),
        margin=dict(l=10, r=10, t=30, b=28),
        plot_bgcolor="rgba(248,250,252,0.42)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title=dict(text="Pieza"),
            bgcolor="rgba(255,255,255,0)",
        ),
    )
    apply_engineering_chart_typography(fig_ing_schedule, title_size=20, body_size=13, tick_size=11, legend_size=11)
    fig_ing_schedule.update_layout(hovermode="closest")
    fig_ing_schedule.update_xaxes(showspikes=False)
    st.plotly_chart(fig_ing_schedule, use_container_width=True, key="inputs_capex_10kw_ing_schedule_chart")
    st.markdown(
        f"""
        <div style="margin:0 0 12px 0;padding:0 2px;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;">
            {legend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    resumen_frp = build_ingenieria_schedule_summary(df_ing_schedule)
    total_tareas_frp = int(df_ing_schedule["Tarea"].nunique() or 0)
    total_frentes_frp = int(df_ing_schedule["PIEZA"].nunique() or 0)
    if "Fecha_dt" in df_ing_schedule.columns and df_ing_schedule["Fecha_dt"].notna().any():
        fecha_inicio_global = pd.Timestamp(df_ing_schedule["Fecha_dt"].min()).strftime("%d-%m-%Y")
        fecha_fin_global = pd.Timestamp(df_ing_schedule["Fecha_dt"].max()).strftime("%d-%m-%Y")
        criterio_text = (
            "La hoja fuente se interpreta como cronograma por rango: para cada tarea se toma "
            "Inicio y Fin explícitos, y se consolida la actividad diaria intermedia para lectura ejecutiva."
        )
    else:
        fecha_inicio_global = str(fecha_ticks.iloc[0]["Fecha"]) if not fecha_ticks.empty else "-"
        fecha_fin_global = str(fecha_ticks.iloc[-1]["Fecha"]) if not fecha_ticks.empty else "-"
        criterio_text = (
            "Los registros de la hoja se leen como marcas de actividad por fecha. "
            "No representan dotación ni horas; se usan para estimar inicio, fin y duración calendario."
        )

    st.markdown(
        '<div class="eng-body-title" style="font-size:18px;font-weight:800;color:#0f172a;margin:18px 0 10px 0;">Resumen ejecutivo — Cronograma FRP</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="margin:0 0 12px 0;padding:14px 16px;border:1px solid rgba(203,213,225,.72);border-radius:14px;background:#F8FAFC;">
            <div style="font-size:14px;font-weight:800;color:#274C77;margin:0 0 6px 0;">Criterio aplicado</div>
            <div style="font-size:13.5px;line-height:1.55;color:#475569;">{html.escape(criterio_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(
        style_engineering_table(resumen_frp, header_color="#2F557F", row_color="#F8FBFF")
        .set_properties(
            **{
                "font-size": "13px",
                "color": "#334155",
                "font-family": '"Aptos","Segoe UI",sans-serif',
            }
        )
        .set_properties(
            subset=["Pieza / frente", "Tarea crítica / mayor duración"],
            **{
                "text-align": "left",
                "font-weight": "700",
                "color": "#243B53",
            }
        )
        .set_properties(
            subset=["Inicio", "Fin", "Duración calendario", "Tareas", "Días con actividad"],
            **{
                "font-variant-numeric": "tabular-nums",
                "font-weight": "600",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=min(420, 80 + 46 * max(len(resumen_frp), 1)),
    )
    st.markdown("### Lectura rápida")
    st.markdown(
        "\n".join(
            [
                f"- El cronograma consolidado contiene `{total_tareas_frp}` tareas distribuidas en `{total_frentes_frp}` frentes.",
                f"- El tramo total va desde `{fecha_inicio_global}` hasta `{fecha_fin_global}`.",
                "- La tabla resume inicio, término, carga de tareas y la actividad crítica de cada frente.",
            ]
        )
    )


def render_inputs_project_gantt():
    try:
        df_gantt = load_project_gantt_data(GANTT_PROJECT_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
    except Exception as exc:
        st.warning(f"No se pudo cargar la Carta Gantt del proyecto: {exc}")
        return

    if df_gantt.empty or "Tarea / Entregable" not in df_gantt.columns:
        return

    render_inputs_gantt_design_css()
    header_mode = st.session_state.get("inputs_gantt_mode", "Real")
    render_inputs_gantt_header(df_gantt, date_mode=header_mode)

    has_linea = "Línea" in df_gantt.columns
    with st.container(border=True):
        st.markdown('<div class="gantt-panel-title">Filtros de análisis</div>', unsafe_allow_html=True)
        if has_linea:
            c1, c2, c3, c4, c5 = st.columns([3.2, 2.6, 2.1, 1.7, 1.9])
        else:
            c1, c3, c4, c5 = st.columns([4, 2.2, 1.8, 1.8])
        with c1:
            fases = sorted(
                df_gantt["Fase"].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan}).dropna().unique().tolist()
            ) if "Fase" in df_gantt.columns else []
            fase_options = ["Todas", ASPAS_FRP_GANTT_PHASE_OPTION] + [
                fase for fase in fases
                if fase != ASPAS_FRP_GANTT_PHASE_OPTION
            ]
            target_phase = next(
                (
                    fase for fase in fases
                    if str(fase).strip().casefold() == "suministro y equipamiento mecanico"
                ),
                None,
            )
            fase_default = target_phase or ("Instalación Turbina" if "Instalación Turbina" in fases else "Todas")
            fase_saved = st.session_state.pop("inputs_gantt_fase__sticky", None)
            if fase_saved in fase_options:
                st.session_state["inputs_gantt_fase"] = fase_saved
            elif "inputs_gantt_fase" not in st.session_state:
                st.session_state["inputs_gantt_fase"] = fase_default
            elif st.session_state["inputs_gantt_fase"] not in fase_options:
                st.session_state["inputs_gantt_fase"] = fase_default
            fase_sel = st.selectbox(
                "Fase",
                fase_options,
                key="inputs_gantt_fase",
            )
        linea_sel = "Todas"
        if has_linea:
            with c2:
                lineas_df = df_gantt.copy()
                if fase_sel != "Todas" and "Fase" in lineas_df.columns:
                    lineas_df = lineas_df[lineas_df["Fase"].astype(str).str.strip() == fase_sel].copy()
                lineas = sorted(
                    lineas_df["Línea"].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan}).dropna().unique().tolist()
                )
                linea_options = ["Todas"] + lineas
                linea_saved = st.session_state.pop("inputs_gantt_linea__sticky", None)
                if linea_saved in linea_options:
                    st.session_state["inputs_gantt_linea"] = linea_saved
                linea_default = st.session_state.get("inputs_gantt_linea", "Todas")
                if linea_default not in linea_options:
                    linea_default = "Todas"
                    st.session_state["inputs_gantt_linea"] = linea_default
                linea_sel = st.selectbox(
                    "Línea",
                    linea_options,
                    index=linea_options.index(linea_default),
                    key="inputs_gantt_linea",
                )
        with c3:
            estados = sorted(
                df_gantt["Estado"].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan}).dropna().unique().tolist()
            ) if "Estado" in df_gantt.columns else []
            estado_options = ["Todos"] + estados
            estado_saved = st.session_state.pop("inputs_gantt_estado__sticky", None)
            if estado_saved in estado_options:
                st.session_state["inputs_gantt_estado"] = estado_saved
            estado_default = st.session_state.get("inputs_gantt_estado", "Todos")
            if estado_default not in estado_options:
                estado_default = "Todos"
                st.session_state["inputs_gantt_estado"] = estado_default
            estado_sel = st.selectbox(
                "Estado",
                estado_options,
                index=estado_options.index(estado_default),
                key="inputs_gantt_estado",
            )
        with c4:
            mode_saved = st.session_state.pop("inputs_gantt_mode__sticky", None)
            if mode_saved in ("Plan", "Real"):
                st.session_state["inputs_gantt_mode"] = mode_saved
            date_mode = st.radio(
                "Fechas",
                ["Plan", "Real"],
                index=1,
                horizontal=True,
                key="inputs_gantt_mode",
            )
        with c5:
            color_saved = st.session_state.pop("inputs_gantt_color__sticky", None)
            color_options = ["Estado", "Línea", "Piloto"] if has_linea else ["Estado", "Piloto"]
            if color_saved in color_options:
                st.session_state["inputs_gantt_color"] = color_saved
            color_by = st.radio(
                "Color por",
                color_options,
                horizontal=True,
                key="inputs_gantt_color",
            )

    if fase_sel == ASPAS_FRP_GANTT_PHASE_OPTION:
        render_inputs_aspas_frp_schedule_chart()
        return

    plot_df = df_gantt.copy()
    if fase_sel != "Todas" and "Fase" in plot_df.columns:
        plot_df = plot_df[plot_df["Fase"].astype(str).str.strip() == fase_sel].copy()
    if linea_sel != "Todas" and "Línea" in plot_df.columns:
        plot_df = plot_df[plot_df["Línea"].astype(str).str.strip() == linea_sel].copy()
    if estado_sel != "Todos" and "Estado" in plot_df.columns:
        plot_df = plot_df[plot_df["Estado"].astype(str).str.strip() == estado_sel].copy()
    if plot_df.empty:
        st.info("No hay tareas para los filtros seleccionados.")
        return

    render_inputs_gantt_kpis(plot_df, date_mode=date_mode)

    legend_color_map = None
    if fase_sel == "Todas":
        legend_color_map = build_gantt_phase_color_map(plot_df)
    elif "Línea" in plot_df.columns and linea_sel == "Todas":
        legend_color_map = build_gantt_line_color_map(plot_df)
    gantt_title = "Cronograma" if fase_sel == "Todas" else f"Cronograma {fase_sel}"
    render_inputs_gantt_custom_chart(
        plot_df,
        date_mode=date_mode,
        legend_color_map=legend_color_map,
        title=gantt_title,
    )


def render_inputs_contexto_block():
    try:
        contexto_title, contexto_sections = build_bullet_contexto_10kw_sections(BULLET_CONTEXTO_10KW_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
    except Exception as exc:
        st.error(f"No se pudo cargar la hoja bullet: {exc}")
        return

    if not contexto_sections:
        st.info("La hoja bullet no contiene secciones para mostrar.")
        return

    contexto_title = contexto_title or "Arquitectura de inversión y creación de valor"
    total_sections = len(contexto_sections)
    total_bullets = sum(len(section["bullets"]) for section in contexto_sections)
    lead_section = contexto_sections[0]["title"] if contexto_sections else "-"

    st.markdown(
        """
        <style>
        .context-hero{
            border-radius:24px;
            padding:20px 22px 18px 22px;
            background:
                radial-gradient(circle at top right, rgba(14,165,164,.14), transparent 28%),
                linear-gradient(90deg,#f8fbff 0%,#e9f6ff 48%,#d7efff 100%);
            border:1px solid rgba(125,211,252,.42);
            box-shadow:0 16px 34px rgba(15,23,42,.08);
            margin-bottom:18px;
        }
        .context-hero-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#0f766e;
            margin-bottom:8px;
        }
        .context-hero-t{
            font-size:34px;
            font-weight:900;
            line-height:1.08;
            color:#0f172a;
            margin-bottom:10px;
            max-width:920px;
        }
        .context-hero-s{
            font-size:15px;
            line-height:1.6;
            color:#475569;
            max-width:980px;
            margin-bottom:14px;
        }
        .context-hero-band{
            display:flex;
            gap:10px;
            flex-wrap:wrap;
        }
        .context-hero-chip{
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding:8px 12px;
            border-radius:999px;
            background:rgba(255,255,255,.82);
            border:1px solid rgba(148,163,184,.22);
            color:#334155;
            font-size:12px;
            font-weight:700;
        }
        .context-stat{
            border-radius:18px;
            padding:16px 18px;
            background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
            border:1px solid rgba(148,163,184,.24);
            box-shadow:0 8px 18px rgba(15,23,42,.05);
            margin-bottom:14px;
        }
        .context-stat-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748b;
            margin-bottom:8px;
        }
        .context-stat-v{
            font-size:30px;
            font-weight:800;
            line-height:1;
            color:#0f172a;
            margin-bottom:8px;
        }
        .context-stat-s{
            font-size:13px;
            color:#475569;
            line-height:1.45;
        }
        .context-card{
            border-radius:20px;
            padding:18px 18px 16px 18px;
            background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
            border:1px solid rgba(148,163,184,.22);
            box-shadow:0 10px 24px rgba(15,23,42,.05);
            margin-bottom:16px;
            height:100%;
        }
        .context-card:hover{
            transform:translateY(-1px);
            box-shadow:0 16px 30px rgba(15,23,42,.08);
            transition:all .18s ease;
        }
        .context-card-h{
            font-size:17px;
            font-weight:800;
            line-height:1.25;
            color:#0f172a;
            margin-bottom:12px;
        }
        .context-chip{
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            font-size:12px;
            font-weight:700;
            background:#ecfeff;
            border:1px solid rgba(14,165,164,.20);
            color:#0f766e;
            margin-bottom:10px;
        }
        .context-bullet{
            display:flex;
            gap:10px;
            align-items:flex-start;
            margin-bottom:10px;
        }
        .context-dot{
            width:9px;
            height:9px;
            margin-top:7px;
            border-radius:999px;
            background:linear-gradient(180deg,#10b981 0%,#0ea5a4 100%);
            flex:0 0 auto;
        }
        .context-bullet-t{
            font-size:14px;
            line-height:1.5;
            color:#334155;
        }
        .context-grid-head{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748b;
            margin:2px 0 12px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    stage_counts = {
        "Diseño y Optimización del Sistema": min(total_sections, 3),
        "Ingeniería Aplicada y Manufactura": max(0, min(total_sections - 3, 3)),
        "Integración y Validación del Activo": max(0, min(total_sections - 6, 2)),
    }
    st.markdown(
        f"""
        <div class="context-hero">
          <div class="context-hero-k">Ruta de Validación</div>
          <div class="context-hero-t">Validación Integrada del Sistema</div>
          <div class="context-hero-s">
            Lectura técnica estructurada para consolidar la validación del activo, conectando diseño, manufactura e integración como base habilitante para el escalamiento.
          </div>
          <div class="context-hero-band">
            <div class="context-hero-chip">Hitos técnicos: {total_sections}</div>
            <div class="context-hero-chip">Frentes documentados: {total_bullets}</div>
            <div class="context-hero-chip">Diseño: {stage_counts["Diseño y Optimización del Sistema"]}</div>
            <div class="context-hero-chip">Manufactura: {stage_counts["Ingeniería Aplicada y Manufactura"]}</div>
            <div class="context-hero-chip">Integración: {stage_counts["Integración y Validación del Activo"]}</div>
          </div>
        </div>
        <div class="context-grid-head">Matriz técnica de hitos</div>
        """,
        unsafe_allow_html=True,
    )
    rows = [contexto_sections[i:i + 2] for i in range(0, len(contexto_sections), 2)]
    for row_sections in rows:
        cols = st.columns(len(row_sections))
        for idx, section in enumerate(row_sections):
            absolute_idx = contexto_sections.index(section)
            if absolute_idx in (0, 1, 2):
                chip_label = "Diseño y Optimización del Sistema"
            elif absolute_idx in (3, 4, 5):
                chip_label = "Ingeniería Aplicada y Manufactura"
            elif absolute_idx in (6, 7):
                chip_label = "Integración y Validación del Activo"
            else:
                chip_label = "Narrativa estratégica"
            bullets_html = "".join(
                f'<div class="context-bullet"><span class="context-dot"></span><div class="context-bullet-t">{bullet}</div></div>'
                for bullet in section["bullets"]
            )
            with cols[idx]:
                st.markdown(
                    f"""
                    <div class="context-card">
                      <div class="context-chip">{chip_label}</div>
                      <div class="context-card-h">{section["title"]}</div>
                      {bullets_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


@st.cache_data(show_spinner=False, ttl=120)
def get_valor_activo_tecnologico_construido(refresh_nonce: int = 0) -> tuple[float, float, float, float]:
    monto_total = 0.0
    capacidades_externo = 0.0
    know_how_fw = 0.0

    try:
        df_fin = load_dashboard_financiero_data(DASHBOARD_FINANCIERO_CSV_URL_DEFAULT, refresh_nonce=refresh_nonce)
        if not df_fin.empty and "Monto" in df_fin.columns:
            monto_total = float(df_fin["Monto"].dropna().sum() or 0.0)
    except Exception:
        monto_total = 0.0

    try:
        df_val_raw = load_valorizacion_raw_data(VALORIZACION_CSV_URL_DEFAULT, refresh_nonce=refresh_nonce)
        if df_val_raw.shape[0] > 6 and df_val_raw.shape[1] > 6:
            capacidades_externo = float(parse_money_clp_robusto(clean_sheet_cell(df_val_raw.iloc[5, 6])) or 0.0)
    except Exception:
        capacidades_externo = 0.0
    knowhow_payload = get_knowhow_resumen_payload()
    know_how_fw = float(
        parse_money_clp_robusto(knowhow_payload.get("kpis", {}).get("Valor know-how modelado", ""))
        or 0.0
    )
    if know_how_fw <= 0:
        try:
            if df_val_raw.shape[0] > 6 and df_val_raw.shape[1] > 6:
                know_how_fw = float(parse_money_clp_robusto(clean_sheet_cell(df_val_raw.iloc[6, 6])) or 0.0)
        except Exception:
            know_how_fw = 0.0

    return monto_total + capacidades_externo + know_how_fw, monto_total, capacidades_externo, know_how_fw


def render_inputs_capex_10kw_detail():
    try:
        df_10kw = build_restante_piloto_10kw_view(RESTANTE_PILOTO_10KW_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
    except Exception as exc:
        st.error(f"No se pudo cargar la hoja Restante piloto 10kw: {exc}")
        return

    if df_10kw.empty:
        st.info("La hoja Restante piloto 10kw no contiene datos para mostrar.")
        return

    resumen_10kw = (
        df_10kw[df_10kw["Valor C"] > 0]
        .groupby("Columna A", as_index=False)
        .agg(Monto_CLP=("Valor C", "sum"), Items=("Columna B", "count"))
        .sort_values("Monto_CLP", ascending=False)
        .reset_index(drop=True)
    )
    total_10kw = float(resumen_10kw["Monto_CLP"].sum() or 0.0)
    resumen_10kw["Pct_total"] = np.where(total_10kw > 0, resumen_10kw["Monto_CLP"] / total_10kw * 100.0, 0.0)
    resumen_10kw["Monto_fmt"] = resumen_10kw["Monto_CLP"].apply(format_clp)

    if resumen_10kw.empty:
        st.info("La columna C no contiene valores numéricos válidos para el gráfico de torta.")
        render_inputs_project_gantt()
        return

    capex_palette = [
        "#087f6f", "#1d4ed8", "#f59e0b", "#7c3aed", "#ef2424",
        "#0891b2", "#65a30d", "#f15a24", "#8e44ad", "#64748b",
        "#f6a400", "#4f7fcf", "#10b981", "#db56b6", "#a7663f",
    ]
    resumen_10kw["_color"] = [capex_palette[idx % len(capex_palette)] for idx in range(len(resumen_10kw))]
    top_component = resumen_10kw.iloc[0]
    top_two_pct = float(resumen_10kw["Pct_total"].head(2).sum() or 0.0)
    total_items = int(resumen_10kw["Items"].sum() or 0)
    total_components = int(len(resumen_10kw))

    st.markdown(
        """
        <style>
        .capex10-shell{border:1px solid #d9e2ee;border-radius:18px;background:#fff;padding:20px 22px 18px 22px;box-shadow:0 18px 42px rgba(15,23,42,.06);margin:0 0 16px 0;}
        .capex10-breadcrumb{display:flex;align-items:center;gap:12px;color:#0f172a;font-size:14px;font-weight:900;margin:0 0 14px 0;}
        .capex10-brand{font-size:23px;color:#0f766e;margin-right:8px;}
        .capex10-sep{color:#64748b;font-weight:800;}
        .capex10-title{font-size:24px;line-height:1.08;font-weight:900;color:#08122a;margin:0 0 8px 0;}
        .capex10-sub{font-size:13px;line-height:1.55;color:#274060;margin:0 0 18px 0;max-width:680px;}
        .capex10-kpis{display:grid;grid-template-columns:1.04fr 1.02fr .92fr .9fr .92fr;gap:14px;margin:0 0 16px 0;}
        .capex10-kpi{border:1px solid var(--bd);background:linear-gradient(135deg,var(--bg1),#fff 72%);border-radius:10px;padding:16px 16px;display:grid;grid-template-columns:56px 1fr;gap:14px;align-items:center;min-height:88px;}
        .capex10-ico{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--ico-bg);color:var(--accent);font-size:28px;font-weight:900;}
        .capex10-k{font-size:10px;letter-spacing:.04em;text-transform:uppercase;color:var(--accent);font-weight:900;margin:0 0 7px 0;}
        .capex10-v{font-size:22px;line-height:1;font-weight:900;color:#08122a;margin:0 0 8px 0;}
        .capex10-s{font-size:11px;color:#14284a;margin:0;}
        .capex10-main{display:grid;grid-template-columns:1.05fr 1fr;gap:16px;margin:0 0 16px 0;}
        .capex10-panel{border:1px solid #d9e2ee;border-radius:14px;background:#fff;padding:18px 18px 16px 18px;height:520px;box-sizing:border-box;overflow:hidden;}
        .capex10-panel-body{height:calc(100% - 38px);display:flex;flex-direction:column;}
        .capex10-panel-head{display:flex;align-items:center;justify-content:space-between;margin:0 0 12px 0;}
        .capex10-panel-title{font-size:15px;font-weight:900;color:#0b1730;margin:0;}
        .capex10-info{width:16px;height:16px;border-radius:50%;border:1px solid #94a3b8;color:#64748b;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;}
        .capex10-download{border:1px solid #dce5f0;border-radius:8px;background:#f8fbff;padding:8px 12px;color:#102039;font-size:11px;font-weight:900;}
        .capex10-legend{display:grid;gap:7px;align-content:start;padding-top:10px;max-height:350px;overflow:auto;padding-right:4px;}
        .capex10-leg-row{display:grid;grid-template-columns:14px 1fr 46px;gap:7px;align-items:center;font-size:10.5px;color:#102039;font-weight:700;}
        .capex10-dot{width:10px;height:10px;border-radius:50%;background:#94a3b8;display:inline-block;flex:0 0 auto;}
        .capex10-pct{text-align:right;font-weight:900;color:#102039;}
        .capex10-chart-area{flex:1;min-height:0;}
        .capex10-callout{display:grid;grid-template-columns:46px 1fr;gap:14px;align-items:center;border:1px solid #d9e5f5;border-radius:12px;background:#fbfdff;margin-top:12px;padding:14px 16px;}
        .capex10-call-ico{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#eef5ff;color:#1d4ed8;font-size:24px;}
        .capex10-call-t{font-size:13px;font-weight:900;color:#1d4ed8;margin:0 0 5px 0;}
        .capex10-call-s{font-size:11.5px;color:#274060;margin:0;}
        .capex10-table{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border-radius:10px;border:1px solid #e2e8f0;font-size:11px;color:#102039;}
        .capex10-table th{background:#0b1736;color:#fff;padding:10px 12px;text-align:center;font-weight:900;}
        .capex10-table th:first-child{text-align:left;padding-left:26px;}
        .capex10-table td{padding:8px 12px;border-bottom:1px solid #e7edf4;border-right:1px solid #e7edf4;text-align:center;}
        .capex10-table td:first-child{text-align:left;font-weight:800;}
        .capex10-table tr:first-child td{background:#e7fbf5;}
        .capex10-table tr.total td{background:#e8f8f4;color:#087f6f;font-size:13px;font-weight:900;border-bottom:0;}
        .capex10-name{display:flex;align-items:center;gap:9px;}
        .capex10-row-dot{width:8px;height:8px;border-radius:50%;background:#94a3b8;display:inline-block;flex:0 0 auto;}
        .capex10-table-scroll{flex:1;min-height:0;overflow:auto;border-radius:10px;}
        .capex10-footer{display:grid;grid-template-columns:1.1fr 1fr 1.2fr 1.25fr 1fr;gap:0;border:1px solid #d9e2ee;border-radius:14px;background:#fbfdff;padding:14px 18px;}
        .capex10-foot-item{display:grid;grid-template-columns:42px 1fr;gap:10px;align-items:center;border-right:1px solid #d8e2ee;padding:0 18px;}
        .capex10-foot-item:first-child{padding-left:0;}
        .capex10-foot-item:last-child{border-right:0;padding-right:0;}
        .capex10-foot-ico{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#eef4ff;color:#315d9b;font-size:20px;}
        .capex10-foot-k{font-size:11px;color:#587093;margin:0 0 4px 0;}
        .capex10-foot-v{font-size:12px;color:#18345c;margin:0;font-weight:600;}
        @media (max-width: 1100px){.capex10-kpis,.capex10-main,.capex10-footer{grid-template-columns:1fr}.capex10-foot-item{border-right:0;border-bottom:1px solid #d8e2ee;padding:10px 0}.capex10-foot-item:last-child{border-bottom:0}.capex10-panel{height:auto;overflow:visible}.capex10-panel-body,.capex10-table-scroll{height:auto;overflow:visible}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="capex10-shell">
          <div class="capex10-breadcrumb"><span class="capex10-brand">✈</span><span>Levantamiento Capital 80kW</span><span class="capex10-sep">›</span><span>Piloto 10 kW</span></div>
          <h2 class="capex10-title">Brecha de Inversión – Piloto 10 kW</h2>
          <p class="capex10-sub">Lectura consolidada de la inversión pendiente del piloto 10 kW,<br>con foco en componentes, cronograma y base de ingeniería.</p>
          <div class="capex10-kpis">
            <div class="capex10-kpi" style="--accent:#087f6f;--bd:#b7e4dc;--bg1:#edfdfa;--ico-bg:#cff7e9;"><div class="capex10-ico">▣</div><div><p class="capex10-k">CAPEX TOTAL (10 kW)</p><p class="capex10-v">{format_clp(total_10kw)}</p><p class="capex10-s">Monto consolidado pendiente</p></div></div>
            <div class="capex10-kpi" style="--accent:#1d4ed8;--bd:#c7d8ff;--bg1:#f2f6ff;--ico-bg:#dfe9ff;"><div class="capex10-ico">◔</div><div><p class="capex10-k">COMPONENTES</p><p class="capex10-v">{total_components}</p><p class="capex10-s">Componentes principales</p></div></div>
            <div class="capex10-kpi" style="--accent:#7c3aed;--bd:#dfccff;--bg1:#faf5ff;--ico-bg:#efe2ff;"><div class="capex10-ico">☷</div><div><p class="capex10-k">ÍTEMS TOTALES</p><p class="capex10-v">{total_items}</p><p class="capex10-s">Ítems considerados</p></div></div>
            <div class="capex10-kpi" style="--accent:#f97316;--bd:#fed7aa;--bg1:#fff7ed;--ico-bg:#ffedd5;"><div class="capex10-ico">%</div><div><p class="capex10-k">MAYOR COMPONENTE</p><p class="capex10-v">{float(top_component["Pct_total"]):.1f}%</p><p class="capex10-s">{html.escape(str(top_component["Columna A"]))}</p></div></div>
            <div class="capex10-kpi" style="--accent:#087f6f;--bd:#b7e4dc;--bg1:#f0fdfa;--ico-bg:#d1fae5;"><div class="capex10-ico">▣</div><div><p class="capex10-k">FECHA DE CORTE</p><p class="capex10-v">13 may 2025</p><p class="capex10-s">3:05 p.m.</p></div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig_10kw = px.pie(
        resumen_10kw,
        values="Monto_CLP",
        names="Columna A",
        hole=0.52,
        color="Columna A",
        color_discrete_map={row["Columna A"]: row["_color"] for _, row in resumen_10kw.iterrows()},
    )
    fig_10kw.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(size=12, color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>Monto: $%{value:,.0f}<br>Participación: %{percent}<extra></extra>",
        marker=dict(line=dict(color="white", width=2)),
        sort=False,
        showlegend=False,
    )
    fig_10kw.add_annotation(
        text=f"<b>CAPEX<br>10 kW</b><br><span style='color:#087f6f'>{format_clp(total_10kw)}</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=18, color="#0B1730"),
    )
    fig_10kw.update_layout(
        margin=dict(l=0, r=0, t=8, b=8),
        height=390,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    legend_html = "".join(
        textwrap.dedent(
            f"""
            <div class="capex10-leg-row">
              <span class="capex10-dot" style="background-color:{row['_color']};"></span>
              <span>{html.escape(str(row['Columna A']))}</span>
              <span class="capex10-pct">{float(row['Pct_total']):.1f}%</span>
            </div>
            """
        ).strip()
        for _, row in resumen_10kw.iterrows()
    )

    table_rows = "".join(
        textwrap.dedent(
            f"""
            <tr>
              <td><span class="capex10-name"><span class="capex10-row-dot" style="background-color:{row['_color']};"></span>{html.escape(str(row['Columna A']))}</span></td>
              <td>{format_clp(float(row['Monto_CLP']))}</td>
              <td>{int(row['Items'])}</td>
              <td>{float(row['Pct_total']):.1f}%</td>
            </tr>
            """
        ).strip()
        for _, row in resumen_10kw.iterrows()
    )

    pie_col, table_col = st.columns([1.04, 1])
    with pie_col:
        with st.container(border=True):
            st.markdown(
                """
              <div class="capex10-panel-head">
                <p class="capex10-panel-title">Distribución relativa por componente</p>
                <span class="capex10-info">i</span>
              </div>
                """,
                unsafe_allow_html=True,
            )
            chart_col, legend_col = st.columns([1.35, 0.8])
            with chart_col:
                st.plotly_chart(fig_10kw, use_container_width=True, config={"displayModeBar": False})
            with legend_col:
                st.markdown(
                    f'<div class="capex10-legend">{"".join(legend_html.splitlines())}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"""
              <div class="capex10-callout">
                <div class="capex10-call-ico">♢</div>
                <div>
                  <p class="capex10-call-t">Información clave</p>
                  <p class="capex10-call-s">Los dos principales componentes concentran el <b style="color:#087f6f;">{top_two_pct:.1f}%</b> del CAPEX total del piloto 10 kW.</p>
                </div>
              </div>
                """,
                unsafe_allow_html=True,
            )
    with table_col:
        st.markdown(
            f"""
            <div class="capex10-panel">
              <div class="capex10-panel-head">
                <p class="capex10-panel-title">Resumen consolidado por componente</p>
                <span class="capex10-download">⇩&nbsp;&nbsp;Descargar</span>
              </div>
              <div class="capex10-panel-body">
                <div class="capex10-table-scroll">
                  <table class="capex10-table">
                    <thead><tr><th>Componente</th><th>Monto CLP.</th><th>Ítems</th><th>% del total</th></tr></thead>
                    <tbody>
                      {table_rows}
                      <tr class="total"><td>TOTAL</td><td>{format_clp(total_10kw)}</td><td>{total_items}</td><td>100%</td></tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="capex10-footer">
          <div class="capex10-foot-item"><div class="capex10-foot-ico">▣</div><div><p class="capex10-foot-k">Proyecto</p><p class="capex10-foot-v">Levantamiento Capital 80kW</p></div></div>
          <div class="capex10-foot-item"><div class="capex10-foot-ico">✈</div><div><p class="capex10-foot-k">Piloto</p><p class="capex10-foot-v">Piloto 10 kW</p></div></div>
          <div class="capex10-foot-item"><div class="capex10-foot-ico">▤</div><div><p class="capex10-foot-k">Base de referencia</p><p class="capex10-foot-v">Ingeniería Conceptual v1.2</p></div></div>
          <div class="capex10-foot-item"><div class="capex10-foot-ico">◷</div><div><p class="capex10-foot-k">Última actualización</p><p class="capex10-foot-v">13 may 2025 · 3:05 p.m.</p></div></div>
          <div class="capex10-foot-item"><div class="capex10-foot-ico">♙</div><div><p class="capex10-foot-k">Responsable</p><p class="capex10-foot-v">Equipo Técnico</p></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_inputs_project_gantt()


def render_inputs_estado_actual_dashboard():
    estado_subblock_key = "inputs_estado_actual_subbloque_sel"

    def _set_estado_subblock(value: str):
        st.session_state[estado_subblock_key] = value

    estado_subblocks = [
        ("contexto", "Construcción del Activo Tecnológico (en ejecución)"),
        ("financiero", "Materialización del Activo – Piloto 10 kW"),
    ]
    estado_subblock_icons = {
        "contexto": "🛠️",
        "financiero": "🧱",
    }
    if estado_subblock_key not in st.session_state:
        st.session_state[estado_subblock_key] = None

    subnav_cols = st.columns(2)
    for idx, (block_value, block_title) in enumerate(estado_subblocks):
        is_active = st.session_state.get(estado_subblock_key) == block_value
        with subnav_cols[idx]:
            st.markdown(
                f"""
                <div class="inputs-nav-card {'active' if is_active else ''}">
                    <div class="inputs-nav-k">Sub-bloque {idx + 1}</div>
                    <div class="inputs-nav-title-row">
                        <div class="inputs-nav-ico">{estado_subblock_icons.get(block_value, '📁')}</div>
                        <div class="inputs-nav-title-wrap">
                            <div class="inputs-nav-t">{block_title}</div>
                        </div>
                    </div>
                    <div class="inputs-nav-s">{'Seleccionado para análisis' if is_active else 'Haz clic para abrir este sub-bloque'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                selector_button_label(block_title, is_active),
                key=f"inputs_estado_subnav_{idx}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                on_click=_set_estado_subblock,
                args=(block_value,),
            )

    st.markdown("---")
    selected_estado_subblock = st.session_state.get(estado_subblock_key)

    if selected_estado_subblock == "contexto":
        render_inputs_contexto_block()
        return
    if selected_estado_subblock != "financiero":
        return

    try:
        df_fin = load_dashboard_financiero_data(DASHBOARD_FINANCIERO_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
    except Exception as exc:
        st.error(f"No se pudo cargar la fuente de Dashboard Financiero Proyecto: {exc}")
        return

    base = df_fin[df_fin["Monto"].notna()].copy()
    if base.empty:
        st.info("La fuente de Dashboard Financiero Proyecto no contiene registros válidos.")
        return

    valor_activo_tecnologico, monto_total, capacidades_externo, know_how_fw = get_valor_activo_tecnologico_construido(refresh_nonce=data_refresh_nonce)

    st.markdown(
        """
        <style>
        .asset-hero{
            border-radius:24px;
            padding:22px 24px;
            background:
                radial-gradient(circle at top right, rgba(14,165,164,.18), transparent 24%),
                linear-gradient(90deg,#f8fbff 0%,#e7f5ff 48%,#d4efff 100%);
            border:1px solid rgba(125,211,252,.45);
            box-shadow:0 16px 36px rgba(15,23,42,.08);
            margin-bottom:20px;
        }
        .asset-hero-grid{
            display:grid;
            grid-template-columns:1.3fr .9fr;
            gap:18px;
            align-items:stretch;
        }
        @media (max-width:1100px){.asset-hero-grid{grid-template-columns:1fr;}}
        .asset-hero-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.14em;
            text-transform:uppercase;
            color:#0f766e;
            margin-bottom:8px;
        }
        .asset-hero-t{
            font-size:18px;
            font-weight:800;
            line-height:1.2;
            color:#0f172a;
            margin-bottom:10px;
        }
        .asset-hero-v{
            font-size:58px;
            font-weight:900;
            line-height:1;
            color:#0f172a;
            margin-bottom:12px;
            letter-spacing:-.03em;
        }
        .asset-hero-p{
            font-size:15px;
            line-height:1.6;
            color:#475569;
            max-width:780px;
        }
        .asset-hero-panel{
            border-radius:18px;
            padding:16px 18px;
            background:rgba(255,255,255,.75);
            border:1px solid rgba(148,163,184,.24);
            backdrop-filter:blur(6px);
        }
        .asset-hero-panel-h{
            font-size:12px;
            font-weight:800;
            letter-spacing:.10em;
            text-transform:uppercase;
            color:#64748b;
            margin-bottom:10px;
        }
        .asset-hero-row{
            display:flex;
            justify-content:space-between;
            gap:12px;
            align-items:flex-start;
            padding:10px 0;
            border-bottom:1px solid rgba(226,232,240,.9);
        }
        .asset-hero-row:last-child{border-bottom:none;padding-bottom:0}
        .asset-hero-label{
            font-size:14px;
            font-weight:700;
            color:#0f172a;
            line-height:1.35;
        }
        .asset-hero-value{
            font-size:16px;
            font-weight:800;
            color:#0f172a;
            white-space:nowrap;
        }
        .asset-hero-total{
            margin-top:10px;
            padding-top:12px;
            border-top:1px dashed rgba(14,165,164,.32);
            display:flex;
            justify-content:space-between;
            gap:12px;
            align-items:center;
        }
        .asset-hero-total .asset-hero-label{color:#0f766e;}
        .asset-hero-total .asset-hero-value{font-size:20px;color:#0f766e;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    panel_rows_html = [
        (
            '<div class="asset-hero-row">'
            '<div class="asset-hero-label">Inversión ejecutada en el activo</div>'
            f'<div class="asset-hero-value">{format_clp(monto_total)}</div>'
            "</div>"
        )
    ]
    if capacidades_externo > 0:
        panel_rows_html.append(
            '<div class="asset-hero-row">'
            '<div class="asset-hero-label">Capacidades externo</div>'
            f'<div class="asset-hero-value">{format_clp(capacidades_externo)}</div>'
            "</div>"
        )
    panel_rows_html.append(
        '<div class="asset-hero-row">'
        '<div class="asset-hero-label">Know-how técnico valorizado</div>'
        f'<div class="asset-hero-value">{format_clp(know_how_fw)}</div>'
        "</div>"
    )
    panel_rows_html.append(
        '<div class="asset-hero-total">'
        '<div class="asset-hero-label">Inversión a la fecha</div>'
        f'<div class="asset-hero-value">{format_clp(valor_activo_tecnologico)}</div>'
        "</div>"
    )
    panel_html = "".join(panel_rows_html)

    hero_html = (
        '<div class="asset-hero">'
        '<div class="asset-hero-grid">'
        '<div>'
        '<div class="asset-hero-k">Resumen patrimonial técnico</div>'
        '<div class="asset-hero-t">Costo ejecutado en Activo Tecnológico Construido</div>'
        f'<div class="asset-hero-v">{format_clp(valor_activo_tecnologico)}</div>'
        '<div class="asset-hero-p">'
        'Valor consolidado del activo construido considerando inversión ejecutada, '
        'capacidades externas incorporadas y know-how técnico valorizado dentro del proceso de desarrollo.'
        '</div>'
        '</div>'
        '<div class="asset-hero-panel">'
        '<div class="asset-hero-panel-h">Descomposición del valor</div>'
        f'{panel_html}'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    st.markdown(
        '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Estado Técnico-Financiero del Piloto 10 kW</div>',
        unsafe_allow_html=True,
    )
    financial_kpis = render_inputs_financial_main_kpis(base)
    selected_financial_asset = financial_kpis.get("selected", "costo_ejecutado")

    if selected_financial_asset == "costo_ejecutado":
        fig_sm, tabla_sm = make_inputs_suministro_chart(base)
        if fig_sm is not None and tabla_sm is not None and not tabla_sm.empty:
            st.plotly_chart(fig_sm, use_container_width=True)
        else:
            st.info("No hay datos válidos para graficar Suministro / Montaje.")

        render_inputs_item_analytics(base)
        render_inputs_factor_chart(base)
    elif selected_financial_asset == "know_how_fw":
        st.markdown(
            '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Diseño de Ingeniería y Know-how Técnico</div>',
            unsafe_allow_html=True,
        )
        render_inputs_knowhow_fw_detail()
    elif selected_financial_asset == "capacidades_externas":
        st.info(
            "La vista de `Capacidades externas` sigue usando la valorización complementaria del modelo. "
            "Si quieres, en el siguiente paso la conecto a una fuente detallada equivalente."
        )


def build_item_color_map(item_to_category: dict) -> dict:
    """Asigna a cada ítem el color de su categoría usando el orden corporativo."""
    ordered_categories = [
        "Desarrollo Tecnológico",
        "Componentes Mecánicos",
        "Sistema Eléctrico y Control",
        "Obras Civiles",
        "Montaje y Logística",
        "Ensayos y Certificación",
        "Contingencias y Administración",
    ]
    mapping = {}
    palette_cycle = list(ordered_categories)
    for item, category in item_to_category.items():
        cat_norm = str(category).strip()
        if cat_norm in CAT_COLOR_MAP:
            color = CAT_COLOR_MAP[cat_norm]
        else:
            # color no definido: usar la siguiente categoría de referencia
            idx = len(mapping) % len(palette_cycle)
            ref_cat = palette_cycle[idx]
            color = CAT_COLOR_MAP[ref_cat]
        mapping[item] = color
    return mapping


def render_category_palette():
    """Muestra una tira de categorías con sus colores corporativos."""
    palette_css = """
    <style>
    .cat-chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-bottom: 0.5rem;
    }
    .cat-chip {
        border-radius: 999px;
        padding: 0.2rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: #fff;
        white-space: nowrap;
    }
    </style>
    """
    chips = "".join(
        f'<span class="cat-chip" style="background:{color};">{cat}</span>'
        for cat, color in CAT_COLOR_MAP.items()
    )
    st.markdown(palette_css + f'<div class="cat-chip-container">{chips}</div>', unsafe_allow_html=True)


def render_pagos_hitos(
    capex_url: str,
    fx_used: float,
    pagos_scale: float,
    key_prefix: str = "",
    include_direction_salaries: bool = True,
):
    st.markdown("---")
    st.markdown(
        '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Estructura de Desembolso de Capital por Hitos del Proyecto</div>',
        unsafe_allow_html=True,
    )

    try:
        df_raw_pagos = load_capex_raw_data(capex_url, refresh_nonce=data_refresh_nonce).copy()
        col_map = {}
        if "ITEM" in df_raw_pagos.columns and "Item" not in df_raw_pagos.columns:
            col_map["ITEM"] = "Item"
        if "Categoría" in df_raw_pagos.columns and "Categoria" not in df_raw_pagos.columns:
            col_map["Categoría"] = "Categoria"
        if col_map:
            df_raw_pagos = df_raw_pagos.rename(columns=col_map)

        required_cols = [
            "Mes_Anticipo",
            "Pago_USD_Anticipo",
            "Mes_Entrega_FAT",
            "Pago_USD_Entrega",
            "Mes_SAT",
            "Pago_USD_SAT",
        ]
        missing_cols = [c for c in required_cols if c not in df_raw_pagos.columns]
        if missing_cols:
            st.error(f"Faltan columnas en la hoja de pagos: {missing_cols}")
            return

        def _sum_by_month(mes_col: str, pago_col: str, out_col: str) -> pd.DataFrame:
            df_tmp = df_raw_pagos[[mes_col, pago_col]].copy()
            df_tmp["Mes_i"] = pd.to_numeric(df_tmp[mes_col], errors="coerce")
            df_tmp["Pago_f"] = df_tmp[pago_col].apply(parse_money_usd_robusto) * pagos_scale
            out = (
                df_tmp.dropna(subset=["Mes_i"])
                .groupby("Mes_i", as_index=False)
                .agg(**{out_col: ("Pago_f", "sum")})
                .rename(columns={"Mes_i": "Mes"})
            )
            return out

        df_meses = pd.DataFrame({"Mes": list(range(1, 16))})

        df_anticipo = _sum_by_month(
            "Mes_Anticipo",
            "Pago_USD_Anticipo",
            "Pago_USD_Anticipo",
        )
        df_entrega = _sum_by_month(
            "Mes_Entrega_FAT",
            "Pago_USD_Entrega",
            "Pago_USD_Entrega",
        )
        df_sat = _sum_by_month("Mes_SAT", "Pago_USD_SAT", "Pago_USD_SAT")

        df_consolidado = (
            df_meses.merge(df_anticipo, on="Mes", how="left")
            .merge(df_entrega, on="Mes", how="left")
            .merge(df_sat, on="Mes", how="left")
            .fillna(0.0)
        )
        df_dir_mensual = pd.DataFrame(columns=["Mes", "Cargo", "Pago_CLP"])
        if include_direction_salaries:
            df_dir_mensual = build_direccion_mensual(df_direccion, horizonte_meses=int(df_meses["Mes"].max()))
            if not df_dir_mensual.empty:
                df_dir_mes = (
                    df_dir_mensual.groupby("Mes", as_index=False)
                    .agg(Pago_CLP_Sueldos=("Pago_CLP", "sum"))
                )
                df_consolidado = df_consolidado.merge(df_dir_mes, on="Mes", how="left")
            else:
                df_consolidado["Pago_CLP_Sueldos"] = 0.0
        else:
            df_consolidado["Pago_CLP_Sueldos"] = 0.0
        df_consolidado["Pago_CLP_Sueldos"] = df_consolidado["Pago_CLP_Sueldos"].fillna(0.0)
        df_consolidado["Pago_USD_Sueldos"] = np.where(
            np.isfinite(fx_used) and fx_used > 0,
            df_consolidado["Pago_CLP_Sueldos"] / fx_used,
            0.0,
        )
        df_consolidado["Total_USD"] = (
            df_consolidado["Pago_USD_Anticipo"]
            + df_consolidado["Pago_USD_Entrega"]
            + df_consolidado["Pago_USD_SAT"]
            + df_consolidado["Pago_USD_Sueldos"]
        )

        item_rows = []
        for _, row in df_raw_pagos.iterrows():
            item = str(row.get("Item", "")).strip() or "Sin ítem"
            categoria = str(row.get("Categoria", "")).strip() or "Sin categoría"
            mes_ant = pd.to_numeric(row.get("Mes_Anticipo"), errors="coerce")
            pago_ant = parse_money_usd_robusto(row.get("Pago_USD_Anticipo")) * pagos_scale
            mes_fat = pd.to_numeric(row.get("Mes_Entrega_FAT"), errors="coerce")
            pago_fat = parse_money_usd_robusto(row.get("Pago_USD_Entrega")) * pagos_scale
            mes_sat = pd.to_numeric(row.get("Mes_SAT"), errors="coerce")
            pago_sat = parse_money_usd_robusto(row.get("Pago_USD_SAT")) * pagos_scale

            if pd.notna(mes_ant):
                item_rows.append(
                    {
                        "Mes": int(mes_ant),
                        "Item": item,
                        "Categoria": categoria,
                        "Pago_USD": pago_ant,
                    }
                )
            if pd.notna(mes_fat):
                item_rows.append(
                    {
                        "Mes": int(mes_fat),
                        "Item": item,
                        "Categoria": categoria,
                        "Pago_USD": pago_fat,
                    }
                )
            if pd.notna(mes_sat):
                item_rows.append(
                    {
                        "Mes": int(mes_sat),
                        "Item": item,
                        "Categoria": categoria,
                        "Pago_USD": pago_sat,
                    }
                )

        df_item_periodo = pd.DataFrame(item_rows)
        if not df_item_periodo.empty:
            df_item_periodo = (
                df_item_periodo.groupby(["Mes", "Item", "Categoria"], as_index=False)
                .agg(Pago_USD=("Pago_USD", "sum"))
                .sort_values(["Mes", "Item"])
            )

        st.markdown(
            '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:0 0 10px 0;">Hitos de pagos</div>',
            unsafe_allow_html=True,
        )
        ctrl_col1, ctrl_col2 = st.columns([1, 1.15], gap="large")
        with ctrl_col1:
            unit_sel = st.selectbox(
                "Moneda/escala",
                ["USD (miles)", "CLP (millones)"],
                index=0,
                key=f"{key_prefix}pay_currency_selector",
            )
        if unit_sel.startswith("USD"):
            scale_factor = 1.0 / 1_000.0
            axis_unit = "miles USD"
            line_label = "Acumulado (miles USD)"
            def fmt_bar_value(val: float) -> str:
                return f"{val:,.0f}k".replace(",", ".")
            def scale_clp(series: pd.Series) -> pd.Series:
                return (series / fx_used) / 1_000.0 if np.isfinite(fx_used) and fx_used > 0 else series * 0.0
        else:
            scale_factor = fx_used / 1_000_000.0
            axis_unit = "MM CLP"
            line_label = "Acumulado (MM CLP)"
            def fmt_bar_value(val: float) -> str:
                return f"{val:.1f} MM"
            def scale_clp(series: pd.Series) -> pd.Series:
                return series / 1_000_000.0

        def scale_usd(series: pd.Series) -> pd.Series:
            return series * scale_factor

        def fmt_pago_detalle(val: float) -> str:
            if unit_sel.startswith("USD"):
                return f"{float(val):,.1f} kUSD".replace(",", ".")
            return f"{float(val):,.2f} MM CLP".replace(",", ".")

        def apply_unified_hover(fig):
            fig.update_layout(
                hovermode="x unified",
                hoverlabel=dict(
                    bgcolor="rgba(255,255,255,0.78)",
                    bordercolor="rgba(148,163,184,0.22)",
                    font=dict(size=12, color="#0f172a"),
                ),
            )
            fig.update_xaxes(
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikecolor="rgba(185,28,28,0.32)",
                spikethickness=1.4,
            )
            try:
                fig.update_xaxes(unifiedhovertitle=dict(text="<b>Mes %{x}</b>"))
            except Exception:
                pass

        with ctrl_col2:
            default_view_index = 0 if "capex_overview" in str(key_prefix) else 1
            view_sel = st.selectbox(
                "Selecciona vista",
                [
                    "1) Inyección por hito (Anticipo/FAT/SAT)",
                    "2) Inyección por ítem",
                    "3) Total por período + categoría",
                ],
                index=default_view_index,
                key=f"{key_prefix}pay_view_selector",
            )
        detail_title = ""
        detail_df = pd.DataFrame()

        if view_sel.startswith("1"):
            df_flujo_plot = df_consolidado.copy()
            df_flujo_plot["Total_plot"] = scale_usd(df_flujo_plot["Total_USD"])
            df_flujo_plot["Acum_plot"] = df_flujo_plot["Total_plot"].cumsum()
            df_flujo_long = df_flujo_plot.melt(
                id_vars=["Mes"],
                value_vars=[
                    "Pago_USD_Anticipo",
                    "Pago_USD_Entrega",
                    "Pago_USD_SAT",
                ],
                var_name="Tipo",
                value_name="Pago_USD",
            )
            df_flujo_long["Pago_plot"] = scale_usd(df_flujo_long["Pago_USD"])
            df_flujo_long["Tipo"] = df_flujo_long["Tipo"].map(
                {
                    "Pago_USD_Anticipo": "Anticipo",
                    "Pago_USD_Entrega": "Entrega FAT",
                    "Pago_USD_SAT": "SAT",
                }
            )
            df_flujo_long = df_flujo_long[["Mes", "Tipo", "Pago_plot"]].copy()
            if include_direction_salaries and float(df_consolidado["Pago_CLP_Sueldos"].sum() or 0.0) > 0:
                df_sueldos_plot = df_consolidado[["Mes", "Pago_CLP_Sueldos"]].copy()
                df_sueldos_plot["Pago_plot"] = scale_clp(df_sueldos_plot["Pago_CLP_Sueldos"])
                df_sueldos_plot["Tipo"] = "Sueldos dirección"
                df_sueldos_plot = df_sueldos_plot[["Mes", "Tipo", "Pago_plot"]]
                df_flujo_long = pd.concat(
                    [df_flujo_long, df_sueldos_plot],
                    ignore_index=True,
                )

            fig_iny = px.bar(
                df_flujo_long,
                x="Mes",
                y="Pago_plot",
                color="Tipo",
                color_discrete_map={
                    "Anticipo": "#0EA5A4",
                    "Entrega FAT": "#6366F1",
                    "SAT": "#F59E0B",
                    "Sueldos dirección": "#64748B",
                },
                labels={
                    "Mes": "Mes del proyecto",
                    "Pago_plot": f"Pago mensual ({axis_unit})",
                    "Tipo": "Hito de pago",
                },
                title=(
                    "Inyección por hito + sueldos de dirección"
                    if include_direction_salaries
                    else "Inyección por hito (Anticipo/FAT/SAT)"
                ),
            )
            fig_iny.add_scatter(
                x=df_flujo_plot["Mes"],
                y=df_flujo_plot["Acum_plot"],
                mode="lines+markers",
                name=line_label,
                yaxis="y2",
                line=dict(color="#0f172a", width=2),
                hovertemplate=f"<b>{line_label}</b>: %{{y:.1f}} {axis_unit}<extra></extra>",
            )
            fig_iny.update_layout(
                barmode="stack",
                height=420,
                margin=dict(l=10, r=10, t=50, b=30),
                yaxis=dict(title=f"Pago mensual ({axis_unit})"),
                yaxis2=dict(
                    title=line_label,
                    overlaying="y",
                    side="right",
                    showgrid=False,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                ),
            )
            fig_iny.update_traces(
                hovertemplate=f"<b>%{{fullData.name}}</b>: %{{y:.1f}} {axis_unit}<extra></extra>",
                selector=dict(type="bar"),
            )
            apply_unified_hover(fig_iny)
            apply_engineering_chart_typography(fig_iny, title_size=20, body_size=13, tick_size=12, legend_size=11)
            fig_iny.update_xaxes(dtick=1)
            for mes, total in zip(df_flujo_plot["Mes"], df_flujo_plot["Total_plot"]):
                fig_iny.add_annotation(
                    x=mes,
                    y=total * 1.05,
                    text=fmt_bar_value(total),
                    showarrow=False,
                    yanchor="bottom",
                    font=dict(color="#111827", size=11),
                )
            st.plotly_chart(
                fig_iny,
                use_container_width=True,
                key=f"{key_prefix}pay_hitos_chart",
            )
            st.markdown(
                """
                <div style="margin:10px 0 12px 0;padding:12px 14px;border-radius:14px;background:#F8FAFC;border:1px solid rgba(148,163,184,.22);">
                    <div style="font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px;">Lectura de hitos</div>
                    <div style="font-size:14px;line-height:1.65;color:#334155;">
                        <strong>Anticipo</strong> → Para iniciar fabricación, compra de materiales y reserva de producción.<br>
                        <strong>Pago FAT / Entrega</strong> → Cuando el equipo está fabricado, probado en taller/fábrica y liberado para despacho.<br>
                        <strong>Pago SAT</strong> → Cuando el equipo está instalado en sitio, comisionado y operando conforme a especificación.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            detail_title = "Detalle mensual por hito"
            detalle_hito_rows = []
            for _, row in df_raw_pagos.iterrows():
                item = str(row.get("Item", "")).strip() or "Sin ítem"
                categoria = str(row.get("Categoria", "")).strip() or "Sin categoría"
                mes_ant = pd.to_numeric(row.get("Mes_Anticipo"), errors="coerce")
                pago_ant = parse_money_usd_robusto(row.get("Pago_USD_Anticipo")) * pagos_scale
                mes_fat = pd.to_numeric(row.get("Mes_Entrega_FAT"), errors="coerce")
                pago_fat = parse_money_usd_robusto(row.get("Pago_USD_Entrega")) * pagos_scale
                mes_sat = pd.to_numeric(row.get("Mes_SAT"), errors="coerce")
                pago_sat = parse_money_usd_robusto(row.get("Pago_USD_SAT")) * pagos_scale

                meses_item = sorted({int(m) for m in [mes_ant, mes_fat, mes_sat] if pd.notna(m)})
                for mes in meses_item:
                    detalle_hito_rows.append(
                        {
                            "Categoria": categoria,
                            "Item": item,
                            "Mes": mes,
                            "Anticipo": scale_usd(pd.Series([pago_ant])).iloc[0] if pd.notna(mes_ant) and int(mes_ant) == mes else 0.0,
                            "Entrega FAT": scale_usd(pd.Series([pago_fat])).iloc[0] if pd.notna(mes_fat) and int(mes_fat) == mes else 0.0,
                            "Pago SAT": scale_usd(pd.Series([pago_sat])).iloc[0] if pd.notna(mes_sat) and int(mes_sat) == mes else 0.0,
                        }
                    )
            detail_df = pd.DataFrame(detalle_hito_rows)
            if include_direction_salaries and not df_dir_mensual.empty:
                df_dir_hito = (
                    df_dir_mensual.groupby("Mes", as_index=False)
                    .agg(Pago_CLP=("Pago_CLP", "sum"))
                    .sort_values("Mes")
                )
                if not df_dir_hito.empty:
                    df_dir_hito["Categoria"] = "Capital humano técnico"
                    df_dir_hito["Item"] = "Capital humano técnico"
                    df_dir_hito["Anticipo"] = 0.0
                    df_dir_hito["Entrega FAT"] = 0.0
                    df_dir_hito["Pago SAT"] = 0.0
                    df_dir_hito["Capital humano técnico"] = scale_clp(df_dir_hito["Pago_CLP"])
                    detail_df = pd.concat(
                        [
                            detail_df,
                            df_dir_hito[["Categoria", "Item", "Mes", "Anticipo", "Entrega FAT", "Pago SAT", "Capital humano técnico"]],
                        ],
                        ignore_index=True,
                    )
            if not detail_df.empty:
                if "Capital humano técnico" not in detail_df.columns:
                    detail_df["Capital humano técnico"] = 0.0
                detail_df["Pago mensual"] = (
                    detail_df["Anticipo"]
                    + detail_df["Entrega FAT"]
                    + detail_df["Pago SAT"]
                    + detail_df["Capital humano técnico"]
                )
                detail_df = detail_df.sort_values(["Mes", "Categoria", "Item"]).copy()
                for col in ["Anticipo", "Entrega FAT", "Pago SAT", "Capital humano técnico", "Pago mensual"]:
                    detail_df[col] = detail_df[col].fillna(0.0)
                detail_df = detail_df[
                    ["Mes", "Categoria", "Item", "Anticipo", "Entrega FAT", "Pago SAT", "Capital humano técnico", "Pago mensual"]
                ]
                for col in ["Anticipo", "Entrega FAT", "Pago SAT", "Capital humano técnico", "Pago mensual"]:
                    detail_df[col] = detail_df[col].map(fmt_pago_detalle)

        elif view_sel.startswith("2"):
            df_item_periodo_plot = df_item_periodo.copy()
            if not df_item_periodo_plot.empty:
                df_item_periodo_plot["Pago_plot"] = scale_usd(df_item_periodo_plot["Pago_USD"])

            if include_direction_salaries and not df_dir_mensual.empty:
                df_dir_item_plot = (
                    df_dir_mensual.groupby("Mes", as_index=False)
                    .agg(Pago_CLP=("Pago_CLP", "sum"))
                )
                df_dir_item_plot["Item"] = "Capital humano técnico"
                df_dir_item_plot["Categoria"] = "Capital humano técnico"
                df_dir_item_plot["Pago_plot"] = scale_clp(df_dir_item_plot["Pago_CLP"])
                df_item_periodo_plot = pd.concat(
                    [
                        df_item_periodo_plot[["Mes", "Item", "Categoria", "Pago_plot"]],
                        df_dir_item_plot[["Mes", "Item", "Categoria", "Pago_plot"]],
                    ],
                    ignore_index=True,
                )

            if df_item_periodo_plot.empty:
                st.info("No hay pagos disponibles para construir la inyección por ítem.")
            else:
                df_item_total = df_consolidado[["Mes", "Total_USD"]].copy().sort_values("Mes")
                df_item_total["Total_plot"] = scale_usd(df_item_total["Total_USD"])
                df_item_total["Acum_plot"] = df_item_total["Total_plot"].cumsum()
                item_color_map_plot = dict(item_color_map)
                item_color_map_plot["Capital humano técnico"] = "#0F4C81"
                fig_item_iny = px.bar(
                    df_item_periodo_plot,
                    x="Mes",
                    y="Pago_plot",
                    color="Item",
                    color_discrete_map=item_color_map_plot,
                    labels={
                        "Mes": "Mes del proyecto",
                        "Pago_plot": f"Pago mensual ({axis_unit})",
                        "Item": "Ítem",
                    },
                    title=(
                        "Inyección por ítem + capital humano técnico"
                        if include_direction_salaries
                        else "Inyección por ítem (Anticipo/FAT/SAT)"
                    ),
                )
                fig_item_iny.add_scatter(
                    x=df_item_total["Mes"],
                    y=df_item_total["Acum_plot"],
                    mode="lines+markers",
                    name=line_label,
                    yaxis="y2",
                    line=dict(color="#0f172a", width=2),
                    hovertemplate=f"<b>{line_label}</b>: %{{y:.1f}} {axis_unit}<extra></extra>",
                )
                fig_item_iny.update_layout(
                    barmode="stack",
                    height=420,
                    margin=dict(l=10, r=10, t=50, b=92),
                    yaxis=dict(title=f"Pago mensual ({axis_unit})"),
                    yaxis2=dict(
                        title=line_label,
                        overlaying="y",
                        side="right",
                        showgrid=False,
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.20,
                        xanchor="center",
                        x=0.5,
                        title=dict(text=""),
                        font=dict(size=11),
                        entrywidth=150,
                        entrywidthmode="pixels",
                    ),
                    hoverlabel=dict(bgcolor="white"),
                )
                fig_item_iny.update_traces(
                    hovertemplate=f"<b>%{{fullData.name}}</b>: %{{y:.1f}} {axis_unit}<extra></extra>",
                    selector=dict(type="bar"),
                )
                apply_unified_hover(fig_item_iny)
                apply_engineering_chart_typography(fig_item_iny, title_size=20, body_size=13, tick_size=12, legend_size=11)
                fig_item_iny.update_xaxes(dtick=1)
                for mes, total in zip(df_item_total["Mes"], df_item_total["Total_plot"]):
                    fig_item_iny.add_annotation(
                        x=mes,
                        y=total * 1.05,
                        text=fmt_bar_value(total),
                        showarrow=False,
                        yanchor="bottom",
                        font=dict(color="#111827", size=11),
                    )
                st.plotly_chart(
                    fig_item_iny,
                    use_container_width=True,
                    key=f"{key_prefix}pay_items_chart",
                )
                detail_title = "Detalle mensual por ítem"
                detail_df = df_item_periodo_plot.sort_values(["Mes", "Categoria", "Item"]).copy()
                detail_df["Pago mensual"] = detail_df["Pago_plot"].map(fmt_pago_detalle)
                detail_df = detail_df[["Mes", "Categoria", "Item", "Pago mensual"]]

        elif view_sel.startswith("3"):
            if df_item_periodo.empty:
                st.info("No hay pagos disponibles para construir el total por período.")
            else:
                df_cat_periodo = (
                    df_item_periodo.groupby(["Mes", "Categoria"], as_index=False)
                    .agg(Pago_USD=("Pago_USD", "sum"))
                )
                df_cat_periodo["Pago_plot"] = scale_usd(df_cat_periodo["Pago_USD"])
                df_total = (
                    df_cat_periodo.groupby("Mes", as_index=False)
                    .agg(Total_USD=("Pago_USD", "sum"))
                    .sort_values("Mes")
                )
                df_total["Total_plot"] = scale_usd(df_total["Total_USD"])
                fig_cat_total = px.bar(
                    df_cat_periodo,
                    x="Mes",
                    y="Pago_plot",
                    color="Categoria",
                    color_discrete_map=CAT_COLOR_MAP,
                    labels={
                        "Mes": "Mes del proyecto",
                        "Pago_plot": f"Pago mensual ({axis_unit})",
                        "Categoria": "Categoría",
                    },
                    title="Total por período (Anticipo/FAT/SAT) por categoría",
                )
                fig_cat_total.update_layout(
                    barmode="stack",
                    height=420,
                    margin=dict(l=10, r=10, t=50, b=30),
                    yaxis=dict(title=f"Pago mensual ({axis_unit})"),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                    ),
                )
                fig_cat_total.update_traces(
                    hovertemplate=f"<b>%{{fullData.name}}</b>: %{{y:.1f}} {axis_unit}<extra></extra>",
                    selector=dict(type="bar"),
                )
                apply_unified_hover(fig_cat_total)
                apply_engineering_chart_typography(fig_cat_total, title_size=20, body_size=13, tick_size=12, legend_size=11)
                fig_cat_total.update_xaxes(dtick=1)
                for mes, total in zip(df_total["Mes"], df_total["Total_plot"]):
                    fig_cat_total.add_annotation(
                        x=mes,
                        y=total * 1.05,
                        text=fmt_bar_value(total),
                        showarrow=False,
                        yanchor="bottom",
                        font=dict(color="#111827", size=11),
                    )
                st.plotly_chart(
                    fig_cat_total,
                    use_container_width=True,
                    key=f"{key_prefix}pay_categoria_chart",
                )
                detail_title = "Detalle mensual por categoría"
                detail_df = df_cat_periodo.sort_values(["Mes", "Categoria"]).copy()
                detail_df["Pago mensual"] = detail_df["Pago_plot"].map(fmt_pago_detalle)
                detail_df = detail_df[["Mes", "Categoria", "Pago mensual"]]

        if not detail_df.empty:
            with st.expander(f"Ver {detail_title.lower()}", expanded=False):
                st.dataframe(
                    style_engineering_table(detail_df, header_color="#4F5D6F", row_color="#F7F4EF"),
                    hide_index=True,
                    use_container_width=True,
                    height=min(420, 36 + (len(detail_df) + 1) * 35),
                )

    except Exception as e:
        st.error(f"No se pudo construir el análisis de pagos: {e}")


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_hitos_owner_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df = read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def render_hitos_owner_freeze_chart(hitos_url: str, key_prefix: str = ""):
    st.markdown("---")
    st.markdown(
        '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Ruta de Freezes e Hitos por Owner</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:0 0 10px 0;">Visual de coordinación para seguir decisiones de freeze, secuencia de entrega y responsable por mes objetivo.</div>',
        unsafe_allow_html=True,
    )
    try:
        df_hitos = load_hitos_owner_data(hitos_url, refresh_nonce=data_refresh_nonce).copy()
        required_cols = ["Hito_ID", "Hito", "Owner", "Mes objetivo", "Depende de"]
        missing_cols = [c for c in required_cols if c not in df_hitos.columns]
        if missing_cols:
            st.error(f"Faltan columnas en la hoja de hitos: {missing_cols}")
            return

        df_hitos["Mes_objetivo_i"] = pd.to_numeric(df_hitos["Mes objetivo"], errors="coerce")
        df_hitos["Owner"] = df_hitos["Owner"].fillna("Sin owner").astype(str).str.strip()
        df_hitos["Hito"] = df_hitos["Hito"].fillna("Sin hito").astype(str).str.strip()
        df_hitos["Depende de"] = df_hitos["Depende de"].fillna("-").astype(str).str.strip()
        df_hitos = df_hitos.dropna(subset=["Mes_objetivo_i"]).copy()
        if df_hitos.empty:
            st.info("No hay hitos con mes objetivo válido.")
            return

        owner_order = (
            df_hitos.groupby("Owner", as_index=False)["Mes_objetivo_i"]
            .min()
            .sort_values(["Mes_objetivo_i", "Owner"])["Owner"]
            .tolist()
        )
        owner_palette = {
            owner: PX_COLORS[idx % len(PX_COLORS)]
            for idx, owner in enumerate(owner_order)
        }
        df_hitos["Tipo_hito"] = np.where(
            df_hitos["Hito"].str.contains("freeze", case=False, na=False),
            "Freeze",
            "Hito",
        )
        df_hitos = df_hitos.sort_values(["Mes_objetivo_i", "Owner", "Hito_ID"])

        fig_hitos_owner = px.scatter(
            df_hitos,
            x="Mes_objetivo_i",
            y="Owner",
            color="Owner",
            symbol="Tipo_hito",
            color_discrete_map=owner_palette,
            symbol_map={"Freeze": "diamond", "Hito": "circle"},
            text="Hito_ID",
            hover_data={
                "Hito_ID": True,
                "Hito": True,
                "Owner": True,
                "Mes objetivo": True,
                "Depende de": True,
                "Tipo_hito": True,
            },
            labels={
                "Mes_objetivo_i": "Mes objetivo",
                "Owner": "Owner",
                "Tipo_hito": "Tipo",
            },
            title="Mapa de ownership y secuencia crítica",
        )
        fig_hitos_owner.update_traces(
            marker=dict(size=18, line=dict(width=1.5, color="white")),
            textposition="top center",
            cliponaxis=False,
        )

        milestone_pos = {
            str(row["Hito_ID"]).strip(): (float(row["Mes_objetivo_i"]), str(row["Owner"]))
            for _, row in df_hitos.iterrows()
        }
        for _, row in df_hitos.iterrows():
            dep = str(row.get("Depende de", "")).strip()
            if not dep or dep == "-":
                continue
            for dep_id in [d.strip() for d in dep.split(",") if d.strip()]:
                if dep_id not in milestone_pos:
                    continue
                x0, y0 = milestone_pos[dep_id]
                x1, y1 = float(row["Mes_objetivo_i"]), str(row["Owner"])
                fig_hitos_owner.add_trace(
                    go.Scatter(
                        x=[x0, x1],
                        y=[y0, y1],
                        mode="lines",
                        line=dict(color="rgba(100,116,139,.45)", width=1.6, dash="dot"),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

        max_month = int(df_hitos["Mes_objetivo_i"].max())
        for month in range(1, max_month + 1):
            fig_hitos_owner.add_vline(
                x=month,
                line_width=1,
                line_dash="dot",
                line_color="rgba(203,213,225,.65)",
            )

        fig_hitos_owner.update_layout(
            height=460,
            margin=dict(l=70, r=20, t=96, b=34),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            title=dict(
                x=0,
                xanchor="left",
                y=0.97,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.00,
                xanchor="left",
                x=0,
                title=dict(text=""),
            ),
            hoverlabel=dict(bgcolor="white"),
        )
        fig_hitos_owner.update_xaxes(
            title="Mes objetivo",
            dtick=1,
            range=[0.5, max_month + 0.7],
            showgrid=False,
            zeroline=False,
        )
        fig_hitos_owner.update_yaxes(
            title=None,
            categoryorder="array",
            categoryarray=owner_order[::-1],
            showgrid=False,
        )
        apply_engineering_chart_typography(fig_hitos_owner, title_size=20, body_size=13, tick_size=12, legend_size=11)
        st.plotly_chart(
            fig_hitos_owner,
            use_container_width=True,
            key=f"{key_prefix}hitos_owner_chart",
        )
    except Exception as e:
        st.error(f"No se pudo construir la ruta de hitos por owner: {e}")


@st.cache_data(show_spinner=False, ttl=REMOTE_FETCH_TTL_SECONDS, persist="disk")
def load_riesgo_data(url: str, refresh_nonce: int = 0) -> pd.DataFrame:
    df = read_remote_csv(url, refresh_nonce=refresh_nonce, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def render_riesgo_matrix_chart(riesgo_url: str, key_prefix: str = ""):
    st.markdown("---")
    st.markdown(
        '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Mapa de Riesgos Críticos del CAPEX</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:0 0 10px 0;">Matriz de criticidad para visualizar probabilidad, impacto y owner responsable sobre los riesgos activos del escalamiento.</div>',
        unsafe_allow_html=True,
    )
    try:
        df_riesgo = load_riesgo_data(riesgo_url, refresh_nonce=data_refresh_nonce).copy()
        required_cols = [
            "Riesgo_ID",
            "Riesgo",
            "Probabilidad(1-5)",
            "Impacto(1-5)",
            "Severidad(PxI)",
            "Owner",
            "Relacionado Hito",
            "Estado",
        ]
        missing_cols = [c for c in required_cols if c not in df_riesgo.columns]
        if missing_cols:
            st.error(f"Faltan columnas en la hoja de riesgo: {missing_cols}")
            return

        df_riesgo = df_riesgo.dropna(subset=["Riesgo_ID"]).copy()
        if df_riesgo.empty:
            st.info("No hay riesgos válidos para mostrar.")
            return

        for col in ["Probabilidad(1-5)", "Impacto(1-5)", "Severidad(PxI)"]:
            df_riesgo[col] = pd.to_numeric(df_riesgo[col], errors="coerce")
        df_riesgo = df_riesgo.dropna(subset=["Probabilidad(1-5)", "Impacto(1-5)", "Severidad(PxI)"]).copy()
        df_riesgo["Owner"] = df_riesgo["Owner"].fillna("Sin owner").astype(str).str.strip()
        df_riesgo["Estado"] = df_riesgo["Estado"].fillna("Sin estado").astype(str).str.strip()
        df_riesgo["Relacionado Hito"] = df_riesgo["Relacionado Hito"].fillna("-").astype(str).str.strip()
        df_riesgo["Riesgo_label"] = df_riesgo["Riesgo_ID"].astype(str).str.strip()
        df_riesgo["Reserva USD"] = df_riesgo.get("Reserva USD", "").fillna("$0").astype(str).str.strip()
        df_riesgo["Prob_plot"] = df_riesgo["Probabilidad(1-5)"].round(2)
        df_riesgo["Imp_plot"] = df_riesgo["Impacto(1-5)"].round(2)

        total_riesgos = int(len(df_riesgo))
        severidad_max = float(df_riesgo["Severidad(PxI)"].max() or 0.0)
        owner_top = (
            df_riesgo.groupby("Owner", as_index=False)
            .agg(Riesgos=("Riesgo_ID", "count"), Severidad_max=("Severidad(PxI)", "max"))
            .sort_values(["Riesgos", "Severidad_max"], ascending=[False, False])
            .iloc[0]["Owner"]
        )
        risk_kpi_cols = st.columns(3)
        with risk_kpi_cols[0]:
            kpi_card("Riesgos activos", f"{total_riesgos}", "Eventos abiertos cargados en la matriz.", variant="palette_gray")
        with risk_kpi_cols[1]:
            kpi_card("Severidad máxima", f"{severidad_max:.0f}", "Puntaje PxI más alto dentro del bloque.", variant="palette_coral")
        with risk_kpi_cols[2]:
            kpi_card("Owner más expuesto", str(owner_top), "Responsable con mayor concentración de riesgos.", variant="palette_teal")

        fig_riesgo = px.scatter(
            df_riesgo,
            x="Prob_plot",
            y="Imp_plot",
            color="Severidad(PxI)",
            size="Severidad(PxI)",
            size_max=38,
            hover_data={
                "Riesgo_ID": True,
                "Riesgo": True,
                "Owner": True,
                "Relacionado Hito": True,
                "Estado": True,
                "Probabilidad(1-5)": True,
                "Impacto(1-5)": True,
                "Severidad(PxI)": True,
            },
            color_continuous_scale=["#7FA8A4", "#D9A766", "#D7605E"],
            labels={
                "Probabilidad(1-5)": "Probabilidad",
                "Impacto(1-5)": "Impacto",
                "Severidad(PxI)": "Severidad",
            },
            title="Criticidad por riesgo y owner",
        )
        fig_riesgo.update_traces(
            marker=dict(line=dict(width=1.6, color="white"), opacity=0.94),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "Owner: %{customdata[2]}<br>"
                "Hito: %{customdata[3]}<br>"
                "Estado: %{customdata[4]}<br>"
                "Probabilidad: %{x:.0f} / 5<br>"
                "Impacto: %{y:.0f} / 5<br>"
                "Severidad: %{marker.size:.0f}<extra></extra>"
            ),
            customdata=np.stack(
                [
                    df_riesgo["Riesgo_ID"],
                    df_riesgo["Riesgo"],
                    df_riesgo["Owner"],
                    df_riesgo["Relacionado Hito"],
                    df_riesgo["Estado"],
                ],
                axis=-1,
            ),
        )
        label_offsets = [(0, -18), (24, -8), (-24, -8), (0, 18), (26, 14), (-26, 14)]
        df_riesgo["_label_rank"] = df_riesgo.groupby(["Prob_plot", "Imp_plot"]).cumcount()
        for _, row in df_riesgo.iterrows():
            dx, dy = label_offsets[int(row["_label_rank"]) % len(label_offsets)]
            fig_riesgo.add_annotation(
                x=float(row["Prob_plot"]),
                y=float(row["Imp_plot"]),
                text=str(row["Riesgo_label"]),
                showarrow=False,
                xshift=dx,
                yshift=dy,
                font=dict(size=11, color="#0f172a"),
                bgcolor="rgba(255,255,255,0.88)",
                bordercolor="rgba(148,163,184,0.35)",
                borderwidth=1,
                borderpad=2,
            )
        fig_riesgo.add_shape(type="rect", x0=0.5, x1=2.5, y0=0.5, y1=2.5, fillcolor="rgba(127,168,164,.10)", line=dict(width=0), layer="below")
        fig_riesgo.add_shape(type="rect", x0=2.5, x1=4.0, y0=2.0, y1=4.0, fillcolor="rgba(217,167,102,.10)", line=dict(width=0), layer="below")
        fig_riesgo.add_shape(type="rect", x0=3.0, x1=5.5, y0=3.0, y1=5.5, fillcolor="rgba(215,96,94,.12)", line=dict(width=0), layer="below")
        fig_riesgo.add_annotation(x=1.2, y=1.2, text="Zona controlable", showarrow=False, font=dict(size=11, color="#64748B"))
        fig_riesgo.add_annotation(x=3.05, y=2.3, text="Atención prioritaria", showarrow=False, font=dict(size=11, color="#9A6B16"))
        fig_riesgo.add_annotation(x=4.15, y=4.8, text="Riesgo crítico", showarrow=False, font=dict(size=11, color="#B91C1C"))
        fig_riesgo.update_layout(
            height=520,
            margin=dict(l=40, r=40, t=76, b=36),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(title="Severidad"),
            title=dict(x=0, xanchor="left"),
            hoverlabel=dict(bgcolor="white"),
        )
        fig_riesgo.update_xaxes(dtick=1, range=[0.7, 5.3], showgrid=True, gridcolor="rgba(203,213,225,.55)", zeroline=False)
        fig_riesgo.update_yaxes(dtick=1, range=[0.7, 5.3], showgrid=True, gridcolor="rgba(203,213,225,.55)", zeroline=False)
        apply_engineering_chart_typography(fig_riesgo, title_size=20, body_size=13, tick_size=12, legend_size=11)
        st.plotly_chart(
            fig_riesgo,
            use_container_width=True,
            key=f"{key_prefix}riesgo_matrix_chart",
        )

        detail_cols = [
            "Riesgo_ID",
            "Categoría",
            "Riesgo",
            "Owner",
            "Relacionado Hito",
            "Estado",
            "Severidad(PxI)",
            "Trigger",
            "Mitigación",
            "Plan B",
            "Reserva USD",
        ]
        df_riesgo_table = (
            df_riesgo[detail_cols]
            .rename(
                columns={
                    "Categoría": "Categoría",
                    "Owner": "Owner",
                    "Relacionado Hito": "Hito",
                    "Estado": "Estado",
                    "Severidad(PxI)": "Severidad",
                    "Trigger": "Trigger",
                    "Mitigación": "Mitigación",
                    "Plan B": "Plan B",
                    "Reserva USD": "Reserva",
                }
            )
            .sort_values(["Severidad", "Riesgo_ID"], ascending=[False, True])
        )
        with st.expander("Ver detalle operativo de riesgos", expanded=False):
            st.dataframe(
                style_engineering_table(df_riesgo_table, header_color="#4F5D6F", row_color="#F7F4EF"),
                hide_index=True,
                use_container_width=True,
                height=min(420, 36 + (len(df_riesgo_table) + 1) * 35),
            )
    except Exception as e:
        st.error(f"No se pudo construir la matriz de riesgos: {e}")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Parámetros")
capex_url = CAPEX_CSV_URL_DEFAULT

st.sidebar.markdown("---")
st.sidebar.caption(
    "El dashboard se alimenta directamente de Google Sheets y recalcula "
    "montos, tipo de cambio y gráficos en tiempo real."
)
if "data_refresh_nonce" not in st.session_state:
    st.session_state["data_refresh_nonce"] = 0
if st.session_state.get("gantt_project_source_version") != GANTT_PROJECT_SOURCE_VERSION:
    load_project_gantt_data.clear()
    st.session_state["gantt_project_source_version"] = GANTT_PROJECT_SOURCE_VERSION
if st.sidebar.button("🔁 Actualizar datos desde URL"):
    for key in (
        "inputs_gantt_fase",
        "inputs_gantt_linea",
        "inputs_gantt_estado",
        "inputs_gantt_mode",
        "inputs_gantt_color",
    ):
        if key in st.session_state:
            st.session_state[f"{key}__sticky"] = st.session_state[key]
    fetch_remote_file_bytes.clear()
    load_project_gantt_data.clear()
    st.session_state["data_refresh_nonce"] += 1
    st.rerun()

# =========================
# DATOS
# =========================
data_refresh_nonce = int(st.session_state.get("data_refresh_nonce", 0))

bootstrap_data_error = None
try:
    df_capex_base = load_capex_data(capex_url, refresh_nonce=data_refresh_nonce)
except Exception as exc:
    bootstrap_data_error = str(exc)
    df_capex_base = pd.DataFrame(
        columns=["Monto_USD", "Monto_CLP", "Categoria", "Participacion_pct", "Item"]
    )

if bootstrap_data_error:
    st.error("No se pudieron cargar los datos base del dashboard desde Google Sheets.")
    st.caption(
        "El servicio quedó operativo, pero la fuente remota no respondió correctamente. "
        "Revisa la conectividad de Render o la publicación de la hoja."
    )
    st.code(bootstrap_data_error)
    st.stop()

capex_total_usd_base = float(df_capex_base["Monto_USD"].sum() or 0.0) if "Monto_USD" in df_capex_base.columns else 0.0
fx_base = 925.0
global_fx_value = st.sidebar.number_input(
    "Tipo de cambio",
    min_value=100.0,
    max_value=5000.0,
    value=925.0,
    step=10.0,
    help="Valor base global CLP/USD. Se usa como referencia inicial para los cálculos y parámetros ligados al dólar.",
)
fx_used = global_fx_value if np.isfinite(global_fx_value) and global_fx_value > 0 else fx_base
df_capex = df_capex_base.copy()
if np.isfinite(fx_used) and fx_used > 0:
    df_capex["Monto_CLP"] = df_capex["Monto_USD"] * fx_used
capex_total_usd = capex_total_usd_base
capex_total_clp = float(df_capex["Monto_CLP"].sum() or 0.0) if "Monto_CLP" in df_capex.columns else 0.0
tipo_cambio_implicito = fx_used
pagos_scale = 1.0

if not np.isfinite(tipo_cambio_implicito) or tipo_cambio_implicito <= 0:
    st.error(
        "No se pudo calcular un tipo de cambio implícito confiable. "
        "Revisa que la hoja tenga montos en USD válidos."
    )
    st.stop()

if not 500 <= tipo_cambio_implicito <= 1200:
    st.warning(
        f"El tipo de cambio implícito ({tipo_cambio_implicito:,.0f} CLP/US$) "
        "está fuera del rango esperado para un proyecto piloto. "
        "Verifica los datos cargados."
    )

df_cat = (
    df_capex
    .groupby("Categoria", as_index=False)
    .agg(
        Monto_USD=("Monto_USD", "sum"),
        Monto_CLP=("Monto_CLP", "sum"),
        Participacion_sum=("Participacion_pct", "sum"),
        Items=("Item", "count"),
    )
    .sort_values("Monto_CLP", ascending=False)
    .reset_index(drop=True)
)

item_category_lookup = (
    df_capex[["Item", "Categoria"]]
    .drop_duplicates(subset=["Item"])
    .set_index("Item")["Categoria"]
    .to_dict()
)
item_color_map = build_item_color_map(item_category_lookup)

# columnas auxiliares para gráficos en MM CLP
df_cat["Monto_CLP_MM"] = df_cat["Monto_CLP"] / 1e6
df_capex["Monto_CLP_MM"] = df_capex["Monto_CLP"] / 1e6

try:
    df_direccion = load_director_general_data(capex_url, refresh_nonce=data_refresh_nonce)
    direccion_error = None
except Exception as exc:
    df_direccion = pd.DataFrame(columns=["Cargo", "Meses", "Costo empresa mensual", "Total"])
    direccion_error = str(exc)

direccion_total_clp = float(df_direccion["Total"].sum() or 0.0) if "Total" in df_direccion.columns else 0.0
capex_total_integrado_clp = capex_total_clp + direccion_total_clp
capex_total_real_clp = load_capex_total_real_clp(capex_url, refresh_nonce=data_refresh_nonce)
capex_total_integrado_real_clp = float(capex_total_real_clp or capex_total_clp) + direccion_total_clp

# =========================
# HEADER
# =========================
render_inputs_main_hero()

total_items = len(df_capex)
total_categorias = df_cat["Categoria"].nunique()
cat_top = df_cat.iloc[0]["Categoria"] if total_categorias > 0 else "-"
cat_top_pct = df_cat.iloc[0]["Participacion_sum"] * 100 if total_categorias > 0 else 0

# =========================
# ESTILO KPI CARDS  (SIEMPRE ANTES DE USAR kpi_card)
# =========================
st.markdown(
    """
    <style>
    .kpi-row {
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: #F9FAFB;
        border-radius: 0.9rem;
        padding: 0.95rem 1.25rem 0.8rem 1.25rem;
        min-height: 116px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
    }
    .kpi-label {
        font-size: 0.80rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 0.15rem;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
        line-height: 1.1;
        margin-bottom: 0.15rem;
        word-break: break-word;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #9CA3AF;
        margin-top: 0.15rem;
    }
    .kpi-card.kpi-card-sky {
        background: linear-gradient(90deg, #EFF8FF 0%, #DFF4FF 42%, #C6ECFF 100%);
    }
    .kpi-card.kpi-card-green {
        background: linear-gradient(90deg, #ECFDF5 0%, #D1FAE5 42%, #A7F3D0 100%);
        border: 1px solid rgba(22,163,74,.28);
    }
    .kpi-card.kpi-card-palette-gray {
        background: linear-gradient(90deg, #D0D0D0 0%, #B8B8B8 100%);
        border: 1px solid rgba(120,120,120,.24);
    }
    .kpi-card.kpi-card-palette-coral {
        background: linear-gradient(90deg, #E36968 0%, #D85E5E 100%);
        border: 1px solid rgba(190,84,84,.24);
    }
    .kpi-card.kpi-card-palette-ochre {
        background: linear-gradient(90deg, #E0AE68 0%, #D9A766 100%);
        border: 1px solid rgba(181,133,56,.24);
    }
    .kpi-card.kpi-card-palette-teal {
        background: linear-gradient(90deg, #86AEAB 0%, #7FA8A4 100%);
        border: 1px solid rgba(76,129,124,.24);
    }
    .kpi-card.kpi-card-palette-slate {
        background: linear-gradient(90deg, #586271 0%, #4F5D6F 100%);
        border: 1px solid rgba(55,65,81,.24);
    }
    .kpi-card.kpi-card-palette-coral .kpi-label,
    .kpi-card.kpi-card-palette-coral .kpi-value,
    .kpi-card.kpi-card-palette-coral .kpi-sub,
    .kpi-card.kpi-card-palette-slate .kpi-label,
    .kpi-card.kpi-card-palette-slate .kpi-value,
    .kpi-card.kpi-card-palette-slate .kpi-sub {
        color: #F8FAFC;
    }
    .kpi-card.kpi-card-compact {
        min-height: 76px;
        border-radius: 0.55rem;
        padding: 0.58rem 0.78rem 0.52rem 0.78rem;
        box-shadow: 0 3px 8px rgba(15, 23, 42, 0.045);
    }
    .kpi-card.kpi-card-compact .kpi-label {
        font-size: 0.64rem;
        letter-spacing: .11em;
        margin-bottom: 0.08rem;
    }
    .kpi-card.kpi-card-compact .kpi-value {
        font-size: 1.35rem;
        line-height: 1.05;
        margin-bottom: 0.08rem;
    }
    .kpi-card.kpi-card-compact .kpi-sub {
        font-size: 0.68rem;
        line-height: 1.25;
        margin-top: 0.05rem;
    }
    .kpi-card.kpi-card-compact.kpi-card-palette-coral {
        background: linear-gradient(90deg, rgba(215,96,94,.82) 0%, rgba(215,96,94,.74) 100%);
    }
    .kpi-card.kpi-card-compact.kpi-card-palette-ochre {
        background: linear-gradient(90deg, rgba(217,167,102,.72) 0%, rgba(217,167,102,.64) 100%);
    }
    .kpi-card.kpi-card-compact.kpi-card-palette-teal {
        background: linear-gradient(90deg, rgba(127,168,164,.62) 0%, rgba(127,168,164,.54) 100%);
    }
    .kpi-card.kpi-card-compact.kpi-card-palette-slate {
        background: linear-gradient(90deg, rgba(79,93,111,.88) 0%, rgba(79,93,111,.80) 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def kpi_card(title: str, value: str, subtitle: str = "", variant: str = "default", compact: bool = False):
    """Renderiza una tarjeta KPI con título, valor y subtítulo."""
    card_class = "kpi-card"
    if compact:
        card_class += " kpi-card-compact"
    if variant == "sky":
        card_class += " kpi-card-sky"
    elif variant == "green":
        card_class += " kpi-card-green"
    elif variant == "palette_gray":
        card_class += " kpi-card-palette-gray"
    elif variant == "palette_coral":
        card_class += " kpi-card-palette-coral"
    elif variant == "palette_ochre":
        card_class += " kpi-card-palette-ochre"
    elif variant == "palette_teal":
        card_class += " kpi-card-palette-teal"
    elif variant == "palette_slate":
        card_class += " kpi-card-palette-slate"
    html = f"""
    <div class="{card_class}">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_resumen_content(
    key_prefix: str = "",
    include_export: bool = True,
    include_direction_item: bool = False,
):
    resumen_title = (
        "Estructura de Inversión y Ejecución requerida – Piloto 80 kW"
        if include_direction_item
        else "CAPEX Técnico – Piloto 80 kW"
    )
    st.markdown(
        f'<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">{resumen_title}</div>',
        unsafe_allow_html=True,
    )

    df_items_tot = (
        df_capex
        .groupby("Item", as_index=False)
        .agg(Total_CLP=("Monto_CLP", "sum"))
    )
    df_items_tot = df_items_tot.merge(
        pd.DataFrame(list(item_category_lookup.items()), columns=["Item", "Categoria"]),
        on="Item",
        how="left",
    )
    if include_direction_item and direccion_total_clp > 0:
        df_items_tot = pd.concat(
            [
                df_items_tot,
                pd.DataFrame(
                    [
                        {
                            "Item": "Capital Humano",
                            "Total_CLP": direccion_total_clp,
                            "Categoria": "Dirección técnica",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    capex_total_clp_calc = (
        capex_total_integrado_clp if include_direction_item else df_items_tot["Total_CLP"].sum()
    )
    df_items_tot["Pct_total"] = df_items_tot["Total_CLP"] / capex_total_clp_calc
    df_items_tot["Total_MM"] = df_items_tot["Total_CLP"] / 1e6
    df_items_tot["Texto"] = df_items_tot.apply(
        lambda r: f"{r['Total_MM']:.1f} MM / {r['Pct_total']*100:.1f}%",
        axis=1
    )
    df_items_tot = df_items_tot.sort_values("Total_CLP", ascending=False)

    item_total_title = (
        "CAPEX + Capital Humano por ítem (monto total y % del total integrado)"
        if include_direction_item
        else "CAPEX por ítem (monto total y % del CAPEX)"
    )

    st.markdown(
        f'<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:0 0 10px 0;">{item_total_title}</div>',
        unsafe_allow_html=True,
    )
    resumen_color_map = {**CAT_COLOR_MAP, "Dirección técnica": HUMAN_CAPITAL_SUMMARY_COLOR}

    if include_direction_item:
        fig_item_total = px.scatter(
            df_items_tot,
            x="Total_MM",
            y="Item",
            color="Categoria",
            color_discrete_map=resumen_color_map,
            size="Total_MM",
            size_max=34,
            text="Texto",
            labels={"Total_MM": "Monto (millones de CLP)", "Item": "Ítem", "Categoria": "Categoría técnica"},
            title=None,
        )
        for _, row in df_items_tot.iterrows():
            fig_item_total.add_shape(
                type="line",
                x0=0,
                x1=row["Total_MM"],
                y0=row["Item"],
                y1=row["Item"],
                xref="x",
                yref="y",
                line=dict(
                    color=resumen_color_map.get(row["Categoria"], "#94A3B8"),
                    width=8,
                ),
                layer="below",
            )
        fig_item_total.update_traces(
            mode="markers+text",
            textposition="middle right",
            textfont_size=11,
            marker=dict(line=dict(color="rgba(255,255,255,0.92)", width=1.6), opacity=0.96),
            hovertemplate="<b>%{y}</b><br>Categoría técnica: %{fullData.name}<br>Monto: %{x:.1f} MM CLP<extra></extra>",
        )
        fig_item_total.update_layout(
            xaxis_title="Monto total (millones de CLP)",
            yaxis_title="",
            margin=dict(l=10, r=10, t=40, b=110),
            showlegend=True,
            legend_title_text="Categoría técnica",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.18,
                xanchor="left",
                x=0,
            ),
            height=460,
        )
    else:
        fig_item_total = px.bar(
            df_items_tot,
            x="Total_MM",
            y="Item",
            orientation="h",
            text="Texto",
            color="Categoria",
            color_discrete_map=resumen_color_map,
            labels={"Total_MM": "Monto (millones de CLP)", "Item": "Ítem", "Categoria": "Categoría técnica"},
            title=None,
        )
        fig_item_total.update_traces(
            textposition="outside",
            textfont=dict(size=11, color="#334155"),
            cliponaxis=False,
            marker=dict(line=dict(color="rgba(255,255,255,0.96)", width=1.6)),
            hovertemplate="<b>%{y}</b><br>Categoría técnica: %{fullData.name}<br>Monto: %{x:.1f} MM CLP<extra></extra>",
        )
        fig_item_total.update_layout(
            xaxis_title="Monto total (millones de CLP)",
            yaxis_title="",
            margin=dict(l=10, r=34, t=32, b=110),
            showlegend=True,
            legend_title_text="Categoría técnica",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.18,
                xanchor="left",
                x=0,
            ),
            height=440,
            bargap=0.34,
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig_item_total.update_xaxes(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.18)",
            zeroline=False,
            ticksuffix=" MM",
        )
        fig_item_total.update_yaxes(showgrid=False)
    apply_engineering_chart_typography(fig_item_total, title_size=20, body_size=13, tick_size=12, legend_size=12)
    fig_item_total.update_layout(hovermode="closest")
    fig_item_total.update_xaxes(showspikes=False)
    st.plotly_chart(fig_item_total, use_container_width=True)
    st.session_state["fig_item_total"] = fig_item_total

    if include_direction_item:
        render_hitos_owner_freeze_chart(
            HITOS_OWNER_CSV_URL_DEFAULT,
            key_prefix=key_prefix,
        )

    st.markdown(
        '<div class="eng-body-title" style="font-size:18px;font-weight:700;color:#0f172a;margin:8px 0 12px 0;">Secuencia de Ejecución del CAPEX y Desarrollo del Proyecto</div>',
        unsafe_allow_html=True,
    )
    if "Mes_inicio" in df_capex.columns and "Mes_termino" in df_capex.columns:
        df_timeline = df_capex.dropna(subset=["Mes_inicio", "Mes_termino"]).copy()
        if not df_timeline.empty:
            df_timeline["Mes_inicio"] = pd.to_numeric(df_timeline["Mes_inicio"], errors="coerce")
            df_timeline["Mes_termino"] = pd.to_numeric(df_timeline["Mes_termino"], errors="coerce")
            df_timeline = df_timeline.dropna(subset=["Mes_inicio", "Mes_termino"])
            if not df_timeline.empty:
                df_timeline_cat = (
                    df_timeline
                    .groupby(["Categoria", "Item"], as_index=False)
                    .agg(
                        Mes_inicio=("Mes_inicio", "min"),
                        Mes_termino=("Mes_termino", "max"),
                        Monto_CLP=("Monto_CLP", "sum"),
                        Monto_USD=("Monto_USD", "sum"),
                    )
                )
                items_todos = sorted(df_timeline_cat["Item"].unique().tolist())
                opciones = ["Todas"] + items_todos

                def _fmt_item(opt: str) -> str:
                    if opt == "Todas":
                        return "🔴 Todas"
                    mapa = {
                        "Desarrollo Tecnológico": "🧪 Desarrollo Tecnológico",
                        "Componentes Mecánicos": "⚙️ Componentes Mecánicos",
                        "Sistema Eléctrico y Control": "🔌 Sistema Eléctrico y Control",
                        "Obras Civiles": "🏗️ Obras Civiles",
                        "Montaje y Logística": "📦 Montaje y Logística",
                        "Ensayos y Certificación": "📏 Ensayos y Certificación",
                        "Contingencias y Administración": "🧾 Contingencias y Administración",
                    }
                    return mapa.get(opt, opt)

                item_sel = render_single_select_pills_compat(
                    "Filtrar por ítem:",
                    options=opciones,
                    default="Todas",
                    key=f"{key_prefix}timeline_radio_item_cat",
                    format_func=_fmt_item,
                )
                df_tl_plot = (
                    df_timeline_cat.copy()
                    if item_sel == "Todas"
                    else df_timeline_cat[df_timeline_cat["Item"] == item_sel].copy()
                )
                if not df_tl_plot.empty:
                    base_date = pd.to_datetime("2025-01-01")
                    df_tl_plot["Fecha_inicio"] = base_date + pd.to_timedelta((df_tl_plot["Mes_inicio"] - 1) * 30, unit="D")
                    df_tl_plot["Fecha_termino"] = base_date + pd.to_timedelta((df_tl_plot["Mes_termino"] - 1) * 30, unit="D")
                    df_tl_plot = df_tl_plot.sort_values(by=["Fecha_inicio", "Fecha_termino"], ascending=[False, False])
                    df_tl_plot["Categoria"] = pd.Categorical(
                        df_tl_plot["Categoria"],
                        categories=df_tl_plot["Categoria"].tolist(),
                        ordered=True,
                    )
                    if include_direction_item:
                        fig_timeline_cat = go.Figure()
                        shown_items = set()
                        for _, row in df_tl_plot.iterrows():
                            item_name = row["Item"]
                            category_name = row["Categoria"]
                            color_value = item_color_map.get(item_name, CAT_COLOR_MAP.get(category_name, "#94A3B8"))
                            fig_timeline_cat.add_trace(
                                go.Scatter(
                                    x=[row["Fecha_inicio"], row["Fecha_termino"]],
                                    y=[category_name, category_name],
                                    mode="lines+markers",
                                    name=item_name,
                                    legendgroup=item_name,
                                    showlegend=item_name not in shown_items,
                                    line=dict(color=color_value, width=10),
                                    marker=dict(size=10, color=color_value, line=dict(color="white", width=1.4)),
                                    hovertemplate=(
                                        f"<b>{item_name}</b><br>"
                                        f"Categoría: {category_name}<br>"
                                        f"Mes inicio: {int(row['Mes_inicio'])}<br>"
                                        f"Mes término: {int(row['Mes_termino'])}<br>"
                                        f"Monto CLP: {row['Monto_CLP']:,.0f}<br>"
                                        f"Monto USD: {row['Monto_USD']:,.0f}<extra></extra>"
                                    ),
                                )
                            )
                            shown_items.add(item_name)
                        fig_timeline_cat.update_yaxes(categoryorder="array", categoryarray=df_tl_plot["Categoria"].tolist(), title="Categoría / Tarea")
                        fig_timeline_cat.update_xaxes(
                            title="Mes del proyecto",
                            tickmode="array",
                            tickvals=df_tl_plot["Fecha_inicio"].sort_values().unique(),
                            ticktext=df_tl_plot["Mes_inicio"].sort_values().unique(),
                            showgrid=True,
                        )
                        fig_timeline_cat.update_layout(
                            margin=dict(l=10, r=10, t=60, b=110),
                            height=520,
                            legend_title_text="Ítem",
                            legend=dict(
                                orientation="h",
                                yanchor="top",
                                y=-0.20,
                                xanchor="center",
                                x=0.5,
                                title=dict(text=""),
                                font=dict(size=11),
                                entrywidth=150,
                                entrywidthmode="pixels",
                            ),
                            hoverlabel=dict(bgcolor="white"),
                            plot_bgcolor="white",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                    else:
                        fig_timeline_cat = px.timeline(
                            df_tl_plot,
                            x_start="Fecha_inicio",
                            x_end="Fecha_termino",
                            y="Categoria",
                            color="Item",
                            color_discrete_map=item_color_map,
                            hover_data={
                                "Categoria": True,
                                "Item": True,
                                "Mes_inicio": True,
                                "Mes_termino": True,
                                "Monto_CLP": ":,.0f",
                                "Monto_USD": ":,.0f",
                            },
                        )
                        fig_timeline_cat.update_yaxes(categoryorder="array", title="Categoría / Tarea")
                        fig_timeline_cat.update_xaxes(
                            title="Mes del proyecto",
                            tickmode="array",
                            tickvals=df_tl_plot["Fecha_inicio"].sort_values().unique(),
                            ticktext=df_tl_plot["Mes_inicio"].sort_values().unique(),
                            showgrid=True,
                        )
                        fig_timeline_cat.update_layout(
                            margin=dict(l=10, r=10, t=60, b=110),
                            height=520,
                            legend=dict(
                                orientation="h",
                                yanchor="top",
                                y=-0.20,
                                xanchor="center",
                                x=0.5,
                                title=dict(text=""),
                                font=dict(size=11),
                                entrywidth=150,
                                entrywidthmode="pixels",
                            ),
                            hoverlabel=dict(bgcolor="white"),
                        )
                    apply_engineering_chart_typography(fig_timeline_cat, title_size=20, body_size=13, tick_size=12, legend_size=11)
                    st.plotly_chart(
                        fig_timeline_cat,
                        use_container_width=True,
                        key=f"{key_prefix}timeline_categoria_chart",
                    )

    render_pagos_hitos(
        capex_url,
        fx_used,
        pagos_scale,
        key_prefix=key_prefix,
        include_direction_salaries=include_direction_item,
    )

    if include_export:
        st.markdown("---")
        st.subheader("📄 Exportar informe técnico")
        if REPORTLAB_AVAILABLE:
            pdf_bytes = build_pdf_report()
            st.download_button(
                label="📥 Descargar reporte PDF técnico (CAPEX Piloto 80 kW)",
                data=pdf_bytes,
                file_name="Reporte_CAPEX_Piloto_80kW.pdf",
                mime="application/pdf",
                key=f"{key_prefix}download_pdf_report",
            )
        else:
            st.info("La exportación PDF está deshabilitada porque `reportlab` no está instalado en este entorno.")

    if include_direction_item:
        render_riesgo_matrix_chart(
            RIESGO_CSV_URL_DEFAULT,
            key_prefix=key_prefix,
        )

# =========================
# KPI CARDS – DISEÑO PRO
# =========================
def render_top_summary_kpis():
    st.markdown('<div class="kpi-row"></div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)

    with k1:
        kpi_card(
            "CAPEX",
            format_clp(capex_total_clp),
            "Inversión piloto 80 kW, incluye I+D, componentes, montaje y contingencias."
        )

    with k2:
        kpi_card(
            "Dirección",
            format_clp(direccion_total_clp),
            "Fondos de dirección técnica separados del CAPEX base."
        )

    with k3:
        kpi_card(
            "CAPEX total",
            format_clp(capex_total_integrado_clp),
            "Suma referencial de CAPEX base + dirección técnica."
        )


def render_capex_categoria_content():
    st.markdown(
        '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Análisis técnico por categoría</div>',
        unsafe_allow_html=True,
    )

    df_cat_filtrado = df_cat.copy()
    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:0 0 10px 0;">Gráfico por ítem · distribución del CAPEX por categoría</div>',
        unsafe_allow_html=True,
    )

    df_capex_filtrado = df_capex.copy()
    items_unicos = df_capex_filtrado["Item"].unique().tolist()
    num_items = len(items_unicos)

    if num_items > 0:
        n_cols = 3
        n_rows = math.ceil(num_items / n_cols)
        for row_idx in range(n_rows):
            cols = st.columns(n_cols)
            for col_idx in range(n_cols):
                idx = row_idx * n_cols + col_idx
                if idx >= num_items:
                    break
                item_name = items_unicos[idx]
                with cols[col_idx]:
                    df_item_cat = (
                        df_capex_filtrado[df_capex_filtrado["Item"] == item_name]
                        .groupby("Categoria", as_index=False)
                        .agg(Monto_CLP=("Monto_CLP", "sum"))
                    )
                    if df_item_cat.empty:
                        st.caption("Sin distribución disponible para este ítem.")
                        continue

                    total_item = df_item_cat["Monto_CLP"].sum()
                    total_capex_visible = df_capex_filtrado["Monto_CLP"].sum()
                    pct_item_total = (total_item / total_capex_visible) if total_capex_visible > 0 else 0
                    st.markdown(
                        (
                            f'<div class="eng-body-title" style="font-size:14px;font-weight:800;color:#0f172a;'
                            f'margin:0 0 2px 0;">{html.escape(str(item_name))}</div>'
                            f'<div style="font-size:12px;font-weight:400;color:#64748b;margin:0 0 10px 0;">'
                            f'{format_clp(total_item)} · {len(df_item_cat)} categorías activas</div>'
                        ),
                        unsafe_allow_html=True,
                    )
                    fig_donut_item = px.pie(
                        df_item_cat,
                        values="Monto_CLP",
                        names="Categoria",
                        hole=0.70,
                        color="Categoria",
                        color_discrete_map=CAT_COLOR_MAP,
                    )
                    fig_donut_item.update_traces(
                        textinfo="percent",
                        textposition="inside",
                        hovertemplate="<b>%{label}</b><br>Participación dentro del ítem: %{percent:.1%}<br>Monto CLP: %{value:,.0f}<br><extra></extra>",
                        insidetextorientation="horizontal"
                    )
                    fig_donut_item.add_annotation(
                        x=0.5, y=0.5, text=f"{pct_item_total*100:.1f}%", showarrow=False,
                        font=dict(size=22, color="black"), xanchor="center", yanchor="middle"
                    )
                    fig_donut_item.update_layout(
                        showlegend=True,
                        legend=dict(orientation="v", x=1.25, y=0.5, xanchor="left", font=dict(size=11)),
                        margin=dict(l=0, r=120, t=10, b=10),
                        height=280,
                    )
                    apply_engineering_chart_typography(fig_donut_item, title_size=18, body_size=12, tick_size=11, legend_size=11)
                    st.plotly_chart(fig_donut_item, use_container_width=True)
    else:
        st.info("No hay ítems para mostrar en los dónuts según las categorías seleccionadas.")

    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:4px 0 10px 0;">Participación porcentual por categoría</div>',
        unsafe_allow_html=True,
    )
    total_clp_cat = df_cat_filtrado["Monto_CLP"].sum()
    df_cat_plot = df_cat_filtrado.copy().sort_values("Monto_CLP", ascending=False)
    df_cat_plot["Pct_cat"] = df_cat_plot["Monto_CLP"] / total_clp_cat if total_clp_cat > 0 else 0.0

    df_cat_item = (
        df_capex.groupby(["Categoria", "Item"], as_index=False)
        .agg(Monto_CLP=("Monto_CLP", "sum"))
        .sort_values(["Categoria", "Monto_CLP"], ascending=[True, False])
    )
    top_item_by_cat = df_cat_item.drop_duplicates(subset=["Categoria"], keep="first")
    cat_item_color_map = {
        row["Categoria"]: item_color_map.get(row["Item"], CAT_COLOR_MAP.get(row["Categoria"], "#2563EB"))
        for _, row in top_item_by_cat.iterrows()
    }

    fig_cat = px.bar(
        df_cat_plot,
        x="Pct_cat",
        y="Categoria",
        orientation="h",
        color="Categoria",
        color_discrete_map=cat_item_color_map,
        text="Pct_cat",
        labels={"Categoria": "", "Pct_cat": "Participación"},
        title="Distribución porcentual del CAPEX por categoría",
    )
    fig_cat.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Participación: %{x:.1%}<extra></extra>",
        marker=dict(line=dict(color="rgba(255,255,255,0.96)", width=1.4)),
    )
    max_part = float(df_cat_plot["Pct_cat"].max() or 0)
    fig_cat.update_xaxes(
        tickformat=".0%",
        range=[0, max_part * 1.18 if max_part > 0 else 1],
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
    )
    fig_cat.update_yaxes(showgrid=False, categoryorder="total ascending")
    fig_cat.update_layout(
        xaxis_title="Participación (%)",
        yaxis_title="",
        margin=dict(l=10, r=34, t=80, b=24),
        height=420,
        bargap=0.32,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    apply_engineering_chart_typography(fig_cat, title_size=20, body_size=13, tick_size=12, legend_size=12)
    st.plotly_chart(fig_cat, use_container_width=True)
    st.session_state["fig_cat_categoria"] = fig_cat

    legend_css = """
    <style>
    .item-legend { display:flex; flex-wrap:wrap; gap:0.45rem 0.75rem; margin-top:0.4rem; margin-bottom:0.8rem; }
    .item-legend-title { font-size:11px; font-weight:500; color:#64748B; text-transform:uppercase; letter-spacing:.10em; margin-top:0.4rem; margin-bottom:0.25rem; }
    .item-legend-chip { display:inline-flex; align-items:center; gap:0.4rem; font-size:13px; font-weight:400; color:#0f172a; }
    .item-legend-swatch { width:12px; height:12px; border-radius:2px; border:1px solid rgba(17, 24, 39, 0.2); }
    </style>
    """
    legend_items = []
    legend_order = [
        "Desarrollo Tecnológico", "Componentes Mecánicos", "Sistema Eléctrico y Control",
        "Obras Civiles", "Montaje y Logística", "Ensayos y Certificación", "Contingencias y Administración",
    ]
    for item in legend_order:
        color = CAT_COLOR_MAP.get(item, "#2563EB")
        legend_items.append(
            f'<span class="item-legend-chip"><span class="item-legend-swatch" style="background:{color}"></span>{item}</span>'
        )
    st.markdown(
        legend_css + '<div class="item-legend-title">Ítem</div>' + f'<div class="item-legend">{"".join(legend_items)}</div>',
        unsafe_allow_html=True,
    )



def render_capex_items_content():
    st.subheader("Top ítems por monto")
    render_category_palette()

    top_n = st.slider("Número de ítems a mostrar (Top N):", 5, 30, 15, step=1, key="capex_items_top_n")
    df_top = df_capex.sort_values("Monto_CLP", ascending=False).head(top_n).copy()
    df_top["Monto_CLP_fmt"] = df_top["Monto_CLP"].apply(format_clp)
    df_top["Monto_USD_fmt"] = df_top["Monto_USD"].apply(format_usd)
    df_top["Participación (%)"] = df_top["Participacion_pct"] * 100
    df_top["Monto_CLP_MM"] = df_top["Monto_CLP"] / 1e6

    fig_top = px.bar(
        df_top,
        x="Monto_CLP_MM",
        y="Item",
        color="Categoria",
        color_discrete_map=CAT_COLOR_MAP,
        orientation="h",
        hover_data={
            "Monto_CLP_MM": False,
            "Monto_CLP": ":,.0f",
            "Monto_USD": ":,.0f",
            "Participacion_pct": ":.2%",
            "Categoria": True,
        },
        labels={"Monto_CLP_MM": "Monto (MM CLP)", "Item": "Ítem", "Categoria": "Categoría"},
        title=f"Top {top_n} ítems por monto (millones de CLP)",
    )
    fig_top.update_traces(text=df_top["Monto_CLP_MM"].apply(lambda v: f"{v:.1f} MM"), textposition="outside")
    fig_top.update_layout(xaxis_title="Monto (millones de CLP)", yaxis_title="", margin=dict(l=10, r=10, t=60, b=10))
    apply_engineering_chart_typography(fig_top, title_size=20, body_size=13, tick_size=12, legend_size=11)
    st.plotly_chart(fig_top, use_container_width=True)
    st.session_state["fig_top_items"] = fig_top

    st.markdown("#### Tabla detallada")
    st.dataframe(
        df_top[["Item", "Categoria", "Participación (%)", "Monto_CLP_fmt", "Monto_USD_fmt", "Bullet"]],
        hide_index=True,
        use_container_width=True,
    )


def render_capex_module_content(selector_key: str = "capex_internal_selector"):
    st.markdown("---")
    render_capex_categoria_content()


def render_direccion_module_content():
    if direccion_error:
        st.error(direccion_error)
    elif df_direccion.empty:
        st.warning("La hoja `Director General Técnico` no tiene registros válidos para mostrar.")
    else:
        total_direccion = float(df_direccion["Total"].sum() or 0.0)
        total_meses = float(df_direccion["Meses"].sum() or 0.0)
        costo_mensual_prom_simple = (
            float(df_direccion["Costo empresa mensual"].mean() or 0.0)
            if not df_direccion["Costo empresa mensual"].empty else 0.0
        )
        costo_mensual_prom_ponderado = total_direccion / total_meses if total_meses > 0 else 0.0
        meses_promedio = total_meses / len(df_direccion) if len(df_direccion) > 0 else 0.0
        capex_mas_direccion = capex_total_clp + total_direccion

        dk1, dk2, dk3 = st.columns(3)
        with dk1:
            kpi_card(
                "Fondos capital humano (CLP)",
                format_clp(total_direccion),
                "Monto total separado del CAPEX técnico base."
            )
        with dk2:
            kpi_card(
                "Cargos cubiertos",
                f"{len(df_direccion):,}".replace(",", "."),
                "Roles leídos desde la hoja Dirección General Técnico."
            )
        with dk3:
            kpi_card(
                "Meses acumulados",
                f"{total_meses:,.0f}".replace(",", "."),
                "Suma de meses reportados por cargo."
            )
        st.markdown(
            """
            <style>
            .dir-pro-shell{
                border:1px solid rgba(226,232,240,.92);
                border-radius:24px;
                background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
                box-shadow:0 14px 32px rgba(15,23,42,.06);
                padding:18px 20px 16px 20px;
                margin:8px 0 14px 0;
            }
            .dir-pro-k{
                font-size:11px;
                font-weight:800;
                letter-spacing:.12em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:6px;
            }
            .dir-pro-t{
                font-size:24px;
                font-weight:900;
                line-height:1.06;
                color:#0f172a;
                margin-bottom:8px;
            }
            .dir-pro-s{
                font-size:13px;
                line-height:1.58;
                color:#475569;
                margin-bottom:12px;
            }
            .dir-pro-chip-row{
                display:flex;
                flex-wrap:wrap;
                gap:10px;
            }
            .dir-pro-chip{
                display:inline-flex;
                align-items:center;
                gap:8px;
                padding:7px 11px;
                border-radius:999px;
                border:1px solid rgba(148,163,184,.26);
                background:rgba(255,255,255,.86);
                box-shadow:0 4px 10px rgba(15,23,42,.04);
                font-size:12px;
                color:#0f172a;
            }
            .dir-pro-dot{
                width:10px;
                height:10px;
                border-radius:999px;
                flex:0 0 auto;
            }
            .dir-insight-grid{
                display:grid;
                grid-template-columns:repeat(3,minmax(0,1fr));
                gap:12px;
                margin:0 0 14px 0;
            }
            @media (max-width:1000px){
                .dir-insight-grid{grid-template-columns:1fr;}
            }
            .dir-insight-card{
                border-radius:18px;
                padding:14px 15px 13px 15px;
                border:1px solid rgba(191,219,254,.68);
                background:linear-gradient(180deg,#ffffff 0%,#eff6ff 100%);
                box-shadow:0 6px 16px rgba(15,23,42,.05);
            }
            .dir-insight-label{
                font-size:11px;
                font-weight:800;
                letter-spacing:.10em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:6px;
            }
            .dir-insight-value{
                font-size:26px;
                font-weight:900;
                line-height:1.02;
                color:#0f172a;
                margin-bottom:6px;
            }
            .dir-insight-sub{
                font-size:13px;
                line-height:1.5;
                color:#475569;
            }
            .dir-notes{
                margin:0;
                padding-left:18px;
            }
            .dir-notes li{
                margin:0 0 10px 0;
                color:#334155;
                line-height:1.58;
                font-size:14px;
            }
            .dir-notes li:last-child{margin-bottom:0;}
            </style>
            """,
            unsafe_allow_html=True,
        )
        df_dir_plot = df_direccion.copy()
        df_dir_plot["Total_MM"] = df_dir_plot["Total"] / 1e6
        df_dir_plot["Participacion_pct"] = np.where(
            total_direccion > 0,
            df_dir_plot["Total"] / total_direccion * 100.0,
            0.0,
        )
        df_dir_plot["Etiqueta_barra"] = df_dir_plot.apply(
            lambda row: f'{row["Total_MM"]:.1f} MM | {row["Participacion_pct"]:.1f}%',
            axis=1,
        )
        df_dir_plot = df_dir_plot.sort_values("Total", ascending=True).copy()
        df_dir_plot["Cargo_grafico"] = df_dir_plot["Cargo"].replace(
            {
                "Ingeniero de Desarrollo Tecnológico": "Ingeniero de Desarrollo<br>Tecnológico",
                "Líder de Ingeniería y Proyecto": "Líder de Ingeniería<br>y Proyecto",
            }
        )
        direccion_color_map = DIRECTION_ROLE_COLOR_MAP
        max_total_mm = float(df_dir_plot["Total_MM"].max() or 0.0)
        top_role_row = df_dir_plot.sort_values("Total", ascending=False).iloc[0]
        top_role = str(top_role_row["Cargo"])
        top_role_pct = float(top_role_row["Participacion_pct"] or 0.0)
        concentration_top_2 = float(
            df_dir_plot.sort_values("Total", ascending=False).head(2)["Participacion_pct"].sum() or 0.0
        )
        st.markdown(
            f"""
            <div class="dir-pro-shell">
                <div class="dir-pro-k">Visual ejecutivo</div>
                <div class="dir-pro-t">Fondos por cargo de dirección técnica</div>
                <div class="dir-pro-s">Composición económica del bloque de capital humano técnico, ordenada por peso financiero y ajustada para cargos con etiquetas largas.</div>
                <div class="dir-pro-chip-row">
                    <div class="dir-pro-chip"><span class="dir-pro-dot" style="background:#0F4C81"></span><strong>Cargo líder:</strong> {top_role}</div>
                    <div class="dir-pro-chip"><span class="dir-pro-dot" style="background:#0F766E"></span><strong>Concentración top 2:</strong> {concentration_top_2:.1f}%</div>
                    <div class="dir-pro-chip"><span class="dir-pro-dot" style="background:#2563EB"></span><strong>Run-rate ponderado:</strong> {format_clp(costo_mensual_prom_ponderado)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig_direccion = px.bar(
            df_dir_plot,
            x="Total_MM",
            y="Cargo_grafico",
            orientation="h",
            text="Etiqueta_barra",
            color="Cargo",
            color_discrete_map=direccion_color_map,
            title=None,
            labels={"Total_MM": "Monto total (MM CLP)", "Cargo_grafico": ""},
        )
        fig_direccion.update_traces(
            textposition="outside",
            textfont=dict(size=11, color="#334155"),
            marker=dict(line=dict(color="rgba(255,255,255,0.96)", width=1.4)),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{customdata[3]}</b><br>"
                "Total: %{x:.1f} MM CLP<br>"
                "Participación: %{customdata[0]:.1f}%<br>"
                "Meses: %{customdata[1]:.0f}<br>"
                "Costo mensual: %{customdata[2]:,.0f} CLP<extra></extra>"
            ),
            customdata=df_dir_plot[["Participacion_pct", "Meses", "Costo empresa mensual", "Cargo"]],
        )
        fig_direccion.update_layout(
            showlegend=False,
            margin=dict(l=16, r=124, t=12, b=12),
            height=max(390, 92 * len(df_dir_plot) + 14),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            bargap=0.30,
            font=dict(color="#334155", size=13),
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        apply_engineering_chart_typography(fig_direccion, title_size=20, body_size=13, tick_size=12, legend_size=12)
        fig_direccion.update_xaxes(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.18)",
            zeroline=False,
            ticksuffix=" MM",
            range=[0, max_total_mm * 1.18 if max_total_mm > 0 else 1],
            automargin=True,
        )
        fig_direccion.update_yaxes(showgrid=False, automargin=True)
        st.plotly_chart(fig_direccion, use_container_width=True)

        df_dir_table = df_dir_plot.sort_values("Total", ascending=False).copy()
        df_dir_table.insert(0, "Ranking", [f"#{i}" for i in range(1, len(df_dir_table) + 1)])
        df_dir_table["Costo mensual"] = df_dir_table["Costo empresa mensual"].apply(format_clp)
        df_dir_table["Intensidad"] = df_dir_table.apply(
            lambda row: f"{float(row['Total_MM']) / max(float(row['Meses']), 1):.1f} MM/mes",
            axis=1,
        )
        df_dir_table["Total"] = df_dir_table["Total_MM"].map(lambda v: f"{v:.1f} MM CLP")
        df_dir_table["Participación"] = df_dir_table["Participacion_pct"].map(lambda v: f"{v:.1f}%")

        col_dir_1, col_dir_2 = st.columns([1.22, 1])
        with col_dir_1:
            st.markdown(
                """
                <div class="dir-pro-shell">
                    <div class="dir-pro-k">Tabla ejecutiva</div>
                    <div class="dir-pro-t">Base de cargos</div>
                    <div class="dir-pro-s">Ranking económico del bloque con duración, costo mensual, intensidad de gasto y participación relativa por rol.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.dataframe(
                style_engineering_table(
                    df_dir_table[["Ranking", "Cargo", "Meses", "Costo mensual", "Intensidad", "Total", "Participación"]],
                    header_color="#24446B",
                    row_color="#F4F8FC",
                ),
                hide_index=True,
                use_container_width=True,
                height=35 * (len(df_dir_table) + 1) + 3,
            )
        with col_dir_2:
            st.markdown(
                """
                <div class="dir-pro-shell">
                    <div class="dir-pro-k">Síntesis ejecutiva</div>
                    <div class="dir-pro-t">Lectura ejecutiva</div>
                    <div class="dir-pro-s">Interpretación de comité enfocada en concentración del gasto, ritmo mensual y relación con el CAPEX técnico.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="dir-insight-grid">
                    <div class="dir-insight-card">
                        <div class="dir-insight-label">Cargo dominante</div>
                        <div class="dir-insight-value">{top_role_pct:.1f}%</div>
                        <div class="dir-insight-sub">{top_role} concentra la mayor parte del bloque y define la referencia principal del costo directivo.</div>
                    </div>
                    <div class="dir-insight-card">
                        <div class="dir-insight-label">Run-rate mensual</div>
                        <div class="dir-insight-value">{format_clp(costo_mensual_prom_ponderado)}</div>
                        <div class="dir-insight-sub">Costo mensual ponderado considerando la duración efectiva de todos los cargos del bloque.</div>
                    </div>
                    <div class="dir-insight-card">
                        <div class="dir-insight-label">Referencia ampliada</div>
                        <div class="dir-insight-value">{format_clp(capex_mas_direccion)}</div>
                        <div class="dir-insight-sub">Valor de referencia si este capital humano técnico se mirara junto con el CAPEX base.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <ul class="dir-notes">
                    <li>Fondos de dirección identificados: <strong>{format_clp(total_direccion)}</strong>.</li>
                    <li>Costo mensual ponderado del bloque: <strong>{format_clp(costo_mensual_prom_ponderado)}</strong> (total dividido por <strong>{f"{total_meses:,.0f}".replace(",", ".")} meses</strong>).</li>
                    <li>Promedio simple entre cargos: <strong>{format_clp(costo_mensual_prom_simple)}</strong>; no coincide con el run-rate porque los cargos tienen distinta duración.</li>
                    <li>Duración promedio por cargo: <strong>{meses_promedio:.1f} meses</strong>.</li>
                    <li>Los dos cargos de mayor peso concentran <strong>{concentration_top_2:.1f}%</strong> del bloque, lo que revela una estructura de gasto relativamente concentrada.</li>
                    <li>Este bloque se mantiene deliberadamente separado para no contaminar el desglose del CAPEX de ingeniería.</li>
                </ul>
                """,
                unsafe_allow_html=True,
            )


def render_valorizacion_module_content(key_prefix: str = "val_"):
    def widget_key(name: str) -> str:
        return f"{key_prefix}{name}"

    bloque_sel = "1. Fundamentos de Creación de Valor"

    try:
        df_valorizacion = load_valorizacion_data(VALORIZACION_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
        valorizacion_error = None
    except Exception as exc:
        df_valorizacion = pd.DataFrame()
        valorizacion_error = str(exc)
    if bloque_sel == "1. Fundamentos de Creación de Valor":
        try:
            df_eerrv2 = load_eerrv2_data(EERRV2_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
            eerrv2_error = None
        except Exception as exc:
            df_eerrv2 = pd.DataFrame()
            eerrv2_error = str(exc)
    else:
        df_eerrv2 = pd.DataFrame()
        eerrv2_error = None

    if valorizacion_error:
        st.error(f"No se pudo cargar la valorización: {valorizacion_error}")
        return
    if df_valorizacion.empty:
        st.warning("La hoja de valorización no contiene registros para mostrar.")
        return

    monto_col = find_best_column(
        df_valorizacion,
        ["total", "monto", "montoclp", "valor", "costo", "costototal"],
    )
    label_col = find_best_column(
        df_valorizacion,
        ["item", "concepto", "descripcion", "detalle", "categoria", "cargo"],
    )

    df_val_plot = pd.DataFrame()
    if monto_col:
        df_valorizacion[f"{monto_col}__num"] = df_valorizacion[monto_col].apply(parse_money_clp_robusto)
        if label_col:
            df_val_plot = (
                df_valorizacion[[label_col, f"{monto_col}__num"]]
                .rename(columns={label_col: "Label", f"{monto_col}__num": "Monto"})
                .groupby("Label", as_index=False)["Monto"]
                .sum()
                .sort_values("Monto", ascending=False)
                .head(15)
            )

    if not df_val_plot.empty:
        df_val_plot["Monto_MM"] = df_val_plot["Monto"] / 1e6
        fig_val = px.bar(
            df_val_plot.sort_values("Monto", ascending=True),
            x="Monto_MM",
            y="Label",
            orientation="h",
            text=df_val_plot.sort_values("Monto", ascending=True)["Monto_MM"].map(lambda v: f"{v:.1f} MM"),
            title="Top conceptos de valorización",
            labels={"Monto_MM": "Monto (MM CLP)", "Label": ""},
            color="Monto_MM",
            color_continuous_scale=["#DBEAFE", "#60A5FA", "#2563EB"],
        )
        fig_val.update_traces(textposition="outside")
        fig_val.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(l=10, r=20, t=60, b=10), height=460)
        st.plotly_chart(fig_val, use_container_width=True)

    df_model, model_map = get_valorizacion_model_map(df_valorizacion)
    fx_default = float(fx_used) if np.isfinite(fx_used) and fx_used > 0 else parse_model_number(model_map.get("fxclpusd", 925))
    total_base_knowhow_clp, _, _, _ = get_valor_activo_tecnologico_construido(refresh_nonce=data_refresh_nonce)
    pre_money_actual_default = total_base_knowhow_clp / fx_default if fx_default > 0 and total_base_knowhow_clp > 0 else 0.0
    capex_10kw_default = 0.0
    try:
        df_restante_10kw = build_restante_piloto_10kw_view(RESTANTE_PILOTO_10KW_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
        if not df_restante_10kw.empty:
            capex_10kw_default = float(df_restante_10kw["Valor C"].sum() or 0.0)
    except Exception:
        capex_10kw_default = 0.0
    inversion_clp_default = capex_10kw_default + float(capex_total_integrado_clp or 0.0)
    ebitda_unit_default = parse_model_number(model_map.get("ebitdaunitariodereferencia", 0))
    volumen_default = parse_model_number(model_map.get("volumencomercialdereferencia", 0))
    multiple_default = 1.0
    multiple_post_default = 5.0
    captura_default = parse_model_percent(model_map.get("capturadelvalorpotencialpostpiloto", "100%"))
    ronda_pct_default = parse_model_percent(model_map.get("participacionobjetivoparanuevosinversionistas", "70%"))
    widget_defaults = {
        "fx": int(round(fx_default or 925)),
        "pre_money": int(round(pre_money_actual_default)),
        "inv_clp": int(round(inversion_clp_default)),
        "investment_currency": "USD",
        "volume": int(round(volumen_default)),
        "ebitda_unit": int(round(ebitda_unit_default)),
        "multiple": float(multiple_default or 1.0),
        "ronda_pct": float((ronda_pct_default or 0.70) * 100.0),
        "valuation_basis": "EBITDA potencial ciclo inicial",
        "alloc_manual": False,
        "fluxial_pct_manual": 50.0,
        "imelsa_pct_manual": 50.0,
    }
    shared_group = "base" if bloque_sel in {"1. Fundamentos de Creación de Valor", "2. Serie A: Inversión Inicial y Validación"} else "post"

    def shared_state_key(name: str, group: str | None = None) -> str:
        active_group = group or shared_group
        return widget_key(f"state_{active_group}_{name}")

    def shared_widget_key(name: str, group: str | None = None) -> str:
        active_group = group or shared_group
        return widget_key(f"widget_{active_group}_{name}")

    def prime_widget(name: str, group: str | None = None) -> str:
        active_group = group or shared_group
        state_key = shared_state_key(name, active_group)
        widget_state_key = shared_widget_key(name, active_group)
        if widget_state_key not in st.session_state:
            st.session_state[widget_state_key] = st.session_state[state_key]
        return widget_state_key

    def sync_widget_to_state(name: str, group: str | None = None):
        active_group = group or shared_group
        st.session_state[shared_state_key(name, active_group)] = st.session_state[shared_widget_key(name, active_group)]

    def sync_investment_currency(group: str | None = None):
        active_group = group or shared_group
        currency = st.session_state[shared_widget_key("investment_currency", active_group)]
        st.session_state[shared_state_key("investment_currency", active_group)] = currency
        if currency == "USD":
            fx_val = float(st.session_state.get(shared_state_key("fx", active_group), 1) or 1)
            clp_val = float(st.session_state.get(shared_state_key("inv_clp", active_group), 0) or 0)
            st.session_state[shared_widget_key("inv_usd_display", active_group)] = int(round(clp_val / fx_val)) if fx_val > 0 else 0

    def sync_investment_usd_to_clp(group: str | None = None):
        active_group = group or shared_group
        fx_val = float(st.session_state.get(shared_state_key("fx", active_group), 1) or 1)
        usd_val = float(st.session_state.get(shared_widget_key("inv_usd_display", active_group), 0) or 0)
        st.session_state[shared_state_key("inv_clp", active_group)] = int(round(usd_val * fx_val))
        st.session_state.pop(shared_widget_key("inv_clp", active_group), None)

    def resolve_fluxial_pre_money(valuation_basis: str, base_usd: float, ebitda_value: float) -> float:
        return base_usd if valuation_basis == "BASE INVERSION + KNOW-HOW" else ebitda_value

    group_widget_defaults = {
        "base": widget_defaults,
        "post": {
            **widget_defaults,
            "multiple": float(multiple_post_default),
        },
    }

    for group_name in ("base", "post"):
        for name, default_value in group_widget_defaults[group_name].items():
            if shared_state_key(name, group_name) not in st.session_state:
                st.session_state[shared_state_key(name, group_name)] = default_value

    # Keep block 2 investment aligned with the "Capital a recaudar" KPI.
    st.session_state[shared_state_key("inv_clp", "base")] = int(round(inversion_clp_default))
    st.session_state.pop(shared_widget_key("inv_clp", "base"), None)

    st.markdown(
        """
        <style>
        .val-summary-hero{
            border-radius:24px;
            padding:16px 20px;
            background:
                radial-gradient(circle at top right, rgba(14,165,164,.16), transparent 24%),
                linear-gradient(90deg,#f8fbff 0%,#e7f5ff 48%,#d4efff 100%);
            border:1px solid rgba(125,211,252,.42);
            box-shadow:0 16px 36px rgba(15,23,42,.08);
            margin-bottom:8px;
        }
        .val-summary-grid{
            display:grid;
            grid-template-columns:1.25fr .95fr;
            gap:14px;
            align-items:stretch;
        }
        @media (max-width:1100px){.val-summary-grid{grid-template-columns:1fr;}}
        .val-summary-k{
            font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#0f766e;margin-bottom:8px;
        }
        .val-summary-t{
            font-size:18px;font-weight:800;line-height:1.2;color:#0f172a;margin-bottom:10px;
        }
        .val-summary-v{
            font-size:52px;font-weight:900;line-height:1;color:#0f172a;margin-bottom:12px;letter-spacing:-.03em;
        }
        .val-summary-p{
            font-size:15px;line-height:1.6;color:#475569;max-width:720px;
        }
        .val-summary-panel{
            border-radius:18px;padding:12px 14px;background:rgba(255,255,255,.76);border:1px solid rgba(148,163,184,.24);backdrop-filter:blur(6px);
        }
        .val-summary-panel-h{
            font-size:12px;font-weight:800;letter-spacing:.10em;text-transform:uppercase;color:#64748b;margin-bottom:8px;
        }
        .val-summary-row{
            display:flex;justify-content:space-between;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid rgba(226,232,240,.9);
        }
        .val-summary-row:last-child{border-bottom:none;padding-bottom:0}
        .val-summary-label{
            font-size:14px;font-weight:700;color:#0f172a;line-height:1.35;
        }
        .val-summary-value{
            font-size:16px;font-weight:800;color:#0f172a;white-space:nowrap;
        }
        .val-multiple-head,
        .val-multiple-row{
            display:grid;
            grid-template-columns:1fr auto;
            gap:12px;
            align-items:center;
        }
        .val-multiple-head{
            padding:0 0 8px 0;
            border-bottom:1px solid rgba(226,232,240,.95);
            margin-bottom:2px;
        }
        .val-multiple-row{
            padding:10px 0;
            border-bottom:1px solid rgba(226,232,240,.9);
        }
        .val-multiple-row:last-child{
            border-bottom:none;
            padding-bottom:0;
        }
        .val-multiple-hl{
            font-size:13px;
            font-weight:800;
            color:#0f172a;
        }
        .val-multiple-hv{
            font-size:13px;
            font-weight:800;
            color:#0f172a;
            text-align:right;
        }
        .val-multiple-l{
            font-size:14px;
            font-weight:700;
            color:#0f172a;
        }
        .val-multiple-v{
            font-size:16px;
            font-weight:800;
            color:#0f172a;
            text-align:right;
            white-space:nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if bloque_sel == "1. Fundamentos de Creación de Valor":
        base_fx_preview = float(st.session_state.get(shared_state_key("fx", "base"), fx_default or 1))
        base_currency_preview = str(st.session_state.get(shared_state_key("investment_currency", "base"), "CLP"))
        volume_preview = float(st.session_state.get(shared_state_key("volume", "base"), volumen_default))
        ebitda_unit_preview = float(st.session_state.get(shared_state_key("ebitda_unit", "base"), ebitda_unit_default))
        multiple_preview = float(st.session_state.get(shared_state_key("multiple", "base"), multiple_default or 1))
        valuation_basis_preview = str(st.session_state.get(shared_state_key("valuation_basis", "base"), "EBITDA potencial ciclo inicial"))
        base_en_usd_preview = (total_base_knowhow_clp / base_fx_preview) if base_fx_preview > 0 else 0.0
        market_ebitda_base_preview = volume_preview * ebitda_unit_preview
        ebitda_preview = volume_preview * ebitda_unit_preview * multiple_preview
        valorizacion_fluxial_preview = resolve_fluxial_pre_money(valuation_basis_preview, base_en_usd_preview, ebitda_preview)
        market_multiple_values = [1.0, 3.0, 7.0]
        market_multiple_rows = []
        for market_multiple in market_multiple_values:
            implied_value_usd = market_ebitda_base_preview * market_multiple
            implied_value_display = (
                format_clp(implied_value_usd * base_fx_preview)
                if base_currency_preview == "CLP"
                else format_compact_usd(implied_value_usd)
            )
            market_multiple_rows.append(
                f'<div class="val-multiple-row">'
                f'<div class="val-multiple-l">{market_multiple:.1f}x</div>'
                f'<div class="val-multiple-v">{implied_value_display}</div>'
                f'</div>'
            )
        composition_rows_preview = (
            f'<div class="val-multiple-head">'
            f'<div class="val-multiple-hl">Múltiplo</div>'
            f'<div class="val-multiple-hv">Valor implícito</div>'
            f'</div>'
            + "".join(market_multiple_rows)
        )
        if valuation_basis_preview == "BASE INVERSION + KNOW-HOW":
            if base_currency_preview == "CLP":
                valorizacion_fluxial_preview_display = format_clp(valorizacion_fluxial_preview * base_fx_preview)
            else:
                valorizacion_fluxial_preview_display = format_usd(valorizacion_fluxial_preview)
        else:
            valorizacion_fluxial_preview_display = format_clp(valorizacion_fluxial_preview * base_fx_preview) if base_currency_preview == "CLP" else format_usd(valorizacion_fluxial_preview)
        st.markdown(
            f"""
            <div class="val-summary-hero">
              <div class="val-summary-grid">
                <div>
                  <div class="val-summary-k">EBITDA OBJETIVO EN REGIMEN</div>
                  <div class="val-summary-t">EBITDA proyectado en escenario de escalamiento</div>
                  <div class="val-summary-v">{valorizacion_fluxial_preview_display}</div>
                  <div class="val-summary-p">
                    Estimación del EBITDA anual en escenario de operación escalada, considerando venta de turbinas bajo modelo industrial proyectado.
                  </div>
                </div>
                <div class="val-summary-panel">
                  <div class="val-summary-panel-h">Rango de Valor según Múltiplos de Mercado</div>
                  {composition_rows_preview}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif bloque_sel == "4. Serie B: Escalamiento Comercial":
        base_fx_preview = float(st.session_state.get(shared_state_key("fx", "base"), fx_default or 1))
        base_volume_preview = float(st.session_state.get(shared_state_key("volume", "base"), volumen_default))
        base_ebitda_unit_preview = float(st.session_state.get(shared_state_key("ebitda_unit", "base"), ebitda_unit_default))
        post_multiple_preview = float(st.session_state.get(shared_state_key("multiple", "post"), multiple_post_default))
        post_ronda_pct_preview = float(st.session_state.get(shared_state_key("ronda_pct", "post"), (ronda_pct_default or 0.70) * 100.0)) / 100.0

        base_ebitda_preview = base_volume_preview * base_ebitda_unit_preview * post_multiple_preview
        valuation_basis_preview = str(st.session_state.get(shared_state_key("valuation_basis", "base"), "EBITDA potencial ciclo inicial"))
        base_base_en_usd_preview = (total_base_knowhow_clp / base_fx_preview) if base_fx_preview > 0 else 0.0
        base_pre_money_preview = resolve_fluxial_pre_money(
            valuation_basis_preview,
            base_base_en_usd_preview,
            (
                float(st.session_state.get(shared_state_key("volume", "base"), volumen_default))
                * float(st.session_state.get(shared_state_key("ebitda_unit", "base"), ebitda_unit_default))
                * float(st.session_state.get(shared_state_key("multiple", "base"), multiple_default or 1))
            ),
        )
        base_inv_preview = float(st.session_state.get(shared_state_key("inv_clp", "base"), inversion_clp_default)) / base_fx_preview if base_fx_preview > 0 else 0.0
        post_money_a_preview = base_pre_money_preview + base_inv_preview
        valor_post_piloto_preview = base_ebitda_preview
        capital_raise_preview = valor_post_piloto_preview * post_ronda_pct_preview
        post_money_b_preview = valor_post_piloto_preview + capital_raise_preview

        st.markdown("---")
        st.markdown(
            f"""
            <div class="val-summary-hero">
              <div class="val-summary-grid">
                <div>
                  <div class="val-summary-k">EBITDA OBJETIVO EN REGIMEN</div>
                  <div class="val-summary-t">Post-money Serie B</div>
                  <div class="val-summary-v">{format_usd(post_money_b_preview)}</div>
                  <div class="val-summary-p">
                    Valorización posterior a la nueva ronda, integrando la base post piloto y el capital a levantar en Serie B.
                  </div>
                </div>
                <div class="val-summary-panel">
                  <div class="val-summary-panel-h">Referencia de Valor Implícito</div>
                  <div class="val-summary-row">
                    <div class="val-summary-label">Valorización base Serie B</div>
                    <div class="val-summary-value">{format_usd(valor_post_piloto_preview)}</div>
                  </div>
                  <div class="val-summary-row">
                    <div class="val-summary-label">Capital Serie B</div>
                    <div class="val-summary-value">{format_usd(capital_raise_preview)}</div>
                  </div>
                  <div class="val-summary-row">
                    <div class="val-summary-label">Post-money Serie B</div>
                    <div class="val-summary-value">{format_usd(post_money_b_preview)}</div>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    supuestos_title_map = {
        "1. Fundamentos de Creación de Valor": "Supuestos Base de Creación de Valor",
        "2. Serie A: Inversión Inicial y Validación": "Supuestos Económicos de Serie A",
        "3. Valorización Post-Validación": "Supuestos de Valorización Post-Validación",
        "4. Serie B: Escalamiento Comercial": "Supuestos de Ronda y Expansión Comercial",
    }
    supuestos_subtitle_map = {
        "1. Fundamentos de Creación de Valor": "Parámetros técnicos y económicos que explican la base de creación de valor del modelo.",
        "2. Serie A: Inversión Inicial y Validación": "Entradas de inversión y validación para estructurar la etapa inicial y la cesión asociada.",
        "3. Valorización Post-Validación": "Variables de volumen y múltiplo para proyectar el valor del activo tras validación.",
        "4. Serie B: Escalamiento Comercial": "Supuestos de ronda, expansión comercial y dilución para la etapa de escalamiento.",
    }

    st.markdown(
        """
        <style>
        .sup-shell{
            border-radius:24px;
            padding:18px 20px 14px 20px;
            border:1px solid rgba(148,163,184,.18);
            background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
            box-shadow:0 12px 28px rgba(15,23,42,.05);
            margin-bottom:18px;
        }
        .sup-head-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:6px;
        }
        .sup-head-main{
            font-size:30px;
            font-weight:800;
            line-height:1.1;
            letter-spacing:.06em;
            text-transform:uppercase;
            color:#64748B;
            margin:0 0 8px 0;
            max-width:980px;
        }
        .sup-head-t{
            font-size:16px;
            line-height:1.55;
            color:#475569;
            margin-top:4px;
            margin-bottom:0;
            max-width:980px;
        }
        .sup-input-shell{
            border-radius:22px;
            padding:16px 16px 8px 16px;
            border:1px solid rgba(203,213,225,.72);
            background:
                radial-gradient(circle at top right, rgba(219,234,254,.35), transparent 24%),
                linear-gradient(180deg,#f8fafc 0%,#ffffff 78%);
            box-shadow:0 10px 22px rgba(15,23,42,.04);
            margin:10px 0 18px 0;
        }
        .sup-input-shell-title{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:10px;
        }
        .sup-input-shell [data-testid="stWidgetLabel"] p{
            font-size:15px;
            line-height:1.55;
            font-weight:600;
            letter-spacing:.04em;
            text-transform:uppercase;
            color:#64748B;
        }
        .sup-kpi-shell{
            margin-top:8px;
            margin-bottom:18px;
        }
        .eng-section-label{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:8px;
        }
        .eng-transition{
            border-top:1px solid rgba(203,213,225,.75);
            padding-top:16px;
            margin-top:10px;
            margin-bottom:18px;
        }
        .eng-transition-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:6px;
        }
        .eng-transition-t{
            font-size:15px;
            line-height:1.55;
            color:#475569;
            max-width:980px;
        }
        .eng-body-title{
            font-size:15px;
            line-height:1.55;
            font-weight:600;
            color:#475569;
            margin:0 0 10px 0;
        }
        .sup-shell div[data-testid="stButton"] > button,
        .sup-shell div[data-testid="stDownloadButton"] > button{
            min-height:74px;
            border-radius:999px;
            padding:0 24px 0 18px;
            font-size:18px;
            font-weight:800;
            letter-spacing:-0.01em;
            border:1px solid rgba(148,163,184,.18);
            box-shadow:0 14px 28px rgba(15,23,42,.10);
            transition:transform .18s ease, box-shadow .18s ease, filter .18s ease;
            display:flex;
            align-items:center;
            justify-content:center;
            gap:12px;
        }
        .sup-shell div[data-testid="stButton"] > button:hover,
        .sup-shell div[data-testid="stDownloadButton"] > button:hover{
            transform:translateY(-1px);
            box-shadow:0 18px 30px rgba(15,23,42,.14);
            filter:saturate(1.03);
        }
        .sup-shell div[data-testid="stButton"] > button{
            color:#ffffff;
            border:1px solid rgba(185,28,28,.18);
            background:
                radial-gradient(circle at 20% 20%, rgba(255,255,255,.16), transparent 34%),
                linear-gradient(135deg,#B91C1C 0%,#991B1B 45%,#7F1D1D 100%);
        }
        .sup-shell div[data-testid="stButton"] > button p{
            font-size:18px;
            font-weight:800;
            color:#ffffff;
            margin:0;
        }
        .sup-shell div[data-testid="stDownloadButton"] > button{
            color:#ffffff;
            border:1px solid rgba(30,64,175,.18);
            background:
                radial-gradient(circle at 24% 24%, rgba(255,255,255,.18), transparent 28%),
                linear-gradient(135deg,#1E3A8A 0%,#1D4ED8 42%,#1E40AF 100%);
        }
        .sup-shell div[data-testid="stDownloadButton"] > button p{
            font-size:18px;
            font-weight:800;
            color:#ffffff;
            margin:0;
        }
        .sup-shell div[data-testid="stDownloadButton"] > button::before{
            content:"📄";
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:34px;
            height:34px;
            border-radius:999px;
            background:rgba(255,255,255,.18);
            border:1px solid rgba(255,255,255,.22);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.18);
            font-size:18px;
            font-weight:900;
            flex:0 0 auto;
        }
        .sup-shell div[data-testid="stButton"] > button::before{
            content:"⟲";
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:34px;
            height:34px;
            border-radius:999px;
            background:rgba(255,255,255,.14);
            border:1px solid rgba(255,255,255,.18);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.18);
            color:#ffffff;
            font-size:18px;
            font-weight:900;
            flex:0 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Seed all calculation inputs from shared state so every branch has valid values.
    fx_input = float(st.session_state[shared_state_key("fx")])
    pre_money_input = float(st.session_state[shared_state_key("pre_money")])
    inversion_clp_input = float(st.session_state[shared_state_key("inv_clp")])
    volume_input = float(st.session_state[shared_state_key("volume")])
    ebitda_unit_input = float(st.session_state[shared_state_key("ebitda_unit")])
    multiple_input = float(st.session_state[shared_state_key("multiple")])
    ronda_pct_input = float(st.session_state[shared_state_key("ronda_pct")]) / 100.0
    captura_input = float(captura_default or 1.0)
    alloc_manual_input = bool(st.session_state[shared_state_key("alloc_manual")])
    fluxial_pct_manual_input = float(st.session_state[shared_state_key("fluxial_pct_manual")]) / 100.0
    imelsa_pct_manual_input = float(st.session_state[shared_state_key("imelsa_pct_manual")]) / 100.0
    investment_currency_input = str(st.session_state.get(shared_state_key("investment_currency"), "USD"))
    aporte_no_pecuniario_clp = 0.0
    aporte_no_pecuniario_usd = 0.0

    def render_supuestos_panel():
        nonlocal fx_input, pre_money_input, inversion_clp_input, volume_input, ebitda_unit_input
        nonlocal multiple_input, ronda_pct_input, captura_input, alloc_manual_input
        nonlocal fluxial_pct_manual_input, imelsa_pct_manual_input, investment_currency_input
        nonlocal aporte_no_pecuniario_clp, aporte_no_pecuniario_usd
        nonlocal reset_requested

        st.markdown('<div class="sup-shell">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sup-head-main">{supuestos_title_map.get(bloque_sel, "Supuestos Clave del Modelo de Valorización")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="eng-body-title">{supuestos_subtitle_map.get(bloque_sel, "")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sup-input-shell"><div class="sup-input-shell-title">Panel de entrada</div>', unsafe_allow_html=True)

        if bloque_sel == "1. Fundamentos de Creación de Valor":
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                fx_input = st.number_input("FX CLP/USD", min_value=1, step=1, format="%d", key=prime_widget("fx"), on_change=sync_widget_to_state, args=("fx",))
                render_input_thousands_hint(fx_input)
            with pcol2:
                investment_currency_input = st.selectbox(
                    "Moneda de inversión",
                    ["CLP", "USD"],
                    key=prime_widget("investment_currency"),
                    on_change=sync_investment_currency,
                )
            with pcol3:
                valuation_basis_input = st.selectbox(
                    "Base de valorización pre-money",
                    ["BASE INVERSION + KNOW-HOW", "EBITDA potencial ciclo inicial"],
                    key=prime_widget("valuation_basis"),
                    on_change=sync_widget_to_state,
                    args=("valuation_basis",),
                )
            if valuation_basis_input == "EBITDA potencial ciclo inicial":
                pcol4, pcol5, pcol6 = st.columns(3)
                with pcol4:
                    volume_input = st.number_input("Volumen comercial", min_value=0, step=1, format="%d", key=prime_widget("volume"), on_change=sync_widget_to_state, args=("volume",))
                    render_input_thousands_hint(volume_input)
                with pcol5:
                    ebitda_unit_input = st.number_input("EBITDA unitario (USD)", min_value=0, step=1000, format="%d", key=prime_widget("ebitda_unit"), on_change=sync_widget_to_state, args=("ebitda_unit",))
                    render_input_thousands_hint(ebitda_unit_input, "US$")
                with pcol6:
                    multiple_input = st.slider("Múltiplo EBITDA", min_value=1.0, max_value=12.0, step=0.5, key=prime_widget("multiple"), on_change=sync_widget_to_state, args=("multiple",))
                action_col_1, action_col_2 = st.columns(2)
                with action_col_1:
                    if st.button("⟲ Restablecer supuestos", key=widget_key("reset_supuestos"), use_container_width=True):
                        reset_requested = True
                with action_col_2:
                    if REPORTLAB_AVAILABLE:
                        st.download_button(
                            label="📄 Descargar PDF de supuestos",
                            data=st.session_state[pdf_data_key],
                            file_name="Supuestos_Modelo_Valorizacion.pdf",
                            mime="application/pdf",
                            key=widget_key("download_supuestos_pdf"),
                            use_container_width=True,
                        )
                    else:
                        st.info("PDF deshabilitado: falta `reportlab`.", icon="ℹ️")
            inversion_clp_input = float(st.session_state[shared_state_key("inv_clp")])
            captura_input = float(captura_default or 1.0)
            ronda_pct_input = float(st.session_state[shared_state_key("ronda_pct")]) / 100.0
        elif bloque_sel == "2. Serie A: Inversión Inicial y Validación":
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                fx_input = st.number_input("FX CLP/USD", min_value=1, step=1, format="%d", key=prime_widget("fx"), on_change=sync_widget_to_state, args=("fx",))
                render_input_thousands_hint(fx_input)
            with pcol2:
                investment_currency_input = st.selectbox(
                    "Moneda de inversión",
                    ["CLP", "USD"],
                    key=prime_widget("investment_currency"),
                    on_change=sync_investment_currency,
                )
            with pcol3:
                if investment_currency_input == "USD":
                    inv_usd_widget_key = shared_widget_key("inv_usd_display")
                    if inv_usd_widget_key not in st.session_state:
                        st.session_state[inv_usd_widget_key] = int(round(float(st.session_state[shared_state_key("inv_clp")]) / fx_input)) if fx_input > 0 else 0
                    inversion_usd_input = st.number_input(
                        "Inversión piloto (USD)",
                        min_value=0,
                        step=10000,
                        format="%d",
                        key=inv_usd_widget_key,
                        on_change=sync_investment_usd_to_clp,
                    )
                    render_input_thousands_hint(inversion_usd_input, "US$")
                    inversion_clp_input = float(inversion_usd_input) * fx_input
                    st.session_state[shared_state_key("inv_clp")] = int(round(inversion_clp_input))
                    st.session_state.pop(shared_widget_key("inv_clp"), None)
                else:
                    inversion_clp_input = st.number_input("Inversión piloto (CLP)", min_value=0, step=10000000, format="%d", key=prime_widget("inv_clp"), on_change=sync_widget_to_state, args=("inv_clp",))
                    render_input_thousands_hint(inversion_clp_input, "$")
            volume_input = float(st.session_state[shared_state_key("volume")])
            ebitda_unit_input = float(st.session_state[shared_state_key("ebitda_unit")])
            multiple_input = float(st.session_state[shared_state_key("multiple")])
            captura_input = float(captura_default or 1.0)
            ronda_pct_input = float(st.session_state[shared_state_key("ronda_pct")]) / 100.0
            auto_ebitda_potencial = volume_input * ebitda_unit_input * multiple_input
            auto_base_en_usd = (total_base_knowhow_clp / fx_input) if fx_input > 0 else 0.0
            auto_valuation_basis = str(st.session_state.get(shared_state_key("valuation_basis", "base"), "EBITDA potencial ciclo inicial"))
            auto_valorizacion_fluxial = resolve_fluxial_pre_money(
                auto_valuation_basis,
                auto_base_en_usd,
                auto_ebitda_potencial,
            )
            auto_inversion_usd = inversion_clp_input / fx_input if fx_input > 0 else 0.0
            auto_post_money = auto_valorizacion_fluxial + auto_inversion_usd
            auto_imelsa_pct = (auto_inversion_usd / auto_post_money) if auto_post_money > 0 else 0.0
            auto_fluxial_pct = max(0.0, 1.0 - auto_imelsa_pct)

            if not alloc_manual_input:
                st.session_state[shared_state_key("fluxial_pct_manual")] = auto_fluxial_pct * 100.0
                st.session_state[shared_state_key("imelsa_pct_manual")] = auto_imelsa_pct * 100.0
                st.session_state.pop(shared_widget_key("fluxial_pct_manual"), None)
                st.session_state.pop(shared_widget_key("imelsa_pct_manual"), None)

            with st.columns(1)[0]:
                alloc_manual_input = st.checkbox(
                    "Asignar participación manual para Fluxial e IMELSA",
                    key=prime_widget("alloc_manual"),
                    on_change=sync_widget_to_state,
                    args=("alloc_manual",),
                )
            if alloc_manual_input:
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                manual_wrap_left, manual_col_1, manual_col_2, manual_col_3, manual_wrap_right = st.columns([0.18, 1.1, 1, 1, 0.18])
                with manual_col_1:
                    imelsa_pct_manual_input = st.slider(
                        "% IMELSA manual",
                        min_value=0.0,
                        max_value=100.0,
                        step=1.0,
                        format="%.0f%%",
                        key=prime_widget("imelsa_pct_manual"),
                        on_change=sync_widget_to_state,
                        args=("imelsa_pct_manual",),
                    ) / 100.0
                    fluxial_pct_manual_input = max(0.0, 1.0 - imelsa_pct_manual_input)
                    st.session_state[shared_state_key("fluxial_pct_manual")] = fluxial_pct_manual_input * 100.0
                    st.session_state.pop(shared_widget_key("fluxial_pct_manual"), None)
                    aporte_no_pecuniario_usd_manual = max(0.0, (auto_post_money * imelsa_pct_manual_input) - auto_inversion_usd) if auto_post_money > 0 else 0.0
                    aporte_no_pecuniario_usd = aporte_no_pecuniario_usd_manual
                    aporte_no_pecuniario_clp = aporte_no_pecuniario_usd_manual * fx_input
                with manual_col_2:
                    st.markdown(
                        f"""
                        <div style="margin-top:-42px;">
                        <div style="
                            border:1px solid rgba(148,163,184,.24);
                            border-radius:16px;
                            padding:16px 18px;
                            background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
                            box-shadow:0 6px 14px rgba(15,23,42,.04);
                        ">
                            <div style="font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px;">
                                Complemento automático
                            </div>
                            <div style="font-size:34px;font-weight:800;line-height:1;color:#0f172a;margin-bottom:8px;">
                                {fluxial_pct_manual_input:.0%}
                            </div>
                            <div style="font-size:13px;line-height:1.45;color:#475569;">
                                Se calcula como 100% menos la participación manual asignada a IMELSA.
                            </div>
                        </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with manual_col_3:
                    st.markdown(
                        f"""
                        <div style="margin-top:-42px;">
                        <div style="
                            border:1px solid rgba(191,219,254,.55);
                            border-radius:16px;
                            padding:16px 18px;
                            background:linear-gradient(90deg,#EFF8FF 0%,#DFF4FF 42%,#C6ECFF 100%);
                            box-shadow:0 6px 14px rgba(15,23,42,.04);
                        ">
                            <div style="font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:8px;">
                                Valor complementario
                            </div>
                            <div style="font-size:34px;font-weight:800;line-height:1;color:#0f172a;margin-bottom:8px;">
                                {format_clp(aporte_no_pecuniario_clp) if investment_currency_input == "CLP" else format_usd(aporte_no_pecuniario_usd)}
                            </div>
                            <div style="font-size:13px;line-height:1.45;color:#475569;">
                                {"Monto adicional reconocido en CLP para complementar la estructura de entrada de la Serie A." if investment_currency_input == "CLP" else "Monto adicional reconocido en USD para complementar la estructura de entrada de la Serie A."}
                            </div>
                        </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
        elif bloque_sel == "3. Valorización Post-Validación":
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                volume_input = st.number_input("Volumen comercial", min_value=0, step=1, format="%d", key=prime_widget("volume"), on_change=sync_widget_to_state, args=("volume",))
                render_input_thousands_hint(volume_input)
            with pcol2:
                ebitda_unit_input = st.number_input("EBITDA unitario (USD)", min_value=0, step=1000, format="%d", key=prime_widget("ebitda_unit"), on_change=sync_widget_to_state, args=("ebitda_unit",))
                render_input_thousands_hint(ebitda_unit_input, "US$")
            with pcol3:
                multiple_input = st.slider("Múltiplo EBITDA", min_value=1.0, max_value=12.0, step=0.5, key=prime_widget("multiple"), on_change=sync_widget_to_state, args=("multiple",))
            pcol4, pcol5 = st.columns(2)
            with pcol4:
                fx_input = st.number_input("FX CLP/USD", min_value=1, step=1, format="%d", key=prime_widget("fx"), on_change=sync_widget_to_state, args=("fx",))
                render_input_thousands_hint(fx_input)
            with pcol5:
                investment_currency_input = st.selectbox(
                    "Moneda de inversión",
                    ["CLP", "USD"],
                    key=prime_widget("investment_currency"),
                    on_change=sync_investment_currency,
                )
            captura_input = float(captura_default or 1.0)
            inversion_clp_input = float(st.session_state[shared_state_key("inv_clp")])
            ronda_pct_input = float(st.session_state[shared_state_key("ronda_pct")]) / 100.0
        else:
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                fx_input = st.number_input("FX CLP/USD", min_value=1, step=1, format="%d", key=prime_widget("fx"), on_change=sync_widget_to_state, args=("fx",))
                render_input_thousands_hint(fx_input)
            with pcol2:
                investment_currency_input = st.selectbox(
                    "Moneda de inversión",
                    ["CLP", "USD"],
                    key=prime_widget("investment_currency"),
                    on_change=sync_investment_currency,
                )
            with pcol3:
                ronda_pct_input = st.slider("Nueva cesión Serie B", min_value=5.0, max_value=90.0, step=1.0, format="%.0f%%", key=prime_widget("ronda_pct"), on_change=sync_widget_to_state, args=("ronda_pct",)) / 100.0
            pcol4, pcol5, pcol6 = st.columns(3)
            with pcol4:
                volume_input = st.number_input("Volumen comercial", min_value=0, step=1, format="%d", key=prime_widget("volume"), on_change=sync_widget_to_state, args=("volume",))
                render_input_thousands_hint(volume_input)
            with pcol5:
                ebitda_unit_input = st.number_input("EBITDA unitario (USD)", min_value=0, step=1000, format="%d", key=prime_widget("ebitda_unit"), on_change=sync_widget_to_state, args=("ebitda_unit",))
                render_input_thousands_hint(ebitda_unit_input, "US$")
            with pcol6:
                multiple_input = st.slider("Múltiplo EBITDA", min_value=1.0, max_value=12.0, step=0.5, key=prime_widget("multiple"), on_change=sync_widget_to_state, args=("multiple",))
            captura_input = float(captura_default or 1.0)
            inversion_clp_input = float(st.session_state[shared_state_key("inv_clp")])

        st.markdown("</div></div>", unsafe_allow_html=True)

    actions_anchor = None

    base_en_usd = (total_base_knowhow_clp / fx_input) if fx_input > 0 else 0.0
    ebitda_potencial_ciclo_inicial = volume_input * ebitda_unit_input
    ebitda_potencial_multiplicado = ebitda_potencial_ciclo_inicial * multiple_input
    valuation_basis_input = str(st.session_state.get(shared_state_key("valuation_basis", "base"), "EBITDA potencial ciclo inicial"))
    valorizacion_fluxial_hoy = resolve_fluxial_pre_money(
        valuation_basis_input,
        base_en_usd,
        ebitda_potencial_multiplicado,
    )
    inversion_usd = inversion_clp_input / fx_input if fx_input > 0 else 0.0
    post_money_serie_a = valorizacion_fluxial_hoy + inversion_usd
    imelsa_pct = (inversion_usd / post_money_serie_a) if post_money_serie_a > 0 else 0.0
    fluxial_pct = max(0.0, 1.0 - imelsa_pct)
    if bloque_sel == "2. Serie A: Inversión Inicial y Validación" and alloc_manual_input:
        fluxial_pct = fluxial_pct_manual_input
        imelsa_pct = imelsa_pct_manual_input
        aporte_no_pecuniario_usd = aporte_no_pecuniario_clp / fx_input if fx_input > 0 else 0.0
        post_money_serie_a += aporte_no_pecuniario_usd
    else:
        aporte_no_pecuniario_usd = max(0.0, (post_money_serie_a * imelsa_pct) - inversion_usd) if post_money_serie_a > 0 else 0.0
        aporte_no_pecuniario_clp = aporte_no_pecuniario_usd * fx_input

    # Serie B must inherit the ownership mix coming from block 2 / Serie A.
    base_fx_input = float(st.session_state.get(shared_state_key("fx", "base"), fx_default or 1))
    base_investment_currency_input = str(st.session_state.get(shared_state_key("investment_currency", "base"), "USD"))
    base_pre_money_input = float(st.session_state.get(shared_state_key("pre_money", "base"), pre_money_actual_default))
    base_volume_input = float(st.session_state.get(shared_state_key("volume", "base"), volumen_default))
    base_ebitda_unit_input = float(st.session_state.get(shared_state_key("ebitda_unit", "base"), ebitda_unit_default))
    base_multiple_input = float(st.session_state.get(shared_state_key("multiple", "base"), multiple_default or 1))
    base_inversion_clp_input = float(st.session_state.get(shared_state_key("inv_clp", "base"), inversion_clp_default))

    base_ebitda_potencial = base_volume_input * base_ebitda_unit_input * base_multiple_input
    base_valuation_basis_input = str(st.session_state.get(shared_state_key("valuation_basis", "base"), "EBITDA potencial ciclo inicial"))
    base_base_en_usd = (total_base_knowhow_clp / base_fx_input) if base_fx_input > 0 else 0.0
    base_valorizacion_fluxial_hoy = resolve_fluxial_pre_money(
        base_valuation_basis_input,
        base_base_en_usd,
        base_ebitda_potencial,
    )
    base_inversion_usd = base_inversion_clp_input / base_fx_input if base_fx_input > 0 else 0.0
    base_post_money_serie_a = base_valorizacion_fluxial_hoy + base_inversion_usd
    base_imelsa_pct = (base_inversion_usd / base_post_money_serie_a) if base_post_money_serie_a > 0 else 0.0
    base_fluxial_pct = max(0.0, 1.0 - base_imelsa_pct)
    base_alloc_manual = bool(st.session_state.get(shared_state_key("alloc_manual", "base"), False))
    if base_alloc_manual:
        base_fluxial_pct = float(st.session_state.get(shared_state_key("fluxial_pct_manual", "base"), base_fluxial_pct * 100.0)) / 100.0
        base_imelsa_pct = float(st.session_state.get(shared_state_key("imelsa_pct_manual", "base"), base_imelsa_pct * 100.0)) / 100.0
        base_aporte_no_pecuniario_usd = max(0.0, (base_post_money_serie_a * base_imelsa_pct) - base_inversion_usd) if base_post_money_serie_a > 0 else 0.0
        base_post_money_serie_a += base_aporte_no_pecuniario_usd
    else:
        base_aporte_no_pecuniario_usd = max(0.0, (base_post_money_serie_a * base_imelsa_pct) - base_inversion_usd) if base_post_money_serie_a > 0 else 0.0

    socios_actuales_total_pct = base_fluxial_pct + base_imelsa_pct
    if socios_actuales_total_pct > 0:
        fluxial_share_base = base_fluxial_pct / socios_actuales_total_pct
        imelsa_share_base = base_imelsa_pct / socios_actuales_total_pct
    else:
        fluxial_share_base = 0.0
        imelsa_share_base = 0.0

    post_fx_input = float(st.session_state.get(shared_state_key("fx", "post"), fx_default or 1))
    post_investment_currency_input = str(st.session_state.get(shared_state_key("investment_currency", "post"), "USD"))
    post_volume_input = float(st.session_state.get(shared_state_key("volume", "post"), volumen_default))
    post_ebitda_unit_input = float(st.session_state.get(shared_state_key("ebitda_unit", "post"), ebitda_unit_default))
    post_multiple_input = float(st.session_state.get(shared_state_key("multiple", "post"), multiple_post_default))
    post_ronda_pct_input = float(st.session_state.get(shared_state_key("ronda_pct", "post"), (ronda_pct_default or 0.70) * 100.0)) / 100.0
    post_ebitda_total = post_volume_input * post_ebitda_unit_input
    post_valor_post_piloto = post_ebitda_total * post_multiple_input
    post_upside_pct = ((post_valor_post_piloto / base_post_money_serie_a) - 1.0) if base_post_money_serie_a > 0 else 0.0
    post_valor_imelsa_post = post_valor_post_piloto * base_imelsa_pct
    post_capital_raise = post_valor_post_piloto * post_ronda_pct_input
    post_money_serie_b_pdf = post_valor_post_piloto + post_capital_raise
    post_pct_remanente = 1.0 - post_ronda_pct_input
    post_fluxial_post_b = post_pct_remanente * fluxial_share_base
    post_imelsa_post_b = post_pct_remanente * imelsa_share_base
    post_valor_post_piloto_clp = post_valor_post_piloto * post_fx_input
    post_capital_raise_clp = post_capital_raise * post_fx_input
    post_money_serie_b_clp_pdf = post_money_serie_b_pdf * post_fx_input
    ebitda_total = ebitda_potencial_ciclo_inicial
    valor_post_piloto = ebitda_total * multiple_input
    upside_pct = ((valor_post_piloto / base_post_money_serie_a) - 1.0) if base_post_money_serie_a > 0 else 0.0
    valor_imelsa_post = valor_post_piloto * base_imelsa_pct
    capital_raise = valor_post_piloto * ronda_pct_input
    post_money_serie_b = valor_post_piloto + capital_raise
    pct_remanente = 1.0 - ronda_pct_input
    fluxial_post_b = pct_remanente * fluxial_share_base
    imelsa_post_b = pct_remanente * imelsa_share_base
    valor_fluxial_post_b = post_money_serie_b * fluxial_post_b
    valor_imelsa_post_b = post_money_serie_b * imelsa_post_b
    base_post_money_serie_a_clp = base_post_money_serie_a * fx_input
    ebitda_total_clp = ebitda_total * fx_input
    valor_post_piloto_clp = valor_post_piloto * fx_input
    valor_imelsa_post_clp = valor_imelsa_post * fx_input
    capital_raise_clp = capital_raise * fx_input
    post_money_serie_b_clp = post_money_serie_b * fx_input
    valor_fluxial_post_b_clp = valor_fluxial_post_b * fx_input
    valor_imelsa_post_b_clp = valor_imelsa_post_b * fx_input

    def build_valorizacion_supuestos_pdf() -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.2 * cm,
            leftMargin=1.2 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm,
        )
        styles = getSampleStyleSheet()
        h1 = styles["Heading1"]
        h2 = styles["Heading2"]
        body = styles["BodyText"]
        body.fontSize = 9
        body.leading = 12
        table_header = styles["BodyText"].clone("TableHeader")
        table_header.fontName = "Helvetica-Bold"
        table_header.fontSize = 8
        table_header.leading = 10
        table_header.wordWrap = "CJK"
        table_cell = styles["BodyText"].clone("TableCell")
        table_cell.fontName = "Helvetica"
        table_cell.fontSize = 8
        table_cell.leading = 10
        table_cell.wordWrap = "CJK"
        elements = []

        investment_currency_label = "CLP" if base_investment_currency_input == "CLP" else "USD"
        valuation_basis_label_pdf = "BASE INVERSION + KNOW-HOW" if base_valuation_basis_input == "BASE INVERSION + KNOW-HOW" else "EBITDA potencial ciclo inicial"
        post_multiple_assumption = post_multiple_input
        post_ronda_assumption = post_ronda_pct_input
        post_money_serie_a_clp_pdf = base_post_money_serie_a * base_fx_input

        def add_table(title: str, rows: list[list[str]], col_widths: list[float]):
            elements.append(Paragraph(title, h2))
            wrapped_rows = []
            for idx, row in enumerate(rows):
                row_style = table_header if idx == 0 else table_cell
                wrapped_rows.append([Paragraph(str(cell), row_style) for cell in row])
            table = Table(wrapped_rows, colWidths=col_widths, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF3FF")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("LEADING", (0, 0), (-1, -1), 10),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 1), (-1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBFF")]),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 0.35 * cm))

        elements.append(Paragraph("Supuestos y KPI Clave - Modelo de Valorización", h1))
        elements.append(Paragraph("Resumen técnico de ingeniería financiera con los supuestos activos y los indicadores actualmente visibles del modelo.", body))
        elements.append(Spacer(1, 0.35 * cm))

        assumptions_rows = [
            ["Parámetro", "Valor", "Observación"],
            ["FX CLP/USD", f"{base_fx_input:,.0f}".replace(",", "."), "Tipo de cambio activo del modelo"],
            ["Base de valorización pre-money", valuation_basis_label_pdf, "Mecanismo activo para valor pre-money"],
            ["Moneda de inversión Serie A", investment_currency_label, "Moneda visible del bloque 2"],
            ["Inversión piloto (CLP)", format_clp(base_inversion_clp_input), "Capital base de entrada al piloto"],
            ["Inversión piloto (USD)", format_usd(base_inversion_usd), "Conversión del capital de entrada usando FX"],
            ["Volumen comercial", f"{base_volume_input:,.0f}".replace(",", "."), "Supuesto operativo del escenario base"],
            ["EBITDA unitario", format_usd(base_ebitda_unit_input), "Margen operativo unitario base"],
            ["Múltiplo EBITDA base", f"{base_multiple_input:.2f}x", "Supuesto usado en bloques 1 a 3"],
            ["Múltiplo EBITDA Serie B", f"{post_multiple_assumption:.2f}x", "Supuesto heredado para escalamiento"],
            ["Nueva cesión Serie B", f"{post_ronda_assumption:.1%}", "Participación objetivo para nuevos inversionistas"],
            ["Asignación manual Serie A", "Sí" if base_alloc_manual else "No", "Activa el complemento de valor para IMELSA"],
        ]
        if base_alloc_manual:
            assumptions_rows.extend(
                [
                    ["% IMELSA manual", f"{base_imelsa_pct:.1%}", "Participación fijada manualmente"],
                    ["% Fluxial manual", f"{base_fluxial_pct:.1%}", "Complemento automático de participación"],
                    ["Valor complementario (USD)", format_usd(base_aporte_no_pecuniario_usd), "Aporte adicional reconocido en la Serie A"],
                ]
            )
        add_table("Supuestos acordados", assumptions_rows, [5.6 * cm, 4.0 * cm, 7.2 * cm])

        valuation_rows = [
            ["KPI", "Valor", "Lectura"],
            ["Pre Money actual (USD)", format_usd(base_post_money_serie_a), "Base heredada desde Serie A"],
            ["EBITDA total", format_usd(post_ebitda_total), "EBITDA unitario multiplicado por volumen"],
            ["Valorización post piloto (USD)", format_usd(post_valor_post_piloto), "EBITDA total multiplicado por el múltiplo activo"],
            ["Valorización post piloto (CLP)", format_clp(post_valor_post_piloto_clp), "Referencia equivalente en CLP"],
            ["Upside vs actual", f"{post_upside_pct:.1%}", "Crecimiento de valorización post piloto respecto de Pre Money actual"],
            ["Valor por 50% post piloto", format_usd(post_valor_imelsa_post), "Valor implícito de una participación equivalente al 50% post piloto"],
        ]
        add_table("Valorización post-validación", valuation_rows, [6.2 * cm, 4.1 * cm, 6.5 * cm])

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    if bloque_sel == "1. Fundamentos de Creación de Valor":
        st.markdown(
            """
            <div class="eng-transition">
              <div class="eng-transition-k">Capa de análisis financiero</div>
              <div class="eng-transition-t">A continuación se despliega la proyección integrada del modelo, sus drivers unitarios y la lectura consolidada de desempeño económico.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if eerrv2_error:
            st.error(f"No se pudo cargar EERRv2: {eerrv2_error}")
        elif df_eerrv2.empty:
            st.warning("La hoja EERRv2 no tiene datos disponibles.")
        else:
            st.markdown(
                """
                <style>
                .eerr-mini{
                    border-radius:16px;padding:14px 15px;border:1px solid rgba(148,163,184,.22);
                    background:linear-gradient(90deg,#EFF8FF 0%,#DFF4FF 42%,#C6ECFF 100%);
                    min-height:132px;
                }
                .eerr-mini-h{font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:6px}
                .eerr-mini-v{font-size:28px;font-weight:800;color:#0f172a;line-height:1.05;margin-bottom:4px}
                .eerr-mini-s{font-size:12px;color:#475569}
                </style>
                """,
                unsafe_allow_html=True,
            )
            eerr_payload = build_eerrv2_payload(
                df_eerrv2,
                tuple(sorted((str(k), "" if pd.isna(v) else str(v)) for k, v in model_map.items())),
                ebitda_unit_default,
            )
            eerr_data = eerr_payload["eerr_data"]
            cash_data = eerr_payload["cash_data"]
            kpi_map = eerr_payload["kpi_map"]
            precio_venta_turbina = eerr_payload["precio_venta_turbina"]
            costo_estimado_turbina = eerr_payload["costo_estimado_turbina"]
            ebitda_unitario_val = eerr_payload["ebitda_unitario_val"]
            capex_inicial_eerr = eerr_payload["capex_inicial_eerr"]
            chart_df = eerr_payload["chart_df"]

            col_eerr_1, col_eerr_2 = st.columns([1.7, 1])
            with col_eerr_1:
                st.markdown('<div class="eng-section-label">Lectura financiera integrada</div>', unsafe_allow_html=True)
                st.markdown('<div class="eng-body-title">Proyección Financiera Integrada " Etapa comercial-escenario conservador"</div>', unsafe_allow_html=True)
                render_engineering_html_table(
                    eerr_data,
                    bold_labels={"Margen bruto (USD)", "EBITDA (USD)"},
                    height=360,
                )
            with col_eerr_2:
                st.markdown('<div class="eng-section-label">Drivers técnicos del modelo</div>', unsafe_allow_html=True)
                st.markdown('<div class="eng-body-title">Drivers unitarios del modelo</div>', unsafe_allow_html=True)
                drv_row_1 = st.columns(2)
                with drv_row_1[0]:
                    kpi_card("Precio venta / turbina", format_usd(precio_venta_turbina), "Supuesto comercial unitario del modelo.", variant="sky")
                with drv_row_1[1]:
                    kpi_card("Costo estimado / turbina", format_usd(costo_estimado_turbina), "Costo directo unitario usado en valorización.", variant="sky")
                drv_row_2 = st.columns(2)
                with drv_row_2[0]:
                    kpi_card("EBITDA unitario", format_usd(ebitda_unitario_val), "Margen operativo unitario por turbina.", variant="sky")
            with drv_row_2[1]:
                kpi_card("CAPEX inicial", format_usd(capex_inicial_eerr), "Valor base tomado de EERRv2 celda C15.", variant="sky")

            st.markdown('<div class="eng-body-title">Flujo de Caja del Proyecto y Estrategia de Reinversión</div>', unsafe_allow_html=True)
            render_engineering_html_table(
                cash_data,
                bold_labels={"EBITDA", "Flujo de caja neto"},
                height=420,
            )
            st.markdown('<div class="eng-section-label">Desempeño consolidado</div>', unsafe_allow_html=True)
            st.markdown('<div class="eng-body-title">Desempeño Financiero y Operativo del Proyecto</div>', unsafe_allow_html=True)
            mini_cards = [
                ("Ingresos promedio", kpi_map.get("Ingresos promedio (USD)", "-"), "Promedio anual del escenario EERR."),
                ("EBITDA promedio", kpi_map.get("EBITDA promedio (USD)", "-"), "Promedio anual operativo."),
                ("Margen EBITDA", kpi_map.get("Margen EBITDA promedio (%)", "-"), "Margen consolidado del modelo."),
                ("Saldo caja año 5", kpi_map.get("Saldo caja final año 5 (USD)", "-"), "Posición final estimada de caja."),
            ]
            mini_cols = st.columns(4)
            for idx, (title, value, subtitle) in enumerate(mini_cards):
                with mini_cols[idx]:
                    st.markdown(
                        f"""
                        <div class="eerr-mini">
                          <div class="eerr-mini-h">{title}</div>
                          <div class="eerr-mini-v">{value}</div>
                          <div class="eerr-mini-s">{subtitle}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            fig_eerr = go.Figure()
            fig_eerr.add_trace(go.Bar(x=chart_df["Año"], y=chart_df["Ingresos_MM"], name="Ingresos", marker_color="#CFE8DA", hovertemplate="Ingresos %{x}: US$%{customdata:,.0f}<extra></extra>", customdata=chart_df["Ingresos"]))
            fig_eerr.add_trace(go.Bar(x=chart_df["Año"], y=chart_df["EBITDA_MM"], name="EBITDA", marker_color="#0F766E", hovertemplate="EBITDA %{x}: US$%{customdata:,.0f}<extra></extra>", customdata=chart_df["EBITDA"]))
            fig_eerr.add_trace(go.Scatter(x=chart_df["Año"], y=chart_df["Caja_MM"], name="Flujo caja neto", mode="lines+markers", line=dict(color="#1D4ED8", width=3), marker=dict(size=9, color="#1D4ED8"), hovertemplate="Caja neta %{x}: US$%{customdata:,.0f}<extra></extra>", customdata=chart_df["Caja_neta"], yaxis="y2"))
            fig_eerr.update_layout(title="Trayectoria operativa del modelo EERRv2", barmode="group", height=420, margin=dict(l=10, r=10, t=60, b=10), plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), yaxis=dict(title="Ingresos / EBITDA (MM USD)", showgrid=True, gridcolor="rgba(148,163,184,0.22)", zeroline=False), yaxis2=dict(title="Caja neta (MM USD)", overlaying="y", side="right", showgrid=False, zeroline=False))
            st.plotly_chart(fig_eerr, use_container_width=True)
            actions_anchor = st.container()

    elif bloque_sel == "2. Serie A: Inversión Inicial y Validación":
        selected_basis_label = "BASE INVERSION + KNOW-HOW" if valuation_basis_input == "BASE INVERSION + KNOW-HOW" else "EBITDA potencial ciclo inicial"
        post_money_serie_a_clp = post_money_serie_a * fx_input
        if investment_currency_input == "CLP":
            metric_cols = st.columns(3)
            mk2, mk3, mk4 = metric_cols
            with mk2:
                kpi_card("Post-money Serie A", format_clp(post_money_serie_a_clp), "Valorización posterior al ingreso para construir el piloto.")
        else:
            metric_cols = st.columns(4)
            mk1, mk2, mk3, mk4 = metric_cols
            with mk1:
                kpi_card("Inv. convertida a USD", format_usd(inversion_usd), "Capital de entrada del piloto convertido con el FX editable.")
            with mk2:
                kpi_card("Post-money Serie A", format_usd(post_money_serie_a), "Valorización posterior al ingreso para construir el piloto.")
        with mk3:
            kpi_card("% IMELSA", f"{imelsa_pct:.1%}", "Participación posterior al ingreso de capital.")
        with mk4:
            kpi_card("% Fluxial", f"{fluxial_pct:.1%}", "Participación remanente posterior al piloto.")
        st.markdown(
            """
            <style>
            .seriea-panel{
                border-radius:22px;
                padding:16px 18px 14px 18px;
                border:1px solid rgba(148,163,184,.20);
                background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
                box-shadow:0 10px 24px rgba(15,23,42,.05);
                height:100%;
            }
            .seriea-panel-k{
                font-size:11px;
                font-weight:800;
                letter-spacing:.12em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:8px;
            }
            .seriea-panel-t{
                font-size:16px;
                font-weight:800;
                color:#0f172a;
                line-height:1.3;
                margin-bottom:10px;
            }
            .seriea-panel-s{
                font-size:13px;
                line-height:1.5;
                color:#475569;
            }
            .seriea-shell{
                border-radius:24px;
                padding:18px 18px 14px 18px;
                border:1px solid rgba(148,163,184,.18);
                background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
                box-shadow:0 12px 26px rgba(15,23,42,.05);
                min-height:100%;
            }
            .seriea-shell-k{
                font-size:11px;
                font-weight:800;
                letter-spacing:.12em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:8px;
            }
            .seriea-shell-t{
                font-size:22px;
                font-weight:800;
                color:#0f172a;
                line-height:1.15;
                margin-bottom:8px;
            }
            .seriea-shell-s{
                font-size:13px;
                line-height:1.55;
                color:#475569;
                margin-bottom:12px;
            }
            .seriea-mini-band{
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                margin:10px 0 14px 0;
            }
            .seriea-mini-chip{
                border-radius:999px;
                padding:8px 12px;
                border:1px solid rgba(29,78,216,.12);
                background:#F8FBFF;
                font-size:12px;
                color:#334155;
            }
            .seriea-foot{
                border-top:1px solid rgba(148,163,184,.16);
                padding-top:10px;
                margin-top:10px;
                font-size:12px;
                color:#64748B;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if investment_currency_input == "CLP":
            serie_a = pd.DataFrame([
                {"Métrica": f"Valorización base ({selected_basis_label})", "Valor": format_clp(valorizacion_fluxial_hoy * fx_input)},
                {"Métrica": "Inversión piloto (CLP)", "Valor": format_clp(inversion_clp_input)},
                {"Métrica": "Post-money", "Valor": format_clp(post_money_serie_a_clp)},
                {"Métrica": "% IMELSA", "Valor": f"{imelsa_pct:.1%}"},
                {"Métrica": "% Fluxial", "Valor": f"{fluxial_pct:.1%}"},
            ])
        else:
            serie_a = pd.DataFrame([
                {"Métrica": f"Valorización base ({selected_basis_label})", "Valor": format_usd(valorizacion_fluxial_hoy)},
                {"Métrica": "Inversión piloto (USD)", "Valor": format_usd(inversion_usd)},
                {"Métrica": "Post-money", "Valor": format_usd(post_money_serie_a)},
                {"Métrica": "% IMELSA", "Valor": f"{imelsa_pct:.1%}"},
                {"Métrica": "% Fluxial", "Valor": f"{fluxial_pct:.1%}"},
            ])
        if alloc_manual_input:
            serie_a = pd.concat(
                [
                    serie_a,
                    pd.DataFrame(
                        [
                            {
                                "Métrica": "Valor complementario (CLP)" if investment_currency_input == "CLP" else "Valor complementario (USD)",
                                "Valor": format_clp(aporte_no_pecuniario_clp) if investment_currency_input == "CLP" else format_usd(aporte_no_pecuniario_usd),
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
        cap_table_a = pd.DataFrame({
            "Socio": ["Fluxial Wind", "IMELSA"],
            "Participación": [fluxial_pct, imelsa_pct],
            "Valor implícito (USD)": [post_money_serie_a * fluxial_pct, post_money_serie_a * imelsa_pct],
        }).sort_values("Participación", ascending=True).reset_index(drop=True)
        cap_table_a["Participación_pct"] = cap_table_a["Participación"] * 100
        cap_table_a["Etiqueta"] = cap_table_a.apply(
            lambda r: f"{r['Participación']:.1%} · {format_usd(r['Valor implícito (USD)'])}",
            axis=1,
        )
        c1, c2 = st.columns([0.95, 1.05])
        with c1:
            st.markdown(
                f"""
                <div class="seriea-shell">
                  <div class="seriea-shell-k">Lectura económica</div>
                  <div class="seriea-shell-t">Resumen de entrada Serie A</div>
                  <div class="seriea-shell-s">Conversión de inversión, valorización base activa, post-money y estructura societaria proyectada tras el ingreso de capital.</div>
                  <div class="seriea-mini-band">
                    <div class="seriea-mini-chip">Base activa: {selected_basis_label}</div>
                    <div class="seriea-mini-chip">Post-money: {format_usd(post_money_serie_a)}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            st.dataframe(style_engineering_table(serie_a), hide_index=True, use_container_width=True, height=310)
            st.markdown(
                f"""
                <div class="seriea-foot">
                  La tabla resume la valorización base seleccionada, el capital invertido y la distribución accionaria resultante.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            fig_cap_a = px.bar(
                cap_table_a,
                x="Participación_pct",
                y="Socio",
                orientation="h",
                text="Etiqueta",
                color="Socio",
                color_discrete_map={"Fluxial Wind": "#1D4ED8", "IMELSA": "#0F766E"},
                title=None,
            )
            fig_cap_a.update_traces(
                textposition="inside",
                insidetextanchor="middle",
                marker=dict(line=dict(color="rgba(255,255,255,0.85)", width=1.2)),
                hovertemplate="<b>%{y}</b><br>Participación: %{customdata[0]:.1%}<br>Valor implícito: US$%{customdata[1]:,.0f}<extra></extra>",
                customdata=np.stack([cap_table_a["Participación"], cap_table_a["Valor implícito (USD)"]], axis=-1),
            )
            fig_cap_a.update_layout(
                showlegend=False,
                xaxis_tickformat=".0f",
                margin=dict(l=8, r=8, t=56, b=8),
                height=330,
                plot_bgcolor="white",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#334155", size=13),
                title=None,
            )
            fig_cap_a.update_xaxes(
                title="Participación accionaria (%)",
                ticksuffix="%",
                range=[0, max(100, cap_table_a["Participación_pct"].max() * 1.08)],
                showgrid=True,
                gridcolor="rgba(148,163,184,0.22)",
                zeroline=False,
            )
            fig_cap_a.update_yaxes(title="", showgrid=False)
            st.markdown(
                f"""
                <div class="seriea-shell">
                  <div class="seriea-shell-k">Cap table proyectado</div>
                  <div class="seriea-shell-t">Distribución posterior al piloto</div>
                  <div class="seriea-shell-s">Lectura visual de participación y valor implícito por socio después del cierre de la Serie A.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig_cap_a, use_container_width=True, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
            st.markdown(
                f"""
                <div class="seriea-foot">
                  Fluxial retiene {fluxial_pct:.1%} e IMELSA consolida {imelsa_pct:.1%} del cap table post-piloto.
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif bloque_sel == "3. Valorización Post-Validación":
        mk1, mk2, mk3, mk4, mk5 = st.columns(5)
        if investment_currency_input == "CLP":
            pre_money_display = format_clp(base_post_money_serie_a_clp)
            ebitda_total_display = format_clp(ebitda_total_clp)
            valor_post_piloto_display = format_clp(valor_post_piloto_clp)
            valor_imelsa_display = format_clp(valor_imelsa_post_clp)
            sens_title = "Sensibilidad de valorización vs volumen comercial (MM CLP)"
            sens_label = "Valorización post piloto (MM CLP)"
            sens_tickprefix = "$"
            sens_values = (base_post_money_serie_a_clp + (sensibilidad["Volumen"] * ebitda_unit_input * multiple_input * fx_input)) if False else None
        else:
            pre_money_display = format_usd(base_post_money_serie_a)
            ebitda_total_display = format_usd(ebitda_total)
            valor_post_piloto_display = format_usd(valor_post_piloto)
            valor_imelsa_display = format_usd(valor_imelsa_post)
            sens_title = "Sensibilidad de valorización vs volumen comercial"
            sens_label = "Valorización post piloto (MM USD)"
            sens_tickprefix = "US$"
        with mk1:
            kpi_card(f"Pre Money actual ({investment_currency_input})", pre_money_display, "Valor base heredado desde Post-money Serie A del bloque 2.")
        with mk2:
            kpi_card(f"EBITDA total ({investment_currency_input})", ebitda_total_display, "EBITDA unitario multiplicado por el volumen.")
        with mk3:
            kpi_card("Valorización post piloto", valor_post_piloto_display, "EBITDA total multiplicado por el múltiplo activo.", variant="sky")
        with mk4:
            kpi_card("Upside vs actual", f"{upside_pct:.1%}", "Crecimiento de valorización post piloto respecto de Pre Money actual.")
        with mk5:
            kpi_card("Valor por 50% post piloto", valor_imelsa_display, "Valor implícito de una participación equivalente al 50% post piloto.")
        st.markdown("#### Motor económico del piloto")
        sensibilidad = pd.DataFrame({"Volumen": [max(1, volume_input * f) for f in [0.6, 0.8, 1.0, 1.2, 1.4]]})
        sensibilidad["Valorización_post_piloto"] = sensibilidad["Volumen"] * ebitda_unit_input * multiple_input
        if investment_currency_input == "CLP":
            sensibilidad["Valorización_millones"] = (sensibilidad["Valorización_post_piloto"] * fx_input) / 1e6
            sensibilidad["Etiqueta"] = sensibilidad["Valorización_millones"].map(lambda v: f"${v:.2f}M")
            sens_customdata = np.stack([sensibilidad["Valorización_post_piloto"] * fx_input, sensibilidad["Volumen"] * ebitda_unit_input * fx_input], axis=-1)
            sens_hover = "<b>Volumen:</b> %{x:.0f} turbinas<br><b>Valorización:</b> $%{customdata[0]:,.0f}<br><b>EBITDA total:</b> $%{customdata[1]:,.0f}<extra></extra>"
            sens_base_y = valor_post_piloto_clp / 1e6
        else:
            sensibilidad["Valorización_millones"] = sensibilidad["Valorización_post_piloto"] / 1e6
            sensibilidad["Etiqueta"] = sensibilidad["Valorización_millones"].map(lambda v: f"US${v:.2f}M")
            sens_customdata = np.stack([sensibilidad["Valorización_post_piloto"], sensibilidad["Volumen"] * ebitda_unit_input], axis=-1)
            sens_hover = "<b>Volumen:</b> %{x:.0f} turbinas<br><b>Valorización:</b> US$%{customdata[0]:,.0f}<br><b>EBITDA total:</b> US$%{customdata[1]:,.0f}<extra></extra>"
            sens_base_y = valor_post_piloto / 1e6
        fig_sens = px.line(sensibilidad, x="Volumen", y="Valorización_millones", markers=True, text="Etiqueta", title=sens_title, labels={"Valorización_millones": sens_label, "Volumen": "Volumen comercial (turbinas)"})
        fig_sens.update_traces(line=dict(color="#0F766E", width=4), marker=dict(size=10, color="#0F766E", line=dict(width=2, color="#ECFDF5")), textposition="top center", hovertemplate=sens_hover, customdata=sens_customdata)
        fig_sens.add_vline(x=volume_input, line_width=1.5, line_dash="dash", line_color="#1D4ED8", opacity=0.8)
        fig_sens.add_hline(y=sens_base_y, line_width=1.5, line_dash="dot", line_color="#1D4ED8", opacity=0.8)
        fig_sens.add_annotation(x=volume_input, y=sens_base_y, text=(f"Base: {volume_input:,.0f} turbinas / ${sens_base_y:.2f}M" if investment_currency_input == "CLP" else f"Base: {volume_input:,.0f} turbinas / US${sens_base_y:.2f}M").replace(",", "."), showarrow=True, arrowhead=2, ax=40, ay=-40, bgcolor="rgba(255,255,255,0.95)", bordercolor="#BFDBFE", font=dict(size=11, color="#0F172A"))
        fig_sens.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=430, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", hovermode="x unified")
        fig_sens.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.22)", zeroline=False)
        fig_sens.update_yaxes(tickprefix=sens_tickprefix, ticksuffix="M", showgrid=True, gridcolor="rgba(148,163,184,0.22)", zeroline=False)
        st.plotly_chart(fig_sens, use_container_width=True)

    else:
        mk1, mk2, mk3, mk4 = st.columns(4)
        if investment_currency_input == "CLP":
            val_base_b_display = format_clp(valor_post_piloto_clp)
            capital_b_display = format_clp(capital_raise_clp)
            post_money_b_display = format_clp(post_money_serie_b_clp)
        else:
            val_base_b_display = format_usd(valor_post_piloto)
            capital_b_display = format_usd(capital_raise)
            post_money_b_display = format_usd(post_money_serie_b)
        with mk1:
            kpi_card("Valorización base Serie B", val_base_b_display, "Pre-money sugerido para la segunda ronda.")
        with mk2:
            kpi_card("Capital Serie B", capital_b_display, "Capital implícito a levantar para la nueva cesión objetivo.")
        with mk3:
            kpi_card("Post-money Serie B", post_money_b_display, "Valorización posterior al cierre de la ronda.", variant="sky")
        with mk4:
            kpi_card("% remanente socios actuales", f"{pct_remanente:.1%}", "Participación conjunta remanente de Fluxial + IMELSA.")
        st.markdown(
            """
            <style>
            .serieb-shell{
                border-radius:24px;
                padding:18px 18px 14px 18px;
                border:1px solid rgba(148,163,184,.18);
                background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
                box-shadow:0 12px 26px rgba(15,23,42,.05);
                min-height:100%;
            }
            .serieb-shell-k{
                font-size:11px;
                font-weight:800;
                letter-spacing:.12em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:8px;
            }
            .serieb-shell-t{
                font-size:22px;
                font-weight:800;
                color:#0f172a;
                line-height:1.15;
                margin-bottom:8px;
            }
            .serieb-shell-s{
                font-size:13px;
                line-height:1.55;
                color:#475569;
                margin-bottom:12px;
            }
            .serieb-mini-band{
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                margin:10px 0 14px 0;
            }
            .serieb-mini-chip{
                border-radius:999px;
                padding:8px 12px;
                border:1px solid rgba(15,118,110,.12);
                background:#F8FBFF;
                font-size:12px;
                color:#334155;
            }
            .serieb-foot{
                border-top:1px solid rgba(148,163,184,.16);
                padding-top:10px;
                margin-top:10px;
                font-size:12px;
                color:#64748B;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        cap_table_b = pd.DataFrame({"Socio": ["Nuevos inversionistas", "Fluxial Wind", "IMELSA"], "Participación": [ronda_pct_input, fluxial_post_b, imelsa_post_b], "Valor económico": [post_money_serie_b * ronda_pct_input, valor_fluxial_post_b, valor_imelsa_post_b]}).sort_values("Participación", ascending=True).reset_index(drop=True)
        if investment_currency_input == "CLP":
            cap_table_b["Valor económico"] = cap_table_b["Valor económico"] * fx_input
        cap_table_b["Participación_pct"] = cap_table_b["Participación"] * 100
        cap_table_b["Etiqueta"] = cap_table_b.apply(lambda r: f"{r['Participación']:.1%}  ·  {(format_clp(r['Valor económico']) if investment_currency_input == 'CLP' else format_usd(r['Valor económico']))}", axis=1)
        fig_cap_b = px.bar(cap_table_b, x="Participación_pct", y="Socio", orientation="h", text="Etiqueta", color="Socio", color_discrete_map={"Nuevos inversionistas": "#C58940", "Fluxial Wind": "#1D4ED8", "IMELSA": "#0F766E"}, title=None)
        fig_cap_b.update_traces(textposition="inside", insidetextanchor="middle", marker=dict(line=dict(color="rgba(255,255,255,0.85)", width=1.2)), hovertemplate=("<b>%{y}</b><br>Participación: %{customdata[0]:.1%}<br>Valor económico: $%{customdata[1]:,.0f}<extra></extra>" if investment_currency_input == "CLP" else "<b>%{y}</b><br>Participación: %{customdata[0]:.1%}<br>Valor económico: US$%{customdata[1]:,.0f}<extra></extra>"), customdata=np.stack([cap_table_b["Participación"], cap_table_b["Valor económico"]], axis=-1))
        fig_cap_b.update_layout(showlegend=False, margin=dict(l=8, r=8, t=18, b=16), height=360, bargap=0.22, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#334155", size=13), title=None)
        fig_cap_b.update_xaxes(title="Participación accionaria (%)", ticksuffix="%", range=[0, max(100, cap_table_b["Participación_pct"].max() * 1.08)], showgrid=True, gridcolor="rgba(148,163,184,0.22)", zeroline=False)
        fig_cap_b.update_yaxes(title="", showgrid=False)
        if investment_currency_input == "CLP":
            serie_b_rows = pd.DataFrame([
                {"Métrica": "Pre-money Serie B (CLP)", "Valor": format_clp(valor_post_piloto_clp)},
                {"Métrica": "Capital a levantar (CLP)", "Valor": format_clp(capital_raise_clp)},
                {"Métrica": "Post-money Serie B (CLP)", "Valor": format_clp(post_money_serie_b_clp)},
                {"Métrica": "% Fluxial post ronda", "Valor": f"{fluxial_post_b:.1%}"},
                {"Métrica": "% IMELSA post ronda", "Valor": f"{imelsa_post_b:.1%}"},
            ])
        else:
            serie_b_rows = pd.DataFrame([
                {"Métrica": "Pre-money Serie B (USD)", "Valor": format_usd(valor_post_piloto)},
                {"Métrica": "Capital a levantar (USD)", "Valor": format_usd(capital_raise)},
                {"Métrica": "Post-money Serie B (USD)", "Valor": format_usd(post_money_serie_b)},
                {"Métrica": "% Fluxial post ronda", "Valor": f"{fluxial_post_b:.1%}"},
                {"Métrica": "% IMELSA post ronda", "Valor": f"{imelsa_post_b:.1%}"},
            ])
        c1, c2 = st.columns([0.95, 1.05])
        with c1:
            st.markdown(
                f"""
                <div class="serieb-shell">
                  <div class="serieb-shell-k">Lectura de ronda</div>
                  <div class="serieb-shell-t">Resumen económico Serie B</div>
                  <div class="serieb-shell-s">La tabla consolida pre-money, capital nuevo, post-money y la estructura accionaria remanente tras la expansión comercial.</div>
                  <div class="serieb-mini-band">
                    <div class="serieb-mini-chip">Moneda visible: {investment_currency_input}</div>
                    <div class="serieb-mini-chip">Nueva cesión: {ronda_pct_input:.1%}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            st.dataframe(style_engineering_table(serie_b_rows), hide_index=True, use_container_width=True, height=310)
            st.markdown(
                """
                <div class="serieb-foot">
                  La tabla resume la valorización base de la ronda, el capital nuevo comprometido y la distribución accionaria posterior al cierre.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="serieb-shell">
                  <div class="serieb-shell-k">Cap table proyectado</div>
                  <div class="serieb-shell-t">Distribución posterior a Serie B</div>
                  <div class="serieb-shell-s">Lectura visual de participación y valor económico por socio después de la nueva cesión para escalamiento.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig_cap_b, use_container_width=True, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
            st.markdown(
                f"""
                <div class="serieb-foot">
                  Nuevos inversionistas concentran {ronda_pct_input:.1%}, mientras Fluxial e IMELSA retienen {fluxial_post_b:.1%} y {imelsa_post_b:.1%} respectivamente.
                </div>
                """,
                unsafe_allow_html=True,
            )

    csv_valorizacion = df_valorizacion.to_csv(index=False).encode("utf-8-sig")
    if REPORTLAB_AVAILABLE:
        pdf_signature = (
            data_refresh_nonce,
            int(round(float(base_fx_input or 0))),
            str(base_investment_currency_input),
            int(round(float(base_inversion_clp_input or 0))),
            int(round(float(base_volume_input or 0))),
            int(round(float(base_ebitda_unit_input or 0))),
            round(float(base_multiple_input or 0), 4),
            round(float(post_ronda_pct_input or 0), 6),
            str(base_valuation_basis_input),
            bool(base_alloc_manual),
            round(float(base_fluxial_pct or 0), 6),
            round(float(base_imelsa_pct or 0), 6),
            round(float(total_base_knowhow_clp or 0), 2),
            round(float(base_base_en_usd or 0), 2),
            round(float(base_ebitda_potencial or 0), 2),
            round(float(base_valorizacion_fluxial_hoy or 0), 2),
            round(float(base_inversion_usd or 0), 2),
            round(float(base_post_money_serie_a or 0), 2),
            int(round(float(post_fx_input or 0))),
            str(post_investment_currency_input),
            int(round(float(post_volume_input or 0))),
            int(round(float(post_ebitda_unit_input or 0))),
            round(float(post_multiple_input or 0), 4),
            round(float(post_ebitda_total or 0), 2),
            round(float(post_valor_post_piloto or 0), 2),
            round(float(post_upside_pct or 0), 6),
            round(float(post_valor_imelsa_post or 0), 2),
            round(float(post_capital_raise or 0), 2),
            round(float(post_money_serie_b_pdf or 0), 2),
            round(float(post_pct_remanente or 0), 6),
            round(float(post_fluxial_post_b or 0), 6),
            round(float(post_imelsa_post_b or 0), 6),
            round(float(base_aporte_no_pecuniario_usd or 0), 2),
        )
        pdf_sig_key = widget_key("cached_supuestos_pdf_signature")
        pdf_data_key = widget_key("cached_supuestos_pdf_bytes")
        if st.session_state.get(pdf_sig_key) != pdf_signature:
            st.session_state[pdf_data_key] = build_valorizacion_supuestos_pdf()
            st.session_state[pdf_sig_key] = pdf_signature
    reset_requested = False
    render_supuestos_panel()
    st.download_button(label="📥 Descargar CSV de valorización", data=csv_valorizacion, file_name="valorizacion.csv", mime="text/csv", key=widget_key("download_csv"))

    if reset_requested:
        for group_name in ("base", "post"):
            for name, default_value in group_widget_defaults[group_name].items():
                st.session_state[shared_state_key(name, group_name)] = default_value
                st.session_state.pop(shared_widget_key(name, group_name), None)


def render_explorador_module_content(key_prefix: str = "explorer_"):
    st.subheader("Explorador interactivo de la tabla CAPEX")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        categoria_filter = st.selectbox(
            "Filtrar por categoría:",
            options=["(Todas)"] + sorted(df_capex["Categoria"].unique().tolist()),
            index=0,
            key=f"{key_prefix}categoria_filter",
        )

    with col_f2:
        item_filter = st.selectbox(
            "Filtrar por ítem:",
            options=["(Todos)"] + sorted(df_capex["Item"].unique().tolist()),
            index=0,
            key=f"{key_prefix}item_filter",
        )

    with col_f3:
        min_pct = st.slider(
            "Participación mínima del ítem (%)",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
            key=f"{key_prefix}min_pct",
        )

    with col_f4:
        ordenar_por = st.selectbox(
            "Ordenar por:",
            options=["Monto_CLP", "Monto_USD", "Participacion_pct"],
            index=0,
            key=f"{key_prefix}ordenar_por",
        )

    df_exp = df_capex.copy()
    if categoria_filter != "(Todas)":
        df_exp = df_exp[df_exp["Categoria"] == categoria_filter]
    if item_filter != "(Todos)":
        df_exp = df_exp[df_exp["Item"] == item_filter]
    df_exp = df_exp[df_exp["Participacion_pct"] * 100 >= min_pct]
    df_exp = df_exp.sort_values(ordenar_por, ascending=False)

    df_exp["Participación (%)"] = df_exp["Participacion_pct"] * 100
    df_exp["Monto_CLP_fmt"] = df_exp["Monto_CLP"].apply(format_clp)
    df_exp["Monto_USD_fmt"] = df_exp["Monto_USD"].apply(format_usd)

    st.markdown("#### Tabla filtrada")
    st.dataframe(
        df_exp[[
            "Item",
            "Categoria",
            "Participación (%)",
            "Monto_CLP_fmt",
            "Monto_USD_fmt",
            "Bullet",
        ]],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### Vista gráfica de los ítems filtrados")
    if not df_exp.empty:
        df_exp["Monto_CLP_MM"] = df_exp["Monto_CLP"] / 1e6
        df_plot = df_exp.sort_values("Monto_CLP", ascending=False).head(20)
        fig_exp = px.bar(
            df_plot,
            x="Monto_CLP_MM",
            y="Categoria",
            color="Item",
            color_discrete_map=item_color_map,
            orientation="h",
            labels={
                "Monto_CLP_MM": "Monto (MM CLP)",
                "Categoria": "Categoría (sub-ítem)",
                "Item": "Ítem",
            },
            title="Ítems filtrados (hasta 20 primeros)",
        )
        fig_exp.update_traces(
            text=df_plot["Monto_CLP_MM"].apply(lambda v: f"{v:.1f} MM"),
            textposition="outside",
        )
        fig_exp.update_layout(
            xaxis_title="Monto (millones de CLP)",
            yaxis_title="",
            margin=dict(l=10, r=10, t=60, b=10),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.16,
                xanchor="left",
                x=0,
                title=dict(text=""),
                font=dict(size=10),
                entrywidth=105,
                entrywidthmode="pixels",
            ),
        )
        st.plotly_chart(fig_exp, use_container_width=True)
    else:
        st.info("No hay ítems que cumplan con los filtros seleccionados.")

    csv_bytes = df_exp.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar CSV filtrado",
        data=csv_bytes,
        file_name="capex_filtrado.csv",
        mime="text/csv",
        key=f"{key_prefix}download_csv",
    )


def render_input_thousands_hint(value: float | int, prefix: str = ""):
    try:
        number = int(round(float(value)))
        formatted = f"{number:,}".replace(",", ".")
        label = f"{prefix}{formatted}" if prefix else formatted
        st.caption(f"Valor formateado: {label}")
    except Exception:
        pass


# =========================
# NAVEGACIÓN PRINCIPAL
# =========================
input_cards = [
    ("estado_actual", "1- Activo Tecnológico y Validación"),
    ("escalamiento", "2- Capital Requerido y Ejecución CAPEX"),
    ("valorizacion", "3-Análisis Financiero Basado en EBITDA"),
]

if "inputs_bloque_sel" not in st.session_state:
    st.session_state["inputs_bloque_sel"] = None

def selector_button_label(label: str, is_active: bool, action_label: str = "Abrir bloque") -> str:
    return f"{label} · Seleccionado" if is_active else action_label

def _set_inputs_bloque(value: str):
    st.session_state["inputs_bloque_sel"] = value
    if value == "estado_actual":
        st.session_state["inputs_estado_actual_subbloque_sel"] = None
    elif value == "escalamiento":
        st.session_state["inputs_escalamiento_capex_sel"] = None
    elif value == "valorizacion":
        st.session_state["inputs_val_bloque_sel"] = None

st.markdown(
        """
        <style>
        .inputs-nav-shell{
            border-radius:24px;
            padding:16px 18px 12px 18px;
            border:1px solid rgba(148,163,184,.18);
            background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
            box-shadow:0 12px 28px rgba(15,23,42,.05);
            margin-bottom:18px;
        }
        .inputs-nav-head-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:6px;
        }
        .inputs-nav-head-t{
            font-size:18px;
            font-weight:900;
            line-height:1.15;
            color:#0f172a;
            margin-bottom:6px;
        }
        .inputs-nav-head-s{
            font-size:13px;
            line-height:1.5;
            color:#475569;
            max-width:760px;
        }
        .inputs-nav-card{
            min-height:132px;
            height:132px;
            display:flex;
            flex-direction:column;
            justify-content:flex-start;
            position:relative;
            overflow:hidden;
            border-radius:20px;
            padding:16px 18px 14px 18px;
            border:1px solid rgba(203,213,225,.75);
            background:
                radial-gradient(circle at top right, rgba(191,219,254,.28), transparent 28%),
                linear-gradient(180deg,#f8fafc 0%,#ffffff 74%);
            box-shadow:0 10px 22px rgba(15,23,42,.04);
            margin-bottom:10px;
        }
        .inputs-nav-card:before{
            content:"";
            position:absolute;
            left:0;
            top:0;
            bottom:0;
            width:5px;
            background:linear-gradient(180deg,#cbd5e1 0%,#e2e8f0 100%);
        }
        .inputs-nav-card.active{
            border:1px solid rgba(239,68,68,.30);
            box-shadow:0 16px 34px rgba(239,68,68,.12);
            background:
                radial-gradient(circle at top right, rgba(254,202,202,.24), transparent 26%),
                linear-gradient(90deg,#fff5f5 0%,#ffe4e6 48%,#ffe8e8 100%);
        }
        .inputs-nav-card.active:before{
            background:linear-gradient(180deg,#ef4444 0%,#f87171 100%);
        }
        .inputs-nav-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.10em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:10px;
        }
        .inputs-nav-t{
            font-size:17px;
            font-weight:900;
            line-height:1.2;
            color:#0f172a;
            margin-bottom:8px;
            max-width:28ch;
        }
        .inputs-nav-title-row{
            display:flex;
            align-items:flex-start;
            gap:10px;
            margin-bottom:8px;
        }
        .inputs-nav-ico{
            font-size:22px;
            line-height:1;
            flex:0 0 auto;
            margin-top:1px;
        }
        .inputs-nav-title-wrap{
            min-width:0;
        }
        .inputs-nav-s{
            font-size:12px;
            line-height:1.45;
            color:#475569;
        }
        .inputs-nav-card.active .inputs-nav-k{color:#b91c1c;}
        .inputs-nav-card.active .inputs-nav-t{color:#b91c1c;}
        .inputs-nav-card.active .inputs-nav-s{color:#991b1b;}
        button[kind="primary"]{
            background:#fff5f5 !important;
            color:#ef4444 !important;
            border:1px solid rgba(239,68,68,.52) !important;
            box-shadow:0 8px 18px rgba(239,68,68,.10) !important;
        }
        button[kind="primary"] p{
            color:#ef4444 !important;
            font-weight:800 !important;
        }
        button[kind="primary"]:hover{
            background:#ffe9e9 !important;
            border-color:#ef4444 !important;
        }
        .inputs-active-banner{
            border-radius:18px;
            padding:12px 14px;
            border:1px solid rgba(59,130,246,.16);
            background:linear-gradient(90deg,#eff6ff 0%,#eefbf5 100%);
            margin:8px 0 4px 0;
        }
        .inputs-active-banner-k{
            font-size:10px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748b;
            margin-bottom:4px;
        }
        .inputs-active-banner-t{
            font-size:14px;
            font-weight:800;
            color:#0f172a;
        }
        .inputs-info-box{
            border-radius:20px;
            padding:22px 24px;
            border:1px solid rgba(148,163,184,.24);
            background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
            box-shadow:0 10px 24px rgba(15,23,42,.05);
        }
        .inputs-info-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748B;
            margin-bottom:8px;
        }
        .inputs-info-t{
            font-size:28px;
            font-weight:800;
            line-height:1.1;
            color:#0f172a;
            margin-bottom:10px;
        }
        .inputs-info-p{
            font-size:15px;
            line-height:1.6;
            color:#475569;
            margin:0;
        }
        </style>
        """,
        unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="inputs-nav-shell">
      <div class="inputs-nav-head-k">Mapa de lectura</div>
      <div class="inputs-nav-head-t">Selecciona el bloque estratégico que quieres revisar</div>
      <div class="inputs-nav-head-s">La pantalla está organizada en tres vistas: activo tecnológico, capital requerido y estructura de valorización.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav_cols = st.columns(3)
for idx, (block_value, block_title) in enumerate(input_cards):
    is_active = st.session_state.get("inputs_bloque_sel") == block_value
    with nav_cols[idx]:
        st.markdown(
            f"""
            <div class="inputs-nav-card {'active' if is_active else ''}">
                <div class="inputs-nav-k">BLOQUE {idx + 1}</div>
                <div class="inputs-nav-t">{block_title}</div>
                <div class="inputs-nav-s">{'Vista activa para análisis' if is_active else 'Abrir vista estratégica'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            selector_button_label(block_title, is_active),
            key=f"inputs_nav_{idx}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            on_click=_set_inputs_bloque,
            args=(block_value,),
        )
selected_input_block = st.session_state.get("inputs_bloque_sel")

if selected_input_block:
    st.markdown(
        """
        <div id="inputs-subblocks-anchor"></div>
        <script>
        const subblockAnchor = window.parent.document.getElementById("inputs-subblocks-anchor");
        if (subblockAnchor) {
          subblockAnchor.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        </script>
        """,
        unsafe_allow_html=True,
    )

input_block_copy = {
    "estado_actual": (
        "1- Activo Tecnológico y Validación",
        "Aquí consolidaremos el diagnóstico base del proyecto: situación actual, hitos alcanzados, brechas técnicas y supuestos iniciales del modelo.",
    ),
    "escalamiento": (
        "2- Capital Requerido y Ejecución CAPEX",
        "Este bloque quedará preparado para mostrar la ruta de escalamiento industrial, prioridades de inversión y asignación de fondos por etapa.",
    ),
    "valorizacion": (
        "3-Análisis Financiero Basado en EBITDA",
        "En esta sección se presenta el análisis financiero del proyecto a partir del EBITDA y su impacto en la valorización del negocio.",
    ),
}
if selected_input_block == "estado_actual":
    render_inputs_estado_actual_dashboard()
elif selected_input_block == "escalamiento":
    capex_selector_state_key = "inputs_escalamiento_capex_sel"

    def _set_capex_focus(value: str):
        st.session_state[capex_selector_state_key] = value

    capex_80kw_view_state_key = "inputs_capex_80kw_view_sel"

    def _set_capex_80kw_view(value: str):
        st.session_state[capex_80kw_view_state_key] = value

    if capex_selector_state_key not in st.session_state:
        st.session_state[capex_selector_state_key] = None

    capex_10kw_val = 0.0
    try:
        df_restante_10kw = build_restante_piloto_10kw_view(RESTANTE_PILOTO_10KW_CSV_URL_DEFAULT, refresh_nonce=data_refresh_nonce)
        if not df_restante_10kw.empty:
            capex_10kw_val = float(df_restante_10kw["Valor C"].sum() or 0.0)
    except Exception:
        capex_10kw_val = 0.0

    capex_80kw_usd_total = float(df_capex_base["Monto_USD"].sum() or 0.0) if "Monto_USD" in df_capex_base.columns else 0.0
    capex_80kw_val = (capex_80kw_usd_total * fx_used) + float(direccion_total_clp or 0.0)
    capital_recaudar_val = capex_10kw_val + capex_80kw_val
    capex_10kw_pct = (capex_10kw_val / capital_recaudar_val * 100.0) if capital_recaudar_val > 0 else 0.0
    capex_80kw_pct = (capex_80kw_val / capital_recaudar_val * 100.0) if capital_recaudar_val > 0 else 0.0

    capex_10kw_active = st.session_state.get(capex_selector_state_key) == "10kw"
    capex_80kw_active = st.session_state.get(capex_selector_state_key) == "80kw"
    st.markdown(
        """
        <style>
        .capex-summary-hero{
            border-radius:24px;
            padding:22px 24px;
            background:
                radial-gradient(circle at top right, rgba(14,165,164,.16), transparent 24%),
                linear-gradient(90deg,#f8fbff 0%,#e7f5ff 48%,#d4efff 100%);
            border:1px solid rgba(125,211,252,.42);
            box-shadow:0 16px 36px rgba(15,23,42,.08);
            margin-bottom:18px;
        }
        .capex-summary-grid{
            display:grid;
            grid-template-columns:1.25fr .95fr;
            gap:18px;
            align-items:stretch;
        }
        @media (max-width:1100px){.capex-summary-grid{grid-template-columns:1fr;}}
        .capex-summary-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.14em;
            text-transform:uppercase;
            color:#0f766e;
            margin-bottom:8px;
        }
        .capex-summary-t{
            font-size:18px;
            font-weight:800;
            line-height:1.2;
            color:#0f172a;
            margin-bottom:10px;
        }
        .capex-summary-v{
            font-size:52px;
            font-weight:900;
            line-height:1;
            color:#0f172a;
            margin-bottom:12px;
            letter-spacing:-.03em;
        }
        .capex-summary-p{
            font-size:15px;
            line-height:1.6;
            color:#475569;
            max-width:720px;
        }
        .capex-summary-panel{
            border-radius:18px;
            padding:16px 18px;
            background:rgba(255,255,255,.76);
            border:1px solid rgba(148,163,184,.24);
            backdrop-filter:blur(6px);
        }
        .capex-summary-panel-h{
            font-size:12px;
            font-weight:800;
            letter-spacing:.10em;
            text-transform:uppercase;
            color:#64748b;
            margin-bottom:10px;
        }
        .capex-summary-row{
            display:flex;
            justify-content:space-between;
            gap:12px;
            align-items:flex-start;
            padding:10px 0;
            border-bottom:1px solid rgba(226,232,240,.9);
        }
        .capex-summary-row:last-child{border-bottom:none;padding-bottom:0}
        .capex-summary-row.total .capex-summary-label{color:#0f766e;}
        .capex-summary-row.total .capex-summary-value{color:#0f766e;}
        .capex-summary-label{
            font-size:14px;
            font-weight:700;
            color:#0f172a;
            line-height:1.35;
        }
        .capex-summary-value{
            font-size:16px;
            font-weight:800;
            color:#0f172a;
            white-space:nowrap;
        }
        .capex-detail-grid{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:16px;
            margin-bottom:10px;
        }
        @media (max-width:900px){.capex-detail-grid{grid-template-columns:1fr;}}
        .capex-detail-card{
            border-radius:20px;
            padding:18px 18px 16px 18px;
            background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
            border:1px solid rgba(148,163,184,.26);
            box-shadow:0 10px 24px rgba(15,23,42,.05);
        }
        .capex-detail-card.active{
            background:linear-gradient(90deg,#fff5f5 0%,#ffe4e6 42%,#ffe8e8 100%);
            border:1px solid rgba(239,68,68,.30);
            box-shadow:0 14px 28px rgba(239,68,68,.10);
        }
        .capex-detail-k{
            font-size:11px;
            font-weight:800;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#64748b;
            margin-bottom:8px;
        }
        .capex-detail-card.active .capex-detail-k{color:#b91c1c;}
        .capex-detail-t{
            font-size:26px;
            font-weight:900;
            line-height:1;
            color:#0f172a;
            margin-bottom:8px;
        }
        .capex-detail-pct{
            font-size:13px;
            font-weight:800;
            color:#0f766e;
            margin-bottom:10px;
        }
        .capex-detail-card.active .capex-detail-pct{color:#b91c1c;}
        .capex-detail-s{
            font-size:14px;
            line-height:1.5;
            color:#475569;
        }
        .capex-detail-card.active .capex-detail-s{color:#991b1b;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="capex-summary-hero">
          <div class="capex-summary-grid">
            <div>
              <div class="capex-summary-k">Resumen de capital</div>
              <div class="capex-summary-t">Capex de escalamiento</div>
              <div class="capex-summary-v">{format_clp(capital_recaudar_val)}</div>
              <div class="capex-summary-p">
                Monto consolidado requerido para cubrir la referencia de CAPEX 10kW y el CAPEX integrado del piloto 80kW.
              </div>
            </div>
            <div class="capex-summary-panel">
              <div class="capex-summary-panel-h">Composición del capital</div>
              <div class="capex-summary-row">
                <div class="capex-summary-label">Brecha piloto 10 kW</div>
                <div class="capex-summary-value">{format_clp(capex_10kw_val)}</div>
              </div>
              <div class="capex-summary-row">
                <div class="capex-summary-label">Escalamiento 80 kW</div>
                <div class="capex-summary-value">{format_clp(capex_80kw_val)}</div>
              </div>
              <div class="capex-summary-row total">
                <div class="capex-summary-label">Capital consolidado</div>
                <div class="capex-summary-value">{format_clp(capital_recaudar_val)}</div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="capex-detail-grid">
          <div class="capex-detail-card {'active' if capex_10kw_active else ''}">
            <div class="capex-detail-k">Brecha piloto 10 kW</div>
            <div class="capex-detail-t">{format_clp(capex_10kw_val)}</div>
            <div class="capex-detail-pct">{capex_10kw_pct:.1f}% del Capital a Recaudar</div>
            <div class="capex-detail-s">CAPEX 10kW asociado al piloto de validación tecnológica inicial.</div>
          </div>
          <div class="capex-detail-card {'active' if capex_80kw_active else ''}">
            <div class="capex-detail-k">Escalamiento 80 kW</div>
            <div class="capex-detail-t">{format_clp(capex_80kw_val)}</div>
            <div class="capex-detail-pct">{capex_80kw_pct:.1f}% del Capital a Recaudar</div>
            <div class="capex-detail-s">CAPEX 80kW total, incorporando estructura técnica y capital humano asociado.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    capex10_col, capex80_col = st.columns(2)
    with capex10_col:
        st.button(
            selector_button_label("CAPEX 10kW", capex_10kw_active, action_label="Seleccionar CAPEX 10kW"),
            key="inputs_capex_focus_kpi_10kw",
            use_container_width=True,
            type="primary" if capex_10kw_active else "secondary",
            on_click=_set_capex_focus,
            args=("10kw",),
        )
    with capex80_col:
        st.button(
            selector_button_label("CAPEX 80kW", capex_80kw_active, action_label="Seleccionar CAPEX 80kW"),
            key="inputs_capex_focus_kpi_80kw",
            use_container_width=True,
            type="primary" if capex_80kw_active else "secondary",
            on_click=_set_capex_focus,
            args=("80kw",),
        )

    st.markdown("---")

    if capex_10kw_active:
        render_inputs_capex_10kw_detail()
    elif capex_80kw_active:
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            button[kind="primary"][data-testid="stBaseButton-secondaryFormSubmit"],
            button[kind="primary"]{
                background:#fff5f5 !important;
                color:#ef4444 !important;
                border:1px solid rgba(239,68,68,.52) !important;
                box-shadow:0 8px 18px rgba(239,68,68,.10) !important;
            }
            button[kind="primary"][data-testid="stBaseButton-secondaryFormSubmit"] p,
            button[kind="primary"] p{
                color:#ef4444 !important;
                font-weight:800 !important;
            }
            button[kind="primary"]:hover{
                background:#ffe9e9 !important;
                border-color:#ef4444 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        capex_80kw_views = [
            ("dashboard", "📊 Modelo Consolidado de Inversión"),
            ("capex", "🏗️ CAPEX Ingeniería, Suministro y Montaje"),
            ("direccion", "🧑‍💼 Inversión en Capital Humano"),
        ]
        if capex_80kw_view_state_key not in st.session_state:
            st.session_state[capex_80kw_view_state_key] = "dashboard"
        if st.session_state[capex_80kw_view_state_key] not in {value for value, _ in capex_80kw_views}:
            st.session_state[capex_80kw_view_state_key] = "dashboard"

        st.markdown(
            """
            <div style="margin:4px 0 14px 0;padding:14px 16px;border-radius:18px;background:linear-gradient(90deg,#eff8ff 0%,#f8fcff 54%,#ffffff 100%);border:1px solid rgba(14,165,233,.22);">
                <div style="font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#0369a1;margin-bottom:6px;">Mapa de lectura</div>
                <div style="font-size:15px;line-height:1.55;color:#475569;">
                    El <strong>Modelo Consolidado de Inversión</strong> integra el <strong>CAPEX de ingeniería, suministro y montaje</strong> con la <strong>inversión en capital humano</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        consolidated_active = st.session_state.get(capex_80kw_view_state_key) == "dashboard"
        st.markdown(
            """
            <style>
            .capex-nav-equals-shell{
                min-height:196px;
                display:flex;
                align-items:center;
                justify-content:center;
            }
            .capex-nav-equals{
                width:64px;
                height:64px;
                border-radius:999px;
                display:flex;
                align-items:center;
                justify-content:center;
                background:linear-gradient(180deg,#fff5f5 0%,#ffe7ea 100%);
                border:1px solid rgba(239,68,68,.18);
                box-shadow:0 10px 22px rgba(239,68,68,.08);
                font-size:34px;
                font-weight:900;
                color:#b91c1c;
                line-height:1;
            }
            .capex-nav-plus-shell{
                display:flex;
                align-items:center;
                justify-content:center;
                margin:8px 0;
            }
            .capex-nav-plus{
                width:42px;
                height:42px;
                border-radius:999px;
                display:flex;
                align-items:center;
                justify-content:center;
                background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
                border:1px solid rgba(148,163,184,.24);
                box-shadow:0 6px 14px rgba(15,23,42,.05);
                font-size:26px;
                font-weight:900;
                color:#475569;
                line-height:1;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        nav_left, nav_mid, nav_right = st.columns([1.0, 0.14, 0.86], gap="medium")
        with nav_left:
            st.markdown("<div style='height:72px;'></div>", unsafe_allow_html=True)
            st.button(
                selector_button_label(
                    "📊 Modelo Consolidado de Inversión · Total integrado CAPEX + Capital Humano",
                    consolidated_active,
                    action_label="📊 Modelo Consolidado de Inversión · Total integrado CAPEX + Capital Humano",
                ),
                key="inputs_capex_80kw_view_dashboard",
                use_container_width=True,
                type="primary" if consolidated_active else "secondary",
                on_click=_set_capex_80kw_view,
                args=("dashboard",),
            )
        with nav_mid:
            st.markdown(
                """
                <div class="capex-nav-equals-shell">
                    <div class="capex-nav-equals">=</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with nav_right:
            is_capex_active = st.session_state.get(capex_80kw_view_state_key) == "capex"
            st.button(
                selector_button_label(
                    "🏗️ Componente 1 · CAPEX Ingeniería, Suministro y Montaje",
                    is_capex_active,
                    action_label="🏗️ Componente 1 · CAPEX Ingeniería, Suministro y Montaje",
                ),
                key="inputs_capex_80kw_view_capex",
                use_container_width=True,
                type="primary" if is_capex_active else "secondary",
                on_click=_set_capex_80kw_view,
                args=("capex",),
            )
            st.markdown(
                """
                <div class="capex-nav-plus-shell">
                    <div class="capex-nav-plus">+</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            is_direccion_active = st.session_state.get(capex_80kw_view_state_key) == "direccion"
            st.button(
                selector_button_label(
                    "🧑‍💼 Componente 2 · Inversión en Capital Humano",
                    is_direccion_active,
                    action_label="🧑‍💼 Componente 2 · Inversión en Capital Humano",
                ),
                key="inputs_capex_80kw_view_direccion",
                use_container_width=True,
                type="primary" if is_direccion_active else "secondary",
                on_click=_set_capex_80kw_view,
                args=("direccion",),
            )

        st.markdown("---")

        selected_capex_80kw_view = st.session_state.get(capex_80kw_view_state_key)
        if selected_capex_80kw_view == "dashboard":
            render_resumen_content(
                key_prefix="inputs_dashboard_general_",
                include_export=False,
                include_direction_item=True,
            )
        elif selected_capex_80kw_view == "capex":
            render_resumen_content(
                key_prefix="inputs_capex_overview_",
                include_export=False,
                include_direction_item=False,
            )
            render_capex_module_content(selector_key="inputs_capex_internal_selector")
        elif selected_capex_80kw_view == "direccion":
            render_direccion_module_content()
    else:
        pass
elif selected_input_block == "valorizacion":
    render_valorizacion_module_content(key_prefix="inputs_val_")
else:
    st.info("Selecciona uno de los KPIs principales para abrir sus sub-bloques y contenido.")

# -------------------------
# TAB RESUMEN
# -------------------------
if False:
    st.subheader("Vista general del CAPEX")

    # ========================
    # 1) CAPEX por Ítem — barra única + monto total + %
    # ========================

    df_items_tot = (
        df_capex
        .groupby("Item", as_index=False)
        .agg(Total_CLP=("Monto_CLP", "sum"))
    )

    df_items_tot = df_items_tot.merge(
        pd.DataFrame(
            list(item_category_lookup.items()),
            columns=["Item", "Categoria"]
        ),
        on="Item",
        how="left",
    )
    # Total proyecto (por seguridad se calcula desde la tabla)
    capex_total_clp_calc = df_items_tot["Total_CLP"].sum()

    # Porcentaje de cada ítem sobre el total
    df_items_tot["Pct_total"] = df_items_tot["Total_CLP"] / capex_total_clp_calc

    # Monto en millones de CLP
    df_items_tot["Total_MM"] = df_items_tot["Total_CLP"] / 1e6

    # Texto dentro de la barra: "XX.X MM / YY.Y%"
    df_items_tot["Texto"] = df_items_tot.apply(
        lambda r: f"{r['Total_MM']:.1f} MM / {r['Pct_total']*100:.1f}%",
        axis=1
    )

    # Orden descendente por monto
    df_items_tot = df_items_tot.sort_values("Total_CLP", ascending=False)

    fig_item_total = px.bar(
        df_items_tot,
        x="Total_MM",
        y="Item",
        orientation="h",
        text="Texto",
        color="Item",
        color_discrete_map=item_color_map,
        labels={
            "Total_MM": "Monto (millones de CLP)",
            "Item": "Ítem",
            "Item": "Ítem",
        },
        title="CAPEX por ítem (monto total y % del CAPEX)",
    )

    fig_item_total.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont_size=11,
    )

    fig_item_total.update_layout(
        xaxis_title="Monto total (millones de CLP)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        height=420,
        bargap=0.25,
    )
    st.plotly_chart(fig_item_total, use_container_width=True)

    st.session_state["fig_item_total"] = fig_item_total

 # ========================
if False:
    render_pagos_hitos(capex_url, fx_used, pagos_scale, include_direction_salaries=False)
    
    # 1.bis) LÍNEA DE TIEMPO TÉCNICA POR CATEGORÍA
    # ========================
    st.markdown("### Línea de tiempo del proyecto por categoría")
    
    if "Mes_inicio" in df_capex.columns and "Mes_termino" in df_capex.columns:
    
        # Filtrar filas válidas
        df_timeline = df_capex.dropna(subset=["Mes_inicio", "Mes_termino"]).copy()
    
        if not df_timeline.empty:
            # Convertir a numérico
            df_timeline["Mes_inicio"] = pd.to_numeric(df_timeline["Mes_inicio"], errors="coerce")
            df_timeline["Mes_termino"] = pd.to_numeric(df_timeline["Mes_termino"], errors="coerce")
            df_timeline = df_timeline.dropna(subset=["Mes_inicio", "Mes_termino"])
    
            if not df_timeline.empty:
                # Agregar a nivel técnico por categoría + ítem
                df_timeline_cat = (
                    df_timeline
                    .groupby(["Categoria", "Item"], as_index=False)
                    .agg(
                        Mes_inicio=("Mes_inicio", "min"),
                        Mes_termino=("Mes_termino", "max"),
                        Monto_CLP=("Monto_CLP", "sum"),
                        Monto_USD=("Monto_USD", "sum"),
                    )
                )
    
                # =============================================
                # Filtro estilo "píldoras" con emojis (radio button)
                # =============================================
                items_todos = sorted(df_timeline_cat["Item"].unique().tolist())
                opciones = ["Todas"] + items_todos
    
                def _fmt_item(opt: str) -> str:
                    if opt == "Todas":
                        return "🔴 Todas"
                    mapa = {
                        "Desarrollo Tecnológico": "🧪 Desarrollo Tecnológico",
                        "Componentes Mecánicos": "⚙️ Componentes Mecánicos",
                        "Sistema Eléctrico y Control": "🔌 Sistema Eléctrico y Control",
                        "Obras Civiles": "🏗️ Obras Civiles",
                        "Montaje y Logística": "📦 Montaje y Logística",
                        "Ensayos y Certificación": "📏 Ensayos y Certificación",
                        "Contingencias y Administración": "🧾 Contingencias y Administración",
                    }
                    return mapa.get(opt, opt)
    
                item_sel = render_single_select_pills_compat(
                    "Filtrar por ítem:",
                    options=opciones,
                    default="Todas",
                    key="timeline_radio_item_cat",
                    format_func=_fmt_item,
                )
    
                # Filtrar ítems
                df_tl_plot = (
                    df_timeline_cat.copy()
                    if item_sel == "Todas"
                    else df_timeline_cat[df_timeline_cat["Item"] == item_sel].copy()
                )
    
                if not df_tl_plot.empty:
                    # =============================================
                    # Mapear Mes 1–15 a fechas reales ficticias
                    # =============================================
                    base_date = pd.to_datetime("2025-01-01")
    
                    df_tl_plot["Fecha_inicio"] = base_date + pd.to_timedelta(
                        (df_tl_plot["Mes_inicio"] - 1) * 30, unit="D"
                    )
                    df_tl_plot["Fecha_termino"] = base_date + pd.to_timedelta(
                        (df_tl_plot["Mes_termino"] - 1) * 30, unit="D"
                    )
    
                    # =============================================
                    # ORDEN TÉCNICO: tareas de la más lejana a la más cercana
                    # =============================================
                    df_tl_plot = df_tl_plot.sort_values(
                        by=["Fecha_inicio", "Fecha_termino"],
                        ascending=[False, False],  # descendente
                    )
    
                    # Mantener este orden en el eje Y
                    df_tl_plot["Categoria"] = pd.Categorical(
                        df_tl_plot["Categoria"],
                        categories=df_tl_plot["Categoria"].tolist(),
                        ordered=True,
                    )
    
                    # =============================================
                    # Construcción de la Gantt técnica
                    # =============================================
                    fig_timeline_cat = px.timeline(
                        df_tl_plot,
                        x_start="Fecha_inicio",
                        x_end="Fecha_termino",
                        y="Categoria",
                       color="Item",
                       color_discrete_map=item_color_map,   # <--- CLAVE
                       hover_data={
                           "Categoria": True,
                           "Item": True,
                           "Mes_inicio": True,
                           "Mes_termino": True,
                           "Monto_CLP": ":,.0f",
                           "Monto_USD": ":,.0f",
                     },
        
                    )
    
    
                    fig_timeline_cat.update_yaxes(
                        categoryorder="array",
                        title="Categoría / Tarea",
                    )
    
                    # ==========================
                    # Eje X formateado como meses 1–15
                    # ==========================
                    fig_timeline_cat.update_xaxes(
                        title="Mes del proyecto",
                        tickmode="array",
                        tickvals=df_tl_plot["Fecha_inicio"].sort_values().unique(),
                        ticktext=df_tl_plot["Mes_inicio"].sort_values().unique(),
                        showgrid=True,
                    )
    
                    fig_timeline_cat.update_layout(
                        margin=dict(l=10, r=10, t=60, b=10),
                        height=520,
                        legend_title_text="Ítem",
                    )
    
                    st.plotly_chart(fig_timeline_cat, use_container_width=True)
    
                    st.markdown("---")
                    st.subheader("Línea de tiempo de hitos por profesional")
    
                    try:
                        hitos_url = (
                            "https://docs.google.com/spreadsheets/d/e/"
                            "2PACX-1vSlNd3zXc1zV6TUQHnhXlfZtv7QVOv0mBfR_HH69Ht-0qi2aDtCfw5ouLDGIoPH_knhSAtyT2DYE-Qo/"
                            "pub?gid=1007478838&single=true&output=csv"
                        )
                        df_hitos = read_remote_csv(
                            hitos_url,
                            refresh_nonce=data_refresh_nonce,
                            dtype=str,
                        )
                        df_hitos.columns = [str(c).strip() for c in df_hitos.columns]
    
                        required_cols = [
                            "Hito_ID",
                            "Hito",
                            "Descripción",
                            "Entregables",
                            "Criterio de salida",
                            "Owner",
                            "Mes objetivo",
                            "Depende de",
                        ]
                        missing_cols = [c for c in required_cols if c not in df_hitos.columns]
                        if missing_cols:
                            st.error(f"Faltan columnas en la hoja de hitos: {missing_cols}")
                        else:
                            df_hitos["Mes_objetivo_i"] = pd.to_numeric(
                                df_hitos["Mes objetivo"], errors="coerce"
                            )
                            df_hitos = df_hitos.dropna(subset=["Mes_objetivo_i"]).copy()
    
                            if df_hitos.empty:
                                st.info("No hay hitos con Mes objetivo válido.")
                            else:
                                df_hitos["Hito_label"] = (
                                    df_hitos["Hito_ID"].astype(str).str.strip()
                                    + " — "
                                    + df_hitos["Hito"].astype(str).str.strip()
                                )
                                df_hitos = df_hitos.sort_values("Mes_objetivo_i")
                                y_order = df_hitos["Hito_label"].tolist()
    
                                fig_hitos = px.scatter(
                                    df_hitos,
                                    x="Mes_objetivo_i",
                                    y="Hito_label",
                                    color="Owner",
                                    labels={
                                        "Mes_objetivo_i": "Mes objetivo",
                                        "Hito_label": "Hito",
                                        "Owner": "Owner",
                                    },
                                    hover_data={
                                        "Hito_ID": True,
                                        "Hito": True,
                                        "Descripción": True,
                                        "Entregables": True,
                                        "Criterio de salida": True,
                                        "Owner": True,
                                        "Mes objetivo": True,
                                        "Depende de": True,
                                    },
                                    title="Ruta crítica de hitos del proyecto",
                                )
    
                                fig_hitos.update_traces(
                                    marker=dict(size=14, line=dict(width=1, color="#111827"))
                                )
    
                                hito_pos = {
                                    row["Hito_ID"]: (row["Mes_objetivo_i"], row["Hito_label"])
                                    for _, row in df_hitos.iterrows()
                                }
                                for _, row in df_hitos.iterrows():
                                    dep = str(row.get("Depende de", "")).strip()
                                    if not dep or dep == "-":
                                        continue
                                    if dep in hito_pos:
                                        x0, y0 = hito_pos[dep]
                                        x1, y1 = row["Mes_objetivo_i"], row["Hito_label"]
                                        fig_hitos.add_trace(
                                            go.Scatter(
                                                x=[x0, x1],
                                                y=[y0, y1],
                                                mode="lines",
                                                line=dict(color="#9CA3AF", width=2, dash="dot"),
                                                hoverinfo="skip",
                                                showlegend=False,
                                            )
                                        )
    
                                fig_hitos.update_layout(
                                    height=520,
                                    margin=dict(l=10, r=10, t=60, b=20),
                                    yaxis=dict(categoryorder="array", categoryarray=y_order),
                                    xaxis=dict(
                                        dtick=1,
                                        showgrid=True,
                                        title="Mes objetivo",
                                    ),
                                    legend=dict(
                                        orientation="h",
                                        yanchor="top",
                                        y=-0.2,
                                        xanchor="center",
                                        x=0.5,
                                    ),
                                )
                                st.plotly_chart(fig_hitos, use_container_width=True)
    
                    except Exception as e:
                        st.error(f"No se pudo construir la línea de tiempo de hitos: {e}")
    
                    st.markdown("---")
                    st.subheader("Mapa de zonas críticas de riesgos")
    
                    try:
                        riesgos_url = (
                            "https://docs.google.com/spreadsheets/d/e/"
                            "2PACX-1vSlNd3zXc1zV6TUQHnhXlfZtv7QVOv0mBfR_HH69Ht-0qi2aDtCfw5ouLDGIoPH_knhSAtyT2DYE-Qo/"
                            "pub?gid=1912427793&single=true&output=csv"
                        )
                        df_riesgos = read_remote_csv(
                            riesgos_url,
                            refresh_nonce=data_refresh_nonce,
                            dtype=str,
                        )
                        df_riesgos.columns = [str(c).strip() for c in df_riesgos.columns]
    
                        def _norm_col(s: str) -> str:
                            s = str(s)
                            s = unicodedata.normalize("NFKD", s)
                            s = "".join(c for c in s if not unicodedata.combining(c))
                            return re.sub(r"[^a-z0-9]", "", s.lower())
    
                        col_lookup = {_norm_col(c): c for c in df_riesgos.columns}
                        required_norm = {
                            "riesgoid": "Riesgo_ID",
                            "categoria": "Categoria",
                            "riesgo": "Riesgo",
                            "probabilidad15": "Probabilidad (1-5)",
                            "impacto15": "Impacto (1-5)",
                            "severidadpxi": "Severidad (PxI)",
                            "owner": "Owner",
                            "relacionadohito": "Relacionado Hito",
                            "estado": "Estado",
                        }
                        missing_cols = [
                            display
                            for key, display in required_norm.items()
                            if key not in col_lookup
                        ]
                        if missing_cols:
                            st.error(f"Faltan columnas en la hoja de riesgos: {missing_cols}")
                        else:
                            rename_map = {
                                col_lookup[key]: display
                                for key, display in required_norm.items()
                            }
                            df_riesgos = df_riesgos.rename(columns=rename_map)
    
                            df_riesgos["Severidad_i"] = pd.to_numeric(
                                df_riesgos["Severidad (PxI)"], errors="coerce"
                            )
                            df_riesgos["Probabilidad_i"] = pd.to_numeric(
                                df_riesgos["Probabilidad (1-5)"], errors="coerce"
                            )
                            df_riesgos["Impacto_i"] = pd.to_numeric(
                                df_riesgos["Impacto (1-5)"], errors="coerce"
                            )
                            df_riesgos = df_riesgos.dropna(
                                subset=["Probabilidad_i", "Impacto_i", "Severidad_i"]
                            ).copy()
    
                            if df_riesgos.empty:
                                st.info("No hay riesgos con Probabilidad/Impacto válidos.")
                            else:
                                categorias = sorted(df_riesgos["Categoria"].astype(str).unique().tolist())
                                offset_map = {}
                                n_cats = len(categorias)
                                for idx, cat in enumerate(categorias):
                                    offset = (idx - (n_cats - 1) / 2) * 0.08
                                    offset_map[cat] = offset
    
                                df_riesgos["Prob_plot"] = df_riesgos["Probabilidad_i"] + df_riesgos[
                                    "Categoria"
                                ].map(offset_map).fillna(0.0)
                                df_riesgos["Imp_plot"] = df_riesgos["Impacto_i"] - df_riesgos[
                                    "Categoria"
                                ].map(offset_map).fillna(0.0)
    
                                df_riesgos["Prob_plot"] = df_riesgos["Prob_plot"].clip(0.6, 5.4)
                                df_riesgos["Imp_plot"] = df_riesgos["Imp_plot"].clip(0.6, 5.4)
    
                                fig_riesgos = px.scatter(
                                    df_riesgos,
                                    x="Prob_plot",
                                    y="Imp_plot",
                                    color="Categoria",
                                    symbol="Categoria",
                                    size="Severidad_i",
                                    size_max=28,
                                    labels={
                                        "Prob_plot": "Probabilidad (1–5)",
                                        "Imp_plot": "Impacto (1–5)",
                                        "Categoria": "Categoría",
                                    },
                                    hover_data={
                                        "Riesgo_ID": True,
                                        "Riesgo": True,
                                        "Probabilidad (1-5)": True,
                                        "Impacto (1-5)": True,
                                        "Severidad (PxI)": True,
                                        "Owner": True,
                                        "Estado": True,
                                    },
                                    title="Mapa de riesgos (Probabilidad × Impacto)",
                                )
                                fig_riesgos.update_traces(
                                    marker=dict(line=dict(width=1, color="#111827"))
                                )
                                shapes = []
                                for p in range(1, 6):
                                    for i in range(1, 6):
                                        sev = p * i
                                        if sev <= 6:
                                            fill = "#D1FAE5"
                                        elif sev <= 12:
                                            fill = "#FEF3C7"
                                        else:
                                            fill = "#FEE2E2"
                                        shapes.append(
                                            dict(
                                                type="rect",
                                                xref="x",
                                                yref="y",
                                                x0=p - 0.5,
                                                y0=i - 0.5,
                                                x1=p + 0.5,
                                                y1=i + 0.5,
                                                fillcolor=fill,
                                                opacity=0.35,
                                                line=dict(width=0),
                                                layer="below",
                                            )
                                        )
    
                                fig_riesgos.update_layout(
                                    height=520,
                                    margin=dict(l=10, r=10, t=60, b=20),
                                    xaxis=dict(dtick=1, range=[0.5, 5.5], showgrid=True),
                                    yaxis=dict(dtick=1, range=[0.5, 5.5], showgrid=True),
                                    legend=dict(
                                        orientation="h",
                                        yanchor="top",
                                        y=-0.2,
                                        xanchor="center",
                                        x=0.5,
                                    ),
                                    shapes=shapes,
                                )
                                st.plotly_chart(fig_riesgos, use_container_width=True)
    
                    except Exception as e:
                        st.error(f"No se pudo construir la línea de tiempo de riesgos: {e}")
    
                else:
                    st.info("No hay categorías para el ítem seleccionado en la línea de tiempo.")
            else:
                st.info("No hay datos válidos en 'Mes_inicio' y 'Mes_termino'.")
        else:
            st.info("La tabla de CAPEX no contiene datos suficientes para construir la línea de tiempo.")
    else:
        st.info("Agrega columnas 'Mes_inicio' y 'Mes_termino' en Google Sheets para habilitar esta sección.")
    
    
        # ========================
        # 1) Gráfico PRO: ítems segmentados por categoría
        # ========================
    
        # Totales por categoría
        df_cat_tot = (
            df_capex
            .groupby("Categoria", as_index=False)
            .agg(Total_CLP=("Monto_CLP", "sum"))
        )
    
        df_capex_merged = df_capex.merge(df_cat_tot, on="Categoria", how="left")
    
        # % del ítem dentro de su categoría y del proyecto
        total_clp = df_capex_merged["Monto_CLP"].sum()
        df_capex_merged["Pct_en_categoria"] = df_capex_merged["Monto_CLP"] / df_capex_merged["Total_CLP"]
        df_capex_merged["Pct_total"] = df_capex_merged["Monto_CLP"] / total_clp
    
        # Texto dentro del segmento: "x.x MM / yy% cat"
        df_capex_merged["Texto_seg"] = df_capex_merged.apply(
            lambda r: f"{r['Monto_CLP_MM']:.1f} MM\n{r['Pct_en_categoria']*100:.0f}% cat",
            axis=1
        )
    
        # Ordenar categorías por total CLP (de menor a mayor para que la mayor quede abajo)
        cat_order = (
            df_capex_merged
            .groupby("Categoria")["Monto_CLP"]
            .sum()
            .sort_values(ascending=True)
            .index
            .tolist()
        )
    
        df_capex_plot = df_capex_merged.copy()
        df_capex_plot["Categoria"] = pd.Categorical(
            df_capex_plot["Categoria"],
            categories=cat_order,
            ordered=True,
        )
        legend_label_map = {
            "Generador axial 80kW": "Generador 80kW",
            "Montaje rotor/generador": "Montaje rotor",
            "Simulaciones CFD de rotor híbrido": "Simulaciones CFD",
            "Movimientos de tierra y rellenos": "Tierras y rellenos",
            "Ensayo curva potencia IEC 61400-12": "Ensayo curva IEC",
            "Ensayo curva de potencia IEC 61400-12": "Ensayo curva IEC",
        }
        df_capex_plot["Item_legend"] = df_capex_plot["Item"].replace(legend_label_map)
        item_legend_color_map = {
            legend_label_map.get(item, item): color
            for item, color in item_color_map.items()
        }

        fig_stack = px.bar(
            df_capex_plot,
            x="Monto_CLP_MM",
            y="Categoria",
            color="Item_legend",
            color_discrete_map=item_legend_color_map,
            orientation="h",
            text="Texto_seg",
            labels={
                "Monto_CLP_MM": "Monto (millones de CLP)",
                "Categoria": "",
                "Item_legend": "",
            },
            title="CAPEX por ítem segmentado por categoría (millones de CLP)",
        )
    
        fig_stack.update_traces(
            textposition="inside",
            insidetextanchor="middle",
            textfont_size=10,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Categoría: %{y}<br>"
                "Monto: %{x:.2f} MM CLP<br>"
                "Monto CLP: %{customdata[1]:,.0f}<br>"
                "Monto USD: %{customdata[2]:,.0f}<br>"
                "% en categoría: %{customdata[3]:.1%}<br>"
                "% del proyecto: %{customdata[4]:.1%}<br>"
                "<extra></extra>"
            ),
            customdata=np.stack([
                df_capex_plot["Item"],
                df_capex_plot["Monto_CLP"],
                df_capex_plot["Monto_USD"],
                df_capex_plot["Pct_en_categoria"],
                df_capex_plot["Pct_total"],
            ], axis=-1),
        )
    
        fig_stack.update_layout(
            xaxis_title="Monto (millones de CLP)",
            yaxis_title="",
            margin=dict(l=10, r=10, t=60, b=10),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="left",
                x=0,
                title=dict(text=""),
                font=dict(size=9),
                entrywidth=88,
                entrywidthmode="pixels",
            ),
            height=650,
        )
    
        # Totales por categoría al final de cada barra
        for _, row in df_cat_tot.iterrows():
            fig_stack.add_annotation(
                x=row["Total_CLP"] / 1e6,
                y=row["Categoria"],
                text=f"{row['Total_CLP']/1e6:.1f} MM",
                xanchor="left",
                yanchor="middle",
                showarrow=False,
                font=dict(size=11, color="black"),
                align="left",
                xshift=12,
            )
    
        st.plotly_chart(fig_stack, use_container_width=True)
    
        # ========================
        # 2) Gráfico por CATEGORÍA (abajo)
        # ========================
    
        st.markdown("### Participación relativa por categoría")
    
        fig_cat_pie = px.pie(
            df_cat,
            values="Monto_CLP",
            names="Categoria",
            title="Participación relativa por categoría",
            hole=0.45,
        )
    
        fig_cat_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>"
                          "Participación: %{percent:.1%}<br>"
                          "Monto CLP: %{value:,.0f}<br>"
                          "<extra></extra>",
        )
        fig_cat_pie.update_layout(
            margin=dict(l=10, r=10, t=60, b=10),
            height=600,
        )
    
        st.plotly_chart(fig_cat_pie, use_container_width=True)
        st.session_state["fig_cat_pie"] = fig_cat_pie
    
        # ========================
        # 3) Comentario automático
        # ========================
    
        st.markdown("### Lectura rápida")
        st.write(
            f"- La categoría **{cat_top}** concentra aproximadamente **{cat_top_pct:.1f}%** del CAPEX total.\n"
            f"- Se consideran **{total_items} ítems** distribuidos en **{total_categorias} categorías**.\n"
            f"- El tipo de cambio implícito de la tabla es de **{tipo_cambio_implicito:,.0f} CLP/US$**, "
            f"coherente con un CAPEX de {format_clp(capex_total_clp)}."
        )
    
def render_capex_categoria_content():
    st.markdown(
        '<div class="eng-body-title" style="font-size:21px;font-weight:800;color:#0f172a;margin:0 0 14px 0;">Análisis técnico por categoría</div>',
        unsafe_allow_html=True,
    )

    df_cat_filtrado = df_cat.copy()
    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:0 0 10px 0;">Gráfico por ítem · distribución del CAPEX por categoría</div>',
        unsafe_allow_html=True,
    )

    df_capex_filtrado = df_capex.copy()
    items_unicos = df_capex_filtrado["Item"].unique().tolist()
    num_items = len(items_unicos)

    if num_items > 0:
        n_cols = 3
        n_rows = math.ceil(num_items / n_cols)
        for row_idx in range(n_rows):
            cols = st.columns(n_cols)
            for col_idx in range(n_cols):
                idx = row_idx * n_cols + col_idx
                if idx >= num_items:
                    break
                item_name = items_unicos[idx]
                with cols[col_idx]:
                    df_item_cat = (
                        df_capex_filtrado[df_capex_filtrado["Item"] == item_name]
                        .groupby("Categoria", as_index=False)
                        .agg(Monto_CLP=("Monto_CLP", "sum"))
                    )
                    if df_item_cat.empty:
                        st.caption("Sin distribución disponible para este ítem.")
                        continue

                    total_item = df_item_cat["Monto_CLP"].sum()
                    total_capex_visible = df_capex_filtrado["Monto_CLP"].sum()
                    pct_item_total = (total_item / total_capex_visible) if total_capex_visible > 0 else 0
                    st.markdown(
                        (
                            f'<div class="eng-body-title" style="font-size:14px;font-weight:800;color:#0f172a;'
                            f'margin:0 0 2px 0;">{html.escape(str(item_name))}</div>'
                            f'<div style="font-size:12px;font-weight:400;color:#64748b;margin:0 0 10px 0;">'
                            f'{format_clp(total_item)} · {len(df_item_cat)} categorías activas</div>'
                        ),
                        unsafe_allow_html=True,
                    )
                    fig_donut_item = px.pie(
                        df_item_cat,
                        values="Monto_CLP",
                        names="Categoria",
                        hole=0.70,
                        color="Categoria",
                        color_discrete_map=CAT_COLOR_MAP,
                    )
                    fig_donut_item.update_traces(
                        textinfo="percent",
                        textposition="inside",
                        hovertemplate="<b>%{label}</b><br>Participación dentro del ítem: %{percent:.1%}<br>Monto CLP: %{value:,.0f}<br><extra></extra>",
                        insidetextorientation="horizontal"
                    )
                    fig_donut_item.add_annotation(
                        x=0.5, y=0.5, text=f"{pct_item_total*100:.1f}%", showarrow=False,
                        font=dict(size=22, color="black"), xanchor="center", yanchor="middle"
                    )
                    fig_donut_item.update_layout(
                        showlegend=True,
                        legend=dict(orientation="v", x=1.25, y=0.5, xanchor="left", font=dict(size=11)),
                        margin=dict(l=0, r=120, t=10, b=10),
                        height=280,
                    )
                    st.plotly_chart(fig_donut_item, use_container_width=True)
    else:
        st.info("No hay ítems para mostrar en los dónuts según las categorías seleccionadas.")

    st.markdown(
        '<div class="eng-body-title" style="font-size:15px;font-weight:600;color:#475569;margin:4px 0 10px 0;">Participación porcentual por categoría</div>',
        unsafe_allow_html=True,
    )
    total_clp_cat = df_cat_filtrado["Monto_CLP"].sum()
    df_cat_plot = df_cat_filtrado.copy().sort_values("Monto_CLP", ascending=False)
    df_cat_plot["Pct_cat"] = df_cat_plot["Monto_CLP"] / total_clp_cat if total_clp_cat > 0 else 0.0

    df_cat_item = (
        df_capex.groupby(["Categoria", "Item"], as_index=False)
        .agg(Monto_CLP=("Monto_CLP", "sum"))
        .sort_values(["Categoria", "Monto_CLP"], ascending=[True, False])
    )
    top_item_by_cat = df_cat_item.drop_duplicates(subset=["Categoria"], keep="first")
    cat_item_color_map = {
        row["Categoria"]: item_color_map.get(row["Item"], CAT_COLOR_MAP.get(row["Categoria"], "#2563EB"))
        for _, row in top_item_by_cat.iterrows()
    }

    fig_cat = px.bar(
        df_cat_plot,
        x="Pct_cat",
        y="Categoria",
        orientation="h",
        color="Categoria",
        color_discrete_map=cat_item_color_map,
        text="Pct_cat",
        labels={"Categoria": "", "Pct_cat": "Participación"},
        title="Distribución porcentual del CAPEX por categoría",
    )
    fig_cat.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Participación: %{x:.1%}<extra></extra>",
        marker=dict(line=dict(color="rgba(255,255,255,0.96)", width=1.4)),
    )
    max_part = float(df_cat_plot["Pct_cat"].max() or 0)
    fig_cat.update_xaxes(
        tickformat=".0%",
        range=[0, max_part * 1.18 if max_part > 0 else 1],
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
    )
    fig_cat.update_yaxes(showgrid=False, categoryorder="total ascending")
    fig_cat.update_layout(
        xaxis_title="Participación (%)",
        yaxis_title="",
        margin=dict(l=10, r=34, t=80, b=24),
        height=420,
        bargap=0.32,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_cat, use_container_width=True)
    st.session_state["fig_cat_categoria"] = fig_cat

    legend_css = """
    <style>
    .item-legend { display:flex; flex-wrap:wrap; gap:0.45rem 0.75rem; margin-top:0.4rem; margin-bottom:0.8rem; }
    .item-legend-title { font-size:11px; font-weight:500; color:#64748B; text-transform:uppercase; letter-spacing:.10em; margin-top:0.4rem; margin-bottom:0.25rem; }
    .item-legend-chip { display:inline-flex; align-items:center; gap:0.4rem; font-size:13px; font-weight:400; color:#0f172a; }
    .item-legend-swatch { width:12px; height:12px; border-radius:2px; border:1px solid rgba(17, 24, 39, 0.2); }
    </style>
    """
    legend_items = []
    legend_order = [
        "Desarrollo Tecnológico", "Componentes Mecánicos", "Sistema Eléctrico y Control",
        "Obras Civiles", "Montaje y Logística", "Ensayos y Certificación", "Contingencias y Administración",
    ]
    for item in legend_order:
        color = CAT_COLOR_MAP.get(item, "#2563EB")
        legend_items.append(
            f'<span class="item-legend-chip"><span class="item-legend-swatch" style="background:{color}"></span>{item}</span>'
        )
    st.markdown(
        legend_css + '<div class="item-legend-title">Ítem</div>' + f'<div class="item-legend">{"".join(legend_items)}</div>',
        unsafe_allow_html=True,
    )



def render_capex_items_content():
    st.subheader("Top ítems por monto")
    render_category_palette()

    top_n = st.slider("Número de ítems a mostrar (Top N):", 5, 30, 15, step=1, key="capex_items_top_n")
    df_top = df_capex.sort_values("Monto_CLP", ascending=False).head(top_n).copy()
    df_top["Monto_CLP_fmt"] = df_top["Monto_CLP"].apply(format_clp)
    df_top["Monto_USD_fmt"] = df_top["Monto_USD"].apply(format_usd)
    df_top["Participación (%)"] = df_top["Participacion_pct"] * 100
    df_top["Monto_CLP_MM"] = df_top["Monto_CLP"] / 1e6

    fig_top = px.bar(
        df_top,
        x="Monto_CLP_MM",
        y="Item",
        color="Categoria",
        color_discrete_map=CAT_COLOR_MAP,
        orientation="h",
        hover_data={
            "Monto_CLP_MM": False,
            "Monto_CLP": ":,.0f",
            "Monto_USD": ":,.0f",
            "Participacion_pct": ":.2%",
            "Categoria": True,
        },
        labels={"Monto_CLP_MM": "Monto (MM CLP)", "Item": "Ítem", "Categoria": "Categoría"},
        title=f"Top {top_n} ítems por monto (millones de CLP)",
    )
    fig_top.update_traces(text=df_top["Monto_CLP_MM"].apply(lambda v: f"{v:.1f} MM"), textposition="outside")
    fig_top.update_layout(xaxis_title="Monto (millones de CLP)", yaxis_title="", margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig_top, use_container_width=True)
    st.session_state["fig_top_items"] = fig_top

    st.markdown("#### Tabla detallada")
    st.dataframe(
        df_top[["Item", "Categoria", "Participación (%)", "Monto_CLP_fmt", "Monto_USD_fmt", "Bullet"]],
        hide_index=True,
        use_container_width=True,
    )


def render_capex_module_content(selector_key: str = "capex_internal_selector"):
    st.markdown("---")
    render_capex_categoria_content()


def render_direccion_module_content():
    st.subheader("Fondos de Dirección / Director General Técnico")
    st.info(
        "Esta pestaña muestra fondos de estructura técnica y dirección que se leen desde la hoja "
        "`Director General Técnico`. Estos montos no se suman al CAPEX base de 480 MM CLP."
    )

    if direccion_error:
        st.error(direccion_error)
    elif df_direccion.empty:
        st.warning("La hoja `Director General Técnico` no tiene registros válidos para mostrar.")
    else:
        total_direccion = float(df_direccion["Total"].sum() or 0.0)
        total_meses = float(df_direccion["Meses"].sum() or 0.0)
        costo_mensual_prom_simple = (
            float(df_direccion["Costo empresa mensual"].mean() or 0.0)
            if not df_direccion["Costo empresa mensual"].empty else 0.0
        )
        costo_mensual_prom_ponderado = total_direccion / total_meses if total_meses > 0 else 0.0
        meses_promedio = total_meses / len(df_direccion) if len(df_direccion) > 0 else 0.0
        capex_mas_direccion = capex_total_clp + total_direccion

        dk1, dk2, dk3 = st.columns(3)
        with dk1:
            kpi_card(
                "Fondos capital humano (CLP)",
                format_clp(total_direccion),
                "Monto total separado del CAPEX técnico base."
            )
        with dk2:
            kpi_card(
                "Cargos cubiertos",
                f"{len(df_direccion):,}".replace(",", "."),
                "Roles leídos desde la hoja Dirección General Técnico."
            )
        with dk3:
            kpi_card(
                "Meses acumulados",
                f"{total_meses:,.0f}".replace(",", "."),
                "Suma de meses reportados por cargo."
            )
        st.markdown(
            """
            <style>
            .dir-pro-shell{
                border:1px solid rgba(226,232,240,.92);
                border-radius:24px;
                background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
                box-shadow:0 14px 32px rgba(15,23,42,.06);
                padding:18px 20px 16px 20px;
                margin:8px 0 14px 0;
            }
            .dir-pro-k{
                font-size:11px;
                font-weight:800;
                letter-spacing:.12em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:6px;
            }
            .dir-pro-t{
                font-size:24px;
                font-weight:900;
                line-height:1.06;
                color:#0f172a;
                margin-bottom:8px;
            }
            .dir-pro-s{
                font-size:13px;
                line-height:1.58;
                color:#475569;
                margin-bottom:12px;
            }
            .dir-pro-chip-row{
                display:flex;
                flex-wrap:wrap;
                gap:10px;
            }
            .dir-pro-chip{
                display:inline-flex;
                align-items:center;
                gap:8px;
                padding:7px 11px;
                border-radius:999px;
                border:1px solid rgba(148,163,184,.26);
                background:rgba(255,255,255,.86);
                box-shadow:0 4px 10px rgba(15,23,42,.04);
                font-size:12px;
                color:#0f172a;
            }
            .dir-pro-dot{
                width:10px;
                height:10px;
                border-radius:999px;
                flex:0 0 auto;
            }
            .dir-insight-grid{
                display:grid;
                grid-template-columns:repeat(3,minmax(0,1fr));
                gap:12px;
                margin:0 0 14px 0;
            }
            @media (max-width:1000px){
                .dir-insight-grid{grid-template-columns:1fr;}
            }
            .dir-insight-card{
                border-radius:18px;
                padding:14px 15px 13px 15px;
                border:1px solid rgba(191,219,254,.68);
                background:linear-gradient(180deg,#ffffff 0%,#eff6ff 100%);
                box-shadow:0 6px 16px rgba(15,23,42,.05);
            }
            .dir-insight-label{
                font-size:11px;
                font-weight:800;
                letter-spacing:.10em;
                text-transform:uppercase;
                color:#64748B;
                margin-bottom:6px;
            }
            .dir-insight-value{
                font-size:26px;
                font-weight:900;
                line-height:1.02;
                color:#0f172a;
                margin-bottom:6px;
            }
            .dir-insight-sub{
                font-size:13px;
                line-height:1.5;
                color:#475569;
            }
            .dir-notes{
                margin:0;
                padding-left:18px;
            }
            .dir-notes li{
                margin:0 0 10px 0;
                color:#334155;
                line-height:1.58;
                font-size:14px;
            }
            .dir-notes li:last-child{margin-bottom:0;}
            </style>
            """,
            unsafe_allow_html=True,
        )

        df_dir_plot = df_direccion.copy()
        df_dir_plot["Total_MM"] = df_dir_plot["Total"] / 1e6
        df_dir_plot["Participacion_pct"] = np.where(
            total_direccion > 0,
            df_dir_plot["Total"] / total_direccion * 100.0,
            0.0,
        )
        df_dir_plot["Etiqueta_barra"] = df_dir_plot.apply(
            lambda row: f'{row["Total_MM"]:.1f} MM | {row["Participacion_pct"]:.1f}%',
            axis=1,
        )
        df_dir_plot = df_dir_plot.sort_values("Total", ascending=True).copy()
        df_dir_plot["Cargo_grafico"] = df_dir_plot["Cargo"].replace(
            {
                "Ingeniero de Desarrollo Tecnológico": "Ingeniero de Desarrollo<br>Tecnológico",
                "Líder de Ingeniería y Proyecto": "Líder de Ingeniería<br>y Proyecto",
            }
        )

        direccion_color_map = DIRECTION_ROLE_COLOR_MAP
        max_total_mm = float(df_dir_plot["Total_MM"].max() or 0.0)
        top_role_row = df_dir_plot.sort_values("Total", ascending=False).iloc[0]
        top_role = str(top_role_row["Cargo"])
        top_role_pct = float(top_role_row["Participacion_pct"] or 0.0)
        concentration_top_2 = float(
            df_dir_plot.sort_values("Total", ascending=False).head(2)["Participacion_pct"].sum() or 0.0
        )

        st.markdown(
            f"""
            <div class="dir-pro-shell">
                <div class="dir-pro-k">Visual ejecutivo</div>
                <div class="dir-pro-t">Fondos por cargo de dirección técnica</div>
                <div class="dir-pro-s">Composición económica del bloque de capital humano técnico, ordenada por peso financiero y ajustada para cargos con etiquetas largas.</div>
                <div class="dir-pro-chip-row">
                    <div class="dir-pro-chip"><span class="dir-pro-dot" style="background:#0F4C81"></span><strong>Cargo líder:</strong> {top_role}</div>
                    <div class="dir-pro-chip"><span class="dir-pro-dot" style="background:#0F766E"></span><strong>Concentración top 2:</strong> {concentration_top_2:.1f}%</div>
                    <div class="dir-pro-chip"><span class="dir-pro-dot" style="background:#2563EB"></span><strong>Run-rate ponderado:</strong> {format_clp(costo_mensual_prom_ponderado)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_direccion = px.bar(
            df_dir_plot,
            x="Total_MM",
            y="Cargo_grafico",
            orientation="h",
            text="Etiqueta_barra",
            color="Cargo",
            color_discrete_map=direccion_color_map,
            title="Fondos por cargo de dirección técnica",
            labels={"Total_MM": "Monto total (MM CLP)", "Cargo_grafico": ""},
        )
        fig_direccion.update_traces(
            textposition="outside",
            textfont=dict(size=11, color="#334155"),
            marker=dict(line=dict(color="rgba(255,255,255,0.96)", width=1.4)),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{customdata[3]}</b><br>"
                "Total: %{x:.1f} MM CLP<br>"
                "Participación: %{customdata[0]:.1f}%<br>"
                "Meses: %{customdata[1]:.0f}<br>"
                "Costo mensual: %{customdata[2]:,.0f} CLP<extra></extra>"
            ),
            customdata=df_dir_plot[["Participacion_pct", "Meses", "Costo empresa mensual", "Cargo"]],
        )
        fig_direccion.update_layout(
            showlegend=False,
            margin=dict(l=16, r=124, t=66, b=12),
            height=max(390, 92 * len(df_dir_plot) + 14),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            bargap=0.30,
            title=dict(
                text="Fondos por cargo de direccion tecnica",
                font=dict(size=22, color="#0f172a"),
                x=0.02,
            ),
            font=dict(color="#334155", size=13),
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        apply_engineering_chart_typography(fig_direccion, title_size=20, body_size=13, tick_size=12, legend_size=12)
        fig_direccion.update_xaxes(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.18)",
            zeroline=False,
            ticksuffix=" MM",
            range=[0, max_total_mm * 1.18 if max_total_mm > 0 else 1],
            automargin=True,
        )
        fig_direccion.update_yaxes(showgrid=False, automargin=True)
        st.plotly_chart(fig_direccion, use_container_width=True)

        df_dir_table = df_dir_plot.sort_values("Total", ascending=False).copy()
        df_dir_table.insert(0, "Ranking", [f"#{i}" for i in range(1, len(df_dir_table) + 1)])
        df_dir_table["Costo mensual"] = df_dir_table["Costo empresa mensual"].apply(format_clp)
        df_dir_table["Intensidad"] = df_dir_table.apply(
            lambda row: f"{float(row['Total_MM']) / max(float(row['Meses']), 1):.1f} MM/mes",
            axis=1,
        )
        df_dir_table["Total"] = df_dir_table["Total_MM"].map(lambda v: f"{v:.1f} MM CLP")
        df_dir_table["Participación"] = df_dir_table["Participacion_pct"].map(lambda v: f"{v:.1f}%")

        col_dir_1, col_dir_2 = st.columns([1.22, 1])
        with col_dir_1:
            st.markdown(
                """
                <div class="dir-pro-shell">
                    <div class="dir-pro-k">Tabla ejecutiva</div>
                    <div class="dir-pro-t">Base de cargos</div>
                    <div class="dir-pro-s">Ranking económico del bloque con duración, costo mensual, intensidad de gasto y participación relativa por rol.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.dataframe(
                style_engineering_table(
                    df_dir_table[["Ranking", "Cargo", "Meses", "Costo mensual", "Intensidad", "Total", "Participación"]],
                    header_color="#24446B",
                    row_color="#F4F8FC",
                ),
                hide_index=True,
                use_container_width=True,
                height=220 + 36 * len(df_dir_table),
            )
        with col_dir_2:
            st.markdown(
                """
                <div class="dir-pro-shell">
                    <div class="dir-pro-k">Síntesis ejecutiva</div>
                    <div class="dir-pro-t">Lectura ejecutiva</div>
                    <div class="dir-pro-s">Interpretación de comité enfocada en concentración del gasto, ritmo mensual y relación con el CAPEX técnico.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="dir-insight-grid">
                    <div class="dir-insight-card">
                        <div class="dir-insight-label">Cargo dominante</div>
                        <div class="dir-insight-value">{top_role_pct:.1f}%</div>
                        <div class="dir-insight-sub">{top_role} concentra la mayor parte del bloque y define la referencia principal del costo directivo.</div>
                    </div>
                    <div class="dir-insight-card">
                        <div class="dir-insight-label">Run-rate mensual</div>
                        <div class="dir-insight-value">{format_clp(costo_mensual_prom_ponderado)}</div>
                        <div class="dir-insight-sub">Costo mensual ponderado considerando la duración efectiva de todos los cargos del bloque.</div>
                    </div>
                    <div class="dir-insight-card">
                        <div class="dir-insight-label">Referencia ampliada</div>
                        <div class="dir-insight-value">{format_clp(capex_mas_direccion)}</div>
                        <div class="dir-insight-sub">Valor de referencia si este capital humano técnico se mirara junto con el CAPEX base.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <ul class="dir-notes">
                    <li>Fondos de dirección identificados: <strong>{format_clp(total_direccion)}</strong>.</li>
                    <li>Costo mensual ponderado del bloque: <strong>{format_clp(costo_mensual_prom_ponderado)}</strong> (total dividido por <strong>{f"{total_meses:,.0f}".replace(",", ".")} meses</strong>).</li>
                    <li>Promedio simple entre cargos: <strong>{format_clp(costo_mensual_prom_simple)}</strong>; no coincide con el run-rate porque los cargos tienen distinta duración.</li>
                    <li>Duración promedio por cargo: <strong>{meses_promedio:.1f} meses</strong>.</li>
                    <li>Los dos cargos de mayor peso concentran <strong>{concentration_top_2:.1f}%</strong> del bloque, lo que revela una estructura de gasto relativamente concentrada.</li>
                    <li>Este bloque se mantiene deliberadamente separado para no contaminar el desglose del CAPEX de ingeniería.</li>
                </ul>
                """,
                unsafe_allow_html=True,
            )


if False:
    render_top_summary_kpis()
    render_capex_module_content(selector_key="capex_internal_selector")

# -------------------------
# TAB EXPLORADOR
# -------------------------
if False:
    render_top_summary_kpis()
    render_explorador_module_content(key_prefix="explorer_")

# -------------------------
# TAB DIRECCIÓN TÉCNICA
# -------------------------
if False:
    render_top_summary_kpis()
    render_direccion_module_content()

# -------------------------
# TAB VALORIZACIÓN
# -------------------------
if False:
    render_top_summary_kpis()
    render_valorizacion_module_content(key_prefix="val_")

# =========================
# REPORTING PDF TÉCNICO
# =========================

def build_pdf_report() -> bytes:
    """Genera un informe técnico en PDF para directivos con KPIs y gráficos principales."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    elementos = []

    # --- Portada ---
    elementos.append(Paragraph("Reporte CAPEX – Piloto Eólico 80 kW", h1))
    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(Paragraph("Informe técnico ejecutivo para directorio y comité de inversiones.", body))
    elementos.append(Spacer(1, 1.0 * cm))

    # Tabla de KPIs
    kpi_data = [
        ["Indicador", "Valor", "Comentario"],
        ["CAPEX total (CLP)", format_clp(capex_total_clp), "Inversión total piloto 80 kW"],
        ["CAPEX total (USD)", format_usd(capex_total_usd), f"Tipo de cambio implícito ≈ {tipo_cambio_implicito:,.0f} CLP/US$"],
        ["Tipo de cambio implícito", f"{tipo_cambio_implicito:,.1f} CLP/US$", "CAPEX CLP / suma de costos en USD"],
        ["Categoría de mayor peso", cat_top, f"≈ {cat_top_pct:.1f}% del CAPEX total"],
    ]
    kpi_table = Table(kpi_data, colWidths=[5 * cm, 4 * cm, 7 * cm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (1, 1), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    elementos.append(kpi_table)
    elementos.append(PageBreak())

    # --- Gráfico 1: CAPEX por ítem ---
    if "fig_item_total" in st.session_state:
        elementos.append(Paragraph("1. Distribución de CAPEX por ítem", h2))
        img_bytes = pio.to_image(st.session_state["fig_item_total"], format="png", scale=2)
        elementos.append(Image(BytesIO(img_bytes), width=17 * cm, height=9 * cm))
        elementos.append(Spacer(1, 0.6 * cm))

    # --- Gráfico 2: Pie por categoría (resumen ejecutivo) ---
    if "fig_cat_pie" in st.session_state:
        elementos.append(Paragraph("2. Participación relativa por categoría", h2))
        img_bytes = pio.to_image(st.session_state["fig_cat_pie"], format="png", scale=2)
        elementos.append(Image(BytesIO(img_bytes), width=14 * cm, height=8 * cm))
        elementos.append(PageBreak())

    # --- Gráfico 3: Barra por categoría (TAB 'Por categoría') ---
    if "fig_cat_categoria" in st.session_state:
        elementos.append(Paragraph("3. Análisis de CAPEX por categoría (vista ingeniería)", h2))
        img_bytes = pio.to_image(st.session_state["fig_cat_categoria"], format="png", scale=2)
        elementos.append(Image(BytesIO(img_bytes), width=17 * cm, height=9 * cm))
        elementos.append(Spacer(1, 0.6 * cm))

    # --- Gráfico 4: Top ítems (TAB 'Detalle de ítems') ---
    if "fig_top_items" in st.session_state:
        elementos.append(Paragraph("4. Top ítems de inversión", h2))
        img_bytes = pio.to_image(st.session_state["fig_top_items"], format="png", scale=2)
        elementos.append(Image(BytesIO(img_bytes), width=17 * cm, height=9 * cm))
        elementos.append(PageBreak())

    # --- Tablas resumen clave ---
    elementos.append(Paragraph("5. Resumen tabular de categorías", h2))
    df_tab_cat = df_cat.sort_values("Monto_CLP", ascending=False).head(10).copy()
    df_tab_cat["Participación (%)"] = df_tab_cat["Participacion_sum"] * 100

    table_data = [["Categoría", "Participación (%)", "Monto CLP", "Monto USD"]]
    for _, row in df_tab_cat.iterrows():
        table_data.append(
            [
                row["Categoria"],
                f"{row['Participación (%)']:.1f}%",
                format_clp(row["Monto_CLP"]),
                format_usd(row["Monto_USD"]),
            ]
        )

    cat_table = Table(table_data, colWidths=[7 * cm, 3 * cm, 3.5 * cm, 3.5 * cm])
    cat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    elementos.append(cat_table)

    doc.build(elementos)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value


if False:
    st.markdown("---")
    st.subheader("📄 Exportar informe técnico")
    
    pdf_bytes = build_pdf_report()
    st.download_button(
        label="📥 Descargar reporte PDF técnico (CAPEX Piloto 80 kW)",
        data=pdf_bytes,
        file_name="Reporte_CAPEX_Piloto_80kW.pdf",
        mime="application/pdf",
    )
