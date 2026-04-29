from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.http import FileResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)

from .forms import UserCarForm
from .models import Car, Favorite


def favicon_view(request):
    response = FileResponse(
        open(settings.BASE_DIR / "cars/static/cars/favicons/favicon.ico", "rb"),
        content_type="image/x-icon",
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def _should_expose_email_links():
    return bool(getattr(settings, "EMAIL_LINKS_IN_RESPONSE", False))


def _get_int_param(request, name):
    value = request.GET.get(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _get_session_favorite_ids(request):
    raw_ids = request.session.get("favorite_car_ids", [])
    return [int(car_id) for car_id in raw_ids if str(car_id).isdigit()]


def _set_session_favorite_ids(request, favorite_ids):
    request.session["favorite_car_ids"] = sorted(set(int(car_id) for car_id in favorite_ids))
    request.session.modified = True


def _get_favorite_ids(request):
    if request.user.is_authenticated:
        return list(
            Favorite.objects.filter(user=request.user)
            .values_list("car_id", flat=True)
        )
    return _get_session_favorite_ids(request)


def _toggle_favorite_id(request, car_id):
    if request.user.is_authenticated:
        favorite = Favorite.objects.filter(user=request.user, car_id=car_id)
        if favorite.exists():
            favorite.delete()
        else:
            Favorite.objects.create(user=request.user, car_id=car_id)
    else:
        favorite_ids = set(_get_session_favorite_ids(request))
        if car_id in favorite_ids:
            favorite_ids.remove(car_id)
        else:
            favorite_ids.add(car_id)
        _set_session_favorite_ids(request, favorite_ids)


def _sync_session_favorites_to_user(request, user):
    favorite_ids = _get_session_favorite_ids(request)
    if not favorite_ids:
        return

    existing_ids = set(
        Favorite.objects.filter(user=user, car_id__in=favorite_ids)
        .values_list("car_id", flat=True)
    )
    new_ids = [car_id for car_id in favorite_ids if car_id not in existing_ids]
    if new_ids:
        Favorite.objects.bulk_create(
            [Favorite(user=user, car_id=car_id) for car_id in new_ids],
            ignore_conflicts=True,
        )
    request.session.pop("favorite_car_ids", None)
    request.session.modified = True


def _user_has_submitted_car(user):
    if not user.is_authenticated:
        return False
    return Car.objects.filter(created_by=user).exists()


def _get_safe_next_url(request, fallback):
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback


def _build_add_car_redirect(request, next_url=None):
    add_car_url = reverse("add_car")
    target_url = next_url or request.get_full_path()
    if target_url and target_url != add_car_url:
        return redirect(f"{add_car_url}?{urlencode({'next': target_url})}")
    return redirect("add_car")


def _redirect_after_authentication(request):
    if _user_has_submitted_car(request.user):
        return redirect("home")
    return _build_add_car_redirect(request, reverse("home"))


def _profile_context(request):
    user_cars = Car.objects.filter(created_by=request.user).order_by("-id")
    return {
        "user_cars": user_cars,
        "user_cars_count": user_cars.count(),
        "favorites_count": len(_get_favorite_ids(request)),
    }


def _build_add_car_context(*, request, form, next_url, is_required, user_cars, user_cars_count, is_edit_mode, editing_car):
    return {
        "form": form,
        "basic_fields": [form[field_name] for field_name in form.BASIC_FIELDS],
        "safety_fields": [form[field_name] for field_name in form.SAFETY_FIELDS],
        "equipment_fields": [form[field_name] for field_name in form.EQUIPMENT_FIELDS],
        "next_url": next_url,
        "is_required": is_required,
        "user_cars": user_cars,
        "user_cars_count": user_cars_count,
        "is_edit_mode": is_edit_mode,
        "editing_car": editing_car,
        "favorites_count": len(_get_favorite_ids(request)),
    }


def require_user_car(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not _user_has_submitted_car(request.user):
            return _build_add_car_redirect(request)
        return view_func(request, *args, **kwargs)

    return wrapped_view


def _build_catalog_context(request, *, favorites_only=False):
    favorite_ids = _get_favorite_ids(request)
    cars = Car.objects.all()

    if favorites_only:
        cars = cars.filter(id__in=favorite_ids)

    cars = cars.order_by("brand", "model")

    query = request.GET.get("q", "").strip()
    brand = request.GET.get("brand", "").strip()
    fuel = request.GET.get("fuel")
    drive = request.GET.get("drive")
    segment = request.GET.get("segment")
    body_type = request.GET.get("body_type", "").strip()
    gearbox = request.GET.get("gearbox", "").strip()
    min_price = _get_int_param(request, "min_price")
    max_price = _get_int_param(request, "max_price")
    min_power = _get_int_param(request, "min_power")
    year_from = _get_int_param(request, "year_from")
    year_to = _get_int_param(request, "year_to")
    sort_by = request.GET.get("sort", "").strip()

    if query:
        cars = cars.filter(
            Q(brand__icontains=query)
            | Q(model__icontains=query)
            | Q(body_type__icontains=query)
        )

    if brand:
        cars = cars.filter(brand__iexact=brand)

    if fuel:
        cars = cars.filter(fuel_type=fuel)

    if drive:
        cars = cars.filter(drive=drive)

    if segment:
        cars = cars.filter(segment=segment)

    if body_type:
        cars = cars.filter(body_type=body_type)

    if gearbox:
        cars = cars.filter(gearbox__iexact=gearbox)

    if min_price is not None:
        cars = cars.filter(price__gte=min_price)

    if max_price is not None:
        cars = cars.filter(price__lte=max_price)

    if min_power is not None:
        cars = cars.filter(power__gte=min_power)

    if year_from is not None:
        cars = cars.filter(year__gte=year_from)

    if year_to is not None:
        cars = cars.filter(year__lte=year_to)

    sort_map = {
        "price_asc": ("price", "brand", "model"),
        "price_desc": ("-price", "brand", "model"),
        "power_desc": ("-power", "brand", "model"),
        "year_desc": ("-year", "brand", "model"),
        "year_asc": ("year", "brand", "model"),
        "brand_asc": ("brand", "model"),
    }
    if sort_by in sort_map:
        cars = cars.order_by(*sort_map[sort_by])

    return {
        "cars": cars,
        "cars_count": cars.count(),
        "query": query,
        "selected_brand": brand,
        "selected_fuel": fuel,
        "selected_drive": drive,
        "selected_segment": segment,
        "selected_body_type": body_type,
        "selected_gearbox": gearbox,
        "min_price": min_price,
        "max_price": max_price,
        "min_power": min_power,
        "year_from": year_from,
        "year_to": year_to,
        "selected_sort": sort_by,
        "favorites_only": favorites_only,
        "favorite_ids": favorite_ids,
        "favorites_count": len(favorite_ids),
        "brand_options": Car.objects.order_by("brand").values_list("brand", flat=True).distinct(),
        "fuel_options": Car.FUEL_CHOICES,
        "drive_options": Car.DRIVE_CHOICES,
        "segment_options": Car.SEGMENT_CHOICES,
        "body_type_options": Car.BODY_CHOICES,
        "gearbox_options": (
            Car.objects.exclude(gearbox="")
            .order_by("gearbox")
            .values_list("gearbox", flat=True)
            .distinct()
        ),
        "sort_options": (
            ("brand_asc", "Marka A-Z"),
            ("price_asc", "Cena rosnąco"),
            ("price_desc", "Cena malejąco"),
            ("power_desc", "Moc malejąco"),
            ("year_desc", "Najnowsze"),
            ("year_asc", "Najstarsze"),
        ),
    }


def _build_token_url(request, route_name, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return request.build_absolute_uri(
        reverse(route_name, kwargs={"uidb64": uidb64, "token": token})
    )

def _send_branded_email(
    *,
    subject,
    recipient,
    html_template,
    text_template,
    context,
):
    html_body = render_to_string(html_template, context)
    text_body = render_to_string(text_template, context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


def _email_error_message(exc):
    return (
        "Nie udało się wysłać e-maila. Sprawdź konfigurację SMTP w pliku .env "
        f"i spróbuj ponownie. Szczegóły: {exc}"
    )


def _send_activation_email(request, user):
    activation_url = _build_token_url(request, "activate_account", user)
    _send_branded_email(
        subject="Zaproszenie do RedLine Cars - aktywuj konto",
        recipient=user.email,
        html_template="cars/emails/activation_email.html",
        text_template="cars/emails/activation_email.txt",
        context={
            "username": user.username,
            "activation_url": activation_url,
            "home_url": request.build_absolute_uri(reverse("home")),
        },
    )
    return activation_url


def _activation_email_failure_context(request, activation_url, exc):
    if _should_expose_email_links():
        return {
            "success": (
                "Konto zostało utworzone. Wysyłka maila nie przeszła, ale link "
                "aktywacyjny jest dostępny poniżej."
            ),
            "activation_url": activation_url,
            "email_links_in_response": True,
            "warning": _email_error_message(exc),
        }

    return {
        "error": _email_error_message(exc),
        "email_links_in_response": _should_expose_email_links(),
    }


def _send_login_email(request, user):
    login_url = _build_token_url(request, "magic_login_verify", user)
    _send_branded_email(
        subject="RedLine Cars - link do logowania",
        recipient=user.email,
        html_template="cars/emails/login_email.html",
        text_template="cars/emails/login_email.txt",
        context={
            "username": user.username,
            "login_url": login_url,
            "expire_minutes": settings.MAGIC_LINK_EXPIRE_SECONDS // 60,
            "home_url": request.build_absolute_uri(reverse("home")),
        },
    )
    return login_url


@require_user_car
def home(request):
    user_cars = Car.objects.filter(created_by=request.user).order_by("-id")[:3] if request.user.is_authenticated else []
    return render(request, "cars/home.html", {"user_cars": user_cars})


@require_user_car
def car_list(request):
    return render(request, "cars/car_list.html", _build_catalog_context(request))


@require_user_car
def favorites_view(request):
    return render(
        request,
        "cars/car_list.html",
        _build_catalog_context(request, favorites_only=True),
    )


@require_user_car
def toggle_favorite_view(request, car_id):
    if request.method != "POST":
        return redirect("car_list")

    get_object_or_404(Car, pk=car_id)
    _toggle_favorite_id(request, car_id)
    return redirect(request.POST.get("next") or reverse("car_list"))


COMPARE_SECTION_DEFINITIONS = [
    {
        "title": "Podstawy",
        "rows": [
            {"label": "Marka", "getter": lambda car: car.brand},
            {"label": "Model", "getter": lambda car: car.model},
            {"label": "Rocznik", "getter": lambda car: car.year, "better": "higher"},
            {"label": "Cena", "getter": lambda car: car.price, "unit": "zl", "better": "lower"},
            {"label": "Kolor", "getter": lambda car: car.color},
        ],
    },
    {
        "title": "Osiagi",
        "rows": [
            {"label": "Silnik", "getter": lambda car: car.engine},
            {"label": "Moc", "getter": lambda car: car.power, "unit": "KM", "better": "higher"},
            {"label": "0-100", "getter": lambda car: car.acceleration, "unit": "s", "better": "lower"},
            {"label": "Predkosc max", "getter": lambda car: car.max_speed, "unit": "km/h", "better": "higher"},
            {"label": "Spalanie", "getter": lambda car: car.consumption, "unit": "l/100 km", "better": "lower"},
        ],
    },
    {
        "title": "Nadwozie",
        "rows": [
            {"label": "Paliwo", "getter": lambda car: car.get_fuel_type_display()},
            {"label": "Naped", "getter": lambda car: car.get_drive_display()},
            {"label": "Skrzynia", "getter": lambda car: car.gearbox},
            {"label": "Bagaznik", "getter": lambda car: car.trunk_capacity, "unit": "L", "better": "higher"},
            {"label": "Miejsca", "getter": lambda car: car.seats, "better": "higher"},
        ],
    },
    {
        "title": "Wyposazenie",
        "rows": [
            {"label": "Nawigacja", "getter": lambda car: car.navigation, "better": "truthy"},
            {"label": "Kamera cofania", "getter": lambda car: car.parking_camera, "better": "truthy"},
            {"label": "Tempomat adapt.", "getter": lambda car: car.adaptive_cruise, "better": "truthy"},
            {"label": "Panorama", "getter": lambda car: car.panoramic_roof, "better": "truthy"},
            {"label": "Podgrzewane fotele", "getter": lambda car: car.heated_seats, "better": "truthy"},
        ],
    },
]


def _format_compare_value(value, unit=None):
    if value in (None, ""):
        return "-"
    if isinstance(value, bool):
        return "Tak" if value else "Nie"
    if isinstance(value, float):
        value = f"{value:.1f}".rstrip("0").rstrip(".")
    text = str(value)
    if unit:
        return f"{text} {unit}"
    return text


def _resolve_compare_state(left_value, right_value, better=None):
    if left_value == right_value:
        return "same", "same"

    if better == "truthy":
        if bool(left_value) and not bool(right_value):
            return "winner", "different"
        if bool(right_value) and not bool(left_value):
            return "different", "winner"
        return "different", "different"

    if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)) and better:
        if better == "higher":
            if left_value > right_value:
                return "winner", "different"
            if right_value > left_value:
                return "different", "winner"
        if better == "lower":
            if left_value < right_value:
                return "winner", "different"
            if right_value < left_value:
                return "different", "winner"

    return "different", "different"


def _build_compare_sections(left_car, right_car):
    sections = []

    for section in COMPARE_SECTION_DEFINITIONS:
        rows = []
        for row in section["rows"]:
            getter = row["getter"]
            left_value = getter(left_car)
            right_value = getter(right_car)
            left_state, right_state = _resolve_compare_state(
                left_value,
                right_value,
                row.get("better"),
            )
            rows.append(
                {
                    "label": row["label"],
                    "left_display": _format_compare_value(left_value, row.get("unit")),
                    "right_display": _format_compare_value(right_value, row.get("unit")),
                    "left_state": left_state,
                    "right_state": right_state,
                }
            )
        sections.append({"title": section["title"], "rows": rows})

    return sections


def _count_compare_advantages(comparison_sections, side):
    winner_count = 0
    differences_count = 0
    state_key = f"{side}_state"

    for section in comparison_sections:
        for row in section["rows"]:
            state = row[state_key]
            if state == "winner":
                winner_count += 1
            if state != "same":
                differences_count += 1

    return winner_count, differences_count


def _compare_highlight_rows(left_car, right_car):
    definitions = [
        ("Nizsza cena", left_car.price, right_car.price, "lower"),
        ("Wiecej mocy", left_car.power, right_car.power, "higher"),
        ("Lepsze 0-100", left_car.acceleration, right_car.acceleration, "lower"),
        ("Wiekszy bagaznik", left_car.trunk_capacity, right_car.trunk_capacity, "higher"),
        ("Tansze 100 km", left_car.cost_per_100km, right_car.cost_per_100km, "lower"),
        ("Nizszy koszt roczny", left_car.yearly_cost, right_car.yearly_cost, "lower"),
        (
            "Bogatsze wyposazenie",
            len(left_car.equipment_labels),
            len(right_car.equipment_labels),
            "higher",
        ),
    ]

    left_highlights = []
    right_highlights = []

    for label, left_value, right_value, better in definitions:
        left_state, right_state = _resolve_compare_state(left_value, right_value, better)
        if left_state == "winner":
            left_highlights.append(label)
        if right_state == "winner":
            right_highlights.append(label)

    return left_highlights[:4], right_highlights[:4]


def _build_compare_summary(left_car, right_car, comparison_sections):
    left_advantages, differences_count = _count_compare_advantages(comparison_sections, "left")
    right_advantages, _ = _count_compare_advantages(comparison_sections, "right")
    left_highlights, right_highlights = _compare_highlight_rows(left_car, right_car)

    price_gap = abs(left_car.price - right_car.price)
    yearly_cost_gap = abs(left_car.yearly_cost - right_car.yearly_cost)
    cost_100_gap = abs(left_car.cost_per_100km - right_car.cost_per_100km)

    return {
        "left_advantages": left_advantages,
        "right_advantages": right_advantages,
        "differences_count": differences_count,
        "price_gap": _format_compare_value(price_gap, "zl"),
        "yearly_cost_gap": _format_compare_value(yearly_cost_gap, "zl"),
        "cost_100_gap": _format_compare_value(cost_100_gap, "zl"),
        "left_highlights": left_highlights,
        "right_highlights": right_highlights,
        "left_equipment_count": len(left_car.equipment_labels),
        "right_equipment_count": len(right_car.equipment_labels),
    }


@require_user_car
def compare(request):
    cars = []
    left_car = None
    right_car = None
    comparison_sections = []
    compare_error = None
    compare_summary = None

    if request.method == "POST":
        selected_ids = []
        for raw_id in request.POST.getlist("cars"):
            try:
                car_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if car_id not in selected_ids:
                selected_ids.append(car_id)

        if len(selected_ids) != 2:
            compare_error = "Wybierz dokladnie dwa auta do porownania."
        else:
            car_map = {car.id: car for car in Car.objects.filter(id__in=selected_ids)}
            cars = [car_map[car_id] for car_id in selected_ids if car_id in car_map]
            if len(cars) != 2:
                compare_error = "Nie udalo sie pobrac dwoch wybranych aut."
            else:
                left_car, right_car = cars
                comparison_sections = _build_compare_sections(left_car, right_car)
                compare_summary = _build_compare_summary(left_car, right_car, comparison_sections)

    return render(
        request,
        "cars/compare.html",
        {
            "cars": cars,
            "left_car": left_car,
            "right_car": right_car,
            "comparison_sections": comparison_sections,
            "compare_error": compare_error,
            "compare_summary": compare_summary,
        },
    )


@require_user_car
def profile_view(request):
    context = _profile_context(request)
    return render(request, "cars/profile.html", context)


def add_car_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    form = UserCarForm(request.POST or None, request.FILES or None)
    existing_cars = Car.objects.filter(created_by=request.user).order_by("-id")
    next_url = _get_safe_next_url(request, reverse("home"))
    is_required = not existing_cars.exists()

    if request.method == "POST" and form.is_valid():
        car = form.save(commit=False)
        car.created_by = request.user
        car.save()
        messages.success(request, "Twój samochód został dodany do bazy RedLine Cars.")
        return redirect(next_url)

    return render(
        request,
        "cars/add_car.html",
        _build_add_car_context(
            request=request,
            form=form,
            next_url=next_url,
            is_required=is_required,
            user_cars=existing_cars[:4],
            user_cars_count=existing_cars.count(),
            is_edit_mode=False,
            editing_car=None,
        ),
    )


@require_user_car
def edit_car_view(request, car_id):
    car = get_object_or_404(Car, pk=car_id, created_by=request.user)
    form = UserCarForm(request.POST or None, request.FILES or None, instance=car)
    next_url = _get_safe_next_url(request, reverse("profile"))
    existing_cars = Car.objects.filter(created_by=request.user).exclude(pk=car.pk).order_by("-id")

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Zmiany w Twoim samochodzie zostały zapisane.")
        return redirect(next_url)

    return render(
        request,
        "cars/add_car.html",
        _build_add_car_context(
            request=request,
            form=form,
            next_url=next_url,
            is_required=False,
            user_cars=existing_cars[:4],
            user_cars_count=existing_cars.count() + 1,
            is_edit_mode=True,
            editing_car=car,
        ),
    )


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_after_authentication(request)

    context = {
        "email_links_in_response": _should_expose_email_links(),
        "entered_email": "",
    }

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        context["entered_email"] = email

        if not email or not password:
            context["error"] = "Podaj adres e-mail i hasło."
            return render(request, "cars/login.html", context)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            context["error"] = "Nie znaleziono konta z takim adresem e-mail."
            return render(request, "cars/login.html", context)

        if not user.check_password(password):
            context["error"] = "Nieprawidłowy adres e-mail lub hasło."
            return render(request, "cars/login.html", context)

        if not user.is_active:
            try:
                activation_url = _send_activation_email(request, user)
            except Exception as exc:
                context["error"] = _email_error_message(exc)
            else:
                context["error"] = "Konto nie jest jeszcze aktywne. Wysłaliśmy ponownie link aktywacyjny."
                if _should_expose_email_links():
                    context["activation_url"] = activation_url
            return render(request, "cars/login.html", context)

        authenticated_user = authenticate(request, username=user.username, password=password)
        if authenticated_user is None:
            context["error"] = "Nie udało się zalogować. Spróbuj ponownie."
            return render(request, "cars/login.html", context)

        login(request, authenticated_user)
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        _sync_session_favorites_to_user(request, authenticated_user)
        messages.success(request, "Zalogowano pomyślnie.")
        return _redirect_after_authentication(request)

    return render(request, "cars/login.html", context)


def email_login_request_view(request):
    messages.info(request, "Logowanie linkiem zostało wyłączone. Użyj adresu e-mail i hasła.")
    return redirect("login")


def activate_account_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)
    except (TypeError, ValueError, OverflowError):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return render(
            request,
            "cars/login.html",
            {"error": "Ten link aktywacyjny jest nieprawidłowy albo już wygasł."},
        )

    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])

    login(request, user)
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    _sync_session_favorites_to_user(request, user)
    messages.success(request, "Konto zostało aktywowane i jesteś już zalogowany.")
    return _redirect_after_authentication(request)


