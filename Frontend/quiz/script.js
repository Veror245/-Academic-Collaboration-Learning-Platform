/**
 * Quiz Builder Functional Logic 
 * Tailored for the AI Quiz Generator | StudioControl HTML
 */

document.addEventListener('DOMContentLoaded', () => {
    // Select elements based on your HTML classes
    const questionList = document.querySelector('.question-list');
    const addBtn = document.querySelector('.btn-outline');
    const saveBtn = document.querySelector('.btn-save');
    const generateBtn = document.querySelector('.btn-generate');
    const headerCountText = document.querySelector('.header-info p');

    /**
     * Helper Function: Update Question Count
     * Syncs the "X Questions Generated" text in the header
     */
    const updateCount = () => {
        const count = document.querySelectorAll('.question-card').length;
        headerCountText.innerText = `${count} Question${count !== 1 ? 's' : ''} Total`;
    };

    /**
     * 1. ADD QUESTION MANUALLY
     * Injects a new MCQ card into the workspace
     */
    addBtn.addEventListener('click', () => {
        const questionId = Date.now(); // Unique ID for radio button groups
        const newCard = document.createElement('div');
        newCard.className = 'question-card';
        
        // Setup initial animation state
        newCard.style.opacity = '0';
        newCard.style.transform = 'translateY(20px)';
        
        newCard.innerHTML = `
            <div class="card-tag">MCQ</div>
            <div class="card-content">
                <input type="text" class="q-title" placeholder="Type your manual question here...">
                <div class="options-grid">
                    <div class="option"><input type="radio" name="q_${questionId}"> <input type="text" placeholder="Option A"></div>
                    <div class="option"><input type="radio" name="q_${questionId}"> <input type="text" placeholder="Option B"></div>
                    <div class="option"><input type="radio" name="q_${questionId}"> <input type="text" placeholder="Option C"></div>
                    <div class="option"><input type="radio" name="q_${questionId}"> <input type="text" placeholder="Option D"></div>
                </div>
            </div>
            <button class="btn-del">&times;</button>
        `;

        questionList.appendChild(newCard);
        updateCount();

        // Smooth Fade-in
        requestAnimationFrame(() => {
            newCard.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            newCard.style.opacity = '1';
            newCard.style.transform = 'translateY(0)';
        });
    });

    /**
     * 2. DELETE QUESTION
     * Uses Event Delegation to handle existing and new cards
     */
    questionList.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-del')) {
            const card = e.target.closest('.question-card');
            
            // Exit Animation
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                card.remove();
                updateCount();
            }, 300);
        }
    });

    /**
     * 3. GENERATE QUIZ (Sidebar Button)
     * Simulates AI processing
     */
    generateBtn.addEventListener('click', () => {
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = "Processing AI... 🧠";
        generateBtn.disabled = true;
        generateBtn.style.opacity = "0.7";

        // Simulate 1.5s delay
        setTimeout(() => {
            alert("AI has finished analyzing Physics_Notes_Final.pdf!");
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
            generateBtn.style.opacity = "1";
        }, 1500);
    });

    /**
     * 4. SAVE & PUBLISH
     * Scrapes data from all cards for export
     */
    saveBtn.addEventListener('click', () => {
        const allQuestions = [];
        const cards = document.querySelectorAll('.question-card');

        cards.forEach(card => {
            const questionTitle = card.querySelector('.q-title').value;
            const type = card.querySelector('.card-tag').innerText;
            
            let data = { type, questionTitle };

            if (type === 'MCQ') {
                const options = [];
                card.querySelectorAll('.option input[type="text"]').forEach(input => {
                    options.push(input.value);
                });
                data.options = options;
            } else {
                data.answerKey = card.querySelector('textarea')?.value || "";
            }

            allQuestions.push(data);
        });

        console.log("Final Quiz Export:", allQuestions);
        alert(`Quiz saved successfully with ${allQuestions.length} questions! Check console (F12) for JSON.`);
    });
});