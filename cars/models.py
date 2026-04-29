from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models


class Car(models.Model):
    IMAGE_CHOICES = [
        ("cars/hero-2.jpg", "Domyślny RedLine"),
        ("cars/Tesla3.jpg", "Tesla Model 3"),
        ("cars/lexus.jpg", "Lexus"),
        ("cars/COROLLA.jpg", "Toyota Corolla"),
        ("cars/bmw-3.jpg", "BMW Seria 3"),
        ("cars/bmw-3B.jpg", "BMW Seria 3 - granatowe"),
        ("cars/audi-a4.jpg", "Audi A4"),
        ("cars/AudiA3.jpg", "Audi A3"),
        ("cars/hero-1.jpg", "RedLine Hero 1"),
        ("cars/hero.jpg", "RedLine Hero"),
    ]
    IMAGE_PATHS = {path for path, _label in IMAGE_CHOICES}
    EQUIPMENT_LABELS = {
        "air_conditioning": "Klimatyzacja",
        "dual_zone_climate": "Klimatyzacja dwustrefowa",
        "heated_seats": "Podgrzewane fotele",
        "ventilated_seats": "Wentylowane fotele",
        "leather_seats": "Skórzana tapicerka",
        "heated_steering_wheel": "Podgrzewana kierownica",
        "ambient_lighting": "Oświetlenie ambientowe",
        "sunroof": "Szyberdach",
        "panoramic_roof": "Dach panoramiczny",
        "touchscreen": "Ekran dotykowy",
        "navigation": "Nawigacja",
        "bluetooth": "Bluetooth",
        "parking_sensors": "Czujniki parkowania",
        "parking_camera": "Kamera cofania",
        "automatic_parking": "Asystent parkowania",
        "cruise_control": "Tempomat",
        "adaptive_cruise": "Tempomat adaptacyjny",
        "lane_assist": "Asystent pasa ruchu",
        "blind_spot_monitor": "Monitor martwego pola",
        "keyless_entry": "Dostęp bezkluczykowy",
        "push_start": "Odpalanie przyciskiem",
    }

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_cars",
        verbose_name="Dodane przez",
    )
    brand = models.CharField(max_length=100, verbose_name="Marka")
    model = models.CharField(max_length=100, verbose_name="Model")
    year = models.IntegerField(verbose_name="Rocznik")
    price = models.IntegerField(verbose_name="Cena")
    image_path = models.CharField(
        max_length=255,
        blank=True,
        help_text="Wybierz jedno z gotowych zdjęć z aplikacji.",
        verbose_name="Gotowe zdjęcie",
    )
    uploaded_image = models.ImageField(
        upload_to="car_uploads/",
        blank=True,
        null=True,
        verbose_name="Własne zdjęcie",
    )

    engine = models.CharField(max_length=50, verbose_name="Silnik")
    power = models.IntegerField(verbose_name="Moc")

    FUEL_CHOICES = [
        ("electric", "Elektryczny"),
        ("petrol", "Benzyna"),
        ("diesel", "Diesel"),
        ("hybrid", "Hybryda"),
    ]
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, verbose_name="Paliwo")

    DRIVE_CHOICES = [
        ("FWD", "Przedni"),
        ("RWD", "Tylny"),
        ("AWD", "4x4"),
    ]
    drive = models.CharField(max_length=10, choices=DRIVE_CHOICES, verbose_name="Napęd")

    gearbox = models.CharField(max_length=50, default="manual", verbose_name="Skrzynia biegów")
    consumption = models.FloatField(verbose_name="Spalanie / zużycie")

    acceleration = models.FloatField(default=10, verbose_name="Przyspieszenie 0-100")
    max_speed = models.IntegerField(default=200, verbose_name="Prędkość maksymalna")

    doors = models.IntegerField(default=4, verbose_name="Liczba drzwi")
    seats = models.IntegerField(default=5, verbose_name="Liczba miejsc")
    trunk_capacity = models.IntegerField(default=400, verbose_name="Pojemność bagażnika")
    weight = models.IntegerField(default=1500, verbose_name="Masa")
    length = models.IntegerField(default=4500, verbose_name="Długość")
    color = models.CharField(max_length=50, default="black", verbose_name="Kolor")

    battery_kwh = models.FloatField(null=True, blank=True, verbose_name="Bateria kWh")
    range_km = models.IntegerField(null=True, blank=True, verbose_name="Zasięg km")

    fuel_tank = models.IntegerField(default=50, verbose_name="Bak")
    range_petrol = models.IntegerField(default=600, verbose_name="Zasięg spalinowy")
    cylinders = models.IntegerField(default=4, verbose_name="Liczba cylindrów")

    co2_emission = models.IntegerField(default=0, verbose_name="Emisja CO2")

    SEGMENT_CHOICES = [
        ("A", "Miejskie"),
        ("B", "Kompaktowe"),
        ("C", "Średnie"),
        ("D", "Premium"),
        ("SUV", "SUV"),
    ]
    segment = models.CharField(max_length=10, choices=SEGMENT_CHOICES, default="C", verbose_name="Segment")

    BODY_CHOICES = [
        ("sedan", "Sedan"),
        ("hatchback", "Hatchback"),
        ("suv", "SUV"),
        ("wagon", "Kombi"),
    ]
    body_type = models.CharField(max_length=20, choices=BODY_CHOICES, default="sedan", verbose_name="Nadwozie")

    cost_per_100km = models.FloatField(default=0, verbose_name="Koszt 100 km")
    yearly_cost = models.IntegerField(default=0, verbose_name="Koszt roczny")

    abs_system = models.BooleanField(default=True, verbose_name="System ABS")
    esp_system = models.BooleanField(default=True, verbose_name="System ESP")
    airbags = models.IntegerField(default=6, verbose_name="Liczba poduszek")

    heated_seats = models.BooleanField(default=False, verbose_name="Podgrzewane fotele")
    ventilated_seats = models.BooleanField(default=False, verbose_name="Wentylowane fotele")
    leather_seats = models.BooleanField(default=False, verbose_name="Skórzana tapicerka")
    sunroof = models.BooleanField(default=False, verbose_name="Szyberdach")
    panoramic_roof = models.BooleanField(default=False, verbose_name="Dach panoramiczny")
    touchscreen = models.BooleanField(default=False, verbose_name="Ekran dotykowy")
    navigation = models.BooleanField(default=False, verbose_name="Nawigacja")
    bluetooth = models.BooleanField(default=False, verbose_name="Bluetooth")
    parking_sensors = models.BooleanField(default=False, verbose_name="Czujniki parkowania")
    parking_camera = models.BooleanField(default=False, verbose_name="Kamera cofania")
    automatic_parking = models.BooleanField(default=False, verbose_name="Asystent parkowania")
    cruise_control = models.BooleanField(default=False, verbose_name="Tempomat")
    adaptive_cruise = models.BooleanField(default=False, verbose_name="Tempomat adaptacyjny")
    lane_assist = models.BooleanField(default=False, verbose_name="Asystent pasa ruchu")
    blind_spot_monitor = models.BooleanField(default=False, verbose_name="Monitor martwego pola")
    keyless_entry = models.BooleanField(default=False, verbose_name="Dostęp bezkluczykowy")
    push_start = models.BooleanField(default=False, verbose_name="Odpalanie przyciskiem")
    air_conditioning = models.BooleanField(default=True, verbose_name="Klimatyzacja")
    dual_zone_climate = models.BooleanField(default=False, verbose_name="Klimatyzacja dwustrefowa")
    heated_steering_wheel = models.BooleanField(default=False, verbose_name="Podgrzewana kierownica")
    ambient_lighting = models.BooleanField(default=False, verbose_name="Oświetlenie ambientowe")

    @property
    def resolved_image_path(self):
        if not self.image_path:
            return "cars/hero-2.jpg"

        candidate = self.image_path.replace("\\", "/")
        if "/" not in candidate:
            candidate = f"cars/{candidate}"

        if candidate in self.IMAGE_PATHS:
            return candidate
        return "cars/hero-2.jpg"

    @property
    def display_image_url(self):
        if self.uploaded_image:
            try:
                return self.uploaded_image.url
            except ValueError:
                pass
        return staticfiles_storage.url(self.resolved_image_path)

    @property
    def equipment_labels(self):
        return [
            label
            for field_name, label in self.EQUIPMENT_LABELS.items()
            if getattr(self, field_name, False)
        ]

    @property
    def featured_equipment_labels(self):
        return self.equipment_labels[:6]

    def __str__(self):
        return f"{self.brand} {self.model}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_cars",
        verbose_name="Użytkownik",
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Samochód",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "car"),
                name="unique_user_car_favorite",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.car}"
