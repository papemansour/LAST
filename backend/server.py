from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Body, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
import stripe
from passlib.context import CryptContext
from email_service import email_service
from websocket_manager import ws_manager

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
    first_login: bool = True  # True until user opens welcome letter
    welcome_letter_opened_at: Optional[datetime] = None

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

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    file_url: str
    file_name: str
    file_type: str
    sender_id: str
    sender_name: str
    sender_role: str  # 'admin' or 'teacher'
    recipient_ids: List[str]  # Liste des IDs d'étudiants destinataires
    read_by: List[str] = []  # Liste des IDs d'étudiants qui ont lu/ouvert le document
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentCreate(BaseModel):
    title: str
    description: str
    file_url: str
    file_name: str
    file_type: str
    recipient_ids: List[str]  # Liste des IDs d'étudiants destinataires

class MeetLink(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    teacher_id: str
    meet_link: str
    title: str
    scheduled_date: datetime
    completed: bool = False
    attended: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MeetLinkCreate(BaseModel):
    student_id: str
    meet_link: str
    title: str
    scheduled_date: str  # ISO format

class Badge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: str
    description: str
    condition_type: str  # 'first_login', 'courses_completed', 'level_completed'
    condition_value: int  # Number needed (5 courses, 10 courses, etc.)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BadgeCreate(BaseModel):
    name: str
    icon: str
    description: str
    condition_type: str
    condition_value: int

class StudentBadge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    badge_id: str
    awarded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WeeklyChallenge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    challenge_type: str  # 'like_posts', 'comment_posts', 'attend_webinars'
    target_count: int  # Number of actions needed
    points_reward: int  # XP points to earn
    week_start: datetime
    week_end: datetime
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StudentPoints(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    total_points: int = 0
    available_points: int = 0  # Points not yet converted to discount
    total_discount_earned: float = 0.0  # Total discount in currency
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChallengeProgress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    challenge_id: str
    current_count: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None

class GroupCourse(BaseModel):
    """Modèle pour les cours groupés"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    teacher_id: str
    level: str  # beginner, intermediate, advanced
    max_students: int = 6
    current_students: List[str] = []  # List of student IDs
    scheduled_days: List[str] = []  # ["monday", "wednesday", "friday"]
    scheduled_time: str = ""  # "18:00"
    price_per_person_eur: float = 80.0
    price_per_person_fcfa: float = 50000.0
    discount_4_plus: int = 10  # 10% discount for 4+ students
    meet_link: str = ""
    status: str = "open"  # open, full, in_progress, completed
    start_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupCourseEnrollment(BaseModel):
    """Inscription à un cours groupé"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_course_id: str
    student_id: str
    enrolled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_status: str = "pending"  # pending, paid, cancelled
    amount_paid: float = 0.0
    currency: str = "EUR"

# ============ UTILITIES ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
    except JWTError:
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

# ============ HELPER FUNCTIONS ============

async def add_student_points(student_id: str, points: int, reason: str = ""):
    """Add points to a student's treasure chest (Coffre aux Trésors)"""
    try:
        # Get or create points record
        points_record = await db.student_points.find_one({"student_id": student_id})
        
        if points_record:
            # Update existing record
            new_total = points_record.get('total_points', 0) + points
            new_available = points_record.get('available_points', 0) + points
            await db.student_points.update_one(
                {"student_id": student_id},
                {
                    "$set": {
                        "total_points": new_total,
                        "available_points": new_available,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        else:
            # Create new record
            new_record = {
                "id": str(uuid4()),
                "student_id": student_id,
                "total_points": points,
                "available_points": points,
                "total_discount_earned": 0.0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.student_points.insert_one(new_record)
        
        logger.info(f"Added {points} points to student {student_id}: {reason}")
        
        # Check if student reached 50 points milestone
        updated_record = await db.student_points.find_one({"student_id": student_id})
        if updated_record and updated_record.get('available_points', 0) >= 50:
            # Create notification for unlocked rewards
            await create_notification(
                user_id=student_id,
                title="🎁 Récompenses débloquées !",
                message="Félicitations ! Vous avez atteint 50 points. Vos réductions sont maintenant actives dans votre Coffre aux Trésors !",
                notification_type="reward"
            )
        
        return True
    except Exception as e:
        logger.error(f"Error adding points to student {student_id}: {str(e)}")
        return False

# ============ ROUTES ============

@api_router.get("/uploads/{file_path:path}")
async def serve_uploaded_file_api(file_path: str):
    """Serve uploaded files from persistent storage via /api/uploads/ route"""
    from fastapi.responses import Response
    import mimetypes
    
    file_full_path = Path("/app/uploads") / file_path
    
    # Security check: ensure file is within uploads directory
    try:
        file_full_path.resolve().relative_to(Path("/app/uploads").resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Check if file exists
    if not file_full_path.exists() or not file_full_path.is_file():
        logger.warning(f"File not found: {file_full_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(file_full_path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    logger.info(f"Serving file via API: {file_path} ({mime_type})")
    
    # Read file content
    with open(file_full_path, "rb") as f:
        content = f.read()
    
    # Return response with download headers
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_full_path.name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

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
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get('is_active'):
        raise HTTPException(status_code=403, detail="Account not activated yet. Please wait for admin approval.")
    
    # Check if student access is restricted
    if user.get('role') == 'student' and user.get('is_restricted', False):
        raise HTTPException(status_code=403, detail="Your access has been restricted. Please contact the administrator.")
    
    # Verify password
    if not verify_password(credentials.password, user['password_hash']):
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

@api_router.post("/auth/secretary-login")
async def secretary_login(code: str = Body(..., embed=True)):
    """Special login for secretary with secret code - gives admin access"""
    if code != "secretaire2025":
        raise HTTPException(status_code=401, detail="Code incorrect")
    
    # Find or create secretary user with admin role
    secretary = await db.users.find_one({"email": "secretaire@mykalamaenglish.com"}, {"_id": 0})
    
    if not secretary:
        # Create secretary user with admin role
        secretary_id = str(uuid4())
        secretary = {
            "id": secretary_id,
            "email": "secretaire@mykalamaenglish.com",
            "first_name": "Secrétaire",
            "last_name": "KALAMA",
            "phone": "+221000000000",
            "role": "secretary",  # Secretary role to access secretary dashboard
            "is_active": True,
            "password_hash": hash_password("secretaire2025"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "first_login": False
        }
        await db.users.insert_one(secretary)
        logger.info(f"Secretary user created with admin access via code")
    
    # Create token with secretary role
    token = create_access_token({"sub": secretary['id'], "role": "secretary"})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": secretary['id'],
            "email": secretary['email'],
            "first_name": secretary['first_name'],
            "last_name": secretary['last_name'],
            "role": "secretary"  # Return secretary role
        }
    }

# SECRETARY ENDPOINTS
@api_router.get("/secretary/meetings")
async def get_secretary_meetings(current_user: dict = Depends(get_current_user)):
    """Get all meetings created by secretary"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    meetings = await db.secretary_meetings.find({}, {"_id": 0}).sort("date", -1).to_list(100)
    return meetings

@api_router.post("/secretary/meetings")
async def create_secretary_meeting(meeting_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new meeting"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    meeting = {
        "id": str(uuid4()),
        "title": meeting_data.get("title"),
        "date": meeting_data.get("date"),
        "time": meeting_data.get("time"),
        "attendees": meeting_data.get("attendees", ""),
        "notes": meeting_data.get("notes", ""),
        "meeting_link": meeting_data.get("meetingLink", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.secretary_meetings.insert_one(meeting)
    logger.info(f"Meeting created by secretary: {meeting['title']}")
    return {"message": "Meeting created", "id": meeting['id']}

@api_router.delete("/secretary/meetings/{meeting_id}")
async def delete_secretary_meeting(meeting_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a meeting"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.secretary_meetings.delete_one({"id": meeting_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting deleted"}

@api_router.put("/secretary/meetings/{meeting_id}")
async def update_secretary_meeting(meeting_id: str, meeting_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update a meeting"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    update_data = {
        "title": meeting_data.get("title"),
        "date": meeting_data.get("date"),
        "time": meeting_data.get("time"),
        "attendees": meeting_data.get("attendees", ""),
        "notes": meeting_data.get("notes", ""),
        "meetingLink": meeting_data.get("meetingLink", ""),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.secretary_meetings.update_one(
        {"id": meeting_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting updated"}

@api_router.get("/secretary/reports")
async def get_secretary_reports(current_user: dict = Depends(get_current_user)):
    """Get all teacher reports"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    reports = await db.teacher_reports.find({}, {"_id": 0}).sort("date", -1).to_list(100)
    return reports

@api_router.post("/secretary/reports")
async def create_secretary_report(report_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new teacher report"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    report = {
        "id": str(uuid4()),
        "prof_name": report_data.get("profName"),
        "date": report_data.get("date"),
        "content": report_data.get("content"),
        "notes": report_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.teacher_reports.insert_one(report)
    logger.info(f"Teacher report created for: {report['prof_name']}")
    return {"message": "Report created", "id": report['id']}

@api_router.delete("/secretary/reports/{report_id}")
async def delete_secretary_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a teacher report"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.teacher_reports.delete_one({"id": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted"}

# SECRETARY BILLING ENDPOINTS
@api_router.get("/secretary/teacher-payments")
async def get_teacher_payments(current_user: dict = Depends(get_current_user)):
    """Get all teacher payments"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    payments = await db.teacher_payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments

@api_router.post("/secretary/teacher-payments")
async def create_teacher_payment(payment_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a teacher payment record"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    payment = {
        "id": str(uuid4()),
        "teacher_id": payment_data.get("teacherId"),
        "teacher_name": payment_data.get("teacherName"),
        "teacher_email": payment_data.get("teacherEmail", ""),
        "teacher_address": payment_data.get("teacherAddress", ""),
        "month": payment_data.get("month"),
        "amount": payment_data.get("amount"),
        "currency": payment_data.get("currency", "EUR"),
        "hours_worked": payment_data.get("hoursWorked", ""),
        "hourly_rate": payment_data.get("hourlyRate", ""),
        "bonus": payment_data.get("bonus", "0"),
        "description": payment_data.get("description", "Cours de langue anglaise"),
        "notes": payment_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.teacher_payments.insert_one(payment)
    
    # Sync to Monday.com
    try:
        from monday_integration import create_invoice_in_monday
        create_invoice_in_monday(payment, "teacher")
    except Exception as e:
        logger.warning(f"Could not sync teacher payment to Monday: {e}")
    
    logger.info(f"Teacher payment created for: {payment['teacher_name']} - {payment['amount']} {payment['currency']}")
    return {"message": "Payment created", "id": payment['id']}

@api_router.delete("/secretary/teacher-payments/{payment_id}")
async def delete_teacher_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a teacher payment"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.teacher_payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment deleted"}

@api_router.get("/secretary/student-receipts")
async def get_student_receipts(current_user: dict = Depends(get_current_user)):
    """Get all student receipts"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    receipts = await db.student_receipts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return receipts

@api_router.post("/secretary/student-receipts")
async def create_student_receipt(receipt_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a student receipt"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    receipt = {
        "id": str(uuid4()),
        "student_id": receipt_data.get("studentId"),
        "student_name": receipt_data.get("studentName"),
        "pack_type": receipt_data.get("packType"),
        "amount": receipt_data.get("amount"),
        "currency": receipt_data.get("currency", "EUR"),
        "payment_method": receipt_data.get("paymentMethod", "Virement"),
        "notes": receipt_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.student_receipts.insert_one(receipt)
    
    # Sync to Monday.com
    try:
        from monday_integration import create_invoice_in_monday
        create_invoice_in_monday(receipt, "student")
    except Exception as e:
        logger.warning(f"Could not sync student receipt to Monday: {e}")
    
    logger.info(f"Student receipt created for: {receipt['student_name']} - {receipt['amount']} {receipt['currency']}")
    return {"message": "Receipt created", "id": receipt['id']}

@api_router.delete("/secretary/student-receipts/{receipt_id}")
async def delete_student_receipt(receipt_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a student receipt"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.student_receipts.delete_one({"id": receipt_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return {"message": "Receipt deleted"}

# Prestataire invoices endpoints
@api_router.get("/secretary/prestataire-invoices")
async def get_prestataire_invoices(current_user: dict = Depends(get_current_user)):
    """Get all prestataire invoices"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    invoices = await db.prestataire_invoices.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return invoices

@api_router.post("/secretary/prestataire-invoices")
async def create_prestataire_invoice(invoice_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a prestataire invoice"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    invoice = {
        "id": str(uuid4()),
        "name": invoice_data.get("name"),
        "service": invoice_data.get("service"),
        "amount": invoice_data.get("amount"),
        "currency": invoice_data.get("currency", "EUR"),
        "description": invoice_data.get("description", ""),
        "notes": invoice_data.get("notes", ""),
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.prestataire_invoices.insert_one(invoice)
    
    # Sync to Monday.com
    try:
        from monday_integration import create_invoice_in_monday
        create_invoice_in_monday(invoice, "prestataire")
    except Exception as e:
        logger.warning(f"Could not sync prestataire invoice to Monday: {e}")
    
    logger.info(f"Prestataire invoice created for: {invoice['name']} - {invoice['amount']} {invoice['currency']}")
    return {"message": "Invoice created", "id": invoice['id']}

@api_router.delete("/secretary/prestataire-invoices/{invoice_id}")
async def delete_prestataire_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a prestataire invoice"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.prestataire_invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"message": "Invoice deleted"}

@api_router.post("/secretary/send-invoice-email")
async def send_invoice_by_email(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Send invoice by email"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    invoice_type = data.get("invoice_type", "student")
    recipient_email = data.get("recipient_email")
    recipient_name = data.get("recipient_name", "")
    amount = float(data.get("amount", 0))
    currency = data.get("currency", "EUR")
    
    # TVA INCLUSE dans le montant - calcul du montant net
    tva_rate = 0.20 if currency == "EUR" else 0.18  # 20% EUR, 18% FCFA
    montant_net = amount / (1 + tva_rate)
    tva_amount = amount - montant_net
    
    # Générer le contenu de l'email
    subject = f"Facture MyKalama English - {recipient_name}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎓 MyKalama English</h1>
                <p style="color: rgba(255,255,255,0.9); margin-top: 10px;">Facture {'Professeur' if invoice_type == 'teacher' else 'Étudiant'}</p>
            </div>
            <div style="padding: 30px;">
                <p>Bonjour <strong>{recipient_name}</strong>,</p>
                <p>Veuillez trouver ci-dessous le détail de votre facture :</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background: #f3f4f6;">
                        <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>Montant brut (TTC)</strong></td>
                        <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right;">{amount:.2f} {currency}</td>
                    </tr>
                    <tr style="background: #f3f4f6;">
                        <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>TVA déduite ({int(tva_rate*100)}%)</strong></td>
                        <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right;">- {tva_amount:.2f} {currency}</td>
                    </tr>
                    <tr style="background: #d1fae5;">
                        <td style="padding: 12px; border: 1px solid #e5e7eb;"><strong>💰 Montant net à recevoir</strong></td>
                        <td style="padding: 12px; border: 1px solid #e5e7eb; text-align: right; font-weight: bold; font-size: 18px;">{montant_net:.2f} {currency}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 30px;">Cordialement,<br><strong>L'équipe MyKalama English</strong></p>
            </div>
            <div style="background: #1f2937; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p>MyKalama English - Paris, France / Dakar, Sénégal</p>
                <p>📞 +221 78 260 75 49 / 78 528 68 89</p>
                <p>📧 mykalamaenglish@gmail.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Facture MyKalama English - {recipient_name}
    
    Bonjour {recipient_name},
    
    Veuillez trouver ci-dessous le détail de votre facture :
    
    Montant brut (TTC): {amount:.2f} {currency}
    TVA déduite ({int(tva_rate*100)}%): -{tva_amount:.2f} {currency}
    Montant net à recevoir: {montant_net:.2f} {currency}
    
    Cordialement,
    L'équipe MyKalama English
    
    📞 +221 78 260 75 49 / 78 528 68 89
    📧 mykalamaenglish@gmail.com
    """
    
    # Envoyer via le service email
    email_sent = await email_service.send_invoice_email(
        recipient_email,
        recipient_name,
        subject,
        html_content,
        text_content
    )
    
    # Sauvegarder l'email dans la base
    await db.pending_emails.insert_one({
        "id": str(uuid4()),
        "to": recipient_email,
        "subject": subject,
        "html_content": html_content,
        "invoice_type": invoice_type,
        "amount_brut": amount,
        "tva_amount": tva_amount,
        "montant_net": montant_net,
        "currency": currency,
        "status": "sent" if email_sent else "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Invoice email {'sent' if email_sent else 'prepared'} for: {recipient_email} - Net: {montant_net:.2f} {currency}")
    return {"message": "Invoice email sent" if email_sent else "Invoice email queued", "recipient": recipient_email, "sent": email_sent, "montant_net": montant_net}

@api_router.post("/secretary/reset-billing-stats")
async def reset_billing_stats(current_user: dict = Depends(get_current_user)):
    """Reset all billing statistics (delete all payments, receipts, invoices)"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    # Delete all billing data
    deleted_payments = await db.teacher_payments.delete_many({})
    deleted_receipts = await db.student_receipts.delete_many({})
    deleted_invoices = await db.prestataire_invoices.delete_many({})
    
    logger.info(f"Billing stats reset by {current_user['id']}: {deleted_payments.deleted_count} payments, {deleted_receipts.deleted_count} receipts, {deleted_invoices.deleted_count} invoices")
    
    return {
        "message": "Statistiques de facturation remises à zéro",
        "deleted": {
            "teacher_payments": deleted_payments.deleted_count,
            "student_receipts": deleted_receipts.deleted_count,
            "prestataire_invoices": deleted_invoices.deleted_count
        }
    }


@api_router.delete("/secretary/teacher-payments/{payment_id}")
async def delete_teacher_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a teacher payment"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.teacher_payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    
    logger.info(f"Teacher payment {payment_id} deleted by {current_user['id']}")
    return {"message": "Paiement supprimé avec succès"}

@api_router.delete("/secretary/student-receipts/{receipt_id}")
async def delete_student_receipt(receipt_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a student receipt"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.student_receipts.delete_one({"id": receipt_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reçu non trouvé")
    
    logger.info(f"Student receipt {receipt_id} deleted by {current_user['id']}")
    return {"message": "Reçu supprimé avec succès"}

@api_router.delete("/secretary/prestataire-invoices/{invoice_id}")
async def delete_prestataire_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a prestataire invoice"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    result = await db.prestataire_invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    logger.info(f"Prestataire invoice {invoice_id} deleted by {current_user['id']}")
    return {"message": "Facture supprimée avec succès"}


@api_router.get("/secretary/teachers-list")
async def get_teachers_list_for_secretary(current_user: dict = Depends(get_current_user)):
    """Get list of all teachers for secretary billing"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    teachers = await db.users.find(
        {"role": "teacher", "is_active": True}, 
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    ).to_list(100)
    return teachers

@api_router.get("/secretary/students-list")
async def get_students_list_for_secretary(current_user: dict = Depends(get_current_user)):
    """Get list of all students for secretary billing"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    students = await db.users.find(
        {"role": "student", "is_active": True}, 
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "level": 1}
    ).to_list(500)
    return students

@api_router.get("/secretary/admin-info")
async def get_admin_info_for_secretary(current_user: dict = Depends(get_current_user)):
    """Get admin info for secretary messaging"""
    if current_user['role'] not in ['secretary', 'admin']:
        raise HTTPException(status_code=403, detail="Secretary or admin access required")
    
    admin = await db.users.find_one(
        {"role": "admin", "is_active": True}, 
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    )
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

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

@api_router.post("/auth/mark-welcome-letter-opened")
async def mark_welcome_letter_opened(current_user: dict = Depends(get_current_user)):
    """Mark welcome letter as opened for first-time users"""
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {
            "first_login": False,
            "welcome_letter_opened_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    logger.info(f"Welcome letter opened by user {current_user['id']}")
    return {"message": "Welcome letter marked as opened"}

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

@api_router.post("/admin/change-student-teacher")
async def change_student_teacher(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Change the assigned teacher for a student"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student_id = data.get('student_id')
    new_teacher_id = data.get('new_teacher_id')
    
    if not student_id:
        raise HTTPException(status_code=400, detail="Student ID required")
    
    # Update student's assigned teacher
    update_data = {"assigned_teacher": new_teacher_id} if new_teacher_id else {"assigned_teacher": None}
    
    result = await db.users.update_one(
        {"id": student_id, "role": "student"},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # If new teacher assigned, update teacher's students list
    if new_teacher_id:
        await db.users.update_one(
            {"id": new_teacher_id, "role": "teacher"},
            {"$addToSet": {"students": student_id}}
        )
    
    logger.info(f"Admin {current_user['id']} changed teacher for student {student_id} to {new_teacher_id}")
    
    return {"message": "Teacher changed successfully"}

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
    
    # Générer le mot de passe Digika pour la bibliothèque
    digika_password = f"DIGIKA{user_id[:4].upper()}"
    
    # Sauvegarder le Digika dans la base
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"digika_password": digika_password}}
    )
    
    # Envoyer les infos à Monday.com CRM avec mot de passe et Digika
    try:
        from monday_integration import create_monday_item, generate_welcome_email_html
        
        # Créer l'item dans Monday.com avec le mot de passe et Digika
        monday_item_id = create_monday_item({
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'level': user.get('level', 'beginner'),
            'temporary_password': temp_password,
            'digika_password': digika_password,
        })
        
        if monday_item_id:
            logger.info(f"Student {user_id} added to Monday.com with credentials: {monday_item_id}")
            
            # Sauvegarder l'ID Monday.com dans la base
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"monday_item_id": monday_item_id}}
            )
            
            # Générer le contenu HTML de l'email de bienvenue
            welcome_email_html = generate_welcome_email_html({
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'email': user.get('email', ''),
                'level': user.get('level', 'beginner'),
                'temporary_password': temp_password,
                'digika_password': digika_password,
            })
            
            # Sauvegarder l'email HTML pour envoi via Monday automation
            await db.pending_welcome_emails.insert_one({
                "id": str(uuid4()),
                "user_id": user_id,
                "email": user.get('email', ''),
                "html_content": welcome_email_html,
                "subject": f"Hello and Welcome to MyKalama - {user.get('first_name', '')}!",
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
    except Exception as e:
        logger.error(f"Monday.com integration error: {e}")
    
    # Send level-based welcome email
    await email_service.send_level_based_welcome_email(
        user['email'],
        user['first_name'],
        user.get('level', 'beginner'),
        temp_password,
        user.get('last_name', '')
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
    
    logger.info(f"User {user_id} approved, email and welcome letter created (Level: {user.get('level', 'beginner')}). Monday.com integration attempted.")
    
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

# ========== COURSE SUMMARIES / REVISION SYSTEM ==========

@api_router.post("/teacher/create-course-summary")
async def create_course_summary(summary_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher creates a course summary with rich text formatting"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    summary = {
        "id": str(uuid4()),
        "teacher_id": current_user['id'],
        "teacher_name": f"{current_user['first_name']} {current_user['last_name']}",
        "title": summary_data['title'],
        "content": summary_data['content'],  # HTML content with formatting
        "comments": summary_data.get('comments', ''),
        "student_ids": summary_data.get('student_ids', []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.course_summaries.insert_one(summary)
    
    # Notify students
    for student_id in summary_data.get('student_ids', []):
        await create_notification(
            user_id=student_id,
            title="Nouveau résumé de cours",
            message=f"Nouveau résumé de cours: {summary_data['title']}",
            notification_type="new_summary"
        )
    
    logger.info(f"Course summary created by teacher {current_user['id']}: {summary_data['title']}")
    return {"message": "Résumé de cours créé avec succès", "summary_id": summary["id"]}

@api_router.get("/teacher/my-course-summaries")
async def get_teacher_course_summaries(current_user: dict = Depends(get_current_user)):
    """Get all course summaries created by the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    summaries = await db.course_summaries.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with student names
    for summary in summaries:
        student_names = []
        for sid in summary.get('student_ids', []):
            student = await db.users.find_one({"id": sid}, {"_id": 0, "first_name": 1, "last_name": 1})
            if student:
                student_names.append(f"{student['first_name']} {student['last_name']}")
        summary['student_names'] = student_names
        
        # Get question count
        questions = await db.summary_questions.count_documents({"summary_id": summary['id']})
        summary['question_count'] = questions
    
    return summaries

@api_router.put("/teacher/update-course-summary/{summary_id}")
async def update_course_summary(summary_id: str, summary_data: dict, current_user: dict = Depends(get_current_user)):
    """Update a course summary"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.course_summaries.update_one(
        {"id": summary_id, "teacher_id": current_user['id']},
        {"$set": {
            "title": summary_data.get('title'),
            "content": summary_data.get('content'),
            "comments": summary_data.get('comments', ''),
            "student_ids": summary_data.get('student_ids', []),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return {"message": "Résumé mis à jour avec succès"}

@api_router.delete("/teacher/delete-course-summary/{summary_id}")
async def delete_course_summary(summary_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a course summary"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.course_summaries.delete_one({"id": summary_id, "teacher_id": current_user['id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Also delete related questions
    await db.summary_questions.delete_many({"summary_id": summary_id})
    
    return {"message": "Résumé supprimé avec succès"}

@api_router.get("/student/my-course-summaries")
async def get_student_course_summaries(current_user: dict = Depends(get_current_user)):
    """Get all course summaries sent to the student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    summaries = await db.course_summaries.find(
        {"student_ids": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Mark as read and get question status
    for summary in summaries:
        # Check if student has unread questions
        unread_answers = await db.summary_questions.count_documents({
            "summary_id": summary['id'],
            "student_id": current_user['id'],
            "answer": {"$exists": True},
            "answer_read": {"$ne": True}
        })
        summary['unread_answers'] = unread_answers
    
    return summaries

@api_router.post("/student/ask-summary-question")
async def ask_summary_question(question_data: dict, current_user: dict = Depends(get_current_user)):
    """Student asks a question about a course summary"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Verify student has access to this summary
    summary = await db.course_summaries.find_one(
        {"id": question_data['summary_id'], "student_ids": current_user['id']},
        {"_id": 0}
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found or access denied")
    
    question = {
        "id": str(uuid4()),
        "summary_id": question_data['summary_id'],
        "student_id": current_user['id'],
        "student_name": f"{current_user['first_name']} {current_user['last_name']}",
        "teacher_id": summary['teacher_id'],
        "question": question_data.get('question', ''),
        "question_audio_url": question_data.get('question_audio_url'),
        "answer": None,
        "answer_audio_url": None,
        "question_read": False,
        "answer_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.summary_questions.insert_one(question)
    
    # Notify teacher via database notification
    try:
        await create_notification(
            user_id=summary['teacher_id'],
            notification_type="summary_question",
            data={"message": f"Question de {current_user['first_name']}: {question_data.get('question', 'Message vocal')[:50]}..."}
        )
    except Exception as e:
        logger.warning(f"Failed to create notification: {e}")
    
    # Send real-time WebSocket notification to teacher
    try:
        await ws_manager.send_personal_notification(
            user_id=summary['teacher_id'],
            notification={
                "type": "new_question",
                "title": "📩 Nouvelle Question",
                "message": f"{current_user['first_name']} a posé une question sur '{summary.get('title', 'Résumé')}'",
                "summary_id": question_data['summary_id'],
                "question_id": question['id'],
                "student_name": f"{current_user['first_name']} {current_user['last_name']}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket notification: {e}")
    
    logger.info(f"Summary question from student {current_user['id']} on summary {question_data['summary_id']}")
    return {"message": "Question envoyée avec succès", "question": question}

@api_router.post("/student/upload-question-audio")
async def upload_question_audio(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload audio file for student voice question"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    allowed_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/webm', 'audio/ogg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'webm'
    unique_filename = f"student_audio_{uuid4()}.{file_extension}"
    file_path = f"/app/uploads/audio/{unique_filename}"
    
    os.makedirs("/app/uploads/audio", exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    file_url = f"/uploads/audio/{unique_filename}"
    return {"file_url": file_url, "message": "Audio uploadé avec succès"}

@api_router.delete("/student/delete-question/{question_id}")
async def delete_student_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Student deletes their own question"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    result = await db.summary_questions.delete_one({
        "id": question_id,
        "student_id": current_user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question supprimée"}

@api_router.delete("/teacher/delete-question/{question_id}")
async def delete_teacher_question(question_id: str, current_user: dict = Depends(get_current_user)):
    """Teacher deletes a question"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    result = await db.summary_questions.delete_one({
        "id": question_id,
        "teacher_id": current_user['id']
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question supprimée"}

@api_router.put("/teacher/mark-question-read/{question_id}")
async def mark_question_read(question_id: str, current_user: dict = Depends(get_current_user)):
    """Teacher marks question as read"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    await db.summary_questions.update_one(
        {"id": question_id, "teacher_id": current_user['id']},
        {"$set": {"question_read": True}}
    )
    return {"message": "Question marquée comme lue"}

@api_router.put("/student/mark-answer-read/{question_id}")
async def mark_answer_read(question_id: str, current_user: dict = Depends(get_current_user)):
    """Student marks an answer as read"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    await db.summary_questions.update_one(
        {"id": question_id, "student_id": current_user['id']},
        {"$set": {"answer_read": True}}
    )
    return {"message": "Réponse marquée comme lue"}

@api_router.get("/teacher/summary-questions/{summary_id}")
async def get_summary_questions(summary_id: str, current_user: dict = Depends(get_current_user)):
    """Get all questions for a specific summary"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    questions = await db.summary_questions.find(
        {"summary_id": summary_id, "teacher_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return questions

@api_router.get("/teacher/all-summary-questions")
async def get_all_summary_questions(current_user: dict = Depends(get_current_user)):
    """Get all unanswered questions for the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    questions = await db.summary_questions.find(
        {"teacher_id": current_user['id'], "answer": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with summary titles
    for q in questions:
        summary = await db.course_summaries.find_one({"id": q['summary_id']}, {"_id": 0, "title": 1})
        q['summary_title'] = summary['title'] if summary else "Résumé supprimé"
    
    return questions

@api_router.post("/teacher/answer-summary-question/{question_id}")
async def answer_summary_question(question_id: str, answer_data: dict, current_user: dict = Depends(get_current_user)):
    """Teacher answers a student's question (text or audio)"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    update_data = {
        "answered_at": datetime.now(timezone.utc).isoformat(),
        "answer_read": False
    }
    
    if answer_data.get('answer'):
        update_data['answer'] = answer_data['answer']
    if answer_data.get('answer_audio_url'):
        update_data['answer_audio_url'] = answer_data['answer_audio_url']
    
    result = await db.summary_questions.update_one(
        {"id": question_id, "teacher_id": current_user['id']},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get question to notify student
    question = await db.summary_questions.find_one({"id": question_id}, {"_id": 0})
    if question:
        # Database notification
        await create_notification(
            user_id=question['student_id'],
            title="Réponse du professeur",
            message="Réponse du professeur à votre question",
            notification_type="summary_answer"
        )
        
        # Real-time WebSocket notification to student
        try:
            await ws_manager.send_personal_notification(
                user_id=question['student_id'],
                notification={
                    "type": "new_answer",
                    "title": "✅ Réponse reçue",
                    "message": f"Le professeur {current_user['first_name']} a répondu à votre question",
                    "summary_id": question.get('summary_id'),
                    "question_id": question_id,
                    "teacher_name": f"{current_user['first_name']} {current_user['last_name']}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification: {e}")
    
    return {"message": "Réponse envoyée avec succès"}

@api_router.get("/student/my-summary-questions/{summary_id}")
async def get_student_summary_questions(summary_id: str, current_user: dict = Depends(get_current_user)):
    """Get student's questions and answers for a summary"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    questions = await db.summary_questions.find(
        {"summary_id": summary_id, "student_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Mark answers as read
    await db.summary_questions.update_many(
        {"summary_id": summary_id, "student_id": current_user['id'], "answer": {"$exists": True}},
        {"$set": {"answer_read": True}}
    )
    
    return questions

@api_router.post("/teacher/upload-audio-answer")
async def upload_audio_answer(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload audio file for voice answer"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Validate file type
    allowed_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/webm', 'audio/ogg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    
    # Save file
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp3'
    unique_filename = f"audio_{uuid4()}.{file_extension}"
    file_path = f"/app/frontend/public/uploads/audio/{unique_filename}"
    
    # Ensure directory exists
    os.makedirs("/app/frontend/public/uploads/audio", exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    file_url = f"/uploads/audio/{unique_filename}"
    logger.info(f"Audio answer uploaded by teacher {current_user['id']}: {file_url}")
    
    return {"file_url": file_url, "message": "Audio uploadé avec succès"}



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

async def create_notification(user_id: str, arg2=None, arg3=None, arg4=None, *, 
                             notification_type: str = None, data: dict = None, 
                             title: str = None, message: str = None):
    """Helper function to create notifications
    Supports multiple calling formats:
    1. create_notification(user_id, notification_type, data) - legacy 3-param format
    2. create_notification(user_id, title, message, notification_type) - 4-param positional
    3. create_notification(user_id, title=..., message=..., notification_type=...) - named params
    """
    # Determine which format was used
    actual_title = title
    actual_message = message
    actual_type = notification_type
    actual_data = data
    
    if isinstance(arg2, str) and isinstance(arg3, dict):
        # Format 1: create_notification(user_id, notification_type, data)
        actual_type = arg2
        actual_data = arg3
    elif isinstance(arg2, str) and isinstance(arg3, str) and isinstance(arg4, str):
        # Format 2: create_notification(user_id, title, message, notification_type)
        actual_title = arg2
        actual_message = arg3
        actual_type = arg4
    elif isinstance(arg2, str) and isinstance(arg3, str) and arg4 is None:
        # Format 2 with 3 positional: create_notification(user_id, title, message)
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
    
    # Handle legacy format with data dict
    if actual_data:
        notification.update(actual_data)
    
    # Handle named parameters
    if actual_title:
        notification["title"] = actual_title
    if actual_message:
        notification["message"] = actual_message
    
    await db.notifications.insert_one(notification)
    logger.info(f"Notification created for user {user_id}: {notification.get('type')}")
    return notification

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
    
    logger.info(f"Teacher {current_user['id']} requesting pending group students")
    
    # Find students assigned to this teacher, with course_type='group' and not yet active
    query = {
        "assigned_teacher": current_user['id'],
        "course_type": "group",
        "is_active": False
    }
    logger.info(f"Query: {query}")
    
    students = await db.users.find(
        query,
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
    students = await db.users.find(
        {
            "id": {"$in": data.student_ids},
            "assigned_teacher": current_user['id'],
            "course_type": "group",
            "is_active": False
        },
        {"_id": 0}
    ).to_list(1000)
    
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
            'Code de groupe généré',
            f"Le professeur {current_user['first_name']} {current_user['last_name']} a généré le code {magic_code} pour le groupe '{data.group_name}' ({len(students)} étudiants: {student_names})",
            'group_code_generated'
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
    # Get questions from database
    db_questions = await db.test_questions.find({"level": level, "active": True}, {"_id": 0}).to_list(100)
    
    # If no questions in DB, fallback to hardcoded questions
    if not db_questions:
        if level not in TEST_QUESTIONS:
            raise HTTPException(status_code=404, detail="Test not found")
        questions = [{"id": q["id"], "question": q["question"], "options": q["options"]} 
                     for q in TEST_QUESTIONS[level]]
    else:
        # Return questions without correct answers
        questions = [{"id": q["id"], "question": q["question"], "options": q.get("options", [])} 
                     for q in db_questions]
    
    return {"level": level, "questions": questions}

@api_router.post("/tests/submit")
async def submit_test(submission: TestSubmission):
    # Get questions from database first
    db_questions = await db.test_questions.find({"level": submission.level, "active": True}, {"_id": 0}).to_list(100)
    
    # If no questions in DB, fallback to hardcoded questions
    if not db_questions:
        if submission.level not in TEST_QUESTIONS:
            raise HTTPException(status_code=404, detail="Test not found")
        correct_answers = TEST_QUESTIONS[submission.level]
        
        # Calculate score with hardcoded questions
        score = 0
        for answer in submission.answers:
            correct = next((q for q in correct_answers if q["id"] == answer["question_id"]), None)
            if correct and correct["correct"] == answer["selected_option"]:
                score += 1
    else:
        # Calculate score with database questions
        score = 0
        for answer in submission.answers:
            correct = next((q for q in db_questions if q["id"] == answer["question_id"]), None)
            if correct and str(correct.get("correct_answer")) == str(answer["selected_option"]):
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
    
    # Enrichir avec les noms des candidats
    enriched_results = []
    for result in results:
        user = await db.users.find_one(
            {"id": result.get('user_id')},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        
        result_with_user = {**result}
        if user:
            result_with_user['candidate_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            result_with_user['candidate_email'] = user.get('email', '')
        else:
            result_with_user['candidate_name'] = 'Candidat anonyme'
            result_with_user['candidate_email'] = ''
        
        enriched_results.append(result_with_user)
    
    return enriched_results

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

class HomeworkDocumentCreate(BaseModel):
    title: str
    description: str
    recipient_type: str  # 'admin' or 'student'
    recipient_id: Optional[str] = None
    file_url: str

class HomeworkDocument(BaseModel):
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
    
    # Create upload directory if it doesn't exist (persistent storage)
    upload_dir = Path("/app/uploads")
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
async def send_homework_document(doc_data: HomeworkDocumentCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get teacher info
    teacher = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    document = HomeworkDocument(
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

@api_router.delete("/admin/teacher-sessions/{session_id}")
async def delete_teacher_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a specific teacher attendance session"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.teacher_sessions.delete_one({"id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    # Also delete the notification if exists
    await db.admin_notifications.delete_one({"session_id": session_id})
    
    logger.info(f"Session {session_id} deleted by admin {current_user['id']}")
    return {"message": "Session supprimée avec succès"}

@api_router.delete("/admin/teacher-sessions")
async def delete_all_teacher_sessions(current_user: dict = Depends(get_current_user)):
    """Delete all teacher attendance sessions"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.teacher_sessions.delete_many({})
    await db.admin_notifications.delete_many({"type": "session_completed"})
    
    logger.info(f"All {result.deleted_count} sessions deleted by admin {current_user['id']}")
    return {"message": f"{result.deleted_count} sessions supprimées"}

@api_router.get("/admin/monthly-teacher-hours")
async def get_monthly_teacher_hours(month: int = None, year: int = None, current_user: dict = Depends(get_current_user)):
    """Get monthly summary of hours worked by each teacher based on attendance"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Use current month if not specified
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year
    
    # Get start and end of month
    start_date = datetime(target_year, target_month, 1, tzinfo=timezone.utc)
    if target_month == 12:
        end_date = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(target_year, target_month + 1, 1, tzinfo=timezone.utc)
    
    # Get all completed sessions for this month
    sessions = await db.teacher_sessions.find({
        "status": "completed",
        "end_time": {
            "$gte": start_date.isoformat(),
            "$lt": end_date.isoformat()
        }
    }, {"_id": 0}).to_list(10000)
    
    # Group by teacher
    teacher_hours = {}
    for session in sessions:
        teacher_id = session['teacher_id']
        if teacher_id not in teacher_hours:
            teacher_hours[teacher_id] = {
                "teacher_id": teacher_id,
                "teacher_name": session.get('teacher_name', 'Inconnu'),
                "teacher_email": session.get('teacher_email', ''),
                "total_minutes": 0,
                "total_sessions": 0,
                "sessions": []
            }
        
        # Calculate duration from total_time (in seconds) or from times
        duration_minutes = session.get('total_time', 0) / 60
        if duration_minutes == 0 and session.get('start_time') and session.get('end_time'):
            try:
                start = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(session['end_time'].replace('Z', '+00:00'))
                duration_minutes = (end - start).total_seconds() / 60
            except:
                pass
        
        teacher_hours[teacher_id]['total_minutes'] += duration_minutes
        teacher_hours[teacher_id]['total_sessions'] += 1
        teacher_hours[teacher_id]['sessions'].append({
            "date": session.get('end_time', session.get('created_at')),
            "duration_minutes": round(duration_minutes, 2)
        })
    
    # Convert to list and format
    result = []
    for data in teacher_hours.values():
        total_hours = data['total_minutes'] / 60
        result.append({
            "teacher_id": data['teacher_id'],
            "teacher_name": data['teacher_name'],
            "teacher_email": data['teacher_email'],
            "total_hours": round(total_hours, 2),
            "total_minutes": round(data['total_minutes'], 2),
            "total_sessions": data['total_sessions'],
            "sessions": data['sessions'][-10:]  # Last 10 sessions
        })
    
    # Sort by total hours descending
    result.sort(key=lambda x: x['total_hours'], reverse=True)
    
    return {
        "month": target_month,
        "year": target_year,
        "month_name": ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                       "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"][target_month],
        "teachers": result,
        "total_teachers": len(result),
        "total_hours_all": round(sum(t['total_hours'] for t in result), 2)
    }

@api_router.get("/admin/analytics")
async def get_admin_analytics(period: str = "month", current_user: dict = Depends(get_current_user)):
    """Get comprehensive analytics for admin dashboard"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    
    # Calculate date ranges based on period
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # month
        start_date = now - timedelta(days=30)
    
    # Get student counts
    total_students = await db.users.count_documents({"role": "student"})
    active_students = await db.users.count_documents({"role": "student", "is_active": True})
    total_teachers = await db.users.count_documents({"role": "teacher"})
    
    # Get students by level
    levels = await db.users.aggregate([
        {"$match": {"role": "student"}},
        {"$group": {"_id": "$level", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    students_by_level = [
        {"name": l['_id'] or "Non défini", "value": l['count']} 
        for l in levels if l['_id']
    ]
    
    # Get monthly student growth (last 6 months)
    students_by_month = []
    month_names = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
    for i in range(5, -1, -1):
        target_date = now - timedelta(days=i*30)
        month_start = datetime(target_date.year, target_date.month, 1, tzinfo=timezone.utc)
        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1, tzinfo=timezone.utc)
        
        count = await db.users.count_documents({
            "role": "student",
            "created_at": {"$lt": month_end.isoformat()}
        })
        students_by_month.append({
            "month": month_names[target_date.month],
            "count": count
        })
    
    # Get hours by week (last 4 weeks)
    hours_by_week = []
    for i in range(3, -1, -1):
        week_start = now - timedelta(days=(i+1)*7)
        week_end = now - timedelta(days=i*7)
        
        sessions = await db.teacher_sessions.find({
            "status": "completed",
            "end_time": {"$gte": week_start.isoformat(), "$lt": week_end.isoformat()}
        }, {"_id": 0, "total_time_seconds": 1}).to_list(1000)
        
        total_hours = sum(s.get('total_time_seconds', 0) for s in sessions) / 3600
        hours_by_week.append({
            "week": f"Sem {4-i}",
            "hours": round(total_hours, 1)
        })
    
    # Get revenue by month (from payments)
    revenue_by_month = []
    for i in range(5, -1, -1):
        target_date = now - timedelta(days=i*30)
        month_start = datetime(target_date.year, target_date.month, 1, tzinfo=timezone.utc)
        if target_date.month == 12:
            month_end = datetime(target_date.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(target_date.year, target_date.month + 1, 1, tzinfo=timezone.utc)
        
        payments_eur = await db.payments.find({
            "currency": "EUR",
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        }, {"_id": 0, "amount": 1}).to_list(1000)
        
        payments_fcfa = await db.payments.find({
            "currency": "FCFA",
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        }, {"_id": 0, "amount": 1}).to_list(1000)
        
        revenue_by_month.append({
            "month": month_names[target_date.month],
            "eur": sum(p.get('amount', 0) for p in payments_eur),
            "fcfa": sum(p.get('amount', 0) for p in payments_fcfa)
        })
    
    # Get top teachers by hours this month
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    teacher_sessions = await db.teacher_sessions.find({
        "status": "completed",
        "end_time": {"$gte": month_start.isoformat()}
    }, {"_id": 0, "teacher_id": 1, "teacher_name": 1, "total_time_seconds": 1}).to_list(1000)
    
    teacher_hours = {}
    for s in teacher_sessions:
        tid = s.get('teacher_id')
        if tid:
            if tid not in teacher_hours:
                teacher_hours[tid] = {"name": s.get('teacher_name', 'Unknown'), "hours": 0, "students": 0}
            teacher_hours[tid]['hours'] += s.get('total_time_seconds', 0) / 3600
    
    # Count students per teacher
    for tid in teacher_hours:
        count = await db.users.count_documents({"assigned_teacher": tid, "role": "student"})
        teacher_hours[tid]['students'] = count
    
    top_teachers = sorted(
        [{"name": v['name'], "hours": round(v['hours'], 1), "students": v['students']} 
         for v in teacher_hours.values()],
        key=lambda x: x['hours'],
        reverse=True
    )[:5]
    
    # Calculate total hours this month
    total_hours_this_month = sum(t['hours'] for t in top_teachers)
    
    # Calculate growth rate
    prev_month_students = await db.users.count_documents({
        "role": "student",
        "created_at": {"$lt": month_start.isoformat()}
    })
    growth_rate = ((total_students - prev_month_students) / max(prev_month_students, 1)) * 100 if prev_month_students > 0 else 0
    
    # Total revenue
    total_eur = sum(r['eur'] for r in revenue_by_month[-1:])
    total_fcfa = sum(r['fcfa'] for r in revenue_by_month[-1:])
    
    return {
        "summary": {
            "total_students": total_students,
            "active_students": active_students,
            "total_teachers": total_teachers,
            "total_hours_this_month": round(total_hours_this_month, 1),
            "revenue_eur": total_eur,
            "revenue_fcfa": total_fcfa,
            "growth_rate": round(growth_rate, 1)
        },
        "students_by_month": students_by_month,
        "hours_by_week": hours_by_week,
        "revenue_by_month": revenue_by_month,
        "students_by_level": students_by_level,
        "top_teachers": top_teachers
    }


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
@api_router.post("/messages/upload-attachment")
async def upload_message_attachment(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a file attachment for messages"""
    from pathlib import Path
    
    # File size limit: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    contents = await file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Create upload directory (persistent storage)
    upload_dir = Path("/app/uploads/messages")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'file'
    unique_filename = f"{str(uuid4())}.{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        file_url = f"/uploads/messages/{unique_filename}"
        
        # Determine file type
        file_type = "other"
        if file_ext.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
            file_type = "image"
        elif file_ext.lower() in ['pdf']:
            file_type = "pdf"
        elif file_ext.lower() in ['doc', 'docx']:
            file_type = "document"
        elif file_ext.lower() in ['xls', 'xlsx']:
            file_type = "spreadsheet"
        elif file_ext.lower() in ['mp4', 'avi', 'mov', 'webm']:
            file_type = "video"
        elif file_ext.lower() in ['mp3', 'wav', 'ogg']:
            file_type = "audio"
        
        logger.info(f"Message attachment uploaded by {current_user['id']}: {file.filename}")
        
        return {
            "file_url": file_url,
            "filename": file.filename,
            "file_type": file_type
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")

@api_router.post("/messages/send")
async def send_message(message_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    # Get sender info
    sender = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    message = Message(
        from_user_id=current_user['id'],
        to_user_id=message_data.to_user_id,
        content=message_data.content,
        attachment=message_data.attachment
    )
    
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('attachment'):
        doc['attachment'] = dict(doc['attachment'])
    await db.messages.insert_one(doc)
    
    # Create notification for recipient
    attachment_text = " avec une pièce jointe" if message_data.attachment else ""
    await create_notification(
        user_id=message_data.to_user_id,
        title=f"💬 Nouveau message",
        message=f"{sender['first_name']} {sender['last_name']} vous a envoyé un message{attachment_text}",
        notification_type="message"
    )
    
    return {"message": "Message sent", "attachment_sent": message_data.attachment is not None}

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

# ==================== DOCUMENTS ENDPOINTS ====================

@api_router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a document file"""
    from pathlib import Path
    
    # File size limit: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024
    contents = await file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    # Create upload directory (persistent storage)
    upload_dir = Path("/app/uploads/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'file'
    unique_filename = f"{str(uuid4())}.{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        file_url = f"/uploads/documents/{unique_filename}"
        
        # Determine file type
        file_type = "other"
        if file_ext.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
            file_type = "image"
        elif file_ext.lower() in ['pdf']:
            file_type = "pdf"
        elif file_ext.lower() in ['doc', 'docx']:
            file_type = "document"
        elif file_ext.lower() in ['xls', 'xlsx']:
            file_type = "spreadsheet"
        elif file_ext.lower() in ['ppt', 'pptx']:
            file_type = "presentation"
        elif file_ext.lower() in ['mp4', 'avi', 'mov', 'webm']:
            file_type = "video"
        elif file_ext.lower() in ['mp3', 'wav', 'ogg']:
            file_type = "audio"
        
        logger.info(f"Document uploaded by {current_user['id']}: {file.filename}")
        
        return {
            "file_url": file_url,
            "file_name": file.filename,
            "file_type": file_type
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading file")

@api_router.post("/documents/send")
async def send_document(document_data: DocumentCreate, current_user: dict = Depends(get_current_user)):
    """Send a document to students"""
    # Verify sender is admin or teacher
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Only admins and teachers can send documents")
    
    sender = await db.users.find_one({"id": current_user['id']}, {"_id": 0})
    
    document = Document(
        title=document_data.title,
        description=document_data.description,
        file_url=document_data.file_url,
        file_name=document_data.file_name,
        file_type=document_data.file_type,
        sender_id=current_user['id'],
        sender_name=f"{sender['first_name']} {sender['last_name']}" if current_user['role'] == 'teacher' else "Admin KALAMA",
        sender_role=current_user['role'],
        recipient_ids=document_data.recipient_ids,
        read_by=[]
    )
    
    doc = document.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.documents.insert_one(doc)
    
    # Create notification for each recipient
    for recipient_id in document_data.recipient_ids:
        await create_notification(
            user_id=recipient_id,
            title=f"📄 Nouveau document",
            message=f"{document.sender_name} vous a envoyé un document: {document_data.title}",
            notification_type="document"
        )
    
    logger.info(f"Document sent by {current_user['id']} to {len(document_data.recipient_ids)} student(s)")
    
    return {"message": "Document sent successfully", "recipients_count": len(document_data.recipient_ids)}

@api_router.get("/documents/my-documents")
async def get_my_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents for current user (students receive, admin/teachers see sent)"""
    if current_user['role'] == 'student':
        # Students see documents sent to them
        documents = await db.documents.find(
            {"recipient_ids": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        # Add 'is_read' flag for each document
        for doc in documents:
            doc['is_read'] = current_user['id'] in doc.get('read_by', [])
        
        return documents
    else:
        # Admin and teachers see documents they sent
        documents = await db.documents.find(
            {"sender_id": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return documents

@api_router.put("/documents/{document_id}/mark-read")
async def mark_document_as_read(document_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a document as read by current student"""
    # Add current user to read_by list if not already there
    result = await db.documents.update_one(
        {"id": document_id, "recipient_ids": current_user['id']},
        {"$addToSet": {"read_by": current_user['id']}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Document not found or already marked as read")
    
    return {"message": "Document marked as read"}

@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document (only sender can delete)"""
    # Find document
    document = await db.documents.find_one({"id": document_id}, {"_id": 0})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify sender
    if document['sender_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="You can only delete your own documents")
    
    # Delete from database
    await db.documents.delete_one({"id": document_id})
    
    # Optionally delete file from disk
    try:
        from pathlib import Path
        file_path = Path(f"/app/frontend/public{document['file_url']}")
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning(f"Could not delete file: {str(e)}")
    
    logger.info(f"Document deleted by {current_user['id']}: {document_id}")
    
    return {"message": "Document deleted successfully"}

# ==================== PROGRESSION & MEET LINKS ENDPOINTS ====================

@api_router.post("/teacher/send-meet-link")
async def send_meet_link(data: MeetLinkCreate, current_user: dict = Depends(get_current_user)):
    """Teacher sends a Google Meet link to a student"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    meet_link = MeetLink(
        student_id=data.student_id,
        teacher_id=current_user['id'],
        meet_link=data.meet_link,
        title=data.title,
        scheduled_date=datetime.fromisoformat(data.scheduled_date.replace('Z', '+00:00'))
    )
    
    doc = meet_link.model_dump()
    doc['scheduled_date'] = doc['scheduled_date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    # Add teacher name for display in student dashboard
    doc['teacher_name'] = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
    await db.meet_links.insert_one(doc)
    
    # Create notification for student
    await create_notification(
        user_id=data.student_id,
        title="📅 Nouveau cours programmé",
        message=f"Votre professeur vous a envoyé un lien de cours: {data.title}",
        notification_type="meet_link"
    )
    
    # 🎁 Coffre aux Trésors: Ajouter +1 point pour chaque lien de cours reçu
    await add_student_points(
        student_id=data.student_id, 
        points=1, 
        reason=f"Lien de cours reçu: {data.title}"
    )
    
    logger.info(f"Meet link sent by teacher {current_user['id']} to student {data.student_id}")
    return {"message": "Lien de cours envoyé", "meet_link_id": meet_link.id}

@api_router.get("/student/my-meet-links")
async def get_my_meet_links(current_user: dict = Depends(get_current_user)):
    """Get all meet links for current student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    meet_links = await db.meet_links.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).sort("scheduled_date", -1).to_list(100)
    
    return meet_links

@api_router.put("/student/mark-meet-attended/{meet_id}")
async def mark_meet_attended(meet_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a meet link as attended by student"""

# ========== STUDENT AVAILABILITY SYSTEM ==========

@api_router.post("/student/set-availability")
async def set_student_availability(data: dict, current_user: dict = Depends(get_current_user)):
    """Student sets their weekly availability"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    availability = {
        "student_id": current_user['id'],
        "student_name": f"{current_user['first_name']} {current_user['last_name']}",
        "slots": data.get('slots', []),  # List of {day: "monday", time: "09:00", available: true}
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert - update if exists, insert if not
    await db.student_availability.update_one(
        {"student_id": current_user['id']},
        {"$set": availability},
        upsert=True
    )
    
    return {"message": "Disponibilités enregistrées", "availability": availability}

@api_router.get("/student/my-availability")
async def get_student_availability(current_user: dict = Depends(get_current_user)):
    """Get student's own availability"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    availability = await db.student_availability.find_one(
        {"student_id": current_user['id']},
        {"_id": 0}
    )
    
    return availability or {"slots": []}

@api_router.get("/teacher/students-availability")
async def get_students_availability_for_teacher(current_user: dict = Depends(get_current_user)):
    """Teacher gets availability of their assigned students"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get teacher's assigned students
    students = await db.users.find(
        {"role": "student", "assigned_teacher": current_user['id']},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    ).to_list(1000)
    
    student_ids = [s['id'] for s in students]
    
    # Get availability for these students
    availabilities = await db.student_availability.find(
        {"student_id": {"$in": student_ids}},
        {"_id": 0}
    ).to_list(1000)
    
    # Merge student info with availability
    result = []
    for student in students:
        avail = next((a for a in availabilities if a['student_id'] == student['id']), {"slots": []})
        result.append({
            "student_id": student['id'],
            "student_name": f"{student['first_name']} {student['last_name']}",
            "email": student.get('email'),
            "slots": avail.get('slots', []),
            "updated_at": avail.get('updated_at')
        })
    
    return result

@api_router.get("/admin/all-students-availability")
async def get_all_students_availability(current_user: dict = Depends(get_current_user)):
    """Admin gets availability of all students"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all students
    students = await db.users.find(
        {"role": "student"},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "assigned_teacher": 1}
    ).to_list(1000)
    
    # Get all availabilities
    availabilities = await db.student_availability.find({}, {"_id": 0}).to_list(1000)
    
    # Merge
    result = []
    for student in students:
        avail = next((a for a in availabilities if a['student_id'] == student['id']), {"slots": []})
        
        # Get teacher name if assigned
        teacher_name = None
        if student.get('assigned_teacher'):
            teacher = await db.users.find_one({"id": student['assigned_teacher']}, {"_id": 0, "first_name": 1, "last_name": 1})
            if teacher:
                teacher_name = f"{teacher['first_name']} {teacher['last_name']}"
        
        result.append({
            "student_id": student['id'],
            "student_name": f"{student['first_name']} {student['last_name']}",
            "email": student.get('email'),
            "teacher_name": teacher_name,
            "slots": avail.get('slots', []),
            "updated_at": avail.get('updated_at')
        })
    
    return result

@api_router.get("/student/my-progression")
async def get_my_progression(current_user: dict = Depends(get_current_user)):
    """Get student progression statistics"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get all meet links
    all_meets = await db.meet_links.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    # Calculate statistics
    total_courses = len(all_meets)
    completed_courses = len([m for m in all_meets if m.get('attended', False)])
    
    # Calculate percentage
    percentage = round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0
    
    # Calculate consecutive days (simplified - count unique dates of attended courses in last 30 days)
    now = datetime.now(timezone.utc)
    recent_attended = [
        m for m in all_meets 
        if m.get('attended', False) and 
        datetime.fromisoformat(m['scheduled_date'].replace('Z', '+00:00')) > now - timedelta(days=30)
    ]
    
    # Get unique dates
    attended_dates = set()
    for m in recent_attended:
        date = datetime.fromisoformat(m['scheduled_date'].replace('Z', '+00:00')).date()
        attended_dates.add(date)
    
    # Calculate consecutive days
    consecutive_days = 0
    if attended_dates:
        sorted_dates = sorted(attended_dates, reverse=True)
        consecutive_days = 1
        for i in range(len(sorted_dates) - 1):
            if (sorted_dates[i] - sorted_dates[i+1]).days == 1:
                consecutive_days += 1
            else:
                break
    
    return {
        "percentage": percentage,
        "consecutive_days": consecutive_days,
        "courses_completed": completed_courses,
        "total_courses": total_courses
    }

# ==================== BADGES ENDPOINTS ====================

@api_router.post("/admin/create-badge")
async def create_badge(data: BadgeCreate, current_user: dict = Depends(get_current_user)):
    """Admin creates a new badge"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    badge = Badge(
        name=data.name,
        icon=data.icon,
        description=data.description,
        condition_type=data.condition_type,
        condition_value=data.condition_value
    )
    
    doc = badge.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.badges.insert_one(doc)
    
    logger.info(f"Badge created by admin: {badge.name}")
    return {"message": "Badge créé", "badge_id": badge.id}

@api_router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    badges = await db.badges.find({}, {"_id": 0}).to_list(100)
    return badges

@api_router.post("/admin/award-badge")
async def award_badge(data: dict, current_user: dict = Depends(get_current_user)):
    """Admin awards a badge to a student"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student_id = data['student_id']
    badge_id = data['badge_id']
    
    # Check if student already has this badge
    existing = await db.student_badges.find_one({
        "student_id": student_id,
        "badge_id": badge_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Badge déjà attribué")
    
    student_badge = StudentBadge(
        student_id=student_id,
        badge_id=badge_id
    )
    
    doc = student_badge.model_dump()
    doc['awarded_at'] = doc['awarded_at'].isoformat()
    await db.student_badges.insert_one(doc)
    
    # Get badge info for notification
    badge = await db.badges.find_one({"id": badge_id}, {"_id": 0})
    
    # Create notification
    await create_notification(
        user_id=student_id,
        title=f"🏆 Nouveau badge obtenu !",
        message=f"Félicitations ! Vous avez reçu le badge '{badge['name']}'",
        notification_type="badge"
    )
    
    logger.info(f"Badge {badge_id} awarded to student {student_id}")
    return {"message": "Badge attribué"}

@api_router.get("/student/my-badges")
async def get_my_badges(current_user: dict = Depends(get_current_user)):
    """Get all badges for current student"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get student's badge IDs
    student_badges = await db.student_badges.find(
        {"student_id": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    badge_ids = [sb['badge_id'] for sb in student_badges]
    
    # Get all badges
    all_badges = await db.badges.find({}, {"_id": 0}).to_list(100)
    
    # Mark which badges the student has
    for badge in all_badges:
        badge['earned'] = badge['id'] in badge_ids
        if badge['earned']:
            sb = next((sb for sb in student_badges if sb['badge_id'] == badge['id']), None)
            if sb:
                badge['awarded_at'] = sb.get('awarded_at')
    
    return all_badges

@api_router.delete("/admin/remove-badge/{student_id}/{badge_id}")
async def remove_badge(student_id: str, badge_id: str, current_user: dict = Depends(get_current_user)):
    """Admin removes a badge from a student"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.student_badges.delete_one({
        "student_id": student_id,
        "badge_id": badge_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Badge non trouvé")
    
    return {"message": "Badge retiré"}

# ==================== WEEKLY CHALLENGES & POINTS ENDPOINTS ====================

@api_router.get("/challenges/current")
async def get_current_challenges():
    """Get current week's challenges"""
    now = datetime.now(timezone.utc)
    challenges = await db.weekly_challenges.find(
        {
            "active": True,
            "week_start": {"$lte": now},
            "week_end": {"$gte": now}
        },
        {"_id": 0}
    ).to_list(100)
    return challenges

@api_router.get("/student/my-points")
async def get_my_points(current_user: dict = Depends(get_current_user)):
    """Get student's points and discount - Coffre aux Trésors"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get or create student points record
    points_record = await db.student_points.find_one({"student_id": current_user['id']}, {"_id": 0})
    
    if not points_record:
        # Create new record
        points = StudentPoints(student_id=current_user['id'])
        doc = points.model_dump()
        doc['last_updated'] = doc['last_updated'].isoformat()
        await db.student_points.insert_one(doc)
        points_record = doc
    
    available_points = points_record.get('available_points', 0)
    
    # Système de récompenses par paliers
    rewards = {
        "unlocked": available_points >= 50,  # Réductions actives à partir de 50 points
        "current_tier": 0,
        "tiers": [
            {"points": 50, "discount_eur": 5, "discount_fcfa": 3000, "label": "🥉 Bronze", "unlocked": available_points >= 50},
            {"points": 100, "discount_eur": 12, "discount_fcfa": 7500, "label": "🥈 Argent", "unlocked": available_points >= 100},
            {"points": 200, "discount_eur": 25, "discount_fcfa": 15000, "label": "🥇 Or", "unlocked": available_points >= 200},
            {"points": 500, "discount_eur": 70, "discount_fcfa": 45000, "label": "💎 Diamant", "unlocked": available_points >= 500}
        ],
        "next_tier_points": 50 if available_points < 50 else (100 if available_points < 100 else (200 if available_points < 200 else (500 if available_points < 500 else None)))
    }
    
    # Déterminer le palier actuel
    if available_points >= 500:
        rewards["current_tier"] = 4
    elif available_points >= 200:
        rewards["current_tier"] = 3
    elif available_points >= 100:
        rewards["current_tier"] = 2
    elif available_points >= 50:
        rewards["current_tier"] = 1
    
    # Calculer la réduction actuelle basée sur le palier
    current_discount_eur = 0
    current_discount_fcfa = 0
    if rewards["current_tier"] > 0:
        tier_index = rewards["current_tier"] - 1
        current_discount_eur = rewards["tiers"][tier_index]["discount_eur"]
        current_discount_fcfa = rewards["tiers"][tier_index]["discount_fcfa"]
    
    return {
        "total_points": points_record.get('total_points', 0),
        "available_points": available_points,
        "rewards": rewards,
        "current_discount_eur": current_discount_eur,
        "current_discount_fcfa": current_discount_fcfa,
        "points_to_next_tier": (rewards["next_tier_points"] - available_points) if rewards["next_tier_points"] else 0,
        "total_discount_earned": points_record.get('total_discount_earned', 0)
    }


# ============ COURS GROUPÉS (GROUP COURSES) ============

@api_router.get("/group-courses")
async def get_group_courses():
    """Get all available group courses"""
    courses = await db.group_courses.find(
        {"status": {"$in": ["open", "in_progress"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with teacher info and student count
    for course in courses:
        teacher = await db.users.find_one(
            {"id": course['teacher_id']},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if teacher:
            course['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
        course['enrolled_count'] = len(course.get('current_students', []))
        course['spots_left'] = course['max_students'] - course['enrolled_count']
        # Apply discount for 4+ students
        if course['enrolled_count'] >= 4:
            course['discount_applied'] = True
            course['final_price_eur'] = course['price_per_person_eur'] * (1 - course['discount_4_plus'] / 100)
            course['final_price_fcfa'] = course['price_per_person_fcfa'] * (1 - course['discount_4_plus'] / 100)
        else:
            course['discount_applied'] = False
            course['final_price_eur'] = course['price_per_person_eur']
            course['final_price_fcfa'] = course['price_per_person_fcfa']
    
    return courses

@api_router.post("/group-courses")
async def create_group_course(course_data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new group course (admin or teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    course = GroupCourse(
        title=course_data['title'],
        description=course_data.get('description', ''),
        teacher_id=course_data.get('teacher_id', current_user['id']),
        level=course_data['level'],
        max_students=course_data.get('max_students', 6),
        scheduled_days=course_data.get('scheduled_days', []),
        scheduled_time=course_data.get('scheduled_time', ''),
        price_per_person_eur=course_data.get('price_per_person_eur', 80.0),
        price_per_person_fcfa=course_data.get('price_per_person_fcfa', 50000.0),
        discount_4_plus=course_data.get('discount_4_plus', 10),
        meet_link=course_data.get('meet_link', ''),
        start_date=course_data.get('start_date')
    )
    
    doc = course.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.group_courses.insert_one(doc)
    
    logger.info(f"Group course created: {course.title} by {current_user['id']}")
    return {"message": "Cours groupé créé", "course_id": course.id}

@api_router.post("/group-courses/{course_id}/enroll")
async def enroll_in_group_course(course_id: str, current_user: dict = Depends(get_current_user)):
    """Enroll in a group course"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    course = await db.group_courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    if course['status'] == 'full':
        raise HTTPException(status_code=400, detail="Ce cours est complet")
    
    if current_user['id'] in course.get('current_students', []):
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit à ce cours")
    
    # Add student to course
    current_students = course.get('current_students', [])
    current_students.append(current_user['id'])
    
    # Update status if full
    new_status = 'full' if len(current_students) >= course['max_students'] else 'open'
    
    await db.group_courses.update_one(
        {"id": course_id},
        {"$set": {"current_students": current_students, "status": new_status}}
    )
    
    # Create enrollment record
    enrollment = GroupCourseEnrollment(
        group_course_id=course_id,
        student_id=current_user['id']
    )
    enrollment_doc = enrollment.model_dump()
    enrollment_doc['enrolled_at'] = enrollment_doc['enrolled_at'].isoformat()
    await db.group_course_enrollments.insert_one(enrollment_doc)
    
    # Notify student
    await create_notification(
        user_id=current_user['id'],
        title="✅ Inscription au cours groupé",
        message=f"Vous êtes inscrit au cours: {course['title']}",
        notification_type="group_course"
    )
    
    # 🎁 Coffre aux Trésors: +2 points pour inscription cours groupé
    await add_student_points(
        student_id=current_user['id'],
        points=2,
        reason=f"Inscription cours groupé: {course['title']}"
    )
    
    logger.info(f"Student {current_user['id']} enrolled in group course {course_id}")
    return {"message": "Inscription réussie", "enrollment_id": enrollment.id}

@api_router.get("/student/my-group-courses")
async def get_my_group_courses(current_user: dict = Depends(get_current_user)):
    """Get all group courses the student is enrolled in"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Find courses where student is enrolled
    courses = await db.group_courses.find(
        {"current_students": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    for course in courses:
        teacher = await db.users.find_one(
            {"id": course['teacher_id']},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if teacher:
            course['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
        
        # Get other students in the group (for social features)
        course['group_members'] = []
        for student_id in course.get('current_students', []):
            if student_id != current_user['id']:
                student = await db.users.find_one(
                    {"id": student_id},
                    {"_id": 0, "first_name": 1, "last_name": 1}
                )
                if student:
                    course['group_members'].append(f"{student['first_name']} {student['last_name'][0]}.")
    
    return courses

@api_router.get("/teacher/my-group-courses")
async def get_teacher_group_courses(current_user: dict = Depends(get_current_user)):
    """Get all group courses taught by the teacher"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    courses = await db.group_courses.find(
        {"teacher_id": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    for course in courses:
        course['enrolled_count'] = len(course.get('current_students', []))
        # Get student details
        course['students'] = []
        for student_id in course.get('current_students', []):
            student = await db.users.find_one(
                {"id": student_id},
                {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
            )
            if student:
                course['students'].append(student)
    
    return courses

@api_router.post("/teacher/group-courses/{course_id}/send-link")
async def send_group_meet_link(course_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Send meet link to all students in a group course"""
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    course = await db.group_courses.find_one({"id": course_id, "teacher_id": current_user['id']}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    # Update course meet link
    await db.group_courses.update_one(
        {"id": course_id},
        {"$set": {"meet_link": data.get('meet_link', '')}}
    )
    
    # Send notification and points to each student
    for student_id in course.get('current_students', []):
        await create_notification(
            user_id=student_id,
            title="📅 Cours groupé - Nouveau lien",
            message=f"Votre professeur a partagé le lien pour: {course['title']}",
            notification_type="meet_link"
        )
        # 🎁 +2 points pour chaque lien reçu
        await add_student_points(
            student_id=student_id,
            points=2,
            reason=f"Lien cours groupé: {course['title']}"
        )
    
    logger.info(f"Group meet link sent to {len(course.get('current_students', []))} students for course {course_id}")
    return {"message": f"Lien envoyé à {len(course.get('current_students', []))} étudiants"}


@api_router.get("/student/my-challenge-progress")
async def get_my_challenge_progress(current_user: dict = Depends(get_current_user)):
    """Get student's progress on current challenges"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get current challenges
    now = datetime.now(timezone.utc)
    challenges = await db.weekly_challenges.find(
        {
            "active": True,
            "week_start": {"$lte": now},
            "week_end": {"$gte": now}
        },
        {"_id": 0}
    ).to_list(100)
    
    # Get progress for each challenge
    for challenge in challenges:
        progress = await db.challenge_progress.find_one(
            {"student_id": current_user['id'], "challenge_id": challenge['id']},
            {"_id": 0}
        )
        challenge['progress'] = progress if progress else {
            "current_count": 0,
            "completed": False
        }
    
    return challenges

@api_router.post("/student/complete-challenge/{challenge_id}")
async def complete_challenge(challenge_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a challenge as completed and award points"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Student access required")
    
    # Get challenge
    challenge = await db.weekly_challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if already completed
    existing_progress = await db.challenge_progress.find_one({
        "student_id": current_user['id'],
        "challenge_id": challenge_id,
        "completed": True
    })
    
    if existing_progress:
        raise HTTPException(status_code=400, detail="Challenge already completed")
    
    # Mark as completed
    progress = ChallengeProgress(
        student_id=current_user['id'],
        challenge_id=challenge_id,
        current_count=challenge['target_count'],
        completed=True,
        completed_at=datetime.now(timezone.utc)
    )
    
    progress_doc = progress.model_dump()
    progress_doc['completed_at'] = progress_doc['completed_at'].isoformat()
    await db.challenge_progress.update_one(
        {"student_id": current_user['id'], "challenge_id": challenge_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    # Award points
    points_record = await db.student_points.find_one({"student_id": current_user['id']})
    
    if not points_record:
        points = StudentPoints(
            student_id=current_user['id'],
            total_points=challenge['points_reward'],
            available_points=challenge['points_reward']
        )
        doc = points.model_dump()
        doc['last_updated'] = doc['last_updated'].isoformat()
        await db.student_points.insert_one(doc)
    else:
        await db.student_points.update_one(
            {"student_id": current_user['id']},
            {
                "$inc": {
                    "total_points": challenge['points_reward'],
                    "available_points": challenge['points_reward']
                },
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    # Get updated points
    updated_points = await db.student_points.find_one({"student_id": current_user['id']}, {"_id": 0})
    
    # Check if student reached 50 points threshold - notify admin
    if updated_points['available_points'] >= 50:
        # Get admin
        admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
        if admin:
            await create_notification(
                user_id=admin['id'],
                title=f"💰 Étudiant a atteint 50 points",
                message=f"L'étudiant {current_user['id']} a atteint {updated_points['available_points']} points",
                notification_type="points_milestone"
            )
    
    # Notify student
    await create_notification(
        user_id=current_user['id'],
        title=f"🎉 Défi complété !",
        message=f"Vous avez gagné {challenge['points_reward']} points XP",
        notification_type="challenge_completed"
    )
    
    return {
        "message": "Défi complété !",
        "points_earned": challenge['points_reward'],
        "total_points": updated_points['total_points'],
        "available_points": updated_points['available_points']
    }

# ==================== NOTIFICATIONS ENDPOINTS ====================

@api_router.get("/notifications/my-notifications")
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    """Get all notifications for the current user"""
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    await db.notifications.update_many(
        {"user_id": current_user['id'], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    result = await db.notifications.delete_one(
        {"id": notification_id, "user_id": current_user['id']}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}

@api_router.delete("/notifications/clear-all")
async def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Delete all notifications for current user"""
    result = await db.notifications.delete_many({"user_id": current_user['id']})
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
    
    # Initialize default badges if they don't exist
    existing_badges = await db.badges.count_documents({})
    if existing_badges == 0:
        default_badges = [
            {
                "id": str(uuid4()),
                "name": "Débutant",
                "icon": "🚀",
                "description": "Première connexion",
                "condition_type": "first_login",
                "condition_value": 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Étudiant Assidu",
                "icon": "📚",
                "description": "5 cours complétés",
                "condition_type": "courses_completed",
                "condition_value": 5,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Expert",
                "icon": "⭐",
                "description": "10 cours complétés",
                "condition_type": "courses_completed",
                "condition_value": 10,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Champion",
                "icon": "🏆",
                "description": "Niveau complété",
                "condition_type": "level_completed",
                "condition_value": 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.badges.insert_many(default_badges)
        logger.info("Default badges created")

# ============ FILE UPLOAD ROUTE ============

@api_router.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    """Generic file upload endpoint"""
    try:
        # Create uploads directory if not exists (persistent storage)
        upload_dir = "/app/uploads"
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
    """Create news (Admin and Teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
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
    """Update news (Admin and Teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
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
    """Delete news (Admin and Teacher)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
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

@api_router.delete("/club/posts/{post_id}")
async def delete_club_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a club post (admin or teacher only)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    result = await db.club_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post non trouvé")
    
    # Also delete comments for this post
    await db.club_comments.delete_many({"post_id": post_id})
    
    logger.info(f"Club post deleted by {current_user['role']}: {post_id}")
    return {"message": "Post supprimé"}

@api_router.delete("/club/events/{event_id}")
async def delete_club_event(event_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a club event (admin or teacher only)"""
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")
    
    result = await db.club_events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    logger.info(f"Club event deleted by {current_user['role']}: {event_id}")
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


# Pydantic model for payment
class PaymentRequest(BaseModel):
    plan_name: str
    plan_level: str
    amount: int
    currency: str = "FCFA"
    promo_code: Optional[str] = None

# Payment endpoints
@api_router.post("/payments/create-checkout")
async def create_checkout_session(payment: PaymentRequest):
    """Create a Stripe checkout session (returns hardcoded links for now)"""
    
    plan_name = payment.plan_name
    plan_level = payment.plan_level
    amount = payment.amount
    currency = payment.currency
    promo_code = payment.promo_code
    
    # Mapping des liens Stripe directs par pack (mis à jour avec les vrais liens)
    stripe_links = {
        'kkid': 'https://buy.stripe.com/9B64gz8rFaJD7RB4q0',
        'beginner_without_club': 'https://buy.stripe.com/fZufZheQ304Z5Jtg8IenS00',
        'beginner_with_club': 'https://buy.stripe.com/fZufZheQ304Z5Jtg8IenS00',
        'intermediate_without_club': 'https://buy.stripe.com/dRmdR96jx5pjdbVf4EenS01',
        'intermediate_with_club': 'https://buy.stripe.com/dRmdR96jx5pjdbVf4EenS01',
        'advanced_without_club': 'https://buy.stripe.com/00w14nazNg3XefZ2hSenS02',
        'advanced_with_club': 'https://buy.stripe.com/00w14nazNg3XefZ2hSenS02'
    }
    
    # Déterminer la clé du lien
    if plan_level == 'kkid':
        link_key = 'kkid'
    else:
        # Détecter si c'est avec ou sans club basé sur le nom du pack
        has_club = 'Club' in plan_name or 'club' in plan_name.lower()
        link_key = f"{plan_level}_{'with' if has_club else 'without'}_club"
    
    checkout_url = stripe_links.get(link_key)
    
    if not checkout_url:
        logger.error(f"No Stripe link found for key: {link_key}")
        raise HTTPException(
            status_code=400, 
            detail=f"Lien de paiement non trouvé pour le pack {plan_name}"
        )
    
    # Ajouter le code promo à l'URL si fourni
    # Code promo par défaut de l'utilisateur
    default_promo = "promo_1SYGM3I4faCc3GWYbdYRPXX8"
    promo_to_apply = promo_code if promo_code else default_promo
    
    if promo_to_apply:
        # Ajouter le code promo comme paramètre URL
        separator = '&' if '?' in checkout_url else '?'
        checkout_url = f"{checkout_url}{separator}prefilled_promo_code={promo_to_apply}"
    
    logger.info(f"Payment link generated: {link_key} -> {checkout_url}")
    
    return {
        "checkout_url": checkout_url,
        "plan_name": plan_name,
        "amount": amount,
        "currency": currency,
        "promo_applied": promo_to_apply
    }

app.include_router(api_router)

# Create uploads directory if it doesn't exist
uploads_base_path = Path("/app/uploads")
uploads_base_path.mkdir(parents=True, exist_ok=True)
(uploads_base_path / "documents").mkdir(exist_ok=True)
(uploads_base_path / "messages").mkdir(exist_ok=True)

# Serve uploaded files via API endpoint instead of StaticFiles (better for Kubernetes)
@app.get("/uploads/{file_path:path}")
async def serve_uploaded_file(file_path: str):
    """Serve uploaded files from persistent storage with proper headers for iframe embedding"""
    from fastapi.responses import FileResponse, Response
    import mimetypes
    
    file_full_path = Path("/app/uploads") / file_path
    
    # Security check: ensure file is within uploads directory
    try:
        file_full_path.resolve().relative_to(Path("/app/uploads").resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    # Check if file exists
    if not file_full_path.exists() or not file_full_path.is_file():
        logger.warning(f"File not found: {file_full_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(file_full_path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    logger.info(f"Serving file: {file_path} ({mime_type})")
    
    # Read file content
    with open(file_full_path, "rb") as f:
        content = f.read()
    
    # Return response with headers that allow iframe embedding
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{file_full_path.name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=3600"
            # Removed X-Frame-Options to allow embedding from any origin
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ==================== WEBSOCKET FOR REAL-TIME NOTIFICATIONS ====================

@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Client can send 'ping' to keep connection alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)

@app.get("/api/ws/online-status")
async def get_online_status():
    """Get count of online users"""
    return {"online_users": ws_manager.get_online_users_count()}

