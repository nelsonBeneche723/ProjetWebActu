from django.shortcuts import render, get_object_or_404, HttpResponse, redirect
from django.conf import settings
from django.http import StreamingHttpResponse, JsonResponse
import os
import random
from datetime import datetime
import google.generativeai as genai  # Pour l'utilisation de l'IA Gemini
from google import genai as genai_client
from google.genai import types
import feedparser
from babel.dates import format_datetime
from django.template.loader import render_to_string
from .models import Station, Article, Musiques, Profil, Commentaire, ChaineTV, Playlist
from django.contrib.auth.models import User
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
import sqlite3
import requests
import io
import matplotlib.pyplot as plt
import base64
import pytz
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from pyradios import RadioBrowser
from django.utils import timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import traceback

logger = logging.getLogger(__name__)


# Create your views here.
# Avatar pour les profils utilisateurs
avatar_definis = [('avatar-1', 'https://i.pravatar.cc/150?img=1'),
                  ('avatar-2','https://i.pravatar.cc/150?img=5'),
                  ('avatar-3 (Masculin)','https://i.pravatar.cc/150?img=12'),
                  ('avatar-4 (Feminin)', 'https://i.pravatar.cc/150?img=42'),
                  ('avatar-5', 'https://i.pravatar.cc/150?img=68'),
                  ]
def calendriermatch():
    API_KEY = settings.API_KEY_SPORTS
    url = 'https://api.football-data.org/v4/matches'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    resultat = []
    try:
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            if matches:
                # Regrouper par date, puis par compétition
                grouped_matches = defaultdict(lambda: defaultdict(list))
                # parcourir les matches
                for match in matches:
                    # Convertir date UTC en heure Port au Prince et extraire la date et l'heure
                    dt_utc = match['utcDate'] # format date: 2021-09-09T19:01:00Z
                    date_formate = datetime.strptime(dt_utc, '%Y-%m-%dT%H:%M:%SZ')
                    py_tz = pytz.timezone('America/Port-au-Prince')
                    localdate = date_formate.astimezone(py_tz)
                    date = localdate.date()
                    # convertir par exemple august=aout
                    date_f = format_date(date, format='d MMMM y', locale='fr')
                    time_str = localdate.time().strftime('%H:%M')
                    # competitions (nom competition, domicile, a l'extérieur)
                    competition = match['competition']['name']
                    home = match['homeTeam']['name']
                    away = match['awayTeam']['name']
                    grouped_matches[date_f][competition].append(f"{time_str} — {home} vs {away}")
                    # ✅ Affichage
                for date_f, comps in grouped_matches.items():
                    for comp, matchs in comps.items():
                        for m in matchs:
                            resultat.append({"date": f"{date_f}", 'competition': comp, 'match': m})
                return resultat
            else:
                print("Aucun match disponible.")
    except Exception as e:
        return None, str(e)

def matchsencours_premierleague():
    API_KEY = settings.API_KEY_SPORTS    # Remplace par ta vraie clé API
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/PL/matches?status=IN_PLAY'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    resultat_mpl = []
    data = response.json()
    # verifier l'api renvoie une response(ok)
    try:
        if response.status_code == 200:
            for match in data.get('matches', []):
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                # scores equipe dehors, equipe domicile
                score_home = match['score']['fullTime']['home']
                score_away = match['score']['fullTime']['away']
                # date
                utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
                date_ = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                py_tz = pytz.timezone('America/Port-au-Prince')
                localdate = date_.astimezone(py_tz)
                localdate = localdate - timedelta(hours=4)
                date = localdate.date()
                # convertir par exemple august=aout
                date_f = format_date(date, format='d MMMM y', locale='fr')
                heure_utc = localdate.time().strftime('%H:%M')
                status = match['status']  # SCHEDULED, FINISHED, e`tc.
                competition = match['competition']['name']
                minutes = match['score']['duration']
                # ajouter les resultats dans une liste contenant un dictionnaire
                resultat_mpl.append({
                    'home': home_team,
                    'away': away_team,
                    'score': f"{score_home} - {score_away}",
                    'status': status,
                    'date': f"{date_f}/{heure_utc}",
                    'competition': competition,
                    'minutes': minutes
                })
            return resultat_mpl
    except Exception as e:
        return None, str(e)

def matchsencours_liga():
    API_KEY = settings.API_KEY_SPORTS
    url = 'https://api.football-data.org/v4/competitions/PD/matches?status=IN_PLAY'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    resultat_mpd = []
    # verifier l'api renvoie une response(ok)
    try:
        if response.status_code == 200:
            data = response.json()
            for match in data.get('matches', []):
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                # scores equipe dehors, equipe domicile
                score_home = match['score']['fullTime']['home']
                score_away = match['score']['fullTime']['away']
                # date
                utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
                date_ = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                py_tz = pytz.timezone('America/Port-au-Prince')
                localdate = date_.astimezone(py_tz)
                localdate = localdate - timedelta(hours=4)
                date = localdate.date()
                # convertir par exemple august=aout
                date_f = format_date(date, format='d MMMM y', locale='fr')
                heure_utc = localdate.time().strftime('%H:%M')
                status = match['status']  # SCHEDULED, FINISHED, e`tc.
                competition = match['competition']['name']
                minutes = match['score']['duration']
                # ajouter les resultats dans une liste contenant un dictionnaire
                resultat_mpd.append({
                    'home': home_team,
                    'away': away_team,
                    'score': f"{score_home} - {score_away}",
                    'status': status,
                    'date': f'{date_f}/{heure_utc}',
                    'competition': competition,
                    'minutes': minutes
                })
            return resultat_mpd
    except Exception as e:
        return None, str(e)

def matchsencours_seriea():
    API_KEY = settings.API_KEY_SPORTS
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/SA/matches?status=IN_PLAY'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    resultat_msa = []
    try:
        # verifier l'api renvoie une response(ok)
        if response.status_code == 200:
            data = response.json()
            for match in data.get('matches', []):
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                # scores equipe dehors, equipe domicile
                score_home = match['score']['fullTime']['home']
                score_away = match['score']['fullTime']['away']
                # date
                utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
                date_ = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                py_tz = pytz.timezone('America/Port-au-Prince')
                localdate = date_.astimezone(py_tz)
                localdate = localdate - timedelta(hours=4)
                date = localdate.date()
                # convertir par exemple august=aout
                date_f = format_date(date, format='d MMMM y', locale='fr')
                heure_utc = localdate.time().strftime('%H:%M')
                status = match['status']  # SCHEDULED, FINISHED, e`tc.
                competition = match['competition']['name']
                minutes = match['score']['duration']
                # ajouter les resultats dans une liste contenant un dictionnaire
                resultat_msa.append({
                    'home': home_team,
                    'away': away_team,
                    'score': f"{score_home} - {score_away}",
                    'status': status,
                    'date': f'{date_f}/{heure_utc}',
                    'competition': competition,
                    'minutes': minutes
                })
            return resultat_msa
    except Exception as e:
        return None, str(e)

