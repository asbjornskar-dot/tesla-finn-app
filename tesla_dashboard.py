import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Tesla på FINN", layout="wide")
st.title("🚗 Tesla på FINN – Analyse & prisforslag")

CSV_FILE = "tesla_finn.csv"

st.sidebar.header("Data")
st.sidebar.caption("✅ Data oppdateres automatisk kvar dag via GitHub Actions.")

# ---- Load data ----
if not os.path.exists(CSV_FILE):
    st.error("Fann ikkje tesla_finn.csv. Vent litt og prøv igjen.")
    st.stop()

df = pd.read_csv(CSV_FILE)

if df.empty:
    st.warning("CSV er tom. Vent litt og prøv igjen.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Alle Tesla", "💰 Prisforslag"])

# ======================
# FANE 1
# ======================
with tab1:
    st.sidebar.header("Filtrer")

    modell = st.sidebar.multiselect(
        "Modell",
        sorted(df["Modell"].dropna().unique()),
        default=sorted(df["Modell"].dropna().unique())
    )

    driv = st.sidebar.multiselect(
        "Drivlinje",
        sorted(df["Drivlinje"].dropna().unique()),
        default=sorted(df["Drivlinje"].dropna().unique())
    )

    df2 = df.copy()
    df2 = df2[df2["Modell"].isin(modell)]
    df2 = df2[df2["Drivlinje"].isin(driv)]

    # Sliders berre om vi har data
    if "Årsmodell" in df2.columns and df2["Årsmodell"].notna().any():
        år_min, år_max = int(df2["Årsmodell"].min()), int(df2["Årsmodell"].max())
        år = st.sidebar.slider("Årsmodell", år_min, år_max, (år_min, år_max))
        df2 = df2[df2["Årsmodell"].between(*år)]

    if "Km" in df2.columns and df2["Km"].notna().any():
        km_min, km_max = int(df2["Km"].min()), int(df2["Km"].max())
        km = st.sidebar.slider("Kilometer", km_min, km_max, (km_min, km_max))
        df2 = df2[df2["Km"].between(*km)]

    sortering = st.selectbox("Sorter etter", ["Pris", "Km", "Årsmodell"])
    if sortering in df2.columns:
        df2 = df2.sort_values(sortering)

    st.markdown(f"### Treffer: **{len(df2)}**")
    st.dataframe(df2, use_container_width=True)

# ======================
# FANE 2 – Prisforslag STRAM
# ======================
with tab2:
    st.subheader("💰 Prisforslag (STRAM samanlikning)")

    m = st.selectbox("Modell", sorted(df["Modell"].dropna().unique()))
    d = st.selectbox("Drivlinje", ["AWD", "RWD"])
    år_inn = st.number_input("Årsmodell", 2013, 2025, 2021)
    km_inn = st.number_input("Kilometerstand", 0, 500000, 60000)

    if st.button("Beregn pris"):
        s = df[
            (df["Modell"] == m) &
            (df["Drivlinje"] == d) &
            (df["Årsmodell"].between(år_inn - 1, år_inn + 1)) &
            (df["Km"].between(km_inn - 15000, km_inn + 15000))
        ]

        if len(s) < 3:
            st.warning("For få samanliknbare bilar. Prøv å justere km/år.")
        else:
            st.success(f"🎯 Anbefalt pris: **{int(s['Pris'].median()):,} kr**")
            st.caption(f"Basert på {len(s)} bilar")
            st.dataframe(s.sort_values("Pris"), use_container_width=True)
