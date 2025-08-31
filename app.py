from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from decimal import Decimal
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from functools import wraps
from flask import g
import requests
import json
import re
from typing import Dict, List, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', uuid.uuid4().hex)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///family_finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Sessions last 7 days
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Hugging Face API Configuration
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', 'hf_demo_key')  # Replace with your actual API key

# Financial Advisor AI Configuration
FINANCIAL_ADVISOR_PROMPT = """You are a professional financial advisor AI assistant. Your role is to help users with:
1. Budget planning and management
2. Investment advice and portfolio analysis
3. Debt management strategies
4. Savings goal planning
5. Financial education and literacy
6. Expense tracking and categorization
7. Retirement planning
8. Tax optimization strategies

Always provide helpful, accurate, and safe financial advice. If you're unsure about specific financial details, recommend consulting with a licensed financial professional. Be encouraging and supportive while maintaining professional boundaries.

Current conversation context: {context}

User message: {message}

Please provide a helpful financial advisory response:"""

db = SQLAlchemy(app)
CORS(app)

# Enhanced Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    profile_picture = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_admin': self.is_admin,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'profile_picture': self.profile_picture,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    # Enhanced Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy=True, cascade='all, delete-orphan')
    preferences = db.relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    investments = db.relationship('Investment', backref='user', lazy=True, cascade='all, delete-orphan')
    debts = db.relationship('Debt', backref='user', lazy=True, cascade='all, delete-orphan')
    recurring_transactions = db.relationship('RecurringTransaction', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    weekly_summary = db.Column(db.Boolean, default=True)
    budget_alerts = db.Column(db.Boolean, default=True)
    savings_updates = db.Column(db.Boolean, default=False)
    investment_alerts = db.Column(db.Boolean, default=True)
    debt_reminders = db.Column(db.Boolean, default=True)
    market_updates = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    currency = db.Column(db.String(3), default='USD')
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    theme = db.Column(db.String(20), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'weekly_summary': self.weekly_summary,
            'budget_alerts': self.budget_alerts,
            'savings_updates': self.savings_updates,
            'investment_alerts': self.investment_alerts,
            'debt_reminders': self.debt_reminders,
            'market_updates': self.market_updates,
            'email_notifications': self.email_notifications,
            'sms_notifications': self.sms_notifications,
            'push_notifications': self.push_notifications,
            'currency': self.currency,
            'timezone': self.timezone,
            'language': self.language,
            'theme': self.theme,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income', 'expense', 'transfer', 'investment', 'debt_payment'
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))
    description = db.Column(db.String(500))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)
    location = db.Column(db.String(200))
    payment_method = db.Column(db.String(50))  # 'cash', 'credit_card', 'debit_card', 'bank_transfer', 'mobile_payment'
    reference_number = db.Column(db.String(100))
    receipt_image = db.Column(db.String(255))
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_id = db.Column(db.Integer, db.ForeignKey('recurring_transaction.id'))
    tags = db.Column(db.String(500))  # JSON string of tags
    notes = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'amount': float(self.amount),
            'category': self.category,
            'subcategory': self.subcategory,
            'description': self.description,
            'date': self.date.isoformat(),
            'time': self.time.isoformat() if self.time else None,
            'location': self.location,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'receipt_image': self.receipt_image,
            'is_recurring': self.is_recurring,
            'recurring_id': self.recurring_id,
            'tags': self.tags,
            'notes': self.notes,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    limit_amount = db.Column(db.Numeric(10, 2), nullable=False)
    period = db.Column(db.String(20), default='monthly')  # 'monthly', 'weekly', 'yearly'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # Calculate spent amount for current period
        spent = self.get_spent_amount()
        return {
            'id': self.id,
            'category': self.category,
            'limit': float(self.limit_amount),
            'spent': spent,
            'period': self.period,
            'percentage': (spent / float(self.limit_amount)) * 100 if self.limit_amount > 0 else 0
        }
    
    def get_spent_amount(self):
        # Get current period start date
        now = datetime.now()
        if self.period == 'monthly':
            start_date = now.replace(day=1).date()
        elif self.period == 'weekly':
            start_date = (now - timedelta(days=now.weekday())).date()
        else:  # yearly
            start_date = now.replace(month=1, day=1).date()
        
        total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.category == self.category,
            Transaction.type == 'expense',
            Transaction.date >= start_date
        ).scalar()
        
        return float(total) if total else 0.0

