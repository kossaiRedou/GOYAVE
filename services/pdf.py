# services/pdf.py

import os
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from ventes.models import Vente
from fournisseurs.models import CommandeFournisseur

# --------------------------------------------------
#  Emplacements de stockage sous MEDIA_ROOT/factures
# --------------------------------------------------
BASE_FACTURES      = os.path.join(settings.MEDIA_ROOT, 'factures')
FACTURES_VENTES    = os.path.join(BASE_FACTURES, 'factures_achat')
FACTURES_COMMANDES = os.path.join(BASE_FACTURES, 'factures_commandes')

os.makedirs(FACTURES_VENTES, exist_ok=True)
os.makedirs(FACTURES_COMMANDES, exist_ok=True)


def generate_vente_pdf(vente: Vente) -> str:
    """
    Génère la facture PDF d'une vente dans
    MEDIA_ROOT/factures/factures_achat/
    et renvoie son chemin relatif.
    """
    vente.refresh_from_db()
    if vente.facture_pdf and os.path.exists(vente.facture_pdf.path):
        os.remove(vente.facture_pdf.path)

    ts       = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"vente_{vente.pk}_{ts}.pdf"
    path     = os.path.join(FACTURES_VENTES, filename)

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    # En-tête
    c.setFont('Helvetica-Bold', 16)
    c.drawString(20*mm, h-20*mm, f"Facture Vente #{vente.pk}")
    c.setFont('Helvetica', 10)
    c.drawString(20*mm, h-30*mm, f"Client: {vente.client.nom}")
    c.drawString(20*mm, h-35*mm, f"Date: {vente.date.strftime('%d/%m/%Y %H:%M')}")

    # Colonnes
    y = h - 50*mm
    c.setFont('Helvetica-Bold', 9)
    for i, hdr in enumerate(['Produit', 'Quantité', 'PU', 'Total']):
        c.drawString((20 + i*40)*mm, y, hdr)
    c.setFont('Helvetica', 9)
    y -= 5*mm

    # Lignes de vente
    for lg in vente.lignes.all():
        c.drawString(20*mm, y, lg.produit.nom)
        c.drawString(60*mm, y, str(lg.quantite))
        c.drawString(100*mm, y, f"{lg.prix_unitaire}")
        c.drawString(140*mm, y, f"{lg.montant_ligne}")
        y -= 5*mm
        if y < 40*mm:
            c.showPage()
            y = h - 20*mm

    # Paiements
    y -= 10*mm
    c.setFont('Helvetica-Bold', 10)
    c.drawString(20*mm, y, "Paiements")
    y -= 5*mm
    c.setFont('Helvetica', 9)
    total_pay = 0
    for p in vente.paiements.all():
        c.drawString(20*mm, y, f"{p.date_paiement.strftime('%d/%m/%Y %H:%M')} : {p.montant}")
        total_pay += p.montant
        y -= 5*mm
        if y < 30*mm:
            c.showPage()
            y = h - 20*mm

    # Totaux
    y -= 10*mm
    c.setFont('Helvetica-Bold', 11)
    c.drawString(20*mm, y, f"Montant total: {vente.montant_total}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Somme paiements: {total_pay}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Reste dû: {vente.reste_du}")

    c.showPage()
    c.save()

    rel_path = os.path.join('factures', 'factures_achat', filename)
    vente.facture_pdf.name = rel_path
    vente.save(update_fields=['facture_pdf'])
    return rel_path


def generate_commande_pdf(cmd: CommandeFournisseur) -> str:
    """
    Génère le bon de commande fournisseur dans
    MEDIA_ROOT/factures/factures_commandes/
    et renvoie son chemin relatif.
    """
    cmd.refresh_from_db()
    if cmd.facture_pdf and os.path.exists(cmd.facture_pdf.path):
        os.remove(cmd.facture_pdf.path)

    ts       = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"commande_{cmd.pk}_{ts}.pdf"
    path     = os.path.join(FACTURES_COMMANDES, filename)

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    # En-tête
    c.setFont('Helvetica-Bold', 16)
    c.drawString(20*mm, h-20*mm, f"Bon de commande #{cmd.pk}")
    c.setFont('Helvetica', 10)
    c.drawString(20*mm, h-30*mm, f"Fournisseur: {cmd.fournisseur.nom}")
    c.drawString(20*mm, h-35*mm, f"Date: {cmd.date_commande.strftime('%d/%m/%Y %H:%M')}")

    # Colonnes
    y = h - 50*mm
    c.setFont('Helvetica-Bold', 9)
    for i, hdr in enumerate(['Produit', 'Quantité', 'PU achat', 'Total']):
        c.drawString((20 + i*45)*mm, y, hdr)
    c.setFont('Helvetica', 9)
    y -= 5*mm

    # Lignes de commande
    total = 0
    for lg in cmd.lignes.all():
        line = lg.quantite * lg.prix_achat
        c.drawString(20*mm, y, lg.produit.nom)
        c.drawString(65*mm, y, str(lg.quantite))
        c.drawString(110*mm, y, f"{lg.prix_achat}")
        c.drawString(150*mm, y, f"{line}")
        total += line
        y -= 5*mm
        if y < 30*mm:
            c.showPage()
            y = h - 20*mm

    # Total général
    y -= 10*mm
    c.setFont('Helvetica-Bold', 11)
    c.drawString(20*mm, y, f"Montant total: {total}")

    c.showPage()
    c.save()

    rel_path = os.path.join('factures', 'factures_commandes', filename)
    cmd.facture_pdf.name = rel_path
    cmd.save(update_fields=['facture_pdf'])
    return rel_path