def matchsencours_bundesliga():
    API_KEY = settings.API_KEY_SPORTS
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/BL1/matches?status=IN_PLAY'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    resultat_mbl1 = []
    # verifier l'api renvoie une response(ok)
    try:
        if response.status_code == 200:
            data = response.json()
            for match in data.get('matches', []):
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                # scores equipe dehors, equipe domicile
                score_home = match['score']['fullTime']['home']
                score_away = match['score']['fullTime']['away']
                # date
                utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
                date_ = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                py_tz = pytz.timezone('America/Port-au-Prince')
                localdate = date_.astimezone(py_tz)
                localdate = localdate - timedelta(hours=4)
                date = localdate.date()
                # convertir par exemple august=aout
                date_f = format_date(date, format='d MMMM y', locale='fr')
                heure_utc = localdate.time().strftime('%H:%M')
                status = match['status']  # SCHEDULED, FINISHED, e`tc.
                competition = match['competition']['name']
                minutes = match['score']['duration']
                # ajouter les resultats dans une liste contenant un dictionnaire
                resultat_mbl1.append({
                    'home': home_team,
                    'away': away_team,
                    'score': f"{score_home} - {score_away}",
                    'status': status,
                    'date': f'{date_f}/{heure_utc}',
                    'competition': competition,
                    'minutes': minutes
                })
            return resultat_mbl1
    except Exception as e:
        return None, str(e)

def matchsencours_ligue1():
    API_KEY = settings.API_KEY_SPORTS
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/FL1/matches?status=IN_PLAY'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    resultat_mfl1 = []
    # verifier l'api renvoie une response(ok)
    try:
        if response.status_code == 200:
            data = response.json()
            for match in data.get('matches', []):
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                # scores équipe dehors, équipe domicile
                score_home = match['score']['fullTime']['home']
                score_away = match['score']['fullTime']['away']
                # date
                utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
                date_ = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                py_tz = pytz.timezone('America/Port-au-Prince')
                localdate = date_.astimezone(py_tz)
                localdate = localdate - timedelta(hours=4)
                date = localdate.date()
                # convertir par exemple august=aout
                date_f = format_date(date, format='d MMMM y', locale='fr')
                heure_utc = localdate.time().strftime('%H:%M')
                status = match['status']  # SCHEDULED, FINISHED, e`tc.
                competition = match['competition']['name']
                minutes = match['score']['duration']
                # ajouter les résultats dans une liste contenant un dictionnaire
                resultat_mfl1.append({
                    'home': home_team,
                    'away': away_team,
                    'score': f"{score_home} - {score_away}",
                    'status': status,
                    'date': f'{date_f}/{heure_utc}',
                    'competition': competition,
                    'minutes': minutes
                })
            return resultat_mfl1

    except Exception as e:
        return None, str(e)

def matchtermine_pl():
    API_KEY = settings.API_KEY_SPORTS
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/PL/matches?status=FINISHED'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    try:
        if response.status_code == 200:
            resultat_tpl = []
            derniers = sorted(data['matches'], key=lambda x:x['utcDate'], reverse=True)[:10]
            for match in derniers:
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                score_home = match['score']['fullTime']['home']
                score_away = match['score']['fullTime']['away']
                # converti les dates
                utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
                utc_date = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                py_tz = pytz.timezone('America/Port-au-Prince')
                localdate = utc_date.astimezone(py_tz)
                date = localdate.date()
                # convertir par exemple august=aout
                date_f = format_date(date, format='d MMMM y', locale='fr')
                heure = localdate.strftime('%H:%M')
                status = match['status']  # SCHEDULED, FINISHED, etc.
                competition = match['competition']['name']
                # dictionnaire de donnees
                resultat_tpl.append({
                    'home': home_team,
                    'away': away_team,
                    'score': f"{score_home} - {score_away}",
                    'status': status,
                    'date': date_f,
                    'heure': heure,
                    'competition': competition
                })
            return resultat_tpl
        else:
            print('echec')

    except Exception as e:
        print("Erreur :")

def matchtermine_liga():
    API_KEY = settings.API_KEY_SPORTS
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/PD/matches?status=FINISHED'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    resultat_tlig = []
    derniers = sorted(data['matches'], key=lambda x: x['utcDate'], reverse=True)[:10]
    if response.status_code == 200:
        for match in derniers:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']
            utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
            # converti les dates
            utc_date = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
            py_tz = pytz.timezone('America/Port-au-Prince')
            localdate = utc_date.astimezone(py_tz)
            date = localdate.date()
            # convertir par exemple august=aout
            date_f = format_date(date, format='d MMMM y', locale='fr')
            heure = localdate.strftime('%H:%M')

            status = match['status']  # SCHEDULED, FINISHED, etc.
            competition = match['competition']['name']

            resultat_tlig.append({
                'home': home_team,
                'away': away_team,
                'score': f"{score_home} - {score_away}",
                'status': status,
                'date': date_f,
                'heure': heure,
                'competition': competition
            })
        return resultat_tlig
    else:
        print("Erreur :")

def matchtermine_seriea():
    API_KEY = settings.API_KEY_SPORTS  # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/SA/matches?status=FINISHED'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers)
    resultat_tsa = []

    if response.status_code == 200:
        data = response.json()
        derniers = sorted(data['matches'], key=lambda x: x['utcDate'], reverse=True)[:10]
        for match in derniers:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']
            utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z

            utc_date = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
            py_tz = pytz.timezone('America/Port-au-Prince')
            localdate = utc_date.astimezone(py_tz)
            date = localdate.date()
            # convertir par exemple august=aout
            date_f = format_date(date, format='d MMMM y', locale='fr')

            heure = localdate.strftime('%H:%M')
            status = match['status']  # SCHEDULED, FINISHED, etc.
            competition = match['competition']['name']

            resultat_tsa.append({
                'home': home_team,
                'away': away_team,
                'score': f"{score_home} - {score_away}",
                'status': status,
                'date': date_f,
                'heure': heure,
                'competition': competition
            })
        return resultat_tsa
    else:
        print("Erreur :")

def matchtermine_ligue1():
    API_KEY = settings.API_KEY_SPORTS
    # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/FL1/matches?status=FINISHED'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers)
    resultat_tlig1 = []

    if response.status_code == 200:
        data = response.json()
        derniers = sorted(data['matches'], key=lambda x: x['utcDate'], reverse=True)[:10]
        for match in derniers:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']

            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']

            utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
            utc_date = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
            py_tz = pytz.timezone('America/Port-au-Prince')
            localdate = utc_date.astimezone(py_tz)
            date = localdate.date()
            # convertir par exemple august=aout
            date_f = format_date(date, format='d MMMM y', locale='fr')
            heure = localdate.strftime('%H:%M')
            status = match['status']  # SCHEDULED, FINISHED, etc.
            competition = match['competition']['name']

            resultat_tlig1.append({
                'home': home_team,
                'away': away_team,
                'score': f"{score_home} - {score_away}",
                'status': status,
                'date': date_f,
                'heure': heure,
                'competition': competition
            })
        return resultat_tlig1
    else:
        print("Erreur :")

def recupererscorejoueur(championnat):
    API_KEY = settings.API_KEY_SPORTS
    headers = {'X-Auth-Token': API_KEY}
    url = f'https://api.football-data.org/v4/competitions/{championnat}/scorers'
    response = requests.get(url, headers=headers)
    resultat = []
    try:
        if response.status_code == 200:
            data = response.json()
            for scorer in data['scorers']:
                player_name = scorer['player']['name']
                team_name = scorer['team']['name']
                goals = scorer['goals']
                # dictionnaire de donnees du resultat
                resultat.append({
                    'player_name': player_name,
                    'team_name': team_name,
                    'goals': goals
                })
            return resultat
        else:
            print('Erreur de reponse')
    except Exception as e:
        print(f"Erreur API{e}")