class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    current_amount = db.Column(db.Numeric(10, 2), default=0)
    target_date = db.Column(db.Date)
    priority = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7))  # Hex color code
    is_active = db.Column(db.Boolean, default=True)
    auto_save = db.Column(db.Boolean, default=False)
    auto_save_amount = db.Column(db.Numeric(10, 2))
    auto_save_frequency = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    last_auto_save = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'target': float(self.target_amount),
            'current': float(self.current_amount),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'priority': self.priority,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active,
            'auto_save': self.auto_save,
            'auto_save_amount': float(self.auto_save_amount) if self.auto_save_amount else None,
            'auto_save_frequency': self.auto_save_frequency,
            'last_auto_save': self.last_auto_save.isoformat() if self.last_auto_save else None,
            'percentage': (float(self.current_amount) / float(self.target_amount)) * 100 if self.target_amount > 0 else 0,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# New Enhanced Models
class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'stocks', 'bonds', 'mutual_funds', 'real_estate', 'crypto', 'other'
    amount_invested = db.Column(db.Numeric(10, 2), nullable=False)
    current_value = db.Column(db.Numeric(10, 2))
    purchase_date = db.Column(db.Date, nullable=False)
    sell_date = db.Column(db.Date)
    broker = db.Column(db.String(100))
    account_number = db.Column(db.String(100))
    risk_level = db.Column(db.String(20))  # 'low', 'medium', 'high'
    expected_return = db.Column(db.Numeric(5, 2))  # Percentage
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'amount_invested': float(self.amount_invested),
            'current_value': float(self.current_value) if self.current_value else None,
            'purchase_date': self.purchase_date.isoformat(),
            'sell_date': self.sell_date.isoformat() if self.sell_date else None,
            'broker': self.broker,
            'account_number': self.account_number,
            'risk_level': self.risk_level,
            'expected_return': float(self.expected_return) if self.expected_return else None,
            'notes': self.notes,
            'is_active': self.is_active,
            'profit_loss': float(self.current_value - self.amount_invested) if self.current_value else None,
            'profit_loss_percentage': (float(self.current_value - self.amount_invested) / float(self.amount_invested) * 100) if self.current_value and self.amount_invested else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'credit_card', 'loan', 'mortgage', 'student_loan', 'other'
    original_amount = db.Column(db.Numeric(10, 2), nullable=False)
    current_balance = db.Column(db.Numeric(10, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2))  # Percentage
    minimum_payment = db.Column(db.Numeric(10, 2))
    due_date = db.Column(db.Date)
    lender = db.Column(db.String(100))
    account_number = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'original_amount': float(self.original_amount),
            'current_balance': float(self.current_balance),
            'interest_rate': float(self.interest_rate) if self.interest_rate else None,
            'minimum_payment': float(self.minimum_payment) if self.minimum_payment else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'lender': self.lender,
            'account_number': self.account_number,
            'is_active': self.is_active,
            'notes': self.notes,
            'amount_paid': float(self.original_amount - self.current_balance),
            'percentage_paid': (float(self.original_amount - self.current_balance) / float(self.original_amount) * 100),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class RecurringTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income', 'expense'
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))
    description = db.Column(db.String(500))
    frequency = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    next_due_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'amount': float(self.amount),
            'category': self.category,
            'subcategory': self.subcategory,
            'description': self.description,
            'frequency': self.frequency,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'next_due_date': self.next_due_date.isoformat(),
            'is_active': self.is_active,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'budget_alert', 'savings_goal', 'bill_reminder', 'investment_update', 'general'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    scheduled_for = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'priority': self.priority,
            'is_read': self.is_read,
            'is_sent': self.is_sent,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat()
        }

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='user')  # 'user', 'assistant'
    category = db.Column(db.String(50))  # 'financial_advice', 'budget_help', 'investment_guidance', 'general'
    sentiment = db.Column(db.String(20))  # 'positive', 'negative', 'neutral'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'category': self.category,
            'sentiment': self.sentiment,
            'created_at': self.created_at.isoformat()
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income', 'expense'
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7))  # Hex color code
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'icon': self.icon,
            'color': self.color,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50))
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    biller = db.Column(db.String(100))
    account_number = db.Column(db.String(100))
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # 'monthly', 'quarterly', 'yearly'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'amount': float(self.amount),
            'due_date': self.due_date.isoformat(),
            'category': self.category,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'payment_method': self.payment_method,
            'biller': self.biller,
            'account_number': self.account_number,
            'is_recurring': self.is_recurring,
            'recurring_frequency': self.recurring_frequency,
            'notes': self.notes,
            'days_until_due': (self.due_date - datetime.now().date()).days if self.due_date else None,
            'is_overdue': self.due_date < datetime.now().date() if self.due_date else False,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# AI Chatbot Functions
