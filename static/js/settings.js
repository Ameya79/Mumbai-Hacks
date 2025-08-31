document.addEventListener('DOMContentLoaded', function() {
    // Currency preferences
    const currencySelect = document.getElementById('currency');
    if (currencySelect) {
        // Set default to INR ₹ and populate
        currencySelect.innerHTML = `
            <option value="INR">INR (₹)</option>
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
        `;
        fetch('/api/settings/profile')
            .then(r => r.json())
            .then(() => fetch('/api/settings/notifications')) // quick fetch to ensure auth
            .finally(() => {
                // Try to get user preferences for currency
                fetch('/api/auth/user')
                    .then(r => r.json())
                    .then(data => {
                        // backend preferences endpoint not exposing currency yet; default INR
                        currencySelect.value = 'INR';
                    })
                    .catch(() => { currencySelect.value = 'INR'; });
            });

        currencySelect.addEventListener('change', () => {
            const currency = currencySelect.value;
            // Persist in preferences when available; for now store locally
            localStorage.setItem('currency', currency);
            document.cookie = `currency=${currency};path=/;max-age=31536000`;
            alert('Currency preference saved');
        });
    }
    const navLinks = document.querySelectorAll('.settings-nav-link');
    const sections = document.querySelectorAll('.settings-section');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            navLinks.forEach(navLink => navLink.classList.remove('active'));
            this.classList.add('active');

            const targetId = this.getAttribute('href').substring(1);
            sections.forEach(section => {
                if (section.id === targetId) {
                    section.classList.remove('hidden');
                } else {
                    section.classList.add('hidden');
                }
            });
        });
    });


    // Handle password form submission
    const passwordForm = document.querySelector('#security form');
    passwordForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const current_password = document.getElementById('current-password').value;
        const new_password = document.getElementById('new-password').value;
        const confirm_password = document.getElementById('confirm-password').value;

        fetch('/api/settings/password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password, new_password, confirm_password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Password updated successfully');
                passwordForm.reset();
            } else {
                alert(data.message);
            }
        });
    });

    // Fetch and display notification settings
    fetch('/api/settings/notifications')
        .then(response => response.json())
        .then(data => {
            document.querySelector('#notifications input[type="checkbox"]').checked = data.weekly_summary;
            document.querySelectorAll('#notifications input[type="checkbox"]')[1].checked = data.budget_alerts;
            document.querySelectorAll('#notifications input[type="checkbox"]')[2].checked = data.savings_updates;
        });

    // Handle notification form changes
    const notificationsForm = document.querySelector('#notifications');
    notificationsForm.addEventListener('change', function(e) {
        if (e.target.type === 'checkbox') {
            const weekly_summary = document.querySelector('#notifications input[type="checkbox"]').checked;
            const budget_alerts = document.querySelectorAll('#notifications input[type="checkbox"]')[1].checked;
            const savings_updates = document.querySelectorAll('#notifications input[type="checkbox"]')[2].checked;

            fetch('/api/settings/notifications', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weekly_summary, budget_alerts, savings_updates })
            });
        }
    });
});
