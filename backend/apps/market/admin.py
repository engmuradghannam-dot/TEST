from django.contrib import admin
from .models import CertificationRecord, ComplianceControl, Partner, MarketplaceApp, CountryLocalization

@admin.register(CertificationRecord)
class CertAdmin(admin.ModelAdmin):
    list_display = ('certification','status','achieved_date','expiry_date','completion_pct','is_current')
    list_filter = ('status','certification')

class ControlInline(admin.TabularInline):
    model = ComplianceControl; extra = 0

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name','type','tier','country','active_deployments','rating','is_active')
    list_filter = ('type','tier','country')

@admin.register(MarketplaceApp)
class MktAppAdmin(admin.ModelAdmin):
    list_display = ('name','category','pricing_model','installs','rating','verified','is_active')
    list_filter = ('category','pricing_model','verified')

@admin.register(CountryLocalization)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('country','country_name','primary_tax_type','standard_tax_rate','e_invoicing_required','supported')
    list_filter = ('primary_tax_type','accounting_standard','supported')
