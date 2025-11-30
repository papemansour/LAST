from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
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

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
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

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_user_id: str
    to_user_id: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_read: bool = False

class MessageCreate(BaseModel):
    to_user_id: str
    content: str

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

# ============ UTILITIES ============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
    
    Lien dashboard: https://kalama-features.preview.emergentagent.com/admin
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
    
    return {"message": "Registration submitted. Please wait for admin approval."}

@api_router.post("/auth/register-group")
async def register_group(group_data: dict):
    """Register a group of students (max 3)"""
    members = group_data.get('members', [])
    
    if len(members) == 0 or len(members) > 3:
        raise HTTPException(status_code=400, detail="Group must have between 1 and 3 members")
    
    # Generate group ID
    group_id = str(uuid.uuid4())
    
    # Register each member
    registered_members = []
    for member in members:
        # Check if email already exists
        existing = await db.users.find_one({"email": member['email']}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail=f"Email {member['email']} already registered")
        
        # Create user
        user = User(
            email=member['email'],
            first_name=member['first_name'],
            last_name=member['last_name'],
            phone=member['phone'],
            level=member['level'],
            role="student",
            is_active=False,
            is_restricted=False,
            password_hash="",
            preferred_slots=group_data.get('preferred_slots', ''),
            referral_source=group_data.get('referral_source', '')
        )
        
        doc = user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['group_id'] = group_id  # Link members together
        doc['course_type'] = 'group'
        
        await db.users.insert_one(doc)
        registered_members.append(f"{member['first_name']} {member['last_name']}")
        
        # Send notification to admin for each member
        await email_service.send_admin_notification(
            member['email'],
            member['first_name'],
            member['last_name'],
            member['level'],
            member['phone']
        )
    
    logger.info(f"Group registration: {len(members)} members, group_id: {group_id}")
    
    return {
        "message": f"Group registration submitted for {len(members)} members",
        "group_id": group_id,
        "members": registered_members
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
    
    # Send welcome email
    await email_service.send_welcome_email(
        user['email'],
        user['first_name'],
        user['last_name'],
        temp_password
    )
    
    return {
        "message": "User approved and welcome email sent",
        "email": user['email'],
        "temporary_password": temp_password
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
    
    return {
        "message": "Teacher created",
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
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = await db.users.find_one({"id": student_id, "role": "student"}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Delete student from database
    await db.users.delete_one({"id": student_id})
    
    # Also delete related data (test results, messages, etc.)
    await db.test_results.delete_many({"user_id": student_id})
    await db.messages.delete_many({
        "$or": [
            {"from_user_id": student_id},
            {"to_user_id": student_id}
        ]
    })
    
    logger.info(f"Student deleted: {student['email']}")
    return {"message": "Student deleted successfully"}

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
    

@api_router.post("/admin/update-prices")
async def update_prices(prices: dict, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Store prices in database
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
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Get admin user
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    document = {
        "id": str(uuid.uuid4()),
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
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot delete admin")
    
    # Delete user and related data
    await db.users.delete_one({"id": user_id})
    await db.test_results.delete_many({"user_id": user_id})
    await db.messages.delete_many({"$or": [{"from_user_id": user_id}, {"to_user_id": user_id}]})
    await db.documents.delete_many({"$or": [{"teacher_id": user_id}, {"recipient_id": user_id}]})
    await db.student_homeworks.delete_many({"$or": [{"student_id": user_id}, {"teacher_id": user_id}]})
    await db.notifications.delete_many({"user_id": user_id})
    
    logger.info(f"User deleted by admin: {user['email']}")
    return {"message": f"{user['role'].capitalize()} deleted successfully"}

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
    await create_notification(
        user_id=user_id,
        notification_type="password_reset",
        data={"message": "Votre mot de passe a été réinitialisé par l'administrateur. Veuillez vérifier votre email."}
    )
    
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
    await create_notification(message_data.to_user_id, 'new_message', {
        "from_name": f"{sender['first_name']} {sender['last_name']}",
        "message": f"Nouveau message de {sender['first_name']} {sender['last_name']}"
    })
    
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
async def kalamatheque_ai_assistant(data: dict, current_user: dict = Depends(get_current_user)):
    """AI Assistant for Kalamathèque - summarize, explain, or give examples"""
    action = data.get('action')  # 'summarize', 'explain', 'examples'
    selected_text = data.get('text')
    
    if not selected_text:
        raise HTTPException(status_code=400, detail="Texte requis")
    
    try:
        from emergentintegrations import OpenAI
        client_openai = OpenAI(api_key=os.environ.get('EMERGENT_LLM_KEY'))
        
        prompts = {
            'summarize': f"Résumez ce texte en français de manière concise :\n\n{selected_text}",
            'explain': f"Expliquez ce texte en français de manière claire et pédagogique :\n\n{selected_text}",
            'examples': f"Donnez 3 exemples concrets en français pour illustrer ce texte :\n\n{selected_text}"
        }
        
        prompt = prompts.get(action, prompts['explain'])
        
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant pédagogique qui aide les étudiants à comprendre les textes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        result = response.choices[0].message.content
        
        logger.info(f"AI Assistant used by {current_user['id']} - action: {action}")
        return {"result": result}
        
    except Exception as e:
        logger.error(f"AI Assistant error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur de l'assistant IA")

@api_router.post("/kalamatheque/text-to-speech")
async def text_to_speech(data: dict, current_user: dict = Depends(get_current_user)):
    """Generate speech from text using OpenAI TTS"""
    text = data.get('text')
    
    if not text:
        raise HTTPException(status_code=400, detail="Texte requis")
    
    try:
        from emergentintegrations import OpenAI
        client_openai = OpenAI(api_key=os.environ.get('EMERGENT_LLM_KEY'))
        
        response = client_openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Save audio file temporarily
        audio_filename = f"audio_{uuid.uuid4()}.mp3"
        audio_path = f"/tmp/{audio_filename}"
        response.stream_to_file(audio_path)
        
        # In production, upload to S3 or CDN
        # For now, return a base64 encoded audio
        import base64
        with open(audio_path, 'rb') as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        
        os.remove(audio_path)
        
        logger.info(f"TTS used by {current_user['id']}")
        return {"audio_base64": audio_data}
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur de synthèse vocale")

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
