
// --- 1. USER IDENTIFICATION ---
const currentUserEmail = localStorage.getItem("user_email") || "guest_user";
const user = localStorage.getItem("user_name");
const STORAGE_KEY = `study_notes_${currentUserEmail}`;

document.getElementById('user-welcome').innerText = `Library for: ${user}`;

// --- 2. STARTUP ---
document.addEventListener('DOMContentLoaded', () => {
  renderNotes();
});

// --- 3. CORE LOGIC ---
function getNotes() {
  const notes = localStorage.getItem(STORAGE_KEY);
  return notes ? JSON.parse(notes) : [];
}

function saveNote() {
  const title = document.getElementById('noteTitle').value;
  const subject = document.getElementById('noteSubject').value;
  const fileInput = document.getElementById('fileInput');

  if (!title || fileInput.files.length === 0) {
    alert("Please fill in a title and select a file.");
    return;
  }

  const file = fileInput.files[0];

  if (file.size > 3000000) {
    alert("File is too large! Please keep it under 3MB.");
    return;
  }

  const reader = new FileReader();
  reader.readAsDataURL(file);

  reader.onload = function () {
    const newNote = {
      id: Date.now(),
      title: title,
      subject: subject,
      fileName: file.name,
      fileData: reader.result,
      date: new Date().toLocaleDateString()
    };

    const currentNotes = getNotes();
    currentNotes.push(newNote);

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentNotes));
      closeUploadModal();
      renderNotes();
    } catch (e) {
      alert("Storage full! Delete some old notes to make space.");
    }
  };
}

function renderNotes(filterSubject = 'all') {
  const notesGrid = document.getElementById('notesGrid');
  const notes = getNotes();

  notesGrid.innerHTML = '';

  if (notes.length === 0) {
    notesGrid.innerHTML = `
                    <div style="grid-column: 1/-1; text-align:center; color:#64748b; padding:40px;">
                        <i class="fas fa-folder-open" style="font-size:3rem; margin-bottom:15px; opacity:0.5;"></i>
                        <p>No notes found. Upload your first PDF!</p>
                    </div>`;
    return;
  }

  notes.forEach(note => {
    if (filterSubject !== 'all' && note.subject !== filterSubject) return;

    const card = document.createElement('div');
    card.className = 'note-card';

    card.innerHTML = `
  <div class="card-header">
    <div class="card-icon"><i class="fas fa-file-pdf"></i></div>
    <div class="card-info">
      <h3>${note.title}</h3>
      <span class="subject-tag">${note.subject}</span>
    </div>
  </div>
  <div class="card-meta">
    <span class="date-text">${note.date}</span>
    <div>
      <button onclick="viewNote('${note.id}')" class="action-btn" title="View">
        <i class="fas fa-eye"></i>
      </button>
      <button onclick="deleteNote('${note.id}')" class="action-btn delete" title="Delete">
        <i class="fas fa-trash"></i>
      </button>
    </div>
  </div>
  `;
    notesGrid.appendChild(card);
  });
}

function viewNote(id) {
  const notes = getNotes();
  const note = notes.find(n => n.id == id);
  if (note) {
    const win = window.open();
    win.document.write(
      `<title>${note.title}</title>
  <body style="margin:0;"><iframe src="${note.fileData}" style="border:0; width:100%; height:100vh;"></iframe></body>`
    );
  }
}

function deleteNote(id) {
  if (confirm("Delete this note?")) {
    let notes = getNotes();
    notes = notes.filter(n => n.id != id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
    renderNotes();
  }
}

// --- 4. UI HELPERS ---
function filterNotes(subject) {
  document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  renderNotes(subject);
}

function openUploadModal() {
  document.getElementById('uploadModal').style.display = 'flex';
}

function closeUploadModal() {
  document.getElementById('uploadModal').style.display = 'none';
  document.getElementById('noteTitle').value = '';
  document.getElementById('fileInput').value = '';
}



function updateFileName() {
  const input = document.getElementById('fileInput');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const labelSpan = document.querySelector('.custom-file-upload span');

  if (input.files && input.files.length > 0) {
    // File Selected
    labelSpan.innerText = "File Selected:";
    fileNameDisplay.innerText = input.files[0].name;
  } else {
    // No File
    labelSpan.innerText = "Click to choose a PDF";
    fileNameDisplay.innerText = "";
  }
}