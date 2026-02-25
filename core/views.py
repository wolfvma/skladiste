from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, ExpressionWrapper, DecimalField, F

from .models import User, Artikal, Zaduzenje, Supplier
from .forms import LoginForm, ArtikalForm, ZaduzenjeForm, UserCreateForm, UserEditForm, SupplierForm
from .decorators import admin_required


# ─── AUTH ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Dobrodošli, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Pogrešno korisničko ime ili lozinka.')
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Uspješno ste se odjavili.')
    return redirect('login')


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    total_artikala = Artikal.objects.count()
    ukupna_kolicina = Artikal.objects.aggregate(total=Sum('kolicina'))['total'] or 0
    otvorena_zaduzenja = Zaduzenje.objects.filter(status='DODIJELJENO').count()
    zavrsena_zaduzenja = Zaduzenje.objects.filter(status='ZAVRSENO').count()
    posljednji_artikli = Artikal.objects.select_related('unio').order_by('-datum_unosa')[:5]
    posljednja_zaduzenja = Zaduzenje.objects.select_related('artikal', 'kome_izdato').order_by('-datum_dodjele')[:5]
    context = {
        'total_artikala': total_artikala,
        'ukupna_kolicina': ukupna_kolicina,
        'otvorena_zaduzenja': otvorena_zaduzenja,
        'zavrsena_zaduzenja': zavrsena_zaduzenja,
        'posljednji_artikli': posljednji_artikli,
        'posljednja_zaduzenja': posljednja_zaduzenja,
    }
    return render(request, 'dashboard.html', context)


# ─── ARTIKLI ─────────────────────────────────────────────────────────────────

@login_required
def artikli_lista(request):
    q = request.GET.get('q', '')
    artikli = Artikal.objects.select_related('unio').order_by('-datum_unosa')
    if q:
        artikli = artikli.filter(
            Q(naziv_artikla__icontains=q) |
            Q(sifra_artikla__icontains=q) |
            Q(random_broj__icontains=q)
        )
    return render(request, 'artikli/lista.html', {'artikli': artikli, 'q': q})


@login_required
def artikal_unos(request):
    form = ArtikalForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            artikal = form.save(commit=False)
            artikal.unio = request.user
            artikal.save()
            messages.success(request, f'Artikal "{artikal.naziv_artikla}" uspješno unesen! Broj: {artikal.random_broj}')
            return redirect('artikli_lista')
    return render(request, 'artikli/unos.html', {'form': form})


# ─── ZADUZENJA ───────────────────────────────────────────────────────────────

@login_required
def zaduzenja_lista(request):
    status_filter = request.GET.get('status', '')
    radnik_filter = request.GET.get('radnik', '')
    zaduzenja = Zaduzenje.objects.select_related('artikal', 'kome_izdato', 'zavrsio').order_by('-datum_dodjele')
    if status_filter:
        zaduzenja = zaduzenja.filter(status=status_filter)
    if radnik_filter:
        zaduzenja = zaduzenja.filter(kome_izdato__username__icontains=radnik_filter)
    radnici = User.objects.filter(is_active=True).order_by('username')
    return render(request, 'zaduzenja/lista.html', {
        'zaduzenja': zaduzenja,
        'status_filter': status_filter,
        'radnik_filter': radnik_filter,
        'radnici': radnici,
    })


@login_required
def zaduzenje_novo(request):
    form = ZaduzenjeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            zaduzenje = form.save(commit=False)
            # Reduce stock
            artikal = zaduzenje.artikal
            artikal.kolicina -= zaduzenje.kolicina
            artikal.save()
            zaduzenje.save()
            messages.success(
                request,
                f'Uspješno dodijeljeno {zaduzenje.kolicina} kom "{artikal.naziv_artikla}" → {zaduzenje.kome_izdato.username}'
            )
            return redirect('zaduzenja_lista')
    return render(request, 'zaduzenja/novo.html', {'form': form})


@login_required
def zaduzenje_zavrsi(request, pk):
    zaduzenje = get_object_or_404(Zaduzenje, pk=pk)
    if zaduzenje.status == 'DODIJELJENO':
        zaduzenje.status = 'ZAVRSENO'
        zaduzenje.zavrsio = request.user
        zaduzenje.datum_zavrsetka = timezone.now()
        zaduzenje.save()
        messages.success(request, f'Zaduženje za "{zaduzenje.artikal.naziv_artikla}" označeno kao završeno.')
    else:
        messages.warning(request, 'Zaduženje je već završeno.')
    return redirect('zaduzenja_lista')


