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
        "attestation": data.get('attestation', {}),  # Attestation sur l'honneur data
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


@router.put("/secretary/edit-facture/{facture_id}")
async def edit_facture(facture_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Secretary edits a facture (hours/amount)"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    facture = await db.prestataire_factures.find_one({"id": facture_id})
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if facture.get('status') == 'paid':
        raise HTTPException(status_code=400, detail="Impossible de modifier une facture déjà payée")
    
    if facture.get('status') == 'rejected':
        raise HTTPException(status_code=400, detail="Impossible de modifier une facture refusée")
    
    update_data = {
        "modified_at": datetime.now(timezone.utc).isoformat(),
        "modified_by": current_user['id']
    }
    
    # Store original values if first modification
    if not facture.get('original_amount'):
        update_data['original_amount'] = facture.get('amount')
        update_data['original_conception_time'] = facture.get('conception_time')
    
    if 'amount' in data:
        update_data['amount'] = float(data['amount'])
    
    if 'conception_time' in data:
        update_data['conception_time'] = data['conception_time']
    
    if 'modification_reason' in data:
        update_data['modification_reason'] = data['modification_reason']
    
    await db.prestataire_factures.update_one(
        {"id": facture_id},
        {"$set": update_data}
    )
    
    logger.info(f"Facture {facture_id} modified by {current_user['email']}: {update_data}")
    
    return {"message": "Facture modifiée avec succès"}


@router.post("/secretary/reject-facture/{facture_id}")
async def reject_facture(facture_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Secretary rejects a facture"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    facture = await db.prestataire_factures.find_one({"id": facture_id})
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if facture.get('status') == 'paid':
        raise HTTPException(status_code=400, detail="Impossible de refuser une facture déjà payée")
    
    rejection_reason = data.get('reason', 'Aucun motif fourni')
    
    await db.prestataire_factures.update_one(
        {"id": facture_id},
        {"$set": {
            "status": "rejected",
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "rejected_by": current_user['id'],
            "rejection_reason": rejection_reason
        }}
    )
    
    # Send email notification to prestataire
    try:
        from email_service import email_service
        prestataire = await db.prestataires.find_one({"prestataire_code": facture['prestataire_code']})
        if prestataire:
            await email_service.send_email(
                to_email=prestataire['email'],
                subject="❌ Facture refusée - MyKalamaEnglish",
                html_content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0;">Facture Refusée</h1>
                    </div>
                    <div style="background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px;">
                        <p>Bonjour <strong>{prestataire['first_name']}</strong>,</p>
                        <p>Votre facture d'un montant de <strong>{facture['amount']}€</strong> a été refusée.</p>
                        
                        <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; color: #dc2626;"><strong>Motif du refus :</strong></p>
                            <p style="margin: 10px 0 0 0; color: #7f1d1d;">{rejection_reason}</p>
                        </div>
                        
                        <p>Vous pouvez soumettre une nouvelle facture en tenant compte de cette remarque.</p>
                        <p style="color: #666;">Cordialement,<br>L'équipe MyKalamaEnglish</p>
                    </div>
                </body>
                </html>
                """
            )
    except Exception as e:
        logger.warning(f"Could not send rejection email: {e}")
    
    logger.info(f"Facture {facture_id} rejected by {current_user['email']}: {rejection_reason}")
    
    return {"message": "Facture refusée"}


@router.put("/secretary/prestataire/{prestataire_code}")
async def update_prestataire(prestataire_code: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update a prestataire's information"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    prestataire = await db.prestataires.find_one({"prestataire_code": prestataire_code})
    if not prestataire:
        raise HTTPException(status_code=404, detail="Prestataire non trouvé")
    
    update_data = {}
    if 'first_name' in data:
        update_data['first_name'] = data['first_name']
    if 'last_name' in data:
        update_data['last_name'] = data['last_name']
    if 'email' in data:
        update_data['email'] = data['email']
    if 'phone' in data:
        update_data['phone'] = data['phone']
    if 'company_name' in data:
        update_data['company_name'] = data['company_name']
    if 'services' in data:
        update_data['services'] = data['services']
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.prestataires.update_one(
        {"prestataire_code": prestataire_code},
        {"$set": update_data}
    )
    
    logger.info(f"Prestataire {prestataire_code} updated by {current_user['email']}")
    
    return {"message": "Prestataire modifié avec succès"}


@router.delete("/secretary/prestataire/{prestataire_code}")
async def delete_prestataire(prestataire_code: str, current_user: dict = Depends(get_current_user)):
    """Delete a prestataire and all their invoices"""
    if current_user['role'] not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    prestataire = await db.prestataires.find_one({"prestataire_code": prestataire_code})
    if not prestataire:
        raise HTTPException(status_code=404, detail="Prestataire non trouvé")
    
    # Delete all invoices
    await db.prestataire_factures.delete_many({"prestataire_code": prestataire_code})
    
    # Delete prestataire
    await db.prestataires.delete_one({"prestataire_code": prestataire_code})
    
    logger.info(f"Prestataire {prestataire_code} and invoices deleted by {current_user['email']}")
    
    return {"message": "Prestataire et factures supprimés"}


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
    """Generate and download facture as PDF-like HTML with premium design"""
    facture = await db.prestataire_factures.find_one({"id": facture_id}, {"_id": 0})
    
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    # Get service label and icon
    services_config = {
        'informatique': {'label': 'INFORMATIQUE', 'icon': '💻', 'color': '#3b82f6'},
        'communication': {'label': 'COMMUNICATION', 'icon': '📢', 'color': '#8b5cf6'},
        'marketing': {'label': 'MARKETING', 'icon': '📊', 'color': '#ec4899'},
        'pedagogique': {'label': 'PÉDAGOGIQUE', 'icon': '📚', 'color': '#10b981'},
        'financier': {'label': 'FINANCIER', 'icon': '💰', 'color': '#f59e0b'}
    }
    service_info = services_config.get(facture.get('services', ''), {'label': 'SERVICE', 'icon': '🔧', 'color': '#6b7280'})
    
    # Format dates
    submitted_date = datetime.fromisoformat(facture['submitted_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y à %H:%M')
    paid_date = ""
    rejected_date = ""
    modified_date = ""
    
    if facture.get('paid_at'):
        paid_date = datetime.fromisoformat(facture['paid_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y à %H:%M')
    if facture.get('rejected_at'):
        rejected_date = datetime.fromisoformat(facture['rejected_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y à %H:%M')
    if facture.get('modified_at'):
        modified_date = datetime.fromisoformat(facture['modified_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y à %H:%M')
    
    # Status configuration
    status = facture.get('status', 'pending')
    status_config = {
        'paid': {'text': 'PAYÉE', 'color': '#16a34a', 'bg': '#dcfce7', 'icon': '✓'},
        'pending': {'text': 'EN ATTENTE', 'color': '#ca8a04', 'bg': '#fef9c3', 'icon': '⏳'},
        'rejected': {'text': 'REFUSÉE', 'color': '#dc2626', 'bg': '#fee2e2', 'icon': '✗'}
    }
    status_info = status_config.get(status, status_config['pending'])
    
    # Generate invoice number
    invoice_number = f"PREST-{facture['id'][:8].upper()}"
    
    # Check if modified
    was_modified = facture.get('original_amount') is not None
    modification_note = ""
    if was_modified:
        orig_amount = facture.get('original_amount', 0)
        orig_time = facture.get('original_conception_time', '')
        reason = facture.get('modification_reason', 'Non spécifié')
        modification_note = f"""
        <div class="modification-alert">
            <div class="alert-icon">⚠️</div>
            <div class="alert-content">
                <strong>Facture modifiée par le secrétariat</strong>
                <p>Montant initial : {orig_amount:.2f}€ | Temps initial : {orig_time}</p>
                <p>Motif : {reason}</p>
                <p class="alert-date">Modifiée le {modified_date}</p>
            </div>
        </div>
        """
    
    # Rejection note
    rejection_note = ""
    if status == 'rejected':
        rejection_note = f"""
        <div class="rejection-alert">
            <div class="alert-icon">❌</div>
            <div class="alert-content">
                <strong>Facture refusée</strong>
                <p>Motif : {facture.get('rejection_reason', 'Non spécifié')}</p>
                <p class="alert-date">Refusée le {rejected_date}</p>
            </div>
        </div>
        """
    
    # HTML content with premium design
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Facture {invoice_number}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            @media print {{
                body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                .no-print {{ display: none !important; }}
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .invoice-container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            .invoice {{ 
                background: white; 
                border-radius: 24px;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
                overflow: hidden;
            }}
            
            /* Header */
            .header {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                padding: 40px;
                position: relative;
                overflow: hidden;
            }}
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -20%;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                border-radius: 50%;
            }}
            .header-content {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                position: relative;
                z-index: 1;
            }}
            .brand {{
                color: white;
            }}
            .brand h1 {{
                font-size: 32px;
                font-weight: 700;
                letter-spacing: -0.5px;
                margin-bottom: 8px;
            }}
            .brand p {{
                opacity: 0.7;
                font-size: 14px;
            }}
            .invoice-info {{
                text-align: right;
                color: white;
            }}
            .invoice-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 2px;
                opacity: 0.6;
                margin-bottom: 4px;
            }}
            .invoice-number {{
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 12px;
            }}
            .status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 16px;
                border-radius: 50px;
                font-size: 12px;
                font-weight: 600;
                background: {status_info['bg']};
                color: {status_info['color']};
            }}
            
            /* Service Banner */
            .service-banner {{
                background: linear-gradient(135deg, {service_info['color']}15 0%, {service_info['color']}05 100%);
                border-left: 4px solid {service_info['color']};
                padding: 20px 30px;
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            .service-icon {{
                width: 50px;
                height: 50px;
                background: {service_info['color']};
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }}
            .service-info h3 {{
                font-size: 18px;
                color: #1e293b;
                margin-bottom: 4px;
            }}
            .service-info p {{
                font-size: 13px;
                color: #64748b;
            }}
            
            /* Body */
            .body {{
                padding: 40px;
            }}
            
            /* Parties */
            .parties {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 40px;
                margin-bottom: 40px;
            }}
            .party-card {{
                padding: 24px;
                border-radius: 16px;
                background: #f8fafc;
            }}
            .party-card.prestataire {{
                border: 2px solid #e2e8f0;
            }}
            .party-card.client {{
                background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
                color: white;
            }}
            .party-label {{
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
                opacity: 0.6;
                margin-bottom: 12px;
            }}
            .party-name {{
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .party-details {{
                font-size: 14px;
                line-height: 1.8;
                opacity: 0.8;
            }}
            
            /* Alerts */
            .modification-alert, .rejection-alert {{
                display: flex;
                gap: 15px;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
            }}
            .modification-alert {{
                background: #fef3c7;
                border: 1px solid #fcd34d;
            }}
            .rejection-alert {{
                background: #fee2e2;
                border: 1px solid #fca5a5;
            }}
            .alert-icon {{
                font-size: 24px;
            }}
            .alert-content {{
                flex: 1;
            }}
            .alert-content strong {{
                display: block;
                margin-bottom: 8px;
                color: #1e293b;
            }}
            .alert-content p {{
                font-size: 13px;
                color: #64748b;
                margin-bottom: 4px;
            }}
            .alert-date {{
                font-size: 12px;
                color: #94a3b8;
            }}
            
            /* Details Table */
            .details-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            .details-table th {{
                text-align: left;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #64748b;
                padding: 12px 16px;
                background: #f1f5f9;
                border-radius: 8px 8px 0 0;
            }}
            .details-table td {{
                padding: 16px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 15px;
            }}
            .details-table tr:last-child td {{
                border-bottom: none;
            }}
            .details-table .label {{
                color: #64748b;
            }}
            .details-table .value {{
                font-weight: 600;
                color: #1e293b;
                text-align: right;
            }}
            
            /* Total */
            .total-section {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 16px;
                padding: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: white;
                position: relative;
                overflow: hidden;
            }}
            .total-section::before {{
                content: '€';
                position: absolute;
                right: 30px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 150px;
                font-weight: 700;
                opacity: 0.05;
            }}
            .total-label {{
                font-size: 14px;
                opacity: 0.7;
                margin-bottom: 4px;
            }}
            .total-title {{
                font-size: 20px;
                font-weight: 600;
            }}
            .total-amount {{
                font-size: 48px;
                font-weight: 700;
                position: relative;
                z-index: 1;
            }}
            
            /* Footer */
            .footer {{
                background: #f8fafc;
                padding: 24px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: #64748b;
            }}
            .footer-brand {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .footer-brand img {{
                width: 24px;
                height: 24px;
            }}
            
            /* Print Button */
            .print-actions {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                display: flex;
                gap: 10px;
            }}
            .print-btn {{
                background: white;
                color: #1e293b;
                border: none;
                padding: 14px 28px;
                border-radius: 12px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s;
            }}
            .print-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 15px 30px rgba(0,0,0,0.25);
            }}
            .print-btn.primary {{
                background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
                color: white;
            }}
            
            @media print {{
                body {{ background: white; padding: 0; }}
                .invoice {{ box-shadow: none; border-radius: 0; }}
                .print-actions {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="invoice-container">
            <div class="invoice">
                <!-- Header -->
                <div class="header">
                    <div class="header-content">
                        <div class="brand">
                            <h1>MyKalamaEnglish</h1>
                            <p>Plateforme E-Learning</p>
                            <p>contact@mykalamaenglish.com</p>
                        </div>
                        <div class="invoice-info">
                            <div class="invoice-label">Facture Prestataire</div>
                            <div class="invoice-number">{invoice_number}</div>
                            <div class="status-badge">
                                <span>{status_info['icon']}</span>
                                <span>{status_info['text']}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Service Banner -->
                <div class="service-banner">
                    <div class="service-icon">{service_info['icon']}</div>
                    <div class="service-info">
                        <h3>Service {service_info['label']}</h3>
                        <p>Prestation de service - {facture.get('conception_time', '')}</p>
                    </div>
                </div>
                
                <!-- Body -->
                <div class="body">
                    {rejection_note}
                    {modification_note}
                    
                    <!-- Parties -->
                    <div class="parties">
                        <div class="party-card prestataire">
                            <div class="party-label">Prestataire</div>
                            <div class="party-name">{facture.get('company_name', '')}</div>
                            <div class="party-details">
                                {facture.get('contact_name', '')}<br>
                                {facture.get('email', '')}<br>
                                {facture.get('phone', '')}
                            </div>
                        </div>
                        <div class="party-card client">
                            <div class="party-label">Client</div>
                            <div class="party-name">MyKalamaEnglish</div>
                            <div class="party-details">
                                Formation linguistique<br>
                                Plateforme E-Learning
                            </div>
                        </div>
                    </div>
                    
                    <!-- Details -->
                    <table class="details-table">
                        <tr>
                            <th colspan="2">Détails de la prestation</th>
                        </tr>
                        <tr>
                            <td class="label">Temps de conception</td>
                            <td class="value">{facture.get('conception_time', '')}</td>
                        </tr>
                        <tr>
                            <td class="label">Tarif horaire</td>
                            <td class="value">10,00 €</td>
                        </tr>
                        <tr>
                            <td class="label">Date de dépôt</td>
                            <td class="value">{submitted_date}</td>
                        </tr>
                        {"<tr><td class='label'>Date de paiement</td><td class='value'>" + paid_date + "</td></tr>" if paid_date else ""}
                        {("<tr><td class='label'>Description</td><td class='value'>" + facture.get('description', '') + "</td></tr>") if facture.get('description') else ""}
                    </table>
                    
                    <!-- Total -->
                    <div class="total-section">
                        <div>
                            <div class="total-label">Montant à payer</div>
                            <div class="total-title">Total TTC</div>
                        </div>
                        <div class="total-amount">{facture.get('amount', 0):.2f} €</div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="footer">
                    <div class="footer-brand">
                        <span>📄</span>
                        <span>Document généré automatiquement</span>
                    </div>
                    <div>Code Prestataire: <strong>{facture.get('prestataire_code', '')}</strong></div>
                </div>
            </div>
        </div>
        
        <!-- Print Actions -->
        <div class="print-actions no-print">
            <button class="print-btn" onclick="window.history.back()">← Retour</button>
            <button class="print-btn primary" onclick="window.print()">🖨️ Imprimer / PDF</button>
        </div>
    </body>
    </html>
    """
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=facture_{invoice_number}.html"}
    )
