from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta
import json
import os
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Fallback AI responses for testing without Ollama
def get_fallback_analysis(transactions):
    """Generate realistic AI analysis without actual AI"""
    if not transactions:
        return "🎯 Ready to start tracking! Add your first expense to get personalized insights."
    
    total = sum(t[0] for t in transactions)
    categories = {}
    for t in transactions:
        categories[t[1]] = categories.get(t[1], 0) + t[0]
    
    top_category = max(categories, key=categories.get) if categories else "Food"
    
    responses = [
        f"📊 You've spent ₹{total:,.0f} across {len(transactions)} transactions. {top_category} is your biggest expense (₹{categories[top_category]:,.0f}). Consider setting a weekly limit for better control.",
        
        f"💡 Smart insight: Your {top_category} spending (₹{categories[top_category]:,.0f}) is trending high. Try the 50-30-20 rule: 50% needs, 30% wants, 20% savings.",
        
        f"🎯 Great progress! Total spending: ₹{total:,.0f}. Pro tip: Review {top_category} expenses weekly - small cuts here can save ₹5,000+ monthly.",
        
        f"⚡ Family finance tip: You're spending ₹{total:,.0f} this period. Set up automatic savings of ₹2,000/week to build a strong emergency fund.",
        
        f"📈 Spending pattern detected: {top_category} dominates at ₹{categories[top_category]:,.0f}. Try meal planning or subscription audits to optimize this category."
    ]
    
    return random.choice(responses)

def get_fallback_chat_response(message, transactions=None):
    """Generate realistic chat responses without AI"""
    message_lower = message.lower()
    
    # Calculate some basic stats if transactions available
    if transactions:
        total_recent = sum(t[0] for t in transactions[-10:])  # Last 10 transactions
        categories = {}
        for t in transactions[-20:]:  # Last 20 for categories
            categories[t[1]] = categories.get(t[1], 0) + t[0]
        top_category = max(categories, key=categories.get) if categories else "Food & Dining"
    else:
        total_recent = 0
        top_category = "Food & Dining"
    
    # Smart responses based on keywords
    if any(word in message_lower for word in ['spend', 'spent', 'spending', 'expense']):
        if transactions:
            return f"💰 Based on your recent transactions, you've spent ₹{total_recent:,.0f}. Your top category is {top_category}. Want specific insights on any category?"
        else:
            return "📊 You haven't added any transactions yet! Start tracking your expenses to get personalized spending insights."
    
    elif any(word in message_lower for word in ['food', 'dining', 'restaurant', 'meal']):
        return f"🍽️ Food spending can be tricky to manage! Try these tips: 1) Set a weekly dining budget 2) Plan meals ahead 3) Use 'one eating out per week' rule. Current food expenses look manageable."
    
    elif any(word in message_lower for word in ['save', 'saving', 'savings', 'money']):
        return f"💡 Smart saving tips for families: 1) Automate ₹5,000/month to savings 2) Use the 24-hour rule for big purchases 3) Track subscription services quarterly. You're on the right track!"
    
    elif any(word in message_lower for word in ['budget', 'budgeting', 'plan']):
        return f"📋 Family budgeting made simple: 50% for needs (rent, groceries), 30% for wants (entertainment), 20% for savings/debt. Your {top_category} spending fits well in this framework!"
    
    elif any(word in message_lower for word in ['goal', 'goals', 'target']):
        return "🎯 Popular family financial goals: 1) Emergency fund (6 months expenses) 2) Kids' education fund 3) Home down payment 4) Vacation fund. Which goal interests you most?"
    
    elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'help']):
        return "👋 Hi there! I'm your family finance assistant. Ask me about budgeting, saving goals, spending patterns, or any money questions. What would you like to know?"
    
    else:
        # Generic helpful response
        responses = [
            f"🤔 That's a great question! With your current spending pattern showing {top_category} as a focus area, I'd suggest reviewing that category monthly for optimization opportunities.",
            
            "💭 Interesting point! Family financial planning works best with clear goals and regular tracking. Have you set up any specific savings targets this year?",
            
            f"📊 Based on general family finance principles, here's my take: Focus on the big expenses first (like {top_category}), automate savings, and review monthly. What specific area would you like to optimize?",
            
            "🎯 Every family's financial journey is unique! The key is consistent tracking, smart budgeting, and having both short and long-term goals. What's your biggest financial priority right now?"
        ]
        return random.choice(responses)

