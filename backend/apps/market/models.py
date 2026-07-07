"""Market Readiness Models — certifications, partner ecosystem, localization.

Covers:
  CertificationRecord — SOC2, ISO 27001, ISO 9001, GDPR compliance status
  Partner            — Implementation partners, consultants, developers
  MarketplaceApp     — ISV apps (extends plugins) with licensing
  CountryLocalization — Per-country taxes, accounting rules, regulation links

These are admin/management models — not tenant-scoped (they're global config).
"""
from django.db import models
from django.utils import timezone


# ── Certifications ────────────────────────────────────────────────
class CertificationRecord(models.Model):
    CERTS = [
        ('SOC2_TYPE1', 'SOC 2 Type I'),
        ('SOC2_TYPE2', 'SOC 2 Type II'),
        ('ISO27001', 'ISO 27001'),
        ('ISO9001', 'ISO 9001'),
        ('ISO27701', 'ISO 27701 (Privacy)'),
        ('GDPR', 'GDPR Compliance'),
        ('PCI_DSS', 'PCI DSS'),
        ('HIPAA', 'HIPAA'),
        ('ZATCA', 'ZATCA Phase 2'),
        ('NCA_ECC', 'NCA Essential Controls'),
        ('NCA_CSCC', 'NCA Cloud Controls'),
    ]
    STATUS = [('in_progress','In Progress'),('achieved','Achieved'),
              ('renewal','Renewal Due'),('expired','Expired')]

    certification = models.CharField(max_length=20, choices=CERTS, unique=True)
    status = models.CharField(max_length=15, choices=STATUS, default='in_progress')
    achieved_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    auditor = models.CharField(max_length=200, blank=True)
    certificate_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    last_assessment = models.DateField(null=True, blank=True)
    controls_passed = models.PositiveIntegerField(default=0)
    controls_total = models.PositiveIntegerField(default=0)

    @property
    def completion_pct(self):
        return round(self.controls_passed / self.controls_total * 100
                     ) if self.controls_total else 0

    @property
    def is_current(self):
        if self.status != 'achieved':
            return False
        if self.expiry_date and self.expiry_date < timezone.localdate():
            return False
        return True

    def __str__(self):
        return f"{self.get_certification_display()} [{self.status}]"


class ComplianceControl(models.Model):
    """Individual control mapping: framework requirement -> evidence."""
    certification = models.ForeignKey(CertificationRecord,
                                      on_delete=models.CASCADE,
                                      related_name='controls')
    control_id = models.CharField(max_length=30)   # e.g. "CC6.1", "A.9.1"
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, default='not_started',
                              choices=[('not_started','Not Started'),
                                       ('in_progress','In Progress'),
                                       ('implemented','Implemented'),
                                       ('verified','Verified')])
    evidence_path = models.CharField(max_length=500, blank=True,
                                     help_text='URL or path to evidence artifact')
    automated = models.BooleanField(default=False,
                                    help_text='Can evidence be auto-collected?')
    automation_query = models.TextField(blank=True,
                                        help_text='Django ORM path or audit event type')

    def __str__(self):
        return f"{self.certification.certification}/{self.control_id}"


# ── Partner Ecosystem ─────────────────────────────────────────────
class Partner(models.Model):
    TIERS = [('platinum','Platinum'),('gold','Gold'),
             ('silver','Silver'),('registered','Registered')]
    TYPES = [('implementation','Implementation'),
             ('consulting','Consulting'),
             ('isv','ISV / Developer'),
             ('reseller','Reseller'),
             ('training','Training')]

    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, choices=TYPES)
    tier = models.CharField(max_length=15, choices=TIERS, default='registered')
    country = models.CharField(max_length=2)   # ISO 3166-1
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    specializations = models.JSONField(default=list,
                                       help_text='["manufacturing","hr","vat"]')
    certifications = models.JSONField(default=list)
    active_deployments = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    logo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} [{self.tier}]"


class MarketplaceApp(models.Model):
    """ISV app listed in the marketplace (extends Plugin model)."""
    PRICING = [('free','Free'),('freemium','Freemium'),
               ('subscription','Subscription'),('one_time','One-time')]

    plugin_slug = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    description_ar = models.TextField(blank=True)
    developer = models.ForeignKey(Partner, on_delete=models.SET_NULL,
                                  null=True, blank=True)
    category = models.CharField(max_length=50)
    pricing_model = models.CharField(max_length=15, choices=PRICING, default='free')
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installs = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    review_count = models.PositiveIntegerField(default=0)
    screenshots = models.JSONField(default=list)
    verified = models.BooleanField(default=False,
                                   help_text='Security-reviewed by Nexus team')
    listed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ── Localization Registry ─────────────────────────────────────────
class CountryLocalization(models.Model):
    """Per-country ERP localization: taxes, accounting rules, regulations."""
    country = models.CharField(max_length=2, unique=True)
    country_name = models.CharField(max_length=100)
    country_name_ar = models.CharField(max_length=100, blank=True)

    # Tax configuration
    primary_tax_type = models.CharField(max_length=20, default='vat',
                                        choices=[('vat','VAT'),('gst','GST'),
                                                 ('sales_tax','Sales Tax'),
                                                 ('none','None')])
    standard_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_registration_threshold = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text='Annual revenue threshold for mandatory registration')
    e_invoicing_required = models.BooleanField(default=False)
    e_invoicing_standard = models.CharField(max_length=50, blank=True,
                                             help_text='e.g. ZATCA, MyInvois, FatturaPA')

    # Accounting rules
    fiscal_year_start_month = models.PositiveSmallIntegerField(default=1)
    accounting_standard = models.CharField(
        max_length=20, default='IFRS',
        choices=[('IFRS','IFRS'),('GAAP','US GAAP'),('LOCAL','Local GAAP')])
    requires_chart_of_accounts = models.BooleanField(default=False,
        help_text='Government-mandated COA format')
    official_coa_url = models.URLField(blank=True)

    # Payroll & labor
    social_insurance_employer_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Employer social insurance / pension contribution %')
    social_insurance_employee_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    payroll_frequency = models.CharField(max_length=20, default='monthly',
                                          choices=[('weekly','Weekly'),
                                                   ('biweekly','Biweekly'),
                                                   ('monthly','Monthly')])

    # Regulations & references
    regulatory_body = models.CharField(max_length=200, blank=True)
    key_regulations = models.JSONField(default=list,
                                       help_text='[{"name":"VAT Law","url":"..."}]')
    localization_notes = models.TextField(blank=True)
    supported = models.BooleanField(default=True)
    last_reviewed = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.country} — {self.country_name}"

    class Meta:
        ordering = ['country_name']
        verbose_name = 'Country Localization'
