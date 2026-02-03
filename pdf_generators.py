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
    
    # Calcul des métriques
    df_duree = data['duree_distance'].copy()
    vehicles = get_vehicles(df_duree)
    total_trajets = len(df_duree[~df_duree['Regroupement'].str.startswith('202', na=False)])
    
    df_trajets = data['trajets_non_autorises']
    trajets_non_auth = len(df_trajets[~df_trajets['Regroupement'].str.startswith('202', na=False)])
    
    df_notif = data['notifications']
    total_notifications = len(df_notif[df_notif['Nom de notification'] != '-----'])
    
    # Section Métriques
    content.append({
        'title': 'Synthèse Globale',
        'metrics': [
            {'label': 'Véhicules Actifs', 'value': len(vehicles)},
            {'label': 'Total Trajets', 'value': total_trajets},
            {'label': 'Trajets Non Autorisés', 'value': trajets_non_auth},
            {'label': 'Notifications', 'value': total_notifications}
        ]
    })
    
    # Graphique résumé - Distance par véhicule
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
    """
    
    content.append({
        'title': 'Vue d\'Ensemble - Distance',
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
    
    # Round for display
    display_stats = distance_stats.copy()
    display_stats['Distance Totale'] = display_stats['Distance Totale'].round(2)
    display_stats['Distance Moyenne'] = display_stats['Distance Moyenne'].round(2)
    
    content.append({
        'title': 'Statistiques Détaillées',
        'table': display_stats.head(20)
    })
    
    fig1 = px.bar(
        distance_stats.head(15),
        x='Véhicule',
        y='Distance Totale',
        title='Top 15 - Distance Totale par Véhicule (km)',
        color='Distance Totale',
        color_continuous_scale='Viridis'
    )
    
    content.append({
        'title': 'Distance Parcourue',
        'figure': fig1,
        'text': "Les véhicules les plus utilisés peuvent nécessiter une maintenance plus fréquente."
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
    
    content.append({
        'title': 'Fréquence des Trajets',
        'figure': fig2,
        'text': "La fréquence des trajets varie considérablement selon les véhicules."
    })
    
    return content

def generate_trajets_pdf(data):
    """Generate PDF content for Trajets Non Autorisés page"""
    content = []
    
    df = data['trajets_non_autorises'].copy()
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    df_vehicles = df_vehicles[df_vehicles['Regroupement'].notna()]
    
    content.append({
        'title': 'Alerte Incidents',
        'metrics': [{'label': 'Incidents Détectés', 'value': len(df_vehicles)}]
    })
    
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
    
    content.append({
        'title': 'Nombre d\'Incidents par Véhicule',
        'figure': fig1,
        'text': "Certains véhicules montrent un nombre d'incidents particulièrement élevé."
    })
    
    # Tableau des incidents
    # Columns to try to include
    cols_to_include = ['Regroupement', 'date_debut', 'Lieu de départ', "Lieu d'arrivée", 'Kilométrage']
    # Filter only existing columns
    existing_cols = [c for c in cols_to_include if c in df_vehicles.columns]
    
    if existing_cols:
        recap = df_vehicles[existing_cols].head(20)
        if 'Kilométrage' in recap.columns:
            recap['Kilométrage'] = recap['Kilométrage'].round(2)
        
        content.append({
            'title': 'Détail des Derniers Incidents',
            'table': recap
        })
    
    return content

def generate_jour_nuit_pdf(data):
    """Generate PDF content for Conduite Jour vs Nuit page"""
    content = []
    
    df_jour = data['conduite_journee'].copy()
    df_nuit = data['conduite_nocturne'].copy()
    
    df_jour_v = df_jour[~df_jour['Regroupement'].str.startswith('202', na=False)]
    df_nuit_v = df_nuit[~df_nuit['Regroupement'].str.startswith('202', na=False)]
    
    # Metrics
    content.append({
        'title': 'Comparaison Globale',
        'metrics': [
            {'label': 'Trajets Jour', 'value': len(df_jour_v)},
            {'label': 'Distance Jour (km)', 'value': int(df_jour_v['Kilométrage'].sum())},
            {'label': 'Trajets Nuit', 'value': len(df_nuit_v)},
            {'label': 'Distance Nuit (km)', 'value': int(df_nuit_v['Kilométrage'].sum())}
        ]
    })
    
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
    
    content.append({
        'title': 'Kilométrage Jour vs Nuit par Véhicule',
        'figure': fig,
        'text': "La conduite nocturne présente des risques accrus. Vérifier que les conducteurs de nuit sont bien reposés."
    })
    
    return content

def generate_limitation_vitesse_pdf(data):
    """Generate PDF for Limitation Vitesse"""
    content = []
    
    df_vitesse = data['vitesse'].copy()
    df_v = df_vitesse[~df_vitesse['Regroupement'].str.startswith('202', na=False)]
    df_v = df_v[df_v['Regroupement'].notna()]
    
    infractions_50 = df_v[df_v['Vitesse maxi'] > 50]
    infractions_90 = df_v[df_v['Vitesse maxi'] > 90]
    
    content.append({
        'title': 'Bilan des Infractions',
        'metrics': [
            {'label': 'Infractions > 50 km/h', 'value': len(infractions_50)},
            {'label': 'Infractions > 90 km/h', 'value': len(infractions_90)}
        ]
    })
    
    # Chart infractions
    inf_par_vehicule = infractions_50.groupby('Regroupement').size().reset_index(name='Nb Infractions')
    inf_par_vehicule = inf_par_vehicule.sort_values('Nb Infractions', ascending=False)
    
    fig1 = px.bar(
        inf_par_vehicule.head(15),
        x='Regroupement',
        y='Nb Infractions',
        title='Top 15 - Véhicules avec le Plus d\'Infractions',
        color='Nb Infractions', 
        color_continuous_scale='Reds'
    )
    
    content.append({
        'title': 'Infractions par Véhicule',
        'figure': fig1
    })
    
    # Table recap
    recap = df_v[df_v['Vitesse maxi'] > 50][['Regroupement', 'Vitesse maxi', 'Emplacement initial', "Lieu d'arrivée"]]
    recap = recap.sort_values('Vitesse maxi', ascending=False).head(20)
    
    content.append({
        'title': 'Détail des Excès de Vitesse',
        'table': recap
    })
    
    return content

def generate_notifications_pdf(data):
    """Generate PDF for Notifications"""
    content = []
    
    df = data['notifications'].copy()
    df = df[df['Nom de notification'] != '-----']
    df = df[df['Nom de notification'].notna()]
    
    content.append({
        'title': 'Synthèse des Notifications',
        'metrics': [{'label': 'Total Notifications', 'value': len(df)}]
    })
    
    # Pie chart
    notif_types = df['Nom de notification'].value_counts().reset_index()
    notif_types.columns = ['Type', 'Nombre']
    
    fig1 = px.pie(
        notif_types,
        values='Nombre',
        names='Type',
        title='Répartition des Types de Notifications'
    )
    
    content.append({
        'title': 'Distribution des Notifications',
        'figure': fig1
    })
    
    # Table top vehicles
    df_vehicles = df[~df['Regroupement'].str.startswith('202', na=False)]
    notif_par_vehicule = df_vehicles.groupby('Regroupement').size().reset_index(name='Nombre')
    notif_par_vehicule = notif_par_vehicule.sort_values('Nombre', ascending=False).head(20)
    
    content.append({
        'title': 'Véhicules les plus notifiés',
        'table': notif_par_vehicule
    })
    
    return content

def generate_temps_poi_pdf(data):
    """Generate PDF for Temps POI"""
    content = []
    
    df = data['temps_poi'].copy()
    vehicles = get_vehicles(data['duree_distance'])
    df_poi = df[~df['Regroupement'].isin(vehicles)]
    
    poi_stats = df_poi.groupby('Regroupement')['Visites'].sum().reset_index()
    poi_stats.columns = ['POI', 'Visites']
    poi_stats = poi_stats.sort_values('Visites', ascending=False)
    
    fig1 = px.bar(
        poi_stats.head(15),
        x='POI',
        y='Visites',
        title='Top 15 - Points d\'Intérêt les Plus Visités'
    )
    
    content.append({
        'title': 'Fréquentation des POI',
        'figure': fig1
    })
    
    content.append({
        'title': 'Détail des Visites par POI',
        'table': poi_stats.head(20)
    })
    
    return content

def generate_visites_poi_pdf(data):
    """Generate PDF for Visites POI"""
    content = []
    
    df = data['visites_poi'].copy()
    
    content.append({
        'title': 'Activité POI',
        'metrics': [{'label': 'Total Visites', 'value': int(df['Visites'].sum())}]
    })
    
    # Visites par véhicule
    vehicles = get_vehicles(data['duree_distance'])
    df_vehicles = df[df['Regroupement'].isin(vehicles)]
    
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
    
    content.append({
        'title': 'Visites par Véhicule',
        'figure': fig2
    })
    
    return content

def generate_vitesse_pdf(data):
    """Generate PDF for Vitesse"""
    content = []
    
    df = data['vitesse'].copy()
    df_v = df[~df['Regroupement'].str.startswith('202', na=False)]
    
    vitesse_max = df_v.groupby('Regroupement')['Vitesse maxi'].max().reset_index()
    vitesse_max = vitesse_max.sort_values('Vitesse maxi', ascending=False)
    
    infractions = len(vitesse_max[vitesse_max['Vitesse maxi'] > 50])
    
    content.append({
        'title': 'Analyse Vitesse',
        'metrics': [{'label': 'Véhicules en infraction (>50)', 'value': infractions}]
    })
    
    fig1 = px.bar(
        vitesse_max.head(15),
        x='Regroupement',
        y='Vitesse maxi',
        title='Top 15 - Vitesse Maximale',
        color='Vitesse maxi',
        color_continuous_scale='YlOrRd'
    )
    fig1.add_hline(y=50, line_dash="dash", line_color="red")
    
    content.append({
        'title': 'Vitesse Maximale par Véhicule',
        'figure': fig1
    })
    
    # Stats table
    stats = df_v.groupby('Regroupement').agg({
        'Vitesse maxi': ['max', 'mean']
    }).reset_index()
    stats.columns = ['Véhicule', 'Vitesse Max', 'Vitesse Moy']
    stats = stats.sort_values('Vitesse Max', ascending=False).head(20)
    stats['Vitesse Moy'] = stats['Vitesse Moy'].round(1)
    
    content.append({
        'title': 'Statistiques Détaillées',
        'table': stats
    })
    
    return content

# Map page names to generator functions
PDF_GENERATORS = {
    'synthese': generate_synthese_pdf,
    'duree': generate_duree_pdf,
    'trajets': generate_trajets_pdf,
    'jour_nuit': generate_jour_nuit_pdf,
    'limitation_vitesse': generate_limitation_vitesse_pdf,
    'notifications': generate_notifications_pdf,
    'temps_poi': generate_temps_poi_pdf,
    'visites_poi': generate_visites_poi_pdf,
    'vitesse': generate_vitesse_pdf
}



def generate_full_report(data):
    """Generate comprehensive PDF with all sections"""
    full_content = []
    
    # Define order of sections
    sections = [
        ('synthese', "Synthèse Générale"),
        ('duree', "Durée - Distance - Conso"),
        ('trajets', "Trajets Non Autorisés"),
        ('jour_nuit', "Conduite Jour vs Nuit"),
        ('limitation_vitesse', "Limitation de Vitesse"),
        ('notifications', "Notifications"),
        ('temps_poi', "Temps dans POI"),
        ('visites_poi', "Visites POI"),
        ('vitesse', "Vitesse de Conduite")
    ]
    
    for page_key, page_title in sections:
        if page_key in PDF_GENERATORS:
            # Add section header
            full_content.append({
                'title': f"=== {page_title} ===",
                'text': ""  # Just a spacer/header
            })
            
            # Generate content for this section
            section_content = PDF_GENERATORS[page_key](data)
            full_content.extend(section_content)
            
    return full_content

def generate_structured_report(data):
    """Generate structured content dict for Excel export"""
    structured_content = {}
    
    sections = [
        ('synthese', "Synthèse Générale"),
        ('duree', "Durée - Distance"),
        ('trajets', "Trajets Non Autorisés"),
        ('jour_nuit', "Jour vs Nuit"),
        ('limitation_vitesse', "Infractions Vitesse"),
        ('notifications', "Notifications"),
        ('temps_poi', "Temps & Visites POI"),
        ('visites_poi', "Détail Visites POI"), # Optional or merge?
        ('vitesse', "Vitesse de Conduite")
    ]
    
    for page_key, sheet_name in sections:
        if page_key in PDF_GENERATORS:
            structured_content[sheet_name] = PDF_GENERATORS[page_key](data)
            
    return structured_content