def get_financial_context(user_id: int) -> str:
    """Get financial context for the user to provide better AI responses"""
    try:
        # Get recent transactions
        recent_transactions = Transaction.query.filter_by(user_id=user_id)\
            .order_by(Transaction.date.desc()).limit(5).all()
        
        # Get current budgets
        budgets = Budget.query.filter_by(user_id=user_id).all()
        
        # Get savings goals
        savings_goals = SavingsGoal.query.filter_by(user_id=user_id).all()
        
        # Get current balance
        income_total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income'
        ).scalar() or 0
        
        expense_total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense'
        ).scalar() or 0
        
        balance = float(income_total - expense_total)
        
        context = f"""
        User Financial Summary:
        - Current Balance: ${balance:,.2f}
        - Recent Transactions: {len(recent_transactions)} transactions
        - Active Budgets: {len(budgets)} budgets
        - Savings Goals: {len(savings_goals)} active goals
        """
        
        if recent_transactions:
            context += "\nRecent Transaction Categories: " + ", ".join([t.category for t in recent_transactions[:3]])
        
        if budgets:
            context += f"\nBudget Categories: {', '.join([b.category for b in budgets[:3]])}"
        
        return context.strip()
        
    except Exception as e:
        return f"Error getting financial context: {str(e)}"

def call_huggingface_api(message: str, context: str = "") -> str:
    """Call Hugging Face API for AI response"""
    try:
        # Prepare the prompt with financial context
        prompt = FINANCIAL_ADVISOR_PROMPT.format(context=context, message=message)
        
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 500,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9
            }
        }
        
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'I apologize, but I could not generate a response at this time.')
            elif isinstance(result, dict):
                return result.get('generated_text', 'I apologize, but I could not generate a response at this time.')
            else:
                return 'I apologize, but I could not generate a response at this time.'
        else:
            # Fallback response if API fails
            return generate_fallback_response(message)
            
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        return generate_fallback_response(message)

def generate_fallback_response(message: str) -> str:
    """Generate a fallback response when AI API is unavailable"""
    message_lower = message.lower()
    
    # Simple keyword-based responses
    if any(word in message_lower for word in ['budget', 'spending', 'expense']):
        return "I'd be happy to help you with budgeting! To get started, try tracking your expenses for a month to see where your money goes. You can then set realistic spending limits for different categories."
    
    elif any(word in message_lower for word in ['save', 'savings', 'goal']):
        return "Great question about savings! Start by setting a specific goal with a target amount and date. Then break it down into smaller, manageable monthly or weekly amounts. Even small regular contributions add up over time!"
    
    elif any(word in message_lower for word in ['invest', 'investment', 'portfolio']):
        return "Investment advice should be personalized to your goals and risk tolerance. Consider starting with diversified index funds and gradually learning about different investment options. Remember, it's important to do thorough research or consult with a financial advisor."
    
    elif any(word in message_lower for word in ['debt', 'loan', 'credit']):
        return "Managing debt effectively is crucial for financial health. Focus on high-interest debt first, consider debt consolidation if it makes sense, and always pay at least the minimum payment on time. Creating a debt payoff plan can help you stay motivated."
    
    elif any(word in message_lower for word in ['income', 'salary', 'earn']):
        return "Increasing your income can significantly impact your financial goals. Consider asking for a raise, developing new skills, taking on side projects, or exploring passive income opportunities. Remember to invest in yourself!"
    
    else:
        return "I'm here to help with your financial questions! Feel free to ask about budgeting, saving, investing, debt management, or any other financial topics. I'll do my best to provide helpful guidance."

def analyze_sentiment(message: str) -> str:
    """Analyze the sentiment of a user message"""
    message_lower = message.lower()
    
    positive_words = ['good', 'great', 'excellent', 'happy', 'excited', 'positive', 'improve', 'better', 'success', 'achieve']
    negative_words = ['bad', 'terrible', 'worried', 'stressed', 'anxious', 'problem', 'issue', 'difficult', 'struggle', 'fail']
    
    positive_count = sum(1 for word in positive_words if word in message_lower)
    negative_count = sum(1 for word in negative_words if word in message_lower)
    
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'

