"""All Pydantic models for the application."""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    role: str
    level: Optional[str] = None
    is_active: bool = False
    is_restricted: bool = False
    password_hash: str
    temporary_password: Optional[str] = None
    assigned_teacher: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None
    first_login: bool = True
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


class StudentCreateByAdmin(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    phone_country_code: str = "+221"
    level: str = "beginner"
    price: float = 0
    currency: str = "EUR"
    password: Optional[str] = None


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
    file_type: str


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
    status: str
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
    event_date: Optional[datetime] = None
    published_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author_id: str
    author_name: str


class NewsCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    event_date: Optional[str] = None


class WelcomeLetter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_name: str
    user_level: str
    user_role: str
    temp_password: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_read: bool = False


class ClubPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    author_name: str
    author_role: str
    title: str
    content: str
    category: str
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
    code: str
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
    first_name: str
    last_name: str


class GroupRegistration(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    country_code: str = "+33"
    level: str
    additional_members: List[GroupMemberSimple] = []
    preferred_slots: Optional[str] = None
    referral_source: Optional[str] = None


class RegisterWithCode(BaseModel):
    code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    number_of_students: int = 2


class PromoCode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    discount_percent: int
    valid_until: datetime
    max_uses: Optional[int] = None
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
    event_link: str = ""
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClubEventCreate(BaseModel):
    title: str
    description: str
    event_date: str
    duration_minutes: int
    max_participants: int
    event_link: str = ""


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
    sender_role: str
    recipient_ids: List[str]
    read_by: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentCreate(BaseModel):
    title: str
    description: str
    file_url: str
    file_name: str
    file_type: str
    recipient_ids: List[str]


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
    scheduled_date: str


class GroupCourse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    teacher_id: str
    level: str
    max_students: int = 6
    current_students: List[str] = []
    scheduled_days: List[str] = []
    scheduled_time: str = ""
    price_per_person_eur: float = 80.0
    price_per_person_fcfa: float = 50000.0
    discount_4_plus: int = 10
    meet_link: str = ""
    status: str = "open"
    start_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GroupCourseEnrollment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_course_id: str
    student_id: str
    enrolled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_status: str = "pending"
    amount_paid: float = 0.0
    currency: str = "EUR"


class GroupCourseCreate(BaseModel):
    name: str
    description: str = ""
    teacher_id: str
    max_students: int = 10
    price_per_person: float = 80.0
    currency: str = "EUR"
    level: str = "beginner"
    schedule: str = ""
    meet_link: str = ""
    start_date: str = ""
    end_date: str = ""
    total_hours: int = 0


class GroupSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    title: str
    scheduled_date: str
    duration_minutes: int = 90
    meet_link: str = ""
    status: str = "scheduled"
    attendees: List[str] = []
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Badge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: str
    description: str
    condition_type: str
    condition_value: int
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
    challenge_type: str
    target_count: int
    points_reward: int
    week_start: datetime
    week_end: datetime
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudentPoints(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    total_points: int = 0
    available_points: int = 0
    total_discount_earned: float = 0.0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChallengeProgress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    challenge_id: str
    current_count: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None


class PaymentRequest(BaseModel):
    plan_name: str
    plan_level: str
    amount: int
    currency: str = "FCFA"
    promo_code: Optional[str] = None
