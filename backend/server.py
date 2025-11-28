from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import jwt
import stripe
from passlib.context import CryptContext
from email_service import email_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Frontend URL for emails and notifications
FRONTEND_URL = os.environ.get('FRONTEND_URL', '')

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET') or os.environ.get('SECRET_KEY', 'development-secret-key-change-in-production')
# Warn if using default key
if SECRET_KEY == 'development-secret-key-change-in-production':
    logger.warning("⚠️ Using default JWT secret key. Set JWT_SECRET environment variable in production!")
ALGORITHM = "HS256"

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    role: str  # admin, student, teacher
    level: Optional[str] = None  # beginner, intermediate, advanced
    is_active: bool = False
    is_restricted: bool = False  # for restricting student access
    password_hash: str
    temporary_password: Optional[str] = None
    assigned_teacher: Optional[str] = None  # teacher id for students
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    level: str
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class TeacherCreate(BaseModel):
    first_name: str
    last_name: str

class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    title: str
    description: str
    level: str
    schedule: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CourseCreate(BaseModel):
    title: str
    description: str
    level: str
    schedule: str

class TestResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    level: str
    score: int
    total_questions: int
    answers: List[dict]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TestSubmission(BaseModel):
    level: str
    answers: List[dict]

class MessageAttachment(BaseModel):
    file_url: str
    filename: str
    file_type: str  # pdf, doc, docx, image, etc.

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_user_id: str
    to_user_id: str
    content: str
    attachment: Optional[MessageAttachment] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_read: bool = False

class MessageCreate(BaseModel):
    to_user_id: str
    content: str
    attachment: Optional[MessageAttachment] = None

class Attendance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    date: datetime
    status: str  # present, absent, late
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AttendanceCreate(BaseModel):
    date: str
    status: str

class GenerateGroupMagicCode(BaseModel):
    student_ids: List[str]
    group_name: str

