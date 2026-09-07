import os

from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import requests
# Create your models here.
# Liste des avatars predefinis (URLS Externe)
avatar_definis = [('avatar-1', 'https://i.pravatar.cc/150?img=1'),
                  ('avatar-2','https://i.pravatar.cc/150?img=5'),
                  ('avatar-3 (Masculin)','https://i.pravatar.cc/150?img=12'),
                  ('avatar-4 (Feminin)', 'https://i.pravatar.cc/150?img=42'),
                  ('avatar-5', 'https://i.pravatar.cc/150?img=68'),
                  ]
class Station(models.Model):
    nomstation = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    image = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.nomstation}"

class Article(models.Model):
    title  = models.CharField(max_length=300, verbose_name='titre')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='Slug(URL)')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles', verbose_name='Auteur'                         )
    summary = models.TextField(max_length=200, help_text='Un resume court pour les cartes actualites', verbose_name='Resume')
    content = models.TextField(verbose_name='Contenu de l\'article')
    image = models.URLField(max_length=1000, blank=True, null=True,verbose_name='Adresse URL de l\'image')
    category = models.CharField(max_length=20, choices=[('actualites','actualites'),('sports', 'sports'),('sante', 'sante'),('sciences','sciences'),('politiques','politiques')],default='actualites',verbose_name='Categories')
    sources = models.CharField(max_length=255, blank=True, null=True, help_text='Exemple: lemonde, AFP, Reuters(separes des virgules)')
    status = models.CharField(max_length=10, choices=[('brouillon', 'brouillon'),('publie', 'publie')])
    created_at =  models.DateTimeField(auto_now_add=True, verbose_name='date de creation')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='date de modification')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='date de publication')
    class Meta:
        ordering = ['-published_at']
        verbose_name = 'article'
        verbose_name_plural = 'articles'

    def __str__(self):
        return f"{self.title}"
    # creation de slug automatiquement (pour les urls)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Si aucune image n'est fournie manuellement, on interroge Unsplash
        if not self.image:
            try:
                API_Unsplash = os.getenv('API_Unsplash')
                # On combine la catégorie en français et le titre pour maximiser la pertinence
                recherche = f"{self.title}"
                url = "https://api.unsplash.com/search/photos"
                params = {'query': recherche, 'per_page': 1,
                          'orientation': 'landscape'}#
                # Force le format horizontal
                headers = {'Authorization': f'Client-ID {API_Unsplash}'}
                response = requests.get(url, params=params, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        # "regular" donne une excellente définition (1080px) adaptée au web
                        self.image = data['results'][0]['urls']['regular']
                        print(self.image)
                else:
                    print(f"Unsplash API a renvoyé une erreur: {response.status_code}")
            except Exception as e:
                print(f"Erreur de connexion à l'API Unsplash: {e}")

        super().save(*args, **kwargs)


class Musiques(models.Model):
    genre_m = [('kompa','Kompa'),('rap','Rap'),('afrobeat','Afrobeat'),('rnb','RNB'),('gospel','Gospel'),('racine','Musique Racine'),('autre','Autre')]
    titre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    artiste = models.CharField(max_length=200)
    genre = models.CharField(max_length=20, choices=genre_m, default='autre')
    audio_url = models.URLField(max_length=500, help_text="Lien direct vers le fichier")
    image_url = models.URLField(max_length=500, blank=True, help_text="Pochette (Bunny.net ou autre CDN)")
    nb_ecoutes = models.PositiveIntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-date_ajout']
        verbose_name="Musique"
        verbose_name_plural = "Musiques"

    def __str__(self):
        return f"{self.titre}-{self.artiste}"
        # creation de slug automatiquement (pour les urls)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

class Lyric(models.Model):
    musique = models.OneToOneField(Musiques, on_delete=models.CASCADE, related_name='lyrics')
    contenu = models.TextField(blank=True, null=True)
    contenu_lrc = models.TextField(blank=True, null=True)
    source = models.TextField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Lyrics de :{self.musique.titre}"

#
class Commentaire(models.Model):
    musique = models.ForeignKey(Musiques, on_delete=models.CASCADE, related_name='commentaires')
    user = models.ForeignKey(User,  on_delete=models.CASCADE)
    commentaire = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-date']
        verbose_name='Commentaire'
        verbose_name_plural='Commentaires'
    def __str__(self):
        return f"Commentaire de {self.user.username}"

# classe profil pour les utilisateurs
class Profil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.CharField(max_length=50, choices=[(cle, cle) for cle, url in avatar_definis] ,blank=True, default=avatar_definis[0][1])
    bio = models.TextField(max_length=500, blank=True)
    datenaissance = models.DateField(null=True,blank=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    def __str__(self):
        return f"Profil de {self.user.username}"

    # methode qui va permet d'afficher l'image du profil de l'utilisateur
    @property
    def get_avatar_url(self):
        avatars_dict = dict(avatar_definis)
        # si l'utilisateur a choisi un avatar et qu'il existe dans notre liste
        if self.photo in avatars_dict:
            return avatars_dict[str(self.photo)]
        return avatar_definis[0][1]


class ChaineTV(models.Model):
    nom = models.CharField(max_length=200, null=True ,verbose_name='Nom')
    slug = models.SlugField(max_length=220,null=True, blank=True, unique=True)
    url = models.URLField(max_length=300,help_text='Lien vers la chaine..')
    logo = models.URLField(max_length=300,help_text='Logo de la chaine..')
    class Meta:
        verbose_name = 'ChaineTV'
        verbose_name_plural = 'ChainesTV'
    def __str__(self):
        return f"Tele {self.nom}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

# La classe playlist
class Playlist(models.Model):
    user = models.ForeignKey(User,	on_delete=models.CASCADE, related_name='playlists')
    nom	= models.CharField(max_length=100)
    morceaux = models.ManyToManyField(Musiques, related_name='playlists', blank=True)
    date_creation =	models.DateTimeField(auto_now_add=True)
    def	__str__(self):
        return	f"Playlist: {self.nom}"