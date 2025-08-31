document.addEventListener('DOMContentLoaded', () => {
    const apiUrl = '/api/transactions';
    const tbody = document.getElementById('transactionsBody');

    const fetchTransactions = async () => {
        try {
            const response = await fetch(apiUrl);
            const transactions = await response.json();
            renderTransactions(transactions);
        } catch (error) {
            console.error('Error fetching transactions:', error);
        }
    };

    const renderTransactions = (transactions) => {
        tbody.innerHTML = '';
        transactions.forEach(tx => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${tx.date}</td>
                <td>${tx.description}</td>
                <td>${tx.category}</td>
                <td class="${tx.type === 'income' ? 'text-green-500' : 'text-red-500'}">${tx.type === 'income' ? '+' : '-'}$${tx.amount.toFixed(2)}</td>
                <td>${tx.type}</td>
            `;
            tbody.appendChild(tr);
        });
    };

    document.getElementById('addTransactionBtn').addEventListener('click', () => {
        // For now, we can reuse the modal logic from dashboard.js
        // A better approach would be to have a shared modal component
        const transactionModal = document.getElementById('transactionModal');
        if (transactionModal) {
            transactionModal.classList.remove('hidden');
            transactionModal.querySelector('.bg-white').classList.add('modal-enter');
        } else {
            alert('Add transaction modal not found!');
        }
    });

    fetchTransactions();

    document.addEventListener('transactionAdded', () => {
        fetchTransactions();
    });

    const uploadReceiptBtn = document.getElementById('uploadReceiptBtn');
    const receiptInput = document.createElement('input');
    receiptInput.type = 'file';
    receiptInput.accept = 'image/*';
    receiptInput.style.display = 'none';

    uploadReceiptBtn.addEventListener('click', () => {
        receiptInput.click();
    });

    receiptInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('receipt', file);

        try {
            const response = await fetch('/api/parse-receipt', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            document.getElementById('amount').value = data.amount;
            document.getElementById('category').value = data.category;
            document.getElementById('description').value = data.description;
            document.getElementById('date').value = data.date;

            const transactionModal = document.getElementById('transactionModal');
            transactionModal.classList.remove('hidden');
            transactionModal.querySelector('.bg-white').classList.add('modal-enter');

        } catch (error) {
            console.error('Error parsing receipt:', error);
            alert('Error parsing receipt');
        }
    });

    document.body.appendChild(receiptInput);
});
