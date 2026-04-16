"""Shared helper functions used across route modules."""
import uuid
from datetime import datetime, timezone
from config import db, logger, FRONTEND_URL


async def create_notification(user_id: str, arg2=None, arg3=None, arg4=None, *,
                             notification_type: str = None, data: dict = None,
                             title: str = None, message: str = None):
    """Helper function to create notifications.
    Supports multiple calling formats:
    1. create_notification(user_id, notification_type, data) - legacy 3-param format
    2. create_notification(user_id, title, message, notification_type) - 4-param positional
    3. create_notification(user_id, title=..., message=..., notification_type=...) - named params
    """
    actual_title = title
    actual_message = message
    actual_type = notification_type
    actual_data = data

    if isinstance(arg2, str) and isinstance(arg3, dict):
        actual_type = arg2
        actual_data = arg3
    elif isinstance(arg2, str) and isinstance(arg3, str) and isinstance(arg4, str):
        actual_title = arg2
        actual_message = arg3
        actual_type = arg4
    elif isinstance(arg2, str) and isinstance(arg3, str) and arg4 is None:
        actual_title = arg2
        actual_message = arg3

    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": actual_type or "general",
        "is_read": False,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if actual_data:
        notification.update(actual_data)
    if actual_title:
        notification["title"] = actual_title
    if actual_message:
        notification["message"] = actual_message

    await db.notifications.insert_one(notification)
    logger.info(f"Notification created for user {user_id}: {notification.get('type')}")
    return notification


