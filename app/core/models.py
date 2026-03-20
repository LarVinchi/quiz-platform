from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base, engine

# --- UNIFIED USER MODEL ---
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password = Column(String, nullable=False)
    role = Column(String, default="student") # 'student' or 'instructor'
    is_master = Column(Boolean, default=False)
    
    # ADDED THIS LINE FOR THE PASSWORD RESET FIX:
    needs_password_change = Column(Boolean, default=True) 
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Quiz(Base):
    __tablename__ = 'quizzes'
    
    quiz_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True) 
    
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = 'questions'
    
    question_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.quiz_id'))
    question_text = Column(String, nullable=False)
    question_type = Column(String, default="text") 
    expected_answer = Column(String, nullable=True)
    options = Column(String, nullable=True) 
    
    # Data Capabilities
    dataset_path = Column(String, nullable=True) 
    schema_info = Column(String, nullable=True)  
    points = Column(Integer, default=1)
    
    quiz = relationship("Quiz", back_populates="questions")
    # Updated to map to the renamed 'Answer' class
    student_answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = 'submissions'
    
    submission_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id')) 
    quiz_id = Column(Integer, ForeignKey('quizzes.quiz_id'))
    
    score = Column(Float, default=0.0) 
    total_questions = Column(Integer)
    email_sent = Column(Boolean, default=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Updated to map to the renamed 'Answer' class
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")


# --- RENAMED TO Answer TO FIX THE IMPORT ERROR ---
class Answer(Base):
    __tablename__ = 'answers' 
    
    answer_id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey('submissions.submission_id'))
    question_id = Column(Integer, ForeignKey('questions.question_id'))
    student_answer = Column(String, nullable=True)
    is_correct = Column(Boolean, default=False)
    points_awarded = Column(Float, default=0.0) 
    
    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="student_answers")