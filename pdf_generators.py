"""
PDF content generators for each analysis page
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def get_vehicles(df):
    """Extract vehicle list from dataframe"""
    vehicles = df['Regroupement'].dropna().unique()
    return [v for v in vehicles if not str(v).startswith('202') and v != '-----']


def generate_synthese_pdf(data):
    """Generate PDF content for Synthèse page"""
    content = []
    
    # Distance par véhicule chart
    df_duree = data['duree_distance'].copy()
    df_vehicles = df_duree[~df_duree['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    distance_par_vehicule = df_vehicles.groupby('Regroupement')['Distance Parcourue'].sum().reset_index()
    distance_par_vehicule = distance_par_vehicule.sort_values('Distance Parcourue', ascending=True)
    
    fig1 = px.bar(
        distance_par_vehicule,
        x='Distance Parcourue',
        y='Regroupement',
        orientation='h',
        title='Distance Totale Parcourue par Véhicule (km)',
        color='Distance Parcourue',
        color_continuous_scale='Blues'
    )
    fig1.update_layout(height=500, showlegend=False)
    
    interpretation1 = """
    Observations Clés:
    - La flotte comprend plusieurs véhicules avec des niveaux d'utilisation très variés
    - Certains véhicules présentent une activité significativement plus importante
    - Les trajets non autorisés représentent un point d'attention majeur
    
    Recommandations:
    1. Optimisation de la flotte: Réévaluer l'affectation des véhicules selon l'utilisation réelle
    2. Suivi des infractions: Mettre en place un système de suivi plus strict pour les trajets non autorisés
    3. Formation conducteurs: Organiser des sessions de sensibilisation sur le respect des règles
    """
    
    content.append({
        'title': 'Vue d\'Ensemble - Distance Totale par Véhicule',
        'figure': fig1,
        'text': interpretation1
    })
    
    # Répartition Jour/Nuit
    trajets_jour = len(data['conduite_journee'][~data['conduite_journee']['Regroupement'].str.startswith('202', na=False)])
    trajets_nuit = len(data['conduite_nocturne'][~data['conduite_nocturne']['Regroupement'].str.startswith('202', na=False)])
    
    fig2 = px.pie(
        values=[trajets_jour, trajets_nuit],
        names=['Conduite de Jour', 'Conduite de Nuit'],
        title='Répartition des Trajets Jour/Nuit',
        color_discrete_sequence=['#FFA500', '#1E3A5F']
    )
    
    interpretation2 = f"""
    Trajets de jour: {trajets_jour} ({trajets_jour/(trajets_jour+trajets_nuit)*100:.1f}%)
    Trajets de nuit: {trajets_nuit} ({trajets_nuit/(trajets_jour+trajets_nuit)*100:.1f}%)
    
    La répartition jour/nuit permet d'évaluer les habitudes de conduite et les risques associés.
    """
    
    content.append({
        'title': 'Répartition Conduite Jour vs Nuit',
        'figure': fig2,
        'text': interpretation2
    })
    
    return content


def generate_duree_pdf(data):
    """Generate PDF content for Durée-Distance-Conso page"""
    content = []
    
    df = data['duree_distance'].copy()
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    # Distance stats
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
    
    interpretation1 = """
    Analyse:
    - Les véhicules présentent des disparités importantes en termes de kilométrage
    - Les véhicules les plus utilisés peuvent nécessiter une maintenance plus fréquente
    
    Points d'attention:
    - Véhicules avec kilométrage élevé: planifier des contrôles techniques
    - Véhicules peu utilisés: évaluer la pertinence de leur maintien dans la flotte
    """
    
    content.append({
        'title': 'Distance Parcourue par Véhicule',
        'figure': fig1,
        'text': interpretation1
    })
    
    # Nb trajets
    fig2 = px.bar(
        distance_stats.sort_values('Nb Trajets', ascending=False).head(15),
        x='Véhicule',
        y='Nb Trajets',
        title='Top 15 - Nombre de Trajets par Véhicule',
        color='Nb Trajets',
        color_continuous_scale='Oranges'
    )
    
    interpretation2 = """
    Observations:
    - La fréquence des trajets varie considérablement selon les véhicules
    - Un nombre élevé de trajets courts peut indiquer des missions de proximité
    
    Recommandations:
    1. Analyser la corrélation entre nombre de trajets et type de mission
    2. Optimiser les affectations pour réduire les trajets à vide
    """
    
    content.append({
        'title': 'Nombre de Trajets par Véhicule',
        'figure': fig2,
        'text': interpretation2
    })
    
    return content


def generate_trajets_pdf(data):
    """Generate PDF content for Trajets Non Autorisés page"""
    content = []
    
    df = data['trajets_non_autorises'].copy()
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    # Incidents par véhicule
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
    
    interpretation1 = f"""
    {len(df_vehicles)} incidents de trajets non autorisés détectés cette semaine
    
    Analyse Critique:
    - Certains véhicules montrent un nombre d'incidents particulièrement élevé
    - Ces véhicules nécessitent une attention immédiate et un suivi renforcé
    
    Actions Recommandées:
    1. Priorité Haute: Convoquer les conducteurs des véhicules les plus problématiques
    2. Priorité Moyenne: Mettre en place un système d'alerte en temps réel
    3. Amélioration Continue: Former les conducteurs sur les zones autorisées
    """
    
    content.append({
        'title': 'Nombre d\'Incidents par Véhicule',
        'figure': fig1,
        'text': interpretation1
    })
    
    return content


def generate_jour_nuit_pdf(data):
    """Generate PDF content for Conduite Jour vs Nuit page"""
    content = []
    
    df_jour = data['conduite_journee'].copy()
    df_nuit = data['conduite_nocturne'].copy()
    
    df_jour_v = df_jour[~df_jour['Regroupement'].str.startswith('202', na=False)]
    df_jour_v = df_jour_v[df_jour_v['Regroupement'].notna()]
    
    df_nuit_v = df_nuit[~df_nuit['Regroupement'].str.startswith('202', na=False)]
    df_nuit_v = df_nuit_v[df_nuit_v['Regroupement'].notna()]
    
    # Kilométrage jour vs nuit
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
    
    interpretation = """
    Observations:
    - La majorité des trajets s'effectuent de jour, ce qui est conforme aux bonnes pratiques
    - Certains véhicules présentent une activité nocturne significative
    
    Points de Vigilance:
    - La conduite nocturne présente des risques accrus (fatigue, visibilité réduite)
    - Vérifier que les conducteurs de nuit sont bien reposés
    """
    
    content.append({
        'title': 'Kilométrage Jour vs Nuit par Véhicule',
        'figure': fig,
        'text': interpretation
    })
    
    return content


# Map page names to generator functions
PDF_GENERATORS = {
    'synthese': generate_synthese_pdf,
    'duree': generate_duree_pdf,
    'trajets': generate_trajets_pdf,
    'jour_nuit': generate_jour_nuit_pdf,
    # Add more as needed
}
