"""
URL configuration for ProjetActuWeb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('ActuWebApp.urls')),
    path('admin/', admin.site.urls),
    path('article/<int:year>/<int:month>/<int:day>/<slug:slug>/', include('ActuWebApp.urls')),
    path('sports/', include('ActuWebApp.urls')),
    path('sports/score-en-direct/', include('ActuWebApp.urls')),
    path('sports/classements-buteurs/', include('ActuWebApp.urls')),
    path('sports/match-termine/', include('ActuWebApp.urls')),
    path('previsions-meteo/', include('ActuWebApp.urls')),
    path('musiques/', include('ActuWebApp.urls')),
    path('musiques/lecture/<slug:slug>/', include('ActuWebApp.urls')),
    path('login/', include('ActuWebApp.urls')),
    path('logout/', include('ActuWebApp.urls')),
    path('create-account/', include('ActuWebApp.urls')),
    path('musiques/lecture/<slug:slug>/commenter/', include('ActuWebApp.urls')),
    path('stations-radios', include('ActuWebApp.urls')),
    path('sport/<int:year>/<int:month>/<int:day>/<slug:slug>/', include('ActuWebApp.urls')),
    path('sante/', include('ActuWebApp.urls')),
    path('sante/<int:year>/<int:month>/<int:day>/<slug:slug>/', include('ActuWebApp.urls')),
    path('sciences/', include('ActuWebApp.urls')),
    path('sciences/<int:year>/<int:month>/<int:day>/<slug:slug>/', include('ActuWebApp.urls')),
    path('live-tv/', include('ActuWebApp.urls')),
    path('live-tv/<slug:slug>', include('ActuWebApp.urls')),
#     path('playlist/modal/creer', include('ActuWebApp.urls')),
#     path('playlist/creer', include('ActuWebApp.urls')),
#     path('playlist/fragment',include('ActuWebApp.urls')),
#     path('playlist/ajouter/<int:musique_id>/<int:playlist_id>/',include('ActuWebApp.urls')),
#     path('playlist/menu/<int:musique_id>/<int:playlist_id>/', include('ActuWebApp.urls'))
#
    path('playlists/creer/modal/',include('ActuWebApp.urls')),
    path('playlists/creer/', include('ActuWebApp.urls')),
    path('playlists/mes-playlists/',include('ActuWebApp.urls')),
    path('playlists/<int:playlist_id>/musiques/',include('ActuWebApp.urls')),
    path('playlists/<int:playlist_id>/retirer/<int:musique_id>/', include('ActuWebApp.urls')),
    path('musique/<int:musique_id>/ajouter-playlist/', include('ActuWebApp.urls')),
    path('musique/<int:musique_id>/playlist/<int:playlist_id>/ajouter/', include('ActuWebApp.urls')),
    path('playlists/<int:playlist_id>/supprimerplaylist/', include('ActuWebApp.urls')),
    path('playlists/<int:playlist_id>/detailplaylist/', include('ActuWebApp.urls')),
    path('assistant-ai', include('ActuWebApp.urls')),
    path('recherche-musique', include('ActuWebApp.urls'))

]