class News(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    image_url: Optional[str] = None
    event_date: Optional[datetime] = None  # For scheduled events
    published_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author_id: str
    author_name: str

class NewsCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    event_date: Optional[str] = None  # ISO format string

class WelcomeLetter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_name: str
    user_level: str  # beginner, intermediate, advanced
    user_role: str  # student, teacher
    temp_password: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_read: bool = False

class ClubPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    author_name: str
    author_role: str  # student, teacher
    title: str
    content: str
    category: str  # discussion, challenge, event, resource
    likes: int = 0
    comments_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClubPostCreate(BaseModel):
    title: str
    content: str
    category: str

class ClubComment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str
    author_id: str
    author_name: str
    author_role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClubCommentCreate(BaseModel):
    content: str

class GroupCode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # Unique 6-character alphanumeric code
    teacher_id: str
    teacher_name: str
    group_name: str
    level: str
    max_students: int = 3
    current_students: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupCodeCreate(BaseModel):
    group_name: str
    level: str
    max_students: int = 3

class GroupMemberSimple(BaseModel):
    """Membre additionnel du groupe (juste nom et prénom)"""
    first_name: str
    last_name: str

class GroupRegistration(BaseModel):
    """Inscription de groupe - une personne principale + 1-2 personnes additionnelles"""
    # Personne principale (infos complètes)
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    country_code: str = "+33"
    level: str
    # Membres additionnels (juste nom/prénom)
    additional_members: List[GroupMemberSimple] = []
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None

class RegisterWithCode(BaseModel):
    code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    number_of_students: int = 2  # Nombre de personnes dans le groupe (2 ou 3)

class PromoCode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # Code promo (ex: KALAMA15)
    discount_percent: int  # Pourcentage de réduction (ex: 15)
    valid_until: datetime  # Date d'expiration
    max_uses: Optional[int] = None  # Nombre maximum d'utilisations (None = illimité)
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PromoCodeUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    promo_code_id: str
    promo_code: str
    user_email: str
    used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ValidatePromoCodeRequest(BaseModel):
    code: str

class ClubEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    event_date: datetime
    duration_minutes: int
    max_participants: int
    participants: list = []
    event_link: str = ""  # NEW: Lien vers l'événement (Zoom, Meet, etc.)
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClubEventCreate(BaseModel):
    title: str
    description: str
    event_date: str  # ISO format
    duration_minutes: int
    max_participants: int
    event_link: str = ""  # NEW: Lien vers l'événement

# ============ UTILITIES ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"verify_password: plain_len={len(plain_password)}, hash={hashed_password[:25]}..., result={result}")
        return result
    except Exception as e:
        logger.error(f"verify_password error: {e}")
        return False

def generate_welcome_letter_content(first_name: str, level: str, role: str, email: str, temp_password: str) -> str:
    """Generate welcome letter content based on user level and role"""
    if role == "teacher":
        return f"""Dear Professor,

We are delighted to welcome you to MYKALMAENGLISH, our online platform dedicated to English language learning. Your registration is now confirmed, and we look forward to having you join our community of teachers and learners.

Here are some details to help you get started:

Access to the Platform: You can log in to your account using the credentials below. You can also change your password in your profile settings.

Your Credentials:
📧 Email: {email}
🔑 Temporary Password: {temp_password}

Available Resources: Explore our digital library, KALAMATHÈQUE, along with other teaching materials designed to enhance your instruction.

Technical Support: If you have any questions or encounter any technical issues, please feel free to reach out to our support team at support@mykalmaenglish.com or mykalamaenglish@gmail.com.

Upcoming Events: Stay tuned for our webinars and workshops featured in the News section, where you can discover new teaching methods and connect with other professionals.

We wish you great success on your journey with MYKALMAENGLISH. Please do not hesitate to share your suggestions or questions with us.

Best regards,
DIAGNE Mansour
CEO of KalamaEnglish
Email: mykalamaenglish@gmail.com
Website: mykalamaenglish.com"""
    
    # Student letters based on level
    if level == "beginner":
        return f"""Hello {first_name},

Nous sommes ravis de vous accueillir sur MYKALMAENGLISH ! 🎉

Félicitations pour avoir fait le premier pas dans votre parcours d'apprentissage de l'anglais. En tant que débutant, vous trouverez que notre plateforme est conçue pour vous accompagner à chaque étape. Voici ce à quoi vous pouvez vous attendre :

Leçons interactives : un contenu engageant adapté aux débutants pour vous aider à construire une base solide en anglais.

Apprentissage flexible : accédez à vos cours à tout moment, partout, à votre propre rythme.

Communauté de soutien : rejoignez notre communauté dynamique d'apprenants et d'instructeurs qui sont là pour vous aider à réussir.

Vos identifiants de connexion :
📧 Email: {email}
🔑 Mot de passe provisoire: {temp_password}

Vos accès :
- Kalamathèque : Bibliothèque en ligne avec accès illimité pour lire des livres
- News : Section actualités et événements pour rester informé
- Profil : Changez votre mot de passe provisoire dans votre espace, partie Profil

Pour commencer, connectez-vous simplement à votre compte et explorez les cours disponibles. Si vous avez des questions ou avez besoin d'aide, n'hésitez pas à contacter notre équipe de support.

Nous vous souhaitons une expérience d'apprentissage enrichissante et agréable !

Cordialement,

L'équipe MYKALMAENGLISH"""
    
    elif level == "intermediate":
        return f"""Hello {first_name},

Nous sommes ravis de vous accueillir sur MYKALMAENGLISH ! Vous vous êtes inscrit avec succès à notre cours en ligne de niveau intermédiaire, et nous sommes impatients de vous accompagner dans votre apprentissage de la langue.

Leçons interactives : un contenu engageant adapté à votre niveau pour vous aider à approfondir vos connaissances en anglais.

Apprentissage flexible : accédez à vos cours à tout moment, partout, à votre propre rythme.

Communauté de soutien : rejoignez notre communauté dynamique d'apprenants et d'instructeurs qui sont là pour vous aider à réussir.

Vos identifiants de connexion :
📧 Email: {email}
🔑 Mot de passe provisoire: {temp_password}

Vos accès :
- Kalamathèque : Bibliothèque en ligne avec accès illimité pour lire des livres
- News : Section actualités et événements pour rester informé
- Profil : Changez votre mot de passe provisoire dans votre espace, partie Profil

Pour commencer, connectez-vous simplement à votre compte et explorez les cours disponibles. Si vous avez des questions ou avez besoin d'aide, n'hésitez pas à contacter notre équipe de support.

Sur MYKALMAENGLISH, vous trouverez une variété de ressources conçues pour améliorer vos compétences en anglais, notamment des leçons interactives, des exercices engageants et une communauté d'apprenants soudée. Nous vous encourageons à explorer la plateforme et à profiter pleinement de tout ce que nous offrons.

Nous vous souhaitons une expérience d'apprentissage enrichissante et agréable !

Cordialement,

L'équipe MYKALMAENGLISH"""
    
    else:  # advanced / Pack professionnel
        return f"""Hello {first_name},

Nous sommes ravis de vous accueillir sur MYKALMAENGLISH ! Vous avez franchi une étape importante pour améliorer vos compétences en anglais professionnel, et nous sommes impatients de vous accompagner dans cette aventure.

Notre programme de formation intensive et accélérée en anglais est conçu spécialement pour des professionnels comme vous. Voici ce que vous pouvez attendre :

Apprentissage complet : Engagez-vous avec un contenu adapté qui se concentre sur des applications concrètes.

Accès flexible : Apprenez à votre rythme grâce à notre plateforme en ligne, disponible à tout moment et de n'importe où.

Communauté de soutien : Connectez-vous avec d'autres apprenants et des instructeurs qui sont là pour vous soutenir.

Vos identifiants de connexion :
📧 Email: {email}
🔑 Mot de passe provisoire: {temp_password}

Vos accès :
- Kalamathèque : Bibliothèque en ligne avec accès illimité pour lire des livres
- News : Section actualités et événements pour rester informé
- Profil : Changez votre mot de passe provisoire dans votre espace, partie Profil

Pour commencer, veuillez vous connecter à votre compte et explorer les matériaux de cours. Si vous avez des questions ou avez besoin d'assistance, n'hésitez pas à contacter notre équipe de support.

Nous sommes impatients de vous voir progresser dans votre apprentissage de l'anglais !

Cordialement,

L'équipe MYKALMAENGLISH"""

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ TEST QUESTIONS ============

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

# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "KALAMAENGLISH API"}

# AUTH ROUTES
async def send_admin_notification_email(user_email: str, first_name: str, last_name: str, level: str):
    """
    Send email notification to admin when a new student registers
    """
    email_content = f"""
    NOUVELLE INSCRIPTION - My KALAMA ENGLISH
    
    Un nouvel étudiant s'est inscrit sur la plateforme :
    
    Nom complet: {first_name} {last_name}
    Email: {user_email}
    Niveau: {level}
    Date d'inscription: {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M')}
    
    Veuillez vous connecter au dashboard admin pour approuver cette inscription.
    
    Lien dashboard: {FRONTEND_URL}/admin
    """
    
    # TODO: Implement actual email sending to mykalamaenglish@gmail.com
    logger.info(f"Admin notification email for new registration: {user_email}")
    logger.info(email_content)
    return True

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (inactive until admin approves)
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        level=user_data.level,
        role="student",
        is_active=False,
        is_restricted=False,
        password_hash="",  # Will be set by admin
        preferred_slots=user_data.preferred_slots,
        referral_source=user_data.referral_source
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Send notification email to admin
    await email_service.send_admin_notification(
        user_data.email,
        user_data.first_name,
        user_data.last_name,
        user_data.level,
        user_data.phone
    )
    
    # Send confirmation email to student
    await email_service.send_registration_confirmation_email(
        user_data.email,
        user_data.first_name,
        user_data.last_name
    )
    
    return {"message": "Registration submitted. Please wait for admin approval."}

@api_router.post("/auth/register-group")
async def register_group(group_data: GroupRegistration):
    """Register a group - 1 person with full info + 1-2 additional members (name only)"""
    
    # Validate: must have at least 1 additional member for group registration
    if len(group_data.additional_members) == 0:
        raise HTTPException(status_code=400, detail="L'inscription de groupe nécessite au moins 2 personnes")
    
    if len(group_data.additional_members) > 2:
        raise HTTPException(status_code=400, detail="Maximum 3 personnes au total (vous + 2 autres)")
    
    # Check if email already exists
    existing = await db.users.find_one({"email": group_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà enregistrée")
    
    # Generate group ID
    group_id = str(uuid.uuid4())
    
    # Prepare group members list
    total_members = len(group_data.additional_members) + 1
    members_list = [
        {
            "first_name": group_data.first_name,
            "last_name": group_data.last_name,
            "is_main": True
        }
    ]
    
    for member in group_data.additional_members:
        members_list.append({
            "first_name": member.first_name,
            "last_name": member.last_name,
            "is_main": False
        })
    
    # Create ONE pending group registration (not activated yet)
    group_registration = {
        "id": group_id,
        "email": group_data.email,
        "phone": group_data.phone,
        "level": group_data.level,
        "role": "student",
        "course_type": "group",
        "is_active": False,
        "is_approved": False,  # Admin needs to approve
        "password_hash": "",
        "temporary_password": None,  # Will be set by admin when generating magic code
        "total_members": total_members,
        "members": members_list,
        "assigned_teacher": None,  # Will be set by admin
        "preferred_slots": group_data.preferred_slots or "",
        "referral_source": group_data.referral_source or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "magic_code_generated": False
    }
    
    await db.users.insert_one(group_registration)
    
    # Send notification to admin
    members_names = ", ".join([f"{m['first_name']} {m['last_name']}" for m in members_list])
    await email_service.send_admin_notification(
        group_data.email,
        f"Groupe de {total_members}",
        members_names,
        group_data.level,
        group_data.phone
    )
    
    logger.info(f"Group registration submitted: {group_data.email} with {total_members} members")
    
    return {
        "message": f"Inscription de groupe envoyée avec succès pour {total_members} personne(s)! En attente d'approbation par l'administrateur.",
        "group_id": group_id,
        "total_members": total_members,
        "members_names": members_names
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user:
        logger.warning(f"Login attempt - user not found: {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.info(f"Login attempt for: {credentials.email}, role: {user.get('role')}, is_active: {user.get('is_active')}")
    
    if not user.get('is_active'):
        raise HTTPException(status_code=403, detail="Account not activated yet. Please wait for admin approval.")
    
    # Check if student access is restricted
    if user.get('role') == 'student' and user.get('is_restricted', False):
        raise HTTPException(status_code=403, detail="Your access has been restricted. Please contact the administrator.")
    
    # Verify password
    verified = verify_password(credentials.password, user['password_hash'])
    logger.info(f"Password verification for {credentials.email}: {verified}")
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_access_token({"sub": user['id'], "role": user['role']})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "role": user['role'],
            "level": user.get('level')
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/change-password")
async def change_password(password_data: PasswordChange, current_user: dict = Depends(get_current_user)):
    # Verify old password
    if not verify_password(password_data.old_password, current_user['password_hash']):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Update password
    new_hash = hash_password(password_data.new_password)
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {
            "password_hash": new_hash, 
            "temporary_password": None,
            "current_password_plain": password_data.new_password,  # Store plain password for admin visibility
            "password_changed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Password changed by user {current_user['id']} - plain text stored for admin")
    return {"message": "Password changed successfully"}

# ADMIN ROUTES
@api_router.get("/admin/pending-registrations")
async def get_pending_registrations(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    registrations = await db.users.find(
        {"role": "student", "is_active": False},
        {"_id": 0}
    ).to_list(1000)
    
    return registrations

# Email sending is now handled by email_service.py

@api_router.post("/admin/approve-registration/{user_id}")
async def approve_registration(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate temporary password
    temp_password = f"Kalama{user_id[:6]}"
    password_hash = hash_password(temp_password)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": True, "password_hash": password_hash, "temporary_password": temp_password}}
    )
    
    # Send level-based welcome email
    await email_service.send_level_based_welcome_email(
        user['email'],
        user['first_name'],
        user.get('level', 'beginner'),  # Get level from user data, default to beginner
        temp_password
    )
    
    # Create welcome letter in database
    letter_content = generate_welcome_letter_content(
        user['first_name'],
        user.get('level', 'beginner'),
        'student',
        user['email'],
        temp_password
    )
    
    welcome_letter = WelcomeLetter(
        user_id=user_id,
        user_email=user['email'],
        user_name=f"{user['first_name']} {user['last_name']}",
        user_level=user.get('level', 'beginner'),
        user_role='student',
        temp_password=temp_password,
        content=letter_content
    )
    
    letter_doc = welcome_letter.model_dump()
    letter_doc['created_at'] = letter_doc['created_at'].isoformat()
    await db.welcome_letters.insert_one(letter_doc)
    
    logger.info(f"User {user_id} approved, email and welcome letter created (Level: {user.get('level', 'beginner')})")
    
    return {
        "message": "User approved, welcome email and letter created",
        "email": user['email'],
        "temporary_password": temp_password,
        "level": user.get('level', 'beginner')
    }

@api_router.post("/admin/create-teacher")
async def create_teacher(teacher_data: TeacherCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Create teacher email
    email = f"{teacher_data.first_name.lower()}.{teacher_data.last_name.lower()}@mykalamaenglish.com"
    
    # Check if exists
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Teacher email already exists")
    
    # Generate password
    temp_password = f"Teacher{uuid.uuid4().hex[:8]}"
    password_hash = hash_password(temp_password)
    
    teacher = User(
        email=email,
        first_name=teacher_data.first_name,
        last_name=teacher_data.last_name,
        phone="",
        role="teacher",
        is_active=True,
        password_hash=password_hash,
        temporary_password=temp_password
    )
    
    doc = teacher.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Create welcome letter for teacher
    letter_content = generate_welcome_letter_content(
        teacher_data.first_name,
        'teacher',  # level parameter, but not used for teachers
        'teacher',
        email,
        temp_password
    )
    
    welcome_letter = WelcomeLetter(
        user_id=teacher.id,
        user_email=email,
        user_name=f"{teacher_data.first_name} {teacher_data.last_name}",
        user_level='teacher',
        user_role='teacher',
        temp_password=temp_password,
        content=letter_content
    )
    
    letter_doc = welcome_letter.model_dump()
    letter_doc['created_at'] = letter_doc['created_at'].isoformat()
    await db.welcome_letters.insert_one(letter_doc)
    
    logger.info(f"Teacher {teacher.id} created with welcome letter")
    
    return {
        "message": "Teacher created with welcome letter",
        "email": email,
        "temporary_password": temp_password
    }

@api_router.get("/admin/all-users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.post("/admin/assign-teacher/{student_id}/{teacher_id}")
async def assign_teacher(student_id: str, teacher_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.users.update_one(
        {"id": student_id},
        {"$set": {"assigned_teacher": teacher_id}}
    )
    
    return {"message": "Teacher assigned successfully"}

@api_router.delete("/admin/delete-student/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(get_current_user)):
    """Admin soft-deletes a student - moves to trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = await db.users.find_one({"id": student_id, "role": "student"}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Add deletion metadata
    student['deleted_at'] = datetime.now(timezone.utc).isoformat()
    student['deleted_by'] = current_user['id']
    
    # Move to trash collection
    await db.deleted_users.insert_one(student)
    
    # Delete from main collection
    await db.users.delete_one({"id": student_id})
    
    # NOTE: We keep related data for potential restoration
    
    logger.info(f"Student soft-deleted: {student['email']}")
    return {"message": "Student moved to trash successfully"}

@api_router.post("/admin/restrict-student/{student_id}")
async def restrict_student(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = await db.users.find_one({"id": student_id, "role": "student"}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Toggle restriction status
    new_status = not student.get('is_restricted', False)
    await db.users.update_one(
        {"id": student_id},
        {"$set": {"is_restricted": new_status}}
    )
    
    action = "restricted" if new_status else "unrestricted"
    logger.info(f"Student {action}: {student['email']}")
    
    return {
        "message": f"Student access {'restricted' if new_status else 'restored'} successfully",
        "is_restricted": new_status
    }

@api_router.post("/admin/restrict-user/{user_id}")
async def restrict_user_generic(user_id: str, current_user: dict = Depends(get_current_user)):
    """Generic endpoint to restrict/unrestrict any user (student or teacher)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot restrict admin")
    
    # Toggle restriction status
    new_status = not user.get('is_restricted', False)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_restricted": new_status}}
    )
    
    action = "restricted" if new_status else "unrestricted"
    logger.info(f"{user['role'].title()} {action}: {user['email']}")
    
    return {
        "message": f"Access {'restricted' if new_status else 'restored'} successfully",
        "is_restricted": new_status
    }

@api_router.get("/admin/session-notifications")
async def get_session_notifications(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    notifications = await db.admin_notifications.find(
        {"type": "session_completed"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    

@api_router.get("/pricing")
async def get_pricing():
    """Get current pricing - Public endpoint"""
    pricing = await db.pricing.find_one({"id": "pricing"}, {"_id": 0})
    if not pricing:
        # Default pricing structure matching frontend expectations
        return {
            "kkid_eur": 30,
            "kkid_discount": 0,
            "beginner_eur": 76,
            "beginner_discount": 0,
            "intermediate_eur": 90,
            "intermediate_discount": 0,
            "advanced_eur": 102,
            "advanced_discount": 0
        }
    return pricing

@api_router.post("/admin/update-prices")
async def update_prices(prices: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Store prices in database with discount support
    prices_doc = {
        "id": "pricing",
        **prices,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user['id']
    }
    
    await db.pricing.replace_one({"id": "pricing"}, prices_doc, upsert=True)
    logger.info(f"Prices updated by admin {current_user['id']}")
    return {"message": "Prices updated successfully"}

@api_router.post("/admin/send-document")
async def admin_send_document(doc_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    document = {
        "id": str(uuid.uuid4()),
        "from_user_id": current_user['id'],
        "from_user_role": "admin",
        "to_user_id": doc_data['recipient_id'],
        "to_user_role": doc_data['recipient_type'],
        "title": doc_data['title'],
        "description": doc_data.get('description', ''),
        "file_url": doc_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(document)
    
    # Create notification
    await create_notification(
        user_id=doc_data['recipient_id'],
        notification_type="new_document",
        data={"message": f"Nouveau document de l'admin: {doc_data['title']}"}
    )
    
    logger.info(f"Document sent by admin to {doc_data['recipient_type']}: {doc_data['recipient_id']}")
    return {"message": "Document sent successfully"}

@api_router.get("/teacher/documents-from-admin")
async def get_teacher_documents_from_admin(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    documents = await db.documents.find(
        {"to_user_id": current_user['id'], "from_user_role": "admin"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return documents

@api_router.post("/teacher/send-document-to-admin")
async def teacher_send_document_to_admin(doc_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher sends a document to admin"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get admin user
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    document = {
        "id": str(uuid4()),
        "from_user_id": current_user['id'],
        "from_user_role": "teacher",
        "to_user_id": admin['id'],
        "to_user_role": "admin",
        "title": doc_data['title'],
        "description": doc_data.get('description', ''),
        "file_url": doc_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(document)
    
    # Create notification for admin
    await create_notification(
        user_id=admin['id'],
        notification_type="new_document",
        data={"message": f"Nouveau document du professeur {current_user['first_name']}: {doc_data['title']}"}
    )
    
    logger.info(f"Document sent by teacher {current_user['id']} to admin")
    return {"message": "Document sent to admin successfully"}

@api_router.post("/teacher/send-kkid-video")
async def teacher_send_kkid_video(video_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher uploads and sends a video to a specific K-Kid student"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Verify the student exists and is a K-Kid
    student = await db.users.find_one({"id": video_data['student_id']}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student.get('level') != 'kkid':
        raise HTTPException(status_code=400, detail="Only K-Kid students can receive these videos")
    
    video = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "teacher_name": f"{current_user['first_name']} {current_user['last_name']}",
        "student_id": video_data['student_id'],
        "student_name": f"{student['first_name']} {student['last_name']}",
        "title": video_data['title'],
        "description": video_data.get('description', ''),
        "video_url": video_data['video_url'],
        "thumbnail_url": video_data.get('thumbnail_url', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.kkid_videos.insert_one(video)
    
    # Create notification for the K-Kid student
    await create_notification(
        user_id=video_data['student_id'],
        notification_type="new_video",
        data={"message": f"Nouvelle vidéo de {current_user['first_name']}: {video_data['title']}"}
    )
    
    logger.info(f"K-Kid video uploaded by teacher {current_user['id']} for student {video_data['student_id']}: {video_data['title']}")
    return {"message": "Vidéo envoyée avec succès à l'élève K-Kid", "video": video}

@api_router.get("/kkid/videos")
async def get_kkid_videos(current_user: dict = Depends(get_current_user)):
    """Get K-Kid videos for current user"""
    if current_user.get('level') != 'kkid' and current_user['role'] not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Access restricted to K-Kids, teachers, and admins")
    
    # K-Kids only see their own videos
    if current_user.get('level') == 'kkid':
        videos = await db.kkid_videos.find(
            {"student_id": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(1000)
    # Teachers and admins see all videos they sent/manage
    else:
        if current_user['role'] == 'teacher':
            videos = await db.kkid_videos.find(
                {"teacher_id": current_user['id']},
                {"_id": 0}
            ).sort("created_at", -1).to_list(1000)
        else:  # admin
            videos = await db.kkid_videos.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return videos

@api_router.delete("/teacher/delete-kkid-video/{video_id}")
async def delete_kkid_video(video_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a K-Kid video"""
    if current_user['role'] not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")
    
    result = await db.kkid_videos.delete_one({"id": video_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    logger.info(f"K-Kid video {video_id} deleted by {current_user['role']} {current_user['id']}")
    return {"message": "Vidéo supprimée avec succès"}

@api_router.get("/admin/documents-from-teachers")
async def get_admin_documents_from_teachers(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    documents = await db.documents.find(
        {"to_user_role": "admin", "from_user_role": "teacher"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with teacher info
    for doc in documents:
        teacher = await db.users.find_one(
            {"id": doc['from_user_id']},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        if teacher:
            doc['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
            doc['teacher_email'] = teacher['email']

@api_router.get("/admin/received-documents")
async def get_admin_received_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents sent to admin from teachers and students"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    documents = await db.documents.find(
        {"to_user_role": "admin"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with sender info
    for doc in documents:
        sender = await db.users.find_one(
            {"id": doc['from_user_id']},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "role": 1}
        )
        if sender:
            doc['sender_name'] = f"{sender['first_name']} {sender['last_name']}"
            doc['sender_email'] = sender['email']
            doc['sender_role'] = sender['role']
    
    return documents

@api_router.delete("/admin/delete-document/{document_id}")
async def delete_admin_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document received by admin"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.documents.delete_one({"id": document_id, "to_user_role": "admin"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    logger.info(f"Document {document_id} deleted by admin {current_user['id']}")
    return {"message": "Document supprimé avec succès"}

@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document (for students and teachers)"""
    # Check if document belongs to current user (either as sender or recipient)
    document = await db.documents.find_one({"id": document_id}, {"_id": 0})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check authorization (compatible with both old and new document formats)
    is_authorized = False
    
    # Check if user is recipient (support both formats)
    if document.get('to_user_id') == current_user['id'] or document.get('recipient_id') == current_user['id']:
        is_authorized = True
    
    # Check if user is sender (support both formats)
    if document.get('from_user_id') == current_user['id'] or document.get('teacher_id') == current_user['id']:
        is_authorized = True
    
    # Admin can delete any document
    if current_user['role'] == 'admin':
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    result = await db.documents.delete_one({"id": document_id})
    logger.info(f"Document {document_id} deleted by user {current_user['id']}")
    return {"message": "Document supprimé avec succès"}
    
    return documents

@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    document = await db.documents.find_one({"id": document_id}, {"_id": 0})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has permission to delete
    if document['from_user_id'] != current_user['id'] and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    await db.documents.delete_one({"id": document_id})
    logger.info(f"Document {document_id} deleted by {current_user['id']}")
    return {"message": "Document deleted successfully"}

# Notification routes
@api_router.get("/notifications/my-notifications")
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return notifications

@api_router.post("/notifications/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

async def create_notification(user_id: str, notification_type: str, data: dict):
    """Helper function to create notifications"""
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": notification_type,
        **data,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    logger.info(f"Notification created for user {user_id}: {notification_type}")

# Admin delete user (teacher or student)
@api_router.delete("/admin/delete-user/{user_id}")
async def admin_delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Admin soft-deletes a user (student/teacher) - moves to trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get the user first
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot delete admin")
    
    # Add deletion metadata
    user['deleted_at'] = datetime.now(timezone.utc).isoformat()
    user['deleted_by'] = current_user['id']
    
    # Move to trash collection
    await db.deleted_users.insert_one(user)
    
    # Delete from main collection
    await db.users.delete_one({"id": user_id})
    
    # NOTE: We keep related data for potential restoration
    
    logger.info(f"User soft-deleted by admin: {user['email']}")
    return {"message": f"{user['role'].capitalize()} moved to trash successfully"}

@api_router.get("/admin/trash")
async def get_trash(current_user: dict = Depends(get_current_user)):
    """Get all deleted users (trash)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deleted_users = await db.deleted_users.find({}, {"_id": 0}).to_list(1000)
    return deleted_users

@api_router.post("/admin/restore-user/{user_id}")
async def restore_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Restore a deleted user from trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find user in trash
    user = await db.deleted_users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found in trash")
    
    # Remove deletion metadata
    user.pop('deleted_at', None)
    user.pop('deleted_by', None)
    
    # Restore to main collection
    await db.users.insert_one(user)
    
    # Remove from trash
    await db.deleted_users.delete_one({"id": user_id})
    
    logger.info(f"User restored by admin: {user['email']}")
    return {"message": f"{user['role'].capitalize()} restored successfully"}

@api_router.delete("/admin/permanent-delete/{user_id}")
async def permanent_delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Permanently delete a user from trash"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Delete from trash
    result = await db.deleted_users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found in trash")
    
    logger.info(f"User permanently deleted by admin: {user_id}")
    return {"message": "User permanently deleted"}

@api_router.get("/admin/users")
async def get_users_by_role(role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all users, optionally filtered by role"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

# Endpoint en doublon supprimé - le changement de mot de passe se fait via la route ligne 339

# ADMIN: Reset user password (SECURE)
@api_router.post("/admin/reset-user-password/{user_id}")
async def admin_reset_user_password(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot reset admin password")
    
    # Generate a secure temporary password
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    temporary_password = ''.join(secrets.choice(alphabet) for i in range(10))
    
    # Hash the temporary password
    hashed = hash_password(temporary_password)
    
    # Update user with temporary password
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": hashed,
            "temporary_password": temporary_password,
            "password_reset_at": datetime.now(timezone.utc).isoformat(),
            "password_reset_by": current_user['id']
        }}
    )
    
    # Send email to user with the temporary password
    try:
        from email_service import send_password_reset_email
        await send_password_reset_email(
            to_email=user['email'],
            user_name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            temporary_password=temporary_password
        )
        email_sent = True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        email_sent = False
    
    # Create notification for user
    # (notification logic can be added here if needed)

# ADMIN: Generate Magic Code for Group Registration
@api_router.post("/admin/generate-magic-code/{user_id}")
async def admin_generate_magic_code(
    user_id: str,
    teacher_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Admin generates a magic code for a group registration and assigns to teacher"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find the group registration
    group_reg = await db.users.find_one({"id": user_id, "course_type": "group"}, {"_id": 0})
    if not group_reg:
        raise HTTPException(status_code=404, detail="Inscription de groupe non trouvée")
    
    if group_reg.get('magic_code_generated'):
        raise HTTPException(status_code=400, detail="Un code magique a déjà été généré pour ce groupe")
    
    # Verify teacher exists
    teacher = await db.users.find_one({"id": teacher_id, "role": "teacher"}, {"_id": 0})
    if not teacher:
        raise HTTPException(status_code=404, detail="Professeur non trouvé")
    
    # Generate unique magic code (8 characters)
    magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure code is unique
    while await db.users.find_one({"temporary_password": magic_code}, {"_id": 0}):
        magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Get the main member's name from the members array
    main_member = next((m for m in group_reg['members'] if m.get('is_main')), group_reg['members'][0])
    
    # Update the group registration
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_active": True,  # Activate the account
            "is_approved": True,  # Mark as approved
            "password_hash": pwd_context.hash(magic_code),  # Hash the magic code
            "temporary_password": magic_code,  # Store for display
            "assigned_teacher": teacher_id,
            "magic_code_generated": True,
            "magic_code_generated_at": datetime.now(timezone.utc).isoformat(),
            "magic_code_generated_by": current_user['id'],
            # Add the main member's name for login compatibility
            "first_name": main_member['first_name'],
            "last_name": main_member['last_name']
        }}
    )
    
    logger.info(f"Magic code {magic_code} generated for group {user_id} by admin {current_user['id']}")
    
    # Get member names for response
    members_names = ", ".join([f"{m['first_name']} {m['last_name']}" for m in group_reg['members']])
    
    return {
        "message": "Code magique généré avec succès",
        "magic_code": magic_code,
        "group_id": user_id,
        "email": group_reg['email'],
        "total_members": group_reg['total_members'],
        "members_names": members_names,
        "teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
        "teacher_email": teacher['email']
    }

# ADMIN: Get pending group registrations
@api_router.get("/admin/pending-group-registrations")
async def get_pending_group_registrations(current_user: dict = Depends(get_current_user)):
    """Get all pending group registrations waiting for magic code"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pending_groups = await db.users.find(
        {
            "course_type": "group",
            "is_approved": False,
            "magic_code_generated": False
        },
        {"_id": 0}
    ).to_list(1000)
    
    return pending_groups

@api_router.post("/admin/reset-password/{user_id}")
async def admin_reset_password(user_id: str, current_user: dict = Depends(get_current_user)):
    """Admin resets password for a user"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"Password reset by admin {current_user['email']} for user {user['email']}")
    
    return {
        "message": "Password reset successfully",
        "temporary_password": temporary_password,
        "email_sent": email_sent,
        "note": "User will receive email with temporary password. They should change it after login."
    }

# News routes (admin only can create, everyone can read)
@api_router.get("/news/all")
async def get_all_news():
    news = await db.news.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return news

@api_router.post("/admin/create-news")
async def create_news(news_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    news_item = {
        "id": str(uuid.uuid4()),
        "title": news_data['title'],
        "content": news_data['content'],
        "type": news_data.get('type', 'article'),  # article, video, link, publication
        "url": news_data.get('url', ''),
        "image_url": news_data.get('image_url', ''),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.news.insert_one(news_item)
    
    # Notify all users
    all_users = await db.users.find({"role": {"$in": ["student", "teacher"]}}, {"_id": 0, "id": 1}).to_list(1000)
    for user in all_users:
        await create_notification(user['id'], 'new_news', {
            "title": news_data['title'],
            "message": f"Nouvelle actualité: {news_data['title']}"
        })
    
    logger.info(f"News created by admin: {news_data['title']}")
    return {"message": "News published successfully"}

@api_router.delete("/admin/delete-news/{news_id}")
async def delete_news(news_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.news.delete_one({"id": news_id})
    return {"message": "News deleted"}

# Contact form route (public)
@api_router.post("/contact/send")
async def send_contact_email(contact_data: dict):
    """
    Handle contact form submissions from homepage
    Sends email to mykalamaenglish@gmail.com
    """
    name = contact_data.get('name', '')
    email = contact_data.get('email', '')
    message = contact_data.get('message', '')
    
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    # Validate email format
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Send email to admin
    admin_email = "mykalamaenglish@gmail.com"
    subject = f"Nouveau message de contact - {name}"
    
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
            .message-box {{ background: white; padding: 20px; border-left: 4px solid #14b8a6; 
                           margin: 20px 0; border-radius: 5px; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📧 Nouveau Message de Contact</h1>
            </div>
            <div class="content">
                <p><strong>Vous avez reçu un nouveau message depuis le formulaire de contact du site web.</strong></p>
                
                <div class="message-box">
                    <p><strong>De :</strong> {name}</p>
                    <p><strong>Email :</strong> {email}</p>
                    <p><strong>Date :</strong> {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}</p>
                </div>
                
                <div class="message-box">
                    <h3>Message :</h3>
                    <p>{message}</p>
                </div>
                
                <p><strong>Pour répondre :</strong> Envoyez votre réponse directement à <a href="mailto:{email}">{email}</a></p>
                
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
    NOUVEAU MESSAGE DE CONTACT - My KALAMA ENGLISH
    
    De: {name}
    Email: {email}
    Date: {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}
    
    MESSAGE:
    {message}
    
    Pour répondre, envoyez votre réponse directement à {email}
    """
    
    try:
        from email_service import email_service
        success = await email_service._send_email(admin_email, subject, html_body, text_body)
        
        if success:
            logger.info(f"Contact form email sent from {email}")
            return {"message": "Message sent successfully"}
        else:
            logger.warning(f"Contact form email logged (not sent) from {email}")
            return {"message": "Message received and will be processed"}
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending message")

# Admin annuaire (directory)
@api_router.get("/admin/directory")
async def get_directory(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find(
        {"role": {"$in": ["teacher", "student"]}, "is_active": True},
        {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1, "phone": 1, "role": 1}
    ).to_list(1000)
    
    return users

# Teacher availability routes
@api_router.post("/teacher/set-availability")
async def set_teacher_availability(availability_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # availability_data format: { "monday": ["09:00", "10:00", "14:00"], "tuesday": [...], ... }
    availability = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "availability": availability_data['availability'],
        "week_start": availability_data.get('week_start', datetime.now(timezone.utc).isoformat()),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Replace existing availability
    await db.teacher_availability.delete_many({"teacher_id": current_user['id']})
    await db.teacher_availability.insert_one(availability)
    
    logger.info(f"Availability set by teacher {current_user['id']}")
    return {"message": "Availability updated successfully"}

@api_router.get("/teacher/my-availability")
async def get_my_availability(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    availability = await db.teacher_availability.find_one(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    )
    
    return availability or {"availability": {}}

# ============ GROUP CODE ENDPOINTS ============

import random
import string

def generate_unique_code():
    """Generate a unique 6-character alphanumeric code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@api_router.post("/teacher/create-group-code")
async def create_group_code(code_data: GroupCodeCreate, current_user: dict = Depends(get_current_user)):
    """Teacher creates a group code for students to join"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Generate unique code
    code = generate_unique_code()
    
    # Ensure code is unique
    while await db.group_codes.find_one({"code": code}, {"_id": 0}):
        code = generate_unique_code()
    
    # Create group code
    group_code = GroupCode(
        code=code,
        teacher_id=current_user['id'],
        teacher_name=f"{current_user['first_name']} {current_user['last_name']}",
        group_name=code_data.group_name,
        level=code_data.level,
        max_students=code_data.max_students,
        current_students=0,
        is_active=True
    )
    
    doc = group_code.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.group_codes.insert_one(doc)
    
    # Retrieve the inserted document without _id
    created_code = await db.group_codes.find_one({"id": group_code.id}, {"_id": 0})
    
    logger.info(f"Group code {code} created by teacher {current_user['id']}")
    
    return {
        "message": "Code de groupe créé avec succès",
        "group_code": created_code
    }

@api_router.get("/teacher/my-group-codes")
async def get_my_group_codes(current_user: dict = Depends(get_current_user)):
    """Get all group codes created by the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    codes = await db.group_codes.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    return codes

@api_router.put("/teacher/toggle-group-code/{code_id}")
async def toggle_group_code(code_id: str, current_user: dict = Depends(get_current_user)):
    """Activate or deactivate a group code"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    code = await db.group_codes.find_one(
        {"id": code_id, "teacher_id": current_user['id']},
        {"_id": 0}
    )
    
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    new_status = not code['is_active']
    
    await db.group_codes.update_one(
        {"id": code_id},
        {"$set": {"is_active": new_status}}
    )
    
    logger.info(f"Group code {code['code']} toggled to {new_status} by teacher {current_user['id']}")
    
    return {
        "message": f"Code {'activé' if new_status else 'désactivé'} avec succès",
        "is_active": new_status
    }

@api_router.get("/teacher/pending-group-students")
async def get_pending_group_students(current_user: dict = Depends(get_current_user)):
    """Get students assigned to teacher waiting for magic code generation"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Find students assigned to this teacher, with course_type='group' and no magic code yet
    students = await db.users.find(
        {
            "assigned_teacher": current_user['id'],
            "course_type": "group",
            "magic_code_generated": {"$ne": True}
        },
        {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1, "members": 1, "level": 1, "created_at": 1}
    ).to_list(1000)
    
    logger.info(f"Teacher {current_user['id']} retrieved {len(students)} pending group students")
    
    return students

@api_router.post("/teacher/generate-group-magic-code")
async def generate_group_magic_code(
    data: GenerateGroupMagicCode,
    current_user: dict = Depends(get_current_user)
):
    """Teacher generates a magic code for selected group students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    if not data.student_ids or len(data.student_ids) == 0:
        raise HTTPException(status_code=400, detail="Veuillez sélectionner au moins un étudiant")
    
    # Verify all students belong to this teacher and are pending
    logger.info(f"Searching for students with IDs: {data.student_ids}, teacher: {current_user['id']}")
    students = await db.users.find(
        {
            "id": {"$in": data.student_ids},
            "assigned_teacher": current_user['id'],
            "course_type": "group",
            "magic_code_generated": {"$ne": True}
        },
        {"_id": 0}
    ).to_list(1000)
    
    logger.info(f"Found {len(students)} students matching criteria (expected {len(data.student_ids)})")
    
    if len(students) != len(data.student_ids):
        raise HTTPException(
            status_code=400, 
            detail="Certains étudiants ne sont pas valides ou ont déjà un code"
        )
    
    # Generate unique magic code (8 characters)
    magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure code is unique
    while await db.users.find_one({"temporary_password": magic_code}, {"_id": 0}):
        magic_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Update all selected students with the same magic code
    hashed_password = pwd_context.hash(magic_code)
    
    for student in students:
        # Get main member info for login compatibility
        main_member = next((m for m in student.get('members', []) if m.get('is_main')), student.get('members', [{}])[0] if student.get('members') else {})
        
        await db.users.update_one(
            {"id": student['id']},
            {"$set": {
                "is_active": True,
                "is_approved": True,
                "password_hash": hashed_password,
                "temporary_password": magic_code,
                "magic_code_generated": True,
                "magic_code_generated_at": datetime.now(timezone.utc).isoformat(),
                "magic_code_generated_by": current_user['id'],
                "group_magic_code_name": data.group_name,
                "first_name": main_member.get('first_name', student.get('first_name', '')),
                "last_name": main_member.get('last_name', student.get('last_name', ''))
            }}
        )
    
    logger.info(f"Magic code {magic_code} generated for {len(students)} students in group '{data.group_name}' by teacher {current_user['id']}")
    
    # Create notification for admin
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0, "id": 1})
    if admin:
        student_names = ", ".join([
            f"{s.get('first_name', '')} {s.get('last_name', '')}" 
            for s in students
        ])
        await create_notification(
            admin['id'],
            'group_code_generated',
            {
                'teacher_name': f"{current_user['first_name']} {current_user['last_name']}",
                'group_name': data.group_name,
                'magic_code': magic_code,
                'student_count': len(students),
                'student_names': student_names
            }
        )
    
    return {
        "success": True,
        "magic_code": magic_code,
        "group_name": data.group_name,
        "student_count": len(students),
        "students": [
            {
                "id": s['id'],
                "name": f"{s.get('first_name', '')} {s.get('last_name', '')}",
                "email": s['email']
            }
            for s in students
        ]
    }

@api_router.get("/teacher/my-generated-groups")
async def get_my_generated_groups(current_user: dict = Depends(get_current_user)):
    """Get all groups with magic codes generated by this teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Find all students where this teacher generated their magic code
    groups = await db.users.find(
        {
            "magic_code_generated_by": current_user['id'],
            "magic_code_generated": True,
            "course_type": "group"
        },
        {"_id": 0}
    ).to_list(1000)
    
    # Group by magic code
    grouped = {}
    for student in groups:
        code = student.get('temporary_password', '')
        if code not in grouped:
            grouped[code] = {
                "magic_code": code,
                "group_name": student.get('group_magic_code_name', 'Groupe sans nom'),
                "created_at": student.get('magic_code_generated_at', ''),
                "students": []
            }
        
        grouped[code]['students'].append({
            "id": student['id'],
            "name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
            "email": student['email'],
            "level": student.get('level', ''),
            "members": student.get('members', [])
        })
    
    # Convert to list and sort by creation date
    result = list(grouped.values())
    result.sort(key=lambda x: x['created_at'], reverse=True)
    
    return result


@api_router.get("/auth/validate-code/{code}")
async def validate_group_code(code: str):
    """Validate a group code and return group information (public endpoint)"""
    group_code = await db.group_codes.find_one(
        {"code": code.upper()},
        {"_id": 0}
    )
    
    if not group_code:
        raise HTTPException(status_code=404, detail="Code invalide")
    
    if not group_code['is_active']:
        raise HTTPException(status_code=400, detail="Ce code n'est plus actif")
    
    if group_code['current_students'] >= group_code['max_students']:
        raise HTTPException(status_code=400, detail="Ce groupe est complet")
    
    return {
        "valid": True,
        "group_name": group_code['group_name'],
        "teacher_name": group_code['teacher_name'],
        "level": group_code['level'],
        "available_spots": group_code['max_students'] - group_code['current_students']
    }

@api_router.post("/auth/register-with-code")
async def register_with_code(registration: RegisterWithCode):
    """Register a GROUP account with a shared login code"""
    # Validate code
    group_code = await db.group_codes.find_one(
        {"code": registration.code.upper()},
        {"_id": 0}
    )
    
    if not group_code:
        raise HTTPException(status_code=404, detail="Code invalide")
    
    if not group_code['is_active']:
        raise HTTPException(status_code=400, detail="Ce code n'est plus actif")
    
    # Check if there's enough space for this group
    remaining_spots = group_code['max_students'] - group_code['current_students']
    if remaining_spots < registration.number_of_students:
        raise HTTPException(
            status_code=400, 
            detail=f"Pas assez de places disponibles. Places restantes: {remaining_spots}"
        )
    
    # Check if email already exists
    existing = await db.users.find_one({"email": registration.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà enregistrée")
    
    # Generate unique shared login code (8 characters)
    shared_login_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure code is unique
    while await db.users.find_one({"temporary_password": shared_login_code}, {"_id": 0}):
        shared_login_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Create ONE group account for all members
    user = User(
        email=registration.email,
        first_name=registration.first_name,
        last_name=registration.last_name,
        phone=registration.phone,
        level=group_code['level'],
        role="student",
        is_active=False,  # Will be activated by admin
        is_restricted=False,
        password_hash=pwd_context.hash(shared_login_code),  # Hash the shared code
        temporary_password=shared_login_code,  # Store it for display
        assigned_teacher=group_code['teacher_id']
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['group_code'] = registration.code.upper()
    doc['group_id'] = group_code['id']
    doc['course_type'] = 'group'
    doc['number_of_students'] = registration.number_of_students  # Track group size
    
    await db.users.insert_one(doc)
    
    # Increment student count by the number of students in this group
    await db.group_codes.update_one(
        {"id": group_code['id']},
        {"$inc": {"current_students": registration.number_of_students}}
    )
    
    # Send notification to admin
    await email_service.send_admin_notification(
        registration.email,
        f"{registration.first_name} {registration.last_name} (Groupe de {registration.number_of_students})",
        registration.last_name,
        group_code['level'],
        registration.phone
    )
    
    logger.info(f"Group account created with code {registration.code.upper()}: {registration.email} ({registration.number_of_students} students)")
    
    return {
        "message": "Inscription envoyée avec succès! Voici votre code de connexion partagé.",
        "group_name": group_code['group_name'],
        "teacher_name": group_code['teacher_name'],
        "shared_login_code": shared_login_code,  # Return the code to display to user
        "email": registration.email,
        "number_of_students": registration.number_of_students
    }


@api_router.get("/admin/all-teacher-availability")
async def get_all_teacher_availability(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all teachers with their availability
    teachers = await db.users.find({"role": "teacher"}, {"_id": 0}).to_list(1000)
    
    result = []
    for teacher in teachers:
        availability = await db.teacher_availability.find_one(
            {"teacher_id": teacher['id']},
            {"_id": 0}
        )
        result.append({
            "teacher_id": teacher['id'],
            "teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
            "email": teacher['email'],
            "availability": availability.get('availability', {}) if availability else {}
        })
    
    return result

    
    await db.admin_documents.insert_one(document)
    logger.info(f"Document sent by admin to {doc_data['recipient_type']} {doc_data['recipient_id']}")
    return {"message": "Document sent successfully"}

    return notifications


# TEST ROUTES
@api_router.get("/tests/{level}")
async def get_test(level: str):
    if level not in TEST_QUESTIONS:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Return questions without correct answers
    questions = [{"id": q["id"], "question": q["question"], "options": q["options"]} 
                 for q in TEST_QUESTIONS[level]]
    return {"level": level, "questions": questions}

@api_router.post("/tests/submit")
async def submit_test(submission: TestSubmission):
    if submission.level not in TEST_QUESTIONS:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Calculate score
    correct_answers = TEST_QUESTIONS[submission.level]
    score = 0
    for answer in submission.answers:
        correct = next((q for q in correct_answers if q["id"] == answer["question_id"]), None)
        if correct and correct["correct"] == answer["selected_option"]:
            score += 1
    
    # Save result
    result = TestResult(
        user_id=None,
        level=submission.level,
        score=score,
        total_questions=len(submission.answers),
        answers=submission.answers
    )
    
    doc = result.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.test_results.insert_one(doc)
    
    return {
        "score": score,
        "total": len(submission.answers),
        "percentage": round((score / len(submission.answers)) * 100, 2),
        "level": submission.level
    }

@api_router.get("/tests/results/my")
async def get_my_test_results(current_user: dict = Depends(get_current_user)):
    results = await db.test_results.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return results

@api_router.get("/tests/results/all")
async def get_all_test_results(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = await db.test_results.find({}, {"_id": 0}).to_list(1000)
    return results

# TEACHER ROUTES
@api_router.get("/teacher/my-students")
async def get_my_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    students = await db.users.find(
        {"assigned_teacher": current_user['id']},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    return students

@api_router.get("/teacher/my-courses")
async def get_my_courses(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    courses = await db.courses.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return courses

@api_router.post("/teacher/create-course")
async def create_course(course_data: CourseCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    course = Course(
        teacher_id=current_user['id'],
        title=course_data.title,
        description=course_data.description,
        level=course_data.level,
        schedule=course_data.schedule
    )
    
    doc = course.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.courses.insert_one(doc)
    
    return {"message": "Course created", "course": course}

# New models for enhanced teacher features
class CourseCreateEnhanced(BaseModel):
    title: str
    description: str
    level: str
    schedule: str
    student_id: Optional[str] = None
    meet_link: Optional[str] = None

class DocumentCreate(BaseModel):
    title: str
    description: str
    recipient_type: str  # 'admin' or 'student'
    recipient_id: Optional[str] = None
    file_url: str

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    title: str
    description: str
    recipient_type: str
    recipient_id: Optional[str] = None
    file_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionAction(BaseModel):
    action: str  # 'start', 'pause', 'resume', 'end'
    elapsed_time: Optional[int] = None
    paused_duration: Optional[int] = None

# Enhanced teacher routes
@api_router.post("/teacher/create-course")
async def create_course_enhanced(course_data: CourseCreateEnhanced, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")

@api_router.post("/teacher/upload-file")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Pour simplifier, on stocke juste le nom du fichier
    # En production, il faudrait uploader vers S3, Google Cloud Storage, etc.
    file_url = f"/uploads/{current_user['id']}/{file.filename}"
    
    logger.info(f"File uploaded by teacher {current_user['id']}: {file.filename}")
    
    return {
        "message": "File uploaded successfully",
        "file_url": file_url,
        "filename": file.filename
    }

# Student routes for links, documents and homeworks
@api_router.get("/student/my-links")
async def get_student_links(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get links sent by teacher to this student
    links = await db.student_links.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return links

@api_router.get("/student/my-documents")
async def get_student_documents(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get documents from teacher
    teacher_docs = await db.documents.find(
        {"recipient_id": current_user['id'], "recipient_type": "student"},
        {"_id": 0}
    ).to_list(1000)
    
    # Get documents from admin
    admin_docs = await db.admin_documents.find(
        {"to_user_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    return teacher_docs + admin_docs

@api_router.get("/student/my-homeworks")
async def get_student_homeworks(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    homeworks = await db.student_homeworks.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return homeworks

@api_router.get("/student/my-teacher/{teacher_id}")
async def get_student_teacher(teacher_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    teacher = await db.users.find_one(
        {"id": teacher_id, "role": "teacher"},
        {"_id": 0, "password_hash": 0}
    )
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return teacher

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a file (document, video, image, etc.)"""
    import os
    from pathlib import Path
    
    # Create upload directory if it doesn't exist
    upload_dir = Path("/app/frontend/public/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1]
    unique_filename = f"{str(uuid4())}.{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        file_url = f"/uploads/{unique_filename}"
        logger.info(f"File uploaded by {current_user['role']} {current_user['id']}: {file.filename}")
        
        return {
            "message": "File uploaded successfully",
            "file_url": file_url,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")

@api_router.post("/student/send-document-to-admin")
async def student_send_document_to_admin(doc_data: dict, current_user: dict = Depends(get_current_user)):
    """Student sends a document to admin"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get admin user
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    document = {
        "id": str(uuid4()),
        "from_user_id": current_user['id'],
        "from_user_role": "student",
        "to_user_id": admin['id'],
        "to_user_role": "admin",
        "title": doc_data['title'],
        "description": doc_data.get('description', ''),
        "file_url": doc_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(document)
    
    # Create notification for admin
    await create_notification(
        user_id=admin['id'],
        notification_type="new_document",
        data={"message": f"Nouveau document de l'étudiant {current_user['first_name']}: {doc_data['title']}"}
    )
    
    logger.info(f"Document sent by student {current_user['id']} to admin")
    return {"message": "Document envoyé à l'admin avec succès"}

@api_router.post("/student/upload-homework")
async def upload_homework(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    file_url = f"/uploads/homeworks/{current_user['id']}/{file.filename}"
    logger.info(f"Homework file uploaded by student {current_user['id']}: {file.filename}")
    
    return {
        "message": "File uploaded successfully",
        "file_url": file_url,
        "filename": file.filename
    }

@api_router.post("/student/submit-homework")
async def submit_homework(homework_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get student info
    student = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    homework = {
        "id": str(uuid.uuid4()),
        "student_id": current_user['id'],
        "student_name": f"{student['first_name']} {student['last_name']}",
        "teacher_id": student.get('assigned_teacher'),
        "title": homework_data['title'],
        "description": homework_data.get('description', ''),
        "file_url": homework_data['file_url'],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "submitted"
    }
    
    await db.student_homeworks.insert_one(homework)
    logger.info(f"Homework submitted by student {current_user['id']}: {homework_data['title']}")
    
    # Create notification for teacher if assigned
    if student.get('assigned_teacher'):
        await create_notification(student['assigned_teacher'], 'homework_submitted', {
            "student_name": f"{student['first_name']} {student['last_name']}",
            "title": homework_data['title']
        })
    
    return {"message": "Homework submitted successfully"}

# Route for teacher to send links to specific student
@api_router.post("/teacher/send-link")
async def teacher_send_link(link_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    link = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "from_teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
        "student_id": link_data['student_id'],
        "title": link_data['title'],
        "description": link_data.get('description', ''),
        "url": link_data['url'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.student_links.insert_one(link)
    logger.info(f"Link sent by teacher {current_user['id']} to student {link_data['student_id']}")
    
    # Create notification for student
    await create_notification(link_data['student_id'], 'new_link', {
        "title": link_data['title'],
        "from_name": f"{teacher['first_name']} {teacher['last_name']}"
    })
    
    return {"message": "Link sent successfully"}

# Route for teacher to get homeworks from their students
@api_router.get("/teacher/student-homeworks")
async def get_teacher_student_homeworks(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    homeworks = await db.student_homeworks.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    return homeworks
    
@api_router.post("/teacher/create-course-enhanced")
async def create_course_new(course_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    course = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "title": course_data.title,
        "description": course_data.description,
        "level": course_data.level,
        "schedule": course_data.schedule,
        "student_id": course_data.student_id,
        "meet_link": course_data.meet_link,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.courses.insert_one(course)
    return {"message": "Course created", "course": course}

@api_router.get("/teacher/my-documents")
async def get_my_documents(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    documents = await db.documents.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return documents

@api_router.post("/teacher/send-document")
async def send_document(doc_data: DocumentCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get teacher info
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    document = Document(
        teacher_id=current_user['id'],
        title=doc_data.title,
        description=doc_data.description,
        recipient_type=doc_data.recipient_type,
        recipient_id=doc_data.recipient_id if doc_data.recipient_type == 'student' else None,
        file_url=doc_data.file_url
    )
    
    doc = document.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['from_teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
    await db.documents.insert_one(doc)
    
    # Create notification for recipient
    if doc_data.recipient_type == 'student' and doc_data.recipient_id:
        await create_notification(doc_data.recipient_id, 'new_document', {
            "title": doc_data.title,
            "from_name": f"{teacher['first_name']} {teacher['last_name']}"
        })
    
    logger.info(f"Document sent by teacher {current_user['id']} to {doc_data.recipient_type}")
    return {"message": "Document sent successfully", "document": document}

@api_router.post("/teacher/session/start")
async def start_session(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = {
        "id": str(uuid.uuid4()),
        "teacher_id": current_user['id'],
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "in_progress",
        "pauses": []
    }
    
    await db.teacher_sessions.insert_one(session)
    logger.info(f"Session started by teacher {current_user['id']}")
    return {"message": "Session started", "session_id": session['id']}

@api_router.post("/teacher/session/pause")
async def pause_session(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = await db.teacher_sessions.find_one(
        {"teacher_id": current_user['id'], "status": "in_progress"},
        {"_id": 0},
        sort=[("start_time", -1)]
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    pause_record = {
        "pause_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.teacher_sessions.update_one(
        {"id": session['id']},
        {"$push": {"pauses": pause_record}}
    )
    
    logger.info(f"Session paused by teacher {current_user['id']}")
    return {"message": "Session paused"}

@api_router.post("/teacher/session/resume")
async def resume_session(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = await db.teacher_sessions.find_one(
        {"teacher_id": current_user['id'], "status": "in_progress"},
        {"_id": 0},
        sort=[("start_time", -1)]
    )
    
    if not session or not session.get('pauses'):
        raise HTTPException(status_code=404, detail="No paused session found")
    
    await db.teacher_sessions.update_one(
        {"id": session['id'], "pauses.resume_time": {"$exists": False}},
        {"$set": {"pauses.$[elem].resume_time": datetime.now(timezone.utc).isoformat()}},
        array_filters=[{"elem.resume_time": {"$exists": False}}]
    )
    
    logger.info(f"Session resumed by teacher {current_user['id']}")
    return {"message": "Session resumed"}

@api_router.post("/teacher/session/end")
async def end_session(session_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    session = await db.teacher_sessions.find_one(
        {"teacher_id": current_user['id'], "status": "in_progress"},
        {"_id": 0},
        sort=[("start_time", -1)]
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Update session with end time and total duration
    await db.teacher_sessions.update_one(
        {"id": session['id']},
        {"$set": {
            "end_time": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "total_time_seconds": session_data.get('total_time', 0),
            "paused_duration_seconds": session_data.get('paused_duration', 0)
        }}
    )
    
    # Get teacher and admin info
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    # Create notification for admin
    notification = {
        "id": str(uuid.uuid4()),
        "type": "session_completed",
        "teacher_id": current_user['id'],
        "teacher_name": f"{teacher['first_name']} {teacher['last_name']}",
        "session_id": session['id'],
        "start_time": session['start_time'],
        "end_time": datetime.now(timezone.utc).isoformat(),
        "total_time_seconds": session_data.get('total_time', 0),
        "paused_duration_seconds": session_data.get('paused_duration', 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False
    }
    
    await db.admin_notifications.insert_one(notification)
    
    logger.info(f"Session ended by teacher {current_user['id']}, notification sent to admin")
    return {"message": "Session completed and sent to admin"}

# Admin endpoint to get all teacher sessions (for attendance tracking)
@api_router.get("/admin/teacher-sessions")
async def get_teacher_sessions(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sessions = await db.teacher_sessions.find(
        {"status": "completed"},
        {"_id": 0}
    ).sort("end_time", -1).to_list(1000)
    
    # Enrich with teacher info
    for session in sessions:
        teacher = await db.users.find_one(
            {"id": session['teacher_id']},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        if teacher:
            session['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
            session['teacher_email'] = teacher['email']
    
    return sessions

@api_router.post("/admin/manual-session")
async def create_manual_session(session_data: dict, current_user: dict = Depends(get_current_user)):
    """Enregistrer manuellement les heures d'un professeur"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Créer une session manuelle complète
    manual_session = {
        "id": session_data.get('id', str(uuid4())),
        "teacher_id": session_data['teacher_id'],
        "teacher_name": session_data['teacher_name'],
        "teacher_email": session_data['teacher_email'],
        "start_time": session_data['start_time'],
        "end_time": session_data['end_time'],
        "total_time_seconds": session_data['total_time_seconds'],
        "paused_duration_seconds": session_data.get('paused_duration_seconds', 0),
        "status": "completed",
        "is_manual": True,
        "created_at": session_data.get('created_at', datetime.now(timezone.utc).isoformat()),
        "created_by_admin": current_user['id']
    }
    
    await db.teacher_sessions.insert_one(manual_session)
    logger.info(f"Manual session created by admin {current_user['id']} for teacher {session_data['teacher_email']}")
    
    return {"message": "Session enregistrée avec succès", "session_id": manual_session['id']}

@api_router.post("/teacher/attendance")
async def mark_attendance(attendance_data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    attendance = Attendance(
        teacher_id=current_user['id'],
        date=datetime.fromisoformat(attendance_data.date),
        status=attendance_data.status
    )
    
    doc = attendance.model_dump()
    doc['date'] = doc['date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.attendances.insert_one(doc)
    
    return {"message": "Attendance marked"}

@api_router.get("/teacher/attendance")
async def get_my_attendance(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    attendances = await db.attendances.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    return attendances

# MESSAGING
@api_router.post("/messages/send")
async def send_message(message_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    # Get sender info
    sender = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    message = Message(
        from_user_id=current_user['id'],
        to_user_id=message_data.to_user_id,
        content=message_data.content
    )
    
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.messages.insert_one(doc)
    
    # Create notification for recipient
    await create_notification(
        user_id=message_data.to_user_id,
        title=f"💬 Nouveau message",
        message=f"{sender['first_name']} {sender['last_name']} vous a envoyé un message",
        notification_type="message"
    )
    
    return {"message": "Message sent"}

@api_router.get("/messages/conversation/{user_id}")
async def get_conversation(user_id: str, current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find(
        {
            "$or": [
                {"from_user_id": current_user['id'], "to_user_id": user_id},
                {"from_user_id": user_id, "to_user_id": current_user['id']}
            ]
        },
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    return messages

@api_router.delete("/messages/{message_id}/attachment")
async def delete_message_attachment(message_id: str, current_user: dict = Depends(get_current_user)):
    """Delete attachment from a message (only by sender)"""
    message = await db.messages.find_one({"id": message_id, "from_user_id": current_user['id']}, {"_id": 0})
    
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé ou non autorisé")
    
    if not message.get('attachment'):
        raise HTTPException(status_code=404, detail="Aucune pièce jointe à supprimer")
    
    # Remove attachment
    await db.messages.update_one(
        {"id": message_id},
        {"$unset": {"attachment": ""}}
    )
    
    logger.info(f"Attachment removed from message {message_id} by {current_user['id']}")
    return {"message": "Pièce jointe supprimée"}

# LIBRARY ROUTES
@api_router.get("/library/books")
async def get_library_books():
    books = await db.library_books.find({}, {"_id": 0}).to_list(1000)
    return books

@api_router.post("/library/books")
async def add_library_book(book_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = {
        "id": str(uuid.uuid4()),
        "title": book_data.get("title"),
        "author": book_data.get("author"),
        "description": book_data.get("description"),
        "level": book_data.get("level"),
        "type": book_data.get("type", "pdf"),  # pdf, audio
        "file_url": book_data.get("file_url"),
        "audio_url": book_data.get("audio_url"),
        "pages": book_data.get("pages", 0),
        "duration": book_data.get("duration", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.library_books.insert_one(book)
    return {"message": "Book added successfully", "book": book}

@api_router.delete("/library/books/{book_id}")
async def delete_library_book(book_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.library_books.delete_one({"id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": "Book deleted successfully"}

@api_router.get("/messages/my-conversations")
async def get_my_conversations(current_user: dict = Depends(get_current_user)):
    # Get all messages involving current user
    messages = await db.messages.find(
        {
            "$or": [
                {"from_user_id": current_user['id']},
                {"to_user_id": current_user['id']}
            ]
        },
        {"_id": 0}
    ).to_list(1000)
    
    # Get unique user IDs
    user_ids = set()
    for msg in messages:
        if msg['from_user_id'] != current_user['id']:
            user_ids.add(msg['from_user_id'])
        if msg['to_user_id'] != current_user['id']:
            user_ids.add(msg['to_user_id'])
    
    # Get user details
    users = []
    for uid in user_ids:
        user = await db.users.find_one({"id": uid}, {"_id": 0, "password_hash": 0})
        if user:
            users.append(user)
    
    return users

# ==================== NOTIFICATIONS ENDPOINTS ====================

async def create_notification(user_id: str, title: str, message: str, notification_type: str):
    """Helper function to create a notification"""
    notification = {
        "id": str(uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type,  # 'message', 'news', 'club', 'book'
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return notification

@api_router.get("/notifications/my-notifications")
async def get_my_notifications(current_user: User = Depends(get_current_user)):
    """Get all notifications for the current user"""
    notifications = await db.notifications.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_as_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    await db.notifications.update_many(
        {"user_id": current_user.id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    result = await db.notifications.delete_one(
        {"id": notification_id, "user_id": current_user.id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}

@api_router.delete("/notifications/clear-all")
async def clear_all_notifications(current_user: User = Depends(get_current_user)):
    """Delete all notifications for current user"""
    result = await db.notifications.delete_many({"user_id": current_user.id})
    return {"message": f"{result.deleted_count} notifications supprimées"}

# Initialize admin user
@app.on_event("startup")
async def create_admin():
    admin_email = "admin@mykalamaenglish.com"
    existing_admin = await db.users.find_one({"email": admin_email}, {"_id": 0})
    
    if not existing_admin:
        admin = User(
            email=admin_email,
            first_name="Admin",
            last_name="KALAMA",
            phone="",
            role="admin",
            is_active=True,
            password_hash=hash_password("adminco")
        )
        
        doc = admin.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logger.info("Admin user created")

# ============ FILE UPLOAD ROUTE ============

@api_router.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    """Generic file upload endpoint"""
    try:
        # Create uploads directory if not exists
        upload_dir = "/app/frontend/public/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_url = f"/uploads/{unique_filename}"
        logger.info(f"File uploaded: {file.filename} -> {file_url}")
        
        return {
            "message": "File uploaded successfully",
            "file_url": file_url,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")

# ============ KALAMATHÈQUE ROUTES ============

@api_router.post("/kalamatheque/verify-access")
async def verify_kalamatheque_access(data: dict):
    """Verify access code for Kalamathèque"""
    access_code = data.get('access_code')
    correct_code = os.environ.get('KALAMATHEQUE_ACCESS_CODE', 'Digika')
    
    if access_code == correct_code:
        return {"access": True, "message": "Accès accordé"}
    else:
        raise HTTPException(status_code=403, detail="Code d'accès incorrect")

@api_router.post("/kalamatheque/books")
async def create_book(book_data: dict, current_user: dict = Depends(get_current_user)):
    """Admin: Add a new book to Kalamathèque"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    book = {
        "id": str(uuid.uuid4()),
        "title": book_data['title'],
        "author": book_data.get('author', ''),
        "description": book_data.get('description', ''),
        "level": book_data['level'],  # beginner, intermediate, advanced
        "file_url": book_data['file_url'],
        "file_type": book_data['file_type'],  # pdf, epub, txt, html, docx
        "cover_image": book_data.get('cover_image', ''),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.kalamatheque_books.insert_one(book)
    logger.info(f"Book added to Kalamathèque: {book['title']} by admin {current_user['id']}")
    
    # Create notifications for all users (everyone can access Kalamathèque)
    all_users = await db.users.find(
        {"role": {"$in": ["teacher", "student"]}, "status": "approved"},
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in all_users:
        await create_notification(
            user_id=user["id"],
            title="📚 Nouveau livre dans la Kalamathèque !",
            message=f"Découvrez le nouveau livre : {book['title']}",
            notification_type="book"
        )
    
    return {"message": "Livre ajouté avec succès", "book_id": book['id']}

@api_router.get("/kalamatheque/books")
async def get_books(level: Optional[str] = None):
    """Get all books, optionally filtered by level"""
    query = {}
    if level:
        query['level'] = level
    
    books = await db.kalamatheque_books.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return books

@api_router.get("/kalamatheque/books/{book_id}")
async def get_book(book_id: str):
    """Get a specific book by ID"""
    book = await db.kalamatheque_books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return book

@api_router.delete("/kalamatheque/books/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Admin: Delete a book from Kalamathèque"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.kalamatheque_books.delete_one({"id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    logger.info(f"Book {book_id} deleted from Kalamathèque by admin {current_user['id']}")
    return {"message": "Livre supprimé avec succès"}

@api_router.post("/kalamatheque/ai-assistant")
async def kalamatheque_ai_assistant(data: dict):
    """AI Assistant for Kalamathèque - summarize, explain, or give examples (public access)"""
    action = data.get('action')  # 'summarize', 'explain', 'examples'
    selected_text = data.get('text')
    
    if not selected_text:
        raise HTTPException(status_code=400, detail="Texte requis")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        prompts = {
            'summarize': f"Résumez ce texte en français de manière concise :\n\n{selected_text}",
            'explain': f"Expliquez ce texte en français de manière claire et pédagogique :\n\n{selected_text}",
            'examples': f"Donnez 3 exemples concrets en français pour illustrer ce texte :\n\n{selected_text}"
        }
        
        prompt = prompts.get(action, prompts['explain'])
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id="kalamatheque_public",
            system_message="Vous êtes un assistant pédagogique qui aide les étudiants à comprendre les textes."
        )
        
        user_message = UserMessage(text=prompt)
        result = await chat.send_message(user_message)
        
        logger.info(f"AI Assistant used - action: {action}")
        return {"result": result}
        
    except Exception as e:
        logger.error(f"AI Assistant error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur de l'assistant IA")

@api_router.post("/kalamatheque/text-to-speech")
async def text_to_speech(data: dict):
    """Generate speech from text using OpenAI TTS (public access)"""
    text = data.get('text')
    
    if not text:
        raise HTTPException(status_code=400, detail="Texte requis")
    
    try:
        from emergentintegrations.llm.openai.text_to_speech import OpenAITextToSpeech
        
        tts = OpenAITextToSpeech(api_key=os.environ.get('EMERGENT_LLM_KEY'))
        
        # Generate speech and get base64 encoded audio
        audio_base64 = await tts.generate_speech_base64(
            text=text,
            model="tts-1",
            voice="alloy",
            response_format="mp3"
        )
        
        logger.info(f"TTS used for Kalamathèque")
        return {"audio_base64": audio_base64}
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur de synthèse vocale")

# ============ NEWS ROUTES ============

@api_router.get("/news")
async def get_all_news():
    """Get all news (public access for students and teachers)"""
    news_list = await db.news.find({}, {"_id": 0}).sort("published_date", -1).to_list(1000)
    return news_list

@api_router.get("/news/{news_id}")
async def get_news_by_id(news_id: str):
    """Get a specific news item"""
    news = await db.news.find_one({"id": news_id}, {"_id": 0})
    if not news:
        raise HTTPException(status_code=404, detail="News non trouvée")
    return news

@api_router.post("/news")
async def create_news(news_data: NewsCreate, current_user: dict = Depends(get_current_user)):
    """Create news (Admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    news = News(
        title=news_data.title,
        content=news_data.content,
        image_url=news_data.image_url,
        event_date=datetime.fromisoformat(news_data.event_date) if news_data.event_date else None,
        author_id=current_user['id'],
        author_name=f"{current_user['first_name']} {current_user['last_name']}"
    )
    
    doc = news.model_dump()
    doc['published_date'] = doc['published_date'].isoformat()
    if doc.get('event_date'):
        doc['event_date'] = doc['event_date'].isoformat()
    
    await db.news.insert_one(doc)
    logger.info(f"News created by {current_user['id']}: {news.title}")
    
    # Create notifications for all users (teachers and students)
    all_users = await db.users.find(
        {"role": {"$in": ["teacher", "student"]}, "status": "approved"},
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in all_users:
        await create_notification(
            user_id=user["id"],
            title="📰 Nouvelle actualité !",
            message=f"Découvrez : {news.title}",
            notification_type="news"
        )
    
    return {"message": "Actualité créée avec succès", "id": news.id}

@api_router.put("/news/{news_id}")
async def update_news(news_id: str, news_data: NewsCreate, current_user: dict = Depends(get_current_user)):
    """Update news (Admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing_news = await db.news.find_one({"id": news_id})
    if not existing_news:
        raise HTTPException(status_code=404, detail="News non trouvée")
    
    update_data = {
        "title": news_data.title,
        "content": news_data.content,
        "image_url": news_data.image_url,
        "event_date": datetime.fromisoformat(news_data.event_date).isoformat() if news_data.event_date else None
    }
    
    await db.news.update_one({"id": news_id}, {"$set": update_data})
    logger.info(f"News updated by {current_user['id']}: {news_id}")
    
    return {"message": "Actualité mise à jour"}

@api_router.delete("/news/{news_id}")
async def delete_news(news_id: str, current_user: dict = Depends(get_current_user)):
    """Delete news (Admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.news.delete_one({"id": news_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News non trouvée")
    
    logger.info(f"News deleted by {current_user['id']}: {news_id}")
    return {"message": "Actualité supprimée"}

@api_router.post("/news/{news_id}/like")
async def like_news(news_id: str, current_user: dict = Depends(get_current_user)):
    """Like a news post"""
    await db.news.update_one(
        {"id": news_id},
        {"$inc": {"likes": 1}}
    )
    return {"message": "News likée"}

@api_router.get("/news/{news_id}/comments")
async def get_news_comments(news_id: str):
    """Get comments for a news post"""
    comments = await db.news_comments.find({"news_id": news_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return comments

@api_router.post("/news/{news_id}/comments")
async def create_news_comment(news_id: str, comment_data: dict, current_user: dict = Depends(get_current_user)):
    """Add comment to a news post"""
    comment = {
        "id": str(uuid4()),
        "news_id": news_id,
        "author_id": current_user['id'],
        "author_name": f"{current_user['first_name']} {current_user['last_name']}",
        "author_role": current_user['role'],
        "content": comment_data.get('content'),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.news_comments.insert_one(comment)
    
    # Increment comment count
    await db.news.update_one(
        {"id": news_id},
        {"$inc": {"comments": 1}}
    )
    
    logger.info(f"Comment added to news {news_id} by {current_user['id']}")
    return {"message": "Commentaire ajouté", "id": comment["id"]}

# ============ WELCOME LETTER ROUTES ============

@api_router.get("/welcome-letter")
async def get_welcome_letter(current_user: dict = Depends(get_current_user)):
    """Get welcome letter for current user"""
    letter = await db.welcome_letters.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    if not letter:
        return None
    
    return letter

@api_router.put("/welcome-letter/mark-read")
async def mark_welcome_letter_read(current_user: dict = Depends(get_current_user)):
    """Mark welcome letter as read"""
    result = await db.welcome_letters.update_one(
        {"user_id": current_user['id']},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lettre non trouvée")
    
    return {"message": "Lettre marquée comme lue"}

# ============ KALAMA CLUB ROUTES ============

@api_router.get("/club/posts")
async def get_club_posts(category: Optional[str] = None):
    """Get all club posts or filter by category"""
    query = {"category": category} if category else {}
    posts = await db.club_posts.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return posts

@api_router.post("/club/posts")
async def create_club_post(post_data: ClubPostCreate, current_user: dict = Depends(get_current_user)):
    """Create a new club post"""
    post = ClubPost(
        author_id=current_user['id'],
        author_name=f"{current_user['first_name']} {current_user['last_name']}",
        author_role=current_user['role'],
        title=post_data.title,
        content=post_data.content,
        category=post_data.category
    )
    
    doc = post.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.club_posts.insert_one(doc)
    
    logger.info(f"Club post created by {current_user['id']}: {post.title}")
    
    # Create notifications for all users except the author
    all_users = await db.users.find(
        {
            "role": {"$in": ["teacher", "student", "admin"]}, 
            "status": "approved",
            "id": {"$ne": current_user['id']}
        },
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in all_users:
        await create_notification(
            user_id=user["id"],
            title="🏆 Nouveau post KALAMA CLUB !",
            message=f"{current_user['first_name']} {current_user['last_name']} a publié : {post.title}",
            notification_type="club"
        )
    
    return {"message": "Post créé", "id": post.id}

@api_router.post("/club/posts/{post_id}/like")
async def like_club_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Like a club post"""
    await db.club_posts.update_one(
        {"id": post_id},
        {"$inc": {"likes": 1}}
    )
    return {"message": "Post liké"}

@api_router.get("/club/posts/{post_id}/comments")
async def get_post_comments(post_id: str):
    """Get comments for a post"""
    comments = await db.club_comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return comments

@api_router.post("/club/posts/{post_id}/comments")
async def create_comment(post_id: str, comment_data: ClubCommentCreate, current_user: dict = Depends(get_current_user)):
    """Add comment to a post"""
    comment = ClubComment(
        post_id=post_id,
        author_id=current_user['id'],
        author_name=f"{current_user['first_name']} {current_user['last_name']}",
        author_role=current_user['role'],
        content=comment_data.content
    )
    
    doc = comment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.club_comments.insert_one(doc)
    logger.info(f"Comment added to post {post_id} by {current_user['id']}")
    
    # Increment comment count
    await db.club_posts.update_one(
        {"id": post_id},
        {"$inc": {"comments_count": 1}}
    )
    
    return {"message": "Commentaire ajouté", "id": comment.id}

# ==================== LEADERBOARD ENDPOINTS ====================

class LeaderboardEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    user_name: str
    user_role: str  # 'teacher' ou 'student'
    rank: int  # 1-10
    created_by: str  # Admin ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@api_router.get("/club/leaderboard")
async def get_leaderboard():
    """Get current leaderboard - Public endpoint"""
    entries = await db.leaderboard.find({}, {"_id": 0}).sort("rank", 1).to_list(10)
    return entries

@api_router.post("/club/leaderboard")
async def create_leaderboard_entry(
    user_id: str,
    rank: int,
    current_user: dict = Depends(get_current_user)
):
    """Create or update leaderboard entry - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if rank < 1 or rank > 10:
        raise HTTPException(status_code=400, detail="Rank must be between 1 and 10")
    
    # Get user details
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if rank already taken
    existing = await db.leaderboard.find_one({"rank": rank})
    if existing:
        raise HTTPException(status_code=400, detail=f"Rank {rank} is already taken by {existing['user_name']}")
    
    # Check if user already in leaderboard
    user_entry = await db.leaderboard.find_one({"user_id": user_id})
    if user_entry:
        raise HTTPException(status_code=400, detail=f"{user['first_name']} {user['last_name']} is already ranked at position {user_entry['rank']}")
    
    entry = LeaderboardEntry(
        user_id=user_id,
        user_name=f"{user['first_name']} {user['last_name']}",
        user_role=user['role'],
        rank=rank,
        created_by=current_user['id']
    )
    
    doc = entry.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.leaderboard.insert_one(doc)
    
    logger.info(f"Leaderboard entry created: {user['first_name']} {user['last_name']} at rank {rank}")
    return {"message": "Entry added to leaderboard", "id": entry.id}

@api_router.put("/club/leaderboard/{user_id}")
async def update_leaderboard_rank(
    user_id: str,
    new_rank: int,
    current_user: dict = Depends(get_current_user)
):
    """Update user's rank - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if new_rank < 1 or new_rank > 10:
        raise HTTPException(status_code=400, detail="Rank must be between 1 and 10")
    
    # Check if new rank is taken
    existing = await db.leaderboard.find_one({"rank": new_rank, "user_id": {"$ne": user_id}})
    if existing:
        raise HTTPException(status_code=400, detail=f"Rank {new_rank} is already taken")
    
    result = await db.leaderboard.update_one(
        {"user_id": user_id},
        {"$set": {"rank": new_rank, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    
    return {"message": "Rank updated"}

@api_router.delete("/club/leaderboard/{user_id}")
async def remove_from_leaderboard(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove user from leaderboard - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.leaderboard.delete_one({"user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    
    return {"message": "Removed from leaderboard"}

@api_router.get("/club/student-of-month")
async def get_student_of_month():
    """Get current Student of the Month"""
    badge = await db.student_of_month.find_one({"active": True}, {"_id": 0})
    if not badge:
        return None
    
    # Check if expired
    if badge.get('expires_at'):
        expires_date = datetime.fromisoformat(badge['expires_at'])
        if datetime.now(timezone.utc) > expires_date:
            await db.student_of_month.update_one(
                {"user_id": badge['user_id']},
                {"$set": {"active": False}}
            )
            return None
    
    return badge

@api_router.post("/club/student-of-month")
async def set_student_of_month(
    user_id: str,
    duration_days: int,
    current_user: dict = Depends(get_current_user)
):
    """Set Student of the Month - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get user details
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Deactivate previous badge
    await db.student_of_month.update_many(
        {"active": True},
        {"$set": {"active": False}}
    )
    
    # Create new badge
    expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    badge_title = "Meilleur Prof du Mois" if user['role'] == 'teacher' else "Étudiant du Mois"
    badge = {
        "id": str(uuid4()),
        "user_id": user_id,
        "user_name": f"{user['first_name']} {user['last_name']}",
        "user_role": user['role'],
        "badge_title": badge_title,
        "active": True,
        "likes": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at.isoformat(),
        "created_by": current_user['id']
    }
    
    await db.student_of_month.insert_one(badge)
    logger.info(f"{badge_title} set: {user['first_name']} {user['last_name']} for {duration_days} days")
    
    return {"message": f"Badge {badge_title} attribué", "expires_at": expires_at.isoformat()}

@api_router.post("/club/student-of-month/like")
async def like_student_of_month(current_user: dict = Depends(get_current_user)):
    """Like the Student/Teacher of the Month"""
    badge = await db.student_of_month.find_one({"active": True})
    if not badge:
        raise HTTPException(status_code=404, detail="Aucun badge actif")
    
    await db.student_of_month.update_one(
        {"id": badge['id']},
        {"$inc": {"likes": 1}}
    )
    
    return {"message": "Like ajouté!", "likes": badge.get('likes', 0) + 1}

@api_router.get("/club/events")
async def get_club_events():
    """Get all upcoming club events"""
    events = await db.club_events.find({}, {"_id": 0}).sort("event_date", 1).to_list(1000)
    return events

@api_router.post("/club/events")
async def create_club_event(event_data: ClubEventCreate, current_user: dict = Depends(get_current_user)):
    """Create a new club event (teachers and admin only)"""
    if current_user['role'] not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Seuls les professeurs et admins peuvent créer des événements")
    
    event = ClubEvent(
        title=event_data.title,
        description=event_data.description,
        event_date=datetime.fromisoformat(event_data.event_date),
        duration_minutes=event_data.duration_minutes,
        max_participants=event_data.max_participants,
        event_link=event_data.event_link,
        created_by=current_user['id']
    )
    
    doc = event.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['event_date'] = doc['event_date'].isoformat()
    await db.club_events.insert_one(doc)
    
    logger.info(f"Club event created by {current_user['id']}: {event.title}")
    return {"message": "Événement créé", "id": event.id}

@api_router.delete("/club/events/{event_id}")
async def delete_club_event(event_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a club event (admin only, for past events)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.club_events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    logger.info(f"Club event deleted by admin: {event_id}")
    return {"message": "Événement supprimé"}

@api_router.post("/club/events/{event_id}/join")
async def join_club_event(event_id: str, current_user: dict = Depends(get_current_user)):
    """Join a club event"""
    event = await db.club_events.find_one({"id": event_id}, {"_id": 0})
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    if current_user['id'] in event.get('participants', []):
        raise HTTPException(status_code=400, detail="Déjà inscrit")
    
    if len(event.get('participants', [])) >= event['max_participants']:
        raise HTTPException(status_code=400, detail="Événement complet")
    
    await db.club_events.update_one(
        {"id": event_id},
        {"$push": {"participants": current_user['id']}}
    )
    
    return {"message": "Inscription confirmée"}

@api_router.get("/club/leaderboard")
async def get_club_leaderboard():
    """Get club leaderboard based on contributions"""
    # Get post counts per user
    pipeline = [
        {"$group": {
            "_id": "$author_id",
            "author_name": {"$first": "$author_name"},
            "author_role": {"$first": "$author_role"},
            "post_count": {"$sum": 1},
            "total_likes": {"$sum": "$likes"}
        }},
        {"$sort": {"total_likes": -1}},
        {"$limit": 10}
    ]
    
    leaderboard = await db.club_posts.aggregate(pipeline).to_list(10)
    return leaderboard

# ============ GAMES & FLASHCARDS ENDPOINTS ============

@api_router.post("/teacher/create-flashcard-set")
async def create_flashcard_set(data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher creates a new flashcard set"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    flashcard_set = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "flashcards": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.flashcard_sets.insert_one(flashcard_set)
    return {"message": "Flashcard set created", "set_id": flashcard_set['id']}

@api_router.post("/teacher/add-flashcard")
async def add_flashcard(data: dict, current_user: dict = Depends(get_current_user)):
    """Add a flashcard to a set"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    flashcard = {
        "id": str(uuid4()),
        "question": data['question'],
        "answer": data['answer']
    }
    
    result = await db.flashcard_sets.update_one(
        {"id": data['set_id'], "teacher_id": current_user['id']},
        {"$push": {"flashcards": flashcard}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    
    return {"message": "Flashcard added"}

@api_router.get("/teacher/my-flashcard-sets")
async def get_teacher_flashcard_sets(current_user: dict = Depends(get_current_user)):
    """Get all flashcard sets created by teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    sets = await db.flashcard_sets.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    return sets

@api_router.delete("/teacher/delete-flashcard-set/{set_id}")
async def delete_flashcard_set(set_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a flashcard set"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.flashcard_sets.delete_one({"id": set_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    
    return {"message": "Flashcard set deleted"}

@api_router.post("/teacher/assign-game")
async def assign_game(data: dict, current_user: dict = Depends(get_current_user)):
    """Assign a game (flashcard or kahoot) to a student"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    assignment = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "student_id": data['student_id'],
        "game_type": data['game_type'],  # 'flashcard' or 'kahoot'
        "game_id": data.get('game_id'),  # flashcard set id
        "game_url": data.get('game_url'),  # kahoot link
        "title": data['title'],
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "completed": False,
        "score": None
    }
    
    await db.game_assignments.insert_one(assignment)
    return {"message": "Game assigned to student"}

@api_router.get("/teacher/game-scores")
async def get_teacher_game_scores(current_user: dict = Depends(get_current_user)):
    """Get all game scores for teacher's students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    scores = await db.game_assignments.find(
        {"teacher_id": current_user['id'], "completed": True}, 
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with student names
    for score in scores:
        student = await db.users.find_one({"id": score['student_id']}, {"_id": 0, "first_name": 1, "last_name": 1})
        if student:
            score['student_name'] = f"{student['first_name']} {student['last_name']}"
    
    return scores

@api_router.get("/student/my-games")
async def get_student_games(current_user: dict = Depends(get_current_user)):
    """Get all games assigned to student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    games = await db.game_assignments.find({"student_id": current_user['id']}, {"_id": 0}).to_list(100)
    
    # Enrich flashcard games with actual flashcard data
    for game in games:
        if game['game_type'] == 'flashcard' and game.get('game_id'):
            flashcard_set = await db.flashcard_sets.find_one({"id": game['game_id']}, {"_id": 0})
            if flashcard_set:
                game['flashcards'] = flashcard_set['flashcards']
    
    return games

@api_router.post("/student/submit-game-score")
async def submit_game_score(data: dict, current_user: dict = Depends(get_current_user)):
    """Student submits game score"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    result = await db.game_assignments.update_one(
        {"id": data['assignment_id'], "student_id": current_user['id']},
        {
            "$set": {
                "completed": True,
                "score": data['score'],
                "total": data['total'],
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Score submitted successfully"}

# ============ TEST QUESTIONS MANAGEMENT (ADMIN) ============

@api_router.get("/test-questions/{level}")
async def get_test_questions(level: str):
    """Get test questions for a specific level (public endpoint)"""
    questions = await db.test_questions.find({"level": level, "active": True}, {"_id": 0}).to_list(100)
    return questions

@api_router.get("/admin/all-test-questions")
async def get_all_test_questions(current_user: dict = Depends(get_current_user)):
    """Get all test questions (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    questions = await db.test_questions.find({}, {"_id": 0}).to_list(1000)
    return questions

@api_router.post("/admin/create-test-question")
async def create_test_question(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new test question"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    question = {
        "id": str(uuid4()),
        "level": data['level'],  # beginner, intermediate, advanced
        "question_type": data['question_type'],  # 'mcq' or 'true_false'
        "question": data['question'],
        "options": data.get('options', []),  # for MCQ
        "correct_answer": data['correct_answer'],
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.test_questions.insert_one(question)
    return {"message": "Question created", "question_id": question['id']}

@api_router.put("/admin/update-test-question/{question_id}")
async def update_test_question(question_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Update a test question"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {
        "question": data['question'],
        "options": data.get('options', []),
        "correct_answer": data['correct_answer'],
        "active": data.get('active', True)
    }
    
    result = await db.test_questions.update_one(
        {"id": question_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question updated"}

@api_router.delete("/admin/delete-test-question/{question_id}")
async def delete_test_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a test question"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.test_questions.delete_one({"id": question_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question deleted"}

# ============ VIDEOS FOR KIDS ============

@api_router.post("/teacher/assign-video")
async def assign_video(data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher assigns video to a student (K-Kid)"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    video = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "student_id": data['student_id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "video_url": data['video_url'],
        "assigned_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.student_videos.insert_one(video)
    return {"message": "Video assigned"}

@api_router.get("/teacher/my-assigned-videos")
async def get_teacher_assigned_videos(current_user: dict = Depends(get_current_user)):
    """Get all videos assigned by teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    videos = await db.student_videos.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    
    # Enrich with student names
    for video in videos:
        student = await db.users.find_one({"id": video['student_id']}, {"_id": 0, "first_name": 1, "last_name": 1})
        if student:
            video['student_name'] = f"{student['first_name']} {student['last_name']}"
    
    return videos

@api_router.delete("/teacher/delete-video/{video_id}")
async def delete_video(video_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an assigned video"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.student_videos.delete_one({"id": video_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video deleted"}

@api_router.get("/student/my-videos")
async def get_student_videos(current_user: dict = Depends(get_current_user)):
    """Get all videos assigned to student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    videos = await db.student_videos.find({"student_id": current_user['id']}, {"_id": 0}).to_list(100)
    return videos

# ============ WEEKEND GIFTS FOR KIDS ============

@api_router.get("/student/weekend-gift")
async def get_weekend_gift(current_user: dict = Depends(get_current_user)):
    """Get current weekend gift"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get current week number
    from datetime import datetime
    week_number = datetime.now(timezone.utc).isocalendar()[1]
    year = datetime.now(timezone.utc).year
    
    # Check if gift already collected this week
    collected = await db.collected_gifts.find_one({
        "student_id": current_user['id'],
        "week_number": week_number,
        "year": year
    }, {"_id": 0})
    
    # Get gift for this week (rotate through available gifts)
    gifts = await db.weekend_gifts.find({"active": True}, {"_id": 0}).to_list(100)
    if not gifts:
        # Create default gifts if none exist
        await create_default_gifts()
        gifts = await db.weekend_gifts.find({"active": True}, {"_id": 0}).to_list(100)
    
    gift_index = week_number % len(gifts)
    gift = gifts[gift_index]
    gift['is_collected'] = collected is not None
    
    return gift

@api_router.post("/student/collect-gift")
async def collect_gift(data: dict, current_user: dict = Depends(get_current_user)):
    """Mark gift as collected and add stars"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    week_number = datetime.now(timezone.utc).isocalendar()[1]
    year = datetime.now(timezone.utc).year
    
    # Check if already collected
    existing = await db.collected_gifts.find_one({
        "student_id": current_user['id'],
        "week_number": week_number,
        "year": year
    })
    
    if existing:
        return {"message": "Gift already collected"}
    
    # Get the gift details
    gift = await db.weekend_gifts.find_one({"id": data['gift_id']}, {"_id": 0})
    
    # Save collection
    collection = {
        "id": str(uuid4()),
        "student_id": current_user['id'],
        "gift_id": data['gift_id'],
        "word_french": gift['word_french'],
        "word_english": gift['word_english'],
        "image_url": gift['image_url'],
        "week_number": week_number,
        "year": year,
        "collected_at": datetime.now(timezone.utc).isoformat()
    }
    await db.collected_gifts.insert_one(collection)
    
    # Add 10 stars to user
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"stars": 10}}
    )
    
    return {"message": "Gift collected!", "stars_earned": 10}

@api_router.get("/student/my-collected-gifts")
async def get_collected_gifts(current_user: dict = Depends(get_current_user)):
    """Get all collected gifts"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    gifts = await db.collected_gifts.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).sort("collected_at", -1).to_list(100)
    
    return gifts

async def create_default_gifts():
    """Create default weekend gifts"""
    default_gifts = [
        {
            "id": str(uuid4()),
            "word_french": "Chat",
            "word_english": "Cat",
            "image_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Chien",
            "word_english": "Dog",
            "image_url": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Papillon",
            "word_english": "Butterfly",
            "image_url": "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Pomme",
            "word_english": "Apple",
            "image_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400",
            "audio_url": "",
            "active": True
        },
        {
            "id": str(uuid4()),
            "word_french": "Soleil",
            "word_english": "Sun",
            "image_url": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=400",
            "audio_url": "",
            "active": True
        }
    ]
    
    await db.weekend_gifts.insert_many(default_gifts)

# ============ PROMO CODE ROUTES ============

@api_router.post("/promo-codes/validate")
async def validate_promo_code(request: ValidatePromoCodeRequest):
    """Validate a promo code and return discount information"""
    code_upper = request.code.upper()
    
    # Find promo code
    promo = await db.promo_codes.find_one({"code": code_upper}, {"_id": 0})
    
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo invalide")
    
    # Check if active
    if not promo.get('is_active', False):
        raise HTTPException(status_code=400, detail="Ce code promo n'est plus actif")
    
    # Check expiration
    valid_until_str = promo.get('valid_until')
    if valid_until_str:
        # Parse the datetime string
        if isinstance(valid_until_str, str):
            valid_until = datetime.fromisoformat(valid_until_str.replace('Z', '+00:00'))
        else:
            valid_until = valid_until_str
        
        if datetime.now(timezone.utc) > valid_until:
            raise HTTPException(status_code=400, detail="Ce code promo a expiré")
    
    # Check max uses
    max_uses = promo.get('max_uses')
    current_uses = promo.get('current_uses', 0)
    
    if max_uses and current_uses >= max_uses:
        raise HTTPException(status_code=400, detail="Ce code promo a atteint sa limite d'utilisation")
    
    return {
        "valid": True,
        "code": promo['code'],
        "discount_percent": promo['discount_percent'],
        "message": f"Code promo valide ! {promo['discount_percent']}% de réduction"
    }

@api_router.post("/promo-codes/use")
async def use_promo_code(request: ValidatePromoCodeRequest, user_email: str):
    """Mark a promo code as used"""
    code_upper = request.code.upper()
    
    # Validate first
    promo = await db.promo_codes.find_one({"code": code_upper}, {"_id": 0})
    
    if not promo:
        raise HTTPException(status_code=404, detail="Code promo invalide")
    
    # Check if user already used this code
    usage = await db.promo_code_usage.find_one({
        "promo_code": code_upper,
        "user_email": user_email
    })
    
    if usage:
        raise HTTPException(status_code=400, detail="Vous avez déjà utilisé ce code promo")
    
    # Increment usage count
    await db.promo_codes.update_one(
        {"code": code_upper},
        {"$inc": {"current_uses": 1}}
    )
    
    # Record usage
    usage_doc = {
        "id": str(uuid4()),
        "promo_code_id": promo['id'],
        "promo_code": code_upper,
        "user_email": user_email,
        "used_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promo_code_usage.insert_one(usage_doc)
    
    return {"message": "Code promo appliqué avec succès"}

@api_router.post("/admin/promo-codes")
async def create_promo_code(
    code: str,
    discount_percent: int,
    valid_until: str,
    max_uses: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a new promo code - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    code_upper = code.upper()
    
    # Check if code already exists
    existing = await db.promo_codes.find_one({"code": code_upper})
    if existing:
        raise HTTPException(status_code=400, detail="Ce code promo existe déjà")
    
    # Parse date
    valid_until_dt = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
    
    promo = {
        "id": str(uuid4()),
        "code": code_upper,
        "discount_percent": discount_percent,
        "valid_until": valid_until_dt.isoformat(),
        "max_uses": max_uses,
        "current_uses": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promo_codes.insert_one(promo)
    logger.info(f"Promo code created by admin {current_user['id']}: {code_upper}")
    
    return {"message": "Code promo créé", "code": code_upper}

@api_router.get("/admin/promo-codes")
async def get_promo_codes(current_user: dict = Depends(get_current_user)):
    """Get all promo codes - Admin only"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    codes = await db.promo_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return codes

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Health check endpoints for Kubernetes
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "mykalamaenglish-backend"}

@app.get("/readiness")
async def readiness_check():
    """Readiness check - verifies database connection"""
    try:
        # Test MongoDB connection
        await db.command('ping')
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MyKalamaEnglish API", "version": "1.0", "status": "running"}

