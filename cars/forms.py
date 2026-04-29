from django import forms

from .models import Car


class UserCarForm(forms.ModelForm):
    BASIC_FIELDS = (
        "brand",
        "model",
        "year",
        "price",
        "engine",
        "power",
        "fuel_type",
        "drive",
        "gearbox",
        "consumption",
        "segment",
        "body_type",
        "color",
        "image_path",
        "uploaded_image",
    )
    SAFETY_FIELDS = (
        "abs_system",
        "esp_system",
        "airbags",
    )
    EQUIPMENT_FIELDS = (
        "air_conditioning",
        "dual_zone_climate",
        "heated_seats",
        "ventilated_seats",
        "leather_seats",
        "heated_steering_wheel",
        "ambient_lighting",
        "sunroof",
        "panoramic_roof",
        "touchscreen",
        "navigation",
        "bluetooth",
        "parking_sensors",
        "parking_camera",
        "automatic_parking",
        "cruise_control",
        "adaptive_cruise",
        "lane_assist",
        "blind_spot_monitor",
        "keyless_entry",
        "push_start",
    )
    ALL_FIELDS = BASIC_FIELDS + SAFETY_FIELDS + EQUIPMENT_FIELDS

    class Meta:
        model = Car
        fields = (
            "brand",
            "model",
            "year",
            "price",
            "engine",
            "power",
            "fuel_type",
            "drive",
            "gearbox",
            "consumption",
            "segment",
            "body_type",
            "color",
            "image_path",
            "uploaded_image",
            "abs_system",
            "esp_system",
            "airbags",
            "air_conditioning",
            "dual_zone_climate",
            "heated_seats",
            "ventilated_seats",
            "leather_seats",
            "heated_steering_wheel",
            "ambient_lighting",
            "sunroof",
            "panoramic_roof",
            "touchscreen",
            "navigation",
            "bluetooth",
            "parking_sensors",
            "parking_camera",
            "automatic_parking",
            "cruise_control",
            "adaptive_cruise",
            "lane_assist",
            "blind_spot_monitor",
            "keyless_entry",
            "push_start",
        )
        labels = {
            "brand": "Marka",
            "model": "Model",
            "year": "Rocznik",
            "price": "Szacowana cena",
            "engine": "Silnik",
            "power": "Moc (KM)",
            "fuel_type": "Paliwo",
            "drive": "Napęd",
            "gearbox": "Skrzynia",
            "consumption": "Spalanie / zużycie",
            "segment": "Segment",
            "body_type": "Nadwozie",
            "color": "Kolor",
            "image_path": "Gotowe zdjęcie",
            "uploaded_image": "Własne zdjęcie JPG/PNG",
            "abs_system": "System ABS",
            "esp_system": "System ESP",
            "airbags": "Liczba poduszek",
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
        help_texts = {
            "image_path": "Możesz wybrać jedno z gotowych zdjęć dostępnych w aplikacji.",
            "uploaded_image": "Albo wgraj własny plik JPG lub PNG. Własne zdjęcie ma pierwszeństwo przed gotowym.",
        }
        widgets = {
            "brand": forms.TextInput(attrs={"placeholder": "np. BMW"}),
            "model": forms.TextInput(attrs={"placeholder": "np. 320i"}),
            "year": forms.NumberInput(attrs={"min": 1900, "max": 2100}),
            "price": forms.NumberInput(attrs={"min": 0, "step": 1000}),
            "engine": forms.TextInput(attrs={"placeholder": "np. 2.0 Turbo"}),
            "power": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "gearbox": forms.TextInput(attrs={"placeholder": "np. automat"}),
            "consumption": forms.NumberInput(attrs={"min": 0, "step": 0.1}),
            "airbags": forms.NumberInput(attrs={"min": 0, "step": 1}),
            "color": forms.TextInput(attrs={"placeholder": "np. czarny"}),
            "image_path": forms.Select(choices=(("", "Domyślne zdjęcie"), *Car.IMAGE_CHOICES)),
            "uploaded_image": forms.ClearableFileInput(
                attrs={"accept": ".jpg,.jpeg,.png,image/jpeg,image/png"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image_path"].required = False
        self.fields["uploaded_image"].required = False
        for field_name in ("abs_system", "esp_system"):
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs.update({"class": "equipment-checkbox"})
        for field_name in self.EQUIPMENT_FIELDS:
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs.update({"class": "equipment-checkbox"})

    def clean_year(self):
        year = self.cleaned_data["year"]
        if year < 1950 or year > 2100:
            raise forms.ValidationError("Podaj poprawny rocznik.")
        return year

    def clean_power(self):
        power = self.cleaned_data["power"]
        if power <= 0:
            raise forms.ValidationError("Moc musi być większa od zera.")
        return power

    def clean_consumption(self):
        consumption = self.cleaned_data["consumption"]
        if consumption <= 0:
            raise forms.ValidationError("Podaj dodatnią wartość zużycia.")
        return consumption

    def clean_uploaded_image(self):
        uploaded_image = self.cleaned_data.get("uploaded_image")
        if not uploaded_image:
            return uploaded_image

        allowed_extensions = (".jpg", ".jpeg", ".png")
        allowed_types = {"image/jpeg", "image/png"}
        lower_name = uploaded_image.name.lower()

        if not lower_name.endswith(allowed_extensions):
            raise forms.ValidationError("Dodaj zdjęcie w formacie JPG, JPEG albo PNG.")

        content_type = getattr(uploaded_image, "content_type", "")
        if content_type and content_type not in allowed_types:
            raise forms.ValidationError("Dozwolone są tylko pliki JPG, JPEG albo PNG.")

        if uploaded_image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Zdjęcie jest za duże. Maksymalny rozmiar to 5 MB.")

        return uploaded_image