def categorize_message(message: str) -> str:
    """Categorize the type of financial question"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['budget', 'spending', 'expense', 'cost']):
        return 'budget_help'
    elif any(word in message_lower for word in ['save', 'savings', 'goal', 'target']):
        return 'savings_guidance'
    elif any(word in message_lower for word in ['invest', 'investment', 'portfolio', 'stock', 'bond']):
        return 'investment_advice'
    elif any(word in message_lower for word in ['debt', 'loan', 'credit', 'payment']):
        return 'debt_management'
    elif any(word in message_lower for word in ['income', 'salary', 'earn', 'money']):
        return 'income_optimization'
    elif any(word in message_lower for word in ['retirement', 'future', 'planning']):
        return 'retirement_planning'
    elif any(word in message_lower for word in ['tax', 'taxes', 'deduction']):
        return 'tax_optimization'
    else:
        return 'general_financial_advice'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Return JSON for API requests; redirect to login for page requests
            wants_json = request.path.startswith('/api') or \
                (request.accept_mimetypes and request.accept_mimetypes.best == 'application/json')
            if wants_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            g.user = user
        else:
            session.pop('user_id', None)
            g.user = None
    else:
        g.user = None

@app.context_processor
def inject_user():
    return dict(current_user=g.user)

# Routes
@app.route('/')
def index():
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    theme = 'dark'
    return render_template('landing.html', theme=theme)

@app.route('/test')
def test():
    return jsonify({'message': 'Backend is working!', 'timestamp': datetime.now().isoformat()})

@app.route('/dashboard')
@login_required
def dashboard():
    theme = 'dark'
    return render_template('dashboard.html', theme=theme)

@app.route('/reports')
@login_required
def reports():
    theme = 'dark'
    return render_template('reports.html', theme=theme)

@app.route('/transactions')
@login_required
def transactions():
    theme = 'dark'
    return render_template('transactions.html', theme=theme)

@app.route('/budgets')
@login_required
def budgets():
    theme = 'dark'
    return render_template('budgets.html', theme=theme)



@app.route('/savings', methods=['GET'])
@login_required
def savings():
    theme = 'dark'
    return render_template('savings.html', theme=theme)

@app.route('/family_members')
@login_required
def family_members():
    theme = 'dark'
    return render_template('family_members.html', theme=theme)

@app.route('/api/family_members')
@login_required
def api_family_members():
    user_id = session['user_id']
    # For now, return all users as family members
    # In a real application, you'd have a more complex relationship model
    members = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email} for u in members])

@app.route('/settings')
@login_required
def settings():
    theme = 'dark'
    return render_template('settings.html', theme=theme)

@app.route('/profile')
@login_required
def profile():
    theme = 'dark'
    return render_template('profile.html', theme=theme)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
            
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Set session
                session['user_id'] = user.id
                session.permanent = True  # Make session persistent
                
                print(f"User {user.email} logged in successfully. Session: {session}")
                
                return jsonify({
                    'success': True, 
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email
                    }
                })
            else:
                print(f"Login failed for email: {email}")
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred during login'}), 500
    
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    theme = 'dark'
    return render_template('login.html', theme=theme)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
            
            email = data.get('email')
            name = data.get('name')
            password = data.get('password')
            suppress_login = data.get('suppress_login', False)
            
            if not email or not name or not password:
                return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
            if len(password) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            
            # Create new user
            user = User(email=email, name=name)
            user.set_password(password)
            
            try:
                db.session.add(user)
                db.session.commit()
                
                # Create user preferences
                user_preference = UserPreference(user_id=user.id)
                db.session.add(user_preference)
                db.session.commit()
                
                # Log in the user unless suppressed (e.g., admin adding a family member)
                if not suppress_login:
                    session['user_id'] = user.id
                    session.permanent = True
                
                print(f"User {email} registered successfully. Session: {session}")
                
                return jsonify({
                    'success': True, 
                    'message': 'Account created successfully',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email
                    },
                    'logged_in': not suppress_login
                }), 201
                
            except Exception as e:
                db.session.rollback()
                print(f"Signup error: {str(e)}")
                return jsonify({'success': False, 'message': 'An error occurred during registration'}), 500
                
        except Exception as e:
            print(f"Signup error: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred during registration'}), 500
    
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    theme = 'dark'
    return render_template('signup.html', theme=theme)

@app.route('/api/auth/check')
def check_auth():
    try:
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email
                    }
                })
        
        return jsonify({'authenticated': False}), 401
        
    except Exception as e:
        print(f"Auth check error: {str(e)}")
        return jsonify({'authenticated': False, 'error': 'Authentication check failed'}), 500

@app.route('/api/auth/user')
@login_required
def get_current_user():
    try:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        print(f"Get user error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to get user data'}), 500

@app.route('/logout')
def logout():
    try:
        # Clear all session data
        session.clear()
        print("User logged out successfully")
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return redirect(url_for('index'))

@app.route('/api/dashboard')
@login_required
def get_dashboard_data():
    user_id = session['user_id']
    
    try:
        # Calculate current month totals
        now = datetime.now()
        start_of_month = now.replace(day=1).date()
        
        # Total balance (simplified calculation)
        income_total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income'
        ).scalar() or 0
        
        expense_total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense'
        ).scalar() or 0
        
        # Monthly income
        monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income',
            Transaction.date >= start_of_month
        ).scalar() or 0
        
        # Monthly expenses
        monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense',
            Transaction.date >= start_of_month
        ).scalar() or 0
        
        # Savings goals total
        savings_total = db.session.query(db.func.sum(SavingsGoal.current_amount)).filter(
            SavingsGoal.user_id == user_id
        ).scalar() or 0
        
        return jsonify({
            'totalBalance': float(income_total - expense_total),
            'monthlyIncome': float(monthly_income),
            'monthlyExpenses': float(monthly_expenses),
            'savingsGoal': float(savings_total)
        })
    except Exception as e:
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@app.route('/api/dashboard/total-balance', methods=['POST'])
@login_required
def set_total_balance():
    """Adjust total balance by creating an automatic adjustment transaction"""
    user_id = session['user_id']
    data = request.json or {}
    try:
        desired = Decimal(str(data.get('total_balance', '0')))
        income_total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income'
        ).scalar() or 0
        expense_total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense'
        ).scalar() or 0
        current = Decimal(str(income_total)) - Decimal(str(expense_total))
        delta = desired - current
        if abs(delta) < Decimal('0.005'):
            return jsonify({'success': True, 'message': 'No change needed', 'totalBalance': float(current)})
        adj_type = 'income' if delta > 0 else 'expense'
        adj_amount = abs(delta)
        adjustment = Transaction(
            user_id=user_id,
            type=adj_type,
            amount=adj_amount,
            category='adjustment',
            description='Balance adjustment',
            date=datetime.now().date()
        )
        db.session.add(adjustment)
        db.session.commit()
        new_balance = float(desired)
        return jsonify({'success': True, 'message': 'Balance updated', 'totalBalance': new_balance})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update balance'}), 400

@app.route('/api/notifications')
@login_required
def api_notifications():
    user_id = session['user_id']
    notes = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()
    payload = []
    for n in notes:
        payload.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'priority': n.priority,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        })
    return jsonify(payload)

@app.route('/api/transactions', methods=['GET', 'POST'])
@login_required
def api_transactions():
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.json
        
        try:
            transaction = Transaction(
                user_id=user_id,
                type=data['type'],
                amount=Decimal(str(data['amount'])),
                category=data['category'],
                description=data.get('description', ''),
                date=datetime.strptime(data['date'], '%Y-%m-%d').date()
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Transaction added successfully',
                'transaction': transaction.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    else:
        # GET - Return recent transactions
        transactions = Transaction.query.filter_by(user_id=user_id)\
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())\
            .limit(20).all()
        
        return jsonify([t.to_dict() for t in transactions])

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT', 'DELETE'])
@login_required
def transaction_detail(transaction_id):
    user_id = session['user_id']
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first_or_404()
    
    if request.method == 'PUT':
        data = request.json
        try:
            transaction.type = data.get('type', transaction.type)
            transaction.amount = Decimal(str(data.get('amount', transaction.amount)))
            transaction.category = data.get('category', transaction.category)
            transaction.description = data.get('description', transaction.description)
            if 'date' in data:
                transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            db.session.commit()
            return jsonify({'success': True, 'transaction': transaction.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(transaction)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Transaction deleted'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/budgets', methods=['GET', 'POST'])
@login_required
def api_budgets():
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.json
        
        try:
            budget = Budget(
                user_id=user_id,
                category=data['category'],
                limit_amount=Decimal(str(data['limit_amount'])),
                period=data.get('period', 'monthly')
            )
            
            db.session.add(budget)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Budget created successfully',
                'budget': budget.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    else:
        budgets = Budget.query.filter_by(user_id=user_id).all()
        return jsonify([b.to_dict() for b in budgets])

@app.route('/api/budgets/<int:budget_id>', methods=['PUT', 'DELETE'])
@login_required
def budget_detail(budget_id):
    user_id = session['user_id']
    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first_or_404()
    
    if request.method == 'PUT':
        data = request.json
        try:
            budget.category = data.get('category', budget.category)
            budget.limit_amount = Decimal(str(data.get('limit_amount', budget.limit_amount)))
            budget.period = data.get('period', budget.period)
            
            db.session.commit()
            return jsonify({'success': True, 'budget': budget.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(budget)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Budget deleted'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/savings-goals', methods=['GET', 'POST'])
@login_required
def savings_goals():
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.json
        
        try:
            goal = SavingsGoal(
                user_id=user_id,
                name=data['name'],
                target_amount=Decimal(str(data['target_amount'])),
                current_amount=Decimal(str(data.get('current_amount', 0))),
                target_date=datetime.strptime(data['target_date'], '%Y-%m-%d').date() if data.get('target_date') else None,
                priority=data.get('priority', 0)
            )
            
            db.session.add(goal)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Savings goal created successfully',
                'goal': goal.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    else:
        goals = SavingsGoal.query.filter_by(user_id=user_id).order_by(SavingsGoal.priority).all()
        return jsonify([g.to_dict() for g in goals])

@app.route('/api/savings-goals/<int:goal_id>', methods=['PUT', 'DELETE'])
@login_required
def savings_goal_detail(goal_id):
    user_id = session['user_id']
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    
    if request.method == 'PUT':
        data = request.json
        try:
            goal.name = data.get('name', goal.name)
            goal.target_amount = Decimal(str(data.get('target_amount', goal.target_amount)))
            goal.current_amount = Decimal(str(data.get('current_amount', goal.current_amount)))
            goal.priority = data.get('priority', goal.priority)
            if 'target_date' in data:
                goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date() if data['target_date'] else None
            
            db.session.commit()
            return jsonify({'success': True, 'goal': goal.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(goal)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Savings goal deleted'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/savings-goals/reorder', methods=['PUT'])
@login_required
def savings_goals_reorder():
    user_id = session['user_id']
    data = request.json
    goal_ids = data.get('goal_ids', [])

    try:
        for index, goal_id in enumerate(goal_ids):
            goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first()
            if goal:
                goal.priority = index
        db.session.commit()
        return jsonify({'success': True, 'message': 'Priorities updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/analytics/spending-by-category')
@login_required
def spending_by_category():
    user_id = session['user_id']
    
    # Get current month spending by category
    now = datetime.now()
    start_of_month = now.replace(day=1).date()
    
    results = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date >= start_of_month
    ).group_by(Transaction.category).all()
    
    categories = []
    amounts = []
    for category, total in results:
        categories.append(category.title())
        amounts.append(float(total))
    
    return jsonify({
        'categories': categories,
        'amounts': amounts
    })

@app.route('/api/analytics/monthly-trends')
@login_required
def monthly_trends():
    user_id = session['user_id']
    
    # Get last 6 months of income/expense data
    months = []
    income_data = []
    expense_data = []
    
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30 * i)
        start_date = date.replace(day=1).date()
        
        if i == 0:
            end_date = datetime.now().date()
        else:
            next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
            end_date = next_month - timedelta(days=1)
        
        # Income for this month
        income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        # Expenses for this month
        expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        
        months.append(start_date.strftime('%B'))
        income_data.append(float(income))
        expense_data.append(float(expenses))
    
    return jsonify({
        'months': months,
        'income': income_data,
        'expenses': expense_data
    })

@app.route('/api/settings/profile', methods=['GET', 'PUT'])
@login_required
def api_settings_profile():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'PUT':
        data = request.json
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})

    return jsonify({
        'name': user.name,
        'email': user.email
    })

@app.route('/api/settings/password', methods=['PUT'])
@login_required
def api_settings_password():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    data = request.json

    if not check_password_hash(user.password_hash, data.get('current_password')):
        return jsonify({'success': False, 'message': 'Invalid current password'}), 400

    if data.get('new_password') != data.get('confirm_password'):
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

    user.password_hash = generate_password_hash(data.get('new_password'))
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/api/settings/notifications', methods=['GET', 'PUT'])
@login_required
def api_settings_notifications():
    user_id = session['user_id']
    preferences = UserPreference.query.filter_by(user_id=user_id).first()

    if request.method == 'PUT':
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
        
        data = request.json
        preferences.weekly_summary = data.get('weekly_summary', preferences.weekly_summary)
        preferences.budget_alerts = data.get('budget_alerts', preferences.budget_alerts)
        preferences.savings_updates = data.get('savings_updates', preferences.savings_updates)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notification settings updated'})

    if preferences:
        return jsonify(preferences.to_dict())
    else:
        # Return default values if no preferences are set
        return jsonify({
            'weekly_summary': True,
            'budget_alerts': True,
            'savings_updates': False
        })

@app.route('/api/reports/summary')
@login_required
def reports_summary():
    user_id = session['user_id']
    now = datetime.now()
    
    # This year
    start_of_year = now.replace(month=1, day=1).date()
    
    # This month
    start_of_month = now.replace(day=1).date()
    
    # Last month
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    last_month_end = start_of_month - timedelta(days=1)
    
    # Calculate totals
    yearly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.date >= start_of_year
    ).scalar() or 0
    
    yearly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date >= start_of_year
    ).scalar() or 0
    
    monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.date >= start_of_month
    ).scalar() or 0
    
    monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date >= start_of_month
    ).scalar() or 0
    
    last_month_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.date >= last_month_start,
        Transaction.date <= last_month_end
    ).scalar() or 0
    
    last_month_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date >= last_month_start,
        Transaction.date <= last_month_end
    ).scalar() or 0
    
    return jsonify({
        'yearly': {
            'income': float(yearly_income),
            'expenses': float(yearly_expenses),
            'savings': float(yearly_income - yearly_expenses)
        },
        'monthly': {
            'income': float(monthly_income),
            'expenses': float(monthly_expenses),
            'savings': float(monthly_income - monthly_expenses)
        },
        'lastMonth': {
            'income': float(last_month_income),
            'expenses': float(last_month_expenses),
            'savings': float(last_month_income - last_month_expenses)
        }
    })

@app.route('/api/reports/data')
@login_required
def get_report_data():
    user_id = session['user_id']
    period = request.args.get('period', 'this_month')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Determine date range based on period
    now = datetime.now()
    if period == 'this_month':
        start_date = now.replace(day=1).date()
        end_date = now.date()
    elif period == 'last_month':
        end_date = now.replace(day=1).date() - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period == 'this_year':
        start_date = now.replace(month=1, day=1).date()
        end_date = now.date()
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        # Default to this month if period is invalid
        start_date = now.replace(day=1).date()
        end_date = now.date()

    # --- Summary Calculations ---
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).scalar() or 0

    total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).scalar() or 0

    total_savings = total_income - total_expenses

    # --- Chart Data ---
    # Income vs Expenses Trend (monthly for the year)
    income_expenses_chart = {'labels': [], 'income': [], 'expenses': []}
    for i in range(11, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        
        # Correctly calculate the end of the month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

        monthly_income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income',
            Transaction.date >= month_start.date(),
            Transaction.date <= month_end.date()
        ).scalar() or 0

        monthly_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'expense',
            Transaction.date >= month_start.date(),
            Transaction.date <= month_end.date()
        ).scalar() or 0
        
        income_expenses_chart['labels'].append(month_start.strftime('%b'))
        income_expenses_chart['income'].append(float(monthly_income))
        income_expenses_chart['expenses'].append(float(monthly_expenses))

    # Spending by Category
    category_chart = {'labels': [], 'data': []}
    category_spending = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).group_by(Transaction.category).all()

    for category, amount in category_spending:
        category_chart['labels'].append(category.title())
        category_chart['data'].append(float(amount))

    data = {
        'summary': {
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'total_savings': float(total_savings),
        },
        'charts': {
            'income_expenses': income_expenses_chart,
            'categories': category_chart,
        }
    }
    return jsonify(data)

# AI Chatbot API Endpoints
@app.route('/api/chat', methods=['POST'])
@login_required
def chat_with_ai():
    """Main chatbot endpoint for AI financial advice"""
    try:
        user_id = session['user_id']
        data = request.json
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get financial context for better AI responses
        financial_context = get_financial_context(user_id)
        
        # Analyze message sentiment and category
        sentiment = analyze_sentiment(message)
        category = categorize_message(message)
        
        # Get AI response from Hugging Face API
        ai_response = call_huggingface_api(message, financial_context)
        
        # Save chat history
        chat_entry = ChatHistory(
            user_id=user_id,
            message=message,
            response=ai_response,
            message_type='user',
            category=category,
            sentiment=sentiment
        )
        
        db.session.add(chat_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'category': category,
            'sentiment': sentiment,
            'context': financial_context
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500

@app.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_history():
    """Get user's chat history"""
    try:
        user_id = session['user_id']
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get paginated chat history
        chat_history = ChatHistory.query.filter_by(user_id=user_id)\
            .order_by(ChatHistory.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'chats': [chat.to_dict() for chat in chat_history.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': chat_history.total,
                'pages': chat_history.pages,
                'has_next': chat_history.has_next,
                'has_prev': chat_history.has_prev
            }
        })
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({'error': 'An error occurred while fetching chat history'}), 500

