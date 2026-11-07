from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st



st.set_page_config(page_title="Les récoltes agricoles", page_icon="🌾", layout="wide")

st.title("Les récoltes agricoles")
st.caption("Projet final, Python pour l'analyse de données, ESIH 2026. Données fictives.")

CHEMIN_DATA = Path(__file__).parent / "donnees" / "recoltes_propre.csv"

@st.cache_data
def charger_donnees():
    if not CHEMIN_DATA.exists():
        st.error(f"Fichier introuvable : {CHEMIN_DATA}. Veuillez d'abord exécuter le notebook exploration.ipynb.")
        st.stop()
    df = pd.read_csv(CHEMIN_DATA)
    return df
df_base = charger_donnees()

st.sidebar.header("Filtres d'analyse")
annees_dispo = sorted(df_base['annee'].unique())
annees_choisies = st.sidebar.multiselect("Année(s)", options=annees_dispo, default=annees_dispo)
saisons_dispo = sorted(df_base['saison'].unique())
saisons_choisies = st.sidebar.multiselect("Saison(s)", options=saisons_dispo, default=saisons_dispo)
departements_dispo = ["Tous"] + sorted(df_base['departement'].unique())
dept_choisi = st.sidebar.selectbox("Département", options=departements_dispo, index=0)

df = df_base.copy()
if annees_choisies:
    df = df[df['annee'].isin(annees_choisies)]
if saisons_choisies:
    df = df[df['saison'].isin(saisons_choisies)]
if dept_choisi != "Tous":
    df = df[df['departement'] == dept_choisi]

st.subheader("Indicateurs clés de la sélection")
col1, col2, col3, col4 = st.columns(4)
prod_totale_t = df['production_t'].sum()
valeur_totale_mds = df['valeur_htg'].sum() / 1e9
surf_totale_ha = df['surface_ha'].sum()
rdt_moyen_global = (prod_totale_t / surf_totale_ha) if surf_totale_ha > 0 else 0
col1.metric("Production totale", f"{prod_totale_t:,.0f} t".replace(",", " "))
col2.metric("Valeur économique", f"{valeur_totale_mds:,.2f} Mds HTG")
col3.metric("Surface cultivée", f"{surf_totale_ha:,.0f} ha".replace(",", " "))
col4.metric("Rendement moyen", f"{rdt_moyen_global:,.2f} t/ha")
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Poids & Valeur",
    "2. Meilleurs Rendements",
    "3. Pluie & Rendements",
    "4. Dynamique 2023-2025",
    "5. Production / Habitant"
])

with tab1:
    st.markdown("### 1. Poids des cultures : Volume physique vs Valeur économique")
    q1 = df.groupby('culture').agg(
        prod=('production_t', 'sum'),
        valeur=('valeur_htg', 'sum')
    ).reset_index()
    q1['valeur_milliards'] = q1['valeur'] / 1e9
    c1, c2 = st.columns(2)
    with c1:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        q1_p = q1.sort_values('prod', ascending=True)
        ax1.barh(q1_p['culture'], q1_p['prod'] / 1000, color='#2E7D32')
        ax1.set_xlabel("Production (milliers de tonnes)")
        ax1.set_title("Volume produit")
        st.pyplot(fig1)
    with c2:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        q1_v = q1.sort_values('valeur_milliards', ascending=True)
        ax2.barh(q1_v['culture'], q1_v['valeur_milliards'], color='#1565C0')
        ax2.set_xlabel("Valeur (Milliards de Gourdes)")
        ax2.set_title("Valeur marchande")
        st.pyplot(fig2)
    st.info(
        "**Conclusion :** Le classement est bouleversé par le prix unitaire. Si la banane domine en volume "
        "(547 615 t cumulées au niveau national), l'igname génère la plus forte valeur économique globale "
        "(12,07 milliards HTG contre 6,57 milliards HTG pour la banane), grâce à un prix de 30 HTG/kg contre 12 HTG/kg."
    )

with tab2:
    st.markdown("### 2. Répartition géographique des meilleurs rendements")
    q2 = df.groupby(['culture', 'departement'])['rendement_t_ha'].mean().reset_index()
    if not q2.empty:
        idx_max = q2.groupby('culture')['rendement_t_ha'].idxmax()
        top_rdt = q2.loc[idx_max].sort_values('rendement_t_ha', ascending=False)
        fig, ax = plt.subplots(figsize=(9, 4))
        labels = [f"{r.culture} ({r.departement})" for _, r in top_rdt.iterrows()]
        bars = ax.bar(labels, top_rdt['rendement_t_ha'], color='#00897B')
        ax.set_ylabel("Rendement moyen (t/ha)")
        ax.set_title("Meilleur rendement départemental par culture")
        plt.xticks(rotation=25, ha='right')
        st.pyplot(fig)
        st.info(
            "**Conclusion:** Les rendements de pointe reflètent la vocation des terroirs : le Nord mène pour la banane (9,17 t/ha), "
            "la Grand'Anse pour l'igname (8,28 t/ha) et l'Artibonite pour le riz (3,76 t/ha)."
        )

