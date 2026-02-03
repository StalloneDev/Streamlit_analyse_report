import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import export_utils
import pdf_generators

# Configuration de la page
st.set_page_config(
    page_title="Rapport d'Analyses BP - SADCI GAS PARAKOU",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour charger les données
@st.cache_data
def load_data(excel_file):
    # excel_file est maintenant un objet fichier (UploadedFile) ou un path
    
    sheets = {}
    sheets['duree_distance'] = pd.read_excel(excel_file, sheet_name='Durée - Distance - Conso')
    sheets['trajets_non_autorises'] = pd.read_excel(excel_file, sheet_name='Trajets Non Autorisé')
    sheets['conduite_journee'] = pd.read_excel(excel_file, sheet_name='Conduite en Journée')
    sheets['conduite_nocturne'] = pd.read_excel(excel_file, sheet_name='Conduite nocturne')
    sheets['notifications'] = pd.read_excel(excel_file, sheet_name='Notifications')
    sheets['temps_poi'] = pd.read_excel(excel_file, sheet_name='Temps passé dans POI et ...')
    sheets['visites_poi'] = pd.read_excel(excel_file, sheet_name='Visites POI')
    sheets['vitesse'] = pd.read_excel(excel_file, sheet_name='Vitesse de conduite')
    
    return sheets

# Chargement du fichier via la sidebar
st.sidebar.title("📂 Import de Données")
uploaded_file = st.sidebar.file_uploader("Choisissez un rapport Excel", type=['xlsx'])

if uploaded_file is None:
    st.info("👋 Bienvenue! Veuillez importer un fichier Excel pour commencer l'analyse.")
    st.markdown("""
    ### Comment utiliser cette application ?
    1. Regardez dans le menu à gauche (Sidebar)
    2. Cliquez sur **"Browse files"** ou glissez-déposez votre fichier Excel
    3. L'analyse se lancera automatiquement
    """)
    st.stop() # Arrête l'exécution si aucun fichier n'est chargé

# Charger les données depuis le fichier uploadé
try:
    data = load_data(uploaded_file)
    st.sidebar.success("Fichier chargé avec succès!")
except Exception as e:
    st.error(f"Erreur lors de la lecture du fichier: {e}")
    st.stop()

# Navigation dans la sidebar
st.sidebar.markdown("---")
st.sidebar.title("📊 Navigation")
st.sidebar.markdown("---")

pages = {
    "🏠 Synthèse Générale": "synthese",
    "🚗 Durée - Distance - Conso": "duree",
    "⚠️ Trajets Non Autorisés": "trajets",
    "☀️🌙 Conduite Jour vs Nuit": "jour_nuit",
    "🚦 Limitation de Vitesse": "limitation_vitesse",
    "🔔 Notifications": "notifications",
    "📍 Temps dans POI": "temps_poi",
    "📍 Visites POI": "visites_poi",
    "🏎️ Vitesse de Conduite": "vitesse"
}

selection = st.sidebar.radio("Sélectionnez une analyse:", list(pages.keys()))
page = pages[selection]

st.sidebar.markdown("---")
st.sidebar.info("📅 Hebdomadaire")

# Section Export
st.sidebar.markdown("---")
st.sidebar.title("💾 Export")

col1, col2 = st.sidebar.columns(2)

with col1:
    # Export Excel - Page actuelle
    if st.button("📊 Excel (Page)", key="export_excel_current", use_container_width=True):
        # Generate report content for the current page
        report_content = None
        if page in pdf_generators.PDF_GENERATORS:
            report_content = pdf_generators.PDF_GENERATORS[page](data)
            
        excel_data = export_utils.export_data_to_excel(data, current_page=page, report_content=report_content)
        filename = export_utils.get_filename(selection, "xlsx")
        st.sidebar.download_button(
            label="⬇️ Télécharger Excel",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"
        )

with col2:
    # Export Excel - Toutes les données
    if st.button("📑 Excel (Tout)", key="export_excel_all", use_container_width=True):
        with st.spinner('Génération du rapport Excel complet...'):
            # Generate structured report content (dict of sheets)
            full_report_content = pdf_generators.generate_structured_report(data)
            
            excel_data_all = export_utils.export_data_to_excel(data, current_page=None, report_content=full_report_content)
            filename_all = export_utils.get_filename("Rapport_Complet", "xlsx")
            st.sidebar.download_button(
                label="⬇️ Télécharger Excel Complet",
                data=excel_data_all,
                file_name=filename_all,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_all"
            )

st.sidebar.markdown("---")

# PDF Export - Page actuelle
if st.sidebar.button("📄 PDF (Page)", key="export_pdf", use_container_width=True):
    try:
        # Generate PDF content on-demand using the generator for the current page
        if page in pdf_generators.PDF_GENERATORS:
            pdf_content = pdf_generators.PDF_GENERATORS[page](data)
            pdf_data = export_utils.create_pdf_report(selection, pdf_content)
            filename_pdf = export_utils.get_filename(selection, "pdf")
            st.sidebar.download_button(
                label="⬇️ Télécharger PDF",
                data=pdf_data,
                file_name=filename_pdf,
                mime="application/pdf",
                key="download_pdf"
            )
        else:
            st.sidebar.info(f"Export PDF non disponible pour cette page.")
    except Exception as e:
        st.sidebar.error(f"Erreur lors de la génération du PDF: {str(e)}")

# PDF Export - Complet
if st.sidebar.button("📑 PDF (Tout)", key="export_pdf_all", use_container_width=True):
    try:
        with st.spinner('Génération du rapport complet...'):
            pdf_content = pdf_generators.generate_full_report(data)
            pdf_data = export_utils.create_pdf_report("Rapport Complet", pdf_content)
            filename_pdf = export_utils.get_filename("Rapport_Complet", "pdf")
            st.sidebar.download_button(
                label="⬇️ Télécharger Rapport Complet",
                data=pdf_data,
                file_name=filename_pdf,
                mime="application/pdf",
                key="download_pdf_all"
            )
        st.sidebar.success("Rapport complet généré !")
    except Exception as e:
        st.sidebar.error(f"Erreur lors de la génération du rapport complet: {str(e)}")
        
st.sidebar.caption("💡 **Excel/PDF**: Utilisez les boutons (Tout) pour le rapport complet")


# Fonction utilitaire pour extraire les véhicules
def get_vehicles(df):
    vehicles = df['Regroupement'].dropna().unique()
    return [v for v in vehicles if not str(v).startswith('202') and v != '-----']

# Fonction pour parser la durée
def parse_duration(duration_str):
    if pd.isna(duration_str):
        return 0
    duration_str = str(duration_str)
    try:
        if 'jours' in duration_str or 'jour' in duration_str:
            parts = duration_str.split(' ')
            days = int(parts[0])
            time_parts = parts[2].split(':')
            return days * 24 * 60 + int(time_parts[0]) * 60 + int(time_parts[1])
        else:
            parts = duration_str.split(':')
            if len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + int(parts[2])/60
            return 0
    except:
        return 0

# ===== PAGE SYNTHÈSE =====
if page == "synthese":
    st.title("📊 Rapport d'Analyses Détaillées")
    today_date = datetime.now().strftime("%d/%m/%Y")
    st.markdown(f"### BP - SADCI GAS PARAKOU - Rapport du {today_date}")
    st.markdown("---")
    
    st.markdown("""
    ## 📋 Présentation du Rapport
    
    Ce rapport fournit une **analyse approfondie et des interprétations complètes** des données de la flotte 
    de véhicules BP - SADCI GAS PARAKOU. Contrairement à un simple rapport graphique, ce document offre:
    
    - ✅ **Interprétations détaillées** de chaque métrique
    - ✅ **Recommandations actionnables** pour optimiser la gestion de flotte
    - ✅ **Alertes et points d'attention** identifiés dans les données
    - ✅ **Tendances et patterns** observés
    """)
    
    # Métriques clés
    st.markdown("---")
    st.subheader("🎯 Métriques Clés de la Semaine")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcul des métriques
    vehicles = get_vehicles(data['duree_distance'])
    total_trajets = len(data['duree_distance'][~data['duree_distance']['Regroupement'].str.startswith('202', na=False)])
    trajets_non_auth = len(data['trajets_non_autorises'][~data['trajets_non_autorises']['Regroupement'].str.startswith('202', na=False)])
    total_notifications = len(data['notifications'][data['notifications']['Nom de notification'] != '-----'])
    
    with col1:
        st.metric("Véhicules Actifs", len(vehicles))
    with col2:
        st.metric("Total Trajets", total_trajets)
    with col3:
        st.metric("Trajets Non Autorisés", trajets_non_auth, delta="-" if trajets_non_auth > 50 else None, delta_color="inverse")
    with col4:
        st.metric("Notifications", total_notifications)
    
    # Graphique résumé - Distance par véhicule
    st.markdown("---")
    st.subheader("📈 Vue d'Ensemble - Distance Totale par Véhicule")
    
    df_duree = data['duree_distance'].copy()
    df_vehicles = df_duree[~df_duree['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    distance_par_vehicule = df_vehicles.groupby('Regroupement')['Distance Parcourue'].sum().reset_index()
    distance_par_vehicule = distance_par_vehicule.sort_values('Distance Parcourue', ascending=True)
    
    fig = px.bar(
        distance_par_vehicule,
        x='Distance Parcourue',
        y='Regroupement',
        orientation='h',
        title='Distance Totale Parcourue par Véhicule (km)',
        color='Distance Parcourue',
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation Générale
    
    **Observations Clés:**
    - La flotte comprend plusieurs véhicules avec des niveaux d'utilisation très variés
    - Certains véhicules présentent une activité significativement plus importante
    - Les trajets non autorisés représentent un point d'attention majeur
    
    **Recommandations:**
    1. **Optimisation de la flotte**: Réévaluer l'affectation des véhicules selon l'utilisation réelle
    2. **Suivi des infractions**: Mettre en place un système de suivi plus strict pour les trajets non autorisés
    3. **Formation conducteurs**: Organiser des sessions de sensibilisation sur le respect des règles
    """)
    
    # Répartition Jour/Nuit
    st.markdown("---")
    st.subheader("☀️🌙 Répartition Conduite Jour vs Nuit")
    
    trajets_jour = len(data['conduite_journee'][~data['conduite_journee']['Regroupement'].str.startswith('202', na=False)])
    trajets_nuit = len(data['conduite_nocturne'][~data['conduite_nocturne']['Regroupement'].str.startswith('202', na=False)])
    
    fig_pie = px.pie(
        values=[trajets_jour, trajets_nuit],
        names=['Conduite de Jour', 'Conduite de Nuit'],
        title='Répartition des Trajets Jour/Nuit',
        color_discrete_sequence=['#FFA500', '#1E3A5F']
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"☀️ **Trajets de jour**: {trajets_jour} ({trajets_jour/(trajets_jour+trajets_nuit)*100:.1f}%)")
    with col2:
        st.warning(f"🌙 **Trajets de nuit**: {trajets_nuit} ({trajets_nuit/(trajets_jour+trajets_nuit)*100:.1f}%)")

# ===== PAGE DURÉE DISTANCE CONSO =====
elif page == "duree":
    st.title("🚗 Analyse Durée - Distance - Consommation")
    st.markdown("---")
    
    df = data['duree_distance'].copy()
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    # Métriques par véhicule
    st.subheader("📊 Distance Parcourue par Véhicule")
    
    distance_stats = df_vehicles.groupby('Regroupement').agg({
        'Distance Parcourue': ['sum', 'mean', 'count']
    }).reset_index()
    distance_stats.columns = ['Véhicule', 'Distance Totale', 'Distance Moyenne', 'Nb Trajets']
    distance_stats = distance_stats.sort_values('Distance Totale', ascending=False)
    
    fig1 = px.bar(
        distance_stats.head(15),
        x='Véhicule',
        y='Distance Totale',
        title='Top 15 - Distance Totale par Véhicule (km)',
        color='Distance Totale',
        color_continuous_scale='Viridis'
    )
    fig1.update_layout(height=450)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Distance Parcourue
    
    **Analyse:**
    - Les véhicules présentent des disparités importantes en termes de kilométrage
    - Les véhicules les plus utilisés peuvent nécessiter une maintenance plus fréquente
    - L'écart entre le véhicule le plus et le moins utilisé indique une possible sous-utilisation de certains véhicules
    
    **Points d'attention:**
    - 🔴 Véhicules avec kilométrage élevé: planifier des contrôles techniques
    - 🟡 Véhicules peu utilisés: évaluer la pertinence de leur maintien dans la flotte
    """)
    
    # Nombre de trajets par véhicule
    st.markdown("---")
    st.subheader("📈 Nombre de Trajets par Véhicule")
    
    fig2 = px.bar(
        distance_stats.sort_values('Nb Trajets', ascending=False).head(15),
        x='Véhicule',
        y='Nb Trajets',
        title='Top 15 - Nombre de Trajets par Véhicule',
        color='Nb Trajets',
        color_continuous_scale='Oranges'
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Fréquence d'Utilisation
    
    **Observations:**
    - La fréquence des trajets varie considérablement selon les véhicules
    - Un nombre élevé de trajets courts peut indiquer des missions de proximité
    - Un faible nombre de trajets longs peut indiquer des missions inter-régionales
    
    **Recommandations:**
    1. Analyser la corrélation entre nombre de trajets et type de mission
    2. Optimiser les affectations pour réduire les trajets à vide
    """)
    
    # Distance moyenne par trajet
    st.markdown("---")
    st.subheader("📏 Distance Moyenne par Trajet")
    
    fig3 = px.scatter(
        distance_stats,
        x='Nb Trajets',
        y='Distance Moyenne',
        size='Distance Totale',
        color='Véhicule',
        title='Relation Nombre de Trajets vs Distance Moyenne',
        hover_data=['Distance Totale']
    )
    fig3.update_layout(height=450, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Profil d'Utilisation
    
    **Types de profils identifiés:**
    - **Courte distance / Haute fréquence**: Missions urbaines et livraisons locales
    - **Longue distance / Basse fréquence**: Missions inter-villes ou régionales
    - **Usage mixte**: Véhicules polyvalents
    
    **Recommandations:**
    - Adapter le type de véhicule au profil de mission
    - Considérer des véhicules économiques pour les trajets urbains fréquents
    """)
    
    # Tableau récapitulatif
    st.markdown("---")
    st.subheader("📋 Tableau Récapitulatif")
    
    distance_stats['Distance Totale'] = distance_stats['Distance Totale'].round(2)
    distance_stats['Distance Moyenne'] = distance_stats['Distance Moyenne'].round(2)
    st.dataframe(distance_stats, use_container_width=True, hide_index=True)

# ===== PAGE TRAJETS NON AUTORISÉS =====
elif page == "trajets":
    st.title("⚠️ Analyse des Trajets Non Autorisés")
    st.markdown("---")
    
    df = data['trajets_non_autorises'].copy()
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    st.error(f"🚨 **{len(df_vehicles)} incidents de trajets non autorisés détectés cette semaine**")
    
    # Incidents par véhicule
    st.subheader("📊 Nombre d'Incidents par Véhicule")
    
    incidents_par_vehicule = df_vehicles.groupby('Regroupement').size().reset_index(name='Nb Incidents')
    incidents_par_vehicule = incidents_par_vehicule.sort_values('Nb Incidents', ascending=False)
    
    fig1 = px.bar(
        incidents_par_vehicule.head(15),
        x='Regroupement',
        y='Nb Incidents',
        title='Top 15 - Véhicules avec le Plus d\'Incidents',
        color='Nb Incidents',
        color_continuous_scale='Reds'
    )
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Incidents par Véhicule
    
    **Analyse Critique:**
    - Certains véhicules montrent un nombre d'incidents particulièrement élevé
    - Ces véhicules nécessitent une attention immédiate et un suivi renforcé
    - La récurrence d'incidents sur les mêmes véhicules peut indiquer des problèmes systémiques
    
    **Actions Recommandées:**
    1. 🔴 **Priorité Haute**: Convoquer les conducteurs des véhicules les plus problématiques
    2. 🟠 **Priorité Moyenne**: Mettre en place un système d'alerte en temps réel
    3. 🟡 **Amélioration Continue**: Former les conducteurs sur les zones autorisées
    """)
    
    # Kilométrage non autorisé
    st.markdown("---")
    st.subheader("📏 Kilométrage Non Autorisé par Véhicule")
    
    km_non_auth = df_vehicles.groupby('Regroupement')['Kilométrage'].sum().reset_index()
    km_non_auth = km_non_auth.sort_values('Kilométrage', ascending=False)
    
    fig2 = px.bar(
        km_non_auth.head(15),
        x='Regroupement',
        y='Kilométrage',
        title='Top 15 - Kilométrage Non Autorisé (km)',
        color='Kilométrage',
        color_continuous_scale='OrRd'
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Impact Kilométrique
    
    **Coût Estimé des Trajets Non Autorisés:**
    - Consommation de carburant supplémentaire
    - Usure prématurée des véhicules
    - Risques d'accidents hors zones couvertes
    
    **Recommandations:**
    - Calculer le coût financier des trajets non autorisés
    - Établir des sanctions progressives selon le kilométrage
    """)
    
    # Vitesse maximale lors des incidents
    st.markdown("---")
    st.subheader("🏎️ Vitesse Maximale lors des Trajets Non Autorisés")
    
    vitesse_incidents = df_vehicles.groupby('Regroupement')['Vitesse maxi'].max().reset_index()
    vitesse_incidents = vitesse_incidents.sort_values('Vitesse maxi', ascending=False)
    
    fig3 = px.bar(
        vitesse_incidents.head(15),
        x='Regroupement',
        y='Vitesse maxi',
        title='Vitesse Maximale Atteinte par Véhicule lors d\'Incidents',
        color='Vitesse maxi',
        color_continuous_scale='YlOrRd'
    )
    fig3.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Limite 50 km/h")
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Comportement à Risque
    
    **Alerte Sécurité:**
    - Les vitesses élevées lors de trajets non autorisés augmentent considérablement le risque d'accidents
    - Ces comportements doivent être traités avec la plus grande priorité
    
    **Actions Immédiates:**
    1. Identifier les conducteurs concernés
    2. Organiser des entretiens individuels
    3. Envisager des mesures disciplinaires si récidive
    """)

# ===== PAGE CONDUITE JOUR VS NUIT =====
elif page == "jour_nuit":
    st.title("☀️🌙 Analyse Comparative - Conduite Jour vs Nuit")
    st.markdown("---")
    
    df_jour = data['conduite_journee'].copy()
    df_nuit = data['conduite_nocturne'].copy()
    
    df_jour_v = df_jour[~df_jour['Regroupement'].str.startswith('202', na=False)]
    df_jour_v = df_jour_v[df_jour_v['Regroupement'].notna()]
    
    df_nuit_v = df_nuit[~df_nuit['Regroupement'].str.startswith('202', na=False)]
    df_nuit_v = df_nuit_v[df_nuit_v['Regroupement'].notna()]
    
    # Comparaison globale
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("☀️ Trajets de Jour", len(df_jour_v))
        km_jour = df_jour_v['Kilométrage'].sum()
        st.metric("Distance Jour (km)", f"{km_jour:.1f}")
    
    with col2:
        st.metric("🌙 Trajets de Nuit", len(df_nuit_v))
        km_nuit = df_nuit_v['Kilométrage'].sum()
        st.metric("Distance Nuit (km)", f"{km_nuit:.1f}")
    
    # Graphique comparatif par véhicule
    st.markdown("---")
    st.subheader("📊 Kilométrage Jour vs Nuit par Véhicule")
    
    km_jour_par_v = df_jour_v.groupby('Regroupement')['Kilométrage'].sum().reset_index()
    km_jour_par_v.columns = ['Véhicule', 'Km Jour']
    
    km_nuit_par_v = df_nuit_v.groupby('Regroupement')['Kilométrage'].sum().reset_index()
    km_nuit_par_v.columns = ['Véhicule', 'Km Nuit']
    
    comparison = pd.merge(km_jour_par_v, km_nuit_par_v, on='Véhicule', how='outer').fillna(0)
    comparison['Total'] = comparison['Km Jour'] + comparison['Km Nuit']
    comparison = comparison.sort_values('Total', ascending=False).head(15)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Jour', x=comparison['Véhicule'], y=comparison['Km Jour'], marker_color='#FFA500'))
    fig.add_trace(go.Bar(name='Nuit', x=comparison['Véhicule'], y=comparison['Km Nuit'], marker_color='#1E3A5F'))
    fig.update_layout(barmode='group', title='Comparaison Kilométrage Jour/Nuit par Véhicule', height=450)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Répartition Jour/Nuit
    
    **Observations:**
    - La majorité des trajets s'effectuent de jour, ce qui est conforme aux bonnes pratiques
    - Certains véhicules présentent une activité nocturne significative
    - L'activité nocturne peut être justifiée par des missions spécifiques
    
    **Points de Vigilance:**
    - 🌙 La conduite nocturne présente des risques accrus (fatigue, visibilité réduite)
    - Vérifier que les conducteurs de nuit sont bien reposés
    - S'assurer que les trajets nocturnes sont justifiés
    """)
    
    # Vitesse maximale jour vs nuit
    st.markdown("---")
    st.subheader("🏎️ Vitesse Maximale - Jour vs Nuit")
    
    vitesse_jour = df_jour_v.groupby('Regroupement')['Vitesse maxi'].max().reset_index()
    vitesse_jour.columns = ['Véhicule', 'Vitesse Max Jour']
    
    vitesse_nuit = df_nuit_v.groupby('Regroupement')['Vitesse maxi'].max().reset_index()
    vitesse_nuit.columns = ['Véhicule', 'Vitesse Max Nuit']
    
    vitesse_comp = pd.merge(vitesse_jour, vitesse_nuit, on='Véhicule', how='outer').fillna(0)
    vitesse_comp = vitesse_comp.sort_values('Vitesse Max Jour', ascending=False).head(15)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name='Vitesse Max Jour', x=vitesse_comp['Véhicule'], y=vitesse_comp['Vitesse Max Jour'], marker_color='#FFA500'))
    fig2.add_trace(go.Bar(name='Vitesse Max Nuit', x=vitesse_comp['Véhicule'], y=vitesse_comp['Vitesse Max Nuit'], marker_color='#1E3A5F'))
    fig2.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Limite recommandée")
    fig2.update_layout(barmode='group', title='Vitesse Maximale Jour vs Nuit par Véhicule', height=450)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Comportement de Conduite
    
    **Analyse des Vitesses:**
    - Comparer les vitesses jour/nuit permet d'identifier les comportements à risque
    - Une vitesse élevée de nuit est particulièrement dangereuse
    
    **Recommandations:**
    1. Limiter les vitesses autorisées de nuit à un seuil inférieur
    2. Mettre en place des alertes automatiques pour excès de vitesse nocturne
    3. Sensibiliser les conducteurs aux risques de la conduite rapide de nuit
    """)

# ===== PAGE LIMITATION DE VITESSE (INFRACTIONS) =====
elif page == "limitation_vitesse":
    st.title("🚦 Analyse des Limitations de Vitesse - Infractions")
    st.markdown("---")
    
    df_jour = data['conduite_journee'].copy()
    df_nuit = data['conduite_nocturne'].copy()
    df_vitesse = data['vitesse'].copy()
    df_trajets = data['trajets_non_autorises'].copy()
    
    df_jour_v = df_jour[~df_jour['Regroupement'].str.startswith('202', na=False)]
    df_jour_v = df_jour_v[df_jour_v['Regroupement'].notna()]
    
    df_nuit_v = df_nuit[~df_nuit['Regroupement'].str.startswith('202', na=False)]
    df_nuit_v = df_nuit_v[df_nuit_v['Regroupement'].notna()]
    
    df_vitesse_v = df_vitesse[~df_vitesse['Regroupement'].str.startswith('202', na=False)]
    df_vitesse_v = df_vitesse_v[df_vitesse_v['Regroupement'].notna()]
    
    st.markdown("""
    Cette page analyse les **infractions aux limitations de vitesse** en croisant les données 
    de conduite jour/nuit et les vitesses maximales enregistrées.
    """)
    
    limite_urbaine = 50
    limite_nationale = 90
    
    infractions_50 = df_vitesse_v[df_vitesse_v['Vitesse maxi'] > limite_urbaine]
    infractions_90 = df_vitesse_v[df_vitesse_v['Vitesse maxi'] > limite_nationale]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Infractions > 50 km/h", len(infractions_50))
    with col2:
        st.metric("Infractions > 90 km/h", len(infractions_90))
    with col3:
        taux = len(infractions_50) / len(df_vitesse_v) * 100 if len(df_vitesse_v) > 0 else 0
        st.metric("Taux d'Infraction", f"{taux:.1f}%")
    
    st.markdown("---")
    st.subheader("📊 Infractions par Véhicule (> 50 km/h)")
    
    inf_par_vehicule = infractions_50.groupby('Regroupement').size().reset_index(name='Nb Infractions')
    inf_par_vehicule = inf_par_vehicule.sort_values('Nb Infractions', ascending=False)
    
    fig1 = px.bar(
        inf_par_vehicule.head(15),
        x='Regroupement',
        y='Nb Infractions',
        title='Top 15 - Véhicules avec le Plus d\'Infractions de Vitesse',
        color='Nb Infractions',
        color_continuous_scale='Reds'
    )
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Infractions par Véhicule
    
    **Analyse des Dépassements:**
    - Les véhicules listés ont dépassé la limite de 50 km/h (zone urbaine)
    - Un nombre élevé d'infractions indique un comportement à risque récurrent
    
    **Actions Prioritaires:**
    1. 🔴 Convoquer les conducteurs des véhicules avec > 5 infractions
    2. 🟠 Avertissement formel pour 2-5 infractions
    3. 🟡 Sensibilisation pour < 2 infractions
    """)
    
    st.markdown("---")
    st.subheader("📈 Niveaux de Gravité des Infractions")
    
    def categorize_speed(speed):
        if speed <= 50:
            return 'Conforme'
        elif speed <= 60:
            return 'Légère (51-60)'
        elif speed <= 80:
            return 'Modérée (61-80)'
        elif speed <= 100:
            return 'Grave (81-100)'
        else:
            return 'Très Grave (>100)'
    
    df_vitesse_v['Catégorie'] = df_vitesse_v['Vitesse maxi'].apply(categorize_speed)
    
    cat_counts = df_vitesse_v['Catégorie'].value_counts().reset_index()
    cat_counts.columns = ['Catégorie', 'Nombre']
    
    color_map = {
        'Conforme': '#28a745',
        'Légère (51-60)': '#ffc107',
        'Modérée (61-80)': '#fd7e14',
        'Grave (81-100)': '#dc3545',
        'Très Grave (>100)': '#6f42c1'
    }
    
    fig2 = px.pie(
        cat_counts,
        values='Nombre',
        names='Catégorie',
        title='Répartition des Trajets par Niveau de Vitesse',
        color='Catégorie',
        color_discrete_map=color_map
    )
    fig2.update_layout(height=450)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Niveaux de Gravité
    
    **Classification des Infractions:**
    - ✅ **Conforme**: Respect de la limite 50 km/h
    - 🟡 **Légère**: 51-60 km/h - Avertissement
    - 🟠 **Modérée**: 61-80 km/h - Sanction mineure
    - 🔴 **Grave**: 81-100 km/h - Sanction majeure
    - 🟣 **Très Grave**: >100 km/h - Suspension possible
    
    **Barème de Sanctions Recommandé:**
    | Catégorie | Sanction |
    |-----------|----------|
    | Légère | Avertissement verbal |
    | Modérée | Avertissement écrit |
    | Grave | Suspension 1 semaine |
    | Très Grave | Suspension 1 mois |
    """)
    
    st.markdown("---")
    st.subheader("🕐 Infractions Jour vs Nuit")
    
    jour_inf = df_jour_v[df_jour_v['Vitesse maxi'] > limite_urbaine]
    nuit_inf = df_nuit_v[df_nuit_v['Vitesse maxi'] > limite_urbaine]
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name='Infractions Jour', x=['Jour', 'Nuit'], y=[len(jour_inf), len(nuit_inf)], 
                          marker_color=['#FFA500', '#1E3A5F']))
    fig3.update_layout(title='Comparaison des Infractions Jour vs Nuit', height=350)
    st.plotly_chart(fig3, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        taux_jour = len(jour_inf) / len(df_jour_v) * 100 if len(df_jour_v) > 0 else 0
        st.warning(f"☀️ **Taux d'infraction jour**: {taux_jour:.1f}%")
    with col2:
        taux_nuit = len(nuit_inf) / len(df_nuit_v) * 100 if len(df_nuit_v) > 0 else 0
        st.error(f"🌙 **Taux d'infraction nuit**: {taux_nuit:.1f}%")
    
    st.markdown("""
    ### 📝 Interprétation - Infractions Temporelles
    
    **Observations:**
    - Le taux d'infraction peut varier entre jour et nuit
    - Les infractions nocturnes sont particulièrement dangereuses
    
    **Risques Nocturnes:**
    - Visibilité réduite
    - Fatigue des conducteurs
    - Moins de surveillance routière
    
    **Recommandations:**
    1. Renforcer la surveillance des vitesses nocturnes
    2. Limiter les trajets nocturnes aux missions essentielles
    3. Installer des limiteurs de vitesse sur les véhicules récidivistes
    """)
    
    st.markdown("---")
    st.subheader("📋 Tableau Récapitulatif des Infractions")
    
    recap = df_vitesse_v[df_vitesse_v['Vitesse maxi'] > limite_urbaine][['Regroupement', 'Vitesse maxi', 'Emplacement initial', "Lieu d'arrivée"]]
    recap = recap.sort_values('Vitesse maxi', ascending=False)
    recap.columns = ['Véhicule', 'Vitesse Max (km/h)', 'Départ', 'Arrivée']
    st.dataframe(recap.head(20), use_container_width=True, hide_index=True)

# ===== PAGE NOTIFICATIONS =====
elif page == "notifications":
    st.title("🔔 Analyse des Notifications")
    st.markdown("---")
    
    df = data['notifications'].copy()
    df = df[df['Nom de notification'] != '-----']
    df = df[df['Nom de notification'].notna()]
    
    st.info(f"📊 **{len(df)} notifications enregistrées cette semaine**")
    
    # Types de notifications
    st.subheader("📊 Distribution des Types de Notifications")
    
    notif_types = df['Nom de notification'].value_counts().reset_index()
    notif_types.columns = ['Type de Notification', 'Nombre']
    
    fig1 = px.pie(
        notif_types,
        values='Nombre',
        names='Type de Notification',
        title='Répartition des Types de Notifications'
    )
    fig1.update_layout(height=450)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Types de Notifications
    
    **Analyse des Alertes:**
    - Les notifications reflètent les événements importants de la flotte
    - La prépondérance de certains types peut indiquer des problèmes récurrents
    
    **Types Courants:**
    - **Perte de Connexion**: Problèmes techniques ou zones non couvertes
    - **Entrée/Sortie POI**: Suivi des passages dans les zones définies
    - **Alertes de Vitesse**: Dépassements des limites autorisées
    """)
    
    # Notifications par véhicule
    st.markdown("---")
    st.subheader("📊 Notifications par Véhicule")
    
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    notif_par_vehicule = df_vehicles.groupby('Regroupement').size().reset_index(name='Nombre')
    notif_par_vehicule = notif_par_vehicule.sort_values('Nombre', ascending=False)
    
    fig2 = px.bar(
        notif_par_vehicule.head(15),
        x='Regroupement',
        y='Nombre',
        title='Top 15 - Véhicules avec le Plus de Notifications',
        color='Nombre',
        color_continuous_scale='Blues'
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Alertes par Véhicule
    
    **Points d'Attention:**
    - Un nombre élevé de notifications peut indiquer des problèmes avec le véhicule ou le conducteur
    - Analyser la nature des notifications pour chaque véhicule problématique
    
    **Actions:**
    1. Examiner en détail les véhicules avec le plus de notifications
    2. Identifier si les alertes sont techniques ou comportementales
    3. Prendre les mesures correctives appropriées
    """)
    
    # Tableau des types par véhicule
    st.markdown("---")
    st.subheader("📋 Détail des Notifications par Type et Véhicule")
    
    pivot = df_vehicles.pivot_table(index='Regroupement', columns='Nom de notification', aggfunc='size', fill_value=0)
    st.dataframe(pivot, use_container_width=True)

# ===== PAGE TEMPS POI =====
elif page == "temps_poi":
    st.title("📍 Analyse du Temps Passé dans les Points d'Intérêt")
    st.markdown("---")
    
    df = data['temps_poi'].copy()
    df = df[df['Regroupement'].notna()]
    
    # Identifier les POI (lignes qui ne sont pas des véhicules)
    vehicles = get_vehicles(data['duree_distance'])
    df_poi = df[~df['Regroupement'].isin(vehicles)]
    df_poi = df_poi[~df_poi['Regroupement'].str.startswith('202', na=False)]
    
    st.subheader("📊 Visites et Temps par Point d'Intérêt")
    
    poi_stats = df_poi.groupby('Regroupement').agg({
        'Visites': 'sum'
    }).reset_index()
    poi_stats.columns = ['POI', 'Total Visites']
    poi_stats = poi_stats.sort_values('Total Visites', ascending=False)
    
    fig1 = px.bar(
        poi_stats.head(15),
        x='POI',
        y='Total Visites',
        title='Top 15 - Points d\'Intérêt les Plus Visités',
        color='Total Visites',
        color_continuous_scale='Greens'
    )
    fig1.update_layout(height=450, xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Fréquentation des POI
    
    **Analyse:**
    - Les points d'intérêt les plus visités reflètent les activités principales de la flotte
    - Ces données permettent d'optimiser les itinéraires et les affectations
    
    **Recommandations:**
    1. Analyser la cohérence des visites avec les missions assignées
    2. Identifier les POI stratégiques pour l'activité
    3. Optimiser les temps de passage dans chaque POI
    """)
    
    # Temps par véhicule dans les POI
    st.markdown("---")
    st.subheader("🚗 Visites POI par Véhicule")
    
    df_vehicules = df[df['Regroupement'].isin(vehicles)]
    
    if len(df_vehicules) > 0:
        visites_vehicule = df_vehicules.groupby('Regroupement')['Visites'].sum().reset_index()
        visites_vehicule = visites_vehicule.sort_values('Visites', ascending=False)
        
        fig2 = px.bar(
            visites_vehicule.head(15),
            x='Regroupement',
            y='Visites',
            title='Nombre de Visites POI par Véhicule',
            color='Visites',
            color_continuous_scale='Teal'
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Activité par Véhicule
    
    **Observations:**
    - Le nombre de visites reflète l'activité de chaque véhicule
    - Permet d'évaluer la productivité relative de chaque véhicule
    
    **Points d'Amélioration:**
    - Équilibrer la charge de travail entre les véhicules
    - Identifier les véhicules sous-utilisés
    """)

# ===== PAGE VISITES POI =====
elif page == "visites_poi":
    st.title("📍 Analyse Détaillée des Visites POI")
    st.markdown("---")
    
    df = data['visites_poi'].copy()
    df = df[df['Regroupement'].notna()]
    
    # Statistiques globales
    total_visites = df['Visites'].sum()
    st.metric("Total des Visites POI", int(total_visites))
    
    # Visites par lieu
    st.subheader("📊 Distribution des Visites par Lieu")
    
    # Séparer POI et véhicules
    vehicles = get_vehicles(data['duree_distance'])
    
    df_poi = df[df['Regroupement'].str.startswith('BP', na=False)]
    
    if len(df_poi) > 0:
        poi_visites = df_poi.groupby('Regroupement')['Visites'].sum().reset_index()
        poi_visites = poi_visites.sort_values('Visites', ascending=False)
        
        fig1 = px.bar(
            poi_visites.head(20),
            x='Regroupement',
            y='Visites',
            title='Top 20 - POI par Nombre de Visites',
            color='Visites',
            color_continuous_scale='Purples'
        )
        fig1.update_layout(height=450, xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Visites par POI
    
    **Analyse Détaillée:**
    - Cette vue permet d'identifier les destinations les plus fréquentes
    - Les POI très visités sont critiques pour les opérations
    
    **Recommandations:**
    1. Optimiser les itinéraires vers les POI les plus fréquentés
    2. Évaluer le temps passé dans chaque POI
    3. Identifier les POI rarement visités qui pourraient être retirés de la liste
    """)
    
    # Visites par véhicule
    st.markdown("---")
    st.subheader("🚗 Visites par Véhicule")
    
    df_vehicles = df[df['Regroupement'].isin(vehicles)]
    
    if len(df_vehicles) > 0:
        vehicle_visites = df_vehicles.groupby('Regroupement')['Visites'].sum().reset_index()
        vehicle_visites = vehicle_visites.sort_values('Visites', ascending=False)
        
        fig2 = px.bar(
            vehicle_visites.head(15),
            x='Regroupement',
            y='Visites',
            title='Visites POI par Véhicule',
            color='Visites',
            color_continuous_scale='Tealgrn'
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Activité des Véhicules
    
    **Observations:**
    - Le nombre de visites par véhicule reflète son niveau d'activité
    - Permet de mesurer la productivité et l'utilisation effective
    
    **Actions:**
    - Comparer avec les objectifs de visites assignés
    - Identifier les véhicules les plus/moins productifs
    """)

# ===== PAGE VITESSE =====
elif page == "vitesse":
    st.title("🏎️ Analyse de la Vitesse de Conduite")
    st.markdown("---")
    
    df = data['vitesse'].copy()
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    # Vitesse maximale par véhicule
    st.subheader("📊 Vitesse Maximale par Véhicule")
    
    vitesse_max = df_vehicles.groupby('Regroupement')['Vitesse maxi'].max().reset_index()
    vitesse_max = vitesse_max.sort_values('Vitesse maxi', ascending=False)
    
    fig1 = px.bar(
        vitesse_max.head(15),
        x='Regroupement',
        y='Vitesse maxi',
        title='Top 15 - Vitesse Maximale Atteinte par Véhicule (km/h)',
        color='Vitesse maxi',
        color_continuous_scale='YlOrRd'
    )
    fig1.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Limite 50 km/h")
    fig1.add_hline(y=80, line_dash="dash", line_color="darkred", annotation_text="Limite 80 km/h")
    fig1.update_layout(height=450)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Identifier les infractions
    infractions = vitesse_max[vitesse_max['Vitesse maxi'] > 50]
    
    if len(infractions) > 0:
        st.error(f"🚨 **{len(infractions)} véhicules ont dépassé la limite de 50 km/h**")
    
    st.markdown("""
    ### 📝 Interprétation - Vitesses Maximales
    
    **Analyse des Infractions:**
    - Les dépassements de vitesse représentent un risque majeur pour la sécurité
    - Chaque infraction doit être documentée et suivie
    
    **Niveaux d'Alerte:**
    - 🟡 50-60 km/h : Avertissement
    - 🟠 60-80 km/h : Infraction modérée
    - 🔴 >80 km/h : Infraction grave
    
    **Actions Recommandées:**
    1. Avertissement formel pour les conducteurs concernés
    2. Formation obligatoire sur la sécurité routière
    3. Sanctions progressives en cas de récidive
    """)
    
    # Distribution des vitesses
    st.markdown("---")
    st.subheader("📈 Distribution des Vitesses Maximales")
    
    fig2 = px.histogram(
        df_vehicles,
        x='Vitesse maxi',
        nbins=20,
        title='Distribution des Vitesses Maximales',
        color_discrete_sequence=['#3366CC']
    )
    fig2.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Limite 50 km/h")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    ### 📝 Interprétation - Profil de Vitesse Global
    
    **Observations:**
    - La distribution montre le comportement général de la flotte
    - L'étalement vers les vitesses élevées indique des comportements à risque
    
    **Indicateurs Clés:**
    - Médiane des vitesses maximales
    - Pourcentage de trajets avec dépassement
    - Fréquence des infractions par conducteur
    """)
    
    # Statistiques détaillées
    st.markdown("---")
    st.subheader("📋 Statistiques de Vitesse par Véhicule")
    
    vitesse_stats = df_vehicles.groupby('Regroupement').agg({
        'Vitesse maxi': ['max', 'mean', 'count']
    }).reset_index()
    vitesse_stats.columns = ['Véhicule', 'Vitesse Max', 'Vitesse Moyenne', 'Nb Trajets']
    vitesse_stats = vitesse_stats.sort_values('Vitesse Max', ascending=False)
    vitesse_stats['Vitesse Moyenne'] = vitesse_stats['Vitesse Moyenne'].round(1)
    
    st.dataframe(vitesse_stats, use_container_width=True, hide_index=True)
    
    st.markdown("""
    ### 📝 Recommandations Finales - Gestion de la Vitesse
    
    1. **Surveillance Active**: Mettre en place des alertes en temps réel pour les dépassements
    2. **Analyse Comportementale**: Identifier les patterns de conduite à risque
    3. **Formation Continue**: Sessions régulières de sensibilisation à la sécurité
    4. **Incentives**: Récompenser les conducteurs respectueux des limites
    5. **Technologie**: Envisager l'installation de limiteurs de vitesse
    """)