def scorer_europeen():
    topscorerpl = recupererscorejoueur('PL')
    topscorerpd = recupererscorejoueur('PD')
    topscorersa = recupererscorejoueur('SA')
    topscorerfl1 = recupererscorejoueur('FL1')
    topscorerbl1 = recupererscorejoueur('BL1')

    topsc = []
    result1 = next(((maxscorepl['player_name'], maxscorepl['goals']) for maxscorepl in topscorerpl if maxscorepl['goals'] > 0), None)
    result2 = next(((maxscorepd['player_name'], maxscorepd['goals']) for maxscorepd in topscorerpd if maxscorepd['goals'] > 0), None)
    result3 = next(((maxscoresa['player_name'], maxscoresa['goals']) for maxscoresa in topscorersa if maxscoresa['goals'] > 0), None)
    result4 = next(((maxscorefl1['player_name'], maxscorefl1['goals']) for maxscorefl1 in topscorerfl1 if maxscorefl1['goals'] > 0), None)
    result5 = next(((maxscorebl1['player_name'], maxscorebl1['goals']) for maxscorebl1 in topscorerbl1 if maxscorebl1['goals'] > 0), None)

    topsc.append({'Angleterre': result1, 'Espagne': result2, 'Italie': result3, 'France': result4, 'Allemagne': result5})
    # print(f"'Angletere':result1 , 'Espagne':{result2}, 'Italie':{result3}, 'France': {result4}, 'Allemagne': {result5}")

    # parcourir la liste de dictionnaire
    max_buts = 0
    meilleur_joueur = []

    for d in topsc:
        for pays, (joueur, buts) in d.items():

            if buts > max_buts:
                max_buts = buts
                # meilleur_joueur = joueur
                pays_meilleur = pays
                print(pays_meilleur, joueur, max_buts)
                meilleur_joueur = [{"pays":pays,
                                    "joueur":joueur,
                                    "buts":buts
                                    }]
            elif buts == max_buts:
                meilleur_joueur.append({"pays":pays,"joueur":joueur, "buts":buts})
        return meilleur_joueur

def matchtermine_bundesliga():
    API_KEY = settings.API_KEY_SPORTS  # Remplace par ta vraie clé API
    url = 'https://api.football-data.org/v4/competitions/BL1/matches?status=FINISHED'
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(url, headers=headers)
    resultat_tligb = []
    if response.status_code == 200:
        data = response.json()
        derniers = sorted(data['matches'], key=lambda x: x['utcDate'], reverse=True)[:10]
        for match in derniers:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']
            utc_date = match['utcDate']  # format : 2025-08-07T18:00:00Z
            utc_date = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
            py_tz = pytz.timezone('America/Port-au-Prince')
            localdate = utc_date.astimezone(py_tz)
            date = localdate.date()
            # convertir par exemple august=aout
            date_f = format_date(date, format='d MMMM y', locale='fr')
            heure = localdate.strftime('%H:%M')
            status = match['status']  # SCHEDULED, FINISHED, etc.
            competition = match['competition']['name']
            # ajouter le resultat
            resultat_tligb.append({
                'home': home_team,
                'away': away_teamm,
                'score': f"{score_home} - {score_away}",
                'status': status,
                'date': date_f,
                "heure": heure,
                'competition': competition
            })
        return resultat_tligb
    else:
        print("Erreur :")

def classementchampionnat_france():
    competition_id = 'FL1'  # Ex: Ligue 1
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/standings'
    headers = {
        'X-Auth-Token':settings.API_KEY_SPORTS
    }
    response = requests.get(url, headers=headers)  # reponse de l'api apres la requete https
    classementfrance = []
    nomequipes = []
    nbpoints = []
    image_base64 = None
    colors = []
    # si l'api renvoi des valeurs
    if response.status_code == 200:
        data = response.json()
        table = data['standings'][0]['table']
        for i, team in enumerate(table):
            classementfrance.append({'position':team['position'],'equipe': team['team']['name'], 'journee':team['playedGames'],'points': team['points'],
                                     'gagne':team['won'],'nul':team['draw'],'perdu':team['lost'],'buts_marques':team['goalsFor'],'buts_encaisses':team['goalsAgainst'],'difference':team['goalDifference']})
            nomequipes.append(team['team']['name'])
            nbpoints.append(team['points'])
            # Colorier en rouge les 3 derniers (relégués), sinon bleu
            if i < 2:
                colors.append('mediumseagreen')  # Europe
            elif i >= len(table) - 3:
                colors.append('crimson')  # relegation
            else:
                colors.append('skyblue')  # milieu tableau
        # Générer le graphique
        fig, ax = plt.subplots(figsize=(13, 6))
        ax.barh(nomequipes[::-1], nbpoints[::-1], color=colors[::-1], height=0.6)  # Inversé pour que le 1er soit en haut
        ax.set_title("Classement du Championnat")
        ax.set_ylabel("Points")
        plt.tight_layout()
        # sauvegarde en memoire
        buf = io.BytesIO()
        # enregistrer sous le format png
        plt.savefig(buf, format='png', bbox_inches="tight")
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return classementfrance, image_base64
    else:
        print(f"Erreur : {response.status_code}")

def calendrier_ligue1():
    API_KEY = settings.API_KEY_SPORTS
    competition_id = 'FL1'  # Ligue 1
    time_zone = pytz.timezone('America/Port-au-Prince')
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/matches'
    headers = {'X-Auth-Token': API_KEY}
    match_ligue1_auj = []
    match_ligue1_dem = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        matchs = data.get('matches', [])
        today = datetime.now(time_zone).date()
        tomorrow = today + timedelta(days=1)
        for match in matchs:
            utc_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            # Passer en timezone locale
            local_time = utc_time.astimezone(time_zone)
            match_date = local_time.date()
            if match_date == today:
                match_ligue1_auj.append({
                    'domicile': match['homeTeam']['name'],
                    'exterieur': match['awayTeam']['name'],
                    'date': local_time.strftime('%d/%m/%Y %H:%M')
                })
            elif match_date == tomorrow:
                match_ligue1_dem.append({
                    'domicile_dem': match['homeTeam']['name'],
                    'exterieur_dem': match['awayTeam']['name'],
                    'date_dem': local_time.strftime('%d/%m/%Y %H:%M')
                })

        return match_ligue1_auj, match_ligue1_dem
    else:
        print(f"Erreur API : {response.status_code}")
        return [], []

def classementchampionnat_espagne():
    competition_id = 'PD'  # Ex: Ligue 1
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/standings'
    headers = {
        'X-Auth-Token': settings.API_KEY_SPORTS
    }
    response = requests.get(url, headers=headers)  # on effectue une requete vers l'api
    classementespagne = []
    nomsequipes = []
    points = []
    colors = []
    image_base64 = None
    # si l'api renvoi des valeurs
    if response.status_code == 200:
        data = response.json()  # on transforme la reponse en format json
        table = data['standings'][0]['table']
        # parcourir l'ensemble de valeurs de la table
        for i, team in enumerate(table):
            classementespagne.append({'position':team['position'],'equipe': team['team']['name'],'journee':team['playedGames'], 'points': team['points'],
                                     'gagne':team['won'],'nul':team['draw'],'perdu':team['lost'],'buts_marques':team['goalsFor'],'buts_encaisses':team['goalsAgainst'],'difference':team['goalDifference']})
            nomsequipes.append(team['team']['name'])
            points.append(team['points'])
            if i < 3:
                colors.append('mediumseagreen')
            elif i >=len(table) -3:
                colors.append('crimson')
            else:
                colors.append('skyblue')
        # maintenant on cree le graphe (barh)
        fig, ax = plt.subplots(figsize=(13, 6))
        ax.set_title('Classement du championnat Espagne')
        ax.set_ylabel('Points')
        ax.barh(nomsequipes[::-1], points[::-1], color=colors[::-1], height=0.6)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return classementespagne, image_base64
    else:
        print(f"Erreur : {response.status_code}")

