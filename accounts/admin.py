from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TechnicianProfile, NeurologistProfile, PatientProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone_number')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(TechnicianProfile)
admin.site.register(NeurologistProfile)
admin.site.register(PatientProfile)