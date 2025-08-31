// Global JavaScript
class FamilyFinanceApp {
    constructor() {
        this.apiUrl = '/api';
        this.transactions = [];
        this.budgets = [];
        this.savingsGoals = [];
        this.init();
    }

    init() {
        this.initModal();
        this.initChart();
        this.loadDashboardData();
        this.bindEvents();
    }


    // Modal Management
    initModal() {
        const floatingBtn = document.querySelector('.floating-btn');
        const transactionModal = document.getElementById('transactionModal');
        const closeModal = document.getElementById('closeModal');
        const transactionForm = document.getElementById('transactionForm');
        
        if (floatingBtn) {
            floatingBtn.addEventListener('click', () => {
                transactionModal.classList.remove('hidden');
                transactionModal.querySelector('.bg-white').classList.add('modal-enter');
            });
        }
        
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                this.closeTransactionModal();
            });
        }

        // Close modal when clicking outside
        if (transactionModal) {
            transactionModal.addEventListener('click', (e) => {
                if (e.target === transactionModal) {
                    this.closeTransactionModal();
                }
            });
        }

        // Handle form submission
        if (transactionForm) {
            transactionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addTransaction();
            });
        }

        // Transaction type toggle
        const typeButtons = document.querySelectorAll('[data-type]');
        const transactionTypeInput = document.getElementById('transactionType');
        
        typeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const type = btn.getAttribute('data-type');
                transactionTypeInput.value = type;

                typeButtons.forEach(b => {
                    b.classList.remove('bg-secondary/10', 'text-secondary', 'border-secondary', 'bg-danger/10', 'text-danger', 'border-danger');
                    b.classList.add('border-gray-300');
                });

                if (type === 'income') {
                    btn.classList.add('bg-secondary/10', 'text-secondary', 'border-secondary');
                } else {
                    btn.classList.add('bg-danger/10', 'text-danger', 'border-danger');
                }
                btn.classList.remove('border-gray-300');
            });
        });
    }

    closeTransactionModal() {
        const transactionModal = document.getElementById('transactionModal');
        transactionModal.classList.add('hidden');
        document.getElementById('transactionForm').reset();
    }

    // Chart Initialization
    initChart() {
        const ctx = document.getElementById('spendingChart');
        if (!ctx) return;

        this.spendingChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Housing', 'Food', 'Transport', 'Utilities', 'Entertainment', 'Healthcare', 'Others'],
                datasets: [{
                    label: 'Spending ($)',
                    data: [1200, 650, 450, 210, 180, 150, 300],
                    backgroundColor: [
                        'rgba(79, 70, 229, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(239, 68, 68, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(20, 184, 166, 0.7)',
                        'rgba(139, 92, 246, 0.7)'
                    ],
                    borderColor: [
                        'rgba(79, 70, 229, 1)',
                        'rgba(16, 185, 129, 1)',
                        'rgba(239, 68, 68, 1)',
                        'rgba(245, 158, 11, 1)',
                        'rgba(99, 102, 241, 1)',
                        'rgba(20, 184, 166, 1)',
                        'rgba(139, 92, 246, 1)'
                    ],
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        // Add dark mode options
        const isDark = document.documentElement.classList.contains('dark');
        this.spendingChart.options.plugins.legend.labels.color = isDark ? '#fff' : '#374151';
        this.spendingChart.options.scales.y.grid.color = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        this.spendingChart.options.scales.y.ticks.color = isDark ? '#fff' : '#374151';
        this.spendingChart.options.scales.x.ticks.color = isDark ? '#fff' : '#374151';
    }

    // Event Binding
    bindEvents() {
        // Period selector for chart
        const periodSelect = document.querySelector('select');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.updateChartPeriod(e.target.value);
            });
        }

        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('transactionModal');
                if (!modal.classList.contains('hidden')) {
                    this.closeTransactionModal();
                }
            }
        });
        
    }

    // API Methods
    async loadDashboardData() {
        try {
            const loader = document.getElementById('loader');
            if (loader) {
                loader.classList.remove('hidden');
            }
            
            const [dashboardData, transactions, budgets, savingsGoals] = await Promise.all([
                this.fetchAPI('/dashboard'),
                this.fetchAPI('/transactions'),
                this.fetchAPI('/budgets'),
                this.fetchAPI('/savings-goals')
            ]);

            this.updateDashboardSummary(dashboardData);
            this.updateTransactionsList(transactions);
            this.updateBudgetProgress(budgets);
            this.updateSavingsGoals(savingsGoals);
            
            if (loader) {
                loader.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Error loading dashboard data', 'error');
            const loader = document.getElementById('loader');
            if (loader) {
                loader.classList.add('hidden');
            }
        }
    }

    async fetchAPI(endpoint, options = {}) {
        const response = await fetch(`${this.apiUrl}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    async addTransaction() {
        try {
            const form = document.getElementById('transactionForm');
            const formData = new FormData(form);
            const transactionData = Object.fromEntries(formData.entries());
            transactionData.amount = parseFloat(transactionData.amount);

            if (!this.validateTransaction(transactionData)) {
                return;
            }

            const result = await this.fetchAPI('/transactions', {
                method: 'POST',
                body: JSON.stringify(transactionData)
            });

            this.showNotification('Transaction added successfully!', 'success');
            this.closeTransactionModal();
            this.loadDashboardData();
            // Dispatch a custom event to notify other parts of the app
            document.dispatchEvent(new CustomEvent('transactionAdded'));
            
        } catch (error) {
            console.error('Error adding transaction:', error);
            this.showNotification('Error adding transaction', 'error');
        }
    }

    validateTransaction(data) {
        const errors = [];
        
        if (!data.amount || data.amount <= 0) {
            errors.push('Amount must be greater than 0');
        }
        if (!data.category) {
            errors.push('Please select a category');
        }
        if (!data.date) {
            errors.push('Please select a date');
        }

        if (errors.length > 0) {
            this.showNotification(errors.join(', '), 'error');
            return false;
        }
        
        return true;
    }

    updateDashboardSummary(data) {
        if (!data) return;
        
        const elements = {
            totalBalance: document.querySelector('[data-metric="totalBalance"]'),
            monthlyIncome: document.querySelector('[data-metric="monthlyIncome"]'),
            monthlyExpenses: document.querySelector('[data-metric="monthlyExpenses"]'),
            savingsGoal: document.querySelector('[data-metric="savingsGoal"]')
        };

        Object.keys(elements).forEach(key => {
            if (elements[key] && data[key]) {
                elements[key].textContent = this.formatCurrency(data[key]);
            }
        });
    }

    updateTransactionsList(transactions) {
        const container = document.querySelector('[data-transactions-list]');
        if (!container || !transactions) return;

        container.innerHTML = transactions.slice(0, 4).map(transaction => `
            <div class="flex items-start">
                <div class="p-2 rounded-lg ${this.getCategoryColor(transaction.category)} mr-3">
                    <i class="fas ${this.getCategoryIcon(transaction.category)}"></i>
                </div>
                <div class="flex-1">
                    <p class="font-medium">${transaction.description || transaction.category}</p>
                    <p class="text-xs text-gray-500">${this.formatDate(transaction.date)}</p>
                </div>
                <div class="text-${transaction.type === 'income' ? 'secondary' : 'danger'} font-medium">
                    ${transaction.type === 'income' ? '+' : '-'}${this.formatCurrency(transaction.amount)}
                </div>
            </div>
        `).join('');
    }

    updateBudgetProgress(budgets) {
        const container = document.querySelector('[data-budget-list]');
        if (!container || !budgets) return;

        container.innerHTML = budgets.map(budget => {
            const percentage = (budget.spent / budget.limit) * 100;
            return `
                <div class="mb-4">
                    <div class="flex justify-between mb-1">
                        <span class="font-medium">${budget.category}</span>
                        <span class="text-sm text-gray-500">$${budget.spent} / $${budget.limit}</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-${this.getBudgetColor(percentage)} h-2 rounded-full progress-bar" 
                            style="width: ${Math.min(percentage, 100)}%">
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateSavingsGoals(goals) {
        if (!goals || goals.length === 0) return;

        const mainGoal = goals[0];
        const percentage = (mainGoal.current / mainGoal.target) * 100;

        const progressRing = document.querySelector('.progress-ring__circle');
        if (progressRing) {
            progressRing.style.strokeDasharray = `${percentage}, 100`;
        }

        const percentageText = document.querySelector('.w-32.h-32 text');
        if (percentageText) {
            percentageText.textContent = `${Math.round(percentage)}%`;
        }

        const goalName = document.querySelector('.text-lg.font-medium.mt-2');
        if (goalName) {
            goalName.textContent = mainGoal.name;
        }

        const goalAmount = document.querySelector('.text-sm.text-gray-500');
        if (goalAmount) {
            goalAmount.textContent = `$${mainGoal.current} / $${mainGoal.target}`;
        }
    }

    updateChartPeriod(period) {
        console.log('Updating chart for period:', period);
        // Implementation would fetch new data and update the chart
    }

    // Utility Methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    }

    getCategoryIcon(category) {
        const icons = {
            'Groceries': 'fa-shopping-basket',
            'Utilities': 'fa-lightbulb',
            'Transportation': 'fa-car',
            'Entertainment': 'fa-film',
            'Healthcare': 'fa-heart',
            'Salary': 'fa-money-bill-wave',
            'Dining': 'fa-utensils',
            'Shopping': 'fa-shopping-bag',
            'Other': 'fa-question'
        };
        return icons[category] || 'fa-question';
    }

    getCategoryColor(category) {
        const colors = {
            'Groceries': 'bg-red-100 text-red-500',
            'Utilities': 'bg-purple-100 text-purple-500',
            'Transportation': 'bg-blue-100 text-blue-500',
            'Entertainment': 'bg-green-100 text-green-500',
            'Healthcare': 'bg-pink-100 text-pink-500',
            'Salary': 'bg-green-100 text-green-500',
            'Dining': 'bg-orange-100 text-orange-500',
            'Shopping': 'bg-indigo-100 text-indigo-500',
            'Other': 'bg-gray-100 text-gray-500'
        };
        return colors[category] || 'bg-gray-100 text-gray-500';
    }

    getBudgetColor(percentage) {
        if (percentage < 50) return 'secondary';
        if (percentage < 80) return 'warning';
        return 'danger';
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }

    showLoading() {
        const loader = document.createElement('div');
        loader.innerHTML = '<div class="loading"></div>';
        loader.id = 'globalLoader';
        loader.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        document.body.appendChild(loader);
    }

    hideLoading() {
        const loader = document.getElementById('globalLoader');
        if (loader) loader.remove();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'none';
    }

    // Theme Management (force dark everywhere)
    const html = document.documentElement;
    html.classList.add('dark');
    try {
        localStorage.setItem('theme', 'dark');
        document.cookie = 'theme=dark;path=/;max-age=31536000';
    } catch (e) {}

    // Sidebar Management
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const sidebar = document.getElementById('sidebar');
    const minimizeBtn = document.getElementById('minimizeBtn');
    if (mobileMenuButton && sidebar) {
        mobileMenuButton.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
    if (minimizeBtn && sidebar) {
        minimizeBtn.addEventListener('click', () => {
            sidebar.classList.toggle('minimized');
            const mainContent = document.getElementById('mainContent');
            mainContent.classList.toggle('md:ml-64');
            mainContent.classList.toggle('md:ml-20');
            if (sidebar.classList.contains('minimized')) {
                minimizeBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
            } else {
                minimizeBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
            }
        });
    }
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768 && sidebar && mobileMenuButton && !sidebar.contains(e.target) && !mobileMenuButton.contains(e.target) && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });

    // Navigation Links
    const navLinks = document.querySelectorAll('nav a');
    const path = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === path) {
            link.classList.add('bg-gray-100', 'dark:bg-gray-800');
        }
        link.addEventListener('click', () => {
            window.location.href = link.href;
        });
    });

    // Profile Link
    const profileLink = document.getElementById('profile-link');
    if (profileLink) {
        profileLink.addEventListener('click', () => {
            window.location.href = '/profile';
        });
    }

    // Chatbot functionality
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotInput = document.getElementById('chatbot-input');

    if (chatbotToggle && chatbotWindow) {
        chatbotToggle.addEventListener('click', () => {
            chatbotWindow.classList.toggle('hidden');
        });
    }

    async function sendChatMessage(text) {
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `HTTP ${res.status}`);
            }
            const data = await res.json();
            appendMessage('bot', data.response || 'Sorry, I could not reply.');
        } catch (e) {
            appendMessage('bot', 'Please log in to use the chatbot.');
        }
    }

    const chatbotSend = document.getElementById('chatbot-send');
    if (chatbotInput && chatbotMessages) {
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && chatbotInput.value.trim() !== '') {
                const userMessage = chatbotInput.value.trim();
                appendMessage('user', userMessage);
                chatbotInput.value = '';
                sendChatMessage(userMessage);
            }
        });
    }
    if (chatbotSend && chatbotInput) {
        chatbotSend.addEventListener('click', () => {
            if (chatbotInput.value.trim() === '') return;
            const userMessage = chatbotInput.value.trim();
            appendMessage('user', userMessage);
            chatbotInput.value = '';
            sendChatMessage(userMessage);
        });
    }

    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('mb-2', sender === 'user' ? 'text-right' : 'text-left');
        
        const messageBubble = document.createElement('div');
        messageBubble.classList.add('inline-block', 'p-2', 'rounded-lg', 
            sender === 'user' ? 'bg-primary' : 'bg-gray-200',
            sender === 'user' ? 'text-white' : 'text-gray-800'
        );
        messageBubble.textContent = text;
        
        messageDiv.appendChild(messageBubble);
        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
});