def calendrier_espagne():
    API_KEY = settings.API_KEY_SPORTS
    competition_id = 'PD'  # Ligue 1
    time_zone = pytz.timezone('America/Port-au-Prince')
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/matches'
    headers = {'X-Auth-Token': API_KEY}
    match_esp_auj = []
    match_esp_dem = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        matchs = data.get('matches', [])
        today = datetime.now(time_zone).date()
        tomorrow = today + timedelta(days=1)
        for match in matchs:
            utc_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            # Passer en timezone locale
            local_time = utc_time.astimezone(time_zone)
            match_date = local_time.date()
            if match_date == today:
                match_esp_auj.append({
                    'domicile': match['homeTeam']['name'],
                    'exterieur': match['awayTeam']['name'],
                    'date': local_time.strftime('%d/%m/%Y %H:%M')
                })
            elif match_date == tomorrow:
                match_esp_dem.append({
                    'domicile_dem': match['homeTeam']['name'],
                    'exterieur_dem': match['awayTeam']['name'],
                    'date_dem': local_time.strftime('%d/%m/%Y %H:%M')
                })

        return match_esp_auj, match_esp_dem
    else:
        print(f"Erreur API : {response.status_code}")
        return [], []

def classementchampionnat_angleterre():
    competition_id = 'PL'  # Ex: Ligue 1
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/standings'
    headers = {
        'X-Auth-Token': settings.API_KEY_SPORTS
    }
    response = requests.get(url, headers=headers)  # Reponse de l'api apres la requete https
    classementangleterre = []
    nomsequipes = []
    points = []
    colors = []
    # si l'api renvoi des valeurs
    if response.status_code == 200:
        data = response.json()
        table = data['standings'][0]['table']
        for i, team in enumerate(table):
            classementangleterre.append({'position':team['position'],'equipe': team['team']['name'],'journee':team['playedGames'], 'points': team['points'],
                                     'gagne':team['won'],'nul':team['draw'],'perdu':team['lost'],'buts_marques':team['goalsFor'],'buts_encaisses':team['goalsAgainst'],'difference':team['goalDifference']})
            nomsequipes.append(team['team']['name'])
            points.append(team['points'])
            if i < 3:
                colors.append('mediumseagreen')
            elif i >=len(table) -3:
                colors.append('crimson')
            else:
                colors.append('skyblue')
        # maintenant on cree le graphe (barh)
        fig, ax = plt.subplots(figsize=(13, 6))
        ax.set_title('Classement du championnat Espagne')
        ax.set_ylabel('Points')
        ax.barh(nomsequipes[::-1], points[::-1], color=colors[::-1], height=0.6)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return classementangleterre, image_base64
    else:
        print(f"Erreur : {response.status_code}")

def calendrier_angleterre():
    API_KEY = settings.API_KEY_SPORTS
    competition_id = 'PL'  # Ligue 1
    time_zone = pytz.timezone('America/Port-au-Prince')
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/matches'
    headers = {'X-Auth-Token': API_KEY}
    match_ang_auj = []
    match_ang_dem = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        matchs = data.get('matches', [])
        today = datetime.now(time_zone).date()
        tomorrow = today + timedelta(days=1)
        for match in matchs:
            utc_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            # Passer en timezone locale
            local_time = utc_time.astimezone(time_zone)
            match_date = local_time.date()
            if match_date == today:
                match_ang_auj.append({
                    'domicile': match['homeTeam']['name'],
                    'exterieur': match['awayTeam']['name'],
                    'date': local_time.strftime('%d/%m/%Y %H:%M')
                })
            elif match_date == tomorrow:
                match_ang_dem.append({
                    'domicile_dem': match['homeTeam']['name'],
                    'exterieur_dem': match['awayTeam']['name'],
                    'date_dem': local_time.strftime('%d/%m/%Y %H:%M')
                })

        return match_ang_auj, match_ang_dem
    else:
        print(f"Erreur API : {response.status_code}")
        return [], []

def classementchampionnat_italie():
    competition_id = 'SA'  # Ex: Ligue 1
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/standings'
    headers = {
        'X-Auth-Token': settings.API_KEY_SPORTS
    }
    response = requests.get(url, headers=headers)  # Reponse de l'api apres la requete https
    classementitalie = []
    nomsequipes = []
    points = []
    colors = []
    # si l'api renvoi des valeurs
    if response.status_code == 200:
        data = response.json()
        table = data['standings'][0]['table']
        for i, team in enumerate(table) :
            classementitalie.append({'position':team['position'],'equipe': team['team']['name'],'journee':team['playedGames'], 'points': team['points'],
                                     'gagne':team['won'],'nul':team['draw'],'perdu':team['lost'],'buts_marques':team['goalsFor'],'buts_encaisses':team['goalsAgainst'],'difference':team['goalDifference']})
            nomsequipes.append(team['team']['name'])
            points.append(team['points'])
            if i < 3:
                colors.append('mediumseagreen')
            elif i >=len(table) -3:
                colors.append('crimson')
            else:
                colors.append('skyblue')
        # maintenant on cree le graphe (barh)
        fig, ax = plt.subplots(figsize=(13, 6))
        ax.set_title('Classement du championnat Italie')
        ax.set_ylabel('Points')
        ax.barh(nomsequipes[::-1], points[::-1], color=colors[::-1], height=0.6)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return classementitalie, image_base64
    else:
        print(f"Erreur : {response.status_code}")

def calendrier_italie():
    API_KEY = settings.API_KEY_SPORTS
    competition_id = 'SA'  # Ligue 1
    time_zone = pytz.timezone('America/Port-au-Prince')
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/matches'
    headers = {'X-Auth-Token': API_KEY}
    match_ita_auj = []
    match_ita_dem = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        matchs = data.get('matches', [])
        today = datetime.now(time_zone).date()
        tomorrow = today + timedelta(days=1)
        for match in matchs:
            utc_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            # Passer en timezone locale
            local_time = utc_time.astimezone(time_zone)
            match_date = local_time.date()
            if match_date == today:
                match_ita_auj.append({
                    'domicile': match['homeTeam']['name'],
                    'exterieur': match['awayTeam']['name'],
                    'date': local_time.strftime('%d/%m/%Y %H:%M')
                })
            elif match_date == tomorrow:
                match_ita_dem.append({
                    'domicile_dem': match['homeTeam']['name'],
                    'exterieur_dem': match['awayTeam']['name'],
                    'date_dem': local_time.strftime('%d/%m/%Y %H:%M')
                })

        return match_ita_auj, match_ita_dem
    else:
        print(f"Erreur API : {response.status_code}")
        return [], []

def classementchampionnat_allemagne():
    competition_id = 'BL1'  # Ex: Ligue 1
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/standings'
    headers = {
        'X-Auth-Token': settings.API_KEY_SPORTS
    }
    response = requests.get(url, headers=headers)  # Reponse de l'api apres la requete https
    classementallemagne = []
    colors = []
    nomsequipes = []
    points = []
    # si l'api renvoi des valeurs
    if response.status_code == 200:
        data = response.json()
        table = data['standings'][0]['table']
        for i, team in enumerate(table):
            classementallemagne.append({'position':team['position'],'equipe': team['team']['name'],'journee':team['playedGames'], 'points': team['points'],
                                     'gagne':team['won'],'nul':team['draw'],'perdu':team['lost'],'buts_marques':team['goalsFor'],'buts_encaisses':team['goalsAgainst'],'difference':team['goalDifference']})
            nomsequipes.append(team['team']['name'])
            points.append(team['points'])
            if i < 3:
                colors.append('mediumseagreen')
            elif i >=len(table) -3:
                colors.append('crimson')
            else:
                colors.append('skyblue')
        # maintenant on cree le graphe (barh)
        fig, ax = plt.subplots(figsize=(13, 6))
        ax.set_title('Classement du championnat Allemagne')
        ax.set_ylabel('Points')
        ax.barh(nomsequipes[::-1], points[::-1], color=colors[::-1], height=0.6)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return classementallemagne, image_base64
    else:
        print(f"Erreur : {response.status_code}")