@app.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat_history():
    """Clear user's chat history"""
    try:
        user_id = session['user_id']
        
        # Delete all chat history for the user
        ChatHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared successfully'
        })
        
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred while clearing chat history'}), 500

@app.route('/api/chat/insights', methods=['GET'])
@login_required
def get_chat_insights():
    """Get insights from user's chat history"""
    try:
        user_id = session['user_id']
        
        # Get chat statistics
        total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
        categories = db.session.query(
            ChatHistory.category,
            db.func.count(ChatHistory.id).label('count')
        ).filter_by(user_id=user_id).group_by(ChatHistory.category).all()
        
        sentiments = db.session.query(
            ChatHistory.sentiment,
            db.func.count(ChatHistory.id).label('count')
        ).filter_by(user_id=user_id).group_by(ChatHistory.sentiment).all()
        
        # Get recent topics
        recent_topics = db.session.query(
            ChatHistory.category,
            db.func.count(ChatHistory.id).label('count')
        ).filter_by(user_id=user_id)\
            .filter(ChatHistory.created_at >= datetime.now() - timedelta(days=30))\
            .group_by(ChatHistory.category)\
            .order_by(db.func.count(ChatHistory.id).desc())\
            .limit(5).all()
        
        return jsonify({
            'success': True,
            'insights': {
                'total_chats': total_chats,
                'categories': [{'category': c.category, 'count': c.count} for c in categories],
                'sentiments': [{'sentiment': s.sentiment, 'count': s.count} for s in sentiments],
                'recent_topics': [{'category': t.category, 'count': t.count} for t in recent_topics]
            }
        })
        
    except Exception as e:
        print(f"Error getting chat insights: {e}")
        return jsonify({'error': 'An error occurred while fetching chat insights'}), 500