# Initialize database
def init_db():
    conn = sqlite3.connect('finagent.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            transaction_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            target_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    family_name = data.get('family_name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([family_name, email, password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (family_name, email, password_hash) VALUES (?, ?, ?)',
            (family_name, email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Set session
        session['user_id'] = user_id
        session['family_name'] = family_name
        
        return jsonify({'success': True, 'user_id': user_id, 'family_name': family_name})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, family_name, password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['family_name'] = user[1]
            return jsonify({'success': True, 'user_id': user[0], 'family_name': user[1]})
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    category = data.get('category')
    description = data.get('description', '')
    
    if not all([amount, category]):
        return jsonify({'error': 'Amount and category are required'}), 400
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO transactions (user_id, amount, category, description, transaction_date) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'], float(amount), category, description, datetime.now().date())
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Transaction added successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, category, description, transaction_date, created_at 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY transaction_date DESC 
            LIMIT 50
        ''', (session['user_id'],))
        
        transactions = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'transactions': [
                {
                    'amount': t[0],
                    'category': t[1],
                    'description': t[2],
                    'transaction_date': t[3],
                    'created_at': t[4]
                } for t in transactions
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        # Current month spending
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', transaction_date) = ?
        ''', (session['user_id'], current_month))
        
        monthly_spending = cursor.fetchone()[0] or 0
        
        # Budget calculation (simple example - 70k monthly budget)
        monthly_budget = 70000
        budget_remaining = monthly_budget - monthly_spending
        
        # Goals count (placeholder)
        goals_on_track = 3
        total_goals = 5
        
        # Savings (placeholder)
        monthly_savings = 18500
        
        conn.close()
        
        return jsonify({
            'monthly_spending': monthly_spending,
            'budget_remaining': budget_remaining,
            'goals_on_track': f"{goals_on_track} of {total_goals}",
            'monthly_savings': monthly_savings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Get user's transaction data for context
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, category, description, transaction_date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY transaction_date DESC 
            LIMIT 20
        ''', (session['user_id'],))
        
        transactions = cursor.fetchall()
        conn.close()
        
        # Get AI response using fallback (no Ollama needed)
        response = get_fallback_chat_response(message, transactions)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        # Get user's recent transactions for generating smart alerts
        cursor.execute('''
            SELECT amount, category, transaction_date 
            FROM transactions 
            WHERE user_id = ? AND transaction_date >= ?
            ORDER BY transaction_date DESC
        ''', (session['user_id'], (datetime.now() - timedelta(days=7)).date()))
        
        transactions = cursor.fetchall()
        
        # Generate smart alerts based on spending patterns
        alerts = []
        
        if transactions:
            # Calculate weekly spending
            weekly_total = sum(t[0] for t in transactions)
            
            # Category analysis
            categories = {}
            for t in transactions:
                categories[t[1]] = categories.get(t[1], 0) + t[0]
            
            # Generate alerts
            if weekly_total > 15000:
                alerts.append({
                    'type': 'overspending',
                    'message': f'🚨 High spending alert: ₹{weekly_total:,.0f} this week. Consider reviewing your budget.',
                    'is_read': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if categories:
                top_category = max(categories, key=categories.get)
                if categories[top_category] > 8000:
                    alerts.append({
                        'type': 'category_alert',
                        'message': f'💡 {top_category} spending is high this week (₹{categories[top_category]:,.0f}). Try setting a weekly limit.',
                        'is_read': False,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # Positive reinforcement
            if weekly_total < 8000:
                alerts.append({
                    'type': 'good_progress',
                    'message': f'🎉 Great job! You\'ve kept spending under control this week (₹{weekly_total:,.0f}). Keep it up!',
                    'is_read': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Default alerts for new users
        if not alerts:
            alerts = [
                {
                    'type': 'welcome',
                    'message': '👋 Welcome to FinAgent! Start by adding your daily expenses to get personalized insights.',
                    'is_read': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    'type': 'tip',
                    'message': '💡 Pro tip: Set up weekly budgets for different categories like Food, Transport, and Entertainment.',
                    'is_read': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        
        conn.close()
        
        return jsonify({'alerts': alerts})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/insights', methods=['GET'])
def get_insights():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('finagent.db')
        cursor = conn.cursor()
        
        # Get recent transactions
        cursor.execute('''
            SELECT amount, category, description, transaction_date 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY transaction_date DESC 
            LIMIT 30
        ''', (session['user_id'],))
        
        transactions = cursor.fetchall()
        
        # Generate insights using fallback analysis
        insights = get_fallback_analysis(transactions)
        
        conn.close()
        
        return jsonify({'insights': insights})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__": #initiates server
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)