async def add_student_points(student_id: str, points: int, reason: str = ""):
    """Add points to a student's treasure chest."""
    try:
        points_record = await db.student_points.find_one({"student_id": student_id})

        if points_record:
            new_total = points_record.get('total_points', 0) + points
            new_available = points_record.get('available_points', 0) + points
            await db.student_points.update_one(
                {"student_id": student_id},
                {"$set": {
                    "total_points": new_total,
                    "available_points": new_available,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
        else:
            new_record = {
                "id": str(uuid.uuid4()),
                "student_id": student_id,
                "total_points": points,
                "available_points": points,
                "total_discount_earned": 0.0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.student_points.insert_one(new_record)

        logger.info(f"Added {points} points to student {student_id}: {reason}")

        updated_record = await db.student_points.find_one({"student_id": student_id})
        if updated_record and updated_record.get('available_points', 0) >= 50:
            await create_notification(
                user_id=student_id,
                title="Recompenses debloquees !",
                message="Felicitations ! Vous avez atteint 50 points. Vos reductions sont maintenant actives dans votre Coffre aux Tresors !",
                notification_type="reward"
            )

        return True
    except Exception as e:
        logger.error(f"Error adding points to student {student_id}: {str(e)}")
        return False


async def send_admin_notification_email(user_email: str, first_name: str, last_name: str, level: str):
    """Send email notification to admin when a new student registers."""
    email_content = f"""
    NOUVELLE INSCRIPTION - My KALAMA ENGLISH
    
    Un nouvel etudiant s'est inscrit sur la plateforme :
    
    Nom complet: {first_name} {last_name}
    Email: {user_email}
    Niveau: {level}
    Date d'inscription: {datetime.now(timezone.utc).strftime('%d/%m/%Y a %H:%M')}
    
    Veuillez vous connecter au dashboard admin pour approuver cette inscription.
    
    Lien dashboard: {FRONTEND_URL}/admin
    """
    logger.info(f"Admin notification email for new registration: {user_email}")
    logger.info(email_content)
    return True


def generate_welcome_letter_content(first_name: str, level: str, role: str, email: str, temp_password: str) -> str:
    """Generate welcome letter content based on user level and role."""
    if role == "teacher":
        return f"""Dear Professor,

We are delighted to welcome you to MYKALMAENGLISH, our online platform dedicated to English language learning. Your registration is now confirmed, and we look forward to having you join our community of teachers and learners.

Here are some details to help you get started:

Access to the Platform: You can log in to your account using the credentials below. You can also change your password in your profile settings.

Your Credentials:
Email: {email}
Temporary Password: {temp_password}

Available Resources: Explore our digital library, KALAMATHÈQUE, along with other teaching materials designed to enhance your instruction.

Technical Support: If you have any questions or encounter any technical issues, please feel free to reach out to our support team at support@mykalmaenglish.com or mykalamaenglish@gmail.com.

Upcoming Events: Stay tuned for our webinars and workshops featured in the News section, where you can discover new teaching methods and connect with other professionals.

We wish you great success on your journey with MYKALMAENGLISH. Please do not hesitate to share your suggestions or questions with us.

Best regards,
DIAGNE Mansour
CEO of KalamaEnglish
Email: mykalamaenglish@gmail.com
Website: mykalamaenglish.com"""

    if level == "beginner":
        return f"""Hello {first_name},

Nous sommes ravis de vous accueillir sur MYKALMAENGLISH !

Felicitations pour avoir fait le premier pas dans votre parcours d'apprentissage de l'anglais. En tant que debutant, vous trouverez que notre plateforme est concue pour vous accompagner a chaque etape. Voici ce a quoi vous pouvez vous attendre :

Lecons interactives : un contenu engageant adapte aux debutants pour vous aider a construire une base solide en anglais.

Apprentissage flexible : accedez a vos cours a tout moment, partout, a votre propre rythme.

Communaute de soutien : rejoignez notre communaute dynamique d'apprenants et d'instructeurs qui sont la pour vous aider a reussir.

Vos identifiants de connexion :
Email: {email}
Mot de passe provisoire: {temp_password}

Vos acces :
- Kalamatheque : Bibliotheque en ligne avec acces illimite pour lire des livres
- News : Section actualites et evenements pour rester informe
- Profil : Changez votre mot de passe provisoire dans votre espace, partie Profil

Pour commencer, connectez-vous simplement a votre compte et explorez les cours disponibles. Si vous avez des questions ou avez besoin d'aide, n'hesitez pas a contacter notre equipe de support.

Nous vous souhaitons une experience d'apprentissage enrichissante et agreable !

Cordialement,

L'equipe MYKALMAENGLISH"""

    elif level == "intermediate":
        return f"""Hello {first_name},

Nous sommes ravis de vous accueillir sur MYKALMAENGLISH ! Vous vous etes inscrit avec succes a notre cours en ligne de niveau intermediaire, et nous sommes impatients de vous accompagner dans votre apprentissage de la langue.

Lecons interactives : un contenu engageant adapte a votre niveau pour vous aider a approfondir vos connaissances en anglais.

Apprentissage flexible : accedez a vos cours a tout moment, partout, a votre propre rythme.

Communaute de soutien : rejoignez notre communaute dynamique d'apprenants et d'instructeurs qui sont la pour vous aider a reussir.

Vos identifiants de connexion :
Email: {email}
Mot de passe provisoire: {temp_password}

Vos acces :
- Kalamatheque : Bibliotheque en ligne avec acces illimite pour lire des livres
- News : Section actualites et evenements pour rester informe
- Profil : Changez votre mot de passe provisoire dans votre espace, partie Profil

Pour commencer, connectez-vous simplement a votre compte et explorez les cours disponibles. Si vous avez des questions ou avez besoin d'aide, n'hesitez pas a contacter notre equipe de support.

Sur MYKALMAENGLISH, vous trouverez une variete de ressources concues pour ameliorer vos competences en anglais, notamment des lecons interactives, des exercices engageants et une communaute d'apprenants soudee. Nous vous encourageons a explorer la plateforme et a profiter pleinement de tout ce que nous offrons.

Nous vous souhaitons une experience d'apprentissage enrichissante et agreable !

Cordialement,

L'equipe MYKALMAENGLISH"""

    else:
        return f"""Hello {first_name},

Nous sommes ravis de vous accueillir sur MYKALMAENGLISH ! Vous avez franchi une etape importante pour ameliorer vos competences en anglais professionnel, et nous sommes impatients de vous accompagner dans cette aventure.

Notre programme de formation intensive et acceleree en anglais est concu specialement pour des professionnels comme vous. Voici ce que vous pouvez attendre :

Apprentissage complet : Engagez-vous avec un contenu adapte qui se concentre sur des applications concretes.

Acces flexible : Apprenez a votre rythme grace a notre plateforme en ligne, disponible a tout moment et de n'importe ou.

Communaute de soutien : Connectez-vous avec d'autres apprenants et des instructeurs qui sont la pour vous soutenir.

Vos identifiants de connexion :
Email: {email}
Mot de passe provisoire: {temp_password}

Vos acces :
- Kalamatheque : Bibliotheque en ligne avec acces illimite pour lire des livres
- News : Section actualites et evenements pour rester informe
- Profil : Changez votre mot de passe provisoire dans votre espace, partie Profil

Pour commencer, veuillez vous connecter a votre compte et explorer les materiaux de cours. Si vous avez des questions ou avez besoin d'assistance, n'hesitez pas a contacter notre equipe de support.

Nous sommes impatients de vous voir progresser dans votre apprentissage de l'anglais !

Cordialement,

L'equipe MYKALMAENGLISH"""


# Hardcoded test questions (fallback when DB is empty)
TEST_QUESTIONS = {
    "beginner": [
        {"id": 1, "question": "What is the correct greeting?", "options": ["Hello", "Bonjour", "Hola", "Ciao"], "correct": 0},
        {"id": 2, "question": "How do you say 'thank you'?", "options": ["Please", "Sorry", "Thank you", "Welcome"], "correct": 2},
        {"id": 3, "question": "Complete: I ___ a student", "options": ["am", "is", "are", "be"], "correct": 0},
        {"id": 4, "question": "What is the opposite of 'hot'?", "options": ["warm", "cool", "cold", "freeze"], "correct": 2},
        {"id": 5, "question": "How many days are in a week?", "options": ["5", "6", "7", "8"], "correct": 2},
        {"id": 6, "question": "Complete: She ___ a teacher", "options": ["am", "is", "are", "be"], "correct": 1},
        {"id": 7, "question": "What color is the sky?", "options": ["Green", "Blue", "Red", "Yellow"], "correct": 1},
        {"id": 8, "question": "How do you say 'goodbye'?", "options": ["Hello", "Hi", "Goodbye", "Welcome"], "correct": 2},
        {"id": 9, "question": "Complete: They ___ happy", "options": ["am", "is", "are", "be"], "correct": 2},
        {"id": 10, "question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "correct": 1},
        {"id": 11, "question": "Complete: I ___ coffee", "options": ["like", "likes", "liking", "liked"], "correct": 0},
        {"id": 12, "question": "What is the first month of the year?", "options": ["December", "January", "February", "March"], "correct": 1},
        {"id": 13, "question": "How do you spell the number 1?", "options": ["won", "one", "own", "on"], "correct": 1},
        {"id": 14, "question": "Complete: We ___ to school", "options": ["go", "goes", "going", "went"], "correct": 0},
        {"id": 15, "question": "What do you say when you meet someone?", "options": ["Goodbye", "Nice to meet you", "See you later", "Take care"], "correct": 1},
        {"id": 16, "question": "Complete: He ___ a book", "options": ["read", "reads", "reading", "readed"], "correct": 1},
        {"id": 17, "question": "What is the opposite of 'big'?", "options": ["large", "huge", "small", "tiny"], "correct": 2},
        {"id": 18, "question": "How many seasons are there?", "options": ["2", "3", "4", "5"], "correct": 2},
        {"id": 19, "question": "Complete: It ___ raining", "options": ["am", "is", "are", "be"], "correct": 1},
        {"id": 20, "question": "What comes after Monday?", "options": ["Sunday", "Tuesday", "Wednesday", "Thursday"], "correct": 1}
    ],
    "intermediate": [
        {"id": 1, "question": "Choose the correct form: I ___ to Paris last year", "options": ["go", "went", "have gone", "going"], "correct": 1},
        {"id": 2, "question": "What is the past participle of 'write'?", "options": ["wrote", "written", "writing", "writes"], "correct": 1},
        {"id": 3, "question": "Complete: If I ___ rich, I would travel the world", "options": ["am", "was", "were", "be"], "correct": 2},
        {"id": 4, "question": "Which is correct?", "options": ["She don't like it", "She doesn't like it", "She not like it", "She no like it"], "correct": 1},
        {"id": 5, "question": "Complete: I have ___ this movie before", "options": ["see", "saw", "seen", "seeing"], "correct": 2},
        {"id": 6, "question": "What is the comparative form of 'good'?", "options": ["gooder", "more good", "better", "best"], "correct": 2},
        {"id": 7, "question": "Complete: She ___ working here for 5 years", "options": ["is", "has been", "was", "have been"], "correct": 1},
        {"id": 8, "question": "Which preposition? I'm interested ___ music", "options": ["at", "in", "on", "for"], "correct": 1},
        {"id": 9, "question": "Complete: By next year, I ___ graduated", "options": ["will", "will have", "would", "would have"], "correct": 1},
        {"id": 10, "question": "What is the correct form: ___ you ever been to London?", "options": ["Did", "Do", "Have", "Has"], "correct": 2},
        {"id": 11, "question": "Complete: I wish I ___ speak French", "options": ["can", "could", "will", "would"], "correct": 1},
        {"id": 12, "question": "Which is passive voice?", "options": ["I wrote a letter", "A letter was written", "I am writing", "I write letters"], "correct": 1},
        {"id": 13, "question": "Complete: Neither John ___ Mary came", "options": ["or", "nor", "and", "but"], "correct": 1},
        {"id": 14, "question": "What is correct?", "options": ["He said me", "He told to me", "He told me", "He said to I"], "correct": 2},
        {"id": 15, "question": "Complete: I'm looking forward ___ you", "options": ["to see", "to seeing", "see", "seeing"], "correct": 1},
        {"id": 16, "question": "Which modal for obligation?", "options": ["can", "may", "must", "might"], "correct": 2},
        {"id": 17, "question": "Complete: The meeting ___ postponed", "options": ["has", "has been", "have", "have been"], "correct": 1},
        {"id": 18, "question": "What is correct?", "options": ["Despite of the rain", "Despite the rain", "Despite to the rain", "Despite for the rain"], "correct": 1},
        {"id": 19, "question": "Complete: I would rather ___ at home", "options": ["stay", "to stay", "staying", "stayed"], "correct": 0},
        {"id": 20, "question": "Which is correct?", "options": ["She made me to laugh", "She made me laugh", "She made me laughing", "She made I laugh"], "correct": 1}
    ],
    "advanced": [
        {"id": 1, "question": "Choose the correct: Had I known, I ___ differently", "options": ["would act", "would have acted", "will act", "acted"], "correct": 1},
        {"id": 2, "question": "What is the meaning of 'ubiquitous'?", "options": ["Rare", "Everywhere", "Unique", "Special"], "correct": 1},
        {"id": 3, "question": "Complete: Scarcely ___ arrived when it started raining", "options": ["I had", "had I", "I have", "have I"], "correct": 1},
        {"id": 4, "question": "Which is correct?", "options": ["It's high time we left", "It's high time we leave", "It's high time we leaving", "It's high time we to leave"], "correct": 0},
        {"id": 5, "question": "What does 'ephemeral' mean?", "options": ["Lasting forever", "Short-lived", "Beautiful", "Mysterious"], "correct": 1},
        {"id": 6, "question": "Complete: Not only ___ late, but he forgot the documents", "options": ["he was", "was he", "he is", "is he"], "correct": 1},
        {"id": 7, "question": "Which is subjunctive mood?", "options": ["I suggest he goes", "I suggest he go", "I suggest he going", "I suggest him to go"], "correct": 1},
        {"id": 8, "question": "What is 'verisimilitude'?", "options": ["Truth", "Lie", "Appearance of truth", "Deception"], "correct": 2},
        {"id": 9, "question": "Complete: The proposal ___ thorough consideration", "options": ["warrants", "warranty", "warranting", "warranted"], "correct": 0},
        {"id": 10, "question": "What does 'obfuscate' mean?", "options": ["Clarify", "Confuse", "Simplify", "Explain"], "correct": 1},
        {"id": 11, "question": "Which is correct?", "options": ["I am used to wake up early", "I used to wake up early", "I am use to wake up early", "I use to waking up early"], "correct": 1},
        {"id": 12, "question": "What is 'sanguine'?", "options": ["Pessimistic", "Optimistic", "Angry", "Sad"], "correct": 1},
        {"id": 13, "question": "Complete: Were it not for your help, I ___ failed", "options": ["would", "would have", "will", "will have"], "correct": 1},
        {"id": 14, "question": "What does 'pellucid' mean?", "options": ["Opaque", "Clear", "Dirty", "Colored"], "correct": 1},
        {"id": 15, "question": "Which is correct cleft sentence?", "options": ["It was John who broke the vase", "It is John who broke the vase", "It John who broke the vase", "John who broke the vase"], "correct": 0},
        {"id": 16, "question": "What is 'quixotic'?", "options": ["Practical", "Realistic", "Idealistic but impractical", "Pessimistic"], "correct": 2},
        {"id": 17, "question": "Complete: Little ___ that this would happen", "options": ["I knew", "did I know", "I know", "do I know"], "correct": 1},
        {"id": 18, "question": "What does 'laconic' mean?", "options": ["Verbose", "Brief", "Eloquent", "Detailed"], "correct": 1},
        {"id": 19, "question": "Which is correct?", "options": ["I'd sooner die than betray", "I'd sooner die than to betray", "I'd sooner to die than betray", "I'd sooner dying than betray"], "correct": 0},
        {"id": 20, "question": "What is 'perspicacious'?", "options": ["Dull", "Insightful", "Confused", "Ignorant"], "correct": 1}
    ]
}
