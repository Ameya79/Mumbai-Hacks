// Simple, Clean Dashboard with Core Functionality
class Dashboard {
    constructor() {
        this.apiUrl = '/api';
        this.transactions = [];
        this.budgets = [];
        this.savingsGoals = [];
        this.init();
    }

    init() {
        this.initElements();
        this.bindEvents();
        this.checkAuthentication();
    }

    initElements() {
        // Get DOM elements
        this.summaryCards = document.querySelector('[data-summary-cards]');
        this.transactionsList = document.querySelector('[data-transactions-list]');
        this.budgetList = document.querySelector('[data-budget-list]');
        this.savingsGoals = document.querySelector('[data-savings-goals]');
        this.spendingChart = document.getElementById('spendingChart');
        this.spendingChartEmpty = document.getElementById('spendingChartEmpty');
        
        // Modal elements
        this.transactionModal = document.getElementById('transactionModal');
        this.transactionForm = document.getElementById('transactionForm');
        this.closeModal = document.getElementById('closeModal');
        this.cancelBtn = document.getElementById('cancelBtn');
        
        // Notifications
        this.notifBtn = document.getElementById('notifBtn');
        this.notifDropdown = document.getElementById('notifDropdown');
        this.notifList = document.getElementById('notifList');
        this.notifDot = document.getElementById('notifDot');

        // Dark mode is forced globally; no toggle

        // Editable metrics
        this.editableMetrics = document.querySelectorAll('[data-editable-metric]');
    }

    async checkAuthentication() {
        try {
            const response = await fetch('/api/auth/check');
            const data = await response.json();
            
            if (data.authenticated) {
                // User is authenticated, load dashboard
                this.loadDashboardData();
                this.initChart();
                this.updateUserInfo(data.user);
            } else {
                // User is not authenticated, redirect to login
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            // Redirect to login on error
            window.location.href = '/login';
        }
    }

    updateUserInfo(user) {
        // No-op for now
    }

    bindEvents() {
        // Transaction modal events
        if (this.closeModal) {
            this.closeModal.addEventListener('click', () => this.closeTransactionModal());
        }
        
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.closeTransactionModal());
        }

        // Close modal when clicking outside
        if (this.transactionModal) {
            this.transactionModal.addEventListener('click', (e) => {
                if (e.target === this.transactionModal) {
                    this.closeTransactionModal();
                }
            });
        }

