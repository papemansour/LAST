"""
Monday.com CRM Integration - MyKalama English
Gestion des étudiants, professeurs, prestataires et factures
"""
import os
import requests
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Configuration depuis les variables d'environnement
MONDAY_API_KEY = os.environ.get("MONDAY_API_KEY", "")
MONDAY_API_URL = "https://api.monday.com/v2"

# Board IDs depuis les variables d'environnement
MONDAY_BOARD_STUDENTS = os.environ.get("MONDAY_BOARD_STUDENTS", "5089020316")

# Column IDs pour le board étudiants
STUDENT_COLUMNS = {
    "name": "name",  # Prénom (colonne principale)
    "last_name": "text_mkyn39my",  # Nom
    "email": "contact_email",
    "phone": "contact_phone",
    "level": "status",  # Niveau
    "password": "text_mkyr55gy",  # Mot de passe
    "digika": "text_mkyr9db5",  # Digika
    "comments": "long_text4"  # Commentaires
}

# Mapping des niveaux
LEVEL_MAPPING = {
    'beginner': 'K-Débutant',
    'intermediate': 'K-Intermédiaire', 
    'advanced': 'K-Professionnel',
    'professional': 'K-Professionnel',
    'kkid': 'K-Kids'
}

LEVEL_MAPPING_FR = {
    'beginner': 'débutant',
    'intermediate': 'intermédiaire', 
    'advanced': 'avancé',
    'professional': 'professionnel',
    'kkid': 'K-Kids (3-9 ans)'
}


