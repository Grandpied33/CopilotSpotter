// Initialisation de l'utilisateur
const userId = localStorage.getItem('spotter_userId') || crypto.randomUUID();
if (!localStorage.getItem('spotter_userId')) {
  localStorage.setItem('spotter_userId', userId);
}

// Sélection des éléments DOM
const intro = document.getElementById('intro');
const chat = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');
const fbBtn = document.getElementById('feedback-btn');
const wrapper = document.getElementById('wrapper');
let loaderElem, repInterval;

// Fonction pour formater un programme en HTML lisible
function formatProgram(text) {
  const lines = text.split('\n');
  let html = '', inList = false;
  lines.forEach(line => {
    line = line.trim();
    if (!line) return;
    if (/^─{5,}$/.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += '<hr class="divider">';
    } else if (/^[0-9]+\s*–/.test(line) || /^[0-9]+\./.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h3 class="prog-step">${line}</h3>`;
    } else if (/^[•*-]\s/.test(line)) {
      if (!inList) { html += '<ul class="prog-list">'; inList = true; }
      html += `<li>${line.replace(/^[•*-]\s*/, '')}</li>`;
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<p class="prog-text">${line}</p>`;
    }
  });
  if (inList) html += '</ul>';
  return html;
}

// Fonction pour déclencher l'animation d'intro
function explodeIntro() {
  const text = intro.textContent;
  intro.textContent = '';

  const chars = Array.from(text).map(ch => {
    const s = document.createElement('span');
    s.textContent = ch;
    s.classList.add('letter');
    s.style.transition = 'transform 0.8s ease-out, opacity 0.8s ease-out';
    intro.appendChild(s);
    return s;
  });

  requestAnimationFrame(() => {
    chars.forEach(s => {
      const dx = (Math.random() - 0.5) * 200;
      const dy = (Math.random() - 0.5) * 200;
      const rot = (Math.random() - 0.5) * 720;
      s.style.transform = `translate(${dx}px,${dy}px) rotate(${rot}deg)`;
      s.style.opacity = '0';
    });
  });

  setTimeout(() => {
    intro.style.display = 'none';
  }, 800);
}

// Ajustement dynamique de la hauteur de l'input
const textarea = document.querySelector('.input-area textarea');
textarea.addEventListener('input', () => {
  textarea.style.height = 'auto';
  textarea.style.height = `${textarea.scrollHeight}px`;
});

// Fonction pour ajouter une bulle de message
function addBubble(text, who) {
  if (intro && intro.style.display !== 'none') {
    explodeIntro();
  }

  const b = document.createElement('div');
  b.className = `bubble ${who}`;

  if (who === 'assistant' && (/^[0-9].*|^─{5,}|^[•*-]/m).test(text)) {
    b.innerHTML = formatProgram(text);

    fbBtn.style.display = 'inline-block';
    fbBtn.onclick = () => {
      textarea.value = 'feedback: ';
      textarea.focus();
    };
  } else {
    b.textContent = text;
  }

  chat.appendChild(b);
  chat.scrollTop = chat.scrollHeight;
}


textarea.addEventListener('focus', () => {
  setTimeout(() => {
    textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 200);
});


// Fonction pour extraire les exercices du texte
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

// Fonction principale pour envoyer une requête au backend
async function ask() {
  const q = promptEl.value.trim();
  if (!q) return;
  promptEl.value = '';
  promptEl.style.height = '2rem';
  sendBtn.disabled = true;
  fbBtn.style.display = 'none';
  wrapper.classList.add('pump');
  wrapper.addEventListener('animationend', () => wrapper.classList.remove('pump'), { once: true });
  addBubble(q, 'user');

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
  } catch (error) {
    clearInterval(repInterval);
    loaderElem.remove();
    console.error('Erreur de connexion :', error);
    addBubble('⚠️ Connexion échouée', 'assistant');
  } finally {
    sendBtn.disabled = false;
    promptEl.focus();
  }
}

// Événements pour envoyer un message
sendBtn.addEventListener('click', ask);
promptEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    ask();
  }
});

// Gestion de la modal d'introduction
document.addEventListener('DOMContentLoaded', () => {
  const introModal = document.getElementById('intro-modal');
  const closeIntroModalBtn = document.getElementById('close-intro-modal');

  const hasSeenIntro = localStorage.getItem('hasSeenIntro');
  if (!hasSeenIntro) {
    introModal.classList.remove('hidden');
  }

  closeIntroModalBtn.addEventListener('click', () => {
    introModal.classList.add('hidden');
    localStorage.setItem('hasSeenIntro', 'true');
  });
});

// Gestion de la modal de bug report
document.addEventListener('DOMContentLoaded', () => {
  const reportBugBtn = document.getElementById('report-bug-btn');
  const bugModal = document.getElementById('bug-modal');
  const closeBugModalBtn = document.getElementById('close-bug-modal');
  const generateMailtoBtn = document.getElementById('generate-mailto');
  const bugComment = document.getElementById('bug-comment');

  reportBugBtn.addEventListener('click', () => {
    bugModal.classList.remove('hidden');
  });

  closeBugModalBtn.addEventListener('click', () => {
    bugModal.classList.add('hidden');
  });

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