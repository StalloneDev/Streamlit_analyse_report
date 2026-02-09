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
**Observations Clés:**
- La flotte comprend plusieurs véhicules avec des niveaux d'utilisation très variés
- Certains véhicules présentent une activité significativement plus importante
- Les trajets non autorisés représentent un point d'attention majeur

**Recommandations:**
1. **Optimisation de la flotte**: Réévaluer l'affectation des véhicules selon l'utilisation réelle
2. **Suivi des infractions**: Mettre en place un système de suivi plus strict pour les trajets non autorisés
3. **Formation conducteurs**: Organiser des sessions de sensibilisation sur le respect des règles
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
    
    interpretation1 = """
**Analyse:**
- Les véhicules présentent des disparités importantes en termes de kilométrage
- Les véhicules les plus utilisés peuvent nécessiter une maintenance plus fréquente
- L'écart entre le véhicule le plus et le moins utilisé indique une possible sous-utilisation de certains véhicules

**Points d'attention:**
- 🔴 Véhicules avec kilométrage élevé: planifier des contrôles techniques
- 🟡 Véhicules peu utilisés: évaluer la pertinence de leur maintien dans la flotte
"""

    content.append({
        'title': 'Distance Parcourue',
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
**Observations:**
- La fréquence des trajets varie considérablement selon les véhicules
- Un nombre élevé de trajets courts peut indiquer des missions de proximité
- Un faible nombre de trajets longs peut indiquer des missions inter-régionales

**Recommandations:**
1. Analyser la corrélation entre nombre de trajets et type de mission
2. Optimiser les affectations pour réduire les trajets à vide
"""

    content.append({
        'title': 'Fréquence des Trajets',
        'figure': fig2,
        'text': interpretation2
    })

    # Profil d'utilisation
    interpretation3 = """
**Types de profils identifiés:**
- **Courte distance / Haute fréquence**: Missions urbaines et livraisons locales
- **Longue distance / Basse fréquence**: Missions inter-villes ou régionales
- **Usage mixte**: Véhicules polyvalents

**Recommandations:**
- Adapter le type de véhicule au profil de mission
- Considérer des véhicules économiques pour les trajets urbains fréquents
"""
    content.append({
        'title': 'Profil d\'Utilisation',
        'text': interpretation3
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
    
    interpretation1 = """
**Analyse Critique:**
- Certains véhicules montrent un nombre d'incidents particulièrement élevé
- Ces véhicules nécessitent une attention immédiate et un suivi renforcé
- La récurrence d'incidents sur les mêmes véhicules peut indiquer des problèmes systémiques

**Actions Recommandées:**
1. 🔴 **Priorité Haute**: Convoquer les conducteurs des véhicules les plus problématiques
2. 🟠 **Priorité Moyenne**: Mettre en place un système d'alerte en temps réel
3. 🟡 **Amélioration Continue**: Former les conducteurs sur les zones autorisées
"""

    content.append({
        'title': 'Nombre d\'Incidents par Véhicule',
        'figure': fig1,
        'text': interpretation1
    })
    
    # Kilométrage non autorisé
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
    
    interpretation2 = """
**Coût Estimé des Trajets Non Autorisés:**
- Consommation de carburant supplémentaire
- Usure prématurée des véhicules
- Risques d'accidents hors zones couvertes

**Recommandations:**
- Calculer le coût financier des trajets non autorisés
- Établir des sanctions progressives selon le kilométrage
"""

    content.append({
        'title': 'Kilométrage Non Autorisé',
        'figure': fig2,
        'text': interpretation2
    })

    # Vitesse lors des incidents
    vitesse_incidents = df_vehicles.groupby('Regroupement')['Vitesse maxi'].max().reset_index()
    vitesse_incidents = vitesse_incidents.sort_values('Vitesse maxi', ascending=False)
    
    fig3 = px.bar(
        vitesse_incidents.head(15),
        x='Regroupement',
        y='Vitesse maxi',
        title='Vitesse Maximale lors d\'Incidents',
        color='Vitesse maxi',
        color_continuous_scale='YlOrRd'
    )
    fig3.add_hline(y=50, line_dash="dash", line_color="red")
    
    interpretation3 = """
**Alerte Sécurité:**
- Les vitesses élevées lors de trajets non autorisés augmentent considérablement le risque d'accidents
- Ces comportements doivent être traités avec la plus grande priorité

**Actions Immédiates:**
1. Identifier les conducteurs concernés
2. Organiser des entretiens individuels
3. Envisager des mesures disciplinaires si récidive
"""

    content.append({
        'title': 'Vitesse pendant les Incidents',
        'figure': fig3,
        'text': interpretation3
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
    
    interpretation1 = """
**Observations:**
- La majorité des trajets s'effectuent de jour, ce qui est conforme aux bonnes pratiques
- Certains véhicules présentent une activité nocturne significative
- L'activité nocturne peut être justifiée par des missions spécifiques

**Points de Vigilance:**
- 🌙 La conduite nocturne présente des risques accrus (fatigue, visibilité réduite)
- Vérifier que les conducteurs de nuit sont bien reposés
- S'assurer que les trajets nocturnes sont justifiés
"""

    content.append({
        'title': 'Kilométrage Jour vs Nuit par Véhicule',
        'figure': fig,
        'text': interpretation1
    })

    interpretation2 = """
**Analyse des Vitesses:**
- Comparer les vitesses jour/nuit permet d'identifier les comportements à risque
- Une vitesse élevée de nuit est particulièrement dangereuse

**Recommandations:**
1. Limiter les vitesses autorisées de nuit à un seuil inférieur
2. Mettre en place des alertes automatiques pour excès de vitesse nocturne
3. Sensibiliser les conducteurs aux risques de la conduite rapide de nuit
"""
    content.append({
        'title': 'Analyse des Vitesses Jour vs Nuit',
        'text': interpretation2
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
    
    interpretation1 = """
**Analyse des Dépassements:**
- Les véhicules listés ont dépassé la limite de 50 km/h (zone urbaine)
- Un nombre élevé d'infractions indique un comportement à risque récurrent

**Actions Prioritaires:**
1. 🔴 Convoquer les conducteurs des véhicules avec > 5 infractions
2. 🟠 Avertissement formel pour 2-5 infractions
3. 🟡 Sensibilisation pour < 2 infractions
"""

    content.append({
        'title': 'Infractions par Véhicule',
        'figure': fig1,
        'text': interpretation1
    })

    interpretation2 = """
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
"""
    content.append({
        'title': 'Niveaux de Gravité et Sanctions',
        'text': interpretation2
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
    
    interpretation1 = """
**Analyse des Alertes:**
- Les notifications reflètent les événements importants de la flotte
- La prépondérance de certains types peut indiquer des problèmes récurrents

**Types Courants:**
- **Perte de Connexion**: Problèmes techniques ou zones non couvertes
- **Entrée/Sortie POI**: Suivi des passages dans les zones définies
- **Alertes de Vitesse**: Dépassements des limites autorisées
"""

    content.append({
        'title': 'Distribution des Notifications',
        'figure': fig1,
        'text': interpretation1
    })

    interpretation2 = """
**Points d'Attention:**
- Un nombre élevé de notifications peut indiquer des problèmes avec le véhicule ou le conducteur
- Analyser la nature des notifications pour chaque véhicule problématique

**Actions:**
1. Examiner en détail les véhicules avec le plus de notifications
2. Identifier si les alertes sont techniques ou comportementales
3. Prendre les mesures correctives appropriées
"""
    content.append({
        'title': 'Analyse des Alertes par Véhicule',
        'text': interpretation2
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
    
    interpretation1 = """
**Analyse:**
- Les points d'intérêt les plus visités reflètent les activités principales de la flotte
- Ces données permettent d'optimiser les itinéraires et les affectations

**Recommandations:**
1. Analyser la cohérence des visites avec les missions assignées
2. Identifier les POI stratégiques pour l'activité
3. Optimiser les temps de passage dans chaque POI
"""

    content.append({
        'title': 'Fréquentation des POI',
        'figure': fig1,
        'text': interpretation1
    })

    interpretation2 = """
**Observations:**
- Le nombre de visites reflète l'activité de chaque véhicule
- Permet d'évaluer la productivité relative de chaque véhicule

**Points d'Amélioration:**
- Équilibrer la charge de travail entre les véhicules
- Identifier les véhicules sous-utilisés
"""
    content.append({
        'title': 'Analyse de l\'Activité par Véhicule',
        'text': interpretation2
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
    
    interpretation1 = """
**Analyse Détaillée:**
- Cette vue permet d'identifier les destinations les plus fréquentes
- Les POI très visités sont critiques pour les opérations

**Recommandations:**
1. Optimiser les itinéraires vers les POI les plus fréquentés
2. Évaluer le temps passé dans chaque POI
3. Identifier les POI rarement visités qui pourraient être retirés de la liste
"""

    content.append({
        'title': 'Visites par Véhicule',
        'figure': fig2,
        'text': interpretation1
    })

    interpretation2 = """
**Observations:**
- Le nombre de visites par véhicule reflète son niveau d'activité
- Permet de mesurer la productivité et l'utilisation effective

**Actions:**
- Comparer avec les objectifs de visites assignés
- Identifier les véhicules les plus/moins productifs
"""
    content.append({
        'title': 'Productivité des Véhicules',
        'text': interpretation2
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
    
    interpretation1 = """
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
"""

    content.append({
        'title': 'Vitesse Maximale par Véhicule',
        'figure': fig1,
        'text': interpretation1
    })

    interpretation2 = """
1. **Surveillance Active**: Mettre en place des alertes en temps réel pour les dépassements
2. **Analyse Comportementale**: Identifier les patterns de conduite à risque
3. **Formation Continue**: Sessions régulières de sensibilisation à la sécurité
4. **Incentives**: Récompenser les conducteurs respectueux des limites
5. **Technologie**: Envisager l'installation de limiteurs de vitesse
"""
    content.append({
        'title': 'Recommandations Finales',
        'text': interpretation2
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
