from __future__ import annotations

from io import BytesIO
import html
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components


CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vR6ouTippfyLquWDgCXB7j_arqGGn2i5kND2FX5CKxTiQ0amOu33ZC2sY7kh_yqtQ/"
    "pub?gid=176738706&single=true&output=csv"
)

PMO_MATRIX_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vR6ouTippfyLquWDgCXB7j_arqGGn2i5kND2FX5CKxTiQ0amOu33ZC2sY7kh_yqtQ/"
    "pub?gid=446249592&single=true&output=csv"
)

TECHNICAL_MILESTONES = [
    "Gestion tecnica y continuidad del proyecto",
    "Habilitacion del sitio y obras previas",
    "Fundacion estructural y anclajes",
    "Fabricacion y cierre tecnico de aspas FRP",
    "Logistica, suministros y armado inicial",
    "Integracion mecanica, izaje y balanceo",
    "Integracion electrica, proteccion e instrumentacion",
    "Comisionamiento, documentacion y puesta en marcha",
]

DISPLAY_MILESTONES = [
    "Gestión técnica y continuidad del proyecto",
    "Habilitación del sitio y obras previas",
    "Fundación estructural y anclajes",
    "Fabricación y cierre técnico de aspas FRP",
    "Logística, suministros y armado inicial",
    "Integración mecánica, izaje y balanceo",
    "Integración eléctrica, protección e instrumentación",
    "Comisionamiento, documentación y puesta en marcha",
]

MILESTONE_DISPLAY_BY_KEY = dict(zip(TECHNICAL_MILESTONES, DISPLAY_MILESTONES))

ROADMAP_LABELS = {
    "Gestión técnica y continuidad del proyecto": "Gestión técnica y continuidad",
    "Habilitación del sitio y obras previas": "Obras preliminares",
    "Fundación estructural y anclajes": "Fundación estructural",
    "Fabricación y cierre técnico de aspas FRP": "Fabricación aspas FRP",
    "Logística, suministros y armado inicial": "Logística y armado",
    "Integración mecánica, izaje y balanceo": "Integración mecánica",
    "Integración eléctrica, protección e instrumentación": "Integración eléctrica",
    "Comisionamiento, documentación y puesta en marcha": "Puesta en marcha",
}

ROADMAP_ICONS = {
    "Gestión técnica y continuidad del proyecto": "PMO",
    "Habilitación del sitio y obras previas": "CIV",
    "Fundación estructural y anclajes": "FND",
    "Fabricación y cierre técnico de aspas FRP": "FRP",
    "Logística, suministros y armado inicial": "LOG",
    "Integración mecánica, izaje y balanceo": "MEC",
    "Integración eléctrica, protección e instrumentación": "ELE",
    "Comisionamiento, documentación y puesta en marcha": "RUN",
}

SOURCE_COLORS = {
    "Restante piloto 10kW": "#0F766E",
    "Hoja 1 línea de tiempo": "#1E3A5F",
    "Hoja 1 linea de tiempo": "#1E3A5F",
    "Sin fuente": "#64748B",
}

MILESTONE_COLORS = [
    "#0B2D42",
    "#276749",
    "#2F557F",
    "#9A6A16",
    "#4B5563",
    "#0E7490",
    "#475569",
    "#0F766E",
]

STATE_COLORS = {
    "Pendiente": "#F59E0B",
    "En curso": "#0EA5A4",
    "Completado": "#16A34A",
    "Atrasado": "#DC2626",
    "Sin estado": "#64748B",
}


st.set_page_config(
    page_title="Fluxial Wind 10 kW | Avance Ejecutivo",
    layout="wide",
    initial_sidebar_state="collapsed",
)

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = [
    "#0B2D42",
    "#0F766E",
    "#2F557F",
    "#94A3B8",
    "#14B8A6",
    "#475569",
    "#F59E0B",
    "#16A34A",
]


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    replacements = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")
    return re.sub(r"\s+", " ", text.translate(replacements))


def parse_money(value: object) -> float:
    if pd.isna(value):
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text:
        return 0.0
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    else:
        pieces = text.split(".")
        if len(pieces) == 2 and len(pieces[1]) == 3:
            text = "".join(pieces)
        else:
            text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_percent(value: object) -> float:
    if pd.isna(value):
        return 0.0
    text = str(value).strip().replace("%", "").replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return 0.0
    return number / 100 if number > 1 else number


def parse_date(value: object) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    return pd.to_datetime(text, dayfirst=True, errors="coerce")


def format_clp(value: float) -> str:
    return f"${value:,.0f}".replace(",", ".")


def format_pct(value: float) -> str:
    return f"{value:.1%}".replace(".", ",")


def format_date(value: object) -> str:
    dt = pd.to_datetime(value, errors="coerce")
    return "-" if pd.isna(dt) else dt.strftime("%d-%m-%Y")


def business_days(start: object, end: object) -> int:
    start_dt = pd.to_datetime(start, errors="coerce")
    end_dt = pd.to_datetime(end, errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt):
        return 0
    if end_dt < start_dt:
        end_dt = start_dt
    return int(np.busday_count(start_dt.date(), (end_dt + pd.Timedelta(days=1)).date()))


