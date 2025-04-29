from django.contrib import admin
from .models import Settings, Brand, Ad

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('hourly_rate',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'daily_budget', 'monthly_budget')

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'brand', 'start_time', 'end_time')
    list_filter = ('brand',)
    search_fields = ('name',)