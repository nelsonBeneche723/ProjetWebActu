from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Station, Article, Musiques, Commentaire, Profil, Lyric, ChaineTV
# Register your models here.
class ListerStation(admin.ModelAdmin):
    list_display = ('nomstation','url','image')
    search_fields = ('nomstation',)
    list_filter = ('image',)

    def aff_nomstation(self, obj):
        return obj.station.nomstation
    aff_nomstation.short_description = 'nom'

class ListerArticle(admin.ModelAdmin):
    list_display = ('title','category','author','status','published_at')
    list_filter = ('category','status','created_at','author')
    search_fields = ('title','content','summary','sources')
    prepopulated_fields = {'slug': ('title', )}
    date_hierarchy = 'published_at'

class ListerMusique(admin.ModelAdmin):
    list_display = ('artiste','titre','genre','audio_url','image_url','date_ajout')
    list_filter = ('artiste','genre','date_ajout')
    search_fields = ('titre','artiste')
    prepopulated_fields = {'slug': ('titre', )}
    date_hierarchy = 'date_ajout'

@admin.register(Commentaire)
class VoirCommentaire(admin.ModelAdmin):
    list_display = ('musique','user','contenu_court','date')
    list_filter = ('user','date','musique')
    search_fields = ('commentaire','user__username')
    date_hierarchy = 'date'
    ordering = ['-date']
    # pour afficher les contenus au nombre de 50 caracteres
    def contenu_court(self, obj):
        return obj.commentaire[:50]+ '...' if len(obj.commentaire) > 50 else obj.commentaire
    contenu_court.short_description = 'Commentaire'


class ProfilInline(admin.StackedInline):
    model= Profil
    can_delete = False
    verbose_name_plural = 'Profil'

class UserAdminProfil(admin.ModelAdmin):
    inlines = (ProfilInline,)

# Reenregistrer User avec le profil integre
admin.site.unregister(User)
admin.site.register(User, UserAdminProfil)

class ProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'ville', 'date_creation')
    list_filter = ('user__username', 'user__email', 'ville')
    search_fields = ('date_creation', )

class AfficherLyric(admin.ModelAdmin):
    list_display = ('musique', 'contenu', 'source','date')
    list_filter = ('date','musique')
    search_fields = ('date',)
    def contenu(self, obj):
        return obj.contenu[:50]+ '...' if len(obj.contenu) > 50 else obj.contenu

class ChaineTvAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug','url', 'logo')
    list_filter = ('nom',)
    search_fields = ('nom', )
    prepopulated_fields = {'slug': ('nom', )}


# @receiver(post_save, sender=User)
# def creer_profil(sender, instance,created, **kwargs):
#     if created:
#         Profil.objects.create(user=instance)
#
# @receiver(post_save, sender=User)
# def sauvegarder_profil(sender, instance, **kwargs):
#     instance.profil.save()

# Enregistrement toutes les modeles dans la page administrateur
admin.site.register(Station, ListerStation)
admin.site.register(Article, ListerArticle)
admin.site.register(Musiques, ListerMusique)
admin.site.register(Profil, ProfilAdmin)
admin.site.register(Lyric, AfficherLyric)
admin.site.register(ChaineTV, ChaineTvAdmin)
