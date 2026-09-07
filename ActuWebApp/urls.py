from django.urls import path
from . import views

app_name = 'ActuWebApp'
urlpatterns = [
    path('',  views.index, name='index'),
    path('article/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.article_detail, name='article_detail'),
    path('sports/', views.infossportsactualites, name='sports_view'),
    path('sports/score-en-direct/',views.matchsencours, name='match_encours'),
    path('sports/classements-buteurs/', views.recuperertousbuteurs, name='cl_buteurs'),
    path('sports/match-termine/', views.matchtermineend, name='match_termine'),
    path('previsions-meteo/', views.affichermeteo, name='meteo_view'),
    path('musiques/', views.affichermusiques, name='aff_mus'),
    path('musiques/lecture/<slug:slug>/', views.lecturemusiques, name='play_mus'),
    path('login/', views.seconnecter, name='connect'),
    path('logout/', views.sedeconnecter, name='logout'),
    path('create-account/', views.inscription, name='create'),
    path('musiques/lecture/<slug:slug>/commenter/', views.ajoutercommentaires, name='addcomment'),
    path('stations-radios', views.stationradio, name='statradio'),
    path('sport/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.sport_detail, name='sport_detail'),
    path('sante/', views.infos_sante, name='sante'),
    path('sciences/', views.infos_sciences, name='sciences'),
    path('sante/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.sante_detail, name='sante_detail'),
    path('sciences/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.science_detail, name='sciences_detail'),
    path('live-tv/', views.AfficherTele, name='tele'),
    path('live-tv/<slug:slug>/', views.regardertv, name='livetv'),
    path('playlist/modal/creer', views.modal_creer_playlist, name='modal_creer_play'),
    path('playlist/creer', views.creerplaylist, name='creer_playlist'),
    # path('playlist/fragment', views.fragment_Play, name='fragment_mes_playlists'),
    # path('playlist/ajouter/<int:musique_id>/<int:playlist_id>/', views.ajouter_playlist, name='ajout_playlist'),
    # path('playlist/menu/<int:musique_id>/<int:playlist_id>/', views.menu_playlist, name='menu_playlists'),
    # path('playlists/creer/modal/', views.modal_creer_playlist, name='modal_creer_play'),
    # path('playlists/creer/', views.creer_playlist, name='modal_creer_play'),
    path('playlists/mes-playlists/', views.fragment_mes_playlists, name='fragment_mes_playlists'),
    path('playlists/<int:playlist_id>/musiques/', views.playlist_musiques, name='playlist_musiques'),
    path('playlists/<int:playlist_id>/retirer/<int:musique_id>/', views.retirer_musique_playlist,name='retirer_musique_playlist'),
    path('musique/<int:musique_id>/ajouter-playlist/', views.ajout_playlist, name='ajout_playlist'),
    path('musique/<int:musique_id>/playlist/<int:playlist_id>/ajouter/', views.ajouter_musique_playlist, name='ajouter_musique_playlist'),
    path('playlists/<int:playlist_id>/supprimerplaylist/', views.supprimerplaylist, name='supp_playlist'),
    path('playlists/<int:playlist_id>/detailplaylist/', views.detail_playlist, name='detail_playlist'),
    path('gemini-ai', views.assistanceai, name='ai_assistant'),
    path('recherche-musique', views.recherchermusiques, name='rechmus')

]