@st.cache_data(ttl=60, show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return pd.read_csv(BytesIO(response.content))


def find_week_columns(df: pd.DataFrame) -> list[str]:
    week_cols = []
    for col in df.columns:
        if re.fullmatch(r"\d{2}-\d{2}", str(col).strip()):
            week_cols.append(col)
    return week_cols


def horizon_dates(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    week_dates = [
        pd.to_datetime(f"{col}-2026", format="%d-%m-%Y", errors="coerce")
        for col in find_week_columns(df)
    ]
    week_dates = [date for date in week_dates if pd.notna(date)]
    if week_dates:
        start = min(week_dates)
        end = max(week_dates) + pd.Timedelta(days=6)
    else:
        scheduled = df[df["Inicio"].notna() & df["Termino"].notna()]
        start = scheduled["Inicio"].min() if not scheduled.empty else pd.Timestamp("today").normalize()
        end = scheduled["Termino"].max() if not scheduled.empty else start + pd.DateOffset(months=4)
    hard_end = start + pd.DateOffset(months=4)
    return start, min(end, hard_end)


def clean_schedule(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw_df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    expected = {
        "ID",
        "Fuente",
        "Hito",
        "Hito Ejecutivo",
        "Categoría/Línea",
        "Descripción Técnica / Acción",
        "Estado",
        "Avance",
        "Inicio Acción",
        "Término Acción",
        "Duración Hábil",
        "Monto CLP",
        "Liberación Inicial",
        "Liberación Avance",
        "Liberación Cierre",
        "Total Liberación",
    }
    missing = sorted(expected - set(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas en la fuente: {', '.join(missing)}")

    raw_id = df["ID"].astype(str).str.strip().str.lower()
    raw_desc = df["Descripción Técnica / Acción"].astype(str).str.strip().str.lower()
    auxiliary_rows = raw_id.isin({"", "nan", "none"}) & raw_desc.isin({"", "nan", "none"})
    df = df.loc[~auxiliary_rows].copy()

    df["ID"] = df["ID"].astype(str).str.strip()
    df["Fuente"] = df["Fuente"].fillna("Sin fuente").astype(str).str.strip().replace("", "Sin fuente")
    df["Estado"] = df["Estado"].fillna("Sin estado").astype(str).str.strip().replace("", "Sin estado")
    df["Hito"] = df["Hito"].fillna("Sin hito").astype(str).str.strip().replace("", "Sin hito")
    df["Hito Ejecutivo"] = df["Hito Ejecutivo"].fillna("Sin hito ejecutivo").astype(str).str.strip()
    df["Hito Key"] = df["Hito Ejecutivo"].map(normalize_text)
    df["Hito Ejecutivo"] = df["Hito Key"].map(MILESTONE_DISPLAY_BY_KEY).fillna(df["Hito Ejecutivo"])
    df["Categoría/Línea"] = df["Categoría/Línea"].fillna("Sin categoría").astype(str).str.strip()
    df["Descripción Técnica / Acción"] = (
        df["Descripción Técnica / Acción"].fillna("Sin descripción").astype(str).str.strip()
    )
    df["Inicio"] = df["Inicio Acción"].apply(parse_date)
    df["Termino"] = df["Término Acción"].apply(parse_date)
    df["Fecha corregida"] = False
    invalid_order = df["Inicio"].notna() & df["Termino"].notna() & (df["Termino"] < df["Inicio"])
    df.loc[invalid_order, "Termino"] = df.loc[invalid_order, "Inicio"]
    df.loc[invalid_order, "Fecha corregida"] = True
    df["Pendiente programación"] = df["Inicio"].isna() | df["Termino"].isna()

    for col in ["Monto CLP", "Liberación Inicial", "Liberación Avance", "Liberación Cierre", "Total Liberación"]:
        df[f"{col} Num"] = df[col].apply(parse_money)

    df["Avance Num"] = df["Avance"].apply(parse_percent)
    df["Duración Hábil Num"] = pd.to_numeric(df["Duración Hábil"], errors="coerce")
    computed_duration = df.apply(lambda row: business_days(row["Inicio"], row["Termino"]), axis=1)
    df["Duración Hábil Num"] = df["Duración Hábil Num"].fillna(computed_duration).astype(float)
    df.loc[df["Duración Hábil Num"] < 0, "Duración Hábil Num"] = 0
    df["Duración Hábil Num"] = df["Duración Hábil Num"].astype(int)

    df["Actividad"] = df["ID"] + " | " + df["Descripción Técnica / Acción"].str.slice(0, 92)
    df["Monto MMCLP"] = df["Monto CLP Num"] / 1_000_000
    df["Fuente Color"] = df["Fuente"].map(SOURCE_COLORS).fillna("#64748B")
    df["Hito Corto"] = df["Hito Ejecutivo"].map(ROADMAP_LABELS).fillna(df["Hito Ejecutivo"])
    text_flags = (
        df["Descripción Técnica / Acción"].astype(str)
        + " "
        + df["Categoría/Línea"].astype(str)
        + " "
        + df["Hito Ejecutivo"].astype(str)
    ).str.lower()
    amount_threshold = df["Monto CLP Num"].quantile(0.82) if len(df) else 0
    today = pd.Timestamp("today").normalize()
    df["Es crítica"] = (
        text_flags.str.contains("crit|imprevisto|fundaci|izaje|proteccion|comision|puesta en marcha|scada|instrument")
        | (df["Monto CLP Num"] >= amount_threshold)
        | df["Estado"].astype(str).str.contains("atras", case=False, na=False)
    )
    df["Es habilitante"] = text_flags.str.contains(
        "habilit|fundaci|anclaje|izaje|balanceo|conexion|proteccion|instrument|scada|comision|puesta en marcha",
        regex=True,
    )
    df["Es próxima"] = df["Inicio"].between(today, today + pd.Timedelta(days=30), inclusive="both")
    df["Riesgo operacional"] = np.select(
        [
            df["Es crítica"] & df["Es habilitante"],
            df["Es crítica"] | (df["Monto CLP Num"] >= amount_threshold),
            df["Es próxima"] | df["Es habilitante"],
        ],
        ["Alto", "Medio", "Bajo"],
        default="Controlado",
    )
    df["Criticidad"] = np.select(
        [df["Es crítica"], df["Es habilitante"], df["Es próxima"]],
        ["Crítica", "Habilitante", "Próxima"],
        default="Operacional",
    )

    week_cols = find_week_columns(df)
    weekly_records = []
    for _, row in df.iterrows():
        active_weeks = [col for col in week_cols if str(row.get(col, "")).strip() not in {"", "nan", "NaN"}]
        if active_weeks:
            weekly_amount = row["Total Liberación Num"] / len(active_weeks) if active_weeks else 0.0
            for col in active_weeks:
                weekly_records.append(
                    {
                        "Semana": pd.to_datetime(f"{col}-2026", format="%d-%m-%Y", errors="coerce"),
                        "Monto CLP": weekly_amount,
                        "Fuente": row["Fuente"],
                        "Hito Ejecutivo": row["Hito Ejecutivo"],
                    }
                )
        elif pd.notna(row["Inicio"]):
            weekly_records.append(
                {
                    "Semana": pd.to_datetime(row["Inicio"]).to_period("W-MON").start_time,
                    "Monto CLP": row["Total Liberación Num"],
                    "Fuente": row["Fuente"],
                    "Hito Ejecutivo": row["Hito Ejecutivo"],
                }
            )
    weekly_df = pd.DataFrame(weekly_records)
    if not weekly_df.empty:
        weekly_df = (
            weekly_df.dropna(subset=["Semana"])
            .groupby("Semana", as_index=False)["Monto CLP"]
            .sum()
            .sort_values("Semana")
        )
        weekly_df["Acumulado CLP"] = weekly_df["Monto CLP"].cumsum()
        weekly_df["Monto MMCLP"] = weekly_df["Monto CLP"] / 1_000_000
        weekly_df["Acumulado MMCLP"] = weekly_df["Acumulado CLP"] / 1_000_000

    return df, weekly_df


def make_hito_summary(df: pd.DataFrame) -> pd.DataFrame:
    total = float(df["Monto CLP Num"].sum() or 0)
    grouped = (
        df.groupby(["Hito", "Hito Ejecutivo"], as_index=False)
        .agg(
            Monto_CLP=("Monto CLP Num", "sum"),
            Liberacion_Inicial=("Liberación Inicial Num", "sum"),
            Liberacion_Avance=("Liberación Avance Num", "sum"),
            Liberacion_Cierre=("Liberación Cierre Num", "sum"),
            Total_Liberacion=("Total Liberación Num", "sum"),
            Partidas=("ID", "count"),
            Inicio=("Inicio", "min"),
            Termino=("Termino", "max"),
            Duracion_habil=("Duración Hábil Num", "sum"),
            Avance_promedio=("Avance Num", "mean"),
            Pendientes_programacion=("Pendiente programación", "sum"),
        )
        .sort_values("Inicio", na_position="last")
    )
    grouped["% sobre total"] = np.where(total > 0, grouped["Monto_CLP"] / total, 0)
    source_mode = (
        df.groupby("Hito Ejecutivo")["Fuente"]
        .agg(lambda s: s.value_counts().idxmax() if not s.dropna().empty else "Sin fuente")
        .to_dict()
    )
    state_mode = (
        df.groupby("Hito Ejecutivo")["Estado"]
        .agg(lambda s: s.value_counts().idxmax() if not s.dropna().empty else "Sin estado")
        .to_dict()
    )
    grouped["Fuente principal"] = grouped["Hito Ejecutivo"].map(source_mode).fillna("Sin fuente")
    grouped["Estado"] = grouped["Hito Ejecutivo"].map(state_mode).fillna("Sin estado")
    grouped["Hito Corto"] = grouped["Hito Ejecutivo"].map(ROADMAP_LABELS).fillna(grouped["Hito Ejecutivo"])
    grouped["Hito Orden"] = grouped["Hito"].astype(str).str.extract(r"(\d+)").astype(float).fillna(99)
    grouped["Inicio"] = grouped["Inicio"].apply(format_date)
    grouped["Termino"] = grouped["Termino"].apply(format_date)
    grouped["Monto total"] = grouped["Monto_CLP"].apply(format_clp)
    grouped["Liberación Inicial"] = grouped["Liberacion_Inicial"].apply(format_clp)
    grouped["Liberación Avance"] = grouped["Liberacion_Avance"].apply(format_clp)
    grouped["Liberación Cierre"] = grouped["Liberacion_Cierre"].apply(format_clp)
    grouped["Total Liberación"] = grouped["Total_Liberacion"].apply(format_clp)
    grouped["% total"] = grouped["% sobre total"].apply(format_pct)
    return grouped.sort_values("Hito Orden").reset_index(drop=True)


def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)
            worksheet = writer.sheets[safe_name]
            for idx, col in enumerate(df.columns):
                width = min(max(12, int(df[col].astype(str).str.len().quantile(0.9)) + 2), 42)
                worksheet.column_dimensions[worksheet.cell(row=1, column=idx + 1).column_letter].width = width
    return output.getvalue()


def add_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #0B2D42;
            --graphite: #1F2937;
            --teal: #0F766E;
            --aqua: #14B8A6;
            --line: #DDE6EF;
            --soft: #F5F8FB;
        }
        .stApp { background: #F6F8FB; color: #111827; }
        .block-container {
            max-width: 1480px;
            padding-top: 3.25rem;
            padding-bottom: 3rem;
            margin-left: auto;
            margin-right: auto;
        }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E5EAF0; }
        h1, h2, h3 { color: var(--navy); letter-spacing: 0; }
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E3EAF2;
            border-left: 4px solid var(--teal);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, .05);
        }
        div[data-testid="stMetric"] label { color: #64748B; font-weight: 700; }
        div[data-testid="stMetricValue"] { color: var(--navy); font-weight: 800; }
        .hero {
            background: transparent;
            border: 0;
            border-radius: 0;
            padding: 4px 4px 20px;
            margin-bottom: 2px;
            box-shadow: none;
        }
        .hero-kicker {
            display: none;
            color: #475569;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .hero-title {
            color: #23457A;
            font-size: 20px;
            line-height: 1.1;
            font-weight: 950;
            margin: 0 0 6px 0;
        }
        .hero-copy {
            color: #64748B;
            font-size: 12px;
            line-height: 1.38;
            max-width: 780px;
        }
        .section-note {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 14px 16px;
            color: #334155;
            line-height: 1.55;
        }
        .exec-list {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 8px 20px rgba(15,23,42,.04);
        }
        .exec-list li { margin-bottom: 8px; }
        .pill {
            display: inline-block;
            border: 1px solid #CBD5E1;
            border-radius: 999px;
            padding: 5px 10px;
            margin: 0 8px 8px 0;
            background: #FFFFFF;
            color: #334155;
            font-size: 12px;
            font-weight: 700;
        }
        .pmo-card {
            background: linear-gradient(180deg,#FFFFFF 0%,#F8FBFC 100%);
            border: 1px solid #DDE8EE;
            border-radius: 10px;
            padding: 16px 17px;
            min-height: 112px;
            box-shadow: 0 14px 28px rgba(15,23,42,.06);
        }
        .pmo-card .label {
            color: #64748B;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .pmo-card .value {
            color: #0B2D42;
            font-size: 24px;
            font-weight: 850;
            line-height: 1.15;
            margin-top: 8px;
        }
        .pmo-card .note {
            color: #64748B;
            font-size: 12px;
            line-height: 1.35;
            margin-top: 8px;
        }
        .roadmap-shell {
            background:
                linear-gradient(180deg, rgba(255,255,255,.98) 0%, rgba(246,250,252,.98) 100%);
            border: 1px solid #DAE6ED;
            border-radius: 12px;
            padding: 20px 22px 18px 22px;
            box-shadow: 0 18px 42px rgba(15,23,42,.07);
            overflow-x: auto;
        }
        .roadmap-titlebar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 18px;
        }
        .roadmap-titlebar h3 {
            margin: 0;
            color: #0B2D42;
            font-size: 20px;
            line-height: 1.1;
            letter-spacing: 0;
        }
        .roadmap-titlebar p {
            margin: 6px 0 0 0;
            color: #64748B;
            font-size: 13px;
            line-height: 1.45;
        }
        .roadmap-grid {
            position: relative;
            min-width: 1060px;
            padding: 46px 0 14px 0;
        }
        .roadmap-months {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0;
            position: absolute;
            inset: 0 0 auto 190px;
            height: 34px;
            border-bottom: 1px solid #DCE5EC;
        }
        .roadmap-month {
            color: #475569;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            padding-left: 12px;
            border-left: 1px solid #E6EEF3;
        }
        .roadmap-today {
            position: absolute;
            top: 36px;
            bottom: 0;
            width: 2px;
            background: #0B2D42;
            opacity: .9;
            z-index: 5;
        }
        .roadmap-today span {
            position: absolute;
            top: -31px;
            left: -19px;
            background: #0B2D42;
            color: #FFFFFF;
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 10px;
            font-weight: 850;
            letter-spacing: .04em;
        }
        .roadmap-next30 {
            position: absolute;
            top: 36px;
            bottom: 0;
            background: rgba(20,184,166,.10);
            border-left: 1px solid rgba(20,184,166,.22);
            border-right: 1px solid rgba(20,184,166,.22);
            z-index: 1;
        }
        .roadmap-row {
            position: relative;
            display: grid;
            grid-template-columns: 190px 1fr;
            min-height: 74px;
            align-items: center;
            border-bottom: 1px solid rgba(226,232,240,.82);
            z-index: 2;
        }
        .roadmap-label {
            display: flex;
            align-items: center;
            gap: 11px;
            padding-right: 16px;
        }
        .roadmap-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg,#0B2D42,#0F766E);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 900;
            box-shadow: 0 10px 22px rgba(15,118,110,.22);
        }
        .roadmap-name {
            color: #0F172A;
            font-size: 13px;
            font-weight: 850;
            line-height: 1.18;
        }
        .roadmap-meta {
            color: #64748B;
            font-size: 11px;
            margin-top: 5px;
        }
        .roadmap-track {
            position: relative;
            height: 44px;
            border-left: 1px solid #EEF2F6;
            background:
                linear-gradient(90deg, transparent 0%, transparent 24.8%, rgba(226,232,240,.78) 25%, transparent 25.2%, transparent 49.8%, rgba(226,232,240,.78) 50%, transparent 50.2%, transparent 74.8%, rgba(226,232,240,.78) 75%, transparent 75.2%);
        }
        .roadmap-bar {
            position: absolute;
            top: 9px;
            height: 25px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(11,45,66,.96), rgba(15,118,110,.94));
            box-shadow: 0 12px 20px rgba(15,23,42,.13);
        }
        .roadmap-badges {
            position: absolute;
            top: -11px;
            display: flex;
            gap: 6px;
            flex-wrap: nowrap;
        }
        .roadmap-badge {
            background: rgba(255,255,255,.96);
            border: 1px solid #D7E2EA;
            color: #334155;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 10px;
            font-weight: 850;
            white-space: nowrap;
            box-shadow: 0 6px 14px rgba(15,23,42,.06);
        }
        .roadmap-badge.high { color: #B91C1C; border-color: rgba(220,38,38,.28); }
        .roadmap-badge.next { color: #0F766E; border-color: rgba(15,118,110,.28); }
        .roadmap-caption {
            color: #64748B;
            font-size: 12px;
            margin-top: 14px;
            line-height: 1.45;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            border: 1px solid #DDE6EF;
            border-radius: 999px;
            padding: 8px 16px;
            background: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">FLUXIAL WIND · PILOTO 10 KW</div>
            <div class="hero-title">Control ejecutivo de integración y continuidad operacional</div>
            <div class="hero-copy">Seguimiento técnico, financiero y PMO del piloto eólico vertical.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(df: pd.DataFrame) -> None:
    dated = df[~df["Pendiente programación"]].copy()
    total_amount = float(df["Monto CLP Num"].sum() or 0)
    source_amounts = df.groupby("Fuente")["Monto CLP Num"].sum().to_dict()
    start, end = horizon_dates(df)
    calendar_days = int((end - start).days + 1) if pd.notna(start) and pd.notna(end) else 0
    business_total = business_days(start, end) if calendar_days else 0

    row_1 = st.columns(4)
    row_1[0].metric("Partidas cronograma", f"{len(df):,.0f}".replace(",", "."))
    row_1[1].metric("Monto total proyecto", format_clp(total_amount))
    row_1[2].metric("Hitos tecnicos principales", f"{df['Hito Ejecutivo'].nunique():,.0f}".replace(",", "."))
    row_1[3].metric("Duracion total", f"{business_total} dias habiles", f"{calendar_days} dias corridos")

    row_2 = st.columns(4)
    row_2[0].metric("Restante piloto 10kW", format_clp(source_amounts.get("Restante piloto 10kW", 0)))
    row_2[1].metric(
        "Hoja 1 linea de tiempo",
        format_clp(
            source_amounts.get("Hoja 1 línea de tiempo", 0)
            + source_amounts.get("Hoja 1 linea de tiempo", 0)
        ),
    )
    row_2[2].metric("Fecha inicio", format_date(start))
    row_2[3].metric("Termino estimado", format_date(end))


def project_stage(df: pd.DataFrame) -> tuple[str, str]:
    today = pd.Timestamp("today").normalize()
    scheduled = df[~df["Pendiente programación"]].copy()
    if scheduled.empty:
        return "-", "-"
    current = scheduled[(scheduled["Inicio"] <= today) & (scheduled["Termino"] >= today)]
    if current.empty:
        current = scheduled.sort_values("Inicio").head(1)
    next_stage = scheduled[scheduled["Inicio"] > today].sort_values("Inicio").head(1)
    current_hito = current.iloc[0]["Hito Corto"] if not current.empty else "-"
    next_hito = next_stage.iloc[0]["Hito Corto"] if not next_stage.empty else "-"
    return str(current_hito), str(next_hito)


def render_premium_kpis(df: pd.DataFrame) -> None:
    total = float(df["Monto CLP Num"].sum() or 0)
    committed = float(df.loc[df["Avance Num"] > 0, "Monto CLP Num"].sum())
    weighted_progress = float((df["Monto CLP Num"] * df["Avance Num"]).sum() / total) if total else 0.0
    remaining = max(total - committed, 0.0)
    critical_count = int(df["Es crítica"].sum())
    current_hito, next_hito = project_stage(df)
    horizon_start, horizon_end = horizon_dates(df)
    launch_rows = df[df["Hito Ejecutivo"].str.contains("Comisionamiento|puesta en marcha", case=False, na=False)]
    launch_date = launch_rows["Termino"].max() if not launch_rows.empty else horizon_end
    horizon_remaining = max(business_days(pd.Timestamp("today").normalize(), horizon_end), 0)

    cards = [
        ("Avance estimado", format_pct(weighted_progress), "Ponderado por monto y avance declarado"),
        ("Monto comprometido", format_clp(committed), "Actividades con avance registrado"),
        ("Monto restante", format_clp(remaining), "Brecha financiera por ejecutar"),
        ("Actividades críticas", f"{critical_count}", "Riesgo, habilitantes o alto monto"),
        ("Hito actual", current_hito, "Foco operacional del periodo"),
        ("Próximo hito", next_hito, "Siguiente transición de riesgo"),
        ("Puesta en marcha", format_date(launch_date), "Fecha esperada de cierre operativo"),
        ("Horizonte restante", f"{horizon_remaining} días hábiles", f"Hasta {format_date(horizon_end)}"),
    ]
    cols = st.columns(4)
    for idx, (label, value, note) in enumerate(cards):
        with cols[idx % 4]:
            st.markdown(
                f"""
                <div class="pmo-card">
                  <div class="label">{html.escape(label)}</div>
                  <div class="value">{html.escape(str(value))}</div>
                  <div class="note">{html.escape(note)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if idx == 3:
            cols = st.columns(4)


def roadmap_month_labels(start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
    labels = []
    cursor = pd.Timestamp(start.year, start.month, 1)
    while cursor <= end:
        labels.append(cursor.strftime("%b %Y").upper())
        cursor = cursor + pd.DateOffset(months=1)
    return labels[:4] if labels else []


def render_executive_roadmap(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> None:
    pmo_matrix = build_pmo_hito_matrix(df, hito_summary, pmo_source).sort_values("Hito Orden").copy()
    scheduled_hitos = pmo_matrix[pmo_matrix["_Inicio"].notna() & pmo_matrix["_Termino"].notna()]
    if not scheduled_hitos.empty:
        horizon_start = scheduled_hitos["_Inicio"].min()
        horizon_end = scheduled_hitos["_Termino"].max()
    else:
        horizon_start, horizon_end = horizon_dates(df)
    horizon_days = max((horizon_end - horizon_start).days, 1)
    today = pd.Timestamp("today").normalize()

    def pct(date_value: pd.Timestamp) -> float:
        return max(0.0, min(100.0, ((date_value - horizon_start).days / horizon_days) * 100.0))

    today_left = pct(today)
    next_left = pct(today)
    next_width = max(0.0, pct(today + pd.Timedelta(days=30)) - next_left)
    months = roadmap_month_labels(horizon_start, horizon_end)
    month_cells = "".join(f"<div class='roadmap-month'>{html.escape(label)}</div>" for label in months)
    while len(months) < 4:
        month_cells += "<div class='roadmap-month'></div>"
        months.append("")

    rows = []
    for _, hito in pmo_matrix.iterrows():
        milestone = str(hito.get("Hito Ejecutivo", ""))
        hito_df = df[df["Hito Ejecutivo"].eq(milestone)].copy()
        raw_start = pd.to_datetime(hito.get("_Inicio", pd.NaT), errors="coerce")
        raw_end = pd.to_datetime(hito.get("_Termino", pd.NaT), errors="coerce")
        if pd.isna(raw_start) or pd.isna(raw_end):
            scheduled = hito_df[~hito_df["Pendiente programación"]].copy()
            raw_start = scheduled["Inicio"].min() if not scheduled.empty else horizon_start
            raw_end = scheduled["Termino"].max() if not scheduled.empty else horizon_start + pd.Timedelta(days=7)
        start = max(pd.Timestamp(raw_start), horizon_start)
        end = min(max(pd.Timestamp(raw_end), start + pd.Timedelta(days=1)), horizon_end)
        left = pct(start)
        width = max(3.0, pct(end) - left)
        amount = float(hito.get("Total_Liberacion", 0) or hito.get("Monto_CLP", 0) or 0)
        initial = float(hito.get("Liberacion_Inicial", 0) or 0)
        advance = float(hito.get("Liberacion_Avance", 0) or 0)
        close = float(hito.get("Liberacion_Cierre", 0) or 0)
        criticality = str(hito.get("Criticidad", "Media"))
        status = str(hito.get("Estado", "Pendiente"))
        condition = str(hito.get("Condición de Liberación", "")).strip()
        risk = "alto" if criticality == "Alta" else "medio" if criticality == "Media" else "controlado"
        next_count = int(hito_df["Es próxima"].sum()) if not hito_df.empty else 0
        badges = [
            f"<span class='roadmap-badge high'>Riesgo {risk}</span>" if criticality in {"Alta", "Media"} else "<span class='roadmap-badge'>Riesgo controlado</span>",
            f"<span class='roadmap-badge next'>{html.escape(status)}</span>",
            f"<span class='roadmap-badge'>{format_clp(amount)}</span>",
        ]
        rows.append(
            f"""
            <div class="roadmap-row">
              <div class="roadmap-label">
                <div class="roadmap-icon">{html.escape(ROADMAP_ICONS.get(milestone, "PMO"))}</div>
                <div>
                  <div class="roadmap-name">{html.escape(ROADMAP_LABELS.get(milestone, milestone))}</div>
                  <div class="roadmap-meta">{html.escape(str(hito.get("Hito", "")))} · {format_date(raw_start)} a {format_date(raw_end)}</div>
                  <div class="roadmap-meta">Inicial {format_clp(initial)} · Avance {format_clp(advance)} · Cierre {format_clp(close)}</div>
                </div>
              </div>
              <div class="roadmap-track">
                <div class="roadmap-bar" style="left:{left:.2f}%;width:{width:.2f}%;"></div>
                <div class="roadmap-badges" style="left:{min(left + width + 1.2, 76):.2f}%;">{''.join(badges)}</div>
                <div class="roadmap-condition" style="left:{max(left, 1):.2f}%;width:{min(max(width, 18), 70):.2f}%;">{html.escape(condition or 'Condición PMO por definir')}</div>
              </div>
            </div>
            """
        )

    component_css = """
        <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Arial, sans-serif;
            color: #0F172A;
        }
        .roadmap-shell {
            background: linear-gradient(180deg, rgba(255,255,255,.99) 0%, rgba(246,250,252,.99) 100%);
            border: 1px solid #DAE6ED;
            border-radius: 14px;
            padding: 20px 22px 18px 22px;
            box-shadow: 0 18px 42px rgba(15,23,42,.07);
            overflow-x: auto;
        }
        .roadmap-titlebar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 18px;
        }
        .roadmap-titlebar h3 {
            margin: 0;
            color: #0B2D42;
            font-size: 21px;
            line-height: 1.1;
            letter-spacing: 0;
        }
        .roadmap-titlebar p {
            margin: 7px 0 0 0;
            color: #64748B;
            font-size: 13px;
            line-height: 1.45;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
            border: 1px solid #CBD5E1;
            border-radius: 999px;
            padding: 6px 11px;
            background: #FFFFFF;
            color: #334155;
            font-size: 12px;
            font-weight: 800;
        }
        .roadmap-grid {
            position: relative;
            min-width: 1060px;
            padding: 46px 0 14px 0;
        }
        .roadmap-months {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0;
            position: absolute;
            left: 190px;
            right: 0;
            top: 0;
            height: 34px;
            border-bottom: 1px solid #DCE5EC;
        }
        .roadmap-month {
            color: #475569;
            font-size: 12px;
            font-weight: 850;
            text-transform: uppercase;
            padding-left: 12px;
            border-left: 1px solid #E6EEF3;
        }
        .roadmap-overlay {
            position: absolute;
            left: 190px;
            right: 0;
            top: 36px;
            bottom: 14px;
            pointer-events: none;
            z-index: 4;
        }
        .roadmap-today {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #0B2D42;
            opacity: .9;
        }
        .roadmap-today span {
            position: absolute;
            top: -31px;
            left: -20px;
            background: #0B2D42;
            color: #FFFFFF;
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: .04em;
        }
        .roadmap-next30 {
            position: absolute;
            top: 0;
            bottom: 0;
            background: rgba(20,184,166,.10);
            border-left: 1px solid rgba(20,184,166,.24);
            border-right: 1px solid rgba(20,184,166,.24);
        }
        .roadmap-row {
            position: relative;
            display: grid;
            grid-template-columns: 190px 1fr;
            min-height: 74px;
            align-items: center;
            border-bottom: 1px solid rgba(226,232,240,.82);
            z-index: 2;
        }
        .roadmap-label {
            display: flex;
            align-items: center;
            gap: 11px;
            padding-right: 16px;
        }
        .roadmap-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg,#0B2D42,#0F766E);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 900;
            box-shadow: 0 10px 22px rgba(15,118,110,.22);
            flex: 0 0 auto;
        }
        .roadmap-name {
            color: #0F172A;
            font-size: 13px;
            font-weight: 850;
            line-height: 1.18;
        }
        .roadmap-meta {
            color: #64748B;
            font-size: 11px;
            margin-top: 5px;
        }
        .roadmap-track {
            position: relative;
            height: 56px;
            border-left: 1px solid #EEF2F6;
            background:
                linear-gradient(90deg, transparent 0%, transparent 24.8%, rgba(226,232,240,.78) 25%, transparent 25.2%, transparent 49.8%, rgba(226,232,240,.78) 50%, transparent 50.2%, transparent 74.8%, rgba(226,232,240,.78) 75%, transparent 75.2%);
        }
        .roadmap-bar {
            position: absolute;
            top: 9px;
            height: 25px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(11,45,66,.96), rgba(15,118,110,.94));
            box-shadow: 0 12px 20px rgba(15,23,42,.13);
        }
        .roadmap-badges {
            position: absolute;
            top: -11px;
            display: flex;
            gap: 6px;
            flex-wrap: nowrap;
            z-index: 3;
        }
        .roadmap-badge {
            background: rgba(255,255,255,.98);
            border: 1px solid #D7E2EA;
            color: #334155;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 10px;
            font-weight: 850;
            white-space: nowrap;
            box-shadow: 0 6px 14px rgba(15,23,42,.06);
        }
        .roadmap-badge.high { color: #B91C1C; border-color: rgba(220,38,38,.28); }
        .roadmap-badge.next { color: #0F766E; border-color: rgba(15,118,110,.28); }
        .roadmap-condition {
            position: absolute;
            top: 39px;
            color: #475569;
            font-size: 10px;
            font-weight: 750;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .roadmap-caption {
            color: #64748B;
            font-size: 12px;
            margin-top: 14px;
            line-height: 1.45;
        }
        </style>
    """
    html_doc = f"""
        {component_css}
        <div class="roadmap-shell">
          <div class="roadmap-titlebar">
            <div>
              <h3>Roadmap ejecutivo de convergencia operacional</h3>
              <p>Hitos H1-H8 alimentados por Matriz PMO: liberación de fondos, condición de desbloqueo y convergencia hacia puesta en marcha.</p>
            </div>
            <div class="pill">Horizonte {format_date(horizon_start)} · {format_date(horizon_end)}</div>
          </div>
          <div class="roadmap-grid">
            <div class="roadmap-months">{month_cells}</div>
            <div class="roadmap-overlay">
              <div class="roadmap-next30" style="left:{next_left:.2f}%;width:{next_width:.2f}%;"></div>
              <div class="roadmap-today" style="left:{today_left:.2f}%;"><span>HOY</span></div>
            </div>
            {''.join(rows)}
          </div>
          <div class="roadmap-caption">
            Fuente financiera: Matriz PMO de hitos. Ventana turquesa: próximos 30 días. Las barras posicionan cada hito en el cronograma operacional y muestran su liberación total asociada.
          </div>
        </div>
    """
    components.html(html_doc, height=690, scrolling=True)


def build_gantt(df: pd.DataFrame, zoom: str = "4 meses") -> go.Figure:
    dfp = df[~df["Pendiente programación"]].sort_values(["Inicio", "Termino", "ID"]).copy()
    horizon_start, horizon_end = horizon_dates(df)
    if zoom == "30 días":
        horizon_end = min(horizon_end, pd.Timestamp("today").normalize() + pd.Timedelta(days=30))
    elif zoom == "60 días":
        horizon_end = min(horizon_end, pd.Timestamp("today").normalize() + pd.Timedelta(days=60))
    dfp = dfp[(dfp["Termino"] >= horizon_start) & (dfp["Inicio"] <= horizon_end)].copy()
    dfp["Bar Start"] = dfp["Inicio"].clip(lower=horizon_start)
    dfp["Bar End"] = dfp["Termino"].clip(upper=horizon_end)
    dfp["Y Label"] = dfp["Hito Corto"] + " · " + dfp["ID"]
    fig = go.Figure()
    if dfp.empty:
        fig.update_layout(
            height=360,
            title="No hay actividades programadas dentro del horizonte de cuatro meses.",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig
    for source, group in dfp.groupby("Fuente", sort=False):
        color = SOURCE_COLORS.get(source, "#64748B")
        fig.add_trace(
            go.Bar(
                x=(group["Bar End"] - group["Bar Start"]).dt.days.clip(lower=1) * 24 * 60 * 60 * 1000,
                y=group["Y Label"],
                base=group["Bar Start"],
                orientation="h",
                name=source,
                marker=dict(color=color, opacity=0.78, line=dict(color="rgba(255,255,255,.9)", width=1.4)),
                width=0.52,
                customdata=np.stack(
                    [
                        group["Hito Ejecutivo"],
                        group["Estado"],
                        group["Monto CLP Num"].map(format_clp),
                        group["Duración Hábil Num"],
                        group["Avance Num"],
                        group["Criticidad"],
                        group["Descripción Técnica / Acción"].str.slice(0, 120),
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "<b>%{customdata[6]}</b><br>"
                    "Hito: %{customdata[0]}<br>"
                    "Estado: %{customdata[1]} · %{customdata[5]}<br>"
                    "Monto: %{customdata[2]}<br>"
                    "Duracion habil: %{customdata[3]} dias<br>"
                    "Avance: %{customdata[4]:.0%}<extra></extra>"
                ),
            )
        )

    milestone_summary = (
        dfp.groupby("Hito Ejecutivo", as_index=False)
        .agg(Inicio=("Bar Start", "min"), Termino=("Bar End", "max"))
        .sort_values("Inicio")
    )
    fig.add_trace(
        go.Scatter(
            x=milestone_summary["Termino"],
            y=[dfp.loc[dfp["Hito Ejecutivo"].eq(h), "Y Label"].iloc[-1] for h in milestone_summary["Hito Ejecutivo"]],
            mode="markers+text",
            name="Dependencia / hito",
            marker=dict(symbol="diamond", size=13, color="#14B8A6", line=dict(color="#0B2D42", width=1.5)),
            text=[f"H{i + 1}" for i in range(len(milestone_summary))],
            textposition="middle right",
            hovertext=milestone_summary["Hito Ejecutivo"],
            hoverinfo="text",
        )
    )

    fig.update_layout(
        height=max(460, min(1040, 130 + 28 * len(dfp))),
        barmode="overlay",
        bargap=0.5,
        margin=dict(l=24, r=30, t=58, b=34),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.12, x=1, xanchor="right", bgcolor="rgba(255,255,255,0)"),
        xaxis=dict(
            range=[horizon_start, horizon_end],
            title=None,
            gridcolor="rgba(148,163,184,.20)",
            tickformat="%d %b",
            dtick=7 * 24 * 60 * 60 * 1000,
        ),
        yaxis=dict(autorange="reversed", title=None, tickfont=dict(size=11, color="#334155"), automargin=True),
        hoverlabel=dict(bgcolor="#0B2D42", font_color="#FFFFFF"),
    )
    today = pd.Timestamp("today").normalize()
    next_end = min(today + pd.Timedelta(days=30), horizon_end)
    if next_end > today:
        fig.add_vrect(
            x0=today,
            x1=next_end,
            fillcolor="rgba(20,184,166,.08)",
            line_width=0,
            layer="below",
        )
    fig.add_shape(
        type="line",
        x0=today.strftime("%Y-%m-%d"),
        x1=today.strftime("%Y-%m-%d"),
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="#0B2D42", width=1.6, dash="dot"),
    )
    fig.add_annotation(
        x=today.strftime("%Y-%m-%d"),
        y=1.02,
        xref="x",
        yref="paper",
        text="HOY",
        showarrow=False,
        font=dict(color="#0B2D42", size=11),
    )
    return fig


def build_financial_figures(df: pd.DataFrame, weekly_df: pd.DataFrame) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure]:
    hito_amount = (
        df.groupby("Hito Ejecutivo", as_index=False)["Monto CLP Num"].sum().sort_values("Monto CLP Num", ascending=True)
    )
    hito_amount["Monto MMCLP"] = hito_amount["Monto CLP Num"] / 1_000_000
    fig_hito = px.bar(
        hito_amount,
        x="Monto MMCLP",
        y="Hito Ejecutivo",
        orientation="h",
        color="Hito Ejecutivo",
        color_discrete_sequence=MILESTONE_COLORS,
        text=hito_amount["Monto CLP Num"].map(format_clp),
        title="Monto por hito tecnico",
    )
    fig_hito.update_layout(showlegend=False, xaxis_title="MM CLP", yaxis_title=None, margin=dict(l=10, r=10, t=58, b=20))

    stages = pd.DataFrame(
        {
            "Etapa": ["Liberacion inicial", "Liberacion avance", "Liberacion cierre"],
            "Monto CLP": [
                df["Liberación Inicial Num"].sum(),
                df["Liberación Avance Num"].sum(),
                df["Liberación Cierre Num"].sum(),
            ],
        }
    )
    stages["Monto MMCLP"] = stages["Monto CLP"] / 1_000_000
    fig_stages = px.bar(
        stages,
        x="Etapa",
        y="Monto MMCLP",
        color="Etapa",
        color_discrete_sequence=["#0B2D42", "#0F766E", "#94A3B8"],
        text=stages["Monto CLP"].map(format_clp),
        title="Liberacion de fondos por etapa",
    )
    fig_stages.update_layout(showlegend=False, xaxis_title=None, yaxis_title="MM CLP", margin=dict(l=10, r=10, t=58, b=20))

    source_budget = df.groupby("Fuente", as_index=False)["Monto CLP Num"].sum()
    fig_source = px.pie(
        source_budget,
        names="Fuente",
        values="Monto CLP Num",
        color="Fuente",
        color_discrete_map=SOURCE_COLORS,
        hole=0.58,
        title="Distribucion del presupuesto por fuente",
    )
    fig_source.update_traces(textposition="outside", texttemplate="%{label}<br>%{percent:.1%}")
    fig_source.update_layout(margin=dict(l=10, r=10, t=58, b=20))

    if weekly_df.empty:
        weekly_df = pd.DataFrame(columns=["Semana", "Monto MMCLP", "Acumulado MMCLP"])
    fig_week = go.Figure()
    fig_week.add_trace(
        go.Bar(
            x=weekly_df["Semana"],
            y=weekly_df["Monto MMCLP"],
            name="Inversion semanal",
            marker_color="#94A3B8",
        )
    )
    fig_week.add_trace(
        go.Scatter(
            x=weekly_df["Semana"],
            y=weekly_df["Acumulado MMCLP"],
            name="Acumulado",
            mode="lines+markers",
            line=dict(color="#0F766E", width=3),
            marker=dict(size=7),
            yaxis="y2",
        )
    )
    fig_week.update_layout(
        title="Curva acumulada de inversion semanal",
        yaxis=dict(title="MM CLP semanal"),
        yaxis2=dict(title="MM CLP acumulado", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1, x=1, xanchor="right"),
        margin=dict(l=10, r=10, t=58, b=20),
    )
    return fig_hito, fig_stages, fig_source, fig_week


def build_operational_figures(df: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    risk_order = ["Alto", "Medio", "Bajo", "Controlado"]
    risk_df = (
        df.groupby(["Categoría/Línea", "Riesgo operacional"], as_index=False)
        .agg(Actividades=("ID", "count"), Monto_CLP=("Monto CLP Num", "sum"))
    )
    risk_df["Riesgo operacional"] = pd.Categorical(risk_df["Riesgo operacional"], risk_order, ordered=True)
    risk_df = risk_df.sort_values(["Riesgo operacional", "Monto_CLP"], ascending=[True, False]).head(18)
    fig_risk = px.scatter(
        risk_df,
        x="Monto_CLP",
        y="Categoría/Línea",
        size="Actividades",
        color="Riesgo operacional",
        color_discrete_map={"Alto": "#DC2626", "Medio": "#F59E0B", "Bajo": "#0EA5A4", "Controlado": "#64748B"},
        title="Riesgo operacional por categoría",
    )
    fig_risk.update_traces(marker=dict(opacity=0.82, line=dict(width=1, color="#FFFFFF")))
    fig_risk.update_layout(
        xaxis_title="Monto CLP",
        yaxis_title=None,
        margin=dict(l=10, r=10, t=58, b=20),
        legend=dict(orientation="h", y=1.12, x=1, xanchor="right"),
    )
    fig_risk.update_xaxes(tickprefix="$", separatethousands=True)

    source_df = (
        df.groupby("Fuente", as_index=False)
        .agg(Avance=("Avance Num", "mean"), Actividades=("ID", "count"), Monto_CLP=("Monto CLP Num", "sum"))
    )
    fig_source_progress = px.bar(
        source_df,
        x="Fuente",
        y="Avance",
        color="Fuente",
        color_discrete_map=SOURCE_COLORS,
        text=source_df["Avance"].map(format_pct),
        title="Avance por fuente de información",
    )
    fig_source_progress.update_layout(
        showlegend=False,
        yaxis_tickformat=".0%",
        yaxis_range=[0, max(0.08, min(1, float(source_df["Avance"].max() if not source_df.empty else 0) + 0.08))],
        xaxis_title=None,
        yaxis_title="Avance promedio",
        margin=dict(l=10, r=10, t=58, b=20),
    )
    return fig_risk, fig_source_progress


def hito_status(row: pd.Series, today: pd.Timestamp | None = None) -> str:
    today = today or pd.Timestamp("today").normalize()
    start = pd.to_datetime(row.get("Inicio"), dayfirst=True, errors="coerce")
    end = pd.to_datetime(row.get("Termino"), dayfirst=True, errors="coerce")
    progress = float(row.get("Avance_promedio", 0) or 0)
    if progress >= 0.95:
        return "Ejecutado"
    if pd.notna(start) and pd.notna(end) and start <= today <= end:
        return "En curso"
    if progress > 0:
        return "En curso"
    return "Pendiente"


def hito_stage(row: pd.Series) -> str:
    progress = float(row.get("Avance_promedio", 0) or 0)
    if progress < 0.20:
        return "Liberación inicial"
    if progress < 0.80:
        return "Avance"
    return "Cierre"


def pmo_risk(financial_progress: float, technical_progress: float) -> str:
    if financial_progress < 0.20 and technical_progress > 0.20:
        return "Alto"
    if financial_progress > 0.60:
        return "Bajo"
    return "Medio"


def hito_criticality(row: pd.Series, df: pd.DataFrame) -> str:
    hito = row.get("Hito Ejecutivo", "")
    group = df[df["Hito Ejecutivo"].eq(hito)]
    total = float(df["Monto CLP Num"].sum() or 0)
    share = float(row.get("Monto_CLP", 0) or 0) / total if total else 0
    critical_count = int(group["Es crítica"].sum()) if not group.empty else 0
    enabling_count = int(group["Es habilitante"].sum()) if not group.empty else 0
    launch_related = bool(re.search("Comisionamiento|puesta en marcha|Integración eléctrica|Integración mecánica", str(hito), re.I))
    if launch_related or critical_count >= 3 or share >= 0.25:
        return "Alta"
    if critical_count >= 1 or enabling_count >= 2 or share >= 0.10:
        return "Media"
    return "Baja"


def scenario_for_criticality(criticality: str, hito_name: str) -> str:
    if criticality == "Alta" or re.search("Comisionamiento|puesta en marcha|Integración eléctrica|Integración mecánica", hito_name, re.I):
        return "Cierre"
    if criticality == "Media":
        return "Base"
    return "Conservador"


def pmo_decision_for(row: pd.Series) -> str:
    scenario = row.get("Escenario recomendado", "Base")
    if scenario == "Cierre":
        return "Aprobar liberación total y bloquear interferencias operacionales."
    if scenario == "Base":
        return "Aprobar inicial + avance con control semanal PMO."
    return "Autorizar liberación inicial y validar gatillos técnicos."


def pmo_comment_for(row: pd.Series) -> str:
    criticality = row.get("Criticidad", "Media")
    if criticality == "Alta":
        return "Hito sensible para continuidad: requiere decisión ejecutiva y monitoreo de dependencias."
    if criticality == "Media":
        return "Mantener fondos de avance disponibles para evitar desaceleración técnica."
    return "Puede operar con liberación inicial mientras no bloquee integración."


def clean_pmo_matrix_source(raw_pmo: pd.DataFrame | None) -> pd.DataFrame:
    if raw_pmo is None or raw_pmo.empty:
        return pd.DataFrame()

    pmo = raw_pmo.copy()
    pmo.columns = [normalize_text(col) for col in pmo.columns]
    rename_map = {
        "Hito": "Hito",
        "Hito Ejecutivo": "Hito Ejecutivo",
        "Inicio": "Inicio",
        "Termino": "Termino",
        "Monto Restante CLP": "Monto_CLP",
        "Liberacion Inicial 30%": "Liberacion_Inicial",
        "Liberacion Avance 50%": "Liberacion_Avance",
        "Liberacion Cierre 20%": "Liberacion_Cierre",
        "Total Liberacion": "Total_Liberacion",
        "Condicion de Liberacion": "Condición de Liberación",
    }
    pmo = pmo.rename(columns={col: rename_map.get(col, col) for col in pmo.columns})

    required = {"Hito", "Hito Ejecutivo"}
    if not required.issubset(set(pmo.columns)):
        return pd.DataFrame()

    for col in ["Monto_CLP", "Liberacion_Inicial", "Liberacion_Avance", "Liberacion_Cierre", "Total_Liberacion"]:
        if col not in pmo.columns:
            pmo[col] = 0.0
        pmo[col] = pmo[col].apply(parse_money)

    for col in ["Inicio", "Termino"]:
        if col not in pmo.columns:
            pmo[col] = pd.NaT
        pmo[col] = pmo[col].apply(parse_date)

    if "Condición de Liberación" not in pmo.columns:
        pmo["Condición de Liberación"] = ""

    pmo["Hito"] = pmo["Hito"].astype(str).str.strip()
    pmo["Hito Ejecutivo"] = pmo["Hito Ejecutivo"].astype(str).str.strip()
    return pmo[
        [
            "Hito",
            "Hito Ejecutivo",
            "Inicio",
            "Termino",
            "Monto_CLP",
            "Liberacion_Inicial",
            "Liberacion_Avance",
            "Liberacion_Cierre",
            "Total_Liberacion",
            "Condición de Liberación",
        ]
    ]


def build_pmo_hito_matrix(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> pd.DataFrame:
    today = pd.Timestamp("today").normalize()
    source = clean_pmo_matrix_source(pmo_source)
    if not source.empty:
        schedule_cols = [
            "Hito",
            "Partidas",
            "Inicio",
            "Termino",
            "Duracion_habil",
            "Avance_promedio",
            "Pendientes_programacion",
            "Fuente principal",
            "Hito Orden",
            "Hito Corto",
        ]
        schedule = hito_summary[[col for col in schedule_cols if col in hito_summary.columns]].copy()
        matrix = source.merge(schedule, on="Hito", how="left", suffixes=("", "_Cronograma"))
        matrix["Fuente matriz"] = "Matriz PMO"
    else:
        matrix = hito_summary.copy()
        matrix["Fuente matriz"] = "Cronograma Integrado"

    matrix["Hito Orden"] = pd.to_numeric(matrix.get("Hito Orden"), errors="coerce")
    hito_order_from_code = matrix["Hito"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    matrix["Hito Orden"] = matrix["Hito Orden"].fillna(hito_order_from_code)
    matrix["Hito Corto"] = matrix.get("Hito Corto", pd.Series(index=matrix.index, dtype=object))
    matrix["Hito Corto"] = matrix["Hito Corto"].fillna(matrix["Hito Ejecutivo"].map(ROADMAP_LABELS)).fillna(matrix["Hito Ejecutivo"])

    defaults: dict[str, object] = {
        "Partidas": 0,
        "Inicio": pd.NaT,
        "Termino": pd.NaT,
        "Duracion_habil": 0,
        "Avance_promedio": 0.0,
        "Pendientes_programacion": 0,
        "Fuente principal": "Matriz PMO",
    }
    for col, default in defaults.items():
        if col not in matrix.columns:
            matrix[col] = default
        matrix[col] = matrix[col].fillna(default)

    if "Inicio_Cronograma" in matrix.columns:
        matrix["Inicio"] = matrix["Inicio"].where(matrix["Inicio"].notna(), matrix["Inicio_Cronograma"])
    if "Termino_Cronograma" in matrix.columns:
        matrix["Termino"] = matrix["Termino"].where(matrix["Termino"].notna(), matrix["Termino_Cronograma"])

    total = float(matrix["Monto_CLP"].sum() or 0)
    matrix["% sobre total"] = np.where(total > 0, matrix["Monto_CLP"] / total, 0)
    matrix["Monto total"] = matrix["Monto_CLP"].apply(format_clp)
    matrix["Liberación Inicial"] = matrix["Liberacion_Inicial"].apply(format_clp)
    matrix["Liberación Avance"] = matrix["Liberacion_Avance"].apply(format_clp)
    matrix["Liberación Cierre"] = matrix["Liberacion_Cierre"].apply(format_clp)
    matrix["Total Liberación"] = matrix["Total_Liberacion"].apply(format_clp)
    matrix["% total"] = matrix["% sobre total"].apply(format_pct)
    if "Condición de Liberación" not in matrix.columns:
        matrix["Condición de Liberación"] = ""

    matrix["_Inicio"] = pd.to_datetime(matrix["Inicio"], dayfirst=True, errors="coerce")
    matrix["_Termino"] = pd.to_datetime(matrix["Termino"], dayfirst=True, errors="coerce")
    matrix["Etapa del hito"] = matrix.apply(hito_stage, axis=1)
    matrix["Estado"] = matrix.apply(lambda row: hito_status(row, today), axis=1)
    matrix["Criticidad"] = matrix.apply(lambda row: hito_criticality(row, df), axis=1)
    matrix["Escenario recomendado"] = matrix.apply(
        lambda row: scenario_for_criticality(row["Criticidad"], str(row["Hito Ejecutivo"])),
        axis=1,
    )
    matrix["Monto crítico próximo Num"] = np.where(
        matrix["_Inicio"].between(today, today + pd.Timedelta(days=60), inclusive="both"),
        matrix["Total_Liberacion"],
        0,
    )
    matrix["Monto crítico próximo"] = matrix["Monto crítico próximo Num"].apply(format_clp)
    matrix["Decisión requerida"] = matrix.apply(pmo_decision_for, axis=1)
    matrix["Comentario ejecutivo"] = matrix.apply(pmo_comment_for, axis=1)
    return matrix


def pmo_financial_metrics(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> dict[str, object]:
    today = pd.Timestamp("today").normalize()
    matrix = build_pmo_hito_matrix(df, hito_summary, pmo_source)
    total_capex = float(matrix["Monto_CLP"].sum() or df["Monto CLP Num"].sum() or 0)
    committed = float((df["Monto CLP Num"] * df["Avance Num"]).sum())
    total_release = float(matrix["Total_Liberacion"].sum() or df["Total Liberación Num"].sum() or 0)
    technical_progress = float((df["Monto CLP Num"] * df["Avance Num"]).sum() / total_capex) if total_capex else 0.0
    financial_progress = committed / total_release if total_release else 0.0
    breach = max(total_capex - committed, 0.0)
    current = matrix[matrix["Estado"].eq("En curso")].sort_values(["Criticidad", "Hito Orden"], ascending=[True, True])
    if current.empty:
        current = matrix[matrix["_Inicio"].ge(today)].sort_values("_Inicio").head(1)
    if current.empty:
        current = matrix.sort_values("Hito Orden").head(1)
    current_row = current.iloc[0] if not current.empty else pd.Series(dtype=object)
    next_row = matrix[matrix["_Inicio"].gt(pd.to_datetime(current_row.get("_Inicio"), errors="coerce"))].sort_values("_Inicio").head(1)
    matrix_launch = matrix[matrix["Hito"].astype(str).eq("H8")]
    if matrix_launch.empty:
        matrix_launch = matrix[matrix["Hito Ejecutivo"].str.contains("Comisionamiento|puesta en marcha", case=False, na=False)]
    if not matrix_launch.empty and matrix_launch["_Termino"].notna().any():
        launch_date = matrix_launch["_Termino"].max()
    else:
        launch_rows = df[df["Hito Ejecutivo"].str.contains("Comisionamiento|puesta en marcha", case=False, na=False)]
        launch_date = launch_rows["Termino"].max() if not launch_rows.empty else pd.NaT
    funds_30 = float(matrix.loc[matrix["_Inicio"].between(today, today + pd.Timedelta(days=30), inclusive="both"), "Total_Liberacion"].sum())
    funds_60 = float(matrix.loc[matrix["_Inicio"].between(today, today + pd.Timedelta(days=60), inclusive="both"), "Total_Liberacion"].sum())
    risk = pmo_risk(financial_progress, technical_progress)
    return {
        "total_capex": total_capex,
        "committed": committed,
        "total_release": total_release,
        "funds_30": funds_30,
        "funds_60": funds_60,
        "technical_progress": technical_progress,
        "financial_progress": financial_progress,
        "breach": breach,
        "risk": risk,
        "matrix": matrix,
        "current_row": current_row,
        "next_row": next_row.iloc[0] if not next_row.empty else pd.Series(dtype=object),
        "launch_date": launch_date,
    }


def render_hitos_header(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> dict[str, object]:
    metrics = pmo_financial_metrics(df, hito_summary, pmo_source)
    current = metrics["current_row"]
    next_row = metrics["next_row"]
    recommendation = (
        "Priorizar liberación inicial del hito actual y asegurar fondos de avance."
        if metrics["risk"] != "Bajo"
        else "Mantener cadencia de liberación y control de cierre técnico."
    )
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#FFFFFF 0%,#F4FAFA 58%,#EEF4F7 100%);border:1px solid #DCE8EF;border-radius:14px;padding:22px 24px;margin:4px 0 18px 0;box-shadow:0 18px 38px rgba(15,23,42,.07);">
          <div style="font-size:12px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#0F766E;margin-bottom:8px;">Executive PMO Financial View</div>
          <div style="font-size:28px;font-weight:900;line-height:1.1;color:#0B2D42;margin-bottom:8px;">Vista Ejecutiva de Hitos y Liberación de Fondos</div>
          <div style="font-size:14px;line-height:1.55;color:#475569;max-width:1120px;">Seguimiento PMO del piloto 10 kW: avance técnico, CAPEX pendiente y escenarios de continuidad.</div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px;">
          <div class="pmo-card"><div class="label">Hito actual</div><div class="value">{html.escape(str(current.get("Hito Corto", "-")))}</div><div class="note">{html.escape(str(current.get("Estado", "-")))} · {html.escape(str(current.get("Escenario recomendado", "-")))}</div></div>
          <div class="pmo-card"><div class="label">Próximo hito</div><div class="value">{html.escape(str(next_row.get("Hito Corto", "-")))}</div><div class="note">{format_date(next_row.get("_Inicio", pd.NaT))}</div></div>
          <div class="pmo-card"><div class="label">Fecha crítica</div><div class="value">{format_date(current.get("_Termino", pd.NaT))}</div><div class="note">Cierre esperado del hito actual</div></div>
          <div class="pmo-card"><div class="label">Recomendación ejecutiva</div><div class="value" style="font-size:16px;line-height:1.25;">{html.escape(recommendation)}</div><div class="note">Riesgo PMO: {html.escape(str(metrics["risk"]))}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return metrics


def render_hitos_kpis(metrics: dict[str, object]) -> None:
    current = metrics["current_row"]
    current_amount = float(current.get("Monto_CLP", 0) or 0)
    cards = [
        ("CAPEX restante total", format_clp(float(metrics["total_capex"])), "Base de decisión financiera"),
        ("Monto hito actual", format_clp(current_amount), str(current.get("Hito Corto", "-"))),
        ("Fondos críticos 30 días", format_clp(float(metrics["funds_30"])), "Liberaciones con inicio próximo"),
        ("Fondos críticos 60 días", format_clp(float(metrics["funds_60"])), "Continuidad de dos ciclos PMO"),
        ("% avance técnico ponderado", format_pct(float(metrics["technical_progress"])), "Ponderado por monto"),
        ("Brecha continuidad", format_clp(float(metrics["breach"])), "CAPEX no comprometido"),
        ("Puesta en marcha", format_date(metrics["launch_date"]), "Fecha estimada"),
        ("Riesgo PMO actual", str(metrics["risk"]), "Bajo / Medio / Alto"),
    ]
    cols = st.columns(4)
    for idx, (label, value, note) in enumerate(cards):
        with cols[idx % 4]:
            st.markdown(
                f"""
                <div class="pmo-card">
                  <div class="label">{html.escape(label)}</div>
                  <div class="value">{html.escape(str(value))}</div>
                  <div class="note">{html.escape(note)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if idx == 3:
            cols = st.columns(4)


def build_funding_roadmap(hito_summary: pd.DataFrame) -> go.Figure:
    plot_df = hito_summary.copy()
    plot_df = plot_df.sort_values("Hito Orden", ascending=False)
    y_values = plot_df["Hito"].astype(str) + " · " + plot_df["Hito Corto"].astype(str)
    fig = go.Figure()
    segments = [
        ("Liberación inicial", "Liberacion_Inicial", "#0B2D42"),
        ("Liberación avance", "Liberacion_Avance", "#14B8A6"),
        ("Liberación cierre", "Liberacion_Cierre", "#16A34A"),
    ]
    cumulative = np.zeros(len(plot_df))
    for label, col, color in segments:
        values = plot_df[col].astype(float).to_numpy()
        fig.add_trace(
            go.Bar(
                x=values / 1_000_000,
                y=y_values,
                base=cumulative / 1_000_000,
                orientation="h",
                name=label,
                marker=dict(color=color, line=dict(color="rgba(255,255,255,.9)", width=1.2)),
                customdata=np.stack([plot_df["Hito Ejecutivo"], pd.Series(values).map(format_clp)], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b><br>%{fullData.name}: %{customdata[1]}<extra></extra>",
            )
        )
        cumulative += values
    fig.update_layout(
        title="Funding Roadmap",
        barmode="stack",
        height=max(430, 96 + 42 * len(plot_df)),
        margin=dict(l=14, r=24, t=58, b=28),
        xaxis_title="MM CLP",
        yaxis_title=None,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.11, x=1, xanchor="right"),
        hoverlabel=dict(bgcolor="#0B2D42", font_color="#FFFFFF"),
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,.18)")
    fig.update_yaxes(tickfont=dict(size=11, color="#334155"))
    return fig


def render_funding_scenarios(metrics: dict[str, object]) -> None:
    current = metrics["current_row"]
    total = float(current.get("Total_Liberacion", 0) or 0)
    scenarios = [
        ("Escenario Conservador", float(current.get("Liberacion_Inicial", 0) or 0), "Solo liberación inicial", "Continuidad limitada", "Alto", "#DC2626"),
        ("Escenario Base", float(current.get("Liberacion_Inicial", 0) or 0) + float(current.get("Liberacion_Avance", 0) or 0), "Inicial + avance", "Continuidad técnica controlada", "Medio", "#F59E0B"),
        ("Escenario Cierre", total, "Liberación total del hito", "Ejecución sin interrupción", "Bajo", "#16A34A"),
    ]
    st.markdown("#### Escenarios de liberación de fondos")
    cols = st.columns(3)
    for col, (title, amount, scope, impact, risk, color) in zip(cols, scenarios):
        pct = amount / total if total else 0
        with col:
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-top:4px solid {color};border-radius:12px;padding:16px 17px;box-shadow:0 14px 28px rgba(15,23,42,.06);min-height:178px;">
                  <div style="font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#475569;">{html.escape(title)}</div>
                  <div style="font-size:25px;font-weight:900;color:#0B2D42;margin-top:10px;">{format_clp(amount)}</div>
                  <div style="font-size:13px;color:#64748B;margin-top:6px;">{format_pct(pct)} del total del hito · {html.escape(scope)}</div>
                  <div style="font-size:13px;color:#334155;line-height:1.45;margin-top:12px;"><b>Impacto:</b> {html.escape(impact)}</div>
                  <div style="display:inline-flex;margin-top:12px;border-radius:999px;padding:5px 9px;background:{color}1A;color:{color};font-size:12px;font-weight:900;">Riesgo {html.escape(risk)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_period_reading(df: pd.DataFrame, hito_summary: pd.DataFrame, metrics: dict[str, object]) -> None:
    concentration = hito_summary.sort_values("Monto_CLP", ascending=False).head(2)
    concentration_txt = " y ".join(concentration["Hito"].astype(str).tolist()) if not concentration.empty else "-"
    st.markdown("#### Lectura ejecutiva del período")
    text = (
        f"El cronograma presenta un CAPEX restante de {format_clp(float(metrics['total_capex']))}, concentrado principalmente en {concentration_txt}. "
        f"El avance técnico ponderado alcanza {format_pct(float(metrics['technical_progress']))}, mientras que la liberación financiera estimada alcanza "
        f"{format_pct(float(metrics['financial_progress']))}, generando una brecha de continuidad operacional de {format_clp(float(metrics['breach']))}. "
        f"Se recomienda priorizar el escenario {html.escape(str(metrics['current_row'].get('Escenario recomendado', 'Base')))} del hito actual y asegurar fondos de avance "
        "para evitar desaceleración en ingeniería, fabricación e integración."
    )
    st.markdown(f"<div class='section-note'>{html.escape(text)}</div>", unsafe_allow_html=True)


def render_required_decisions(metrics: dict[str, object]) -> None:
    current = metrics["current_row"]
    decisions = [
        ("Decisión financiera inmediata", f"Aprobar {html.escape(str(current.get('Escenario recomendado', 'Base')))} por {format_clp(float(current.get('Total_Liberacion', 0) or 0))}.", "#0B2D42"),
        ("Decisión técnica pendiente", f"Confirmar dependencias y entregables del hito {html.escape(str(current.get('Hito', '-')))}.", "#0F766E"),
        ("Riesgo si no se libera financiamiento", "Desaceleración de continuidad operacional y mayor riesgo de integración tardía.", "#DC2626"),
    ]
    st.markdown("#### Decisiones requeridas")
    cols = st.columns(3)
    for col, (title, body, color) in zip(cols, decisions):
        with col:
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid {color};border-radius:12px;padding:15px 16px;box-shadow:0 12px 24px rgba(15,23,42,.05);min-height:132px;">
                  <div style="font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#64748B;">{html.escape(title)}</div>
                  <div style="font-size:14px;line-height:1.45;color:#0F172A;font-weight:700;margin-top:10px;">{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_hitos_timeline(hito_summary: pd.DataFrame, pmo_matrix: pd.DataFrame | None = None) -> go.Figure:
    timeline = pmo_matrix.copy() if pmo_matrix is not None else hito_summary.copy()
    if "_Inicio" not in timeline.columns:
        timeline["_Inicio"] = pd.to_datetime(timeline["Inicio"], dayfirst=True, errors="coerce")
    if "_Termino" not in timeline.columns:
        timeline["_Termino"] = pd.to_datetime(timeline["Termino"], dayfirst=True, errors="coerce")
    timeline = timeline.dropna(subset=["_Inicio", "_Termino"]).sort_values("Hito Orden")
    if timeline.empty:
        return go.Figure()
    status_colors = {"Ejecutado": "#16A34A", "En curso": "#0F766E", "Pendiente": "#94A3B8"}
    critical_outline = {"Alta": "#DC2626", "Media": "#F59E0B", "Baja": "#CBD5E1"}
    y_stage = timeline["Etapa del hito"] if "Etapa del hito" in timeline.columns else ["Avance"] * len(timeline)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timeline["_Inicio"],
            y=y_stage,
            mode="markers+text",
            marker=dict(
                size=24,
                color=timeline["Estado"].map(status_colors).fillna("#94A3B8") if "Estado" in timeline.columns else "#0B2D42",
                symbol="circle",
                line=dict(
                    color=timeline["Criticidad"].map(critical_outline).fillna("#FFFFFF") if "Criticidad" in timeline.columns else "#FFFFFF",
                    width=3,
                ),
            ),
            text=timeline["Hito"],
            textposition="top center",
            customdata=np.stack(
                [
                    timeline["Hito Ejecutivo"],
                    timeline["Inicio"],
                    timeline["Termino"],
                    timeline["Monto total"],
                    timeline["Liberación Inicial"],
                    timeline["Liberación Avance"],
                    timeline["Liberación Cierre"],
                    timeline.get("Criticidad", pd.Series(["-"] * len(timeline), index=timeline.index)),
                    timeline.get("Comentario ejecutivo", pd.Series(["Control PMO del hito."] * len(timeline), index=timeline.index)),
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Inicio: %{customdata[1]}<br>"
                "Término: %{customdata[2]}<br>"
                "Monto restante: %{customdata[3]}<br>"
                "Inicial: %{customdata[4]}<br>"
                "Avance: %{customdata[5]}<br>"
                "Cierre: %{customdata[6]}<br>"
                "Riesgo: %{customdata[7]}<br>"
                "Comentario PMO: %{customdata[8]}<extra></extra>"
            ),
            name="Hitos",
        )
    )
    for _, row in timeline.iterrows():
        fig.add_shape(
            type="line",
            x0=row["_Inicio"],
            x1=row["_Termino"],
            y0=row["Etapa del hito"] if "Etapa del hito" in row.index else "Avance",
            y1=row["Etapa del hito"] if "Etapa del hito" in row.index else "Avance",
            xref="x",
            yref="y",
            line=dict(color=status_colors.get(str(row.get("Estado", "")), "#94A3B8"), width=9),
            opacity=0.35,
        )
    fig.update_layout(
        title="Timeline ejecutivo H1 → H8 por etapa de liberación",
        height=360,
        margin=dict(l=10, r=18, t=58, b=26),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis_title=None,
        yaxis=dict(title=None, categoryorder="array", categoryarray=["Cierre", "Avance", "Liberación inicial"]),
        hoverlabel=dict(bgcolor="#0B2D42", font_color="#FFFFFF"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,.18)", tickformat="%d %b")
    return fig


def build_hitos_financial_charts(df: pd.DataFrame, hito_summary: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    capex_df = hito_summary.copy().sort_values("Hito Orden")
    capex_df["Monto MMCLP"] = capex_df["Monto_CLP"] / 1_000_000
    fig_capex = px.bar(
        capex_df,
        x="Hito",
        y="Monto MMCLP",
        color="Hito Ejecutivo",
        color_discrete_sequence=MILESTONE_COLORS,
        text=capex_df["Monto_CLP"].map(format_clp),
        title="Distribución CAPEX por hito",
    )
    fig_capex.update_layout(showlegend=False, xaxis_title=None, yaxis_title="MM CLP", margin=dict(l=10, r=10, t=58, b=20))

    progress_df = (
        df.groupby("Hito", as_index=False)
        .agg(Avance=("Avance Num", "mean"), Criticas=("Es crítica", "sum"))
        .merge(hito_summary[["Hito", "Hito Corto", "Hito Orden"]], on="Hito", how="left")
        .sort_values("Hito Orden")
    )
    fig_progress = px.line(
        progress_df,
        x="Hito",
        y="Avance",
        markers=True,
        text=progress_df["Avance"].map(format_pct),
        title="Avance técnico por hito",
    )
    fig_progress.update_traces(line=dict(color="#0F766E", width=3), marker=dict(size=10, color="#0B2D42"))
    fig_progress.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1], xaxis_title=None, yaxis_title="Avance", margin=dict(l=10, r=10, t=58, b=20))
    return fig_capex, fig_progress


def hito_relevant_info(df: pd.DataFrame) -> dict[str, str]:
    info = {}
    for hito, group in df.groupby("Hito Ejecutivo"):
        critical = int(group["Es crítica"].sum())
        enabling = int(group["Es habilitante"].sum())
        top = group.sort_values("Monto CLP Num", ascending=False).head(1)
        top_txt = top.iloc[0]["Categoría/Línea"] if not top.empty else "Sin partida dominante"
        info[hito] = f"{critical} críticas · {enabling} habilitantes · foco: {top_txt}"
    return info


def render_hitos_table(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> None:
    table = build_pmo_hito_matrix(df, hito_summary, pmo_source).copy()
    table = table[
        [
            "Hito",
            "Hito Ejecutivo",
            "Etapa del hito",
            "Estado",
            "Criticidad",
            "Inicio",
            "Termino",
            "Duracion_habil",
            "Monto total",
            "% total",
            "Liberación Inicial",
            "Liberación Avance",
            "Liberación Cierre",
            "Total Liberación",
            "Monto crítico próximo",
            "Escenario recomendado",
            "Decisión requerida",
            "Condición de Liberación",
            "Comentario ejecutivo",
        ]
    ].rename(
        columns={
            "Termino": "Término",
            "Duracion_habil": "Duración hábil",
            "Monto total": "Monto restante CLP",
            "% total": "% Total",
            "Partidas": "Actividades relacionadas",
        }
    )
    styler = (
        table.style
        .set_table_styles(
            [
                {"selector": "th", "props": [("background", "#0B2D42"), ("color", "white"), ("font-weight", "800"), ("font-size", "12px"), ("border", "0")]},
                {"selector": "td", "props": [("border-bottom", "1px solid #E2E8F0"), ("font-size", "12px"), ("padding", "9px 10px")]},
                {"selector": "tbody tr:nth-child(even)", "props": [("background", "#F8FBFC")]},
            ]
        )
        .set_properties(subset=["Hito", "Hito Ejecutivo"], **{"font-weight": "800", "color": "#0B2D42"})
        .set_properties(subset=["Monto restante CLP", "Liberación Inicial", "Liberación Avance", "Liberación Cierre", "Total Liberación"], **{"font-variant-numeric": "tabular-nums", "font-weight": "700"})
        .set_properties(subset=["Criticidad", "Escenario recomendado"], **{"font-weight": "800"})
    )
    st.dataframe(styler, hide_index=True, use_container_width=True, height=min(520, 82 + 42 * len(table)))


def render_hito_span_gantt(df: pd.DataFrame) -> None:
    scheduled = df[df["Inicio"].notna() & df["Termino"].notna()].copy()
    if scheduled.empty:
        return

    hito_ranges = (
        scheduled.groupby(["Hito", "Hito Ejecutivo", "Hito Corto"], as_index=False)
        .agg(
            Inicio_hito=("Inicio", "min"),
            Termino_hito=("Termino", "max"),
            Actividades=("ID", "count"),
            Monto=("Monto CLP Num", "sum"),
        )
        .sort_values("Hito")
    )
    if hito_ranges.empty:
        return

    hito_ranges["Orden"] = pd.to_numeric(hito_ranges["Hito"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    hito_ranges = hito_ranges.sort_values(["Orden", "Inicio_hito"])
    horizon_start = hito_ranges["Inicio_hito"].min()
    horizon_end = hito_ranges["Termino_hito"].max()
    horizon_days = max((horizon_end - horizon_start).days, 1)
    today = pd.Timestamp("today").normalize()

    def pct(date_value: pd.Timestamp) -> float:
        return max(0.0, min(100.0, ((date_value - horizon_start).days / horizon_days) * 100.0))

    max_amount = max(float(hito_ranges["Monto"].max() or 0), 1.0)
    critical_hitos = {"H1", "H4", "H8"}
    gantt_colors = {
        "H1": "#0B2D42",
        "H2": "#2F80ED",
        "H3": "#1D4ED8",
        "H4": "#DC2626",
        "H5": "#64748B",
        "H6": "#0F766E",
        "H7": "#7C3AED",
        "H8": "#DC2626",
    }
    rows = []
    for _, hito in hito_ranges.iterrows():
        code = str(hito["Hito"])
        start = pd.Timestamp(hito["Inicio_hito"])
        end = pd.Timestamp(hito["Termino_hito"])
        left = pct(start)
        width = max(2.5, pct(end) - left)
        amount = float(hito["Monto"] or 0)
        amount_width = min(max(amount / max_amount * 100, 8), 100)
        color = gantt_colors.get(code, "#0F766E")
        rows.append(
            f"""
            <div class="span-row {'critical' if code in critical_hitos else ''}">
              <div class="span-label">
                <div class="span-code" style="background:{color};">{html.escape(code)}</div>
                <div>
                  <div class="span-name">{html.escape(str(hito["Hito Corto"]))}</div>
                  <div class="span-meta">{format_date(start)} a {format_date(end)} · {business_days(start, end)} días hábiles</div>
                </div>
              </div>
              <div class="span-track">
                <div class="span-bar" style="left:{left:.2f}%;width:{width:.2f}%;--bar:{color};">
                  <span>{html.escape(code)} · {format_clp(amount)}</span>
                </div>
              </div>
              <div class="span-side">
                <b>{format_clp(amount)}</b>
                <span>{int(hito["Actividades"])} actividades</span>
                <div class="amount-track"><i style="width:{amount_width:.0f}%;background:{color};"></i></div>
              </div>
            </div>
            """
        )

    cut_dates = [
        ("30 mayo", pd.Timestamp("2026-05-30")),
        ("30 junio", pd.Timestamp("2026-06-30")),
        ("30 julio", pd.Timestamp("2026-07-30")),
        ("30 septiembre", pd.Timestamp("2026-09-30")),
    ]
    cut_marks = "".join(
        f"<div class='cut-mark' style='left:{pct(date):.2f}%;'><span>{html.escape(label)}</span></div>"
        for label, date in cut_dates
        if horizon_start <= date <= horizon_end
    )
    month_labels = []
    cursor = pd.Timestamp(horizon_start.year, horizon_start.month, 1)
    while cursor <= horizon_end:
        month_labels.append((cursor.strftime("%b %Y"), pct(cursor)))
        cursor = cursor + pd.DateOffset(months=1)
    months_html = "".join(
        f"<span style='left:{left:.2f}%;'>{html.escape(label.title())}</span>" for label, left in month_labels
    )
    total_amount = float(hito_ranges["Monto"].sum() or 0)
    launch_rows = hito_ranges[hito_ranges["Hito"].astype(str).eq("H8")]
    launch_text = format_date(launch_rows["Termino_hito"].max()) if not launch_rows.empty else format_date(horizon_end)
    today_left = pct(today)

    html_doc = f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#0B1633;overflow-x:hidden;}}
    .span-shell{{background:linear-gradient(180deg,#FFFFFF 0%,#F8FBFD 100%);border:1px solid #DCE6EF;border-radius:14px;padding:18px 20px;box-shadow:0 14px 32px rgba(15,23,42,.06);overflow:hidden;}}
    .span-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:16px;}}
    .span-title{{font-size:21px;line-height:1.1;font-weight:950;color:#23457A;}}
    .span-sub{{font-size:12px;color:#64748B;line-height:1.38;margin-top:6px;max-width:820px;}}
    .span-kpis{{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;}}
    .span-kpi{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:999px;padding:7px 10px;font-size:11px;font-weight:900;color:#334155;white-space:nowrap;}}
    .span-axis{{position:relative;margin-left:260px;margin-right:128px;height:32px;border-bottom:1px solid #E2E8F0;}}
    .span-axis span{{position:absolute;top:4px;transform:translateX(-2px);font-size:10px;font-weight:850;color:#64748B;text-transform:uppercase;white-space:nowrap;}}
    .span-body{{position:relative;display:grid;gap:9px;padding-top:8px;}}
    .span-overlay{{position:absolute;left:260px;right:128px;top:0;bottom:0;pointer-events:none;}}
    .today-span{{position:absolute;top:0;bottom:0;left:{today_left:.2f}%;width:2px;background:#EF4444;box-shadow:0 0 0 5px rgba(239,68,68,.09);z-index:5;}}
    .today-span span{{position:absolute;top:-25px;left:50%;transform:translateX(-50%);background:#EF4444;color:#FFFFFF;border-radius:999px;padding:4px 9px;font-size:10px;font-weight:950;}}
    .cut-mark{{position:absolute;top:0;bottom:0;width:1px;background:rgba(15,23,42,.12);}}
    .cut-mark span{{position:absolute;bottom:-19px;left:5px;font-size:9px;color:#64748B;font-weight:800;white-space:nowrap;}}
    .span-row{{display:grid;grid-template-columns:250px minmax(260px,1fr) 118px;gap:10px;align-items:center;min-height:58px;position:relative;z-index:10;}}
    .span-label{{display:flex;align-items:center;gap:10px;min-width:0;}}
    .span-code{{width:38px;height:38px;border-radius:12px;color:#FFFFFF;font-size:14px;font-weight:950;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 18px rgba(15,23,42,.16);flex:0 0 auto;}}
    .span-row.critical .span-code{{box-shadow:0 0 0 8px rgba(220,38,38,.10),0 12px 24px rgba(220,38,38,.22);}}
    .span-name{{font-size:12px;font-weight:950;color:#0B1633;line-height:1.14;}}
    .span-meta{{font-size:10px;color:#64748B;margin-top:3px;font-weight:750;}}
    .span-track{{height:42px;border-radius:12px;background:linear-gradient(90deg,rgba(226,232,240,.60),rgba(248,250,252,.35));position:relative;overflow:hidden;border:1px solid #EEF3F7;}}
    .span-bar{{position:absolute;top:8px;height:24px;border-radius:999px;background:linear-gradient(90deg,var(--bar),color-mix(in srgb,var(--bar) 72%,#FFFFFF));box-shadow:0 10px 22px color-mix(in srgb,var(--bar) 22%,transparent);display:flex;align-items:center;padding:0 10px;min-width:34px;}}
    .span-row.critical .span-bar{{height:30px;top:5px;box-shadow:0 0 0 5px rgba(220,38,38,.08),0 14px 26px rgba(220,38,38,.20);}}
    .span-bar span{{color:#FFFFFF;font-size:10px;font-weight:950;white-space:nowrap;text-shadow:0 1px 2px rgba(15,23,42,.24);}}
    .span-side{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:11px;padding:8px 9px;box-shadow:0 8px 18px rgba(15,23,42,.04);}}
    .span-side b{{display:block;font-size:11px;color:#0B1633;white-space:nowrap;}}
    .span-side span{{display:block;font-size:9px;color:#64748B;margin-top:3px;font-weight:800;}}
    .amount-track{{height:5px;background:#E2E8F0;border-radius:999px;overflow:hidden;margin-top:6px;}}
    .amount-track i{{display:block;height:100%;border-radius:999px;}}
    @media(max-width:980px){{.span-axis{{margin-left:0;margin-right:0;}}.span-row{{grid-template-columns:1fr;}}.span-overlay{{display:none;}}.span-side{{max-width:220px;}}}}
    </style>
    <div class="span-shell">
      <div class="span-head">
        <div>
          <div class="span-title">Gantt ejecutivo por rango real de hitos</div>
          <div class="span-sub">Inicio calculado con la acción más antigua del hito y término con la fecha de acción más lejana del Cronograma Integrado. Permite ver la ventana real de ejecución antes de los cortes de liberación PMO.</div>
        </div>
        <div class="span-kpis">
          <div class="span-kpi">Horizonte {format_date(horizon_start)} · {format_date(horizon_end)}</div>
          <div class="span-kpi">CAPEX {format_clp(total_amount)}</div>
          <div class="span-kpi">Puesta en marcha {launch_text}</div>
        </div>
      </div>
      <div class="span-axis">{months_html}</div>
      <div class="span-body">
        <div class="span-overlay">{cut_marks}<div class="today-span"><span>HOY</span></div></div>
        {''.join(rows)}
      </div>
    </div>
    """
    components.html(html_doc, height=650, scrolling=True)


def render_board_kpis(df: pd.DataFrame) -> None:
    scheduled = df[df["Inicio"].notna()].copy()
    if scheduled.empty:
        return

    cuts = [
        ("Liberación 1", None, pd.Timestamp("2026-05-30")),
        ("Liberación 2", pd.Timestamp("2026-05-30"), pd.Timestamp("2026-06-30")),
        ("Liberación 3", pd.Timestamp("2026-06-30"), pd.Timestamp("2026-07-30")),
        ("Liberación 4", pd.Timestamp("2026-07-30"), pd.Timestamp("2026-09-30")),
    ]
    release_totals: list[tuple[str, float]] = []
    release_windows: dict[str, pd.DataFrame] = {}
    for name, start_cut, end_cut in cuts:
        if start_cut is None:
            window = scheduled[scheduled["Inicio"].le(end_cut)]
        else:
            window = scheduled[scheduled["Inicio"].gt(start_cut) & scheduled["Inicio"].le(end_cut)]
        release_windows[name] = window.copy()
        release_totals.append((name, float(window["Monto CLP Num"].sum() or 0)))

    total_release = sum(amount for _, amount in release_totals)
    release_1 = release_totals[0][1] if release_totals else 0.0
    release_2_amount = release_totals[1][1] if len(release_totals) > 1 else 0.0
    critical_window = release_1 + release_2_amount

    def money_mm(value: float) -> str:
        return f"${value / 1_000_000:.1f} MM".replace(".", ",")

    release_2 = release_windows.get("Liberación 2", pd.DataFrame())
    weighted_progress = (
        float((scheduled["Monto CLP Num"] * scheduled["Avance Num"]).sum() / total_release)
        if total_release
        else 0.0
    )
    critical_pending = int((scheduled["Es crítica"] & (scheduled["Avance Num"] < 1)).sum())
    financial_pressure = critical_window / total_release if total_release else 0.0
    if critical_pending >= 10 or (weighted_progress > financial_pressure and critical_pending > 0):
        risk_value = "ALTO"
        risk_context = "Brecha entre avance técnico, hitos críticos y liberación financiera."
        risk_metric = f"{critical_pending} partidas críticas pendientes"
        risk_color = "#7F1D1D"
    elif critical_pending > 0:
        risk_value = "MEDIO"
        risk_context = "Continuidad condicionada a liberar fondos de los próximos cortes."
        risk_metric = f"Avance ponderado {format_pct(weighted_progress)}"
        risk_color = "#B7791F"
    else:
        risk_value = "BAJO"
        risk_context = "Liberaciones alineadas con la continuidad técnica del periodo."
        risk_metric = "Sin bloqueos críticos activos"
        risk_color = "#0F766E"

    launch_rows = scheduled[
        scheduled["Hito"].astype(str).eq("H7")
        | scheduled["Hito Ejecutivo"].str.contains("puesta en marcha|comisionamiento", case=False, na=False)
    ]
    launch_date = launch_rows["Termino"].max() if not launch_rows.empty else scheduled["Termino"].dropna().max()
    launch_text = format_date(launch_date) if pd.notna(launch_date) else "Por definir"
    days_left = max(0, int((pd.Timestamp(launch_date).normalize() - pd.Timestamp("today").normalize()).days)) if pd.notna(launch_date) else 0
    risk_display = risk_value.title()
    risk_phrase = "Brecha controlable" if risk_value == "MEDIO" else "Atención inmediata" if risk_value == "ALTO" else "Continuidad controlada"
    recommendation = "Priorizar liberación inicial y asegurar fondos de avance para sostener ruta crítica del cronograma."
    decision = "Asegurar liberación inicial y fondos de avance"

    html_doc = f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#0B1633;overflow-x:hidden;}}
    .exec-summary{{background:#FFFFFF;border:1px solid #DCE6EF;border-radius:18px;box-shadow:0 8px 24px rgba(15,23,42,.06);overflow:hidden;margin:0 0 18px 0;}}
    .exec-title{{font-size:12px;font-weight:950;letter-spacing:.08em;text-transform:uppercase;color:#0F766E;padding:18px 28px 0;}}
    .exec-top{{display:grid;grid-template-columns:1.08fr .88fr 1fr;gap:0;padding:16px 28px 22px;align-items:center;}}
    .exec-block{{display:grid;grid-template-columns:66px minmax(0,1fr);gap:19px;align-items:center;min-height:104px;padding:0 28px;}}
    .exec-block:first-child{{padding-left:0;}}.exec-block:not(:last-child){{border-right:1px solid #E2E8F0;}}
    .exec-icon{{width:64px;height:64px;border-radius:999px;background:linear-gradient(145deg,#F9FBFD,#EEF2F5);display:flex;align-items:center;justify-content:center;color:#0B7780;font-size:30px;font-weight:300;box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 10px 24px rgba(15,23,42,.045);}}
    .exec-label{{font-size:12px;font-weight:950;text-transform:uppercase;letter-spacing:.04em;color:#0F766E;margin-bottom:8px;}}
    .exec-main{{font-size:21px;line-height:1.22;font-weight:950;color:#08152F;letter-spacing:-.02em;}}
    .exec-money{{font-size:37px;line-height:1;font-weight:950;color:#08152F;letter-spacing:-.05em;}}
    .exec-copy{{font-size:13px;line-height:1.38;color:#64748B;font-weight:700;margin-top:8px;max-width:360px;}}
    .exec-pill{{display:inline-flex;margin-top:10px;border-radius:999px;background:#EAF2F8;color:#23457A;padding:6px 12px;font-size:11px;font-weight:950;}}
    .exec-pill.warn{{background:#FBF0D9;color:#B7791F;}}
    @media(max-width:1050px){{.exec-top{{grid-template-columns:1fr;}}.exec-block{{border-right:0!important;border-bottom:1px solid #E2E8F0;padding:16px 0;}}.exec-block:last-child{{border-bottom:0;}}.exec-money{{font-size:34px;}}}}
    </style>
    <div class="exec-summary">
      <div class="exec-title">Resumen ejecutivo</div>
      <div class="exec-top">
        <div class="exec-block">
          <div class="exec-icon">↗</div>
          <div>
            <div class="exec-label">Estado del proyecto</div>
            <div class="exec-main">Piloto en integración técnica y continuidad operacional</div>
            <div class="exec-copy">Avance técnico activo y cronograma en seguimiento.</div>
          </div>
        </div>
        <div class="exec-block">
          <div class="exec-icon">$</div>
          <div>
            <div class="exec-label">CAPEX requerido</div>
            <div class="exec-money">{html.escape(money_mm(total_release))}</div>
            <div class="exec-copy">Para completar integración, validación y puesta en marcha.</div>
            <div class="exec-pill">Capital pendiente</div>
          </div>
        </div>
        <div class="exec-block">
          <div class="exec-icon">◎</div>
          <div>
            <div class="exec-label">Decisión requerida</div>
            <div class="exec-main">{html.escape(decision)}</div>
            <div class="exec-copy">Para evitar desaceleración en ingeniería, integración y puesta en marcha.</div>
            <div class="exec-pill warn">Decisión financiera clave</div>
          </div>
        </div>
      </div>
    </div>
    """
    components.html(html_doc, height=218, scrolling=False)


def render_release_cutoff_intelligence(df: pd.DataFrame) -> None:
    hito_colors = {
        "H1": "#0B2D42",
        "H2": "#2F80ED",
        "H3": "#1D4ED8",
        "H4": "#DC2626",
        "H5": "#64748B",
        "H6": "#0F766E",
        "H7": "#7C3AED",
        "H8": "#DC2626",
    }
    cuts = [
        ("Liberación 1", "hasta 30-05-2026", None, pd.Timestamp("2026-05-30"), "#0F766E", "Activación inicial"),
        ("Liberación 2", "31-05 a 30-06-2026", pd.Timestamp("2026-05-30"), pd.Timestamp("2026-06-30"), "#2563EB", "Continuidad técnica"),
        ("Liberación 3", "01-07 a 30-07-2026", pd.Timestamp("2026-06-30"), pd.Timestamp("2026-07-30"), "#B7791F", "Integración operacional"),
        ("Liberación 4", "31-07 a 30-09-2026", pd.Timestamp("2026-07-30"), pd.Timestamp("2026-09-30"), "#7F1D1D", "Cierre del horizonte"),
    ]
    panels: list[dict[str, object]] = []
    max_amount = 1.0
    scheduled = df[df["Inicio"].notna()].copy()
    for title, date_label, start_cut, end_cut, color, thesis in cuts:
        if start_cut is None:
            window = scheduled[scheduled["Inicio"].le(end_cut)].copy()
        else:
            window = scheduled[scheduled["Inicio"].gt(start_cut) & scheduled["Inicio"].le(end_cut)].copy()
        if window.empty:
            detail = pd.DataFrame(columns=["Hito", "Hito Corto", "Categoría/Línea", "Partidas", "Monto"])
            total = 0.0
        else:
            detail = (
                window.groupby(["Hito", "Hito Corto", "Categoría/Línea"], as_index=False)
                .agg(
                    Partidas=("ID", "count"),
                    Monto=("Monto CLP Num", "sum"),
                    AvanceFisico=("Avance Num", "mean"),
                    Criticas=("Es crítica", "sum"),
                    Habilitantes=("Es habilitante", "sum"),
                    Inicio=("Inicio", "min"),
                    Termino=("Termino", "max"),
                )
                .sort_values(["Monto", "Hito"], ascending=[False, True])
            )
            total = float(detail["Monto"].sum() or 0)
            max_amount = max(max_amount, float(detail["Monto"].max() or 0))
        panels.append({"title": title, "date": date_label, "color": color, "thesis": thesis, "detail": detail, "total": total, "hitos": int(detail["Hito"].nunique()) if not detail.empty else 0, "partidas": int(detail["Partidas"].sum()) if not detail.empty else 0})

    max_total = max(max(float(panel["total"]) for panel in panels), 1.0)

    def money_mm(value: float) -> str:
        return f"${value / 1_000_000:.1f}MM".replace(".", ",")

    def stage_card(panel: dict[str, object], idx: int) -> str:
        color = str(panel["color"])
        width = min(max(float(panel["total"]) / max_total * 100, 3), 100)
        return f"""
        <button class="release-stage {'active' if idx == 0 else ''}" data-stage="{idx}" style="--accent:{color};" type="button">
          <div class="stage-date">{html.escape(str(panel["date"]))}</div>
          <div class="stage-title">{html.escape(str(panel["thesis"]))}</div>
          <div class="stage-total">{money_mm(float(panel["total"]))}</div>
          <div class="stage-detail">{int(panel["hitos"])} hitos · {int(panel["partidas"])} partidas</div>
          <div class="stage-rule"></div>
          <div class="stage-meta">
            <span><i class="meta-icon">◎</i><small>Hitos activos</small></span>
            <span><i class="meta-icon">▤</i><small>Partidas</small></span>
          </div>
          <div class="stage-track"><i style="width:{width:.0f}%;"></i></div>
          <div class="stage-action">Ver requerimiento <b>→</b></div>
        </button>
        """

    release_nodes = "".join(
        f"""
        <div class="release-node-wrap" style="--accent:{html.escape(str(panel['color']))};">
          <div class="release-node">{idx + 1}</div>
        </div>
        """
        for idx, panel in enumerate(panels)
    )

    def detail_rows(panel: dict[str, object]) -> str:
        detail = panel["detail"]
        color = str(panel["color"])
        if not isinstance(detail, pd.DataFrame) or detail.empty:
            return '<div class="release-empty">Sin partidas activas en este corte.</div>'
        rows = []
        panel_total = max(float(panel["total"] or 0), 1)
        critical_count = int((detail.get("Criticas", pd.Series(dtype=float)).fillna(0) > 0).sum())
        habilitating_count = int((detail.get("Habilitantes", pd.Series(dtype=float)).fillna(0) > 0).sum())
        for _, row in detail.iterrows():
            hito_code = str(row["Hito"])
            hito_color = hito_colors.get(hito_code, "#0B2D42")
            amount = float(row["Monto"] or 0)
            physical = float(row.get("AvanceFisico", 0) or 0)
            financial = min(max(amount / panel_total, 0), 1)
            risk = "Crítico" if int(row.get("Criticas", 0) or 0) else "Alto" if int(row.get("Habilitantes", 0) or 0) else "Medio" if amount >= max_amount * 0.35 else "Bajo"
            state = "Riesgo operacional" if risk == "Crítico" else "En ejecución" if physical > 0 else "Esperando liberación"
            dependency = "Depende de liberación PMO" if physical == 0 else "En ruta de ejecución"
            impact = (
                "Bloquea puesta en marcha"
                if str(row["Hito"]) == "H8" or risk == "Crítico"
                else "Condiciona integración eléctrica"
                if str(row["Hito"]) == "H7"
                else "Habilita montaje rotor"
                if str(row["Hito"]) in {"H4", "H6"}
                else "Reduce riesgo de atraso operacional"
            )
            risk_class = {"Bajo": "low", "Medio": "medium", "Alto": "high", "Crítico": "critical"}.get(risk, "medium")
            rows.append(
                f"""
                <div class="release-row">
                  <div class="release-key">
                    <div class="release-hito" style="background:{hito_color};">{html.escape(hito_code)}</div>
                    <span>{html.escape(str(row["Hito Corto"]))}</span>
                  </div>
                  <div class="release-copy">
                    <b>{html.escape(str(row["Categoría/Línea"]))}</b>
                    <span>{int(row["Partidas"])} partidas · {format_date(row.get("Inicio"))} a {format_date(row.get("Termino"))}</span>
                  </div>
                  <div class="release-metrics">
                    <div class="mini-bar"><span>Físico {format_pct(physical)}</span><i><b style="width:{physical * 100:.0f}%;"></b></i></div>
                    <div class="mini-bar"><span>Financiero {format_pct(financial)}</span><i><b style="width:{financial * 100:.0f}%;"></b></i></div>
                  </div>
                  <div class="release-pmo">
                    <span class="risk {risk_class}">{html.escape(risk)}</span>
                    <span class="state">{html.escape(state)}</span>
                  </div>
                  <div class="release-impact"><b>{html.escape(impact)}</b><span>{html.escape(dependency)}</span></div>
                  <div class="release-amount">{format_clp(amount)}</div>
                </div>
                """
            )
        return f"""
        <div class="release-control-summary">
          <div><small>Monto del corte</small><b>{money_mm(float(panel["total"]))}</b></div>
          <div><small>Frentes PMO</small><b>{len(detail)}</b></div>
          <div><small>Riesgo crítico</small><b>{critical_count}</b></div>
          <div><small>Habilitantes</small><b>{habilitating_count}</b></div>
        </div>
        <div class="release-table-head">
          <span>Hito</span><span>Componente técnico</span><span>Avance</span><span>Riesgo / estado</span><span>Impacto operacional</span><span>Monto</span>
        </div>
        {''.join(rows)}
        """

    detail_panels = "".join(
        f"""
        <div class="release-panel {'active expanded' if idx == 0 else ''}" data-panel="{idx}" style="--panel-color:{html.escape(str(panel['color']))};">
          <button class="panel-head" type="button">
            <div><b>Control operacional por hito</b><small>{html.escape(str(panel["date"]))} · {html.escape(str(panel["thesis"]))}</small></div>
            <span>{money_mm(float(panel["total"]))} · {int(panel["partidas"])} partidas <i>⌄</i></span>
          </button>
          <div class="release-list">{detail_rows(panel)}</div>
        </div>
        """
        for idx, panel in enumerate(panels)
    )

    html_doc = f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#0B1633;overflow-x:hidden;}}
    .release-shell{{background:#F8FAFC;border:1px solid #B8C9D8;border-top:2px solid #8FA8BB;border-radius:18px;padding:24px 28px 22px;box-shadow:0 8px 24px rgba(15,23,42,.06),inset 0 1px 0 rgba(255,255,255,.86);overflow:hidden;}}
    .release-head{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:34px;}}
    .release-title{{font-size:20px;font-weight:950;color:#23457A;line-height:1.1;}}
    .release-sub{{font-size:12px;color:#64748B;line-height:1.38;margin-top:6px;max-width:780px;}}
    .release-badge{{border:1px solid #E2E8F0;background:#FFFFFF;border-radius:999px;padding:12px 21px;color:#0B1B3A;font-size:14px;font-weight:900;white-space:nowrap;box-shadow:0 8px 18px rgba(15,23,42,.035);}}
    .release-flow{{position:relative;margin:0 0 15px 0;padding-top:50px;}}
    .release-line{{position:absolute;left:4px;right:4px;top:24px;height:1px;background:#CBD5E1;}}
    .release-line::before,.release-line::after{{content:"";position:absolute;top:50%;width:8px;height:8px;border-radius:999px;background:#CBD5E1;transform:translateY(-50%);}}
    .release-line::before{{left:-1px;}}.release-line::after{{right:-1px;}}
    .release-nodes{{position:absolute;left:0;right:0;top:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));align-items:center;z-index:5;}}
    .release-node-wrap{{display:flex;justify-content:center;position:relative;}}
    .release-node-wrap::after{{content:"";position:absolute;top:43px;width:1px;height:29px;background:#E2E8F0;}}
    .release-node{{width:44px;height:44px;border-radius:999px;background:var(--accent);color:#FFFFFF;font-size:19px;font-weight:950;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 5px #FFFFFF,0 6px 16px rgba(15,23,42,.10);}}
    .stage-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:34px;margin-bottom:12px;}}
    .release-stage{{appearance:none;text-align:left;width:100%;background:#FFFFFF;border:1px solid #E2E8F0;border-top:4px solid var(--accent);border-radius:14px;padding:20px 22px;box-shadow:0 8px 20px rgba(15,23,42,.04);cursor:pointer;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease;position:relative;min-height:238px;}}
    .release-stage:hover{{transform:translateY(-2px);box-shadow:0 14px 24px rgba(15,23,42,.065);}}
    .release-stage.active{{border-color:#CBD5E1;box-shadow:0 0 0 3px rgba(11,27,58,.045),0 14px 26px rgba(15,23,42,.06);}}
    .stage-date{{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:7px 12px;background:#F1F5F9;color:#475569;font-size:12px;font-weight:900;white-space:nowrap;text-transform:uppercase;}}
    .stage-title{{font-size:19px;font-weight:950;color:#0B1B3A;line-height:1.08;margin-top:17px;}}
    .stage-total{{font-size:27px;font-weight:950;color:#0B1633;margin-top:10px;letter-spacing:-.035em;line-height:1;}}
    .stage-detail{{font-size:13px;color:#475569;font-weight:850;margin-top:10px;}}
    .stage-rule{{height:1px;background:#E2E8F0;margin:17px 0 13px 0;}}
    .stage-meta{{display:grid;grid-template-columns:1fr 1fr;gap:0;margin:0 0 15px 0;}}
    .stage-meta span{{display:flex;align-items:center;gap:7px;min-height:28px;color:#475569;}}
    .stage-meta span:first-child{{border-right:1px solid #DCE6EF;}}
    .stage-meta small{{font-size:11px;color:#475569;font-weight:850;}}
    .meta-icon{{width:22px;height:22px;border-radius:999px;background:#F8FAFC;color:#475569;font-style:normal;font-size:14px;display:flex;align-items:center;justify-content:center;}}
    .stage-track{{height:6px;background:#E2E8F0;border-radius:999px;overflow:hidden;margin-top:2px;}}
    .stage-track i{{display:block;height:100%;background:var(--accent);border-radius:999px;}}
    .stage-action{{font-size:13px;font-weight:950;color:#0B1B3A;margin-top:17px;letter-spacing:.01em;}}
    .stage-action b{{font-size:14px;margin-left:4px;}}
    .release-detail-stack{{display:grid;gap:12px;}}
    .release-panel{{display:none;background:#FFFFFF;border:1px solid color-mix(in srgb,var(--panel-color) 34%,#C9D8E6);border-radius:12px;overflow:hidden;box-shadow:0 10px 22px rgba(15,23,42,.04);}}
    .release-panel.active{{display:block;}}
    .panel-head{{appearance:none;width:100%;border:0;border-left:5px solid var(--panel-color);padding:14px 15px;display:flex;justify-content:space-between;gap:10px;align-items:center;background:linear-gradient(180deg,color-mix(in srgb,var(--panel-color) 10%,#FFFFFF),color-mix(in srgb,var(--panel-color) 16%,#FFFFFF));cursor:pointer;text-align:left;}}
    .panel-head:hover{{background:color-mix(in srgb,var(--panel-color) 21%,#FFFFFF);}}
    .panel-head b{{display:block;font-size:14px;color:#0B1B3A;}}.panel-head small{{display:block;font-size:11px;color:#64748B;margin-top:3px;font-weight:750;}}.panel-head span{{font-size:12px;color:#0B1633;font-weight:950;white-space:nowrap;}}.panel-head i{{font-style:normal;font-size:16px;margin-left:4px;color:#475569;display:inline-block;transition:transform .16s ease;}}
    .release-panel.expanded .panel-head{{border-bottom:1px solid color-mix(in srgb,var(--panel-color) 34%,#C9D8E6);}}
    .release-panel.expanded .panel-head i{{transform:rotate(180deg);}}
    .release-list{{padding:12px;display:none;gap:8px;align-content:start;height:560px;overflow-y:scroll;overflow-x:auto;background:#FAFCFE;border-top:1px solid color-mix(in srgb,var(--panel-color) 34%,#C9D8E6);cursor:grab;user-select:none;scrollbar-color:color-mix(in srgb,var(--panel-color) 48%,#94A3B8) #E8EEF5;scrollbar-width:thin;}}
    .release-panel.expanded .release-list{{display:grid;}}
    .release-list.is-dragging{{cursor:grabbing;}}
    .release-list::-webkit-scrollbar{{width:10px;height:10px;}}
    .release-list::-webkit-scrollbar-track{{background:#E8EEF5;border-radius:999px;}}
    .release-list::-webkit-scrollbar-thumb{{background:color-mix(in srgb,var(--panel-color) 48%,#94A3B8);border-radius:999px;border:2px solid #E8EEF5;}}
    .release-control-summary{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:4px;}}
    .release-control-summary div{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:11px;padding:10px 11px;box-shadow:0 8px 18px rgba(15,23,42,.035);}}
    .release-control-summary small{{display:block;font-size:9px;color:#64748B;font-weight:900;text-transform:uppercase;letter-spacing:.04em;}}
    .release-control-summary b{{display:block;margin-top:5px;font-size:15px;color:#0B1633;font-weight:950;}}
    .release-table-head{{display:grid;grid-template-columns:96px minmax(0,1.05fr) minmax(140px,.7fr) 122px minmax(170px,1fr) 96px;gap:10px;padding:8px 11px;background:#EEF4F8;border:1px solid #DCE6EF;border-radius:10px;color:#475569;font-size:9px;font-weight:950;text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0;z-index:2;}}
    .release-row{{display:grid;grid-template-columns:96px minmax(0,1.05fr) minmax(140px,.7fr) 122px minmax(170px,1fr) 96px;gap:10px;align-items:center;padding:12px;border:1px solid #E8EEF5;border-radius:14px;background:#FFFFFF;box-shadow:0 8px 18px rgba(15,23,42,.028);transition:transform .14s ease,box-shadow .14s ease,border-color .14s ease;}}
    .release-row:hover{{transform:translateY(-1px);border-color:#CBD5E1;box-shadow:0 12px 24px rgba(15,23,42,.055);}}
    .release-key{{display:flex;align-items:center;gap:8px;min-width:0;}}
    .release-key span{{font-size:9px;color:#64748B;font-weight:850;line-height:1.1;}}
    .release-hito{{width:34px;height:32px;border-radius:10px;background:#0B1B3A;color:#FFFFFF;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:950;box-shadow:0 8px 16px rgba(15,23,42,.14);flex:0 0 auto;}}
    .release-copy b{{display:block;font-size:11px;color:#0B1633;line-height:1.15;}}.release-copy span{{display:block;font-size:9px;color:#64748B;margin-top:4px;line-height:1.15;font-weight:750;}}
    .release-metrics{{display:grid;gap:5px;}}
    .mini-bar span{{display:flex;justify-content:space-between;font-size:9px;color:#475569;font-weight:850;margin-bottom:3px;}}
    .mini-bar i{{display:block;height:6px;background:#E2E8F0;border-radius:999px;overflow:hidden;}}
    .mini-bar b{{display:block;height:100%;background:linear-gradient(90deg,#0B1B3A,#0F766E);border-radius:999px;}}
    .release-pmo{{display:flex;gap:5px;flex-wrap:wrap;}}
    .risk,.state{{display:inline-flex;border-radius:999px;padding:5px 7px;font-size:9px;font-weight:900;background:#F1F5F9;color:#475569;}}
    .risk.low{{color:#0F766E;background:#EAF6F2;}}.risk.medium{{color:#8A5A16;background:#FBF4E7;}}.risk.high{{color:#7F1D1D;background:#F8EAEA;}}.risk.critical{{color:#7F1D1D;background:#F4DCDC;}}
    .release-impact{{font-size:10px;color:#475569;font-weight:800;line-height:1.2;}}.release-impact b{{display:block;color:#0B1633;font-size:10px;}}.release-impact span{{display:block;margin-top:3px;color:#64748B;font-size:9px;}}
    .release-amount{{font-size:11px;font-weight:950;color:#0B1633;text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;}}
    .release-empty{{font-size:12px;color:#64748B;padding:14px;}}
    .release-legend{{display:flex;gap:26px;justify-content:center;align-items:center;color:#64748B;font-size:12px;font-weight:850;margin:14px auto 18px;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:999px;padding:9px 16px;width:max-content;max-width:100%;}}
    .release-legend span{{display:flex;align-items:center;gap:8px;}}
    .legend-icon{{width:22px;height:22px;border-radius:999px;background:#F8FAFC;display:flex;align-items:center;justify-content:center;color:#475569;font-size:14px;}}
    .legend-line{{width:42px;height:6px;border:1px solid #94A3B8;border-radius:999px;}}
    @media(max-width:1180px){{.stage-grid{{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;}}.release-stage:not(:last-child)::after{{display:none;}}.release-nodes{{display:none;}}.release-line{{display:none;}}.release-flow{{padding-top:0;}}}}
    @media(max-width:920px){{.release-table-head{{display:none;}}.release-row{{grid-template-columns:1fr;}}.release-amount{{text-align:left;}}.release-control-summary{{grid-template-columns:repeat(2,minmax(0,1fr));}}.release-list{{height:auto;overflow:visible;cursor:default;user-select:auto;}}}}
    @media(max-width:720px){{.stage-grid{{grid-template-columns:1fr;}}.release-head{{flex-direction:column;}}.release-control-summary{{grid-template-columns:1fr;}}}}
    </style>
    <div class="release-shell" id="release-shell-main">
      <div class="release-head">
        <div><div class="release-title">Arquitectura de liberación PMO</div><div class="release-sub">Cortes financieros, capital requerido y control operacional por hito.</div></div>
        <div class="release-badge">Fuente: Cronograma Integrado</div>
      </div>
      <div class="release-flow">
        <div class="release-line"></div>
        <div class="release-nodes">{release_nodes}</div>
        <div class="stage-grid">{''.join(stage_card(panel, idx) for idx, panel in enumerate(panels))}</div>
      </div>
      <div class="release-legend"><span><i class="legend-icon">◎</i>Hitos activos</span><span><i class="legend-icon">▤</i>Partidas</span><span><i class="legend-line"></i>Avance</span><span>Montos MMCLP</span></div>
      <div class="release-detail-stack">{detail_panels}</div>
    </div>
    <script>
    (() => {{
      const root = document.getElementById("release-shell-main");
      if (!root) return;
      const cards = Array.from(root.querySelectorAll(".release-stage"));
      const panels = Array.from(root.querySelectorAll(".release-panel"));
      cards.forEach((card) => {{
        card.addEventListener("click", () => {{
          const selected = card.getAttribute("data-stage");
          cards.forEach((item) => item.classList.toggle("active", item.getAttribute("data-stage") === selected));
          panels.forEach((panel) => {{
            const active = panel.getAttribute("data-panel") === selected;
            panel.classList.toggle("active", active);
            panel.classList.toggle("expanded", active);
          }});
        }});
      }});
      root.querySelectorAll(".panel-head").forEach((head) => {{
        head.addEventListener("click", () => {{
          const panel = head.closest(".release-panel");
          if (panel) panel.classList.toggle("expanded");
        }});
      }});
      root.querySelectorAll(".release-list").forEach((list) => {{
        let dragging = false;
        let startX = 0;
        let startY = 0;
        let scrollLeft = 0;
        let scrollTop = 0;
        list.addEventListener("mousedown", (event) => {{
          dragging = true;
          list.classList.add("is-dragging");
          startX = event.pageX - list.offsetLeft;
          startY = event.pageY - list.offsetTop;
          scrollLeft = list.scrollLeft;
          scrollTop = list.scrollTop;
        }});
        list.addEventListener("mouseleave", () => {{
          dragging = false;
          list.classList.remove("is-dragging");
        }});
        list.addEventListener("mouseup", () => {{
          dragging = false;
          list.classList.remove("is-dragging");
        }});
        list.addEventListener("mousemove", (event) => {{
          if (!dragging) return;
          event.preventDefault();
          const x = event.pageX - list.offsetLeft;
          const y = event.pageY - list.offsetTop;
          list.scrollLeft = scrollLeft - (x - startX);
          list.scrollTop = scrollTop - (y - startY);
        }});
      }});
    }})();
    </script>
    """
    components.html(html_doc, height=1280, scrolling=False)


def render_expandable_activity_gantt(df: pd.DataFrame) -> None:
    scheduled = df[df["Inicio"].notna() & df["Termino"].notna()].copy()
    if scheduled.empty:
        return

    hito_ranges = (
        scheduled.groupby(["Hito", "Hito Ejecutivo", "Hito Corto"], as_index=False)
        .agg(
            Inicio_hito=("Inicio", "min"),
            Termino_hito=("Termino", "max"),
            Actividades=("ID", "count"),
            Monto=("Monto CLP Num", "sum"),
        )
        .sort_values("Hito")
    )
    hito_ranges["Orden"] = pd.to_numeric(hito_ranges["Hito"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    hito_ranges = hito_ranges.sort_values(["Orden", "Inicio_hito"])
    horizon_start = hito_ranges["Inicio_hito"].min()
    horizon_end = hito_ranges["Termino_hito"].max()
    horizon_days = max((horizon_end - horizon_start).days, 1)
    today = pd.Timestamp("today").normalize()

    def pct(date_value: pd.Timestamp) -> float:
        return max(0.0, min(100.0, ((date_value - horizon_start).days / horizon_days) * 100.0))

    colors = {
        "H1": "#0B2D42",
        "H2": "#2F80ED",
        "H3": "#1D4ED8",
        "H4": "#DC2626",
        "H5": "#64748B",
        "H6": "#0F766E",
        "H7": "#7C3AED",
        "H8": "#DC2626",
    }
    month_labels = []
    cursor = pd.Timestamp(horizon_start.year, horizon_start.month, 1)
    while cursor <= horizon_end:
        month_labels.append((cursor.strftime("%b %Y"), pct(cursor)))
        cursor = cursor + pd.DateOffset(months=1)
    months_html = "".join(
        f"<span style='left:{left:.2f}%;'>{html.escape(label.title())}</span>" for label, left in month_labels
    )
    today_left = pct(today)
    rows = []
    for idx, hito in hito_ranges.iterrows():
        code = str(hito["Hito"])
        hito_df = scheduled[scheduled["Hito"].astype(str).eq(code)].copy()
        hito_df = hito_df.sort_values(["Inicio", "Termino", "Monto CLP Num"], ascending=[True, True, False])
        start = pd.Timestamp(hito["Inicio_hito"])
        end = pd.Timestamp(hito["Termino_hito"])
        color = colors.get(code, "#0F766E")
        left = pct(start)
        width = max(2.5, pct(end) - left)
        detail_rows = []
        for _, activity in hito_df.iterrows():
            detail_rows.append(
                f"""
                <div class="act-detail-row">
                  <div class="act-id" style="color:{color};">{html.escape(str(activity["ID"]))}</div>
                  <div class="act-copy">
                    <b>{html.escape(str(activity["Categoría/Línea"]))}</b>
                    <span>{html.escape(str(activity["Descripción Técnica / Acción"]))}</span>
                  </div>
                  <div class="act-date">{format_date(activity["Inicio"])}<br>{format_date(activity["Termino"])}</div>
                  <div class="act-amount">{format_clp(float(activity["Monto CLP Num"] or 0))}</div>
                </div>
                """
            )
        rows.append(
            f"""
            <div class="act-row" data-row="{html.escape(code)}">
              <button class="act-main" type="button">
                <div class="act-label">
                  <div class="act-code" style="background:{color};">{html.escape(code)}</div>
                  <div>
                    <div class="act-name">{html.escape(str(hito["Hito Corto"]))}</div>
                    <div class="act-meta">{int(hito["Actividades"])} actividades · {format_date(start)} a {format_date(end)}</div>
                  </div>
                </div>
                <div class="act-track">
                  <div class="act-bar" style="left:{left:.2f}%;width:{width:.2f}%;--accent:{color};">
                    <span>{business_days(start, end)} días hábiles</span>
                  </div>
                </div>
                <div class="act-total">
                  <b>{format_clp(float(hito["Monto"] or 0))}</b>
                  <span>Ver detalle</span>
                </div>
              </button>
              <div class="act-details">{''.join(detail_rows)}</div>
            </div>
            """
        )

    html_doc = f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#0B1633;overflow-x:hidden;}}
    .act-shell{{background:linear-gradient(180deg,#FFFFFF 0%,#F8FBFD 100%);border:1px solid #DCE6EF;border-radius:18px;padding:18px 20px;box-shadow:0 8px 24px rgba(15,23,42,.06);overflow:hidden;}}
    .act-head{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:14px;}}
    .act-title{{font-size:20px;font-weight:950;color:#23457A;line-height:1.1;}}
    .act-sub{{font-size:12px;color:#64748B;line-height:1.38;margin-top:6px;max-width:780px;}}
    .act-badge{{background:#FFFFFF;border:1px solid #DCE6EF;border-radius:999px;padding:7px 10px;font-size:11px;font-weight:900;color:#475569;white-space:nowrap;}}
    .act-axis{{position:relative;margin-left:260px;margin-right:120px;height:30px;border-bottom:1px solid #E2E8F0;}}
    .act-axis span{{position:absolute;top:3px;transform:translateX(-2px);font-size:10px;font-weight:850;color:#64748B;text-transform:uppercase;white-space:nowrap;}}
    .act-list{{position:relative;display:grid;gap:10px;padding-top:8px;}}
    .act-overlay{{position:absolute;left:260px;right:120px;top:0;bottom:0;pointer-events:none;}}
    .act-today{{position:absolute;top:0;bottom:0;left:{today_left:.2f}%;width:2px;background:#EF4444;box-shadow:0 0 0 5px rgba(239,68,68,.08);z-index:5;}}
    .act-today span{{position:absolute;top:-24px;left:50%;transform:translateX(-50%);background:#EF4444;color:#FFFFFF;border-radius:999px;padding:4px 9px;font-size:10px;font-weight:950;}}
    .act-row{{position:relative;z-index:10;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;box-shadow:0 7px 16px rgba(15,23,42,.03);}}
    .act-main{{appearance:none;width:100%;border:0;background:transparent;display:grid;grid-template-columns:250px minmax(260px,1fr) 108px;gap:10px;align-items:center;padding:11px 10px;cursor:pointer;text-align:left;}}
    .act-main:hover{{background:#FAFCFE;}}
    .act-label{{display:flex;align-items:center;gap:10px;min-width:0;}}
    .act-code{{width:38px;height:38px;border-radius:12px;color:#FFFFFF;font-size:14px;font-weight:950;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 18px rgba(15,23,42,.16);flex:0 0 auto;}}
    .act-name{{font-size:12px;font-weight:950;color:#0B1633;line-height:1.14;}}
    .act-meta{{font-size:10px;color:#64748B;margin-top:3px;font-weight:750;}}
    .act-track{{height:34px;border-radius:12px;background:linear-gradient(90deg,rgba(226,232,240,.70),rgba(248,250,252,.35));position:relative;overflow:hidden;border:1px solid #EEF3F7;}}
    .act-bar{{position:absolute;top:8px;height:18px;border-radius:999px;background:linear-gradient(90deg,var(--accent),color-mix(in srgb,var(--accent) 70%,#FFFFFF));box-shadow:0 8px 16px color-mix(in srgb,var(--accent) 16%,transparent);display:flex;align-items:center;padding:0 10px;min-width:34px;}}
    .act-bar span{{font-size:10px;color:#FFFFFF;font-weight:950;white-space:nowrap;text-shadow:0 1px 2px rgba(15,23,42,.22);}}
    .act-total{{text-align:right;}}
    .act-total b{{display:block;font-size:11px;color:#0B1633;white-space:nowrap;}}
    .act-total span{{display:block;margin-top:4px;font-size:9px;font-weight:950;color:#2F80ED;text-transform:uppercase;}}
    .act-details{{display:none;border-top:1px solid #EEF3F7;background:#FBFCFE;padding:9px 10px 11px 10px;gap:7px;}}
    .act-row.open .act-details{{display:grid;}}
    .act-detail-row{{display:grid;grid-template-columns:70px minmax(0,1fr) 86px 94px;gap:10px;align-items:center;background:#FFFFFF;border:1px solid #EEF3F7;border-radius:10px;padding:9px;}}
    .act-id{{font-size:10px;font-weight:950;color:#0B1633;background:#EEF6FF;border-radius:999px;padding:5px 7px;text-align:center;}}
    .act-copy b{{display:block;font-size:11px;color:#0B1633;line-height:1.14;}}
    .act-copy span{{display:block;font-size:10px;color:#64748B;margin-top:3px;line-height:1.25;}}
    .act-date{{font-size:10px;color:#475569;font-weight:850;text-align:center;line-height:1.2;}}
    .act-amount{{font-size:10px;color:#0B1633;font-weight:950;text-align:right;white-space:nowrap;}}
    @media(max-width:980px){{.act-axis{{margin-left:0;margin-right:0;}}.act-main{{grid-template-columns:1fr;}}.act-overlay{{display:none;}}.act-detail-row{{grid-template-columns:1fr;}}.act-total{{text-align:left;}}}}
    </style>
    <div class="act-shell" id="activity-gantt-shell">
      <div class="act-head">
        <div><div class="act-title">Cronograma técnico por hito</div><div class="act-sub">Vista desplegable de actividades, fechas, categorías y montos por hito.</div></div>
        <div class="act-badge">Detalle por hito · Cronograma Integrado</div>
      </div>
      <div class="act-axis">{months_html}</div>
      <div class="act-list">
        <div class="act-overlay"><div class="act-today"><span>HOY</span></div></div>
        {''.join(rows)}
      </div>
    </div>
    <script>
    (() => {{
      const root = document.getElementById("activity-gantt-shell");
      if (!root) return;
      root.querySelectorAll(".act-main").forEach((button) => {{
        button.addEventListener("click", () => {{
          const row = button.closest(".act-row");
          if (row) row.classList.toggle("open");
        }});
      }});
    }})();
    </script>
    """
    components.html(html_doc, height=700, scrolling=True)


def render_project_timeline_conditions(df: pd.DataFrame, pmo_source: pd.DataFrame | None = None) -> None:
    scheduled = df[df["Inicio"].notna() & df["Termino"].notna()].copy()
    if scheduled.empty:
        return

    dependency_cols = [
        col
        for col in scheduled.columns
        if normalize_text(col).lower() in {"dependencia id", "dependencia"}
    ]
    dependency_col = dependency_cols[0] if dependency_cols else None
    dependency_by_hito: dict[str, str] = {}
    if dependency_col:
        dependency_by_hito = (
            scheduled.assign(_dep=scheduled[dependency_col].fillna("").astype(str).str.strip())
            .query("_dep != '' and _dep != 'nan'")
            .groupby("Hito")["_dep"]
            .agg(lambda values: ", ".join(dict.fromkeys(values)))
            .to_dict()
        )

    hito_ranges = (
        scheduled.groupby(["Hito", "Hito Ejecutivo", "Hito Corto"], as_index=False)
        .agg(
            Inicio_hito=("Inicio", "min"),
            Termino_hito=("Termino", "max"),
            Actividades=("ID", "count"),
            Monto=("Monto CLP Num", "sum"),
        )
        .sort_values("Hito")
    )
    if hito_ranges.empty:
        return

    hito_ranges["Orden"] = pd.to_numeric(hito_ranges["Hito"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    hito_ranges = hito_ranges.sort_values(["Orden", "Inicio_hito"]).reset_index(drop=True)

    pmo_conditions = clean_pmo_matrix_source(pmo_source)
    condition_by_name: dict[str, str] = {}
    if not pmo_conditions.empty:
        condition_by_name = {
            normalize_text(row["Hito Ejecutivo"]): str(row["Condición de Liberación"]).strip()
            for _, row in pmo_conditions.iterrows()
            if str(row.get("Condición de Liberación", "")).strip()
        }
    hito_ranges["Condición de Liberación"] = hito_ranges["Hito Ejecutivo"].map(
        lambda value: condition_by_name.get(normalize_text(value), "Condición de liberación PMO por confirmar")
    )

    start = pd.Timestamp(hito_ranges["Inicio_hito"].min())
    end = pd.Timestamp(hito_ranges["Termino_hito"].max())
    months = max(1, (end.year - start.year) * 12 + end.month - start.month + 1)
    total_amount = float(hito_ranges["Monto"].sum() or 0)
    duration_days = business_days(start, end)
    phase_count = 3
    phase_1 = min(2, len(hito_ranges))
    phase_3 = 1 if len(hito_ranges) >= 5 else 0
    phase_2 = max(len(hito_ranges) - phase_1 - phase_3, 1)
    phase_style = f"grid-template-columns:{phase_1}fr {phase_2}fr {max(phase_3, 1)}fr;"

    month_cursor = pd.Timestamp(start.year, start.month, 1)
    month_cells = []
    while month_cursor <= end:
        month_cells.append(month_cursor.strftime("%b").upper())
        month_cursor = month_cursor + pd.DateOffset(months=1)
    months_html = "".join(f"<span>{html.escape(month)}</span>" for month in month_cells)

    def money_mm(value: float) -> str:
        return f"${value / 1_000_000:.1f}MM".replace(".", ",")

    def short_text(value: object, limit: int = 92) -> str:
        text = re.sub(r"\s+", " ", str(value or "").strip())
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    def pct(date_value: pd.Timestamp) -> float:
        total_days = max((end - start).days, 1)
        return max(0.0, min(100.0, ((date_value - start).days / total_days) * 100.0))

    hito_colors = {
        "H1": "#0B2D42",
        "H2": "#2F80ED",
        "H3": "#1D4ED8",
        "H4": "#DC2626",
        "H5": "#64748B",
        "H6": "#0F766E",
        "H7": "#7C3AED",
        "H8": "#DC2626",
    }
    hito_icons = {
        "H1": "CIV",
        "H2": "FRP",
        "H3": "FND",
        "H4": "LOG",
        "H5": "MEC",
        "H6": "ELE",
        "H7": "RUN",
        "H8": "COD",
    }

    cards_html = []
    mini_bars = []
    for idx, hito in hito_ranges.iterrows():
        code = str(hito["Hito"])
        color = hito_colors.get(code, "#0F766E")
        icon = hito_icons.get(code, ROADMAP_ICONS.get(str(hito["Hito Ejecutivo"]), "PMO"))
        start_label = format_date(hito["Inicio_hito"])
        end_label = format_date(hito["Termino_hito"])
        dependency = dependency_by_hito.get(code, f"H{idx}" if idx > 0 else "Inicio PMO")
        condition = str(hito["Condición de Liberación"])
        left = pct(pd.Timestamp(hito["Inicio_hito"]))
        width = max(2.0, pct(pd.Timestamp(hito["Termino_hito"])) - left)
        cards_html.append(
            f"""
            <div class="tl-card" style="--hito:{color};">
              <div class="tl-badge">{html.escape(code)}</div>
              <div class="tl-icon" style="border-color:{color};color:{color};">{html.escape(icon)}</div>
              <div class="tl-name">{html.escape(str(hito["Hito Corto"]))}</div>
              <div class="tl-date">{html.escape(start_label)}</div>
              <div class="tl-condition">{html.escape(short_text(condition))}</div>
              <div class="tl-meta">
                <span>{int(hito["Actividades"])} partidas</span>
                <span>{money_mm(float(hito["Monto"] or 0))}</span>
              </div>
              <div class="tl-dep">Depende de: <b>{html.escape(dependency)}</b></div>
            </div>
            """
        )
        mini_bars.append(
            f"""
            <div class="tl-mini-bar" style="left:{left:.2f}%;width:{width:.2f}%;background:{color};">
              <span>{html.escape(code)}</span><i>{html.escape(start_label)} · {html.escape(end_label)}</i>
            </div>
            """
        )

    flow_html = "".join(
        f"""
        <span class="flow-node" style="--flow:{hito_colors.get(str(row['Hito']), '#0F766E')};">{html.escape(str(row['Hito']))}</span>
        {('<i>→</i>' if idx < len(hito_ranges) - 1 else '')}
        """
        for idx, row in hito_ranges.iterrows()
    )

    html_doc = f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#0B1633;overflow-x:hidden;}}
    .tl-shell{{background:linear-gradient(180deg,#FFFFFF 0%,#F8FBFD 100%);border:1px solid #DCE6EF;border-radius:18px;padding:18px 20px;box-shadow:0 8px 24px rgba(15,23,42,.06);overflow:hidden;}}
    .tl-top{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:start;margin-bottom:14px;}}
    .tl-eyebrow{{font-size:10px;text-transform:uppercase;letter-spacing:.15em;color:#0F766E;font-weight:950;margin-bottom:5px;}}
    .tl-title{{font-size:20px;font-weight:950;color:#23457A;line-height:1.1;letter-spacing:0;}}
    .tl-sub{{font-size:12px;color:#64748B;line-height:1.38;margin-top:6px;max-width:780px;font-weight:750;}}
    .tl-kpis{{display:grid;grid-template-columns:repeat(4,auto);gap:8px;}}
    .tl-kpi{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:9px 12px;min-width:108px;box-shadow:0 8px 18px rgba(15,23,42,.04);}}
    .tl-kpi b{{display:block;font-size:18px;color:#0B1633;line-height:1;}}.tl-kpi span{{display:block;font-size:9px;color:#64748B;font-weight:900;text-transform:uppercase;line-height:1.2;margin-top:4px;}}
    .tl-phases{{display:grid;{phase_style}gap:8px;margin-bottom:12px;}}
    .tl-phase{{border-radius:12px;padding:10px 14px;color:#FFFFFF;min-height:54px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 12px 22px rgba(15,23,42,.08);}}
    .tl-phase b{{display:block;font-size:13px;line-height:1.1;}}.tl-phase span{{display:block;font-size:10px;font-weight:850;opacity:.9;margin-top:4px;}}.tl-phase i{{font-style:normal;font-size:10px;border:1px solid rgba(255,255,255,.38);border-radius:999px;padding:4px 8px;font-weight:950;}}
    .tl-phase.one{{background:linear-gradient(135deg,#0B2D42,#23457A);}}.tl-phase.two{{background:linear-gradient(135deg,#0F766E,#4F7D3A);}}.tl-phase.three{{background:linear-gradient(135deg,#B7791F,#C56A12);}}
    .tl-months{{display:grid;grid-template-columns:repeat({len(month_cells)},1fr);gap:2px;margin:2px 4px 10px;border-bottom:1px solid #CBD5E1;padding-bottom:6px;}}
    .tl-months span{{font-size:10px;color:#64748B;font-weight:950;text-align:center;}}
    .tl-cards{{display:grid;grid-template-columns:repeat({len(hito_ranges)},minmax(0,1fr));gap:8px;align-items:stretch;}}
    .tl-card{{position:relative;background:#FFFFFF;border:1px solid #E2E8F0;border-top:4px solid var(--hito);border-radius:13px;padding:12px 10px 11px;min-height:238px;box-shadow:0 11px 24px rgba(15,23,42,.045);display:flex;flex-direction:column;align-items:center;text-align:center;}}
    .tl-card:before{{content:"";position:absolute;top:-15px;left:50%;height:14px;border-left:1px dashed #CBD5E1;}}
    .tl-badge{{height:28px;min-width:40px;border-radius:999px;background:var(--hito);color:#FFFFFF;font-size:13px;font-weight:950;display:flex;align-items:center;justify-content:center;padding:0 10px;box-shadow:0 8px 18px color-mix(in srgb,var(--hito) 24%,transparent);}}
    .tl-icon{{width:46px;height:46px;margin:10px auto 9px;border:1.5px solid;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:950;background:#FFFFFF;}}
    .tl-name{{font-size:11px;line-height:1.14;font-weight:950;color:#0B1633;min-height:38px;display:flex;align-items:center;justify-content:center;}}
    .tl-date{{display:inline-block;margin-top:8px;padding:5px 7px;border-radius:7px;background:#F1F5F9;color:#334155;font-size:9px;font-weight:950;}}
    .tl-condition{{margin-top:9px;font-size:9.5px;line-height:1.28;color:#475569;font-weight:750;min-height:47px;}}
    .tl-meta{{width:100%;display:flex;justify-content:space-between;gap:6px;margin-top:auto;border-top:1px solid #EEF3F7;padding-top:8px;}}
    .tl-meta span{{font-size:8.5px;color:#64748B;font-weight:900;white-space:nowrap;}}
    .tl-dep{{width:100%;margin-top:7px;background:#F8FAFC;border:1px solid #EEF3F7;border-radius:8px;padding:5px 6px;font-size:8.5px;color:#64748B;font-weight:850;}}.tl-dep b{{color:#0B1633;}}
    .tl-flow{{margin-top:12px;display:grid;grid-template-columns:1fr .52fr;gap:10px;align-items:stretch;}}
    .flow-box,.summary-box{{background:#FFFFFF;border:1px solid #DCE6EF;border-radius:13px;padding:12px 14px;box-shadow:0 9px 20px rgba(15,23,42,.04);}}
    .box-title{{font-size:12px;font-weight:950;color:#23457A;margin-bottom:9px;}}
    .flow-line{{display:flex;align-items:center;gap:7px;flex-wrap:wrap;}}
    .flow-line i{{font-style:normal;color:#94A3B8;font-weight:950;}}
    .flow-node{{background:var(--flow);color:#FFFFFF;border-radius:999px;padding:7px 10px;font-size:11px;font-weight:950;box-shadow:0 7px 15px color-mix(in srgb,var(--flow) 18%,transparent);}}
    .tl-mini-gantt{{position:relative;height:64px;margin-top:11px;border-radius:12px;background:linear-gradient(90deg,#F8FAFC,#FFFFFF);border:1px solid #E2E8F0;overflow:hidden;}}
    .tl-mini-gantt:before{{content:"";position:absolute;left:12px;right:12px;top:31px;height:2px;background:#CBD5E1;}}
    .tl-mini-bar{{position:absolute;top:22px;height:18px;border-radius:999px;box-shadow:0 8px 16px rgba(15,23,42,.08);display:flex;align-items:center;gap:5px;padding:0 7px;color:#FFFFFF;overflow:hidden;}}
    .tl-mini-bar span{{font-size:9px;font-weight:950;}}.tl-mini-bar i{{font-style:normal;font-size:8px;font-weight:850;opacity:.85;white-space:nowrap;}}
    .summary-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;}}
    .summary-item{{background:#F8FAFC;border:1px solid #EEF3F7;border-radius:10px;padding:9px;}}.summary-item b{{display:block;font-size:13px;color:#0B1633;line-height:1;}}.summary-item span{{display:block;font-size:8.5px;color:#64748B;font-weight:900;text-transform:uppercase;margin-top:5px;line-height:1.15;}}
    .commit-text{{font-size:10px;color:#475569;line-height:1.35;margin-top:9px;font-weight:750;}}
    @media(max-width:1100px){{.tl-top{{grid-template-columns:1fr;}}.tl-kpis{{grid-template-columns:repeat(2,minmax(0,1fr));}}.tl-phases{{grid-template-columns:1fr;}}.tl-cards{{grid-template-columns:repeat(2,minmax(0,1fr));}}.tl-flow{{grid-template-columns:1fr;}}.tl-months{{grid-template-columns:repeat(4,minmax(0,1fr));}}}}
    @media(max-width:720px){{.tl-cards{{grid-template-columns:1fr;}}.tl-kpis{{grid-template-columns:1fr;}}}}
    </style>
    <div class="tl-shell">
      <div class="tl-inner">
        <div class="tl-top">
          <div>
            <div class="tl-title">Roadmap ejecutivo de hitos</div>
            <div class="tl-sub">Fases, dependencias y condiciones de liberación del piloto.</div>
          </div>
          <div class="tl-kpis">
            <div class="tl-kpi"><b>{len(hito_ranges)}</b><span>Hitos clave</span></div>
            <div class="tl-kpi"><b>{months}</b><span>Meses de ejecución</span></div>
            <div class="tl-kpi"><b>{phase_count}</b><span>Fases principales</span></div>
            <div class="tl-kpi"><b>0</b><span>Incidentes críticos</span></div>
          </div>
        </div>
        <div class="tl-phases">
          <div class="tl-phase one"><div><b>Fase 1</b><span>Preparación y diseño</span></div><i>H1-H2</i></div>
          <div class="tl-phase two"><div><b>Fase 2</b><span>Construcción e implementación</span></div><i>H3-H6</i></div>
          <div class="tl-phase three"><div><b>Fase 3</b><span>Puesta en marcha y cierre</span></div><i>H7</i></div>
        </div>
        <div class="tl-months">{months_html}</div>
        <div class="tl-cards">{''.join(cards_html)}</div>
        <div class="tl-flow">
          <div class="flow-box">
            <div class="box-title">Flujo de dependencias</div>
            <div class="flow-line">{flow_html}</div>
            <div class="tl-mini-gantt">{''.join(mini_bars)}</div>
          </div>
          <div class="summary-box">
            <div class="box-title">Resumen ejecutivo</div>
            <div class="summary-grid">
              <div class="summary-item"><b>{money_mm(total_amount)}</b><span>Presupuesto asociado</span></div>
              <div class="summary-item"><b>{duration_days}</b><span>Días hábiles</span></div>
              <div class="summary-item"><b>{format_date(end)}</b><span>Cierre estimado</span></div>
            </div>
            <div class="commit-text">La secuencia muestra cómo cada liberación habilita continuidad técnica, integración operacional y puesta en marcha sin desaceleración del piloto.</div>
          </div>
        </div>
      </div>
    </div>
    <script>
    (() => {{
      const adjustRoadmapOffset = () => {{
        try {{
          const frames = Array.from(window.parent.document.querySelectorAll("iframe"));
          const current = frames.find((frame) => frame.contentWindow === window);
          if (!current) return;
          const previous = frames[frames.indexOf(current) - 1];
          if (!previous || !previous.contentDocument) return;
          const previousRoot = previous.contentDocument.getElementById("release-shell-main");
          if (!previousRoot) return;
          const reserved = previous.getBoundingClientRect().height;
          const actual = previousRoot.scrollHeight;
          const gap = Math.max(0, reserved - actual - 36);
          current.parentElement.style.marginTop = gap ? "-" + Math.min(gap, 760) + "px" : "0";
        }} catch (error) {{
          return;
        }}
      }};
      adjustRoadmapOffset();
      window.setInterval(adjustRoadmapOffset, 600);
      window.addEventListener("resize", adjustRoadmapOffset);
    }})();
    </script>
    """
    components.html(html_doc, height=760, scrolling=False)


def render_pmo_roadmap_matrix(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> None:
    metrics = pmo_financial_metrics(df, hito_summary, pmo_source)
    matrix = metrics["matrix"].copy().sort_values("Hito Orden")
    technical_pct = float(metrics["technical_progress"])
    risk = str(metrics["risk"]).upper()
    total = float(metrics["total_capex"])
    next_row = metrics["next_row"]

    def format_clp_mm(value: float) -> str:
        return f"${value / 1_000_000:.1f}MM".replace(".", ",")

    critical_hitos = {"H1", "H4", "H8"}
    status_label = {"Ejecutado": "Ejecutado", "En curso": "En curso", "Pendiente": "Pendiente"}
    status_color = {"Ejecutado": "#10B981", "En curso": "#2F80ED", "Pendiente": "#94A3B8"}
    timeline_start = matrix["_Inicio"].dropna().min() if "_Inicio" in matrix else pd.NaT
    timeline_end = matrix["_Termino"].dropna().max() if "_Termino" in matrix else pd.NaT
    today_dt = pd.Timestamp("today").normalize()
    today_pos = 0.0
    if pd.notna(timeline_start) and pd.notna(timeline_end) and timeline_end > timeline_start:
        today_pos = float((today_dt - timeline_start).days / max((timeline_end - timeline_start).days, 1))
        today_pos = min(max(today_pos, 0.0), 1.0) * 100
    progress_width = min(max(technical_pct * 100, 2), 100)

    timeline_items = []
    previous_hito = ""
    for _, row in matrix.iterrows():
        crit = str(row.get("Criticidad", "Media"))
        stt = str(row.get("Estado", "Pendiente"))
        hito_code = str(row.get("Hito", "-"))
        is_critical = hito_code in critical_hitos
        dot_color = "#EF4444" if is_critical else status_color.get(stt, "#94A3B8")
        dependency = "Inicio del programa" if not previous_hito else f"Depende de cierre técnico y financiero de {previous_hito}"
        previous_hito = hito_code
        timeline_items.append(
            f"""
            <div class="ref-mile {'critical' if is_critical else ''}">
              <div class="ref-node" style="background:{dot_color};">{html.escape(hito_code)}</div>
              <div class="decision-tooltip">
                <b>{html.escape(hito_code)} · {html.escape(str(row.get("Hito Corto", "-")))}</b>
                <span>CAPEX asociado: {html.escape(str(row.get("Monto total", "-")))}</span>
                <span>Riesgo: {'Crítico' if is_critical else html.escape(crit)}</span>
                <span>Dependencia: {html.escape(dependency)}</span>
                <span>Fondos requeridos: {html.escape(str(row.get("Total Liberación", "-")))}</span>
              </div>
              <div class="ref-mile-title">{html.escape(str(row.get("Hito Corto", "-")))}</div>
              <div class="ref-mile-status" style="color:{dot_color};background:{dot_color}18;">{html.escape(status_label.get(stt, stt).upper())}</div>
            </div>
            """
        )

    def impact_for(row: pd.Series) -> str:
        hito = str(row.get("Hito", ""))
        share = float(row.get("% sobre total", 0) or 0)
        crit = str(row.get("Criticidad", "Media"))
        if hito in {"H1", "H4", "H8"}:
            return "Crítico"
        if crit == "Alta" or share >= 0.20:
            return "Alto"
        if crit == "Media" or share >= 0.08:
            return "Medio"
        return "Bajo"

    def impact_class(value: str) -> str:
        return {"Crítico": "red", "Alto": "amber", "Medio": "blue", "Bajo": "green"}.get(value, "gray")

    def pmo_signal(row: pd.Series, impact: str) -> tuple[str, str]:
        state = str(row.get("Estado", "Pendiente"))
        if impact == "Crítico" or str(row.get("Criticidad", "")) == "Alta":
            return "Riesgo PMO", "red"
        if state == "En curso" or impact in {"Alto", "Medio"}:
            return "Seguimiento", "amber"
        return "En control", "green"

    def bar_cell(value: float, color: str, label: str) -> str:
        width = min(max(value, 0), 100)
        return f"""
        <div class="matrix-bar">
          <span>{html.escape(label)}</span>
          <div><i style="width:{width:.0f}%;background:{color};"></i></div>
        </div>
        """

    matrix_rows = []
    for _, row in matrix.iterrows():
        state = str(row.get("Estado", "Pendiente"))
        crit = str(row.get("Criticidad", "Media"))
        scenario_name = str(row.get("Escenario recomendado", "Base")).upper()
        hito_code = str(row.get("Hito", "-"))
        impact = impact_for(row)
        signal, signal_class = pmo_signal(row, impact)
        capex_pct = float(row.get("% sobre total", 0) or 0) * 100
        execution_pct = float(row.get("Avance_promedio", 0) or 0) * 100
        financial_pct = {"CONSERVADOR": 30, "BASE": 80, "CIERRE": 100}.get(scenario_name, 30)
        capex_value = float(row.get("Monto_CLP", 0) or 0)
        duration = int(float(row.get("Duracion_habil", 0) or 0))
        state_class = "blue" if state == "En curso" else "gray"
        crit_class = "red" if crit in {"Alta", "Crítica"} else "amber" if crit == "Media" else "green"
        scen_class = "green" if scenario_name == "CIERRE" else "blue" if scenario_name == "BASE" else "amber"
        matrix_rows.append(
            f"""
            <tr class="{'strategic-row' if hito_code in {'H1', 'H4', 'H8'} else ''} heat-{impact_class(impact)}">
              <td><span class="hito-code">{html.escape(hito_code)}</span></td>
              <td><span class="matrix-pill {state_class}">{html.escape(state)}</span></td>
              <td><span class="matrix-pill {crit_class}">{html.escape(crit)}</span></td>
              <td class="matrix-name"><b>{html.escape(str(row.get("Hito Ejecutivo", "-")))}</b><small>{html.escape(str(row.get("Condición de Liberación", "-")))}</small></td>
              <td><span class="matrix-pill blue">{html.escape(str(row.get("Etapa del hito", "-")))}</span></td>
              <td><span class="matrix-pill {impact_class(impact)}">{html.escape(impact)}</span></td>
              <td><span class="signal {signal_class}"><i></i>{html.escape(signal)}</span></td>
              <td>{bar_cell(financial_pct, "#2F80ED", f"{financial_pct:.0f}%")}</td>
              <td>{bar_cell(execution_pct, "#0F766E", f"{execution_pct:.0f}%")}</td>
              <td>{bar_cell(capex_pct, "#F59E0B", format_clp_mm(capex_value))}</td>
              <td>{duration} días</td>
              <td>{html.escape(format_date(row.get("_Inicio", row.get("Inicio", "-"))))}</td>
              <td>{html.escape(format_date(row.get("_Termino", row.get("Termino", "-"))))}</td>
              <td><span class="matrix-pill {scen_class}">{html.escape(scenario_name)}</span></td>
              <td class="decision-cell">{html.escape(str(row.get("Decisión requerida", "-")))}</td>
            </tr>
            """
        )

    critical_count = int(matrix["Hito"].astype(str).isin(["H1", "H4", "H8"]).sum())
    next_unlock = str(next_row.get("Hito", "H2")) if isinstance(next_row, pd.Series) and not next_row.empty else "H2"
    html_doc = f"""
    <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#0B1633;overflow-x:hidden;}}
    .pmo-mini{{display:grid;gap:14px;background:#F7F9FC;padding:0;overflow-x:hidden;}}
    .control-panel{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:18px 20px;box-shadow:0 12px 24px rgba(15,23,42,.05);overflow:hidden;min-width:0;}}
    .ref-panel-title{{font-size:18px;font-weight:900;color:#23457A;letter-spacing:0;margin-bottom:14px;}}
    .timeline-head{{display:flex;justify-content:space-between;gap:16px;align-items:center;min-width:0;}}
    .timeline-legend{{display:flex;gap:16px;align-items:center;font-size:13px;color:#334155;flex-wrap:wrap;justify-content:flex-end;}}
    .legend-dot{{display:inline-block;width:12px;height:12px;border-radius:999px;margin-right:6px;vertical-align:-1px;}}
    .ref-stage{{display:grid;grid-template-columns:1.45fr 3.2fr 2.1fr;gap:10px;margin:12px 0 36px 0;}}
    .ref-stage div{{height:31px;border-radius:8px;font-size:12px;font-weight:900;display:flex;align-items:center;justify-content:center;color:#334155;}}
    .decision-roadmap{{position:relative;padding:22px 6px 14px 6px;overflow:visible;max-width:100%;}}
    .today-line{{position:absolute;top:-4px;bottom:18px;left:var(--today);width:2px;background:#EF4444;z-index:5;box-shadow:0 0 0 5px rgba(239,68,68,.10);}}
    .today-line span{{position:absolute;top:-24px;left:50%;transform:translateX(-50%);background:#EF4444;color:#FFFFFF;border-radius:999px;padding:5px 10px;font-size:11px;font-weight:950;white-space:nowrap;}}
    .decision-track{{position:absolute;left:24px;right:24px;top:46px;height:7px;border-radius:999px;background:#E2E8F0;box-shadow:inset 0 1px 2px rgba(15,23,42,.06);}}
    .decision-progress{{height:100%;width:var(--progress);border-radius:999px;background:linear-gradient(90deg,#0F766E,#2F80ED);box-shadow:0 6px 14px rgba(47,128,237,.18);}}
    .ref-line{{position:relative;display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:8px;padding-top:0;margin-top:24px;z-index:10;}}
    .ref-mile{{text-align:center;position:relative;min-height:126px;overflow:visible;}}
    .ref-node{{width:42px;height:42px;border-radius:999px;color:#FFFFFF;font-weight:950;display:flex;align-items:center;justify-content:center;margin:0 auto 10px auto;box-shadow:0 7px 14px rgba(15,23,42,.18);position:relative;z-index:3;font-size:18px;}}
    .ref-mile.critical .ref-node{{width:56px;height:56px;margin-top:-7px;margin-bottom:3px;box-shadow:0 0 0 10px rgba(239,68,68,.12),0 15px 30px rgba(239,68,68,.24);}}
    .ref-mile.critical .ref-node::after{{content:"";position:absolute;inset:-12px;border-radius:999px;border:1px solid rgba(239,68,68,.32);}}
    .ref-mile-title{{font-size:13px;color:#243B53;line-height:1.15;min-height:34px;max-width:132px;margin:0 auto;font-weight:850;}}
    .ref-mile-status{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:10px;font-weight:950;margin-top:8px;}}
    .decision-tooltip{{position:absolute;z-index:40;left:50%;bottom:116px;transform:translateX(-50%) translateY(6px);width:235px;background:#08253B;color:#FFFFFF;border-radius:10px;padding:12px 13px;text-align:left;box-shadow:0 18px 38px rgba(8,37,59,.28);opacity:0;pointer-events:none;transition:opacity .16s ease,transform .16s ease;}}
    .decision-tooltip::after{{content:"";position:absolute;left:50%;bottom:-7px;transform:translateX(-50%);border-left:7px solid transparent;border-right:7px solid transparent;border-top:7px solid #08253B;}}
    .decision-tooltip b{{display:block;font-size:12px;margin-bottom:8px;color:#FFFFFF;}}
    .decision-tooltip span{{display:block;font-size:11px;line-height:1.35;color:#DDE8F3;margin-top:4px;}}
    .ref-mile:hover .decision-tooltip{{opacity:1;transform:translateX(-50%) translateY(0);}}
    .matrix-summary{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-bottom:12px;min-width:0;}}
    .summary-tile{{background:linear-gradient(145deg,#FFFFFF,#F9FBFD);border:1px solid #E2E8F0;border-radius:12px;padding:13px 14px;box-shadow:0 10px 20px rgba(15,23,42,.045);}}
    .summary-tile small{{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#64748B;font-weight:850;}}
    .summary-tile b{{display:block;font-size:20px;color:#0B1633;margin-top:5px;}}
    .matrix-scroll{{overflow-x:hidden;overflow-y:auto;border:1px solid #E2E8F0;border-radius:12px;max-height:570px;background:#FFFFFF;width:100%;}}
    .pmo-matrix{{width:100%;min-width:0;table-layout:fixed;border-collapse:separate;border-spacing:0;background:#FFFFFF;font-size:9px;color:#0B1633;}}
    .pmo-matrix th{{position:sticky;top:0;z-index:20;background:#F8FAFC;color:#334155;font-size:8px;letter-spacing:0;border-bottom:1px solid #DCE6EF;padding:10px 5px;text-align:center;white-space:normal;line-height:1.15;word-break:break-word;}}
    .pmo-matrix td{{border-bottom:1px solid #EEF3F7;padding:12px 5px;text-align:center;vertical-align:middle;background:#FFFFFF;line-height:1.22;word-break:break-word;}}
    .strategic-row td{{background:#FFFBF5;}}
    .hito-code{{display:inline-flex;align-items:center;justify-content:center;width:35px;height:32px;border-radius:10px;background:#0B2D42;color:#FFFFFF;font-size:14px;font-weight:950;}}
    .strategic-row .hito-code{{background:#E11D48;box-shadow:0 0 0 6px rgba(225,29,72,.10);}}
    .matrix-name{{text-align:left!important;width:17%;}}
    .matrix-name b{{display:block;font-size:10px;color:#0B1633;line-height:1.2;}}
    .matrix-name small{{display:block;font-size:8px;color:#64748B;line-height:1.2;margin-top:3px;}}
    .matrix-pill{{display:inline-flex;border-radius:5px;padding:4px 6px;font-size:8px;font-weight:950;white-space:normal;justify-content:center;}}
    .matrix-pill.blue{{background:#DBEAFE;color:#2563EB;}}.matrix-pill.gray{{background:#E2E8F0;color:#64748B;}}.matrix-pill.red{{background:#FEE2E2;color:#E11D48;}}.matrix-pill.amber{{background:#FEF3C7;color:#D97706;}}.matrix-pill.green{{background:#D1FAE5;color:#047857;}}
    .signal{{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:5px 7px;font-size:8px;font-weight:900;white-space:normal;justify-content:center;}}
    .signal i{{width:8px;height:8px;border-radius:999px;display:inline-block;}}.signal.green{{background:#D1FAE5;color:#047857;}}.signal.green i{{background:#10B981;}}.signal.amber{{background:#FEF3C7;color:#B45309;}}.signal.amber i{{background:#F59E0B;}}.signal.red{{background:#FEE2E2;color:#BE123C;}}.signal.red i{{background:#E11D48;}}
    .matrix-bar{{text-align:left;}}.matrix-bar span{{display:block;font-size:8px;color:#334155;font-weight:900;margin-bottom:5px;}}.matrix-bar div{{height:7px;background:#E2E8F0;border-radius:999px;overflow:hidden;}}.matrix-bar i{{display:block;height:100%;border-radius:999px;}}
    .decision-cell{{text-align:left!important;color:#334155;line-height:1.25;}}
    .matrix-foot{{font-size:10px;color:#64748B;margin-top:10px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;}}
    </style>
    <div class="pmo-mini">
      <div class="control-panel">
        <div class="timeline-head">
          <div class="ref-panel-title">Roadmap de decisión H1 → H8</div>
          <div class="timeline-legend">
            <span><i class="legend-dot" style="background:#10B981;"></i>Ejecutado</span>
            <span><i class="legend-dot" style="background:#2F80ED;"></i>En curso</span>
            <span><i class="legend-dot" style="background:#94A3B8;"></i>Pendiente</span>
            <span><i class="legend-dot" style="background:#EF4444;"></i>Crítico</span>
          </div>
        </div>
        <div class="ref-stage"><div style="background:#DDF3F7;">Liberación inicial</div><div style="background:#FBF0D5;">Ingeniería y fabricación</div><div style="background:#DDF4EA;">Integración y cierre</div></div>
        <div class="decision-roadmap" style="--today:{today_pos:.2f}%;--progress:{progress_width:.2f}%;">
          <div class="today-line"><span>HOY</span></div>
          <div class="decision-track"><div class="decision-progress"></div></div>
          <div class="ref-line">{''.join(timeline_items)}</div>
        </div>
      </div>
      <div class="control-panel">
        <div class="ref-panel-title">Matriz PMO de hitos</div>
        <div class="matrix-summary">
          <div class="summary-tile"><small>Hitos críticos</small><b>{critical_count}</b></div>
          <div class="summary-tile"><small>CAPEX comprometido</small><b>{format_clp_mm(total)}</b></div>
          <div class="summary-tile"><small>Brecha operacional</small><b>{format_clp_mm(float(metrics["breach"]))}</b></div>
          <div class="summary-tile"><small>Riesgo PMO</small><b>{html.escape(risk)}</b></div>
          <div class="summary-tile"><small>Próximo desbloqueo</small><b>{html.escape(next_unlock)}</b></div>
        </div>
        <div class="matrix-scroll">
          <table class="pmo-matrix">
            <thead>
              <tr>
                <th>Hito</th><th>Estado</th><th>Criticidad</th><th>Hito ejecutivo</th><th>Etapa</th><th>Impacto operativo</th><th>Indicador PMO</th>
                <th>Av. financiero</th><th>Ejecución</th><th>CAPEX restante</th><th>Duración</th><th>Inicio</th><th>Término</th><th>Escenario</th><th>Decisión requerida</th>
              </tr>
            </thead>
            <tbody>{''.join(matrix_rows)}</tbody>
          </table>
        </div>
        <div class="matrix-foot"><span>Fuente: Matriz PMO de hitos</span><span>Criticidad: <b style="color:#E11D48;">● Alta</b> <b style="color:#F59E0B;">● Media</b> <b style="color:#10B981;">● Baja</b></span></div>
      </div>
    </div>
    """
    components.html(html_doc, height=1020, scrolling=True)


def hitos_executive_reading(df: pd.DataFrame, hito_summary: pd.DataFrame) -> str:
    total = float(df["Monto CLP Num"].sum() or 0)
    concentration = hito_summary.sort_values("Monto_CLP", ascending=False).head(1)
    concentration_text = "sin concentración dominante"
    if not concentration.empty and total:
        row = concentration.iloc[0]
        concentration_text = f"{row['Hito Corto']} concentra {format_pct(row['Monto_CLP'] / total)} del CAPEX restante"
    critical = hito_summary.sort_values(["Monto_CLP", "Duracion_habil"], ascending=False).head(3)["Hito Corto"].tolist()
    next_disbursements = df[~df["Pendiente programación"]].sort_values("Inicio").head(4)
    next_txt = "; ".join(f"{r['ID']} {format_clp(r['Total Liberación Num'])}" for _, r in next_disbursements.iterrows())
    unlock = df[df["Es habilitante"]].sort_values(["Inicio", "Monto CLP Num"], ascending=[True, False]).head(3)
    unlock_txt = ", ".join(unlock["Hito Corto"].dropna().unique().tolist()) or "sin habilitantes detectados"
    return (
        f"Lectura PMO: {concentration_text}. Los hitos que requieren mayor gobierno ejecutivo son "
        f"{', '.join(critical)} por exposición financiera, duración y dependencia operacional. "
        f"Los próximos desembolsos visibles son {next_txt}. Los frentes que destraban puesta en marcha son "
        f"{unlock_txt}; su control reduce riesgo tecnológico al asegurar continuidad entre fundación, integración, "
        "protecciones, instrumentación y comisionamiento."
    )


def render_hitos_financial_view(
    df: pd.DataFrame,
    hito_summary: pd.DataFrame,
    pmo_source: pd.DataFrame | None = None,
) -> None:
    metrics = pmo_financial_metrics(df, hito_summary, pmo_source)
    matrix = metrics["matrix"].copy()
    current = metrics["current_row"]
    next_row = metrics["next_row"]
    total = float(metrics["total_capex"])
    current_total = float(current.get("Total_Liberacion", 0) or 0)
    cons = float(current.get("Liberacion_Inicial", 0) or 0)
    base = cons + float(current.get("Liberacion_Avance", 0) or 0)
    close = current_total
    today_label = pd.Timestamp("today").strftime("%d-%m-%Y %H:%M")
    concentration = hito_summary.sort_values("Monto_CLP", ascending=False).head(2)
    concentration_txt = " y ".join(concentration["Hito"].astype(str).tolist()) if not concentration.empty else "-"
    current_hito_label = str(current.get("Hito", "H1"))
    next_hito_label = str(next_row.get("Hito", "H2"))
    launch_date = metrics["launch_date"]
    risk = str(metrics["risk"]).upper()
    risk_color = {"ALTO": "#E11D48", "MEDIO": "#F59E0B", "BAJO": "#10B981"}.get(risk, "#F59E0B")
    technical_pct = float(metrics["technical_progress"])

    def ref_kpi(label: str, value: str, note: str, icon: str, accent: str, variant: str = "") -> str:
        return f"""
        <div class="ref-kpi {variant}" style="--accent:{accent};">
          <div class="ref-kpi-icon">{html.escape(icon)}</div>
          <div class="ref-kpi-copy">
            <div class="ref-kpi-label">{html.escape(label)}</div>
            <div class="ref-kpi-value">{html.escape(value)}</div>
            <div class="ref-kpi-note">{html.escape(note)}</div>
          </div>
        </div>
        """

    def kpi_group(title: str, color: str, cards: list[str], variant: str = "") -> str:
        return f"""
        <div class="kpi-group {variant}" style="--group:{color};">
          <div class="kpi-group-head">
            <span></span>
            <b>{html.escape(title)}</b>
          </div>
          <div class="kpi-group-grid">{''.join(cards)}</div>
        </div>
        """

    def scenario(
        title: str,
        subtitle: str,
        amount: float,
        percent: float,
        bullets: list[str],
        delay_risk: str,
        runway: str,
        color: str,
        featured: bool = False,
    ) -> str:
        coverage = min(max(percent * 100, 0), 100)
        initial_on = percent > 0
        advance_on = percent >= 0.50
        close_on = percent >= 0.99
        bullet_html = "".join(f"<li>{html.escape(item)}</li>" for item in bullets[:3])
        return f"""
        <div class="ref-scenario {'featured' if featured else ''}" style="--scenario:{color};">
          {'<div class="scenario-tag">RECOMENDADO</div>' if featured else ''}
          <div class="ref-scenario-head">
            <div class="scenario-shield">◇</div>
            <div>
              <b>{html.escape(title)}</b>
              <span>{html.escape(subtitle)}</span>
            </div>
          </div>
          <div class="scenario-amount">{format_clp(amount)}</div>
          <div class="scenario-metrics">
            <div><span>{coverage:.0f}%</span><small>continuidad</small></div>
            <div><span>{html.escape(delay_risk)}</span><small>riesgo retraso</small></div>
            <div><span>{html.escape(runway)}</span><small>runway</small></div>
          </div>
          <div class="scenario-coverage">
            <div class="coverage-label"><span>Cobertura operacional</span><b>{coverage:.0f}%</b></div>
            <div class="coverage-track"><div style="width:{coverage:.0f}%;background:{color};"></div></div>
          </div>
          <div class="scenario-mini-timeline">
            <span class="{'on' if initial_on else ''}">Inicial</span>
            <span class="{'on' if advance_on else ''}">Avance</span>
            <span class="{'on' if close_on else ''}">Cierre</span>
          </div>
          <ul class="scenario-bullets">{bullet_html}</ul>
        </div>
        """

    timeline_items = []
    critical_hitos = {"H1", "H4", "H8"}
    status_label = {"Ejecutado": "Ejecutado", "En curso": "En curso", "Pendiente": "Pendiente"}
    status_color = {"Ejecutado": "#10B981", "En curso": "#2F80ED", "Pendiente": "#94A3B8"}
    timeline_matrix = matrix.sort_values("Hito Orden").copy()
    timeline_start = timeline_matrix["_Inicio"].dropna().min() if "_Inicio" in timeline_matrix else pd.NaT
    timeline_end = timeline_matrix["_Termino"].dropna().max() if "_Termino" in timeline_matrix else pd.NaT
    today_dt = pd.Timestamp("today").normalize()
    today_pos = 0.0
    if pd.notna(timeline_start) and pd.notna(timeline_end) and timeline_end > timeline_start:
        today_pos = float((today_dt - timeline_start).days / max((timeline_end - timeline_start).days, 1))
        today_pos = min(max(today_pos, 0.0), 1.0) * 100
    progress_width = min(max(technical_pct * 100, 2), 100)
    previous_hito = ""
    for _, row in timeline_matrix.iterrows():
        crit = str(row.get("Criticidad", "Media"))
        stt = str(row.get("Estado", "Pendiente"))
        hito_code = str(row.get("Hito", "-"))
        is_critical = hito_code in critical_hitos
        dot_color = "#EF4444" if is_critical else status_color.get(stt, "#94A3B8")
        dependency = "Inicio del programa" if not previous_hito else f"Depende de cierre técnico y financiero de {previous_hito}"
        previous_hito = hito_code
        tooltip = f"""
          <div class="decision-tooltip">
            <b>{html.escape(hito_code)} · {html.escape(str(row.get("Hito Corto", "-")))}</b>
            <span>CAPEX asociado: {html.escape(str(row.get("Monto total", "-")))}</span>
            <span>Riesgo: {'Crítico' if is_critical else html.escape(crit)}</span>
            <span>Dependencia: {html.escape(dependency)}</span>
            <span>Fondos requeridos: {html.escape(str(row.get("Total Liberación", "-")))}</span>
          </div>
        """
        timeline_items.append(
            f"""
            <div class="ref-mile {'critical' if is_critical else ''}">
              <div class="ref-node" style="background:{dot_color};">{html.escape(hito_code)}</div>
              {tooltip}
              <div class="ref-mile-title">{html.escape(str(row['Hito Corto']))}</div>
              <div class="ref-mile-status" style="color:{dot_color};background:{dot_color}18;">{html.escape(status_label.get(stt, stt).upper())}</div>
            </div>
            """
        )

    executive_text = (
        f"El cronograma presenta un CAPEX restante de {format_clp(total)}, concentrado principalmente en los hitos {concentration_txt}. "
        f"El avance técnico ponderado alcanza {format_pct(technical_pct)}, mientras que la liberación financiera estimada se mantiene en "
        f"{format_pct(float(metrics['financial_progress']))}, generando una brecha de continuidad operacional de {format_clp(float(metrics['breach']))}. "
        "Se recomienda priorizar la liberación inicial del hito actual y asegurar fondos de avance para evitar desaceleración en ingeniería, fabricación e integración."
    )
    memo_blocks = [
        (
            "Diagnóstico",
            f"CAPEX restante de {format_clp(total)} concentrado en {concentration_txt}; avance técnico ponderado de {format_pct(technical_pct)}.",
        ),
        (
            "Riesgo",
            f"Brecha de continuidad por {format_clp(float(metrics['breach']))}; riesgo PMO actual {risk.lower()}.",
        ),
        (
            "Decisión requerida",
            f"Liberar fondos iniciales del {current_hito_label} y asegurar avance para sostener ingeniería e integración.",
        ),
        (
            "Próximo paso",
            f"Validar condición de liberación del {current_hito_label} y preparar transición hacia {next_hito_label}.",
        ),
    ]
    memo_html = "".join(
        f"""
        <div class="memo-row">
          <b>{html.escape(title)}</b>
          <p>{html.escape(body)}</p>
        </div>
        """
        for title, body in memo_blocks
    )

    def format_clp_mm(value: float) -> str:
        return f"${value / 1_000_000:.1f}MM".replace(".", ",")

    def impact_for(row: pd.Series) -> str:
        hito = str(row.get("Hito", ""))
        share = float(row.get("% sobre total", 0) or 0)
        crit = str(row.get("Criticidad", "Media"))
        if hito in {"H1", "H4", "H8"}:
            return "Crítico"
        if crit == "Alta" or share >= 0.20:
            return "Alto"
        if crit == "Media" or share >= 0.08:
            return "Medio"
        return "Bajo"

    def impact_class(value: str) -> str:
        return {"Crítico": "red", "Alto": "amber", "Medio": "blue", "Bajo": "green"}.get(value, "gray")

    def pmo_signal(row: pd.Series, impact: str) -> tuple[str, str]:
        state = str(row.get("Estado", "Pendiente"))
        if impact == "Crítico" or str(row.get("Criticidad", "")) == "Alta":
            return "Riesgo PMO", "red"
        if state == "En curso" or impact in {"Alto", "Medio"}:
            return "Seguimiento", "amber"
        return "En control", "green"

    def bar_cell(value: float, color: str, label: str) -> str:
        width = min(max(value, 0), 100)
        return f"""
        <div class="matrix-bar">
          <span>{html.escape(label)}</span>
          <div><i style="width:{width:.0f}%;background:{color};"></i></div>
        </div>
        """

    matrix_preview = matrix.sort_values("Hito Orden").copy()
    if matrix_preview.empty:
        matrix_preview = matrix.sort_values(["Criticidad", "Monto_CLP"], ascending=[True, False]).copy()

    matrix_rows = []
    for _, row in matrix_preview.iterrows():
        state = str(row.get("Estado", "Pendiente"))
        crit = str(row.get("Criticidad", "Media"))
        scenario_name = str(row.get("Escenario recomendado", "Base")).upper()
        hito_code = str(row.get("Hito", "-"))
        is_strategic = hito_code in {"H1", "H4", "H8"}
        impact = impact_for(row)
        signal, signal_class = pmo_signal(row, impact)
        capex_pct = float(row.get("% sobre total", 0) or 0) * 100
        execution_pct = float(row.get("Avance_promedio", 0) or 0) * 100
        financial_pct = {"CONSERVADOR": 30, "BASE": 80, "CIERRE": 100}.get(scenario_name, 30)
        capex_value = float(row.get("Monto_CLP", 0) or 0)
        duration = int(float(row.get("Duracion_habil", 0) or 0))
        state_class = "blue" if state == "En curso" else "gray"
        crit_class = "red" if crit in {"Alta", "Crítica"} else "amber" if crit == "Media" else "green"
        scen_class = "green" if scenario_name == "CIERRE" else "blue" if scenario_name == "BASE" else "amber"
        matrix_rows.append(
            f"""
            <tr class="{'strategic-row' if is_strategic else ''} heat-{impact_class(impact)}">
              <td class="sticky-col col-hito"><span class="hito-code">{html.escape(hito_code)}</span></td>
              <td class="sticky-col col-state"><span class="matrix-pill {state_class}">{html.escape(state)}</span></td>
              <td class="sticky-col col-risk"><span class="matrix-pill {crit_class}">{html.escape(crit)}</span></td>
              <td class="matrix-name"><b>{html.escape(str(row.get("Hito ejecutivo", row.get("Hito Ejecutivo", "-"))))}</b><small>{html.escape(str(row.get("Condición de Liberación", "-")))}</small></td>
              <td><span class="matrix-pill blue">{html.escape(str(row.get("Etapa del hito", "-")))}</span></td>
              <td><span class="matrix-pill {impact_class(impact)}">{html.escape(impact)}</span></td>
              <td><span class="signal {signal_class}"><i></i>{html.escape(signal)}</span></td>
              <td>{bar_cell(financial_pct, "#2F80ED", f"{financial_pct:.0f}%")}</td>
              <td>{bar_cell(execution_pct, "#0F766E", f"{execution_pct:.0f}%")}</td>
              <td>{bar_cell(capex_pct, "#F59E0B", format_clp_mm(capex_value))}</td>
              <td>{duration} días</td>
              <td>{html.escape(format_date(row.get("_Inicio", row.get("Inicio", "-"))))}</td>
              <td>{html.escape(format_date(row.get("_Termino", row.get("Termino", "-"))))}</td>
              <td><span class="matrix-pill {scen_class}">{html.escape(scenario_name)}</span></td>
              <td class="decision-cell">{html.escape(str(row.get("Decisión requerida", "-")))}</td>
            </tr>
            """
        )
    critical_30 = float(metrics.get("funds_30", current_total) or 0)
    critical_60 = float(metrics.get("funds_60", current_total) or 0)
    current_share = (current_total / total) if total else 0.0
    remaining_share = total / (total + float(metrics.get("committed", 0) or 0)) if total else 0.0
    hitos_30 = int((matrix["_Inicio"].between(pd.Timestamp("today").normalize(), pd.Timestamp("today").normalize() + pd.Timedelta(days=30), inclusive="both")).sum())
    hitos_60 = int((matrix["_Inicio"].between(pd.Timestamp("today").normalize(), pd.Timestamp("today").normalize() + pd.Timedelta(days=60), inclusive="both")).sum())
    launch_remaining = "-"
    if pd.notna(launch_date):
        launch_remaining = f"{max((pd.Timestamp(launch_date).normalize() - pd.Timestamp('today').normalize()).days, 0)} días restantes"

    critical_count = int(matrix["Hito"].astype(str).isin(["H1", "H4", "H8"]).sum())
    next_unlock = "H2"
    if isinstance(next_row, pd.Series) and not next_row.empty:
        next_unlock = str(next_row.get("Hito", "H2"))
    decision_cards = [
        {
            "tone": "red",
            "icon": "!",
            "title": "Aprobación H1",
            "subtitle": "Liberación inicial para continuidad técnica",
            "amount": format_clp_mm(cons),
            "deadline": "Inmediato",
            "dependency": "Equipo técnico y PMO",
            "risk": "Crítico",
            "cta": "Requiere aprobación",
        },
        {
            "tone": "amber",
            "icon": "✓",
            "title": "Validar transición",
            "subtitle": f"Dependencias antes de {next_unlock}",
            "amount": format_clp_mm(critical_30),
            "deadline": "30 días",
            "dependency": "Ruta técnica crítica",
            "risk": "Seguimiento",
            "cta": "Validación técnica",
        },
        {
            "tone": "green",
            "icon": "↗",
            "title": "Control PMO",
            "subtitle": "Seguimiento de continuidad operacional",
            "amount": format_clp_mm(critical_60),
            "deadline": "60 días",
            "dependency": "Fondos avance y cierre",
            "risk": risk.title(),
            "cta": "Seguimiento PMO",
        },
    ]
    decision_cards_html = "".join(
        f"""
        <div class="decision-card {card['tone']}">
          <div class="semaphore"></div>
          <div class="decision-icon">{html.escape(card['icon'])}</div>
          <div class="decision-copy">
            <b>{html.escape(card['title'])}</b>
            <p>{html.escape(card['subtitle'])}</p>
            <div class="decision-meta">
              <span><small>Monto</small>{html.escape(card['amount'])}</span>
              <span><small>Plazo</small>{html.escape(card['deadline'])}</span>
              <span><small>Riesgo</small>{html.escape(card['risk'])}</span>
            </div>
            <div class="decision-dep">Dependencia: {html.escape(card['dependency'])}</div>
            <div class="decision-cta">{html.escape(card['cta'])}</div>
          </div>
        </div>
        """
        for card in decision_cards
    )

    html_doc = f"""
        <style>
        *{{box-sizing:border-box;}}
        body{{margin:0;background:transparent;overflow-x:hidden;}}
        .ref-wrap{{background:#F7F9FC;border:1px solid #E1E8EF;border-radius:8px;padding:22px 0 24px 0;color:#0B1633;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;overflow-x:hidden;}}
        .dashboard-shell{{max-width:1450px;margin:0 auto;padding:0 24px;overflow-x:hidden;}}
        .ref-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;}}
        .ref-title{{font-size:30px;font-weight:900;color:#0B1633;line-height:1.05;margin:0;}}
        .ref-sub{{font-size:14px;color:#607086;margin-top:9px;}}
        .ref-actions{{display:flex;gap:14px;align-items:center;color:#607086;font-size:11px;}}
        .ref-filter{{border:1px solid #D7E0EA;border-radius:7px;background:#FFFFFF;padding:9px 14px;font-weight:800;color:#25364F;}}
        .ref-band{{display:grid;grid-template-columns:1.15fr 1.15fr 1fr 2.75fr;gap:24px;background:linear-gradient(135deg,#08253B,#0B3554);border-radius:16px;padding:20px 30px;color:#FFFFFF;box-shadow:0 18px 38px rgba(8,37,59,.22);margin-bottom:18px;}}
        .ref-band-block{{border-right:1px solid rgba(255,255,255,.24);padding-right:20px;min-height:76px;}}
        .ref-band-block:last-child{{border-right:0;}}
        .ref-band-k{{font-size:11px;color:#B8C9D8;font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;}}
        .ref-hito{{display:flex;align-items:center;gap:14px;}}
        .ref-hito-code{{font-size:34px;font-weight:900;color:#B8C9D8;line-height:1;}}
        .ref-hito-name{{font-size:14px;line-height:1.3;color:#FFFFFF;font-weight:650;}}
        .ref-next-date{{font-size:14px;color:#B8C9D8;margin-top:16px;}}
        .ref-badge{{display:inline-flex;margin-top:9px;border-radius:999px;padding:5px 12px;background:#14B8A6;color:#FFFFFF;font-size:11px;font-weight:900;}}
        .ref-critical{{font-size:24px;font-weight:900;color:#FF5B6E;display:flex;gap:12px;align-items:center;}}
        .ref-rec{{font-size:13px;line-height:1.45;color:#FFFFFF;max-width:560px;}}
        .ref-action-badge{{display:inline-flex;margin-top:10px;background:#FBBF24;color:#1F2937;border-radius:999px;padding:8px 14px;font-size:12px;font-weight:950;box-shadow:0 10px 20px rgba(251,191,36,.24);}}
        .ref-kpi-groups{{display:grid;grid-template-columns:1.35fr .95fr .7fr 1fr;gap:18px;margin-bottom:16px;min-width:0;}}
        .kpi-group{{background:#FFFFFF;border:1px solid #E2E8F0;border-top:3px solid var(--group);border-radius:14px;padding:12px;box-shadow:0 12px 24px rgba(15,23,42,.052);}}
        .kpi-group.priority{{box-shadow:0 16px 34px rgba(15,23,42,.075);}}
        .kpi-group-head{{display:flex;align-items:center;gap:8px;margin:0 0 10px 2px;}}
        .kpi-group-head span{{width:9px;height:9px;border-radius:999px;background:var(--group);display:inline-block;}}
        .kpi-group-head b{{font-size:12px;color:#25364F;font-weight:850;letter-spacing:0;}}
        .kpi-group-grid{{display:grid;grid-template-columns:repeat(1,minmax(0,1fr));gap:10px;}}
        .kpi-group.priority .kpi-group-grid{{grid-template-columns:repeat(3,minmax(0,1fr));}}
        .kpi-group.urgency .kpi-group-grid,.kpi-group.risk-group .kpi-group-grid{{grid-template-columns:repeat(2,minmax(0,1fr));}}
        .ref-kpi{{position:relative;display:grid;grid-template-columns:34px 1fr;gap:10px;background:#FBFCFE;border:1px solid #E8EEF5;border-radius:12px;padding:13px 12px;min-height:94px;box-shadow:none;overflow:hidden;transition:transform .18s ease,box-shadow .18s ease;}}
        .ref-kpi::after{{content:"";position:absolute;right:-35px;top:-40px;width:92px;height:92px;background:var(--accent);opacity:.045;border-radius:999px;}}
        .ref-kpi:hover{{transform:translateY(-2px);box-shadow:0 18px 32px rgba(15,23,42,.08);}}
        .ref-kpi-icon{{width:31px;height:31px;border-radius:999px;background:var(--accent);color:#FFFFFF;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:900;box-shadow:0 10px 18px rgba(15,23,42,.10);}}
        .ref-kpi-label{{font-size:10px;font-weight:800;color:#41516B;letter-spacing:0;line-height:1.25;min-height:22px;}}
        .ref-kpi-value{{font-size:17px;font-weight:950;color:#0B1633;line-height:1.1;margin-top:8px;white-space:nowrap;}}
        .kpi-group.priority .ref-kpi-value{{font-size:18px;}}
        .ref-kpi-note{{font-size:10px;color:#52647A;line-height:1.35;margin-top:7px;}}
        .ref-kpi.risk .ref-kpi-value{{color:#E11D48;font-size:20px;letter-spacing:.02em;}}
        .pmo-flow{{width:100%;max-width:100%;margin:0 auto;display:grid;gap:14px;min-width:0;overflow-x:hidden;}}
        .ref-main{{display:grid;grid-template-columns:.36fr .64fr;gap:14px;margin:0;align-items:stretch;width:100%;min-width:0;}}
        .ref-panel,.control-panel{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:18px 20px;box-shadow:0 12px 24px rgba(15,23,42,.05);}}
        .ref-panel-title{{font-size:14px;font-weight:850;color:#23457A;letter-spacing:0;margin-bottom:14px;}}
        .memo-card{{background:linear-gradient(145deg,#FFFFFF,#FAFCFF);}}
        .memo-row{{border-bottom:1px solid #E8EEF5;padding:9px 0;}}
        .memo-row:first-of-type{{padding-top:0;}}
        .memo-row:last-child{{border-bottom:0;padding-bottom:0;}}
        .memo-row b{{display:block;font-size:12px;color:#0B2D42;margin-bottom:4px;}}
        .memo-row p{{font-size:12px;line-height:1.45;color:#334155;margin:0;}}
        .ref-scenarios{{display:grid;grid-template-columns:.9fr 1.2fr .9fr;gap:14px;align-items:stretch;min-width:0;}}
        .ref-scenario{{position:relative;border:1px solid #DCE6F0;border-top:4px solid var(--scenario);border-radius:14px;background:linear-gradient(145deg,#FFFFFF,#FCFEFF);padding:16px 18px 14px 18px;min-height:244px;box-shadow:0 12px 24px rgba(15,23,42,.045);}}
        .ref-scenario.featured{{border:2px solid #2F80ED;border-top-width:4px;box-shadow:0 0 0 5px rgba(47,128,237,.10),0 24px 52px rgba(47,128,237,.22);transform:translateY(-5px);}}
        .scenario-tag{{position:absolute;right:14px;top:12px;background:#2F80ED;color:#FFFFFF;border-radius:999px;padding:6px 11px;font-size:10px;font-weight:950;letter-spacing:.02em;box-shadow:0 9px 18px rgba(47,128,237,.22);}}
        .ref-scenario-head{{display:flex;gap:13px;align-items:center;color:#0B1633;}}
        .scenario-shield{{width:34px;height:34px;border-radius:999px;border:3px solid var(--scenario);color:var(--scenario);display:flex;align-items:center;justify-content:center;font-weight:900;background:#FFFFFF;}}
        .ref-scenario-head b{{font-size:16px;}}
        .ref-scenario-head span{{display:block;font-size:12px;color:#52647A;margin-top:2px;}}
        .scenario-amount{{font-size:23px;color:#0B1633;font-weight:950;margin-top:15px;letter-spacing:-.01em;}}
        .scenario-metrics{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-top:12px;}}
        .scenario-metrics div{{background:#F8FAFC;border:1px solid #E8EEF5;border-radius:9px;padding:8px 6px;min-width:0;}}
        .scenario-metrics span{{display:block;font-size:12px;font-weight:950;color:#0B1633;line-height:1.1;white-space:normal;word-break:break-word;}}
        .scenario-metrics small{{display:block;font-size:9px;color:#64748B;margin-top:4px;line-height:1.15;}}
        .scenario-coverage{{margin-top:13px;}}
        .coverage-label{{display:flex;justify-content:space-between;align-items:center;font-size:10px;color:#52647A;font-weight:800;}}
        .coverage-label b{{color:#0B1633;}}
        .coverage-track{{height:8px;background:#E2E8F0;border-radius:999px;overflow:hidden;margin-top:6px;}}
        .coverage-track div{{height:100%;border-radius:999px;box-shadow:0 7px 14px rgba(15,23,42,.12);}}
        .scenario-mini-timeline{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:12px;}}
        .scenario-mini-timeline span{{height:24px;border-radius:999px;background:#EDF2F7;color:#64748B;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:850;}}
        .scenario-mini-timeline span.on{{background:#FFFFFF;color:var(--scenario);box-shadow:inset 0 0 0 1px var(--scenario);}}
        .scenario-bullets{{margin:12px 0 0 0;padding-left:16px;color:#25364F;font-size:11px;line-height:1.42;}}
        .scenario-bullets li{{margin:3px 0;}}
        .control-stack{{display:grid;gap:14px;margin:0;width:100%;min-width:0;overflow-x:hidden;}}
        .control-panel{{overflow:hidden;min-width:0;}}
        .ref-timeline{{margin-bottom:0;}}
        .timeline-head{{display:flex;justify-content:space-between;gap:16px;align-items:center;min-width:0;}}
        .timeline-legend{{display:flex;gap:16px;align-items:center;font-size:11px;color:#334155;flex-wrap:wrap;justify-content:flex-end;}}
        .legend-dot{{display:inline-block;width:12px;height:12px;border-radius:999px;margin-right:6px;vertical-align:-1px;}}
        .ref-stage{{display:grid;grid-template-columns:1.45fr 3.2fr 2.1fr;gap:10px;margin:10px 0 22px 0;}}
        .ref-stage div{{height:28px;border-radius:8px;font-size:11px;font-weight:850;display:flex;align-items:center;justify-content:center;color:#334155;}}
        .decision-roadmap{{position:relative;padding:22px 6px 8px 6px;overflow:visible;max-width:100%;}}
        .today-line{{position:absolute;top:2px;bottom:16px;left:var(--today);width:2px;background:#EF4444;z-index:5;box-shadow:0 0 0 4px rgba(239,68,68,.10);}}
        .today-line span{{position:absolute;top:-22px;left:50%;transform:translateX(-50%);background:#EF4444;color:#FFFFFF;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:900;white-space:nowrap;}}
        .decision-track{{position:absolute;left:18px;right:18px;top:44px;height:6px;border-radius:999px;background:#E2E8F0;box-shadow:inset 0 1px 2px rgba(15,23,42,.06);}}
        .decision-progress{{height:100%;width:var(--progress);border-radius:999px;background:linear-gradient(90deg,#0F766E,#2F80ED);box-shadow:0 6px 14px rgba(47,128,237,.18);}}
        .ref-line{{position:relative;display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:8px;padding-top:0;margin-top:22px;z-index:10;}}
        .ref-mile{{text-align:center;position:relative;min-height:96px;overflow:visible;}}
        .ref-node{{width:38px;height:38px;border-radius:999px;color:#FFFFFF;font-weight:900;display:flex;align-items:center;justify-content:center;margin:0 auto 10px auto;box-shadow:0 7px 14px rgba(15,23,42,.18);position:relative;z-index:3;}}
        .ref-mile.critical .ref-node{{width:46px;height:46px;margin-top:-4px;margin-bottom:6px;box-shadow:0 0 0 8px rgba(239,68,68,.12),0 15px 30px rgba(239,68,68,.24);}}
        .ref-mile.critical .ref-node::after{{content:"";position:absolute;inset:-11px;border-radius:999px;border:1px solid rgba(239,68,68,.32);}}
        .ref-mile-title{{font-size:11px;color:#243B53;line-height:1.22;min-height:30px;max-width:118px;margin:0 auto;font-weight:750;}}
        .ref-mile-status{{display:inline-flex;border-radius:999px;padding:4px 8px;font-size:9px;font-weight:900;margin-top:7px;}}
        .decision-tooltip{{position:absolute;z-index:40;left:50%;bottom:92px;transform:translateX(-50%) translateY(6px);width:210px;background:#08253B;color:#FFFFFF;border-radius:10px;padding:12px 13px;text-align:left;box-shadow:0 18px 38px rgba(8,37,59,.28);opacity:0;pointer-events:none;transition:opacity .16s ease,transform .16s ease;}}
        .decision-tooltip::after{{content:"";position:absolute;left:50%;bottom:-7px;transform:translateX(-50%);border-left:7px solid transparent;border-right:7px solid transparent;border-top:7px solid #08253B;}}
        .decision-tooltip b{{display:block;font-size:12px;margin-bottom:8px;color:#FFFFFF;}}
        .decision-tooltip span{{display:block;font-size:11px;line-height:1.35;color:#DDE8F3;margin-top:4px;}}
        .ref-mile:hover .decision-tooltip{{opacity:1;transform:translateX(-50%) translateY(0);}}
        .ref-decisions{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;min-width:0;}}
        .decision-card{{position:relative;display:grid;grid-template-columns:42px 1fr;gap:11px;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;padding:13px 13px 13px 17px;box-shadow:0 10px 20px rgba(15,23,42,.045);overflow:hidden;min-height:154px;}}
        .decision-card .semaphore{{position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--tone);}}
        .decision-card.red{{--tone:#E11D48;}}
        .decision-card.amber{{--tone:#F59E0B;}}
        .decision-card.green{{--tone:#10B981;}}
        .decision-icon{{width:38px;height:38px;border-radius:12px;background:color-mix(in srgb,var(--tone) 14%,#FFFFFF);color:var(--tone);display:flex;align-items:center;justify-content:center;font-size:19px;font-weight:950;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--tone) 28%,#FFFFFF);}}
        .decision-copy b{{display:block;font-size:13px;color:#0B1633;line-height:1.15;}}
        .decision-copy p{{font-size:11px;color:#475569;line-height:1.35;margin:4px 0 9px 0;}}
        .decision-meta{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;}}
        .decision-meta span{{background:#F8FAFC;border:1px solid #E8EEF5;border-radius:8px;padding:6px 7px;font-size:11px;font-weight:900;color:#0B1633;}}
        .decision-meta small{{display:block;font-size:8px;text-transform:uppercase;letter-spacing:.04em;color:#64748B;margin-bottom:2px;}}
        .decision-dep{{font-size:10px;color:#64748B;margin-top:8px;}}
        .decision-cta{{display:inline-flex;margin-top:8px;border-radius:999px;padding:5px 9px;background:var(--tone);color:#FFFFFF;font-size:10px;font-weight:950;}}
        .matrix-summary{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-bottom:12px;min-width:0;}}
        .summary-tile{{background:linear-gradient(145deg,#FFFFFF,#F9FBFD);border:1px solid #E2E8F0;border-radius:12px;padding:10px 12px;box-shadow:0 10px 20px rgba(15,23,42,.045);}}
        .summary-tile small{{display:block;font-size:9px;text-transform:uppercase;letter-spacing:.04em;color:#64748B;font-weight:850;}}
        .summary-tile b{{display:block;font-size:16px;color:#0B1633;margin-top:5px;}}
        .matrix-scroll{{overflow-x:hidden;overflow-y:auto;border:1px solid #E2E8F0;border-radius:12px;max-height:520px;background:#FFFFFF;width:100%;}}
        .pmo-matrix{{width:100%;min-width:0;table-layout:fixed;border-collapse:separate;border-spacing:0;background:#FFFFFF;font-size:9px;color:#0B1633;}}
        .pmo-matrix th{{position:sticky;top:0;z-index:20;background:#F8FAFC;color:#334155;font-size:8px;letter-spacing:0;border-bottom:1px solid #DCE6EF;padding:9px 5px;text-align:center;white-space:normal;line-height:1.15;word-break:break-word;}}
        .pmo-matrix td{{border-bottom:1px solid #EEF3F7;padding:10px 5px;text-align:center;vertical-align:middle;background:#FFFFFF;line-height:1.22;word-break:break-word;}}
        .pmo-matrix tr:hover td{{background:#F8FBFF;}}
        .pmo-matrix .sticky-col{{position:static;z-index:15;background:inherit;box-shadow:none;}}
        .pmo-matrix th.sticky-col{{z-index:25;}}
        .col-hito{{width:4.2%;}}
        .col-state{{width:7%;}}
        .col-risk{{width:7%;}}
        .matrix-name{{text-align:left!important;width:17%;}}
        .matrix-name b{{display:block;font-size:10px;color:#0B1633;line-height:1.2;}}
        .matrix-name small{{display:block;font-size:8px;color:#64748B;line-height:1.2;margin-top:3px;}}
        .strategic-row td{{background:#FFFBF5;}}
        .hito-code{{display:inline-flex;align-items:center;justify-content:center;width:30px;height:26px;border-radius:9px;background:#0B2D42;color:#FFFFFF;font-size:12px;font-weight:950;}}
        .strategic-row .hito-code{{background:#E11D48;box-shadow:0 0 0 5px rgba(225,29,72,.10);}}
        .matrix-pill{{display:inline-flex;border-radius:5px;padding:4px 6px;font-size:8px;font-weight:950;white-space:normal;justify-content:center;}}
        .matrix-pill.blue{{background:#DBEAFE;color:#2563EB;}}
        .matrix-pill.gray{{background:#E2E8F0;color:#64748B;}}
        .matrix-pill.red{{background:#FEE2E2;color:#E11D48;}}
        .matrix-pill.amber{{background:#FEF3C7;color:#D97706;}}
        .matrix-pill.green{{background:#D1FAE5;color:#047857;}}
        .signal{{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:5px 7px;font-size:8px;font-weight:900;white-space:normal;justify-content:center;}}
        .signal i{{width:8px;height:8px;border-radius:999px;display:inline-block;}}
        .signal.green{{background:#D1FAE5;color:#047857;}}.signal.green i{{background:#10B981;}}
        .signal.amber{{background:#FEF3C7;color:#B45309;}}.signal.amber i{{background:#F59E0B;}}
        .signal.red{{background:#FEE2E2;color:#BE123C;}}.signal.red i{{background:#E11D48;}}
        .matrix-bar{{text-align:left;}}
        .matrix-bar span{{display:block;font-size:8px;color:#334155;font-weight:900;margin-bottom:5px;}}
        .matrix-bar div{{height:7px;background:#E2E8F0;border-radius:999px;overflow:hidden;}}
        .matrix-bar i{{display:block;height:100%;border-radius:999px;}}
        .decision-cell{{text-align:left!important;color:#334155;line-height:1.25;}}
        .heat-red td{{box-shadow:inset 0 0 0 999px rgba(225,29,72,.018);}}
        .heat-amber td{{box-shadow:inset 0 0 0 999px rgba(245,158,11,.018);}}
        .heat-blue td{{box-shadow:inset 0 0 0 999px rgba(47,128,237,.014);}}
        .matrix-foot{{font-size:10px;color:#64748B;margin-top:10px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;}}
        @media(max-width:1320px){{.ref-kpi-groups{{grid-template-columns:1fr 1fr;}}.ref-band{{grid-template-columns:1fr 1fr;}}.ref-band-block:nth-child(2){{border-right:0;}}.ref-scenarios{{grid-template-columns:1fr;}}}}
        @media(max-width:1200px){{.ref-main{{grid-template-columns:1fr;}}.ref-decisions{{grid-template-columns:1fr;}}.matrix-summary{{grid-template-columns:1fr 1fr;}}}}
        </style>
        <div class="ref-wrap">
          <div class="dashboard-shell">
            <div class="ref-top">
              <div>
                <h2 class="ref-title">Vista Ejecutiva de Hitos y Liberación de Fondos</h2>
                <div class="ref-sub">Seguimiento PMO del piloto 10 kW: avance técnico, CAPEX pendiente y escenarios de continuidad</div>
              </div>
              <div class="ref-actions"><div class="ref-filter">▽ Filtros</div><span>Actualizado: {html.escape(today_label)}</span></div>
            </div>
            <div class="ref-band">
              <div class="ref-band-block">
                <div class="ref-band-k">Hito actual</div>
                <div class="ref-hito"><div class="ref-hito-code">{html.escape(current_hito_label)}</div><div class="ref-hito-name">{html.escape(str(current.get("Hito Corto", "-")))}</div></div>
                <div class="ref-badge">{html.escape(str(current.get("Estado", "-")).upper())}</div>
              </div>
              <div class="ref-band-block">
                <div class="ref-band-k">Próximo hito</div>
                <div class="ref-hito"><div class="ref-hito-code">{html.escape(next_hito_label)}</div><div class="ref-hito-name">{html.escape(str(next_row.get("Hito Corto", "-")))}</div></div>
                <div class="ref-next-date">{html.escape(str(next_row.get("Inicio", "-")))}</div>
              </div>
              <div class="ref-band-block">
                <div class="ref-band-k">Puesta en marcha</div>
                <div class="ref-critical"><span>▦</span>{format_date(launch_date)}</div>
                <div style="font-size:12px;color:#B8C9D8;margin-top:12px;">Fecha estimada de continuidad operacional</div>
              </div>
              <div class="ref-band-block">
                <div class="ref-band-k">Recomendación ejecutiva</div>
                <div class="ref-rec">Priorizar liberación inicial del {html.escape(current_hito_label)} y asegurar fondos de avance para sostener continuidad técnica y evitar desaceleración del cronograma.</div>
                <div class="ref-action-badge">Liberar fondos iniciales {html.escape(current_hito_label)} para evitar desaceleración técnica</div>
              </div>
            </div>
            <div class="ref-kpi-groups">
              {kpi_group("Financiero", "#F59E0B", [
                  ref_kpi("CAPEX restante", format_clp(total), f"{format_pct(remaining_share)} del total", "$", "#0F766E"),
                  ref_kpi(f"Monto {current_hito_label}", format_clp(current_total), f"{format_pct(current_share)} del total", "▣", "#0F766E"),
                  ref_kpi("Brecha financiera", format_clp(float(metrics["breach"])), "Riesgo de desaceleración", "!", "#F59E0B"),
              ], "priority")}
              {kpi_group("Urgencia", "#F59E0B", [
                  ref_kpi("Fondos 30 días", format_clp(critical_30), f"{hitos_30} hito{'s' if hitos_30 != 1 else ''} en ventana", "◷", "#F59E0B"),
                  ref_kpi("Fondos 60 días", format_clp(critical_60), f"{hitos_60} hito{'s' if hitos_60 != 1 else ''} en ventana", "◔", "#F59E0B"),
              ], "urgency")}
              {kpi_group("Avance", "#2563EB", [
                  ref_kpi("Avance técnico", format_pct(technical_pct), "Avance real vs plan", "⌁", "#2563EB"),
              ])}
              {kpi_group("Riesgo", risk_color, [
                  ref_kpi("Puesta en marcha", format_date(launch_date), launch_remaining, "⚑", "#64748B"),
                  ref_kpi("Riesgo PMO", risk, "Atención inmediata" if risk == "ALTO" else "Seguimiento activo", "⬟", risk_color, "risk"),
              ], "risk-group")}
            </div>
            <div class="pmo-flow">
            <div class="ref-main">
              <div class="ref-panel memo-card">
                <div class="ref-panel-title">Memo ejecutivo del período</div>
                {memo_html}
              </div>
              <div class="ref-panel">
                <div class="ref-panel-title">Escenarios de liberación de fondos</div>
                <div class="ref-scenarios">
                  {scenario("Escenario mínimo", "Solo liberación inicial", cons, (cons / current_total if current_total else 0), ["Activa continuidad mínima", "No cubre avance técnico", "Requiere control semanal"], "Alto", "30 días", "#F59E0B")}
                  {scenario("Escenario base recomendado", "Inicial + avance", base, (base / current_total if current_total else 0), ["Cubre ruta técnica crítica", "Reduce riesgo de pausa", "Sostiene ejecución PMO"], "Medio", "60 días", "#2F80ED", True)}
                  {scenario("Escenario cierre", "Liberación total del hito", close, (close / current_total if current_total else 0), ["Cubre cierre completo", "Minimiza interrupciones", "Asegura continuidad operacional"], "Bajo", "90+ días", "#10B981")}
                </div>
              </div>
            </div>
            <div class="control-stack">
            <div class="control-panel ref-timeline">
              <div class="timeline-head">
                <div class="ref-panel-title">Roadmap de decisión H1 → H8</div>
                <div class="timeline-legend">
                  <span><i class="legend-dot" style="background:#10B981;"></i>Ejecutado</span>
                  <span><i class="legend-dot" style="background:#2F80ED;"></i>En curso</span>
                  <span><i class="legend-dot" style="background:#94A3B8;"></i>Pendiente</span>
                  <span><i class="legend-dot" style="background:#EF4444;"></i>Crítico</span>
                </div>
              </div>
              <div class="ref-stage"><div style="background:#DDF3F7;">Liberación inicial</div><div style="background:#FBF0D5;">Ingeniería y fabricación</div><div style="background:#DDF4EA;">Integración y cierre</div></div>
              <div class="decision-roadmap" style="--today:{today_pos:.2f}%;--progress:{progress_width:.2f}%;">
                <div class="today-line"><span>HOY</span></div>
                <div class="decision-track"><div class="decision-progress"></div></div>
                <div class="ref-line">{''.join(timeline_items)}</div>
              </div>
            </div>
            <div class="control-panel">
              <div class="ref-panel-title">Matriz PMO de hitos</div>
              <div class="matrix-summary">
                <div class="summary-tile"><small>Hitos críticos</small><b>{critical_count}</b></div>
                <div class="summary-tile"><small>CAPEX comprometido</small><b>{format_clp_mm(total)}</b></div>
                <div class="summary-tile"><small>Brecha operacional</small><b>{format_clp_mm(float(metrics["breach"]))}</b></div>
                <div class="summary-tile"><small>Riesgo PMO</small><b>{html.escape(risk)}</b></div>
                <div class="summary-tile"><small>Próximo desbloqueo</small><b>{html.escape(next_unlock)}</b></div>
              </div>
              <div class="matrix-scroll">
                <table class="pmo-matrix">
                  <thead>
                    <tr>
                      <th class="sticky-col col-hito">Hito</th><th class="sticky-col col-state">Estado</th><th class="sticky-col col-risk">Criticidad</th>
                      <th>Hito ejecutivo</th><th>Etapa</th><th>Impacto operativo</th><th>Indicador PMO</th>
                      <th>Av. financiero</th><th>Ejecución</th><th>CAPEX restante</th><th>Duración</th>
                      <th>Inicio</th><th>Término</th><th>Escenario</th><th>Decisión requerida</th>
                    </tr>
                  </thead>
                  <tbody>{''.join(matrix_rows)}</tbody>
                </table>
              </div>
              <div class="matrix-foot"><span>Criticidad: <b style="color:#E11D48;">● Alta</b> <b style="color:#F59E0B;">● Media</b> <b style="color:#10B981;">● Baja</b></span><span>Escenario recomendado calculado según criticidad e impacto en puesta en marcha.</span></div>
            </div>
            <div class="control-panel">
              <div class="ref-panel-title">Decisiones requeridas</div>
              <div class="ref-decisions">
                {decision_cards_html}
              </div>
            </div>
            </div>
          </div>
          </div>
        </div>
        """
    components.html(html_doc, height=1480, scrolling=True)
    with st.expander("Ver matriz PMO completa", expanded=False):
        render_hitos_table(df, hito_summary, pmo_source)


def executive_reading(df: pd.DataFrame, hito_summary: pd.DataFrame) -> dict[str, list[str] | str]:
    total = float(df["Monto CLP Num"].sum() or 0)
    today = pd.Timestamp("today").normalize()
    scheduled = df[~df["Pendiente programación"]].copy()
    upcoming = scheduled[scheduled["Inicio"].ge(today)].sort_values("Inicio").head(5)
    if upcoming.empty and not scheduled.empty:
        upcoming = scheduled.sort_values("Inicio").head(5)

    top_activities = df.nlargest(5, "Monto CLP Num")
    critical_hitos = hito_summary.sort_values(["Monto_CLP", "Duracion_habil"], ascending=[False, False]).head(3)

    risks = []
    if not hito_summary.empty and total > 0:
        top_hito = hito_summary.iloc[hito_summary["Monto_CLP"].idxmax()]
        top_share = float(top_hito["Monto_CLP"] / total)
        if top_share >= 0.30:
            risks.append(f"{top_hito['Hito Ejecutivo']} concentra {format_pct(top_share)} del presupuesto.")
        top3_share = float(hito_summary.nlargest(3, "Monto_CLP")["Monto_CLP"].sum() / total)
        if top3_share >= 0.60:
            risks.append(f"Los tres hitos de mayor monto concentran {format_pct(top3_share)} de la inversion.")
    top_activity = top_activities.iloc[0] if not top_activities.empty else None
    if top_activity is not None and total > 0 and top_activity["Monto CLP Num"] / total >= 0.15:
        risks.append(
            f"La actividad {top_activity['ID']} representa {format_pct(top_activity['Monto CLP Num'] / total)} del total."
        )
    if not risks:
        risks.append("No se detecta concentracion financiera superior a los umbrales ejecutivos definidos.")

    enable_mask = (
        df["Hito Ejecutivo"].str.contains("Comisionamiento|Integracion electrica|Integracion mecanica", case=False, na=False)
        | df["Descripción Técnica / Acción"].str.contains(
            "puesta en marcha|comisionamiento|instrumentacion|proteccion|balanceo|izaje|conexion",
            case=False,
            na=False,
        )
    )
    enable_activities = df[enable_mask].sort_values(["Inicio", "Monto CLP Num"], ascending=[True, False]).head(6)

    completed_share = float((df["Monto CLP Num"] * df["Avance Num"]).sum() / total) if total > 0 else 0.0
    final_date = scheduled["Termino"].max() if not scheduled.empty else pd.NaT
    comment = (
        "El piloto 10 kW se encuentra estructurado como una transicion desde continuidad tecnica, "
        "obras previas y fabricacion hacia integracion mecanica-electrica, instrumentacion y puesta en marcha. "
        f"El avance financiero ponderado declarado alcanza {format_pct(completed_share)} y el termino estimado "
        f"del horizonte es {format_date(final_date)}. La lectura de directorio debe enfocarse en asegurar "
        "liberacion oportuna de fondos, cierre tecnico de componentes FRP y secuencia sin holguras entre izaje, "
        "protecciones, medicion y comisionamiento."
    )

    return {
        "Hitos criticos": [
            f"{row['Hito Ejecutivo']}: {format_clp(row['Monto_CLP'])}, {row['Duracion_habil']} dias habiles."
            for _, row in critical_hitos.iterrows()
        ],
        "Actividades de mayor monto": [
            f"{row['ID']} - {row['Descripción Técnica / Acción'][:92]}: {format_clp(row['Monto CLP Num'])}."
            for _, row in top_activities.iterrows()
        ],
        "Actividades proximas a iniciar": [
            f"{row['ID']} inicia {format_date(row['Inicio'])}: {row['Descripción Técnica / Acción'][:92]}."
            for _, row in upcoming.iterrows()
        ],
        "Riesgos de concentracion financiera": risks,
        "Actividades que habilitan la puesta en marcha": [
            f"{row['ID']} - {row['Hito Ejecutivo']}: {row['Descripción Técnica / Acción'][:86]}."
            for _, row in enable_activities.iterrows()
        ],
        "Comentario tecnico ejecutivo": comment,
    }


def render_exec_panel(reading: dict[str, list[str] | str]) -> None:
    st.subheader("Lectura ejecutiva del avance")
    cols = st.columns(2)
    sections = [
        "Hitos criticos",
        "Actividades de mayor monto",
        "Actividades proximas a iniciar",
        "Riesgos de concentracion financiera",
        "Actividades que habilitan la puesta en marcha",
    ]
    for idx, section in enumerate(sections):
        with cols[idx % 2]:
            items = reading.get(section, [])
            html_items = "".join(f"<li>{item}</li>" for item in items)
            st.markdown(f"<div class='exec-list'><b>{section}</b><ul>{html_items}</ul></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='section-note'><b>Comentario tecnico ejecutivo.</b> {reading['Comentario tecnico ejecutivo']}</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    add_css()
    render_hero()

    with st.sidebar:
        st.header("Filtros")
        st.caption("Fuente: pestaña publicada Cronograma Integrado.")
        if st.button("Actualizar datos"):
            load_csv.clear()
            st.rerun()

    try:
        raw_df = load_csv(CSV_URL)
        df, weekly_df = clean_schedule(raw_df)
    except Exception as exc:
        st.error("No se pudo cargar o normalizar el cronograma integrado.")
        st.exception(exc)
        st.stop()

    try:
        pmo_source = load_csv(PMO_MATRIX_URL)
    except Exception:
        pmo_source = pd.DataFrame()

    selected_sources = sorted(df["Fuente"].unique())
    selected_hitos = DISPLAY_MILESTONES
    selected_criticidad = "Todas"
    zoom_timeline = "4 meses"
    show_pending = True
    selected_states = sorted(df["Estado"].unique())

    filtered = df[
        df["Fuente"].isin(selected_sources)
        & df["Hito Ejecutivo"].isin(selected_hitos)
        & df["Estado"].isin(selected_states)
    ].copy()
    if selected_criticidad != "Todas":
        filtered = filtered[filtered["Criticidad"].eq(selected_criticidad)].copy()
    if not show_pending:
        filtered = filtered[~filtered["Pendiente programación"]].copy()

    if filtered.empty:
        st.warning("No hay actividades para los filtros seleccionados.")
        st.stop()

    render_board_kpis(filtered)
    render_release_cutoff_intelligence(filtered)
    render_project_timeline_conditions(filtered, pmo_source)
    render_expandable_activity_gantt(filtered)

    pending_df = filtered[filtered["Pendiente programación"]].copy()
    if not pending_df.empty:
        with st.expander("Actividades sin fecha identificadas como pendientes de programacion", expanded=False):
            st.dataframe(
                pending_df[["ID", "Fuente", "Hito Ejecutivo", "Descripción Técnica / Acción", "Estado", "Monto CLP Num"]]
                .rename(columns={"Monto CLP Num": "Monto CLP"}),
                hide_index=True,
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
