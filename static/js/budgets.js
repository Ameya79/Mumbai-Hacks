document.addEventListener('DOMContentLoaded', () => {
    const apiUrl = '/api/budgets';
    const budgetList = document.getElementById('budgetList');
    const addBudgetBtn = document.getElementById('addBudgetBtn');
    const budgetModal = document.getElementById('budgetModal');
    const closeBudgetModal = document.getElementById('closeBudgetModal');
    const budgetForm = document.getElementById('budgetForm');
    const cancelBudgetBtn = document.getElementById('cancelBudgetBtn');

    const openModal = () => {
        budgetModal.classList.remove('hidden');
    };

    const closeModal = () => {
        budgetModal.classList.add('hidden');
        budgetForm.reset();
    };

    const addBudget = async (e) => {
        e.preventDefault();
        const formData = new FormData(budgetForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                closeModal();
                fetchBudgets();
            } else {
                console.error('Failed to add budget');
            }
        } catch (error) {
            console.error('Error adding budget:', error);
        }
    };

    const fetchBudgets = async () => {
        try {
            const response = await fetch(apiUrl);
            const budgets = await response.json();
            renderBudgets(budgets);
        } catch (error) {
            console.error('Error fetching budgets:', error);
        }
    };

    const renderBudgets = (budgets) => {
        budgetList.innerHTML = '';
        budgets.forEach(budget => {
            const budgetCard = document.createElement('div');
            budgetCard.className = 'budget-card';
            const percentage = (budget.spent / budget.limit) * 100;

            budgetCard.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">${budget.category}</h3>
                    <span class="text-sm font-medium">${budget.period}</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-4 dark:bg-gray-700">
                    <div class="h-4 rounded-full" style="width: ${Math.min(percentage, 100)}%; background-color: var(--primary);"></div>
                </div>
                <div class="flex justify-between items-center mt-2">
                    <span class="text-sm text-gray-600 dark:text-gray-400">$${budget.spent.toFixed(2)} spent</span>
                    <span class="text-sm text-gray-600 dark:text-gray-400">$${budget.limit.toFixed(2)} limit</span>
                </div>
            `;
            budgetList.appendChild(budgetCard);
        });
    };

    fetchBudgets();

    addBudgetBtn.addEventListener('click', openModal);
    closeBudgetModal.addEventListener('click', closeModal);
    cancelBudgetBtn.addEventListener('click', closeModal);
    budgetForm.addEventListener('submit', addBudget);

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'add') {
        openModal();
    }
});
