from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Artikal, Zaduzenje


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Detalji', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('username',)
    ordering = ('username',)


@admin.register(Artikal)
class ArtikalAdmin(admin.ModelAdmin):
    list_display = ('random_broj', 'sifra_artikla', 'naziv_artikla', 'kolicina', 'cijena', 'datum_unosa', 'unio')
    search_fields = ('naziv_artikla', 'sifra_artikla', 'random_broj')
    list_filter = ('datum_unosa',)
    readonly_fields = ('random_broj', 'datum_unosa', 'unio')


@admin.register(Zaduzenje)
class ZaduzenjeAdmin(admin.ModelAdmin):
    list_display = ('artikal', 'kome_izdato', 'kolicina', 'datum_dodjele', 'status')
    list_filter = ('status', 'datum_dodjele')
    search_fields = ('artikal__naziv_artikla', 'kome_izdato__username')
    readonly_fields = ('datum_dodjele',)