def _make_monday_request(query: str, variables: Dict = None) -> Optional[Dict]:
    """Effectuer une requête à l'API Monday.com"""
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(
            MONDAY_API_URL,
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Monday.com API error: {str(e)}")
        return None


def create_monday_item(student_data: Dict[str, Any]) -> Optional[str]:
    """
    Créer un item dans Monday.com pour un nouvel étudiant approuvé
    Inclut le mot de passe et Digika
    """
    
    item_name = student_data.get('first_name', '')
    level_label = LEVEL_MAPPING.get(student_data.get('level', 'beginner'), 'K-Débutant')
    
    # Construire les valeurs des colonnes
    column_values = {
        STUDENT_COLUMNS["last_name"]: student_data.get('last_name', ''),
        STUDENT_COLUMNS["email"]: {
            "email": student_data.get('email', ''), 
            "text": student_data.get('email', '')
        },
        STUDENT_COLUMNS["phone"]: {
            "phone": student_data.get('phone', ''), 
            "countryShortName": "SN"
        },
        STUDENT_COLUMNS["level"]: {"label": level_label},
        STUDENT_COLUMNS["password"]: student_data.get('temporary_password', ''),
        STUDENT_COLUMNS["digika"]: student_data.get('digika_password', 'DIGIKA2025'),
    }
    
    query = """
    mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
      create_item (
        board_id: $boardId,
        item_name: $itemName,
        column_values: $columnValues
      ) {
        id
        name
      }
    }
    """
    
    variables = {
        "boardId": MONDAY_BOARD_STUDENTS,
        "itemName": item_name,
        "columnValues": json.dumps(column_values)
    }
    
    result = _make_monday_request(query, variables)
    
    if result and 'data' in result and result['data'].get('create_item'):
        item_id = result['data']['create_item']['id']
        logger.info(f"Monday.com student created: {item_id} for {item_name}")
        return item_id
    else:
        logger.error(f"Monday.com error: {result.get('errors', 'Unknown error') if result else 'No response'}")
        return None


def generate_welcome_email_html(student_data: Dict[str, Any]) -> str:
    """Générer le HTML de l'email de bienvenue"""
    
    first_name = student_data.get('first_name', '')
    last_name = student_data.get('last_name', '')
    email = student_data.get('email', '')
    password = student_data.get('temporary_password', '')
    digika = student_data.get('digika_password', 'DIGIKA2025')
    level = LEVEL_MAPPING_FR.get(student_data.get('level', 'beginner'), 'débutant')
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #333; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 650px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #2dd4bf 100%); padding: 40px 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
        .header .subtitle {{ color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 10px; }}
        .content {{ padding: 40px 30px; }}
        .greeting {{ font-size: 22px; color: #0d9488; margin-bottom: 20px; }}
        .feature-box {{ background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%); border-left: 4px solid #0d9488; padding: 20px; margin: 25px 0; border-radius: 0 10px 10px 0; }}
        .feature {{ display: flex; align-items: flex-start; margin: 15px 0; }}
        .feature-icon {{ font-size: 20px; margin-right: 12px; }}
        .credentials-box {{ background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 25px; margin: 30px 0; }}
        .credentials-title {{ font-size: 18px; font-weight: bold; color: #92400e; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        .credential {{ margin: 12px 0; padding: 10px 15px; background: white; border-radius: 8px; display: flex; align-items: center; gap: 10px; }}
        .credential-label {{ color: #666; min-width: 150px; }}
        .credential-value {{ font-weight: bold; color: #1f2937; font-family: 'Courier New', monospace; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%); color: white; padding: 18px 40px; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 16px; margin: 25px 0; box-shadow: 0 4px 15px rgba(13,148,136,0.4); }}
        .cta-button:hover {{ background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%); }}
        .footer {{ background: #1f2937; color: white; padding: 30px; text-align: center; }}
        .footer p {{ margin: 5px 0; }}
        .footer .team {{ font-size: 18px; font-weight: bold; color: #2dd4bf; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Hello and Welcome to MyKalama!</h1>
            <div class="subtitle">Votre aventure linguistique commence maintenant</div>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {first_name} {last_name.upper()} ! 👋</div>
            
            <p>Nous sommes ravis de vous accueillir sur <strong>MYKALAMA</strong> ! Vous vous êtes inscrit avec succès à notre cours en ligne de niveau <strong>{level}</strong>, et nous sommes impatients de vous accompagner dans votre apprentissage de la langue.</p>
            
            <div class="feature-box">
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <div><strong>Leçons interactives :</strong> un contenu engageant adapté à votre niveau pour vous aider à approfondir vos connaissances en anglais.</div>
                </div>
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <div><strong>Apprentissage flexible :</strong> accédez à vos cours à tout moment, partout, à votre propre rythme.</div>
                </div>
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <div><strong>Communauté de soutien :</strong> rejoignez notre communauté dynamique d'apprenants et d'instructeurs qui sont là pour vous aider à réussir.</div>
                </div>
            </div>
            
            <div class="credentials-box">
                <div class="credentials-title">🔐 Vos identifiants de connexion</div>
                <div class="credential">
                    <span class="credential-label">📧 Email :</span>
                    <span class="credential-value">{email}</span>
                </div>
                <div class="credential">
                    <span class="credential-label">🔑 Mot de passe provisoire :</span>
                    <span class="credential-value">{password}</span>
                </div>
                <div class="credential">
                    <span class="credential-label">📚 Digika (Kalamathèque) :</span>
                    <span class="credential-value">{digika}</span>
                </div>
            </div>
            
            <p style="text-align: center; font-size: 14px; color: #666;">
                <em>Digika est votre mot de passe pour accéder à Kalamathèque, notre bibliothèque en ligne disponible depuis votre espace.</em>
            </p>
            
            <div style="text-align: center;">
                <a href="https://mykalamaenglish.com" class="cta-button">
                    🚀 Connectez-vous maintenant
                </a>
            </div>
            
            <p>Nous vous souhaitons une expérience d'apprentissage enrichissante et agréable !</p>
        </div>
        
        <div class="footer">
            <p>Cordialement,</p>
            <p class="team">L'équipe MYKALAMA 🎓</p>
            <p style="margin-top: 20px; font-size: 12px; color: #9ca3af;">
                © 2025 MyKalama English - Tous droits réservés<br>
                contact@mykalamaenglish.com
            </p>
        </div>
    </div>
</body>
</html>
"""


def create_invoice_in_monday(invoice_data: Dict[str, Any], invoice_type: str = "student") -> Optional[str]:
    """
    Créer une facture dans Monday.com
    
    Args:
        invoice_data: Données de la facture
        invoice_type: "student", "teacher", ou "prestataire"
    
    Returns:
        ID de l'item créé ou None
    """
    
    # Déterminer le groupe selon le type
    group_mapping = {
        "student": "Factures Étudiants",
        "teacher": "Factures Professeurs", 
        "prestataire": "Factures Prestataires"
    }
    
    group_name = group_mapping.get(invoice_type, "Factures Étudiants")
    
    # Construire le nom de la facture
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    invoice_name = f"FAC-{invoice_type.upper()[:3]}-{date_str}-{invoice_data.get('id', '')[:6]}"
    
    # Créer un update/note dans Monday.com avec les détails de la facture
    query = """
    mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
      create_item (
        board_id: $boardId,
        item_name: $itemName,
        column_values: $columnValues
      ) {
        id
      }
    }
    """
    
    column_values = {
        STUDENT_COLUMNS["comments"]: {
            "text": f"FACTURE {invoice_type.upper()}\n"
                    f"Montant: {invoice_data.get('amount', 0)} {invoice_data.get('currency', 'EUR')}\n"
                    f"Date: {invoice_data.get('date', datetime.now().strftime('%d/%m/%Y'))}\n"
                    f"Référence: {invoice_name}"
        }
    }
    
    variables = {
        "boardId": MONDAY_BOARD_STUDENTS,
        "itemName": invoice_name,
        "columnValues": json.dumps(column_values)
    }
    
    result = _make_monday_request(query, variables)
    
    if result and 'data' in result and result['data'].get('create_item'):
        item_id = result['data']['create_item']['id']
        logger.info(f"Monday.com invoice created: {invoice_name} - {item_id}")
        return item_id
    
    return None


def notify_monday_new_registration(student_data: Dict[str, Any]) -> bool:
    """
    Notifier Monday.com d'une nouvelle inscription (avant approbation)
    Ajoute un commentaire sur le board ou crée un item en attente
    """
    
    item_name = f"[EN ATTENTE] {student_data.get('first_name', '')} {student_data.get('last_name', '')}"
    
    column_values = {
        STUDENT_COLUMNS["last_name"]: student_data.get('last_name', ''),
        STUDENT_COLUMNS["email"]: {
            "email": student_data.get('email', ''), 
            "text": student_data.get('email', '')
        },
        STUDENT_COLUMNS["phone"]: {
            "phone": student_data.get('phone', ''), 
            "countryShortName": "SN"
        },
        STUDENT_COLUMNS["comments"]: {
            "text": f"Nouvelle inscription - En attente d'approbation\nDate: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        }
    }
    
    query = """
    mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
      create_item (
        board_id: $boardId,
        item_name: $itemName,
        column_values: $columnValues
      ) {
        id
      }
    }
    """
    
    variables = {
        "boardId": MONDAY_BOARD_STUDENTS,
        "itemName": item_name,
        "columnValues": json.dumps(column_values)
    }
    
    result = _make_monday_request(query, variables)
    
    if result and 'data' in result:
        logger.info(f"Monday.com notified of new registration: {student_data.get('email', '')}")
        return True
    
    return False


def update_monday_item(item_id: str, updates: Dict[str, Any]) -> bool:
    """Mettre à jour un item dans Monday.com"""
    
    query = """
    mutation ($itemId: ID!, $columnValues: JSON!) {
      change_multiple_column_values (
        item_id: $itemId,
        column_values: $columnValues
      ) {
        id
      }
    }
    """
    
    variables = {
        "itemId": item_id,
        "columnValues": json.dumps(updates)
    }
    
    result = _make_monday_request(query, variables)
    
    if result and 'data' in result:
        logger.info(f"Monday.com item updated: {item_id}")
        return True
    
    return False
