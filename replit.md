# Rapport d'Analyses BP - SADCI GAS PARAKOU

## Overview
Application Streamlit de rapport d'analyses détaillées pour la flotte de véhicules BP - SADCI GAS PARAKOU. 
L'application analyse les données de suivi GPS et fournit des interprétations complètes avec recommandations actionnables.

## Recent Changes
- 02/02/2026: Création de l'application complète avec 8 pages d'analyses

## Project Architecture

### Structure des Fichiers
- `app.py`: Application principale Streamlit avec navigation multi-pages
- `attached_assets/`: Fichier Excel source des données

### Pages de l'Application
1. **Synthèse Générale**: Vue d'ensemble avec métriques clés et graphiques résumés
2. **Durée - Distance - Conso**: Analyse par véhicule (distance, trajets, profil d'utilisation)
3. **Trajets Non Autorisés**: Analyse des incidents et comportements à risque
4. **Conduite Jour vs Nuit**: Comparaison des activités diurnes et nocturnes
5. **Notifications**: Types et fréquence des alertes
6. **Temps dans POI**: Temps passé dans les Points d'Intérêt
7. **Visites POI**: Analyse détaillée des visites par lieu et véhicule
8. **Vitesse de Conduite**: Analyse des infractions de vitesse

### Technologies Utilisées
- Streamlit (interface web)
- Pandas (manipulation des données)
- Plotly (graphiques interactifs)
- OpenPyXL (lecture Excel)

## Data Structure
Le fichier Excel contient les feuilles suivantes:
- Durée - Distance - Conso (1055 lignes)
- Trajets Non Autorisé (285 lignes)
- Conduite en Journée (747 lignes)
- Conduite nocturne (171 lignes)
- Notifications (823 lignes)
- Temps passé dans POI (150 lignes)
- Visites POI (445 lignes)
- Vitesse de conduite (140 lignes)

## User Preferences
- Langue: Français
- Graphiques: Ne pas mélanger les catégories hétérogènes (dates + véhicules)
- Chaque catégorie d'analyse dans une page séparée avec interprétations détaillées
