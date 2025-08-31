document.addEventListener('DOMContentLoaded', async function() {
    const periodSelector = document.getElementById('periodSelector');
    const dateRange = document.getElementById('dateRange');
    const incomeEmpty = document.getElementById('incomeExpensesEmpty');
    const categoryEmpty = document.getElementById('categoryPieEmpty');

    periodSelector.addEventListener('change', function() {
        if (this.value === 'custom') {
            dateRange.classList.remove('hidden');
        } else {
            dateRange.classList.add('hidden');
        }
    });

    // Chart.js initialization
    try {
        const resp = await fetch('/api/reports/data?period=this_month');
        if (!resp.ok) throw new Error('Failed to load');
        const data = await resp.json();
        const inc = data.charts.income_expenses;
        const cat = data.charts.categories;

        const incomeExpensesCtx = document.getElementById('incomeExpensesChart').getContext('2d');
        const hasTrend = inc.income.some(v => v > 0) || inc.expenses.some(v => v > 0);
        if (!hasTrend) {
            incomeExpensesCtx.canvas.style.display = 'none';
            if (incomeEmpty) incomeEmpty.classList.remove('hidden');
        } else {
            new Chart(incomeExpensesCtx, {
                type: 'bar',
                data: {
                    labels: inc.labels,
                    datasets: [
                        { label: 'Income', data: inc.income, backgroundColor: '#10b981' },
                        { label: 'Expenses', data: inc.expenses, backgroundColor: '#ef4444' }
                    ]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
        }

        const categoryPieCtx = document.getElementById('categoryPieChart').getContext('2d');
        const hasCats = cat.data && cat.data.some(v => v > 0);
        if (!hasCats) {
            categoryPieCtx.canvas.style.display = 'none';
            if (categoryEmpty) categoryEmpty.classList.remove('hidden');
        } else {
            new Chart(categoryPieCtx, {
                type: 'doughnut',
                data: {
                    labels: cat.labels,
                    datasets: [{ data: cat.data, backgroundColor: ['#4f46e5', '#10b981', '#ef4444', '#f59e0b', '#6366f1'] }]
                },
                options: { responsive: true }
            });
        }
    } catch (e) {
        if (incomeEmpty) incomeEmpty.classList.remove('hidden');
        if (categoryEmpty) categoryEmpty.classList.remove('hidden');
    }
});