def calendrier_allemagne():
    API_KEY = settings.API_KEY_SPORTS
    competition_id = 'BL1'  # Ligue 1
    time_zone = pytz.timezone('America/Port-au-Prince')
    url = f'https://api.football-data.org/v4/competitions/{competition_id}/matches'
    headers = {'X-Auth-Token': API_KEY}
    match_all_auj = []
    match_all_dem = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        matchs = data.get('matches', [])
        today = datetime.now(time_zone).date()
        tomorrow = today + timedelta(days=1)
        for match in matchs:
            utc_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            # Passer en timezone locale
            local_time = utc_time.astimezone(time_zone)
            match_date = local_time.date()
            if match_date == today:
                match_all_auj.append({
                    'domicile': match['homeTeam']['name'],
                    'exterieur': match['awayTeam']['name'],
                    'date': local_time.strftime('%d/%m/%Y %H:%M')
                })
            elif match_date == tomorrow:
                match_all_dem.append({
                    'domicile_dem': match['homeTeam']['name'],
                    'exterieur_dem': match['awayTeam']['name'],
                    'date_dem': local_time.strftime('%d/%m/%Y %H:%M')
                })

        return match_all_auj, match_all_dem
    else:
        print(f"Erreur API : {response.status_code}")
        return [], []

def aff_stationradio():
    stationquery = Station.objects.all()[:30] # lister 30 stations
    stations = []
    for station in stationquery:
        stations.append({'nom': station.nomstation,'url': station.url, 'images': station.image})
    return stations

def stationradio(request):
    stat = aff_stationradio()
    nomstations = []
    sections = ['statdefaut']  # par défaut, on affiche les radios locales
    if request.method == 'GET':
        namestation = request.GET.get('stationradio', '').strip()
        if namestation:  # Si une recherche est faite
            try:
                # response = requests.get(f"https://de1.api.radio-browser.info/json/stations/search?name={namestation}")
                radio = RadioBrowser()
                response = radio.search(name=namestation, name_exact=True)
                if response:
                    for row in response:
                        nomstations.append({'name': row['name'], 'url': row['url_resolved'],
                                            'icon': row['favicon'] or 'static/images/design1.jpg'})
                    # Parcourir la réponse
                    # Conditions
                    if nomstations:
                        sections = ['recherchestat']  # si résultats trouvés (Retourne une seule (1) section)
                    else:
                        sections = ['recherchestat',
                                    'statdefaut']  # aucun résultat, on montre quand même les locales (Retourne (2) sections)
            # En cas d'erreur
            except Exception as e:
                print(f'Erreur lors de connexion API : {e}')
                sections = ['statdefaut']  # fallback si erreur API

    return render(request, 'stationradio.html', {'sections':sections, 'stat':stat, 'nomstations':nomstations})

def infos_sports():
    sportactu = Article.objects.filter(category='sports')[:15]  # a modifier
    return sportactu

def infos_sante(request):
    infosante = Article.objects.filter(category='sante')[:15]
    return render(request, 'sante.html', {'santes': infosante})

def infos_sciences(request):
    infosscience = Article.objects.filter(category='sciences')[:15]
    return render(request, 'sciences.html', {'sciences_': infosscience})


def fluxrss_lemonde(request):
    api_key = os.getenv('api_key_nouvelles')
    pays_actualites = ['Haiti','Usa','France','Canada']
    keyword = random.choice(pays_actualites)
    stations = aff_stationradio()
    articles = []
    connection = True
    url_rss = 'https://www.lemonde.fr/rss/une.xml'
    feed = feedparser.parse(url_rss)
    entries = feed.entries
    # Retrouver des infos sur le site www.lemonde.fr par a son flux RSS
    try:
        for article in entries[:15]:
            image_url = None
            # Cherche une image dans 'media_content'
            if 'media_content' in article:
                for media in article['media_content']:
                    if 'url' in media:
                        image_url = media['url']
                        break  # Prend la première image
            # Ou dans les 'links' avec type image
            elif 'links' in article:
                for link in article['links']:
                    if link.get('type', '').startswith('image'):
                        image_url = link.get('href')
                        break
            dte = article.get('published') # le format fri, 10 oct 2025 11:10:25 +0200
            dt = datetime.strptime(dte, "%a, %d %b %Y %H:%M:%S %z")
            dtt = dt.replace(tzinfo=None)
            dateformatf = format_datetime(dtt , format="EEEE d MMMM y 'à' HH:mm a", locale='fr_FR')
            articles.append({'title': article.get('title'), 'link': article.get('link'), 'summary':article.get('summary'),'published': dateformatf, 'image': image_url})
    except Exception as e:
        print(f'Erreur API:{e}')
    # Création du dictionnaire de l'article

    return render(request,'index.html', context={
                  'stations':stations, 'articles':articles, 'pays':keyword, 'connection':connection
    })

def index(request):
    articles = Article.objects.filter(category='actualites')[:15] # a modifier
    stations = aff_stationradio()
    connection = True
    nb_radios = Station.objects.count()
    nb_tv = ChaineTV.objects.count()
    nb_users_profil = Profil.objects.count()
    nb_musiques = Musiques.objects.count()
    nb_art_actualites = Article.objects.filter(status='publie', category='actualites').count()
    nb_art_sports = Article.objects.filter(status='publie', category='sports').count()
    nb_art_sante = Article.objects.filter(status='publie', category='sante').count()
    nb_art_sciences = Article.objects.filter(status='publie', category='sciences').count()
    nb_art_musiques = Article.objects.filter(status='publie', category='musiques').count()
    nb_art_politiques = Article.objects.filter(status='publie', category='politiques').count()

    return render(request, 'index.html', context={'stations':stations, 'articles':articles,
                                                  'connection':connection, 'nb_radios':nb_radios, 'nb_tv':nb_tv,
                                                  'nb_users_profil':nb_users_profil,'nb_musiques':nb_musiques,
                                                  'nb_art_actualites':nb_art_actualites, 'nb_art_sports':nb_art_sports,
                                                  'nb_art_sante':nb_art_sante,'nb_art_sciences':nb_art_sciences,
                                                  'nb_art_musiques':nb_art_musiques, 'nb_art_politiques':nb_art_politiques

    })

def article_detail(request,year, month, day, slug):
    article = get_object_or_404(Article, published_at__year=year, published_at__month=month, published_at__day=day, slug=slug, status='publie')
    similar_articles = Article.objects.filter(category=article.category, status='publie').exclude(slug=slug)[:3]  # affiche 5 articles similaires
    # if similar_articles.count() < 5:
    #     needed = 3 - similar_articles.count()
    #     additionnel_articles = Article.objects.filter(status='publie')
    #     similar_articles = list(similar_articles)+list(additionnel_articles)
    return render(request, 'article_detail.html', context={'article':article, 'similar_articles':similar_articles})

