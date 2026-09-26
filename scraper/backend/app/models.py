from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    client_name = Column(String)
    client_maps_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    competitors = relationship("Competitor", back_populates="project")

class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    maps_url = Column(String, nullable=False)
    posts_count = Column(Integer, default=0)
    last_scraped_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    is_client = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="competitors")

class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    competitor_id = Column(String, ForeignKey("competitors.id"))
    post_text = Column(Text, nullable=False)
    post_url = Column(String, nullable=True)
    published_date = Column(DateTime, nullable=True)
    image_urls = Column(JSON, default=[])
    cta_text = Column(String, nullable=True)
    content_hash = Column(String, unique=True, nullable=False)
    main_topic = Column(String, nullable=True)
    sub_topic = Column(String, nullable=True)
    keywords = Column(JSON, default=[])
    content_type = Column(String, nullable=True)  # offer, tips, event, announcement
    cta_type = Column(String, nullable=True)  # call, visit, book, buy, learn
    has_promotion = Column(Boolean, default=False)
    ai_analysed = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    competitor_id = Column(String, ForeignKey("competitors.id"))
    status = Column(String, default="queued")  # queued, running, paused, completed, failed
    posts_found = Column(Integer, default=0)
    new_added = Column(Integer, default=0)
    duplicates_skipped = Column(Integer, default=0)
    images_downloaded = Column(Integer, default=0)
    captcha_required = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    topic = Column(String, nullable=False)
    competitor_count = Column(Integer, default=0)
    occurrence_count = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

class GeneratedIdea(Base):
    __tablename__ = "generated_ideas"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    topic_title = Column(String, nullable=False)
    post_copy = Column(Text, nullable=False)
    keywords = Column(JSON, default=[])
    cta_type = Column(String, nullable=True)
    cta_text = Column(String, nullable=True)
    image_concept = Column(Text, nullable=True)
    ai_provider = Column(String, default="gemini")
    generated_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    keyword_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)