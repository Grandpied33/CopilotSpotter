const userId = localStorage.getItem('spotter_userId') || crypto.randomUUID();
if (!localStorage.getItem('spotter_userId')) {
  localStorage.setItem('spotter_userId', userId);
}

const intro = document.getElementById('intro');
const chat = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');
const fbBtn = document.getElementById('feedback-btn');
const wrapper = document.getElementById('wrapper');
let loaderElem, repInterval;

// Format program into readable HTML
function formatProgram(text) {
  const lines = text.split('\n');
  let html = '', inList = false;
  lines.forEach(line => {
    line = line.trim();
    if (!line) return;
    if (/^─{5,}$/.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += '<hr class="divider">';
    }
    else if (/^[0-9]+\s*–/.test(line) || /^[0-9]+\./.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h3 class="prog-step">${line}</h3>`;
    }
    else if (/^[•*-]\s/.test(line)) {
      if (!inList) { html += '<ul class="prog-list">'; inList = true; }
      html += `<li>${line.replace(/^[•*-]\s*/, '')}</li>`;
    }
    else {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<p class="prog-text">${line}</p>`;
    }
  });
  if (inList) html += '</ul>';
  return html;
}

function explodeIntro() {
  const intro = document.getElementById('intro');
  const text = intro.textContent;
  intro.textContent = '';

  // Create a span for each character
  const chars = Array.from(text).map(ch => {
    const s = document.createElement('span');
    s.textContent = ch;
    s.classList.add('letter'); // For CSS targeting
    s.style.transition = 'transform 0.8s ease-out, opacity 0.8s ease-out';
    intro.appendChild(s);
    return s;
  });

  // Trigger animation
  requestAnimationFrame(() => {
    chars.forEach(s => {
      const dx = (Math.random() - 0.5) * 200; // Random X displacement
      const dy = (Math.random() - 0.5) * 200; // Random Y displacement
      const rot = (Math.random() - 0.5) * 720; // Random rotation
      s.style.transform = `translate(${dx}px,${dy}px) rotate(${rot}deg)`;
      s.style.opacity = '0';
    });
  });

  // Hide the container after the animation
  setTimeout(() => {
    intro.style.display = 'none';
  }, 800);
}

const textarea = document.querySelector('.input-area textarea');

textarea.addEventListener('input', () => {
  textarea.style.height = 'auto'; // Reset height
  textarea.style.height = `${textarea.scrollHeight}px`; // Adjust to content
});

// Function to add a message bubble
function addBubble(text, who) {
  const intro = document.getElementById('intro');
  if (intro && intro.style.display !== 'none') {
    explodeIntro(); // Trigger intro animation if visible
  }

  const chat = document.querySelector('.chat-container');
  const b = document.createElement('div');
  b.className = `bubble ${who}`;

  // Special formatting for structured responses
  if (who === 'assistant' && (/^[0-9].*|^─{5,}|^[•*-]/m).test(text)) {
    b.innerHTML = formatProgram(text);

    // Show feedback button
    const fbBtn = document.getElementById('feedback-btn');
    fbBtn.style.display = 'inline-block';
    fbBtn.onclick = () => {
      textarea.value = 'feedback: ';
      textarea.focus();
    };
  } else {
    b.textContent = text;
  }

  chat.appendChild(b);
  chat.scrollTop = chat.scrollHeight; // Auto-scroll to the bottom
}

// Function to extract exercises from assistant's text
function extractExercises(text) {
  const exerciseRegex = /Exercice \d+ : (.+?)\nDescription : (.+?)\nSéries : (\d+)\nRépétitions : (.+?)\nCharge estimée : (.+?)\nRepos : (.+?)(?=\n|$)/g;
  const exercises = [];
  let match;

  while ((match = exerciseRegex.exec(text)) !== null) {
    exercises.push({
      name: match[1],
      description: match[2],
      series: match[3],
      repetitions: match[4],
      charge: match[5],
      rest: match[6],
    });
  }

  return exercises;
}

document.addEventListener('DOMContentLoaded', () => {
  const reportBugBtn = document.getElementById('report-bug-btn');
  const bugModal = document.getElementById('bug-modal');
  const closeBugModalBtn = document.getElementById('close-bug-modal');
  const generateMailtoBtn = document.getElementById('generate-mailto');
  const bugComment = document.getElementById('bug-comment');

  // Open the modal
  reportBugBtn.addEventListener('click', () => {
    bugModal.classList.remove('hidden');
  });

  // Close the modal
  closeBugModalBtn.addEventListener('click', () => {
    bugModal.classList.add('hidden');
  });

  // Generate mailto link
  generateMailtoBtn.addEventListener('click', () => {
    const comment = bugComment.value.trim();
    if (!comment) {
      alert('Veuillez ajouter un commentaire avant d’envoyer.');
      return;
    }

    const subject = encodeURIComponent('Bug Report - SpotterCopilot');
    const body = encodeURIComponent(`Commentaire :\n${comment}`);
    const mailtoLink = `mailto:hugo@monfouga.org?subject=${subject}&body=${body}`;

    window.location.href = mailtoLink;

    bugModal.classList.add('hidden');
    bugComment.value = '';
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const introModal = document.getElementById('intro-modal');
  const closeIntroModalBtn = document.getElementById('close-intro-modal');

  // Check if the user has already seen the modal
  const hasSeenIntro = localStorage.getItem('hasSeenIntro');
  if (!hasSeenIntro) {
    introModal.classList.remove('hidden');
  }

  // Close the modal and save the state
  closeIntroModalBtn.addEventListener('click', () => {
    introModal.classList.add('hidden');
    localStorage.setItem('hasSeenIntro', 'true');
  });
});

async function ask() {
  const q = promptEl.value.trim();
  if (!q) return;
  promptEl.value = '';
  promptEl.style.height = '2rem'; // Réinitialise la hauteur de l'input
  sendBtn.disabled = true;
  fbBtn.style.display = 'none';
  wrapper.classList.add('pump');
  wrapper.addEventListener('animationend', () => wrapper.classList.remove('pump'), { once: true });
  addBubble(q, 'user');

  // Loader
  loaderElem = document.createElement('div');
  loaderElem.className = 'rep-loader';
  loaderElem.innerHTML = `<span id="rep-count">0</span> reps`;
  chat.appendChild(loaderElem);
  chat.scrollTop = chat.scrollHeight;
  let count = 0;
  repInterval = setInterval(() => {
    count = (count % 10) + 1;
    document.getElementById('rep-count').textContent = count;
  }, 200);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': userId
      },
      body: JSON.stringify({ user_input: q })
    });
    const text = await res.text();
    clearInterval(repInterval);
    loaderElem.remove();
    if (!res.ok) {
      addBubble(`⚠️ HTTP ${res.status} : ${text}`, 'assistant');
    } else {
      addBubble(text, 'assistant');
    }
  } catch {
    clearInterval(repInterval);
    loaderElem.remove();
    addBubble('⚠️ Connexion échouée', 'assistant');
  } finally {
    sendBtn.disabled = false;
    promptEl.focus();
  }
}

sendBtn.addEventListener('click', ask);
promptEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault(); ask();
  }
});