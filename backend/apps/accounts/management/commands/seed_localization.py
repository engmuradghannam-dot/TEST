"""Seed Gulf localization defaults: currencies + tax rules.

Usage: python manage.py seed_localization
"""
from django.core.management.base import BaseCommand

from apps.accounts.fiscal import Currency, TaxRule

CURRENCIES = [
    ('SAR', 'Saudi Riyal', 'ريال سعودي', 'ر.س', 2),
    ('AED', 'UAE Dirham', 'درهم إماراتي', 'د.إ', 2),
    ('KWD', 'Kuwaiti Dinar', 'دينار كويتي', 'د.ك', 3),
    ('QAR', 'Qatari Riyal', 'ريال قطري', 'ر.ق', 2),
    ('BHD', 'Bahraini Dinar', 'دينار بحريني', 'د.ب', 3),
    ('OMR', 'Omani Rial', 'ريال عماني', 'ر.ع', 3),
    ('USD', 'US Dollar', 'دولار أمريكي', '$', 2),
    ('EUR', 'Euro', 'يورو', '€', 2),
    ('JOD', 'Jordanian Dinar', 'دينار أردني', 'د.أ', 3),
    ('EGP', 'Egyptian Pound', 'جنيه مصري', 'ج.م', 2),
]

# (country, tax_type, category, rate)
TAX_RULES = [
    ('SA', 'vat', '', 15),          # KSA standard VAT
    ('SA', 'zero', 'export', 0),    # KSA zero-rated exports
    ('SA', 'exempt', 'financial-services', 0),
    ('SA', 'withholding', 'non-resident-services', 15),
    ('AE', 'vat', '', 5),           # UAE VAT
    ('BH', 'vat', '', 10),          # Bahrain VAT
    ('OM', 'vat', '', 5),           # Oman VAT
    ('KW', 'vat', '', 0),           # Kuwait: no VAT yet
    ('QA', 'vat', '', 0),           # Qatar: no VAT yet
    ('JO', 'vat', '', 16),          # Jordan GST
    ('EG', 'vat', '', 14),          # Egypt VAT
]


class Command(BaseCommand):
    help = 'Seed currencies and country tax rules for Gulf localization'

    def handle(self, *args, **options):
        for code, name, name_ar, symbol, decimals in CURRENCIES:
            Currency.objects.update_or_create(
                code=code, defaults=dict(name=name, name_ar=name_ar,
                                         symbol=symbol, decimals=decimals))
        for country, tax_type, category, rate in TAX_RULES:
            TaxRule.objects.update_or_create(
                company=None, country=country, tax_type=tax_type,
                category=category,
                defaults=dict(rate=rate, is_active=True))
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(CURRENCIES)} currencies, {len(TAX_RULES)} tax rules'))
