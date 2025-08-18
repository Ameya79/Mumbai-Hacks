
        // Global state
        let currentUser = null;
        let currentTab = 'overview';

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            initializeNavbar();
            initializeAuth();
            initializeForms();
        });

        // Navbar scroll effect
        function initializeNavbar() {
            window.addEventListener('scroll', function() {
                const navbar = document.getElementById('navbar');
                if (window.scrollY > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            });
        }

        // Modal functions
        function openModal(modalId) {
            document.getElementById(modalId).style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });

        // Authentication functions
        function initializeAuth() {
            // Check if user is already logged in (session storage for demo)
            const savedUser = sessionStorage.getItem('currentUser');
            if (savedUser) {
                currentUser = JSON.parse(savedUser);
                showDashboard();
            }
        }

        async function login(email, password) {
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();
                
                if (data.success) {
                    currentUser = { 
                        id: data.user_id, 
                        familyName: data.family_name,
                        email: email 
                    };
                    sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
                    showDashboard();
                    closeModal('loginModal');
                    showNotification('Welcome back!', 'success');
                } else {
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                showNotification('Login failed. Please try again.', 'error');
            }
        }

        async function signup(familyName, email, password) {
            try {
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        family_name: familyName, 
                        email, 
                        password 
                    })
                });

                const data = await response.json();
                
                if (data.success) {
                    currentUser = { 
                        id: data.user_id, 
                        familyName: data.family_name,
                        email: email 
                    };
                    sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
                    showDashboard();
                    closeModal('signupModal');
                    showNotification('Account created successfully!', 'success');
                } else {
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                showNotification('Signup failed. Please try again.', 'error');
            }
        }

        async function logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                currentUser = null;
                sessionStorage.removeItem('currentUser');
                showLanding();
                showNotification('Logged out successfully', 'success');
            } catch (error) {
                console.error('Logout error:', error);
            }
        }

        function showDashboard() {
            document.getElementById('landingPage').style.display = 'none';
            document.getElementById('dashboardPage').style.display = 'block';
            document.getElementById('authButtons').style.display = 'none';
            document.getElementById('userButtons').style.display = 'flex';
            
            if (currentUser) {
                document.getElementById('userWelcome').textContent = currentUser.familyName;
                document.getElementById('welcomeMessage').textContent = `Welcome back, ${currentUser.familyName}!`;
            }
            
            loadDashboardData();
        }

        function showLanding() {
            document.getElementById('landingPage').style.display = 'block';
            document.getElementById('dashboardPage').style.display = 'none';
            document.getElementById('authButtons').style.display = 'flex';
            document.getElementById('userButtons').style.display = 'none';
        }

        // Tab functionality
        function showTab(tabName) {
            // Hide all tabs
            const tabs = ['overview', 'transactions', 'goals', 'chat', 'alerts'];
            tabs.forEach(tab => {
                document.getElementById(tab + 'Tab').style.display = 'none';
            });

            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });

            // Show selected tab and mark button as active
            document.getElementById(tabName + 'Tab').style.display = 'block';
            event.target.classList.add('active');
            currentTab = tabName;

            // Load tab-specific data
            if (tabName === 'transactions') {
                loadTransactions();
            } else if (tabName === 'alerts') {
                loadAlerts();
            }
        }

        // Dashboard data loading
        async function loadDashboardData() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();
                
                if (data.error) {
                    console.error('Dashboard error:', data.error);
                    return;
                }

                document.getElementById('monthlySpending').textContent = `₹${data.monthly_spending.toLocaleString()}`;
                document.getElementById('budgetRemaining').textContent = `₹${data.budget_remaining.toLocaleString()}`;
                document.getElementById('goalsOnTrack').textContent = data.goals_on_track;
                document.getElementById('monthlySavings').textContent = `₹${data.monthly_savings.toLocaleString()}`;
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }

        // Transaction functions
        function initializeForms() {
            // Login form
            document.getElementById('loginForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                login(email, password);
            });

            // Signup form
            document.getElementById('signupForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const familyName = document.getElementById('familyName').value;
                const email = document.getElementById('signupEmail').value;
                const password = document.getElementById('signupPassword').value;
                signup(familyName, email, password);
            });

            // Transaction form
            document.getElementById('transactionForm').addEventListener('submit', function(e) {
                e.preventDefault();
                addTransaction();
            });
        }

        async function addTransaction() {
            const amount = document.getElementById('amount').value;
            const category = document.getElementById('category').value;
            const description = document.getElementById('description').value;

            if (!amount || !category) {
                showNotification('Please fill in amount and category', 'error');
                return;
            }

            try {
                const response = await fetch('/api/transactions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ amount, category, description })
                });

                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('transactionForm').reset();
                    showNotification('Transaction added successfully!', 'success');
                    loadTransactions();
                    loadDashboardData(); // Refresh dashboard stats
                } else {
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                showNotification('Failed to add transaction', 'error');
            }
        }

        async function loadTransactions() {
            try {
                const response = await fetch('/api/transactions');
                const data = await response.json();
                
                if (data.error) {
                    console.error('Transaction error:', data.error);
                    return;
                }

                const container = document.getElementById('transactionsContainer');
                
                if (data.transactions.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: var(--gray-500);">
                            <i class="fas fa-receipt" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                            <p>No transactions yet. Add your first expense above!</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = data.transactions.map(transaction => `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; border-bottom: 1px solid var(--gray-200); last-child: border-bottom: none;">
                        <div>
                            <div style="font-weight: 600; color: var(--gray-900);">₹${transaction.amount.toLocaleString()}</div>
                            <div style="color: var(--gray-600); font-size: 0.875rem;">${transaction.category}</div>
                            ${transaction.description ? `<div style="color: var(--gray-500); font-size: 0.8rem;">${transaction.description}</div>` : ''}
                        </div>
                        <div style="text-align: right;">
                            <div style="color: var(--gray-600); font-size: 0.875rem;">${new Date(transaction.transaction_date).toLocaleDateString()}</div>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading transactions:', error);
            }
        }

        // Chat functionality
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;

            // Add user message
            addChatMessage(message, 'user');
            input.value = '';

            // Add loading message
            const loadingId = addChatMessage('<div class="loading"></div> Thinking...', 'ai');

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message })
                });

                const data = await response.json();
                
                // Remove loading message
                document.getElementById(loadingId).remove();
                
                if (data.response) {
                    addChatMessage(data.response, 'ai');
                } else {
                    addChatMessage('Sorry, I had trouble processing your request.', 'ai');
                }
            } catch (error) {
                document.getElementById(loadingId).remove();
                addChatMessage('Sorry, I had trouble connecting. Please try again.', 'ai');
            }
        }

        function addChatMessage(content, type) {
            const container = document.getElementById('chatMessages');
            const messageId = 'msg-' + Date.now();
            
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <i class="fas ${type === 'user' ? 'fa-user' : 'fa-robot'}"></i>
                </div>
                <div class="message-content">${content}</div>
            `;
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
            
            return messageId;
        }

        // Alerts functionality
        async function loadAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();
                
                if (data.error) {
                    console.error('Alerts error:', data.error);
                    return;
                }

                const container = document.getElementById('alertsContainer');
                
                if (data.alerts.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: var(--gray-500);">
                            <i class="fas fa-bell" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                            <p>No alerts at the moment. Keep tracking your expenses!</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = data.alerts.map(alert => `
                    <div class="alert-card ${alert.type === 'overspending' ? 'error' : alert.type === 'good_progress' ? 'success' : ''}">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">${alert.type.replace('_', ' ').toUpperCase()}</div>
                        <div style="color: var(--gray-700);">${alert.message}</div>
                        <div style="color: var(--gray-500); font-size: 0.875rem; margin-top: 0.5rem;">
                            ${new Date(alert.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading alerts:', error);
            }
        }

        // Notification system
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--primary)'};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 0.75rem;
                box-shadow: var(--shadow-lg);
                z-index: 3000;
                font-weight: 600;
                transform: translateX(400px);
                transition: transform 0.3s ease;
            `;
            notification.innerHTML = `
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}" style="margin-right: 0.5rem;"></i>
                ${message}
            `;
            
            document.body.appendChild(notification);
            
            // Animate in
            setTimeout(() => {
                notification.style.transform = 'translateX(0)';
            }, 100);
            
            // Remove after 3 seconds
            setTimeout(() => {
                notification.style.transform = 'translateX(400px)';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        }

        // Smooth scrolling for anchor links
        document.addEventListener('click', function(e) {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const target = document.querySelector(e.target.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });

        // Add some demo data for first-time users
        function addDemoData() {
            // This would be called after signup to add some sample transactions
            // For demo purposes only
        }
   