"""Onboarding API views: 4-step self-service wizard."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .onboarding import service


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            result = service.register(
                company_name=request.data['company_name'],
                admin_email=request.data['admin_email'],
                admin_password=request.data['admin_password'],
                country=request.data.get('country', 'SA'),
                vat_number=request.data.get('vat_number', ''),
            )
            return Response(result, status=201)
        except (KeyError, ValueError) as exc:
            return Response({'error': str(exc)}, status=400)


class SetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'error': 'no company linked to user'}, status=400)
        return Response(service.setup(company, request.data.get('options', {})))


class ImportDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'error': 'no company'}, status=400)
        entity = request.data.get('entity', 'items')
        csv_text = request.data.get('csv', '')
        return Response(service.import_csv(company, csv_text, entity))


class OnboardingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'error': 'no company'}, status=400)
        return Response(service.status(company))


class ZATCAView(APIView):
    """Quick ZATCA clearance/reporting endpoint for sales invoices."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.selling.zatca import ZATCAInvoice, ZATCAInvoiceLine, get_client
        from datetime import date
        from decimal import Decimal
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'error': 'no company'}, status=400)

        data = request.data
        invoice = ZATCAInvoice(
            invoice_number=data.get('invoice_number', 'INV-001'),
            issue_date=date.fromisoformat(data.get('date', date.today().isoformat())),
            seller_name=company.name,
            seller_vat=company.tax_id or '',
            seller_address=getattr(company, 'address', ''),
            buyer_name=data.get('buyer_name', ''),
            buyer_vat=data.get('buyer_vat'),
            invoice_type=data.get('invoice_type', 'simplified'),
        )
        for line in data.get('lines', []):
            invoice.lines.append(ZATCAInvoiceLine(
                description=line.get('description', ''),
                quantity=Decimal(str(line.get('quantity', 1))),
                unit_price=Decimal(str(line.get('unit_price', 0))),
                vat_rate=Decimal(str(line.get('vat_rate', 15))),
            ))
        client = get_client(company)
        if invoice.invoice_type == 'standard':
            result = client.clear_invoice(invoice)
        else:
            result = client.report_invoice(invoice)
        return Response(result)
