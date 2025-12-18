"""
Monday.com CRM Integration
"""
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU5OTA0ODM3NSwiYWFpIjoxMSwidWlkIjo5NzM5OTY1MywiaWFkIjoiMjAyNS0xMi0xOFQwMTowNzoxOC42ODZaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MzI5Mjg2NjYsInJnbiI6ImV1YzEifQ.FgB7cs9lMjYIfg5ENGwMHesoGMQ4VT0e0H9koQOOtzc"
MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_BOARD_ID = "5089020316"

def create_monday_item(student_data: Dict[str, Any]) -> Optional[str]:
    """
    Créer un item dans Monday.com pour un nouvel étudiant approuvé
    
    Args:
        student_data: Dictionnaire avec les données de l'étudiant
        
    Returns:
        ID de l'item créé ou None en cas d'erreur
    """
    
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Construire le nom de l'item (Prénom)
    item_name = student_data.get('first_name', '')
    
    # Mapper le niveau en français pour Monday.com
    level_mapping = {
        'beginner': 'Débutant',
        'intermediate': 'Intermédiaire', 
        'advanced': 'Avancé',
        'professional': 'Professionnel',
        'kkid': 'K-Kid'
    }
    level_label = level_mapping.get(student_data.get('level', 'beginner'), 'Débutant')
    
    # Construire les valeurs des colonnes avec les IDs réels du board
    column_values = {
        "text_mkyn39my": student_data.get('last_name', ''),  # Colonne Nom
        "contact_email": {"email": student_data.get('email', ''), "text": student_data.get('email', '')},  # E-mail
        "contact_phone": {"phone": student_data.get('phone', ''), "countryShortName": "SN"},  # Téléphone
        "status": {"label": level_label},  # Niveau
    }
    
    # Query GraphQL pour créer l'item
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
        "boardId": MONDAY_BOARD_ID,
        "itemName": item_name,
        "columnValues": str(column_values).replace("'", '"')
    }
    
    try:
        response = requests.post(
            MONDAY_API_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'data' in result and result['data'].get('create_item'):
            item_id = result['data']['create_item']['id']
            logger.info(f"Monday.com item created: {item_id} for {item_name}")
            return item_id
        else:
            logger.error(f"Monday.com error: {result.get('errors', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating Monday.com item: {str(e)}")
        return None


def send_welcome_email_via_monday(student_email: str, student_name: str) -> bool:
    """
    Envoyer un email de bienvenue via Monday.com
    
    Args:
        student_email: Email de l'étudiant
        student_name: Nom de l'étudiant
        
    Returns:
        True si succès, False sinon
    """
    
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Template d'email de bienvenue
    email_subject = f"🎉 Bienvenue chez MyKalama English, {student_name} !"
    email_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%); border-radius: 10px;">
            <h1 style="color: white; text-align: center;">🎓 Bienvenue chez MyKalama English !</h1>
        </div>
        
        <div style="max-width: 600px; margin: 20px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #0d9488;">Bonjour {student_name} ! 👋</h2>
            
            <p>Nous sommes ravis de vous accueillir dans notre communauté d'apprentissage de l'anglais !</p>
            
            <p>Votre inscription a été approuvée avec succès. Vous pouvez maintenant accéder à votre espace étudiant et commencer votre parcours d'apprentissage.</p>
            
            <h3 style="color: #0d9488;">🎯 Prochaines étapes :</h3>
            <ul>
                <li>Connectez-vous à votre espace étudiant</li>
                <li>Complétez votre profil</li>
                <li>Consultez votre pack de formation</li>
                <li>Contactez votre professeur</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://tutor-hub-32.preview.emergentagent.com/login" 
                   style="background: #0d9488; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Accéder à mon espace
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #666; font-size: 14px;">
                Besoin d'aide ? Contactez-nous à <a href="mailto:info@mykalamaenglish.com">info@mykalamaenglish.com</a>
            </p>
            
            <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
                © 2025 MyKalama English - Tous droits réservés
            </p>
        </div>
    </body>
    </html>
    """
    
    # Query pour envoyer un email via Monday.com
    # Note: Monday.com n'a pas d'API directe pour envoyer des emails
    # Cette fonctionnalité nécessite une intégration avec un service d'emailing
    # ou l'utilisation d'une automation Monday.com
    
    logger.info(f"Welcome email prepared for {student_email}")
    # TODO: Implémenter l'envoi réel via service d'email (SendGrid, AWS SES, etc.)
    
    return True


def update_monday_item(item_id: str, updates: Dict[str, Any]) -> bool:
    """
    Mettre à jour un item dans Monday.com
    
    Args:
        item_id: ID de l'item à mettre à jour
        updates: Dictionnaire des mises à jour
        
    Returns:
        True si succès, False sinon
    """
    
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }
    
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
        "columnValues": str(updates).replace("'", '"')
    }
    
    try:
        response = requests.post(
            MONDAY_API_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'data' in result:
            logger.info(f"Monday.com item updated: {item_id}")
            return True
        else:
            logger.error(f"Monday.com update error: {result.get('errors', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating Monday.com item: {str(e)}")
        return False