def magic_login_verify_view(request, uidb64, token):
    return render(
        request,
        "cars/login.html",
        {"error": "Logowanie linkiem zostało wyłączone. Zaloguj się adresem e-mail i hasłem."},
    )


def register_view(request):
    if request.user.is_authenticated:
        return _redirect_after_authentication(request)

    error = None
    success = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            error = "Uzupełnij login, e-mail i hasło."
        elif password != confirm_password:
            error = "Hasła muszą być identyczne."
        elif User.objects.filter(username=username).exists():
            error = "Taki login jest już zajęty."
        elif User.objects.filter(email__iexact=email).exists():
            error = "Konto z tym adresem e-mail już istnieje."
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False,
            )
            try:
                activation_url = _send_activation_email(request, user)
            except Exception as exc:
                activation_url = _build_token_url(request, "activate_account", user)
                if not _should_expose_email_links():
                    user.delete()
                return render(
                    request,
                    "cars/register.html",
                    _activation_email_failure_context(request, activation_url, exc),
                )
            success = (
                "Konto zostało utworzone. Wysłaliśmy mail z zaproszeniem i "
                "linkiem aktywacyjnym."
            )
            if _should_expose_email_links():
                return render(
                    request,
                    "cars/register.html",
                    {
                        "success": success,
                        "activation_url": activation_url,
                        "email_links_in_response": True,
                    },
                )
            messages.success(request, success)
            return redirect("login")

    return render(
        request,
        "cars/register.html",
        {
            "error": error,
            "success": success,
            "email_links_in_response": _should_expose_email_links(),
        },
    )


def logout_view(request):
    logout(request)
    return redirect("home")