def sport_detail(request,year, month, day, slug):
    sport = get_object_or_404(Article, published_at__year=year, published_at__month=month, published_at__day=day, slug=slug, status='publie')
    similar_articles = Article.objects.filter(category=sport.category, status='publie').exclude(slug=slug)[:3]  # affiche 5 articles similaires
    return render(request, 'article_detail.html', context={'article':sport, 'similar_articles':similar_articles})

def sante_detail(request,year, month, day, slug):
    sante= get_object_or_404(Article, published_at__year=year, published_at__month=month, published_at__day=day, slug=slug, status='publie')
    similar_articles = Article.objects.filter(category=sante.category, status='publie').exclude(slug=slug)[:3]  # affiche 5 articles similaires
    return render(request, 'article_detail.html', context={'article':sante, 'similar_articles':similar_articles})

def science_detail(request,year, month, day, slug):
    science = get_object_or_404(Article, published_at__year=year, published_at__month=month, published_at__day=day, slug=slug, status='publie')
    similar_articles = Article.objects.filter(category=science.category, status='publie').exclude(slug=slug)[:3]  # affiche 5 articles similaires
    return render(request, 'article_detail.html', context={'article':science, 'similar_articles':similar_articles})



def infossportsactualites(request):
    sportsactu = []
    section = request.GET.get("section")
    championnat = request.GET.get('championnat', None)
    # Créer une variable vide
    data = ''
    resultat, image_base64, classementfrance, classementespagne, classementangleterre, classementitalie, classementallemagne = [], [], [], [], [], [], []
    match_ligue1_auj, match_ligue1_dem, match_esp_auj, match_esp_dem, match_ang_auj = [], [], [], [], []
    match_ang_dem, match_ita_auj, match_ita_dem, match_all_auj, match_all_dem = [], [], [], [], []
    resultat_mpl, resultat_mpd, resultat_msa, resultat_mbl1, resultat_mfl1 = [], [], [], [], []
    sportsactu = infos_sports()
    # # conditions
    if section == "classement" and championnat == "france":
        data = f'Classement du championnat {championnat}'
        classementfrance, image_base64 = classementchampionnat_france()
        match_ligue1_auj, match_ligue1_dem = calendrier_ligue1()
    elif section == 'classement' and championnat == 'espagne':
        data = f'Classement du championnat {championnat}'
        classementespagne, image_base64 = classementchampionnat_espagne()
        match_esp_auj, match_esp_dem = calendrier_espagne()
    elif section == 'classement' and championnat == 'angleterre':
        data = f'Classement du championnat {championnat}'
        classementangleterre, image_base64 = classementchampionnat_angleterre()
        match_ang_auj, match_ang_dem = calendrier_angleterre()
    elif section == 'classement' and championnat == 'italie':
        data = f'Classement du championnat {championnat}'
        classementitalie, image_base64 = classementchampionnat_italie()
        match_ita_auj, match_ita_dem = calendrier_italie()
    elif section == 'classement' and championnat == 'allemagne':
        data = f'Classement du championnat {championnat}'
        classementallemagne, image_base64 = classementchampionnat_allemagne()
        match_all_auj, match_all_dem = calendrier_allemagne()
    elif section == "calendrier-matchs":
        data = "⚽ Calendrier des matchs"
        resultat = calendriermatch()
    elif section == "infos-equipes":
        data = "Infos sur les équipes ici..."

    return render(request, 'sports.html', {'sportsactu':sportsactu, 'championnat':championnat, 'data':data,
                                           'classementfrance':classementfrance,'image':image_base64,
                                           'match_ligue1_auj':match_ligue1_auj, 'match_ligue1_dem':match_ligue1_dem, 'classementespagne':classementespagne,
                                           'match_esp_auj':match_esp_auj, 'match_esp_dem':match_esp_dem, 'classementangleterre':classementangleterre,
                                           'match_ang_auj':match_ang_auj, 'match_ang_dem':match_ang_dem, 'classementitalie':classementitalie,
                                           'match_ita_auj':match_ita_auj, 'match_ita_dem':match_ita_dem, 'classementallemagne':classementallemagne,
                                           'match_all_auj':match_all_auj, 'match_all_dem':match_all_dem, 'resultat':resultat, 'section':section,
                                            'resultat_mpl':resultat_mpl})

def matchsencours(request):
    resultat_mpl, resultat_sa, resultat_fl1, resultat_mpd, resultat_bl1 = None, None, None, None, None
    try:
        resultat_mpl = matchsencours_premierleague()
        resultat_sa = matchsencours_seriea()
        resultat_fl1 = matchsencours_ligue1()
        resultat_bl1 = matchsencours_bundesliga()
        resultat_mpd = matchsencours_liga()
    except Exception as e:
        print('erreur')
    return render(request, 'score.html', context= {'section':'championnat', 'resultat_mpl':resultat_mpl, 'resultat_sa':resultat_sa,
                           'resultat_bl1':resultat_bl1, 'resultat_fl1':resultat_fl1, 'resultat_mpd':resultat_mpd})

def recupererscorejoueur(championnat):
    API_KEY = settings.API_KEY_SPORTS
    headers = {'X-Auth-Token': API_KEY}
    url = f'https://api.football-data.org/v4/competitions/{championnat}/scorers'
    response = requests.get(url, headers=headers)
    resultat = []
    try:
        if response.status_code == 200:
            data = response.json()
            for scorer in data['scorers']:
                player_name = scorer['player']['name']
                team_name = scorer['team']['name']
                goals = scorer['goals']
                # dictionnaire de donnees du resultat
                resultat.append({
                    'player_name': player_name,
                    'team_name': team_name,
                    'goals': goals
                })
            return resultat
        else:
            print('Erreur de reponse')
    except Exception as e:
        print(f"Erreur API{e}")

def recuperertousbuteurs(request):
    buteurs_pl, buteurs_sa, buteurs_fl1, buteurs_pd, buteurs_bl1 = None,None,None,None,None
    scorer_europe = []
    pays_drapeaux = {
        'Angleterre': 'GB',
        'Allemagne':'DE',
        'France':'FR',
        'Espagne':'ES',
        'Italie':'IT'
    }
    try:
        buteurs_pl = recupererscorejoueur('PL')
        buteurs_sa = recupererscorejoueur('SA')
        buteurs_pd = recupererscorejoueur('PD')
        buteurs_fl1 = recupererscorejoueur('FL1')
        buteurs_bl1 = recupererscorejoueur('BL1')
        scorer_europe = scorer_europeen()
    except Exception as e:
        print(f'erreur {str(e)}')
    return render(request, 'classementbuteur.html', context={'buteurs_pl':buteurs_pl,
                                     'buteurs_pd':buteurs_pd, 'buteurs_sa':buteurs_sa,'buteurs_bl1':buteurs_bl1,
                                     'buteurs_fl1':buteurs_fl1, 'scorer_europe':scorer_europe,'pays_drapeaux':pays_drapeaux})

def matchtermineend(request):
    resultat_tpl, resultat_tsa, resultat_tlig, resultat_tlig1, resultat_tligb = None, None, None, None, None
    try:
        resultat_tpl = matchtermine_pl()
        resultat_tlig = matchtermine_liga()
        resultat_tsa = matchtermine_seriea()
        resultat_tlig1 = matchtermine_ligue1()
        resultat_tligb = matchtermine_bundesliga()
    except Exception as e:
        print(f'Pas de donnees..{str(e)}')
    return render(request,"match.html", context={'resultat_tpl':resultat_tpl,
                           'resultat_tlig':resultat_tlig, 'resultat_tsa':resultat_tsa,
                           'resultat_tlig1':resultat_tlig1, 'resultat_tligb':resultat_tligb})

