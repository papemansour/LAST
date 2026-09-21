import boto3
from botocore.exceptions import ClientError
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        """Initialize AWS SES client"""
        try:
            # AWS credentials from environment variables
            self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
            self.sender_email = os.environ.get('AWS_SES_SENDER_EMAIL', 'papemansour01@gmail.com')
            self.frontend_url = os.environ.get('FRONTEND_URL', '')
            self.kalamatheque_password = os.environ.get('KALAMATHEQUE_PASSWORD', 'digikode')
            
            if not self.aws_access_key or not self.aws_secret_key:
                logger.warning("AWS credentials not found. Email sending will be logged only.")
                self.ses_client = None
            else:
                self.ses_client = boto3.client(
                    'ses',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )
                logger.info("AWS SES client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AWS SES client: {str(e)}")
            self.ses_client = None
    
    async def send_welcome_email(
        self, 
        to_email: str, 
        first_name: str, 
        last_name: str, 
        temp_password: str
    ) -> bool:
        """
        Send welcome email to newly approved student
        """
        subject = "Bienvenue sur My KALAMA ENGLISH ! 🎉"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .credentials {{ background: white; padding: 20px; border-left: 4px solid #14b8a6; 
                               margin: 20px 0; border-radius: 5px; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #14b8a6; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Bienvenue sur My KALAMA ENGLISH !</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{first_name} {last_name}</strong>,</p>
                    
                    <p>Nous sommes ravis de vous accueillir dans notre communauté d'apprentissage de l'anglais ! 🎓</p>
                    
                    <p>Votre compte a été validé avec succès. Vous pouvez maintenant accéder à tous nos services d'apprentissage de l'anglais.</p>
                    
                    <div class="credentials">
                        <h3>VOS IDENTIFIANTS DE CONNEXION</h3>
                        <p><strong>Email :</strong> {to_email}</p>
                        <p><strong>Mot de passe provisoire :</strong> <code style="background: #f0f0f0; padding: 5px 10px; border-radius: 3px;">{temp_password}</code></p>
                    </div>
                    
                    <div class="credentials">
                        <h3>ACCÈS À LA KALAMATHÈQUE 📚</h3>
                        <p>Bibliothèque numérique de livres et ressources audio</p>
                        <p><strong>Mot de passe KALAMATHÈQUE :</strong> <code style="background: #f0f0f0; padding: 5px 10px; border-radius: 3px;">{self.kalamatheque_password}</code></p>
                    </div>
                    
                    <center>
                        <a href="{self.frontend_url}/login" class="button">
                            Se connecter maintenant
                        </a>
                    </center>
                    
                    <p><strong>⚠️ IMPORTANT :</strong> Nous vous recommandons fortement de changer votre mot de passe dès votre première connexion pour sécuriser votre compte.</p>
                    
                    <p>Vous pouvez le faire depuis votre espace étudiant ➜ Profil ➜ Changer le mot de passe.</p>
                    
                    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
                    
                    <p>Bon apprentissage ! 🚀</p>
                    
                    <p>Cordialement,<br>
                    <strong>L'équipe My KALAMA ENGLISH</strong></p>
                </div>
                <div class="footer">
                    <p>My KALAMA ENGLISH - Plateforme d'apprentissage de l'anglais</p>
                    <p>📧 info.kalamaenglish@gmail.com</p>
                    <p>© 2025 MyKalamaenglish. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Bonjour {first_name} {last_name},
        
        Bienvenue sur My KALAMA ENGLISH ! 🎉
        
        Votre compte a été validé avec succès. Vous pouvez maintenant accéder à tous nos services d'apprentissage de l'anglais.
        
        VOS IDENTIFIANTS:
        - Email: {to_email}
        - Mot de passe provisoire: {temp_password}
        
        ACCÈS À LA KALAMATHÈQUE (Bibliothèque numérique):
        - Mot de passe KALAMATHÈQUE: digikode
        
        LIEN DE CONNEXION:
        {self.frontend_url}/login
        
        CHANGEZ VOTRE MOT DE PASSE:
        Nous vous recommandons fortement de changer votre mot de passe dès votre première connexion pour sécuriser votre compte.
        Vous pouvez le faire depuis votre espace étudiant > Profil > Changer le mot de passe.
        
        N'hésitez pas à nous contacter si vous avez des questions.
        
        Cordialement,
        L'équipe My KALAMA ENGLISH
        info.kalamaenglish@gmail.com
        """
        
        return await self._send_email(to_email, subject, html_body, text_body)
    
    async def send_registration_confirmation_email(
        self,
        to_email: str,
        first_name: str,
        last_name: str
    ) -> bool:
        """
        Send confirmation email to student right after registration
        """
        subject = "📝 Demande d'inscription reçue - My KALAMA ENGLISH"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 20px; border-left: 4px solid #14b8a6; 
                            margin: 20px 0; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Demande d'inscription reçue !</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{first_name} {last_name}</strong>,</p>
                    
                    <p>Merci d'avoir choisi <strong>My KALAMA ENGLISH</strong> pour votre apprentissage de l'anglais ! 🎓</p>
                    
                    <div class="info-box">
                        <h3>📬 Votre demande a bien été reçue</h3>
                        <p>Nous avons bien reçu votre demande d'inscription et nous vous remercions de votre intérêt pour notre plateforme.</p>
                    </div>
                    
                    <div class="info-box">
                        <h3>⏳ Prochaines étapes</h3>
                        <p>Notre équipe administrative est en train d'examiner votre demande. Vous recevrez <strong>un email de bienvenue avec vos identifiants de connexion</strong> dans les plus brefs délais.</p>
                        <p>L'email contiendra :</p>
                        <ul>
                            <li>✉️ Votre adresse email de connexion</li>
                            <li>🔐 Votre mot de passe provisoire</li>
                            <li>📚 Les instructions pour accéder à la plateforme</li>
                        </ul>
                    </div>
                    
                    <p><strong>💡 Conseil :</strong> Surveillez votre boîte de réception (et vos spams) pour ne pas manquer notre email de bienvenue !</p>
                    
                    <p>Si vous avez des questions en attendant, n'hésitez pas à nous contacter à <strong>info.kalamaenglish@gmail.com</strong>.</p>
                    
                    <p>À très bientôt sur My KALAMA ENGLISH ! 🚀</p>
                    
                    <p>Cordialement,<br>
                    <strong>L'équipe My KALAMA ENGLISH</strong></p>
                </div>
                <div class="footer">
                    <p>My KALAMA ENGLISH - Plateforme d'apprentissage de l'anglais</p>
                    <p>📧 info.kalamaenglish@gmail.com</p>
                    <p>© 2025 MyKalamaenglish. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Bonjour {first_name} {last_name},
        
        DEMANDE D'INSCRIPTION REÇUE - My KALAMA ENGLISH
        
        Merci d'avoir choisi My KALAMA ENGLISH pour votre apprentissage de l'anglais !
        
        VOTRE DEMANDE A BIEN ÉTÉ REÇUE:
        Nous avons bien reçu votre demande d'inscription et nous vous remercions de votre intérêt pour notre plateforme.
        
        PROCHAINES ÉTAPES:
        Notre équipe administrative est en train d'examiner votre demande. Vous recevrez un email de bienvenue avec vos identifiants de connexion dans les plus brefs délais.
        
        L'email contiendra:
        - Votre adresse email de connexion
        - Votre mot de passe provisoire
        - Les instructions pour accéder à la plateforme
        
        Conseil: Surveillez votre boîte de réception (et vos spams) pour ne pas manquer notre email de bienvenue !
        
        Si vous avez des questions, contactez-nous à info.kalamaenglish@gmail.com
        
        À très bientôt sur My KALAMA ENGLISH !
        
        Cordialement,
        L'équipe My KALAMA ENGLISH
        info.kalamaenglish@gmail.com
        """
        
        return await self._send_email(to_email, subject, html_body, text_body)

    async def send_admin_notification(
        self, 
        user_email: str, 
        first_name: str, 
        last_name: str, 
        level: str,
        phone: str = ""
    ) -> bool:
        """
        Send email notification to admin when a new student registers
        """
        admin_email = "mykalamaenglish@gmail.com"
        subject = "🔔 Nouvelle inscription sur My KALAMA ENGLISH"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .student-info {{ background: white; padding: 20px; border-left: 4px solid #f59e0b; 
                                margin: 20px 0; border-radius: 5px; }}
                .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; 
                           border-bottom: 1px solid #eee; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #14b8a6; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Nouvelle Inscription</h1>
                </div>
                <div class="content">
                    <p><strong>Un nouvel étudiant s'est inscrit sur la plateforme My KALAMA ENGLISH.</strong></p>
                    
                    <div class="student-info">
                        <h3>Informations de l'étudiant</h3>
                        <div class="info-row">
                            <span><strong>Nom complet:</strong></span>
                            <span>{first_name} {last_name}</span>
                        </div>
                        <div class="info-row">
                            <span><strong>Email:</strong></span>
                            <span>{user_email}</span>
                        </div>
                        <div class="info-row">
                            <span><strong>Téléphone:</strong></span>
                            <span>{phone or 'Non fourni'}</span>
                        </div>
                        <div class="info-row">
                            <span><strong>Niveau:</strong></span>
                            <span>{level.upper()}</span>
                        </div>
                        <div class="info-row">
                            <span><strong>Date d'inscription:</strong></span>
                            <span>{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}</span>
                        </div>
                    </div>
                    
                    <center>
                        <a href="{self.frontend_url}/admin" class="button">
                            Accéder au Dashboard Admin
                        </a>
                    </center>
                    
                    <p><strong>Action requise:</strong> Veuillez vous connecter au dashboard admin pour approuver cette inscription et créer les identifiants de l'étudiant.</p>
                    
                    <p>Cordialement,<br>
                    <strong>Système My KALAMA ENGLISH</strong></p>
                </div>
                <div class="footer">
                    <p>My KALAMA ENGLISH - Système de notification automatique</p>
                    <p>© 2025 MyKalamaenglish. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        NOUVELLE INSCRIPTION - My KALAMA ENGLISH
        
        Un nouvel étudiant s'est inscrit sur la plateforme :
        
        Nom complet: {first_name} {last_name}
        Email: {user_email}
        Téléphone: {phone or 'Non fourni'}
        Niveau: {level.upper()}
        Date d'inscription: {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}
        
        Veuillez vous connecter au dashboard admin pour approuver cette inscription.
        
        Lien dashboard: {self.frontend_url}/admin
        """
        
        return await self._send_email(admin_email, subject, html_body, text_body)
    
    async def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str, 
        text_body: str
    ) -> bool:
        """
        Internal method to send email via AWS SES
        """
        if not self.ses_client:
            logger.warning(f"Email not sent (no SES client). Would send to {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {text_body}")
            return False
        
        try:
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {response['MessageId']}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Error sending email to {to_email}: {error_code} - {error_message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            return False

    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        temporary_password: str
    ) -> bool:
        """
        Send password reset email with temporary password
        """
        subject = "🔐 Réinitialisation de votre mot de passe - My KALAMA ENGLISH"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .credentials {{ background: white; padding: 20px; border-left: 4px solid #ef4444; 
                               margin: 20px 0; border-radius: 5px; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #14b8a6; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; 
                           margin: 20px 0; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Réinitialisation de mot de passe</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{user_name}</strong>,</p>
                    
                    <p>L'administrateur a réinitialisé votre mot de passe sur My KALAMA ENGLISH.</p>
                    
                    <div class="credentials">
                        <h3>VOTRE NOUVEAU MOT DE PASSE TEMPORAIRE</h3>
                        <p><strong>Email :</strong> {to_email}</p>
                        <p><strong>Mot de passe temporaire :</strong> <code style="background: #f0f0f0; padding: 5px 10px; border-radius: 3px; font-size: 16px;">{temporary_password}</code></p>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⚠️ IMPORTANT - Action requise :</strong></p>
                        <ul>
                            <li>Ce mot de passe est temporaire et doit être changé dès votre prochaine connexion</li>
                            <li>Pour votre sécurité, ne partagez jamais ce mot de passe</li>
                            <li>Changez-le immédiatement après connexion depuis votre espace personnel</li>
                        </ul>
                    </div>
                    
                    <center>
                        <a href="{self.frontend_url}/login" class="button">
                            Se connecter maintenant
                        </a>
                    </center>
                    
                    <p><strong>Comment changer votre mot de passe :</strong></p>
                    <ol>
                        <li>Connectez-vous avec le mot de passe temporaire ci-dessus</li>
                        <li>Accédez à votre profil</li>
                        <li>Sélectionnez "Changer le mot de passe"</li>
                        <li>Choisissez un nouveau mot de passe sécurisé</li>
                    </ol>
                    
                    <p>Si vous n'avez pas demandé cette réinitialisation, veuillez contacter immédiatement l'administration.</p>
                    
                    <p>Cordialement,<br>
                    <strong>L'équipe My KALAMA ENGLISH</strong></p>
                </div>
                <div class="footer">
                    <p>My KALAMA ENGLISH - Plateforme d'apprentissage de l'anglais</p>
                    <p>📧 mykalamaenglish@gmail.com</p>
                    <p>© 2025 MyKalamaenglish. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Bonjour {user_name},
        
        RÉINITIALISATION DE MOT DE PASSE - My KALAMA ENGLISH
        
        L'administrateur a réinitialisé votre mot de passe.
        
        NOUVELLES IDENTIFIANTS:
        - Email: {to_email}
        - Mot de passe temporaire: {temporary_password}
        
        ⚠️ IMPORTANT - Action requise:
        - Ce mot de passe est temporaire et doit être changé dès votre prochaine connexion
        - Pour votre sécurité, ne partagez jamais ce mot de passe
        - Changez-le immédiatement après connexion depuis votre espace personnel
        
        LIEN DE CONNEXION:
        {self.frontend_url}/login
        
        COMMENT CHANGER VOTRE MOT DE PASSE:
        1. Connectez-vous avec le mot de passe temporaire ci-dessus
        2. Accédez à votre profil
        3. Sélectionnez "Changer le mot de passe"
        4. Choisissez un nouveau mot de passe sécurisé
        
        Si vous n'avez pas demandé cette réinitialisation, veuillez contacter immédiatement l'administration.
        
        Cordialement,
        L'équipe My KALAMA ENGLISH
        mykalamaenglish@gmail.com
        """
        
        return await self._send_email(to_email, subject, html_body, text_body)
    
    async def send_level_based_welcome_email(
        self, 
        to_email: str, 
        first_name: str, 
        level: str,
        temp_password: str,
        last_name: str = ""
    ) -> bool:
        """
        Send level-based welcome email to newly approved student
        Format exact demandé par l'utilisateur
        """
        # Map level to display name
        level_display = {
            "kkid": "K-Kid (Enfant)",
            "beginner": "Débutant",
            "intermediate": "Intermédiaire",
            "advanced": "Avancé/Professionnel"
        }
        level_name = level_display.get(level, level.capitalize() if level else "Débutant")
        
        subject = "Hello and Welcome"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.8; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; }}
                .credentials {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #14b8a6; 
                               margin: 25px 0; border-radius: 0 8px 8px 0; }}
                .credentials h3 {{ margin-top: 0; color: #14b8a6; }}
                .kalamatheque {{ background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; 
                               margin: 25px 0; border-radius: 0 8px 8px 0; }}
                .features {{ background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .features ul {{ margin: 0; padding-left: 20px; }}
                .features li {{ margin: 10px 0; color: #2e7d32; }}
                .button {{ display: inline-block; padding: 15px 40px; background: #14b8a6; 
                          color: white; text-decoration: none; border-radius: 8px; margin: 25px 0;
                          font-weight: bold; font-size: 16px; }}
                .button:hover {{ background: #0d9488; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px;
                          background: #f8f9fa; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none; }}
                .highlight {{ background: #e3f2fd; padding: 3px 8px; border-radius: 4px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Hello and Welcome!</h1>
                </div>
                <div class="content">
                    <p>Votre inscription à notre cours d'anglais en ligne niveau <strong>{level_name}</strong> est confirmée.</p>
                    
                    <p>Nous sommes ravis de vous accompagner dans votre apprentissage.</p>
                    
                    <div class="features">
                        <p><strong>Vous aurez accès à :</strong></p>
                        <ul>
                            <li>📚 Des leçons interactives adaptées à votre niveau</li>
                            <li>⏰ Une formation flexible accessible à tout moment</li>
                            <li>🎯 Un accompagnement pour progresser efficacement</li>
                        </ul>
                    </div>
                    
                    <div class="credentials">
                        <h3>🔐 Vos identifiants de connexion :</h3>
                        <p>📧 <strong>Email :</strong> <span class="highlight">{to_email}</span></p>
                        <p>🔑 <strong>Mot de passe provisoire :</strong> <span class="highlight">{temp_password}</span></p>
                    </div>
                    
                    <div class="kalamatheque">
                        <p>📖 <strong>Votre accès à Kalamathèque</strong>, notre bibliothèque en ligne, est également disponible depuis votre espace personnel, pour lire des livres en anglais.</p>
                        <p>🔑 <strong>Mot de passe de la Kalamathèque :</strong> <span class="highlight">Digika</span></p>
                    </div>
                    
                    <center>
                        <p><strong>Connectez-vous dès maintenant sur :</strong></p>
                        <a href="{self.frontend_url}/login" class="button">
                            🚀 Accéder à Mykalama
                        </a>
                    </center>
                    
                    <p style="margin-top: 30px;">Nous vous souhaitons une excellente formation !</p>
                    
                    <p>Cordialement,<br>
                    <strong>L'équipe MYKALAMA</strong></p>
                </div>
                <div class="footer">
                    <p>© {self._get_current_year()} MYKALMAENGLISH - Tous droits réservés</p>
                    <p>Cet email a été envoyé à {to_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""Hello and Welcome!

Votre inscription à notre cours d'anglais en ligne niveau {level_name} est confirmée.

Nous sommes ravis de vous accompagner dans votre apprentissage.

Vous aurez accès à :
- Des leçons interactives adaptées à votre niveau
- Une formation flexible accessible à tout moment
- Un accompagnement pour progresser efficacement

Vos identifiants de connexion :
- Email : {to_email}
- Mot de passe provisoire : {temp_password}

Votre accès à Kalamathèque, notre bibliothèque en ligne, est également disponible depuis votre espace personnel, pour lire des livres en anglais.
- Mot de passe de la Kalamathèque : Digika

Connectez-vous dès maintenant sur : {self.frontend_url}/login

Nous vous souhaitons une excellente formation !

Cordialement,
L'équipe MYKALAMA
"""
        
        return await self._send_email(to_email, subject, html_body, text_body)
    
    def _get_current_year(self):
        """Get current year for footer"""
        from datetime import datetime
        return datetime.now().year
    
    async def send_invoice_email(
        self,
        to_email: str,
        recipient_name: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """
        Send invoice email to teacher or student
        """
        return await self._send_email(to_email, subject, html_content, text_content)

# Singleton instance
email_service = EmailService()

# Expose functions for easy import
async def send_welcome_email(to_email: str, first_name: str, last_name: str, temp_password: str) -> bool:
    return await email_service.send_welcome_email(to_email, first_name, last_name, temp_password)

async def send_level_based_welcome_email(to_email: str, first_name: str, level: str, temp_password: str) -> bool:
    return await email_service.send_level_based_welcome_email(to_email, first_name, level, temp_password)

async def send_admin_notification(user_email: str, first_name: str, last_name: str, level: str, phone: str = "") -> bool:
    return await email_service.send_admin_notification(user_email, first_name, last_name, level, phone)

async def send_password_reset_email(to_email: str, user_name: str, temporary_password: str) -> bool:
    return await email_service.send_password_reset_email(to_email, user_name, temporary_password)

async def send_registration_confirmation_email(to_email: str, first_name: str, last_name: str) -> bool:
    return await email_service.send_registration_confirmation_email(to_email, first_name, last_name)
