"""Prestataire (Contractor) routes"""
from fastapi import APIRouter, HTTPException, Body, Depends
from datetime import datetime, timezone
from uuid import uuid4
import random
import string
from config import db, get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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