        // Form submission
        if (this.transactionForm) {
            this.transactionForm.addEventListener('submit', (e) => {
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

                // Reset all buttons
                typeButtons.forEach(b => {
                    b.classList.remove('bg-secondary/10', 'text-secondary', 'border-secondary', 'bg-danger/10', 'text-danger', 'border-danger');
                    b.classList.add('border-gray-300');
                });

                // Style selected button
                if (type === 'income') {
                    btn.classList.add('bg-secondary/10', 'text-secondary', 'border-secondary');
                } else {
                    btn.classList.add('bg-danger/10', 'text-danger', 'border-danger');
                }
                btn.classList.remove('border-gray-300');
            });
        });

        // Floating action button
        const floatingBtn = document.querySelector('.floating-btn');
        if (floatingBtn) {
            floatingBtn.addEventListener('click', () => this.openTransactionModal());
        }

        // No theme toggle logic

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.transactionModal && !this.transactionModal.classList.contains('hidden')) {
                    this.closeTransactionModal();
                }
            }
        });

        // Notifications toggle and fetch
        if (this.notifBtn && this.notifDropdown) {
            this.notifBtn.addEventListener('click', async () => {
                this.notifDropdown.classList.toggle('hidden');
                if (!this.notifDropdown.classList.contains('hidden')) {
                    await this.loadNotifications();
                }
            });
            document.addEventListener('click', (e) => {
                if (!this.notifDropdown.contains(e.target) && !this.notifBtn.contains(e.target)) {
                    this.notifDropdown.classList.add('hidden');
                }
            });
        }

        // Editable metrics events
        this.editableMetrics.forEach((el) => {
            el.addEventListener('focus', () => {
                el.dataset.original = el.textContent.trim();
            });
            el.addEventListener('blur', () => this.handleEditableMetricSave(el));
            el.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    el.blur();
                }
                if (e.key === 'Escape') {
                    el.textContent = el.dataset.original || el.textContent;
                    el.blur();
                }
            });
        });
    }

    async loadDashboardData() {
        try {
            // Show loading state
            this.showLoading();
            
            // Load data in parallel
            const [dashboardData, transactions, budgets, savingsGoals] = await Promise.all([
                this.fetchAPI('/dashboard'),
                this.fetchAPI('/transactions'),
                this.fetchAPI('/budgets'),
                this.fetchAPI('/savings-goals')
            ]);

            // Update UI with data
            this.updateDashboardSummary(dashboardData);
            this.updateTransactionsList(transactions || []);
            this.updateBudgetProgress(budgets || []);
            this.updateSavingsGoals(savingsGoals || []);

            // Keep transactions for chart empty-state decision
            this.transactions = Array.isArray(transactions) ? transactions : [];
            this.initChart();
            
            // Hide loading
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Error loading dashboard data', 'error');
            this.hideLoading();
        }
    }

    async fetchAPI(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login';
                    return null;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            return null;
        }
    }

    updateDashboardSummary(data) {
        if (!data || !this.summaryCards) return;

        // Create summary cards (with editable Total Balance)
        const cards = [
            { label: 'Total Balance', value: data.totalBalance || 0, metric: 'totalBalance', editable: true },
            { label: 'Monthly Income', value: data.monthlyIncome || 0, metric: 'monthlyIncome' },
            { label: 'Monthly Expenses', value: data.monthlyExpenses || 0, metric: 'monthlyExpenses' },
            { label: 'Savings Goal', value: data.savingsGoal || 0, metric: 'savingsGoal' }
        ];

        this.summaryCards.innerHTML = cards.map(card => `
            <div class="bg-white dark:bg-[var(--card-bg)] dark:border dark:border-[var(--border-color)] p-6 rounded-xl shadow-sm">
                <p class="text-sm font-medium text-gray-500 dark:text-[var(--text-tertiary)]">${card.label}</p>
                <h3 class="text-2xl font-bold mt-1 dark:text-[var(--text-primary)] ${card.editable ? 'outline-none focus:ring-2 focus:ring-indigo-500 rounded' : ''}" 
                    ${card.editable ? 'contenteditable="true" data-editable-metric="totalBalance"' : ''} 
                    data-metric="${card.metric}">
                    ${this.formatCurrency(card.value)}
                </h3>
                ${card.editable ? '<p class="text-xs text-gray-400 mt-1">Click to edit</p>' : ''}
            </div>
        `).join('');

        // Re-bind editable metrics after re-render
        this.editableMetrics = document.querySelectorAll('[data-editable-metric]');
        this.editableMetrics.forEach((el) => {
            el.addEventListener('focus', () => {
                el.dataset.original = el.textContent.trim();
            });
            el.addEventListener('blur', () => this.handleEditableMetricSave(el));
            el.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    el.blur();
                }
                if (e.key === 'Escape') {
                    el.textContent = el.dataset.original || el.textContent;
                    el.blur();
                }
            });
        });
    }

    updateTransactionsList(transactions) {
        if (!this.transactionsList) return;

        if (!transactions || transactions.length === 0) {
            this.transactionsList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-receipt text-4xl mb-4"></i>
                    <p>No transactions yet</p>
                    <p class="text-sm">Add your first transaction to get started</p>
                </div>
            `;
            return;
        }

        this.transactionsList.innerHTML = transactions.slice(0, 4).map(transaction => `
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
        if (!this.budgetList) return;

        if (!budgets || budgets.length === 0) {
            this.budgetList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-bullseye text-4xl mb-4"></i>
                    <p>No budgets set yet</p>
                    <p class="text-sm">Create budgets to track your spending</p>
                </div>
            `;
            return;
        }

        this.budgetList.innerHTML = budgets.map(budget => {
            const percentage = (budget.spent / budget.limit) * 100;
            return `
                <div class="mb-4">
                    <div class="flex justify-between mb-1">
                        <span class="font-medium">${budget.category}</span>
                        <span class="text-sm text-gray-500">$${budget.spent} / $${budget.limit}</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-${this.getBudgetColor(percentage)} h-2 rounded-full transition-all duration-300" 
                            style="width: ${Math.min(percentage, 100)}%">
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateSavingsGoals(goals) {
        if (!this.savingsGoals) return;

        if (!goals || goals.length === 0) {
            this.savingsGoals.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-piggy-bank text-4xl mb-4"></i>
                    <p>No savings goals yet</p>
                    <p class="text-sm">Set your first savings goal to start building wealth</p>
                </div>
            `;
            return;
        }

        this.savingsGoals.innerHTML = goals.map(goal => {
            const percentage = (goal.current / goal.target) * 100;
            return `
                <div class="bg-gray-50 dark:bg-[var(--bg-secondary)] p-4 rounded-lg">
                    <div class="flex justify-between items-center mb-2">
                        <h4 class="font-medium">${goal.name}</h4>
                        <span class="text-sm text-gray-500">${Math.round(percentage)}%</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div class="bg-secondary h-2 rounded-full transition-all duration-300" 
                            style="width: ${percentage}%">
                        </div>
                    </div>
                    <p class="text-sm text-gray-600">$${goal.current} / $${goal.target}</p>
                </div>
            `;
        }).join('');
    }

    initChart() {
        if (!this.spendingChart) return;

        const ctx = this.spendingChart.getContext('2d');
        
        // Check if there's data to show
        if (!this.transactions || this.transactions.length === 0) {
            if (this.spendingChartEmpty) {
                this.spendingChart.style.display = 'none';
                this.spendingChartEmpty.classList.remove('hidden');
            }
            return;
        }

        this.chart = new Chart(ctx, {
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
                }
            }
        });
    }

    async addTransaction() {
        try {
            const form = document.getElementById('transactionForm');
            const formData = new FormData(form);
            const transactionData = Object.fromEntries(formData.entries());
            
            // Validate data
            if (!this.validateTransaction(transactionData)) {
                return;
            }

            // Convert amount to number
            transactionData.amount = parseFloat(transactionData.amount);

            const result = await this.fetchAPI('/transactions', {
                method: 'POST',
                body: JSON.stringify(transactionData)
            });

            if (result && result.success) {
                this.showNotification('Transaction added successfully!', 'success');
                this.closeTransactionModal();
                this.loadDashboardData(); // Refresh data
                form.reset();
            } else {
                this.showNotification('Error adding transaction', 'error');
            }
            
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

    // Editable metric save handler
    async handleEditableMetricSave(el) {
        const raw = el.textContent.trim();
        const cleaned = raw.replace(/[^0-9.\-]/g, '');
        const value = parseFloat(cleaned);
        if (isNaN(value)) {
            el.textContent = el.dataset.original || el.textContent;
            this.showNotification('Please enter a valid number', 'error');
            return;
        }
        const confirmed = await this.inlineConfirm(`Set total balance to ${this.formatCurrency(value)}?`);
        if (!confirmed) {
            el.textContent = el.dataset.original || this.formatCurrency(value);
            return;
        }
        // Optimistic UI
        el.textContent = this.formatCurrency(value);
        try {
            const res = await this.fetchAPI('/dashboard/total-balance', {
                method: 'POST',
                body: JSON.stringify({ total_balance: value })
            });
            if (!res || res.success !== true) {
                throw new Error('Save failed');
            }
            // Ensure latest numbers refresh
            await this.loadDashboardData();
            this.showNotification('Total balance updated', 'success');
        } catch (e) {
            this.showNotification('Could not save balance. Please try again shortly.', 'error');
            el.textContent = el.dataset.original || el.textContent;
        }
    }

    inlineConfirm(message) {
        return new Promise((resolve) => {
            const bar = document.createElement('div');
            bar.className = 'inline-confirm-bar';
            bar.innerHTML = `
                <span>${this.escapeHtml(message)}</span>
                <div class="actions">
                    <button class="confirm">OK</button>
                    <button class="cancel">Cancel</button>
                </div>
            `;
            document.body.appendChild(bar);
            const cleanup = () => bar.remove();
            bar.querySelector('.confirm').addEventListener('click', () => { cleanup(); resolve(true); });
            bar.querySelector('.cancel').addEventListener('click', () => { cleanup(); resolve(false); });
        });
    }

    // Notifications loader
    async loadNotifications() {
        const data = await this.fetchAPI('/notifications');
        const list = this.notifList;
        if (!list) return;
        if (!data || !Array.isArray(data) || data.length === 0) {
            list.innerHTML = '<div class="p-4 text-sm text-gray-500">No alerts</div>';
            if (this.notifDot) this.notifDot.classList.add('hidden');
            return;
        }
        if (this.notifDot) this.notifDot.classList.remove('hidden');
        list.innerHTML = data.map(n => `
            <div class="p-4 hover:bg-gray-50 dark:hover:bg-[var(--bg-secondary)]">
                <p class="text-sm ${n.type === 'warning' ? 'text-yellow-600' : n.type === 'error' ? 'text-red-600' : 'text-gray-700'}">${this.escapeHtml(n.message)}</p>
                <p class="text-xs text-gray-400 mt-1">${this.formatDate(n.created_at || n.timestamp)}</p>
            </div>
        `).join('');
    }

    // Modal Management
    openTransactionModal() {
        if (this.transactionModal) {
            this.transactionModal.classList.remove('hidden');
            // Set today's date as default
            const dateInput = document.getElementById('date');
            if (dateInput) {
                dateInput.value = new Date().toISOString().split('T')[0];
            }
        }
    }

    closeTransactionModal() {
        if (this.transactionModal) {
            this.transactionModal.classList.add('hidden');
        }
        if (this.transactionForm) {
            this.transactionForm.reset();
        }
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
            'groceries': 'fa-shopping-basket',
            'utilities': 'fa-lightbulb',
            'transportation': 'fa-car',
            'entertainment': 'fa-film',
            'healthcare': 'fa-heart',
            'salary': 'fa-money-bill-wave',
            'dining': 'fa-utensils',
            'shopping': 'fa-shopping-bag',
            'other': 'fa-question'
        };
        return icons[category] || 'fa-question';
    }

    getCategoryColor(category) {
        const colors = {
            'groceries': 'bg-red-100 text-red-500',
            'utilities': 'bg-purple-100 text-purple-500',
            'transportation': 'bg-blue-100 text-blue-500',
            'entertainment': 'bg-green-100 text-green-500',
            'healthcare': 'bg-pink-100 text-pink-500',
            'salary': 'bg-green-100 text-green-500',
            'dining': 'bg-orange-100 text-orange-500',
            'shopping': 'bg-indigo-100 text-indigo-500',
            'other': 'bg-gray-100 text-gray-500'
        };
        return colors[category] || 'bg-gray-100 text-gray-500';
    }

    getBudgetColor(percentage) {
        if (percentage < 50) return 'secondary';
        if (percentage < 80) return 'warning';
        return 'danger';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }

    showLoading() {
        // Add loading indicator if needed
    }

    hideLoading() {
        // Hide loading indicator if needed
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
