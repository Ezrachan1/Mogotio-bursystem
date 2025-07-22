from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime
from bursary.models import AcademicYear, Institution


class Command(BaseCommand):
    help = 'Seed initial data for the bursary system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial data...')
        
        # Create academic year
        academic_year, created = AcademicYear.objects.get_or_create(
            year='2024/2025',
            defaults={
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 12, 31),
                'application_deadline': timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59)),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created academic year: {academic_year.year}'))
        
        # Create some sample institutions
        institutions_data = [
            # Universities
            {'name': 'University of Nairobi', 'institution_type': 'university', 'county': 'Nairobi'},
            {'name': 'Kenyatta University', 'institution_type': 'university', 'county': 'Kiambu'},
            {'name': 'Moi University', 'institution_type': 'university', 'county': 'Uasin Gishu'},
            {'name': 'JKUAT', 'institution_type': 'university', 'county': 'Kiambu'},
            {'name': 'Egerton University', 'institution_type': 'university', 'county': 'Nakuru'},
            
            # TVET
            {'name': 'Kenya Polytechnic', 'institution_type': 'tvet', 'county': 'Nairobi'},
            {'name': 'Kisumu Polytechnic', 'institution_type': 'tvet', 'county': 'Kisumu'},
            {'name': 'Mombasa Polytechnic', 'institution_type': 'tvet', 'county': 'Mombasa'},
            
            # Secondary Schools
            {'name': 'Alliance High School', 'institution_type': 'secondary', 'county': 'Kiambu'},
            {'name': 'Kenya High School', 'institution_type': 'secondary', 'county': 'Nairobi'},
            {'name': 'Mangu High School', 'institution_type': 'secondary', 'county': 'Kiambu'},
            {'name': 'Starehe Boys Centre', 'institution_type': 'secondary', 'county': 'Nairobi'},
            
            # Primary Schools
            {'name': 'Olympic Primary School', 'institution_type': 'primary', 'county': 'Nairobi'},
            {'name': 'Hospital Hill Primary School', 'institution_type': 'primary', 'county': 'Nairobi'},
        ]
        
        for inst_data in institutions_data:
            institution, created = Institution.objects.get_or_create(
                name=inst_data['name'],
                county=inst_data['county'],
                defaults={
                    'institution_type': inst_data['institution_type'],
                    'address': f"{inst_data['name']}, {inst_data['county']} County",
                    'is_verified': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created institution: {institution.name}'))
        
        self.stdout.write(self.style.SUCCESS('Initial data seeding completed!'))