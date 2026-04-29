from django import forms
from django.contrib import admin

from .models import Car, Favorite


class CarAdminForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = "__all__"


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    form = CarAdminForm
    list_display = ("brand", "model", "year", "fuel_type", "drive", "price", "created_by")
    list_filter = ("fuel_type", "drive", "segment", "body_type", "created_by")
    search_fields = ("brand", "model", "created_by__username", "created_by__email")
    fieldsets = (
        ("Podstawowe informacje", {
            "fields": (
                "created_by",
                "brand",
                "model",
                "year",
                "price",
                "color",
                "image_path",
                "uploaded_image",
            ),
        }),
        ("Silnik i naped", {
            "fields": ("engine", "power", "fuel_type", "drive", "gearbox", "consumption"),
        }),
        ("Osiagi", {
            "fields": ("acceleration", "max_speed"),
        }),
        ("Wymiary i nadwozie", {
            "fields": ("doors", "seats", "trunk_capacity", "weight", "length"),
        }),
        ("Napedy elektryczne", {
            "fields": ("battery_kwh", "range_km"),
        }),
        ("Napedy spalinowe", {
            "fields": ("fuel_tank", "range_petrol", "cylinders"),
        }),
        ("Ekologia", {
            "fields": ("co2_emission",),
        }),
        ("Klasyfikacja", {
            "fields": ("segment", "body_type"),
        }),
        ("Koszty", {
            "fields": ("cost_per_100km", "yearly_cost"),
        }),
        ("Bezpieczenstwo", {
            "fields": ("abs_system", "esp_system", "airbags"),
        }),
        ("Wyposazenie - komfort", {
            "fields": (
                "air_conditioning",
                "dual_zone_climate",
                "heated_seats",
                "ventilated_seats",
                "leather_seats",
                "heated_steering_wheel",
                "ambient_lighting",
            ),
        }),
        ("Wyposazenie - multimedia", {
            "fields": ("touchscreen", "navigation", "bluetooth"),
        }),
        ("Wyposazenie - parkowanie", {
            "fields": ("parking_sensors", "parking_camera", "automatic_parking"),
        }),
        ("Wyposazenie - jazda", {
            "fields": ("cruise_control", "adaptive_cruise"),
        }),
        ("Wyposazenie - asystenci", {
            "fields": ("lane_assist", "blind_spot_monitor"),
        }),
        ("Wyposazenie - dodatki", {
            "fields": ("sunroof", "panoramic_roof", "keyless_entry", "push_start"),
        }),
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "car", "created_at")
    search_fields = ("user__username", "car__brand", "car__model")
