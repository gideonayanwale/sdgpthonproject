"""
SDG NGO Platform - Enhanced Pure Python Version (With Persistence, Crowdfunding, Resources, Better AI)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import uuid
from dataclasses import dataclass, asdict, field
import hashlib
import os
import numpy as np

 ==================== DATA MODELS ====================

@dataclass
class User:
    """User model"""
    id: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    role: str = 'member'  # founder, admin, member
    ngo_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data.pop('password_hash', None)
        return data

@dataclass
class NGO:
    """NGO/Organization model"""
    id: str
    name: str
    email: str
    country: str
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    is_verified: bool = False
    sdg_targets: Optional[str] = None
    focus_areas: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self, users: Dict[str, User] = None):  # Pass users to calculate member_count
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if users:
            data['member_count'] = sum(1 for u in users.values() if u.ngo_id == self.id)
        else:
            data['member_count'] = 0
        return data

@dataclass
class Project:
    """SDG-aligned project"""
    id: str
    ngo_id: str
    created_by_id: str
    title: str
    description: str
    sdg_targets: str  # comma-separated: "3,4,5"
    status: str = 'active'
    focus_areas: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    beneficiaries: Optional[int] = None
    budget: Optional[float] = None
    funding_goal: float = 0.0  # New: For crowdfunding
    current_funding: float = 0.0  # New
    is_public: bool = False
    collaborators: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.start_date:
            data['start_date'] = self.start_date.isoformat()
        if self.end_date:
            data['end_date'] = self.end_date.isoformat()
        return data

@dataclass
class Funding:  # New: For crowdfunding
    """Funding/donation record"""
    id: str
    project_id: str
    donor_id: str
    amount: float
    message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class Resource:  # New: For resource sharing
    """Shared resource (e.g., file, skill, tech)"""
    id: str
    workspace_id: str
    uploaded_by_id: str
    name: str
    description: str
    resource_type: str = 'file'  # file, skill, tech
    content: str = ''
    is_shared_publicly: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data



@dataclass
class AIInsight:
    """AI-generated insights (enhanced with numpy)"""
    id: str
    project_id: str
    analysis_type: str
    title: str
    insight: str
    confidence_score: float
    recommendations: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

==================== IN-MEMORY DATA STORE WITH PERSISTENCE ====================

class DataStore:
    """In-memory data storage with JSON persistence"""
    
    def __init__(self, file_path='datastore.json'):
        self.file_path = file_path
        self.users: Dict[str, User] = {}
        self.ngos: Dict[str, NGO] = {}
        self.projects: Dict[str, Project] = {}
        self.workspaces: Dict[str, Workspace] = {}
        self.updates: Dict[str, ProjectUpdate] = {}
        self.comments: Dict[str, Comment] = {}
        self.discussions: Dict[str, Discussion] = {}
        self.discussion_threads: Dict[str, DiscussionThread] = {}
        self.indicators: Dict[str, ProjectIndicator] = {}
        self.metrics: Dict[str, ProgressMetric] = {}
        self.insights: Dict[str, AIInsight] = {}
        self.notifications: Dict[str, Notification] = {}
        self.fundings: Dict[str, Funding] = {}  # New
        self.resources: Dict[str, Resource] = {}  # New
        
        self._load_data()  # Load from JSON if exists
        if not self.users:  # Seed if empty
            self._seed_demo_data()
            self._save_data()

    def _load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            # Deserialize (simplified; in prod use better serialization)
            self.users = {k: User(**v) for k, v in data.get('users', {}).items()}
            self.ngos = {k: NGO(**v) for k, v in data.get('ngos', {}).items()}
            self.projects = {k: Project(**v) for k, v in data.get('projects', {}).items()}
            # ... (similar for others; omit for brevity, but implement all)

    def _save_data(self):
        data = {
            'users': {k: asdict(v) for k, v in self.users.items()},
            'ngos': {k: asdict(v) for k, v in self.ngos.items()},
            'projects': {k: asdict(v) for k, v in self.projects.items()},
            # ... (all stores)
        }
        with open(self.file_path, 'w') as f:
            json.dump(data, f, default=str)  # Handle datetime


# ==================== MAIN API CLASS ====================

class SDGPlatformAPI:
    """Main API for SDG NGO Platform (Enhanced)"""
    
    def __init__(self):
        self.store = DataStore()
        self.current_user: Optional[User] = None
    
    # Auth enhancements
    def _hash_password(self, password: str) -> str:
        salt = uuid.uuid4().hex
        hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        salt, hashed = stored_hash.split(':')
        return hashed == hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    



    def list_ngos(self, country: Optional[str] = None, search: Optional[str] = None, sdg_filter: Optional[str] = None) -> dict:
        ngos = list(self.store.ngos.values())
        if sdg_filter:
            ngos = [n for n in ngos if n.sdg_targets and sdg_filter in n.sdg_targets]
        return {'ngos': [n.to_dict(self.store.users) for n in ngos], 'status': 200}

 
    def set_funding_goal(self, project_id: str, goal: float) -> dict:
        if not self.current_user:
            return {'error': 'Unauthorized', 'status': 401}
        project = self.store.projects.get(project_id)
        if not project or project.ngo_id != self.current_user.ngo_id:
            return {'error': 'Access denied', 'status': 403}
        project.funding_goal = goal
        self.store._save_data()
        return {'message': 'Funding goal set', 'status': 200}

    def donate_to_project(self, project_id: str, amount: float, message: Optional[str] = None) -> dict:
        if not self.current_user:
            return {'error': 'Unauthorized', 'status': 401}
        project = self.store.projects.get(project_id)
        if not project:
            return {'error': 'Project not found', 'status': 404}
        funding = Funding(
            id=str(uuid.uuid4()),
            project_id=project_id,
            donor_id=self.current_user.id,
            amount=amount,
            message=message
        )
        self.store.fundings[funding.id] = funding
        project.current_funding += amount
        # Notify project creator
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=project.created_by_id,
            title='New Donation',
            message=f'{self.current_user.first_name} donated {amount} to {project.title}',
            notification_type='funding'
        )
        self.store.notifications[notif.id] = notif
        self.store._save_data()
        return {'message': 'Donation successful', 'funding': funding.to_dict(), 'status': 201}

    # Resource sharing (new)
    def add_resource(self, workspace_id: str, name: str, description: str, resource_type: str, content: str) -> dict:
        if not self.current_user:
            return {'error': 'Unauthorized', 'status': 401}
        workspace = self.store.workspaces.get(workspace_id)
        if not workspace or self.current_user.id not in workspace.members:
            return {'error': 'Access denied', 'status': 403}
        resource = Resource(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            uploaded_by_id=self.current_user.id,
            name=name,
            description=description,
            resource_type=resource_type,
            content=content  # In prod: file path/upload
        )
        self.store.resources[resource.id] = resource
        self.store._save_data()
        return {'message': 'Resource added', 'resource': resource.to_dict(), 'status': 201}

    def generate_ai_insights(self, project_id: str) -> None:
        metrics = [m for m in self.store.metrics.values() if m.project_id == project_id]
        if len(metrics) < 2:
            return
        # Simple linear regression on dates/values
        dates = np.array([(m.recorded_date - datetime.min).days for m in metrics])
        values = np.array([m.metric_value for m in metrics])
        slope, intercept = np.polyfit(dates, values, 1)
        prediction = slope * 30 + values[-1]  
        insight_text = f'Trend slope: {slope:.2f}. Predicted next value: {prediction:.2f}.'
        ai_insight = AIInsight(
            id=str(uuid.uuid4()),
            project_id=project_id,
            analysis_type='prediction',
            title='Metric Trend Analysis',
            insight=insight_text,
            confidence_score=90.0,
            recommendations='Adjust based on trend.'
        )
        self.store.insights[ai_insight.id] = ai_insight
        self.store._save_data()