def affichermeteo(request):
    meteos = []
    previsionsjours = []
    previsionshoraires = []
    # verifier quel type de method utilise pour renvoyer le formulaire
    if request.method == 'GET':
        ville = request.GET.get('ville')  # Récupérer les valeurs du champ texte (Ville)
        # conditions par defaut (si l'utilisateur n'a pas saisi une ville)
        if not ville:
            ville = "Port-au-Prince"
        try:
            API_KEYMETEO = settings.API_KEYMETEO
            # Faire une requête à l'API OpenWeatherMap
            url = f"https://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEYMETEO}&lang=fr&units=metric"  # Call de l'api
            r = requests.get(url)
            # Vérifier si la requête a réussi
            if r.status_code == 200:
                data = r.json()  # Récupérer les données en format JSON

                # Utilisation des données du fichier JSON
                lon_lat = data['coord']  # Afficher les coordonnées(latitude, longitude)
                # conditions meteo (pluie, soleil, nuage)
                weather = data['weather'][0]
                sys = data['sys']
                description = weather['description']
                icon_url = f"https://openweathermap.org/img/wn/{weather['icon']}@2x.png"

                # Traduction du français vers l'anglais
                # translator = GoogleTranslator(source='en', target='fr')
                # traduct_fr = translator.translate(description)
                # meteos = []
                # Créer un dictionnaire pour stocker les informations meteos
                meteos.append({"Longitude": lon_lat['lon'],
                               "Latitude": lon_lat['lat'],
                               "Temperature": f"{data['main']['temp']}",
                               "Temperatureressenti": round(data['main']['feels_like'], 1),
                               "Pression": f"{data['main']['pressure']}",
                                "Direction": f"{int(data['wind']['deg'] / 10)} degrés",
                               "Vitessekm": f"{round(data['wind']['speed'] * 3.6)}",
                               "Vitesse_m": f"{data['wind']['speed']} m/s",
                               "Humidite": data['main']['humidity'],
                               "description": f"{description}",
                               "Pays": f"{sys['country']}",
                               'ville': ville,
                               "icon": icon_url})
                # previsions pour les 5 prochains jours
                previsionsjours = previsions_5_journees(lon_lat['lat'], lon_lat['lon'])
                previsionshoraires = previsions_prochains_heure(ville)
                # return messages # retourner la valeur de la fonction
            else:
                # Gérer les erreurs
                if r.status_code == 404:
                    meteos.append({"reponse","Ville introuvable: f{ville}\n. Veuillez vérifier le nom et réessayer."})
                else:
                    meteos.append({"reponse", "Erreur:\nlors de la récupération des données météo. Veuillez réessayer plus tard."})
        except Exception as e:
            print("reponse",f"Erreur:lors de la récupération des données météo.{e}")

    return render(request, 'meteo.html', context={'meteos':meteos, 'previsionsjours':previsionsjours, 'previsionshoraires':previsionshoraires})

def affichermusiques(request):
    resultcompas = Musiques.objects.filter(genre="kompa")[:6]
    resultafro = Musiques.objects.filter(genre="rnb")[:6]
    resultevangelique = Musiques.objects.filter(genre="gospel")[:6]
    return render(request, 'musiques.html', context={'resultcompas':resultcompas, 'resultafro':resultafro,
                                                     'resultevangelique':resultevangelique
                                                     })

def lecturemusiques(request, slug):
    # on recupere la musique ou renvoi une erreur 404 si le slug n'existait pas
    musique = get_object_or_404(Musiques, slug=slug)
    Musiques.objects.filter(slug=slug).update(nb_ecoutes=F('nb_ecoutes') + 1)  # calcul de nombre ecoute
    # Refresh la base
    musique.refresh_from_db()
    # None s'il ny a pas de lyrics
    lyrics = getattr(musique, 'lyrics', 'None')
    # Recuperer d'autres musiques du meme genre
    suggestions = Musiques.objects.filter(genre=musique.genre).exclude(slug=slug)[:4] # afficher 4 musiques
    suggestions_list = list(suggestions)
    if len(suggestions_list) < 6 :
        needed = 6 - len(suggestions_list)
        excluded_ids = [m.id for m in suggestions_list] + [musique.id]
        additionnal_tracks = Musiques.objects.exclude(id__in=excluded_ids)[:needed]
        suggestions_list +=  list(additionnal_tracks)
    return render(request, 'lecteur.html', context={'musique':musique, 'suggestions':suggestions,'Lyrics':lyrics})

def seconnecter(request):
    if request.method=="POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        # if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'ActuWebApp:aff_mus')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
    return render(request, 'login.html')

def sedeconnecter(request):
    logout(request)
    return render(request, 'login.html')

@transaction.atomic
def inscription(request):
    if request.method =='POST':
        username = request.POST.get('username')
        email =  request.POST.get('email')
        password = request.POST.get('password')
        datenaissance = request.POST.get('datenaissance')
        user = User.objects.create_user(username=username, email=email, password=password)
        Profil.objects.update_or_create(user=user, photo=request.POST.get('photo'), ville=request.POST.get('ville', ''),
                              bio=request.POST.get('bio', 'Ok'), datenaissance=datenaissance if datenaissance else None)
        messages.success(request,'Votre compte a été crée avec succès, connectez-vous!')
        return redirect('/login')
    return render(request, 'createaccount.html', {'avatars':avatar_definis})

def ajoutercommentaires(request, slug):
    if request.method=='POST':
        musique = get_object_or_404(Musiques, slug=slug)
        lescommentaires = musique.commentaires.all()
        commentaire_texte = request.POST.get('comment', '').strip()
        if not commentaire_texte:
            return HttpResponseBadRequest("Le commentaire ne peut pas être vide.")
        nouveau_commentaire = Commentaire.objects.create(user=request.user,musique=musique,commentaire=commentaire_texte)
        photo = nouveau_commentaire.user.profil.photo
        return render(request, 'partials/commentaire_item.html', {
            'comment': nouveau_commentaire,
            'show_message': True,
            'commentaires':lescommentaires,
            'avatars':avatar_definis
        })


def AfficherTele(request):
    try:
        tele = ChaineTV.objects.all()[:15]
        return render(request, 'livetv.html', context={'channeltv': tele})
    except Exception as e:
        logger.error("Erreur AfficherTele: %s\n%s", e, traceback.format_exc())
        raise  # important : on relance pour garder le 500 et voir le log
      
def regardertv(request, slug):
    chaine = get_object_or_404(ChaineTV, slug=slug)
    recommendations = ChaineTV.objects.exclude(id=chaine.id)[:5] # exclut la chaine qui en train de lire et affiche 5 autres
    return render(request, 'watchtv.html', context={'channel_tv':chaine, 'recommendations': recommendations})
#
@login_required
def	modal_creer_playlist(request):
    return render(request,	'partials/modal_creer_playlist.html')

def creerplaylist(request):
    if request.method=='POST':
        nom = request.POST.get('nom', '').strip()
        if nom:
            Playlist.objects.create(user=request.user, nom=nom)
            playlists = Playlist.objects.filter(user=request.user)
            html_fermeture = '<div id="modal-container" hx-swap-oob="true"></div>'
            html_liste = render_to_string('partials/fragments_playlists.html',{'playlists':playlists}, request=request)
            html_liste_oob = f'<ul id="liste-mes-playlists" class="liste-mes-playlists" hx-swap-oob="true">{html_liste}</ul>'
        return HttpResponse(html_fermeture + html_liste_oob)
    return redirect('ActuWebApp: aff_mus')

