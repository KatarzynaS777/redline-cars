from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from .models import Car, Favorite


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthPagesTests(TestCase):
    def test_home_contains_login_link(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("login"))

    def test_register_creates_inactive_user_and_sends_activation_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "tester",
                "email": "tester@example.com",
                "password": "MocneHaslo123!",
                "confirm_password": "MocneHaslo123!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="tester")
        self.assertEqual(user.email, "tester@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("tester@example.com", mail.outbox[0].to)
        self.assertIn("/activate/", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertIn("Aktywuj konto", mail.outbox[0].alternatives[0][0])

    def test_activation_link_activates_and_logs_in_user(self):
        user = User.objects.create_user(
            username="inactive-driver",
            email="inactive@example.com",
            password="Sekret123!",
            is_active=False,
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.get(
            reverse("activate_account", kwargs={"uidb64": uidb64, "token": token})
        )

        self.assertRedirects(response, f"{reverse('add_car')}?next=%2F")
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_magic_login_redirects_new_user_to_add_car(self):
        user = User.objects.create_user(
            username="mail-driver",
            email="mail-driver@example.com",
            password="Sekret123!",
            is_active=True,
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.get(
            reverse("magic_login_verify", kwargs={"uidb64": uidb64, "token": token})
        )

        self.assertRedirects(response, f"{reverse('add_car')}?next=%2F")

    def test_email_login_request_sends_magic_link(self):
        User.objects.create_user(
            username="driver",
            email="driver@example.com",
            password="Sekret123!",
            is_active=True,
        )

        response = self.client.post(
            reverse("email_login_request"),
            {"email": "driver@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("driver@example.com", mail.outbox[0].to)
        self.assertIn("/login/email/", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        self.assertIn("Zaloguj przez e-mail", mail.outbox[0].alternatives[0][0])


class CatalogFiltersTests(TestCase):
    def create_car(self, **overrides):
        data = {
            "created_by": None,
            "brand": "BMW",
            "model": "320i",
            "year": 2021,
            "price": 120000,
            "image_path": "",
            "engine": "2.0",
            "power": 184,
            "fuel_type": "petrol",
            "drive": "RWD",
            "gearbox": "automatic",
            "consumption": 6.8,
            "acceleration": 7.1,
            "max_speed": 235,
            "doors": 4,
            "seats": 5,
            "trunk_capacity": 480,
            "weight": 1530,
            "length": 4700,
            "color": "black",
            "battery_kwh": None,
            "range_km": None,
            "fuel_tank": 58,
            "range_petrol": 700,
            "cylinders": 4,
            "co2_emission": 0,
            "segment": "D",
            "body_type": "sedan",
            "cost_per_100km": 0,
            "yearly_cost": 0,
            "abs_system": True,
            "esp_system": True,
            "airbags": 6,
            "heated_seats": False,
            "ventilated_seats": False,
            "leather_seats": False,
            "sunroof": False,
            "panoramic_roof": False,
            "touchscreen": False,
            "navigation": False,
            "bluetooth": True,
            "parking_sensors": False,
            "parking_camera": False,
            "automatic_parking": False,
            "cruise_control": False,
            "adaptive_cruise": False,
            "lane_assist": False,
            "blind_spot_monitor": False,
            "keyless_entry": False,
            "push_start": False,
            "air_conditioning": True,
            "dual_zone_climate": False,
            "heated_steering_wheel": False,
            "ambient_lighting": False,
        }
        data.update(overrides)
        return Car.objects.create(**data)

    def test_catalog_filters_by_multiple_fields(self):
        self.create_car(
            brand="BMW",
            model="330d",
            price=180000,
            power=286,
            fuel_type="diesel",
            drive="AWD",
            body_type="sedan",
            segment="D",
            year=2022,
        )
        self.create_car(
            brand="Audi",
            model="A4",
            price=95000,
            power=150,
            fuel_type="petrol",
            drive="FWD",
            body_type="sedan",
            segment="C",
            year=2019,
        )

        response = self.client.get(
            reverse("car_list"),
            {
                "brand": "BMW",
                "drive": "AWD",
                "min_price": 150000,
                "body_type": "sedan",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BMW 330d")
        self.assertNotContains(response, "Audi A4")

    def test_catalog_sort_by_price_desc(self):
        self.create_car(brand="Tesla", model="Model 3", price=210000)
        self.create_car(brand="Audi", model="A4", price=110000)

        response = self.client.get(reverse("car_list"), {"sort": "price_desc"})

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertLess(content.index("Tesla Model 3"), content.index("Audi A4"))

    def test_toggle_favorite_adds_car_to_session(self):
        car = self.create_car(brand="Tesla", model="Model 3")

        response = self.client.post(
            reverse("toggle_favorite", kwargs={"car_id": car.id}),
            {"next": reverse("car_list")},
        )

        self.assertRedirects(response, reverse("car_list"))
        session = self.client.session
        self.assertIn(car.id, session["favorite_car_ids"])

    def test_favorites_view_shows_only_favorite_cars(self):
        favorite_car = self.create_car(brand="Tesla", model="Model 3")
        regular_car = self.create_car(brand="Audi", model="A4")

        session = self.client.session
        session["favorite_car_ids"] = [favorite_car.id]
        session.save()

        response = self.client.get(reverse("favorites"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tesla Model 3")
        self.assertNotContains(response, "Audi A4")

    def test_authenticated_favorites_persist_after_relogin(self):
        user = User.objects.create_user(
            username="favorite-user",
            email="favorite@example.com",
            password="Sekret123!",
            is_active=True,
        )
        car = self.create_car(brand="Tesla", model="Model 3")
        self.create_car(
            brand="My",
            model="Garage",
            price=10000,
            power=90,
            fuel_type="petrol",
            drive="FWD",
            created_by=user,
        )

        self.client.force_login(user)
        response = self.client.post(
            reverse("toggle_favorite", kwargs={"car_id": car.id}),
            {"next": reverse("car_list")},
        )

        self.assertRedirects(response, reverse("car_list"))
        self.assertTrue(Favorite.objects.filter(user=user, car=car).exists())

        self.client.logout()
        self.client.force_login(user)
        response = self.client.get(reverse("favorites"))

        self.assertContains(response, "Tesla Model 3")


class UserGarageFlowTests(TestCase):
    def create_car(self, **overrides):
        data = {
            "created_by": None,
            "brand": "Audi",
            "model": "A4",
            "year": 2020,
            "price": 90000,
            "image_path": "",
            "engine": "2.0",
            "power": 150,
            "fuel_type": "petrol",
            "drive": "FWD",
            "gearbox": "automatic",
            "consumption": 6.5,
            "acceleration": 8.2,
            "max_speed": 220,
            "doors": 4,
            "seats": 5,
            "trunk_capacity": 460,
            "weight": 1450,
            "length": 4700,
            "color": "white",
            "battery_kwh": None,
            "range_km": None,
            "fuel_tank": 54,
            "range_petrol": 680,
            "cylinders": 4,
            "co2_emission": 0,
            "segment": "D",
            "body_type": "sedan",
            "cost_per_100km": 0,
            "yearly_cost": 0,
            "abs_system": True,
            "esp_system": True,
            "airbags": 6,
            "heated_seats": False,
            "ventilated_seats": False,
            "leather_seats": False,
            "sunroof": False,
            "panoramic_roof": False,
            "touchscreen": False,
            "navigation": False,
            "bluetooth": True,
            "parking_sensors": False,
            "parking_camera": False,
            "automatic_parking": False,
            "cruise_control": False,
            "adaptive_cruise": False,
            "lane_assist": False,
            "blind_spot_monitor": False,
            "keyless_entry": False,
            "push_start": False,
            "air_conditioning": True,
            "dual_zone_climate": False,
            "heated_steering_wheel": False,
            "ambient_lighting": False,
        }
        data.update(overrides)
        return Car.objects.create(**data)

    def test_authenticated_user_without_car_is_redirected_to_add_car(self):
        user = User.objects.create_user(
            username="garage-user",
            email="garage@example.com",
            password="Sekret123!",
            is_active=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, f"{reverse('add_car')}?next=%2F")

    def test_add_car_creates_user_owned_car_and_redirects_to_next_page(self):
        user = User.objects.create_user(
            username="submitter",
            email="submitter@example.com",
            password="Sekret123!",
            is_active=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("add_car"),
            {
                "next": reverse("car_list"),
                "brand": "Tesla",
                "model": "Model 3",
                "year": 2023,
                "price": 189000,
                "engine": "Electric",
                "power": 283,
                "fuel_type": "electric",
                "drive": "RWD",
                "gearbox": "automatic",
                "consumption": 15.4,
                "segment": "D",
                "body_type": "sedan",
                "color": "blue",
                "image_path": "Tesla3.jpg",
            },
        )

        self.assertRedirects(response, reverse("car_list"))
        self.assertTrue(
            Car.objects.filter(
                created_by=user,
                brand="Tesla",
                model="Model 3",
            ).exists()
        )

    def test_user_with_own_car_can_open_home(self):
        user = User.objects.create_user(
            username="complete-user",
            email="complete@example.com",
            password="Sekret123!",
            is_active=True,
        )
        self.create_car(created_by=user, brand="BMW", model="330i")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

    def test_compare_view_keeps_selected_order_and_renders_vs_layout(self):
        user = User.objects.create_user(
            username="compare-user",
            email="compare@example.com",
            password="Sekret123!",
            is_active=True,
        )
        self.create_car(created_by=user, brand="Garage", model="Owner")
        first = self.create_car(brand="Audi", model="A4", power=204, acceleration=7.1)
        second = self.create_car(brand="BMW", model="330i", power=245, acceleration=5.9)
        self.client.force_login(user)

        response = self.client.post(
            reverse("compare"),
            {"cars": [str(second.id), str(first.id)]},
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertContains(response, "VS")
        self.assertLess(content.index("BMW 330i"), content.index("Audi A4"))

    def test_compare_view_shows_message_when_selection_is_not_two_cars(self):
        user = User.objects.create_user(
            username="compare-empty",
            email="compare-empty@example.com",
            password="Sekret123!",
            is_active=True,
        )
        self.create_car(created_by=user, brand="Garage", model="Owner")
        car = self.create_car(brand="Audi", model="A4")
        self.client.force_login(user)

        response = self.client.post(
            reverse("compare"),
            {"cars": [str(car.id)]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wybierz dokladnie dwa auta do porownania.")
