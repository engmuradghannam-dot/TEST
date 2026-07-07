"""Seed: country localizations + initial certifications.
python manage.py seed_market
"""
from django.core.management.base import BaseCommand
from apps.market.models import CountryLocalization, CertificationRecord

COUNTRIES = [
    ('SA','Saudi Arabia','المملكة العربية السعودية','vat',15,375000,True,'ZATCA',1,'IFRS',12,2),
    ('AE','UAE','الإمارات العربية المتحدة','vat',5,375000,True,'UAE FTA',1,'IFRS',5,3.75),
    ('KW','Kuwait','الكويت','none',0,None,False,'',1,'IFRS',10.5,0),
    ('QA','Qatar','قطر','none',0,None,False,'',1,'IFRS',0,0),
    ('BH','Bahrain','البحرين','vat',10,37500,True,'NBR',1,'IFRS',7,0),
    ('OM','Oman','عُمان','vat',5,38500,True,'OTA',1,'IFRS',10.5,0),
    ('JO','Jordan','الأردن','vat',16,30000,False,'',1,'IFRS',14.25,7.5),
    ('EG','Egypt','مصر','vat',14,500000,False,'',7,'IFRS',27,11),
    ('GB','United Kingdom','المملكة المتحدة','vat',20,85000,True,'HMRC MTD',4,'IFRS',13.8,8),
    ('US','United States','الولايات المتحدة','sales_tax',0,None,False,'',1,'GAAP',6.2,1.45),
]
CERTS = [
    ('SOC2_TYPE2',265,100),('ISO27001',93,150),('ISO9001',60,80),
    ('GDPR',99,200),('ZATCA',12,12),('NCA_ECC',60,114),
]

class Command(BaseCommand):
    help = 'Seed country localizations and certifications'
    def handle(self, *a, **kw):
        for cc,cn,cnar,tax_type,rate,thresh,einv,einv_std,fy_month,std,ei_pct,ee_pct in COUNTRIES:
            CountryLocalization.objects.update_or_create(country=cc, defaults=dict(
                country_name=cn,country_name_ar=cnar,primary_tax_type=tax_type,
                standard_tax_rate=rate,tax_registration_threshold=thresh,
                e_invoicing_required=einv,e_invoicing_standard=einv_std,
                fiscal_year_start_month=fy_month,accounting_standard=std,
                social_insurance_employer_pct=ei_pct,social_insurance_employee_pct=ee_pct))
        for cert,passed,total in CERTS:
            CertificationRecord.objects.get_or_create(certification=cert, defaults=dict(
                status='in_progress',controls_passed=passed,controls_total=total))
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(COUNTRIES)} countries, {len(CERTS)} certs'))