# @login_required
# def fragment_Play(request):
#     playlists = Playlist.objects.filter(user=request.user)
#     return render(request,'partials/fragments_mes_playlists.html',{'playlists':playlists})
#
# @login_required
# def menu_playlist(request, musique_id):
#     playlists = Playlist.objects.filter(user=request.user) # on recupere la liste de playlist selon l'utilisateur connecte
#     return render(request, 'partials/menu_playlists.html',{'playlists':playlists,'musique_id':musique_id})
#
# @login_required
# def ajouter_playlist(request, musique_id, playlist_id):
#     musique = get_object_or_404(Musiques, id=musique_id)
#     playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
#     playlist.morceaux.add(musique)
#     return HttpResponse('<span class="toast-success">Ajoute</span>')
#



@login_required
# @require_POST
def creer_playlist(request):
    nom = request.POST.get('nom', '').strip()
    if nom:
        Playlist.objects.get_or_create(nom=nom, user=request.user)
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'partials/fragment_mes_playlists.html', {'playlists': playlists})

@login_required
def fragment_mes_playlists(request):
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'partials/fragment_mes_playlists.html', {'playlists': playlists})

@login_required
def ajout_playlist(request, musique_id):
    musique = get_object_or_404(Musiques, id=musique_id)
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'partials/menu_ajout_playlist.html', {'musique': musique, 'playlists': playlists})

@login_required
# @require_POST
def ajouter_musique_playlist(request, musique_id, playlist_id):
    musique = get_object_or_404(Musiques, id=musique_id)
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    playlist.morceaux.add(musique)
    return render(request, 'partials/confirmation_ajout_playlist.html', {'playlist': playlist})

@login_required
def playlist_musiques(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    return render(request, 'partials/modal_playlist_musiques.html', {'playlist': playlist})

@login_required
# @require_POST
def retirer_musique_playlist(request, playlist_id, musique_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    playlist.morceaux.remove(musique_id)
    return render(request, 'partials/modal_playlist_musiques.html', {'playlist': playlist})

@login_required
def supprimerplaylist(request, playlist_id):
    playlists = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    playlists.delete() # on supprime le playlist selectionne grace a son id
    playlists = Playlist.objects.filter(user=request.user) # on affiche le playlist disponible apres la suppression
    return render(request, 'partials/fragment_mes_playlists.html', {'playlists': playlists})

@login_required
def detail_playlist(request, playlist_id):
    detail_playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    return render(request, 'detailplaylist.html', {'detail_playlist':detail_playlist})

def assistanceai(request):
    genai.configure(api_key=os.getenv('GEMINI_APIKEY'))
    model = genai.GenerativeModel('gemini-3.5-flash-lite') # pour generation de texte
    client = genai_client.Client(api_key=os.getenv('GEMINI_APIKEY')) # pour generation d'image
    reponses = []  # creation d'une liste vide
    # Formulaire (avec requete POST)
    if request.method=='POST':
        prompt = request.POST.get('prompt')  # Récupérer les valeurs du champ texte
        # 1. Détection de la demande d'image par mots-clés
        image_keywords = ["génère une image", "dessine", "fais une image", "image de", "crée une image"]
        is_image_request = any(kw in prompt.lower() for kw in image_keywords)

        if is_image_request:
            try:
                # Génération de l'image via Imagen 3
                result = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=prompt
                )

                # 2. Extraction de l'image depuis les 'parts' de la réponse
                # L'image générée est directement renvoyée dans les candidats sous forme de bytes
                candidate = response.candidates[0]
                image_part = next((part for part in candidate.content.parts if part.inline_data), None)

                if image_part:
                    image_bytes = image_part.inline_data.data
                    b64_str = base64.b64encode(image_bytes).decode('utf-8')

                    # Envoi sous forme de balise HTML
                    html_img = f'<img src="data:image/jpeg;base64,{b64_str}" alt="{prompt}" class="chat-generated-img" />'
                    return StreamingHttpResponse(html_img, content_type='text/html')
                else:
                    return StreamingHttpResponse("Aucune image n'a pu être générée par le modèle.",
                                                 content_type='text/plain')

            except Exception as e:
                return StreamingHttpResponse(f"Erreur image : {str(e)}", content_type='text/plain')

        def generate():
            try:
                response = model.generate_content(prompt, stream=True) # affichage en streaming (affichage ligne par ligne)
                # conditions si le modèle génère des réponses
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"Erreur : {str(e)}"
    # on precise le type de conteu 'text/plain' ou text/event-stream
        return StreamingHttpResponse(generate(), content_type='text/event-stream')
    return render(request, 'assistanceai.html')


def recherchermusiques(request):
    query = request.GET.get('q','').strip()
    if query:
        # if request.method=='GET':
        resultats = Musiques.objects.filter(Q(titre__icontains=query) | Q(artiste__icontains=query))
    else:
        resultats = Musiques.objects.none()

    return render(request, 'partials/resultat-recherche.html', {'resultats':resultats, 'query':query})


def musiques_par_genre(request, genre):
    musiques = Musiques.objects.filter(genre=genre)
    contexte = {'genre': genre, 'musiques': musiques}
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'partials/musique_genre.html', contexte)  # fragment seul
    return render(request, 'partials/musique_genre_page.html', contexte)  # page complète

def tendance(request):
    maintenant = timezone.now()
    musiques = Musiques.objects.annotate(
        age_jours=ExpressionWrapper(
            (maintenant - F('date_ajout')) / timedelta(days=1), output_field=FloatField()
        )
    ).annotate(
        score=ExpressionWrapper(
            F('nb_ecoutes') / F('age_jours') + 2, output_field=FloatField())
    ).order_by('-score')[:20] #+2evite la division par 0, pour les nouveaux morceaux
    return render(request, 'trending-song.html', {'musiques':musiques})

def nouveauxmusiques(request):
    nouveautes = Musiques.objects.order_by('-date_ajout')[:20] # grouper par date(derniere enregistrement)
    return render(request, 'new-song.html', context={'nouveautes':nouveautes})

def actualitesmusiques(request):
    articles = Article.objects.filter(category='musiques')[:15]
    return render(request, 'actualites_musiques.html', {'articles':articles})

def format_vues(vues_str):
    try:
        vues = int(vues_str)
    except (ValueError, TypeError):
        return "0"
    if vues >= 1_000_000:
        formatted = vues / 1_000_000
        return f"{formatted:.1f}".rstrip('0').rstrip('.') + "M"
    elif vues >= 1_000:
        formatted = vues / 1_000_000
        return f"{formatted:.1f}".rstrip('0').rstrip('.') + "k"
    return str(vues)

def playvideosyoutube(request):
    apikey = os.getenv('api_youtubedata')
    videosyoutube = []
    # gestion d'erreur
    try:
        youtube = build('youtube', 'v3', developerKey=apikey)
        yt_request = youtube.videos().list(
            part='snippet,statistics',
            chart='mostPopular',
            regionCode='US',
            videoCategoryId='10',  # Musique
            maxResults=20
        )
        response = yt_request.execute()
        # parcourir toutes les videos
        for video in response.get('items', []):
            vues_str = video['statistics'].get('viewCount', '0')
            try:
                vues = int(vues_str)
            except (ValueError, TypeError):
                vues = 0

            videosyoutube.append({
                "id": video['id'],
                "titre": video['snippet']['title'],
                "artiste": video['snippet']['channelTitle'],
                "vues": format_vues(vues_str),
            })

    except HttpError as e:
        print(f"Erreur API YouTube : {e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

    context = {"videosyoutube": videosyoutube}
    return render(request, 'videosyoutube.html', context)
