const userId = localStorage.getItem('spotter_userId') || crypto.randomUUID();
if (!localStorage.getItem('spotter_userId')) {
  localStorage.setItem('spotter_userId', userId);
}

const intro    = document.getElementById('intro');
const chat     = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn  = document.getElementById('send');
const fbBtn    = document.getElementById('feedback-btn');
const wrapper  = document.getElementById('wrapper');
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
  const text  = intro.textContent;
  intro.textContent = '';

  // 1) On crée un span par caractère
  const chars = Array.from(text).map(ch => {
    const s = document.createElement('span');
    s.textContent = ch;
    s.classList.add('letter');              // pour cibler en CSS
    // on prépare la transition
    s.style.transition = 'transform 0.8s ease-out, opacity 0.8s ease-out';
    intro.appendChild(s);
    return s;
  });

  // 2) on attends le prochain repaint pour lancer l’anim
  requestAnimationFrame(() => {
    chars.forEach(s => {
      const dx  = (Math.random() - 0.5) * 200;  // déplacement X aléatoire
      const dy  = (Math.random() - 0.5) * 200;  // déplacement Y aléatoire
      const rot = (Math.random() - 0.5) * 720;  // rotation aléatoire
      s.style.transform = `translate(${dx}px,${dy}px) rotate(${rot}deg)`;
      s.style.opacity   = '0';
    });
  });

  // 3) après la transition, on masque le container
  setTimeout(() => {
    intro.style.display = 'none';
  }, 800);
}
const textarea = document.querySelector('.input-area textarea');

textarea.addEventListener('input', () => {
  textarea.style.height = 'auto'; // Réinitialise la hauteur
  textarea.style.height = `${textarea.scrollHeight}px`; // Ajuste à la hauteur du contenu
});

// Fonction pour ajouter une bulle de message
function addBubble(text, who) {
  const intro = document.getElementById('intro');
  if (intro && intro.style.display !== 'none') {
    explodeIntro(); // Déclenche l'explosion si l'intro est encore visible
  }

  const chat = document.querySelector('.chat-container');
  const b = document.createElement('div');
  b.className = `bubble ${who}`;

  // Formatage spécial pour les réponses structurées
  if (who === 'assistant' && (/^[0-9].*|^─{5,}|^[•*-]/m).test(text)) {
    b.innerHTML = formatProgram(text);

    // Afficher le bouton de feedback
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
  chat.scrollTop = chat.scrollHeight; // Scroll automatique vers le bas
}

async function ask() {
  const q = promptEl.value.trim();
  if (!q) return;
  promptEl.value = '';
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