from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Artikli
    path('artikli/', views.artikli_lista, name='artikli_lista'),
    path('artikli/unos/', views.artikal_unos, name='artikal_unos'),

    # Zaduzenja
    path('zaduzenja/', views.zaduzenja_lista, name='zaduzenja_lista'),
    path('zaduzenja/novo/', views.zaduzenje_novo, name='zaduzenje_novo'),
    path('zaduzenja/<int:pk>/zavrsi/', views.zaduzenje_zavrsi, name='zaduzenje_zavrsi'),

    # Korisnici (admin only)
    path('korisnici/', views.korisnici_lista, name='korisnici_lista'),
    path('korisnici/novi/', views.korisnik_novi, name='korisnik_novi'),
    path('korisnici/<int:pk>/izmijeni/', views.korisnik_izmijeni, name='korisnik_izmijeni'),
    path('korisnici/<int:pk>/obrisi/', views.korisnik_obrisi, name='korisnik_obrisi'),

    # Dobavljači (admin only)
    path('dobavljaci/', views.dobavljaci_lista, name='dobavljaci_lista'),
    path('dobavljaci/novi/', views.dobavljac_novi, name='dobavljac_novi'),
    path('dobavljaci/<int:pk>/', views.dobavljac_detalj, name='dobavljac_detalj'),
    path('dobavljaci/<int:pk>/izmijeni/', views.dobavljac_izmijeni, name='dobavljac_izmijeni'),
    path('dobavljaci/<int:pk>/obrisi/', views.dobavljac_obrisi, name='dobavljac_obrisi'),
]