# ─── KORISNICI (ADMIN ONLY) ───────────────────────────────────────────────────

@admin_required
def korisnici_lista(request):
    korisnici = User.objects.order_by('username')
    return render(request, 'korisnici/lista.html', {'korisnici': korisnici})


@admin_required
def korisnik_novi(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Korisnik "{user.username}" uspješno kreiran.')
            return redirect('korisnici_lista')
    return render(request, 'korisnici/forma.html', {'form': form, 'naslov': 'Novi korisnik', 'edit': False})


@admin_required
def korisnik_izmijeni(request, pk):
    korisnik = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=korisnik)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Korisnik "{korisnik.username}" uspješno izmijenjen.')
            return redirect('korisnici_lista')
    return render(request, 'korisnici/forma.html', {
        'form': form,
        'naslov': f'Izmijeni korisnika: {korisnik.username}',
        'edit': True,
        'korisnik': korisnik,
    })


@admin_required
def korisnik_obrisi(request, pk):
    korisnik = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if korisnik == request.user:
            messages.error(request, 'Ne možete obrisati vlastiti nalog.')
            return redirect('korisnici_lista')
        ime = korisnik.username
        korisnik.delete()
        messages.success(request, f'Korisnik "{ime}" uspješno obrisan.')
        return redirect('korisnici_lista')
    return render(request, 'korisnici/potvrda_brisanja.html', {'korisnik': korisnik})


# ─── DOBAVLJAČI (ADMIN ONLY) ──────────────────────────────────────────────────

@admin_required
def dobavljaci_lista(request):
    q = request.GET.get('q', '')
    aktivan_filter = request.GET.get('aktivan', '')
    dobavljaci = Supplier.objects.all()
    if q:
        dobavljaci = dobavljaci.filter(
            Q(naziv_firme__icontains=q) |
            Q(kontakt_osoba__icontains=q) |
            Q(grad__icontains=q) |
            Q(opis__icontains=q)
        )
    if aktivan_filter == '1':
        dobavljaci = dobavljaci.filter(aktivan=True)
    elif aktivan_filter == '0':
        dobavljaci = dobavljaci.filter(aktivan=False)
    return render(request, 'dobavljaci/lista.html', {
        'dobavljaci': dobavljaci,
        'q': q,
        'aktivan_filter': aktivan_filter,
    })


@admin_required
def dobavljac_detalj(request, pk):
    dobavljac = get_object_or_404(Supplier, pk=pk)
    artikli = dobavljac.artikli.select_related('unio').order_by('-datum_unosa')
    # Compute total value of all items from this supplier
    ukupna_vrijednost = artikli.filter(cijena__isnull=False).aggregate(
        total=Sum(
            ExpressionWrapper(F('cijena') * F('kolicina'), output_field=DecimalField())
        )
    )['total'] or 0
    return render(request, 'dobavljaci/detalj.html', {
        'dobavljac': dobavljac,
        'artikli': artikli,
        'ukupna_vrijednost': ukupna_vrijednost,
    })


@admin_required
def dobavljac_novi(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            dobavljac = form.save()
            messages.success(request, f'Dobavljač "{dobavljac.naziv_firme}" uspješno dodan.')
            return redirect('dobavljac_detalj', pk=dobavljac.pk)
    return render(request, 'dobavljaci/forma.html', {
        'form': form,
        'naslov': 'Novi dobavljač',
        'edit': False,
    })


@admin_required
def dobavljac_izmijeni(request, pk):
    dobavljac = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=dobavljac)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Dobavljač "{dobavljac.naziv_firme}" uspješno izmijenjen.')
            return redirect('dobavljac_detalj', pk=dobavljac.pk)
    return render(request, 'dobavljaci/forma.html', {
        'form': form,
        'naslov': f'Izmijeni: {dobavljac.naziv_firme}',
        'edit': True,
        'dobavljac': dobavljac,
    })


@admin_required
def dobavljac_obrisi(request, pk):
    dobavljac = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        naziv = dobavljac.naziv_firme
        # Unlink articles (set supplier to NULL)
        dobavljac.artikli.update(supplier=None)
        dobavljac.delete()
        messages.success(request, f'Dobavljač "{naziv}" uspješno obrisan.')
        return redirect('dobavljaci_lista')
    return render(request, 'dobavljaci/potvrda_brisanja.html', {'dobavljac': dobavljac})