with tab3:
    st.markdown("### 3. Impact de la pluviométrie sur les rendements")
    culture_choisie = st.selectbox("Choisir une culture à observer :", options=sorted(df['culture'].unique()))
    df_cult = df[df['culture'] == culture_choisie]
    if len(df_cult) > 1:
        corr = df_cult['pluie_mm'].corr(df_cult['rendement_t_ha'])
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.scatter(df_cult['pluie_mm'], df_cult['rendement_t_ha'], color='#E64A19', alpha=0.7)
        ax.set_title(f"{culture_choisie} : Corrélation r = {corr:.2f}")
        ax.set_xlabel("Précipitations (mm)")
        ax.set_ylabel("Rendement (t/ha)")
        st.pyplot(fig)
    st.info(
        "**Conclusion:** La pluie explique fortement les rendements des cultures vivrières pluviales (corrélation de r = 0,76 pour le haricot "
        "et le maïs). À l'opposé, le riz affiche une corrélation nettement plus faible (r = 0,42) car il bénéficie de l'irrigation continue de la vallée de l'Artibonite."
    )

with tab4:
    st.markdown("### 4. Évolution et dynamique des cultures (2023 vs 2025)")
    evol_df = df_base.groupby(['culture', 'annee'])['production_t'].sum().unstack()
    if 2023 in evol_df.columns and 2025 in evol_df.columns:
        evol_df['diff_pct'] = ((evol_df[2025] - evol_df[2023]) / evol_df[2023]) * 100
        evol_df = evol_df.sort_values('diff_pct', ascending=True)
        fig, ax = plt.subplots(figsize=(8, 4))
        couleurs = ['#2E7D32' if x >= 0 else '#C62828' for x in evol_df['diff_pct']]
        ax.barh(evol_df.index, evol_df['diff_pct'], color=couleurs)
        ax.axvline(0, color='black', linestyle='--', linewidth=0.8)
        ax.set_xlabel("Variation (%)")
        ax.set_title("Variation relative de la production entre 2023 et 2025")
        st.pyplot(fig)
    st.info(
        "**Conclusion :** Le riz (+19,1 %) et le sorgho (+17,6 %) enregistrent les plus fortes hausses de production. "
        "À l'inverse, l'igname subit un recul critique de -32,2 % (perte de 52 115 t) et le haricot diminue de -12,4 %."
    )

with tab5:
    st.markdown("### 5. Sécurité alimentaire : Production par habitant")
    dep_hab = df.groupby('departement').agg(
        prod_t=('production_t', 'sum'),
        population=('population', 'first')
    ).reset_index()
    dep_hab['kg_par_hab'] = (dep_hab['prod_t'] * 1000) / dep_hab['population']
    dep_hab = dep_hab.sort_values('kg_par_hab', ascending=False)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(dep_hab['departement'], dep_hab['kg_par_hab'], color='#4A148C')
    ax.set_ylabel("Production (kg / habitant)")
    ax.set_title("Production cumulée par habitant")
    plt.xticks(rotation=25, ha='right')
    st.pyplot(fig)
    st.info(
        "**Conclusion  :** Les départements de la Grand'Anse (244,3 kg/hab) et du Centre (223,9 kg/hab) ont les ratios les plus élevés. "
        "L'Ouest, avec plus de 4 millions d'habitants, produit à peine 50,8 kg/habitant et dépend des transferts inter-départementaux."
    )
st.divider()

st.subheader("Ce qu'il faut retenir & Limites des données")
c_ret, c_lim = st.columns(2)
with c_ret:
    st.markdown("**Synthèse pour les décideurs :**")
    st.write(
        "L'igname et la banane génèrent la majorité des revenus et du tonnage agricole du pays.\n"
        "La relance urgente de la filière légumineuse (haricot, pois congo) est requise compte tenu de son recul récent.\n"
        "L'irrigation protège efficacement les rendements du riz contre les irrégularités de précipitations."
    )
with c_lim:
    st.markdown("**Limites des données :**")
    st.write(
        "Données agrégées par saison sans détail des épisodes de sécheresse ponctuelle.\n"
        "L'absence d'informations sur les prix des engrais et semences, limitant le calcul de la marge nette réelle.\n"
        "Non prise en compte des pertes post-récolte lors du transport interrégional."
    )
with st.expander("Consulter les données détaillées après filtrage"):
    st.dataframe(df, use_container_width=True)

