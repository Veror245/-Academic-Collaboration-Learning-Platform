/**
 * StudioControl - Admin Dashboard Logic
 * Features: Stat Counter, Tag Management, Sidebar Sync, and Row Actions
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. STAT COUNTER ANIMATION
    // Makes the numbers "roll up" when the dashboard loads
    const animateCounters = () => {
        const counters = document.querySelectorAll('.count');
        counters.forEach(counter => {
            const target = +counter.innerText.replace(/\D/g, '');
            const count = 0;
            const speed = 200; 
            
            const updateCount = () => {
                const current = +counter.innerText;
                const increment = target / speed;

                if (current < target) {
                    counter.innerText = Math.ceil(current + increment);
                    setTimeout(updateCount, 1);
                } else {
                    counter.innerText = target.toLocaleString();
                }
            };
            updateCount();
        });
    };
    animateCounters();

    // 2. SIDEBAR NAVIGATION
    const navLinks = document.querySelectorAll('.nav-links li');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(li => li.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 3. TAG MANAGEMENT (For Banned Words/Filters)
    const tagContainer = document.querySelector('.tag-container');
    const inlineInput = document.querySelector('.inline-input');

    if (inlineInput) {
        inlineInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && inlineInput.value.trim() !== "") {
                const newTag = document.createElement('span');
                newTag.className = 'word-tag';
                newTag.innerHTML = `
                    ${inlineInput.value}
                    <button onclick="this.parentElement.remove()">×</button>
                `;
                tagContainer.insertBefore(newTag, inlineInput);
                inlineInput.value = "";
            }
        });
    }

    // 4. TABLE ACTIONS (Approve / Reject / Delete)
    // Using Event Delegation for performance
    document.addEventListener('click', (e) => {
        const target = e.target;

        // Approve Action
        if (target.classList.contains('btn-approve')) {
            const row = target.closest('tr');
            const statusCell = row.querySelector('.status-pending');
            if (statusCell) {
                statusCell.innerText = 'Approved';
                statusCell.className = 'status-approved';
                target.style.display = 'none'; // Hide approve button after use
            }
        }

        // Reject/Delete Action (with Fade Out)
        if (target.classList.contains('btn-reject') || target.classList.contains('btn-delete')) {
            const elementToRemove = target.closest('tr') || target.closest('.msg-item') || target.closest('.room-card');
            
            if (confirm("Are you sure you want to proceed with this action?")) {
                elementToRemove.style.transition = 'all 0.4s ease';
                elementToRemove.style.opacity = '0';
                elementToRemove.style.transform = 'translateX(20px)';
                
                setTimeout(() => {
                    elementToRemove.remove();
                }, 400);
            }
        }
        
        // View Action
        if (target.classList.contains('btn-view')) {
            const itemName = target.closest('tr')?.cells[0].innerText || "Item";
            alert(`Opening details for: ${itemName}`);
        }
    });

    // 5. SEARCH BAR LOGIC
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
});