@app.route('/api/parse-receipt', methods=['POST'])
@login_required
def parse_receipt():
    if 'receipt' not in request.files:
        return jsonify({'error': 'No receipt file found'}), 400
    
    file = request.files['receipt']
    
    # Placeholder for OCR processing
    # In a real application, you would use an OCR library to parse the receipt
    
    return jsonify({
        'amount': 12.34,
        'category': 'Groceries',
        'description': 'Receipt from ' + file.filename,
        'date': datetime.now().strftime('%Y-%m-%d')
    })


# Initialize database
def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()
        
        # Check if user exists
        if not User.query.first():
            # Create a sample user
            user = User(
                email='admin@familyfinance.com',
                name='Family Admin',
                is_admin=True
            )
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()

            # Create user preferences
            user_preference = UserPreference(user_id=user.id)
            db.session.add(user_preference)
            
            # Add sample data
            sample_transactions = [
                Transaction(user_id=user.id, type='income', amount=5000, category='salary', description='Monthly salary', date=datetime.now().date()),
                Transaction(user_id=user.id, type='expense', amount=1200, category='groceries', description='Weekly groceries', date=datetime.now().date()),
                Transaction(user_id=user.id, type='expense', amount=800, category='utilities', description='Electric and water bills', date=datetime.now().date()),
                Transaction(user_id=user.id, type='expense', amount=300, category='entertainment', description='Family movie night', date=datetime.now().date()),
                Transaction(user_id=user.id, type='expense', amount=150, category='transportation', description='Gas for car', date=datetime.now().date()),
            ]
            
            sample_budgets = [
                Budget(user_id=user.id, category='groceries', limit_amount=1500, period='monthly'),
                Budget(user_id=user.id, category='utilities', limit_amount=1000, period='monthly'),
                Budget(user_id=user.id, category='entertainment', limit_amount=500, period='monthly'),
                Budget(user_id=user.id, category='transportation', limit_amount=400, period='monthly'),
            ]
            
            sample_goals = [
                SavingsGoal(user_id=user.id, name='Emergency Fund', target_amount=10000, current_amount=2500, target_date=datetime(2025, 12, 31).date()),
                SavingsGoal(user_id=user.id, name='Vacation Fund', target_amount=2500, current_amount=1625, target_date=datetime(2025, 8, 15).date()),
                SavingsGoal(user_id=user.id, name='New Car', target_amount=25000, current_amount=5000, target_date=datetime(2026, 6, 30).date()),
            ]
            
            for transaction in sample_transactions:
                db.session.add(transaction)
            
            for budget in sample_budgets:
                db.session.add(budget)
                
            for goal in sample_goals:
                db.session.add(goal)
            
            db.session.commit()
            print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
