"""Prestataire (Contractor) routes"""
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import Response
from datetime import datetime, timezone
from uuid import uuid4
import random
import string
import os
from config import db, get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Get frontend URL from environment
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://app.mykalamaenglish.com')


def generate_prestataire_code():
    """Generate a unique 6-character alphanumeric code for prestataire"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_access_code():
    """Generate a shorter 8-character access code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# Valid services list
VALID_SERVICES = ['informatique', 'communication', 'marketing', 'pedagogique', 'financier']

# ============ PRESTATAIRE REGISTRATION ============

@router.post("/prestataire/register")
async def register_prestataire(data: dict = Body(...)):
    """Register a new prestataire (contractor)"""
    required_fields = ['first_name', 'last_name', 'email', 'phone', 'services']
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Le champ {field} est requis")
    
    # Validate services
    if data['services'] not in VALID_SERVICES:
        raise HTTPException(status_code=400, detail="Service non valide")
    
    # Check if email already exists
    existing = await db.prestataires.find_one({"email": data['email'].lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Un prestataire avec cet email existe déjà")
    
    # Generate codes
    prestataire_code = generate_prestataire_code()
    access_code = generate_access_code()
    
    # Ensure unique prestataire code
    while await db.prestataires.find_one({"prestataire_code": prestataire_code}):
        prestataire_code = generate_prestataire_code()
    
    # Company name is optional - use first_name + last_name if not provided
    company_name = data.get('company_name', '').strip()
    if not company_name:
        company_name = f"{data['first_name']} {data['last_name']}"
    
    prestataire = {
        "id": str(uuid4()),
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "email": data['email'].lower(),
        "phone": data['phone'],
        "company_name": company_name,
        "services": data['services'],
        "prestataire_code": prestataire_code,
        "access_code": access_code,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.prestataires.insert_one(prestataire)
    
    # Send email with access code (using existing email service)
    try:
        from email_service import email_service
        await email_service.send_email(
            to_email=data['email'].lower(),
            subject="Votre code d'accès MyKalamaEnglish",
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #0d9488, #14b8a6); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="margin: 0;">Bienvenue sur MyKalamaEnglish</h1>
                </div>
                <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Bonjour <strong>{data['first_name']} {data['last_name']}</strong>,</p>
                    <p>Votre compte prestataire a été créé avec succès.</p>
                    <div style="background: white; border: 2px solid #0d9488; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center;">
                        <p style="margin: 0 0 10px 0; color: #666;">Votre code d'accès :</p>
                        <p style="font-size: 32px; font-weight: bold; color: #0d9488; margin: 0; letter-spacing: 3px;">{access_code}</p>
                    </div>
                    <div style="background: #e0f2fe; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #0369a1;"><strong>Code prestataire :</strong> {prestataire_code}</p>
                    </div>
                    <p style="color: #666;">Utilisez ce code pour vous connecter et déposer vos factures.</p>
                    <p style="color: #666;">Cordialement,<br>L'équipe MyKalamaEnglish</p>
                </div>
            </body>
            </html>
            """
        )
        logger.info(f"Access code email sent to prestataire: {data['email']}")
    except Exception as e:
        logger.warning(f"Could not send email to prestataire: {e}")
    
    logger.info(f"New prestataire registered: {company_name} ({prestataire_code})")
    
    return {
        "message": "Inscription réussie ! Un code d'accès vous a été envoyé par email.",
        "prestataire_code": prestataire_code,
        "access_code": access_code  # Return for dev/preview - user can use this if email not received
    }


@router.post("/prestataire/login")
async def login_prestataire(data: dict = Body(...)):
    """Login prestataire with access code"""
    access_code = data.get('access_code', '').strip().upper()
    
    if not access_code:
        raise HTTPException(status_code=400, detail="Le code d'accès est requis")
    
    prestataire = await db.prestataires.find_one(
        {"access_code": access_code, "is_active": True},
        {"_id": 0}
    )
    
    if not prestataire:
        raise HTTPException(status_code=401, detail="Code d'accès invalide")
    
    # Mark as verified on first login
    if not prestataire.get('is_verified'):
        await db.prestataires.update_one(
            {"access_code": access_code},
            {"$set": {"is_verified": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    logger.info(f"Prestataire logged in: {prestataire['company_name']}")
    
    return {
        "message": "Connexion réussie",
        "prestataire": {
            "id": prestataire['id'],
            "first_name": prestataire['first_name'],
            "last_name": prestataire['last_name'],
            "email": prestataire['email'],
            "phone": prestataire['phone'],
            "company_name": prestataire['company_name'],
            "services": prestataire['services'],
            "prestataire_code": prestataire['prestataire_code']
        }
    }


# ============ FACTURES (INVOICES) ============

@router.post("/prestataire/facture")
async def submit_facture(data: dict = Body(...)):
    """Prestataire submits an invoice"""
    required_fields = ['prestataire_code', 'amount', 'conception_time']
    for field in required_fields:
        if data.get(field) is None:
            raise HTTPException(status_code=400, detail=f"Le champ {field} est requis")
    
    prestataire_code = data['prestataire_code'].strip().upper()
    
    # Verify prestataire exists
    prestataire = await db.prestataires.find_one(
        {"prestataire_code": prestataire_code, "is_active": True},
        {"_id": 0}
    )
    
    if not prestataire:
        raise HTTPException(status_code=404, detail="Code prestataire invalide")
    
    facture = {
        "id": str(uuid4()),
        "prestataire_id": prestataire['id'],
        "prestataire_code": prestataire_code,
        "company_name": prestataire['company_name'],
        "contact_name": f"{prestataire['first_name']} {prestataire['last_name']}",
        "email": prestataire['email'],
        "phone": prestataire['phone'],
        "services": data.get('services', prestataire['services']),
        "amount": float(data['amount']),
        "conception_time": data['conception_time'],  # e.g., "20 heures"
        "description": data.get('description', ''),
        "status": "pending",  # pending, paid, rejected
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "paid_at": None,
        "paid_by": None
    }
    
    await db.prestataire_factures.insert_one(facture)
    # Remove _id added by insert_one before returning
    facture.pop('_id', None)
    
    # Send email notification to secretary
    try:
        from email_service import email_service
        
        # Find secretary email
        secretary = await db.users.find_one({"role": "secretary"}, {"email": 1})
        secretary_email = secretary['email'] if secretary else None
        
        if secretary_email:
            await email_service.send_email(
                to_email=secretary_email,
                subject=f"🧾 Nouvelle facture prestataire - {prestataire['company_name']}",
                html_content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0;">Nouvelle Facture Prestataire</h1>
                    </div>
                    <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                        <p>Bonjour,</p>
                        <p>Une nouvelle facture a été déposée par un prestataire et nécessite votre validation.</p>
                        
                        <div style="background: white; border: 2px solid #7c3aed; border-radius: 10px; padding: 20px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Prestataire :</td>
                                    <td style="padding: 8px 0; font-weight: bold; text-align: right;">{prestataire['company_name']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Contact :</td>
                                    <td style="padding: 8px 0; text-align: right;">{prestataire['first_name']} {prestataire['last_name']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Service :</td>
                                    <td style="padding: 8px 0; text-align: right;">{facture['services'].upper()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Temps de conception :</td>
                                    <td style="padding: 8px 0; text-align: right;">{facture['conception_time']}</td>
                                </tr>
                                <tr style="border-top: 2px solid #e5e7eb;">
                                    <td style="padding: 12px 0; color: #666; font-weight: bold;">Montant :</td>
                                    <td style="padding: 12px 0; font-size: 24px; font-weight: bold; color: #7c3aed; text-align: right;">{facture['amount']}€</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p style="text-align: center;">
                            <a href="{FRONTEND_URL or 'https://app.mykalamaenglish.com'}/login" 
                               style="display: inline-block; background: #7c3aed; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                                Voir les factures en attente
                            </a>
                        </p>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            Cet email a été envoyé automatiquement. Ne pas répondre directement.
                        </p>
                    </div>
                </body>
                </html>
                """
            )
            logger.info(f"Email notification sent to secretary for facture from {prestataire['company_name']}")
    except Exception as e:
        logger.warning(f"Could not send secretary notification email: {e}")
    
    logger.info(f"New facture submitted by {prestataire['company_name']}: {facture['amount']}€")
    
    return {
        "message": "Facture déposée avec succès",
        "facture_id": facture['id']
    }


@router.get("/prestataire/my-factures/{prestataire_code}")
async def get_prestataire_factures(prestataire_code: str):
    """Get all factures for a prestataire"""
    prestataire_code = prestataire_code.strip().upper()
    
    factures = await db.prestataire_factures.find(
        {"prestataire_code": prestataire_code},
        {"_id": 0}
    ).sort("submitted_at", -1).to_list(100)
    
    return factures


# ============ SECRETARY ROUTES FOR FACTURES ============

@router.get("/secretary/prestataire-factures")
async def get_all_prestataire_factures(current_user: dict = Depends(get_current_user)):
    """Secretary gets all prestataire factures"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    factures = await db.prestataire_factures.find(
        {},
        {"_id": 0}
    ).sort("submitted_at", -1).to_list(200)
    
    return factures


@router.get("/secretary/prestataire/{prestataire_code}")
async def get_prestataire_by_code(prestataire_code: str, current_user: dict = Depends(get_current_user)):
    """Secretary searches prestataire by code"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    prestataire_code = prestataire_code.strip().upper()
    
    prestataire = await db.prestataires.find_one(
        {"prestataire_code": prestataire_code, "is_active": True},
        {"_id": 0, "access_code": 0}
    )
    
    if not prestataire:
        raise HTTPException(status_code=404, detail="Prestataire non trouvé")
    
    # Get pending factures
    factures = await db.prestataire_factures.find(
        {"prestataire_code": prestataire_code, "status": "pending"},
        {"_id": 0}
    ).sort("submitted_at", -1).to_list(50)
    
    return {
        "prestataire": prestataire,
        "pending_factures": factures
    }


@router.post("/secretary/pay-facture/{facture_id}")
async def pay_facture(facture_id: str, current_user: dict = Depends(get_current_user)):
    """Secretary marks a facture as paid"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    facture = await db.prestataire_factures.find_one({"id": facture_id})
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if facture.get('status') == 'paid':
        raise HTTPException(status_code=400, detail="Cette facture a déjà été payée")
    
    await db.prestataire_factures.update_one(
        {"id": facture_id},
        {"$set": {
            "status": "paid",
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "paid_by": current_user['id']
        }}
    )
    
    logger.info(f"Facture {facture_id} paid by {current_user['email']}")
    
    return {"message": "Facture marquée comme payée"}


@router.get("/secretary/all-prestataires")
async def get_all_prestataires(current_user: dict = Depends(get_current_user)):
    """Get all prestataires for secretary"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    prestataires = await db.prestataires.find(
        {"is_active": True},
        {"_id": 0, "access_code": 0}
    ).sort("company_name", 1).to_list(200)
    
    return prestataires


# ============ DOWNLOAD FACTURE PDF ============

@router.get("/prestataire/facture/{facture_id}/download")
async def download_facture_pdf(facture_id: str):
    """Generate and download facture as PDF-like HTML"""
    facture = await db.prestataire_factures.find_one({"id": facture_id}, {"_id": 0})
    
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    # Get service label
    services_labels = {
        'informatique': 'INFORMATIQUE',
        'communication': 'COMMUNICATION',
        'marketing': 'MARKETING',
        'pedagogique': 'PÉDAGOGIQUE',
        'financier': 'FINANCIER'
    }
    service_label = services_labels.get(facture.get('services', ''), facture.get('services', '').upper())
    
    # Format dates
    submitted_date = datetime.fromisoformat(facture['submitted_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y')
    paid_date = ""
    if facture.get('paid_at'):
        paid_date = datetime.fromisoformat(facture['paid_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y')
    
    status_text = "PAYÉE" if facture.get('status') == 'paid' else "EN ATTENTE"
    status_color = "#16a34a" if facture.get('status') == 'paid' else "#ca8a04"
    
    # Generate invoice number
    invoice_number = f"PREST-{facture['id'][:8].upper()}"
    
    # HTML content styled like an invoice
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Facture {invoice_number}</title>
        <style>
            @media print {{
                body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: #f8fafc; 
                padding: 20px;
            }}
            .invoice {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{ 
                background: linear-gradient(135deg, #0d9488, #14b8a6); 
                color: white; 
                padding: 30px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}
            .company-info h1 {{ font-size: 28px; margin-bottom: 8px; }}
            .company-info p {{ opacity: 0.9; font-size: 14px; }}
            .invoice-meta {{ text-align: right; }}
            .invoice-meta h2 {{ font-size: 14px; opacity: 0.8; }}
            .invoice-meta .number {{ font-size: 20px; font-weight: bold; }}
            .status {{ 
                display: inline-block;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-top: 10px;
                background: rgba(255,255,255,0.2);
            }}
            .body {{ padding: 30px; }}
            .parties {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .party {{ flex: 1; }}
            .party h3 {{ 
                font-size: 12px; 
                color: #0d9488; 
                text-transform: uppercase; 
                margin-bottom: 12px;
                letter-spacing: 1px;
            }}
            .party p {{ font-size: 14px; color: #374151; line-height: 1.6; }}
            .party .name {{ font-weight: bold; font-size: 16px; color: #111827; }}
            .details {{ 
                background: #f8fafc; 
                border-radius: 8px; 
                padding: 20px;
                margin-bottom: 30px;
            }}
            .details-row {{ 
                display: flex; 
                justify-content: space-between; 
                padding: 12px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .details-row:last-child {{ border-bottom: none; }}
            .details-row .label {{ color: #6b7280; font-size: 14px; }}
            .details-row .value {{ font-weight: 600; color: #111827; font-size: 14px; }}
            .total-section {{ 
                background: linear-gradient(135deg, #0d9488, #14b8a6);
                border-radius: 8px;
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: white;
            }}
            .total-label {{ font-size: 18px; }}
            .total-amount {{ font-size: 36px; font-weight: bold; }}
            .footer {{ 
                border-top: 1px solid #e5e7eb; 
                padding: 20px 30px;
                text-align: center;
                color: #6b7280;
                font-size: 12px;
            }}
            .print-btn {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #0d9488;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .print-btn:hover {{ background: #0f766e; }}
            @media print {{
                .print-btn {{ display: none; }}
                body {{ padding: 0; background: white; }}
                .invoice {{ box-shadow: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="invoice">
            <div class="header">
                <div class="company-info">
                    <h1>MyKalamaEnglish</h1>
                    <p>Plateforme E-Learning</p>
                    <p>contact@mykalamaenglish.com</p>
                </div>
                <div class="invoice-meta">
                    <h2>FACTURE PRESTATAIRE</h2>
                    <p class="number">{invoice_number}</p>
                    <span class="status" style="background: {status_color};">{status_text}</span>
                </div>
            </div>
            
            <div class="body">
                <div class="parties">
                    <div class="party">
                        <h3>Prestataire</h3>
                        <p class="name">{facture.get('company_name', '')}</p>
                        <p>{facture.get('contact_name', '')}</p>
                        <p>{facture.get('email', '')}</p>
                        <p>{facture.get('phone', '')}</p>
                    </div>
                    <div class="party" style="text-align: right;">
                        <h3>Client</h3>
                        <p class="name">MyKalamaEnglish</p>
                        <p>Formation linguistique</p>
                    </div>
                </div>
                
                <div class="details">
                    <div class="details-row">
                        <span class="label">Service concerné</span>
                        <span class="value">{service_label}</span>
                    </div>
                    <div class="details-row">
                        <span class="label">Temps de conception</span>
                        <span class="value">{facture.get('conception_time', '')}</span>
                    </div>
                    <div class="details-row">
                        <span class="label">Tarif horaire</span>
                        <span class="value">10,00 €</span>
                    </div>
                    <div class="details-row">
                        <span class="label">Date de dépôt</span>
                        <span class="value">{submitted_date}</span>
                    </div>
                    {"<div class='details-row'><span class='label'>Date de paiement</span><span class='value'>" + paid_date + "</span></div>" if paid_date else ""}
                    {("<div class='details-row'><span class='label'>Description</span><span class='value'>" + facture.get('description', '') + "</span></div>") if facture.get('description') else ""}
                </div>
                
                <div class="total-section">
                    <span class="total-label">Montant Total</span>
                    <span class="total-amount">{facture.get('amount', 0):.2f} €</span>
                </div>
            </div>
            
            <div class="footer">
                <p>Facture générée automatiquement par MyKalamaEnglish</p>
                <p>Code Prestataire: {facture.get('prestataire_code', '')}</p>
            </div>
        </div>
        
        <button class="print-btn" onclick="window.print()">🖨️ Imprimer / PDF</button>
    </body>
    </html>
    """
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=facture_{invoice_number}.html"}
    )
