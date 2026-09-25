from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from cleaners.models import Cleaner


class Command(BaseCommand):
    help = "Seed the database with realistic cleaner profiles for demo and matching flows."

    def handle(self, *args, **options):
        User = get_user_model()

        cleaners = [
            {"first_name": "Amarachi", "last_name": "Okafor", "gender": "female", "phone": "+2348030001001", "address": "20 Nnebisi Road, Asaba"},
            {"first_name": "Chinedu", "last_name": "Eze", "gender": "male", "phone": "+2348030001002", "address": "5 Okpanam Road, Asaba"},
            {"first_name": "Blessing", "last_name": "Nwosu", "gender": "female", "phone": "+2348030001003", "address": "9 Nnewi Street, Onitsha"},
            {"first_name": "Emeka", "last_name": "Agu", "gender": "male", "phone": "+2348030001004", "address": "11 Summit Avenue, Warri"},
            {"first_name": "Mariam", "last_name": "Sani", "gender": "female", "phone": "+2348030001005", "address": "3 Wuse Zone 5, Abuja"},
            {"first_name": "Tobi", "last_name": "Adebayo", "gender": "male", "phone": "+2348030001006", "address": "7 Ikoyi Crescent, Lagos"},
            {"first_name": "Grace", "last_name": "Ike", "gender": "female", "phone": "+2348030001007", "address": "18 Oron Road, Uyo"},
            {"first_name": "Kelechi", "last_name": "Opara", "gender": "male", "phone": "+2348030001008", "address": "22 Airport Road, Port Harcourt"},
            {"first_name": "Ifeoma", "last_name": "Akan", "gender": "female", "phone": "+2348030001009", "address": "14 GRA, Enugu"},
            {"first_name": "Samuel", "last_name": "Dike", "gender": "male", "phone": "+2348030001010", "address": "4 Lakeview Estate, Ibadan"},
            {"first_name": "Oluwaseun", "last_name": "Bello", "gender": "female", "phone": "+2348030001011", "address": "33 Lekki Phase 1, Lagos"},
            {"first_name": "Peter", "last_name": "Odoh", "gender": "male", "phone": "+2348030001012", "address": "2 Bende Road, Umuahia"},
            {"first_name": "Rita", "last_name": "Umeh", "gender": "female", "phone": "+2348030001013", "address": "8 Obiagu Layout, Enugu"},
            {"first_name": "Victor", "last_name": "Ezeh", "gender": "male", "phone": "+2348030001014", "address": "10 Aba Road, Port Harcourt"},
            {"first_name": "Adaeze", "last_name": "Mba", "gender": "female", "phone": "+2348030001015", "address": "15 Osondu Street, Awka"},
        ]

        created = 0
        for index, item in enumerate(cleaners, start=1):
            username = f"cleaner{index:02d}"
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "role": User.Role.CLEANER,
                    "phone_number": item["phone"],
                    "phone_verified": True,
                    "is_active": True,
                },
            )

            if user_created:
                user.set_password("Password123!")
                user.save()
            else:
                user.first_name = item["first_name"]
                user.last_name = item["last_name"]
                user.role = User.Role.CLEANER
                user.phone_number = item["phone"]
                user.phone_verified = True
                user.is_active = True
                user.save()

            profile, profile_created = Cleaner.objects.get_or_create(
                user=user,
                defaults={
                    "gender": item["gender"],
                    "is_active": True,
                    "rating": Decimal(str(4.2 + (index % 6) * 0.1)),
                    "completed_jobs": 5 + index,
                },
            )

            if not profile_created:
                profile.gender = item["gender"]
                profile.is_active = True
                profile.rating = Decimal(str(4.2 + (index % 6) * 0.1))
                profile.completed_jobs = 5 + index
                profile.save()

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} cleaner profiles."))
