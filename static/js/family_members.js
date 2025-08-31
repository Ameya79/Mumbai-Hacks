document.addEventListener('DOMContentLoaded', () => {
    const apiUrl = '/api/family_members';
    const memberList = document.getElementById('memberList');
    const addMemberBtn = document.getElementById('addMemberBtn');

    const fetchMembers = async () => {
        try {
            const response = await fetch(apiUrl);
            const members = await response.json();
            renderMembers(members);
        } catch (error) {
            console.error('Error fetching family members:', error);
        }
    };

    const renderMembers = (members) => {
        memberList.innerHTML = '';
        members.forEach(member => {
            const memberCard = document.createElement('div');
            memberCard.className = 'bg-white p-6 rounded-xl shadow-sm';
            memberCard.innerHTML = `
                <div class="flex items-center space-x-4">
                    <img src="https://ui-avatars.com/api/?name=${member.name.replace(' ', '+')}&background=random" class="w-16 h-16 rounded-full" alt="${member.name}">
                    <div>
                        <h3 class="text-xl font-bold">${member.name}</h3>
                        <p class="text-sm text-gray-500">${member.email}</p>
                    </div>
                </div>
            `;
            memberList.appendChild(memberCard);
        });
    };

    if (addMemberBtn) {
        addMemberBtn.addEventListener('click', async () => {
            const name = prompt('Enter member name');
            const email = prompt('Enter member email');
            if (!name || !email) return;
            // In this simplified model, creating a member equals creating a user
            try {
                const res = await fetch('/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password: (Math.random().toString(36).slice(2,8) + 'A1!'), suppress_login: true })
                });
                // Do not auto-login new member; just refresh list from server which returns all users
                await fetchMembers();
                alert('Member added. Share credentials with them separately.');
            } catch (e) {
                alert('Failed to add member');
            }
        });
    }

    fetchMembers();
});
