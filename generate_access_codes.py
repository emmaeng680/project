import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stroke_unit.settings')
django.setup()

from patients.models import Patient

def generate_access_codes():
    patients_without_codes = Patient.objects.filter(access_code__isnull=True)
    print(f"Generating access codes for {patients_without_codes.count()} patients...")
    
    for patient in patients_without_codes:
        patient.access_code = patient.generate_access_code()
        patient.save()
        print(f"Generated code {patient.access_code} for patient {patient.get_full_name()}")
    
    print("Done!")

if __name__ == "__main__":
    generate_access_codes()