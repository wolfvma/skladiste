from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Artikal, Zaduzenje, Supplier


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Korisničko ime',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Unesite korisničko ime',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Lozinka',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Unesite lozinku',
        })
    )


class ArtikalForm(forms.ModelForm):
    class Meta:
        model = Artikal
        fields = ['sifra_artikla', 'naziv_artikla', 'kolicina', 'cijena', 'supplier']
        labels = {
            'sifra_artikla': 'Šifra artikla',
            'naziv_artikla': 'Naziv artikla',
            'kolicina': 'Količina',
            'cijena': 'Cijena (KM) – neobavezno',
            'supplier': 'Dobavljač – neobavezno',
        }
        widgets = {
            'sifra_artikla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'npr. ART-001'}),
            'naziv_artikla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Naziv artikla'}),
            'kolicina': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cijena': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(aktivan=True).order_by('naziv_firme')
        self.fields['supplier'].empty_label = '— Bez dobavljača —'
        self.fields['supplier'].required = False


class ZaduzenjeForm(forms.ModelForm):
    class Meta:
        model = Zaduzenje
        fields = ['artikal', 'kolicina', 'kome_izdato']
        labels = {
            'artikal': 'Artikal',
            'kolicina': 'Količina',
            'kome_izdato': 'Kome dodijeliti',
        }
        widgets = {
            'artikal': forms.Select(attrs={'class': 'form-select'}),
            'kolicina': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'kome_izdato': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show items with stock > 0
        self.fields['artikal'].queryset = Artikal.objects.filter(kolicina__gt=0)
        # Only show active workers (all users can be assigned)
        self.fields['kome_izdato'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['kome_izdato'].label_from_instance = lambda obj: f'{obj.username} ({obj.get_role_display()})'

    def clean(self):
        cleaned_data = super().clean()
        artikal = cleaned_data.get('artikal')
        kolicina = cleaned_data.get('kolicina')
        if artikal and kolicina:
            if kolicina > artikal.kolicina:
                raise forms.ValidationError(
                    f'Nema dovoljno na stanju. Dostupno: {artikal.kolicina} kom.'
                )
        return cleaned_data


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Lozinka',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Unesite lozinku'})
    )
    password2 = forms.CharField(
        label='Potvrda lozinke',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ponovite lozinku'})
    )

    class Meta:
        model = User
        fields = ['username', 'role']
        labels = {
            'username': 'Korisničko ime',
            'role': 'Uloga',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Korisničko ime'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Lozinke se ne poklapaju.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        label='Nova lozinka (ostaviti prazno za bez promjene)',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nova lozinka (opciono)'})
    )

    class Meta:
        model = User
        fields = ['username', 'role', 'is_active']
        labels = {
            'username': 'Korisničko ime',
            'role': 'Uloga',
            'is_active': 'Aktivan',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user


# ─── SUPPLIER FORM ────────────────────────────────────────────────────────────

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'naziv_firme', 'kontakt_osoba', 'telefon', 'email',
            'adresa', 'grad', 'drzava', 'opis', 'napomena', 'aktivan',
        ]
        labels = {
            'naziv_firme': 'Naziv firme',
            'kontakt_osoba': 'Kontakt osoba',
            'telefon': 'Telefon',
            'email': 'Email',
            'adresa': 'Adresa',
            'grad': 'Grad',
            'drzava': 'Država',
            'opis': 'Opis (šta nabavljamo od njih)',
            'napomena': 'Interna napomena',
            'aktivan': 'Aktivan',
        }
        widgets = {
            'naziv_firme': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Naziv firme d.o.o.'}),
            'kontakt_osoba': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ime i prezime'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+387 ...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@firma.ba'}),
            'adresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ulica i broj'}),
            'grad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sarajevo'}),
            'drzava': forms.TextInput(attrs={'class': 'form-control'}),
            'opis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Kratki opis šta nabavljamo...'}),
            'napomena': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Interna napomena...'}),
        }
