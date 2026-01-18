import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tesla på FINN", layout="wide")
st.title("🚗 Tesla på FINN – Analyse & prisforslag")

import os
if os.path.exists("tesla_finn.csv"):
    df = pd.read_csv("tesla_finn.csv")
else:
    import finn_hent_tesla
    df = pd.read_csv("tesla_finn.csv")

tab1, tab2 = st.tabs(["📊 Alle Tesla", "💰 Prisforslag"])

with tab1:
    st.sidebar.header("Filtrer")

    modell = st.sidebar.multiselect(
        "Modell",
        sorted(df["Modell"].unique()),
        default=sorted(df["Modell"].unique())
    )

    driv = st.sidebar.multiselect(
        "Drivlinje",
        sorted(df["Drivlinje"].unique()),
        default=sorted(df["Drivlinje"].unique())
    )

    år_min, år_max = int(df["Årsmodell"].min()), int(df["Årsmodell"].max())
    år = st.sidebar.slider("Årsmodell", år_min, år_max, (år_min, år_max))

    km_min, km_max = int(df["Km"].min()), int(df["Km"].max())
    km = st.sidebar.slider("Kilometer", km_min, km_max, (km_min, km_max))

    filtrert = df[
        (df["Modell"].isin(modell)) &
        (df["Drivlinje"].isin(driv)) &
        (df["Årsmodell"].between(*år)) &
        (df["Km"].between(*km))
    ].sort_values("Pris")

    st.dataframe(filtrert, use_container_width=True)

with tab2:
    st.subheader("💰 Foreslå annonsepris (STRAM)")

    m = st.selectbox("Modell", sorted(df["Modell"].unique()))
    d = st.selectbox("Drivlinje", ["AWD", "RWD"])
    år = st.number_input("Årsmodell", 2013, 2025, 2021)
    km = st.number_input("Kilometerstand", 0, 500000, 60000)

    if st.button("Beregn pris"):
        s = df[
            (df["Modell"] == m) &
            (df["Drivlinje"] == d) &
            (df["Årsmodell"].between(år - 1, år + 1)) &
            (df["Km"].between(km - 15000, km + 15000))
        ]

        if len(s) < 3:
            st.warning("For få samanliknbare bilar.")
        else:
            st.success(f"🎯 Anbefalt pris: **{int(s['Pris'].median()):,} kr**")
            st.dataframe(s.sort_values("Pris"), use_container_width=True)
