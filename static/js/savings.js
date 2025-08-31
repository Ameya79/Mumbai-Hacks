document.addEventListener('DOMContentLoaded', () => {
    const apiUrl = '/api/savings-goals';
    const savingsList = document.getElementById('savingsList');
    const addSavingsBtn = document.getElementById('addSavingsBtn');
    const savingsModal = document.getElementById('savingsModal');
    const closeSavingsModal = document.getElementById('closeSavingsModal');
    const savingsForm = document.getElementById('savingsForm');
    const cancelSavingsBtn = document.getElementById('cancelSavingsBtn');

    const fetchSavings = async () => {
        try {
            const response = await fetch(apiUrl);
            const savings = await response.json();
            renderSavings(savings);
        } catch (error) {
            console.error('Error fetching savings:', error);
        }
    };

    const renderSavings = (savings) => {
        savingsList.innerHTML = '';
        savings.forEach((goal, index) => {
            const savingsCard = document.createElement('div');
            savingsCard.className = 'bg-white p-6 rounded-xl shadow-sm cursor-move';
            savingsCard.dataset.id = goal.id;
            const percentage = (goal.current / goal.target) * 100;

            savingsCard.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">${goal.name}</h3>
                    <span class="text-sm font-medium">Target: $${goal.target.toFixed(2)}</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-4 dark:bg-gray-700">
                    <div class="h-4 rounded-full" style="width: ${Math.min(percentage, 100)}%; background-color: var(--secondary);"></div>
                </div>
                <div class="flex justify-between items-center mt-2">
                    <span class="text-sm text-gray-600 dark:text-gray-400">$${goal.current.toFixed(2)} saved</span>
                    <span class="text-sm text-gray-600 dark:text-gray-400">${goal.target_date ? `Due: ${new Date(goal.target_date).toLocaleDateString()}` : ''}</span>
                </div>
                <div class="flex justify-between items-center mt-2">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Priority: <span class="priority-value">${formatOrdinal(index + 1)}</span></span>
                </div>
            `;
            savingsList.appendChild(savingsCard);
        });

        new Sortable(savingsList, {
            animation: 150,
            onEnd: async (evt) => {
                const goalIds = Array.from(savingsList.children).map(card => card.dataset.id);
                await updatePriorities(goalIds);
            }
        });
    };

    const formatOrdinal = (n) => {
        const s = ["th", "st", "nd", "rd"];
        const v = n % 100;
        return n + (s[(v - 20) % 10] || s[v] || s[0]);
    };

    const updatePriorities = async (goalIds) => {
        try {
            const response = await fetch(`${apiUrl}/reorder`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ goal_ids: goalIds }),
            });

            if (response.ok) {
                fetchSavings();
            } else {
                console.error('Failed to update priorities');
            }
        } catch (error) {
            console.error('Error updating priorities:', error);
        }
    };

    const openModal = () => {
        savingsModal.classList.remove('hidden');
    };

    const closeModal = () => {
        savingsModal.classList.add('hidden');
        savingsForm.reset();
    };

    const addSavingsGoal = async (e) => {
        e.preventDefault();
        const formData = new FormData(savingsForm);
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
                fetchSavings();
            } else {
                console.error('Failed to add savings goal');
            }
        } catch (error) {
            console.error('Error adding savings goal:', error);
        }
    };

    addSavingsBtn.addEventListener('click', openModal);
    closeSavingsModal.addEventListener('click', closeModal);
    cancelSavingsBtn.addEventListener('click', closeModal);
    savingsForm.addEventListener('submit', addSavingsGoal);

    fetchSavings();

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'add') {
        openModal();
    }
});
