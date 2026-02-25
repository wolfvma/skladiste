import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, role='RADNIK', **extra_fields):
        if not username:
            raise ValueError('Korisničko ime je obavezno')
        user = self.model(username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('RADNIK', 'Radnik'),
    ]

    username = models.CharField(max_length=150, unique=True, verbose_name='Korisničko ime')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='RADNIK', verbose_name='Uloga')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Korisnik'
        verbose_name_plural = 'Korisnici'

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_radnik(self):
        return self.role == 'RADNIK'


# ─── SUPPLIER ─────────────────────────────────────────────────────────────────

class Supplier(models.Model):
    naziv_firme = models.CharField(max_length=255, verbose_name='Naziv firme')
    kontakt_osoba = models.CharField(max_length=150, blank=True, verbose_name='Kontakt osoba')
    telefon = models.CharField(max_length=50, blank=True, verbose_name='Telefon')
    email = models.EmailField(blank=True, verbose_name='Email')
    adresa = models.TextField(blank=True, verbose_name='Adresa')
    grad = models.CharField(max_length=100, blank=True, verbose_name='Grad')
    drzava = models.CharField(max_length=100, blank=True, default='Bosna i Hercegovina', verbose_name='Država')
    opis = models.TextField(blank=True, verbose_name='Opis (šta nabavljamo)')
    napomena = models.TextField(blank=True, verbose_name='Interna napomena')
    aktivan = models.BooleanField(default=True, verbose_name='Aktivan')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Datum kreiranja')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Datum izmjene')

    class Meta:
        verbose_name = 'Dobavljač'
        verbose_name_plural = 'Dobavljači'
        ordering = ['naziv_firme']

    def __str__(self):
        return self.naziv_firme

    def ukupna_vrijednost(self):
        """Total value of all items from this supplier."""
        from django.db.models import Sum, F, ExpressionWrapper, DecimalField
        result = self.artikli.filter(cijena__isnull=False).aggregate(
            total=Sum(
                ExpressionWrapper(F('cijena') * F('kolicina'), output_field=DecimalField())
            )
        )['total']
        return result or 0


# ─── ARTIKAL ──────────────────────────────────────────────────────────────────

def generate_random_broj():
    return str(uuid.uuid4()).split('-')[0].upper()


class Artikal(models.Model):
    random_broj = models.CharField(max_length=20, unique=True, default=generate_random_broj, editable=False, verbose_name='Broj artikla')
    sifra_artikla = models.CharField(max_length=100, verbose_name='Šifra artikla')
    naziv_artikla = models.CharField(max_length=255, verbose_name='Naziv artikla')
    kolicina = models.PositiveIntegerField(default=0, verbose_name='Količina')
    cijena = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Cijena (KM)')
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='artikli', verbose_name='Dobavljač'
    )
    datum_unosa = models.DateTimeField(auto_now_add=True, verbose_name='Datum unosa')
    unio = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uneseni_artikli', verbose_name='Unio')

    class Meta:
        verbose_name = 'Artikal'
        verbose_name_plural = 'Artikli'
        ordering = ['-datum_unosa']

    def __str__(self):
        return f'[{self.random_broj}] {self.naziv_artikla} ({self.kolicina} kom)'

    def ukupna_vrijednost(self):
        if self.cijena:
            return self.cijena * self.kolicina
        return None


# ─── ZADUZENJE ────────────────────────────────────────────────────────────────

class Zaduzenje(models.Model):
    STATUS_CHOICES = [
        ('DODIJELJENO', 'Dodijeljeno'),
        ('ZAVRSENO', 'Završeno'),
    ]

    artikal = models.ForeignKey(Artikal, on_delete=models.CASCADE, related_name='zaduzenja', verbose_name='Artikal')
    kome_izdato = models.ForeignKey(User, on_delete=models.CASCADE, related_name='zaduzenja', verbose_name='Kome izdato')
    kolicina = models.PositiveIntegerField(verbose_name='Količina')
    datum_dodjele = models.DateTimeField(auto_now_add=True, verbose_name='Datum dodjele')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DODIJELJENO', verbose_name='Status')
    zavrsio = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='zavrsena_zaduzenja', verbose_name='Završio')
    datum_zavrsetka = models.DateTimeField(null=True, blank=True, verbose_name='Datum završetka')

    class Meta:
        verbose_name = 'Zaduženje'
        verbose_name_plural = 'Zaduženja'
        ordering = ['-datum_dodjele']

    def __str__(self):
        return f'{self.artikal.naziv_artikla} → {self.kome_izdato.username} ({self.get_status_display()})'
