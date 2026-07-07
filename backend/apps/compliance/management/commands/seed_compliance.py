"""Seed compliance frameworks + a starter set of automated controls."""
from django.core.management.base import BaseCommand

from apps.compliance.models import ComplianceFramework, ComplianceControl

FRAMEWORKS = [
    ('soc2', 'SOC 2 Type II', '2017 TSC'),
    ('iso27001', 'ISO/IEC 27001', '2022'),
    ('iso9001', 'ISO 9001', '2015'),
    ('gdpr', 'GDPR', '2016/679'),
]

CONTROLS = {
    'soc2': [
        ('CC6.1', 'Logical access controls',
         'apps.compliance.automation.check_zero_trust_enabled'),
        ('CC6.7', 'Encryption / key management',
         'apps.compliance.automation.check_encryption_at_rest'),
        ('CC7.2', 'Audit trail integrity',
         'apps.compliance.automation.check_immutable_audit'),
    ],
    'iso27001': [
        ('A.8.15', 'Logging',
         'apps.compliance.automation.check_immutable_audit'),
        ('A.5.15', 'Access control',
         'apps.compliance.automation.check_zero_trust_enabled'),
    ],
    'gdpr': [
        ('Art.32', 'Security of processing',
         'apps.compliance.automation.check_encryption_at_rest'),
    ],
    'iso9001': [('7.5', 'Documented information', '')],
}


class Command(BaseCommand):
    help = 'Seed compliance frameworks and automated controls'

    def handle(self, *args, **options):
        for code, name, version in FRAMEWORKS:
            fw, _ = ComplianceFramework.objects.update_or_create(
                code=code, defaults={'name': name, 'version': version})
            for cid, title, check in CONTROLS.get(code, []):
                ComplianceControl.objects.update_or_create(
                    framework=fw, control_id=cid,
                    defaults={'title': title, 'automated_check': check})
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(FRAMEWORKS)} frameworks'))
