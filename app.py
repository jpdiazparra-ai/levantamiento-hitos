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
    initial_sidebar_state="expanded",
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


@st.cache_data(ttl=900, show_spinner=False)
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
        .block-container { padding-top: 1.35rem; padding-bottom: 3rem; }
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
            background: linear-gradient(135deg, #FFFFFF 0%, #EEF7F7 52%, #E8EEF5 100%);
            border: 1px solid #DCE8EF;
            border-radius: 10px;
            padding: 24px 28px;
            margin-bottom: 18px;
            box-shadow: 0 14px 30px rgba(15,23,42,.06);
        }
        .hero-kicker {
            color: var(--teal);
            font-size: 12px;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .hero-title {
            color: var(--navy);
            font-size: 34px;
            line-height: 1.08;
            font-weight: 850;
            margin: 0 0 10px 0;
        }
        .hero-copy {
            color: #475569;
            font-size: 15px;
            line-height: 1.55;
            max-width: 1080px;
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
            <div class="hero-kicker">Dashboard ejecutivo | Fluxial Wind 10 kW</div>
            <div class="hero-title">Avance tecnico, financiero y operacional del piloto eolico vertical</div>
            <div class="hero-copy">
                Vista integrada del cronograma de cuatro meses para presentar continuidad tecnica, uso de fondos,
                secuencia de integracion y condiciones habilitantes para comisionamiento y puesta en marcha.
            </div>
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


def render_executive_roadmap(df: pd.DataFrame) -> None:
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
    for milestone in DISPLAY_MILESTONES:
        hito_df = df[df["Hito Ejecutivo"].eq(milestone)].copy()
        scheduled = hito_df[~hito_df["Pendiente programación"]].copy()
        overlapping = scheduled[(scheduled["Termino"] >= horizon_start) & (scheduled["Inicio"] <= horizon_end)]
        if overlapping.empty and not scheduled.empty:
            overlapping = scheduled.tail(1)
        start = overlapping["Inicio"].min() if not overlapping.empty else horizon_start
        end = overlapping["Termino"].max() if not overlapping.empty else horizon_start + pd.Timedelta(days=7)
        start = max(pd.Timestamp(start), horizon_start)
        end = min(max(pd.Timestamp(end), start + pd.Timedelta(days=1)), horizon_end)
        left = pct(start)
        width = max(3.0, pct(end) - left)
        amount = float(hito_df["Monto CLP Num"].sum() or 0)
        critical = int(hito_df["Es crítica"].sum()) if not hito_df.empty else 0
        next_count = int(hito_df["Es próxima"].sum()) if not hito_df.empty else 0
        risk = (
            "alto" if critical >= 3 else
            "medio" if critical >= 1 else
            "controlado"
        )
        badges = [
            f"<span class='roadmap-badge high'>Riesgo {risk}</span>" if critical else "<span class='roadmap-badge'>Riesgo controlado</span>",
            f"<span class='roadmap-badge next'>{next_count} próximas</span>" if next_count else "",
            f"<span class='roadmap-badge'>{format_clp(amount)}</span>",
        ]
        rows.append(
            f"""
            <div class="roadmap-row">
              <div class="roadmap-label">
                <div class="roadmap-icon">{html.escape(ROADMAP_ICONS.get(milestone, "PMO"))}</div>
                <div>
                  <div class="roadmap-name">{html.escape(ROADMAP_LABELS.get(milestone, milestone))}</div>
                  <div class="roadmap-meta">{len(hito_df)} actividades · {format_date(start)} a {format_date(end)}</div>
                </div>
              </div>
              <div class="roadmap-track">
                <div class="roadmap-bar" style="left:{left:.2f}%;width:{width:.2f}%;"></div>
                <div class="roadmap-badges" style="left:{min(left + width + 1.2, 76):.2f}%;">{''.join(badges)}</div>
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
              <p>Los hitos muestran la transición desde ingeniería y fabricación hacia integración, control de riesgo y puesta en marcha.</p>
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
            Ventana turquesa: próximos 30 días. Las barras gruesas priorizan la historia ejecutiva del proyecto; el detalle técnico queda disponible bajo demanda.
          </div>
        </div>
    """
    components.html(html_doc, height=760, scrolling=True)


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


def build_pmo_hito_matrix(df: pd.DataFrame, hito_summary: pd.DataFrame) -> pd.DataFrame:
    today = pd.Timestamp("today").normalize()
    matrix = hito_summary.copy()
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


def pmo_financial_metrics(df: pd.DataFrame, hito_summary: pd.DataFrame) -> dict[str, object]:
    today = pd.Timestamp("today").normalize()
    total_capex = float(df["Monto CLP Num"].sum() or 0)
    committed = float((df["Monto CLP Num"] * df["Avance Num"]).sum())
    total_release = float(df["Total Liberación Num"].sum() or 0)
    technical_progress = float((df["Monto CLP Num"] * df["Avance Num"]).sum() / total_capex) if total_capex else 0.0
    financial_progress = committed / total_release if total_release else 0.0
    breach = max(total_capex - committed, 0.0)
    matrix = build_pmo_hito_matrix(df, hito_summary)
    current = matrix[matrix["Estado"].eq("En curso")].sort_values(["Criticidad", "Hito Orden"], ascending=[True, True])
    if current.empty:
        current = matrix[matrix["_Inicio"].ge(today)].sort_values("_Inicio").head(1)
    if current.empty:
        current = matrix.sort_values("Hito Orden").head(1)
    current_row = current.iloc[0] if not current.empty else pd.Series(dtype=object)
    next_row = matrix[matrix["_Inicio"].gt(pd.to_datetime(current_row.get("_Inicio"), errors="coerce"))].sort_values("_Inicio").head(1)
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


def render_hitos_header(df: pd.DataFrame, hito_summary: pd.DataFrame) -> dict[str, object]:
    metrics = pmo_financial_metrics(df, hito_summary)
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


def render_hitos_table(df: pd.DataFrame, hito_summary: pd.DataFrame) -> None:
    table = build_pmo_hito_matrix(df, hito_summary).copy()
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


def render_hitos_financial_view(df: pd.DataFrame, hito_summary: pd.DataFrame) -> None:
    metrics = pmo_financial_metrics(df, hito_summary)
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

    def card(label: str, value: str, note: str, icon: str, accent: str = "#0F766E") -> str:
        return f"""
        <div class="ref-kpi">
          <div class="ref-icon" style="background:{accent};">{html.escape(icon)}</div>
          <div>
            <div class="ref-kpi-label">{html.escape(label)}</div>
            <div class="ref-kpi-value">{html.escape(value)} <span>{'CLP' if '$' in value else ''}</span></div>
            <div class="ref-kpi-note">{html.escape(note)}</div>
          </div>
        </div>
        """

    def scenario(title: str, subtitle: str, amount: float, pct: float, impact: str, risk_label: str, color: str, featured: bool = False) -> str:
        star = "<div class='ref-star'>★</div>" if featured else ""
        return f"""
        <div class="ref-scenario" style="border-color:{color};">
          {star}
          <div class="ref-scenario-head">
            <div class="ref-shield" style="border-color:{color};color:{color};">⬡</div>
            <div><b>{html.escape(title)}</b><br><span>{html.escape(subtitle)}</span></div>
          </div>
          <div class="ref-scenario-grid">
            <div><small>MONTO</small><strong>{format_clp(amount)}</strong><em>{format_pct(pct)} del hito</em></div>
            <div><small>IMPLICANCIA OPERATIVA</small><p>{html.escape(impact)}</p></div>
          </div>
          <div class="ref-risk" style="color:{color};">RIESGO: {html.escape(risk_label)}</div>
        </div>
        """

    timeline_items = []
    status_label = {"Ejecutado": "EJECUTADO", "En curso": "EN CURSO", "Pendiente": "PENDIENTE"}
    status_color = {"Ejecutado": "#10B981", "En curso": "#2F80ED", "Pendiente": "#94A3B8"}
    for _, row in matrix.sort_values("Hito Orden").iterrows():
        crit = str(row.get("Criticidad", "Media"))
        stt = str(row.get("Estado", "Pendiente"))
        dot_color = "#EF4444" if crit == "Alta" and stt != "Ejecutado" else status_color.get(stt, "#94A3B8")
        timeline_items.append(
            f"""
            <div class="ref-mile">
              <div class="ref-node" style="background:{dot_color};">{html.escape(str(row['Hito']))}</div>
              <div class="ref-mile-title">{html.escape(str(row['Hito Corto']))}</div>
              <div class="ref-mile-date">{html.escape(str(row['Inicio']))}<br>{html.escape(str(row['Termino']))}</div>
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

    html_doc = f"""
        <style>
        *{{box-sizing:border-box;}}
        body{{margin:0;background:transparent;}}
        .ref-wrap{{background:#F6F8FB;border:1px solid #D9E2EC;border-radius:4px;padding:20px 22px 22px 22px;color:#0B1633;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;}}
        .ref-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;}}
        .ref-title{{font-size:28px;font-weight:900;color:#0B1633;line-height:1.05;margin:0;}}
        .ref-sub{{font-size:13px;color:#607086;margin-top:7px;}}
        .ref-actions{{display:flex;gap:14px;align-items:center;color:#607086;font-size:11px;}}
        .ref-filter{{border:1px solid #D7E0EA;border-radius:7px;background:#FFFFFF;padding:9px 14px;font-weight:800;color:#25364F;}}
        .ref-band{{display:grid;grid-template-columns:1.1fr 1.25fr 1fr 2.2fr;gap:22px;background:linear-gradient(135deg,#08253B,#0B3554);border-radius:12px;padding:22px 32px;color:#FFFFFF;box-shadow:0 16px 34px rgba(8,37,59,.24);margin-bottom:18px;}}
        .ref-band-block{{border-right:1px solid rgba(255,255,255,.28);padding-right:22px;min-height:86px;}}
        .ref-band-block:last-child{{border-right:0;}}
        .ref-band-k{{font-size:11px;color:#B8C9D8;font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;}}
        .ref-hito{{display:flex;align-items:center;gap:14px;}}
        .ref-hito-code{{font-size:34px;font-weight:900;color:#B8C9D8;line-height:1;}}
        .ref-hito-name{{font-size:13px;line-height:1.25;color:#FFFFFF;font-weight:650;}}
        .ref-badge{{display:inline-flex;margin-top:12px;border-radius:4px;padding:5px 12px;background:#14B8A6;color:#FFFFFF;font-size:11px;font-weight:900;}}
        .ref-critical{{font-size:24px;font-weight:900;color:#FF5B6E;}}
        .ref-rec{{font-size:13px;line-height:1.45;color:#FFFFFF;max-width:560px;}}
        .ref-action-badge{{display:inline-flex;margin-top:10px;background:#FBBF24;color:#1F2937;border-radius:4px;padding:5px 13px;font-size:11px;font-weight:900;}}
        .ref-kpis{{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:14px;margin-bottom:18px;}}
        .ref-kpi{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:18px 16px;display:flex;gap:12px;min-height:122px;box-shadow:0 14px 26px rgba(15,23,42,.06);}}
        .ref-icon{{width:34px;height:34px;border-radius:999px;display:flex;align-items:center;justify-content:center;color:#FFFFFF;font-weight:900;flex:0 0 auto;}}
        .ref-kpi-label{{font-size:10px;font-weight:900;color:#4D5E76;letter-spacing:.05em;text-transform:uppercase;line-height:1.15;min-height:24px;}}
        .ref-kpi-value{{font-size:20px;font-weight:900;color:#0B1633;margin-top:12px;white-space:nowrap;}}
        .ref-kpi-value span{{font-size:10px;color:#64748B;margin-left:5px;font-weight:700;}}
        .ref-kpi-note{{font-size:11px;color:#64748B;margin-top:7px;line-height:1.25;}}
        .ref-main{{display:grid;grid-template-columns:1fr 1.8fr;gap:16px;margin-bottom:12px;}}
        .ref-panel{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:18px 20px;box-shadow:0 12px 24px rgba(15,23,42,.05);}}
        .ref-panel-title{{font-size:13px;font-weight:900;color:#23457A;letter-spacing:.04em;text-transform:uppercase;margin-bottom:15px;}}
        .ref-read{{font-size:13px;line-height:1.65;color:#182A44;}}
        .ref-scenarios{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;}}
        .ref-scenario{{position:relative;border:1.5px solid #E2E8F0;border-radius:10px;background:#FFFFFF;padding:18px 18px 14px 18px;min-height:165px;}}
        .ref-scenario-head{{display:flex;gap:12px;align-items:center;font-size:14px;color:#0B1633;}}
        .ref-scenario-head span{{font-size:12px;color:#64748B;font-weight:500;}}
        .ref-shield{{width:34px;height:34px;border:2px solid;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:900;}}
        .ref-star{{position:absolute;right:14px;top:12px;color:#1E88E5;font-size:20px;}}
        .ref-scenario-grid{{display:grid;grid-template-columns:.8fr 1.35fr;gap:16px;margin-top:18px;}}
        .ref-scenario-grid small{{display:block;font-size:9px;color:#4D5E76;font-weight:900;letter-spacing:.05em;}}
        .ref-scenario-grid strong{{display:block;font-size:16px;color:#0B1633;margin-top:7px;}}
        .ref-scenario-grid em{{display:block;font-size:10px;color:#64748B;font-style:normal;margin-top:4px;}}
        .ref-scenario-grid p{{font-size:11px;line-height:1.35;color:#25364F;margin:7px 0 0 0;}}
        .ref-risk{{border-top:1px solid #E5EAF0;margin-top:12px;padding-top:9px;font-size:12px;font-weight:900;}}
        .ref-timeline{{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:14px 18px 18px 18px;margin-bottom:12px;box-shadow:0 12px 24px rgba(15,23,42,.05);}}
        .ref-stage{{display:grid;grid-template-columns:1.9fr 4.1fr 1.6fr;gap:12px;margin:8px 0 18px 0;}}
        .ref-stage div{{height:24px;border-radius:3px;font-size:10px;font-weight:900;display:flex;align-items:center;justify-content:center;color:#334155;}}
        .ref-line{{position:relative;display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:8px;border-top:4px solid #CBD5E1;padding-top:0;margin-top:24px;}}
        .ref-mile{{text-align:center;position:relative;min-height:118px;}}
        .ref-node{{width:38px;height:38px;border-radius:999px;color:#FFFFFF;font-weight:900;display:flex;align-items:center;justify-content:center;margin:-21px auto 8px auto;box-shadow:0 7px 14px rgba(15,23,42,.18);}}
        .ref-mile-title{{font-size:11px;color:#243B53;line-height:1.2;min-height:35px;}}
        .ref-mile-date{{font-size:10px;color:#64748B;line-height:1.35;margin-top:6px;}}
        .ref-mile-status{{display:inline-flex;border-radius:4px;padding:4px 8px;font-size:9px;font-weight:900;margin-top:8px;}}
        .ref-bottom{{display:grid;grid-template-columns:270px 1fr;gap:16px;align-items:start;}}
        .ref-decisions{{display:grid;gap:10px;}}
        .ref-decision{{background:#FFFFFF;border:1px solid #F3B4B4;border-radius:10px;padding:13px 14px;display:grid;grid-template-columns:34px 1fr;gap:10px;}}
        .ref-decision b{{font-size:12px;color:#E11D48;}}
        .ref-decision p{{font-size:11px;color:#334155;line-height:1.35;margin:3px 0 0 0;}}
        @media(max-width:1200px){{.ref-kpis{{grid-template-columns:repeat(4,1fr);}}.ref-main,.ref-bottom{{grid-template-columns:1fr;}}}}
        </style>
        <div class="ref-wrap">
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
              <div style="font-size:12px;color:#B8C9D8;margin-top:12px;">{format_date(next_row.get("_Inicio", pd.NaT))}</div>
            </div>
            <div class="ref-band-block">
              <div class="ref-band-k">Fecha crítica</div>
              <div class="ref-critical">{format_date(launch_date)}</div>
              <div style="font-size:12px;color:#B8C9D8;margin-top:12px;">Puesta en marcha esperada</div>
            </div>
            <div class="ref-band-block">
              <div class="ref-band-k">Recomendación ejecutiva</div>
              <div class="ref-rec">Priorizar liberación inicial del {html.escape(current_hito_label)} y asegurar fondos de avance para sostener continuidad técnica y evitar desaceleración del cronograma.</div>
              <div class="ref-action-badge">ACCIÓN REQUERIDA</div>
            </div>
          </div>
          <div class="ref-kpis">
            {card("CAPEX restante total", format_clp(total), f"{format_pct(total / total) if total else '0,0%'} del total", "$", "#059669")}
            {card(f"Monto hito actual ({current_hito_label})", format_clp(float(current.get("Monto_CLP", 0) or 0)), f"{format_pct(float(current.get('Monto_CLP', 0) or 0)/total) if total else '0,0%'} del total", "▣", "#2563EB")}
            {card("Fondos críticos 30 días", format_clp(float(metrics["funds_30"])), "Ventana de decisión inmediata", "◷", "#0284C7")}
            {card("Fondos críticos 60 días", format_clp(float(metrics["funds_60"])), "Ventana de continuidad", "◔", "#0EA5E9")}
            {card("% avance técnico ponderado", format_pct(technical_pct), "Avance real vs plan", "⌁", "#2563EB")}
            {card("Brecha financiera para continuidad", format_clp(float(metrics["breach"])), "Riesgo de desaceleración", "!", "#F59E0B")}
            {card("Puesta en marcha estimada", format_date(launch_date), "Fecha objetivo del piloto", "⚑", "#64748B")}
            {card("Riesgo PMO actual", risk, "Atención ejecutiva", "♦", risk_color)}
          </div>
          <div class="ref-main">
            <div class="ref-panel">
              <div class="ref-panel-title">Lectura ejecutiva del período</div>
              <div class="ref-read">{html.escape(executive_text)}</div>
            </div>
            <div class="ref-panel">
              <div class="ref-panel-title">Escenarios de liberación de fondos</div>
              <div class="ref-scenarios">
                {scenario("Escenario Conservador", "Solo liberación inicial", cons, cons/current_total if current_total else 0, "Continuidad limitada. Riesgo de retrasos en ingeniería y adquisiciones críticas.", "ALTO", "#F59E0B")}
                {scenario("Escenario Base", "Liberación inicial + avance", base, base/current_total if current_total else 0, "Continuidad técnica controlada. Permite sostener ruta crítica sin interrupciones mayores.", "MEDIO", "#2F80ED", True)}
                {scenario("Escenario Cierre", "Liberación total del hito", close, 1 if current_total else 0, "Ejecución sin interrupciones. Maximiza probabilidad de puesta en marcha en fecha.", "BAJO", "#10B981")}
              </div>
            </div>
          </div>
          <div class="ref-timeline">
            <div class="ref-panel-title">Línea de tiempo ejecutiva H1 → H8</div>
            <div class="ref-stage"><div style="background:#DDF3F7;">LIBERACIÓN INICIAL</div><div style="background:#FBF0D5;">AVANCE</div><div style="background:#DDF4EA;">CIERRE</div></div>
            <div class="ref-line">{''.join(timeline_items)}</div>
          </div>
          <div class="ref-bottom">
            <div class="ref-panel">
              <div class="ref-panel-title">Decisiones requeridas</div>
              <div class="ref-decisions">
                <div class="ref-decision"><div class="ref-icon" style="background:#FCA5A5;">▣</div><div><b>Decisión financiera inmediata</b><p>Aprobar liberación inicial del {html.escape(current_hito_label)} por {format_clp(cons)}.</p></div></div>
                <div class="ref-decision" style="border-color:#FCD34D;"><div class="ref-icon" style="background:#F59E0B;">▣</div><div><b style="color:#D97706;">Decisión técnica pendiente</b><p>Validar dependencias críticas antes de sostener avance del próximo hito.</p></div></div>
                <div class="ref-decision"><div class="ref-icon" style="background:#FB7185;">!</div><div><b>Riesgo si no se libera financiamiento</b><p>Riesgo de desaceleración, aumento de costos y retraso en puesta en marcha.</p></div></div>
              </div>
            </div>
            <div class="ref-panel">
              <div class="ref-panel-title">Matriz PMO de hitos</div>
              <div style="font-size:13px;line-height:1.55;color:#334155;">
                La matriz detallada se muestra bajo este panel para mantener lectura ejecutiva limpia y tabla interactiva.
              </div>
            </div>
          </div>
        </div>
        """
    components.html(html_doc, height=980, scrolling=True)
    st.markdown("#### Matriz PMO de hitos")
    render_hitos_table(df, hito_summary)


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

    st.markdown("<div class='pill'>Controles ejecutivos</div>", unsafe_allow_html=True)
    fc1, fc2, fc3, fc4, fc5 = st.columns([1.4, 2.2, 1.3, 1.4, 1.1])
    with fc1:
        selected_sources = st.multiselect(
            "Fuente",
            sorted(df["Fuente"].unique()),
            default=sorted(df["Fuente"].unique()),
            label_visibility="collapsed",
            placeholder="Fuente",
        )
    with fc2:
        selected_hitos = st.multiselect(
            "Hitos",
            DISPLAY_MILESTONES,
            default=DISPLAY_MILESTONES,
            label_visibility="collapsed",
            placeholder="Hitos",
        )
    with fc3:
        criticidad_options = ["Todas"] + sorted(df["Criticidad"].unique())
        selected_criticidad = st.selectbox("Criticidad", criticidad_options, label_visibility="collapsed")
    with fc4:
        zoom_timeline = st.selectbox("Zoom", ["4 meses", "60 días", "30 días"], label_visibility="collapsed")
    with fc5:
        show_pending = st.toggle("Pendientes", value=True)

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

    render_premium_kpis(filtered)

    pending_count = int(filtered["Pendiente programación"].sum())
    corrected_count = int(filtered["Fecha corregida"].sum())
    chips = [
        f"<span class='pill'>Pendientes de programacion: {pending_count}</span>",
        f"<span class='pill'>Fechas corregidas automaticamente: {corrected_count}</span>",
        "<span class='pill'>Horizonte visual: 4 meses</span>",
        f"<span class='pill'>Vista riesgo: {html.escape(selected_criticidad)}</span>",
    ]
    st.markdown("".join(chips), unsafe_allow_html=True)
    hito_summary = make_hito_summary(filtered)

    st.subheader("Roadmap y Gantt ejecutivo")
    roadmap_tab, technical_tab, hitos_tab = st.tabs(["Vista ejecutiva", "Vista técnica", "Vista hitos"])
    with roadmap_tab:
        render_executive_roadmap(filtered)
        st.markdown("#### Actividades técnicas por hito")
        for milestone in DISPLAY_MILESTONES:
            hito_df = filtered[filtered["Hito Ejecutivo"].eq(milestone)].copy()
            if hito_df.empty:
                continue
            hito_df = hito_df.sort_values(["Es crítica", "Es habilitante", "Inicio"], ascending=[False, False, True])
            preview = hito_df.head(6)[
                [
                    "ID",
                    "Fuente",
                    "Categoría/Línea",
                    "Descripción Técnica / Acción",
                    "Criticidad",
                    "Riesgo operacional",
                    "Inicio Acción",
                    "Término Acción",
                    "Monto CLP",
                ]
            ]
            label = f"{ROADMAP_LABELS.get(milestone, milestone)} · {len(hito_df)} actividades"
            with st.expander(label, expanded=False):
                st.dataframe(preview, hide_index=True, use_container_width=True, height=min(320, 70 + 36 * len(preview)))
                if len(hito_df) > len(preview):
                    st.caption(f"Se muestran las 6 actividades más relevantes de {len(hito_df)}. Usa la vista técnica para ver todo el detalle.")
    with technical_tab:
        st.plotly_chart(build_gantt(filtered, zoom=zoom_timeline), use_container_width=True)
    with hitos_tab:
        render_hitos_financial_view(filtered, hito_summary)

    pending_df = filtered[filtered["Pendiente programación"]].copy()
    if not pending_df.empty:
        with st.expander("Actividades sin fecha identificadas como pendientes de programacion", expanded=False):
            st.dataframe(
                pending_df[["ID", "Fuente", "Hito Ejecutivo", "Descripción Técnica / Acción", "Estado", "Monto CLP Num"]]
                .rename(columns={"Monto CLP Num": "Monto CLP"}),
                hide_index=True,
                use_container_width=True,
            )

    st.subheader("Analisis por hito tecnico")
    hito_table = hito_summary[
        [
            "Hito",
            "Hito Ejecutivo",
            "Monto total",
            "% total",
            "Inicio",
            "Termino",
            "Duracion_habil",
            "Estado",
            "Fuente principal",
            "Partidas",
        ]
    ].rename(columns={"Duracion_habil": "Duracion en dias habiles"})
    st.dataframe(hito_table, hide_index=True, use_container_width=True, height=min(430, 76 + 35 * len(hito_table)))

    seq = hito_summary[["Hito", "Hito Ejecutivo", "Inicio", "Termino", "Fuente principal"]].copy()
    seq["Dependencia / secuencia logica"] = [
        "Inicio de programa" if i == 0 else f"Despues de {seq.iloc[i - 1]['Hito']}"
        for i in range(len(seq))
    ]
    with st.expander("Secuencia logica de hitos", expanded=False):
        st.dataframe(seq, hide_index=True, use_container_width=True)

    st.subheader("Visualizacion financiera")
    fig_hito, fig_stages, fig_source, fig_week = build_financial_figures(filtered, weekly_df)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_hito, use_container_width=True)
    c2.plotly_chart(fig_stages, use_container_width=True)
    c3, c4 = st.columns(2)
    c3.plotly_chart(fig_source, use_container_width=True)
    c4.plotly_chart(fig_week, use_container_width=True)

    st.subheader("Riesgo y avance operacional")
    fig_risk, fig_source_progress = build_operational_figures(filtered)
    r1, r2 = st.columns(2)
    r1.plotly_chart(fig_risk, use_container_width=True)
    r2.plotly_chart(fig_source_progress, use_container_width=True)

    reading = executive_reading(filtered, hito_summary)
    render_exec_panel(reading)

    st.subheader("Tabla operativa editable y exportable")
    table_cols = [
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
        "Pendiente programación",
        "Fecha corregida",
    ]
    edited_view = st.data_editor(
        filtered[table_cols],
        hide_index=True,
        use_container_width=True,
        height=460,
        disabled=[col for col in table_cols if col not in {"Estado", "Avance"}],
        key="cronograma_editor",
    )
    st.caption("La tabla editable no modifica la fuente original; solo permite revisar escenarios en la sesion.")

    export_summary = hito_summary[
        [
            "Hito",
            "Hito Ejecutivo",
            "Monto_CLP",
            "% sobre total",
            "Inicio",
            "Termino",
            "Duracion_habil",
            "Estado",
            "Fuente principal",
            "Partidas",
        ]
    ].copy()
    export_summary["Monto_CLP"] = export_summary["Monto_CLP"].round(0)
    excel_bytes = to_excel_bytes(
        {
            "Cronograma filtrado": filtered[table_cols],
            "Resumen hitos": export_summary,
            "Curva semanal": weekly_df,
        }
    )
    cdl1, cdl2, cdl3 = st.columns(3)
    cdl1.download_button(
        "Descargar resumen Excel",
        data=excel_bytes,
        file_name="fluxial_wind_10kw_resumen_ejecutivo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    cdl2.download_button(
        "Descargar cronograma CSV",
        data=filtered[table_cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="fluxial_wind_10kw_cronograma_filtrado.csv",
        mime="text/csv",
        use_container_width=True,
    )
    cdl3.download_button(
        "Descargar hitos CSV",
        data=export_summary.to_csv(index=False).encode("utf-8-sig"),
        file_name="fluxial_wind_10kw_resumen_hitos.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.subheader("Narrativa ejecutiva")
    st.markdown(
        """
        <div class="section-note">
        El piloto Fluxial Wind 10 kW avanza desde una etapa dominada por ingenieria, continuidad tecnica,
        habilitacion de sitio y cierre de fabricacion hacia una fase de integracion operacional. La prioridad
        ejecutiva es coordinar fundaciones, suministros, armado mecanico, izaje, protecciones electricas e
        instrumentacion para que el comisionamiento ocurra dentro del horizonte de cuatro meses. En terminos
        de gestion, el cronograma permite monitorear la liberacion de fondos por etapa, aislar actividades
        criticas por monto y asegurar que las tareas habilitantes de puesta en marcha no pierdan secuencia.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
