// Récupération / initialisation de l’historique par utilisateur
const userId = localStorage.getItem('spotter_userId') || crypto.randomUUID();
if (!localStorage.getItem('spotter_userId')) {
  localStorage.setItem('spotter_userId', userId);
}

const intro    = document.getElementById('intro');
const chat     = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn  = document.getElementById('send');
const wrapper  = document.getElementById('wrapper');
let loaderElem, repInterval;

// Explosion de l’intro (une seule fois)
function explodeIntro() {
  const text = intro.textContent;
  intro.textContent = '';
  const chars = Array.from(text).map(ch => {
    const s = document.createElement('span');
    s.textContent = ch;
    s.style.transition = 'transform 0.8s ease-out, opacity 0.8s ease-out';
    intro.appendChild(s);
    return s;
  });
  requestAnimationFrame(() => {
    chars.forEach(s => {
      const dx  = (Math.random() - 0.5) * 200;
      const dy  = (Math.random() - 0.5) * 200;
      const rot = (Math.random() - 0.5) * 720;
      s.style.transform = `translate(${dx}px,${dy}px) rotate(${rot}deg)`;
      s.style.opacity   = '0';
    });
  });
  setTimeout(() => intro.style.display = 'none', 800);
}

// Effet « pump » sur l’input
function pumpMuscle() {
  wrapper.classList.add('pump');
  wrapper.addEventListener('animationend',
    () => wrapper.classList.remove('pump'),
    { once: true }
  );
}

// Loader animé (compte de reps)
function showRepLoader() {
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
}
function hideRepLoader() {
  clearInterval(repInterval);
  if (loaderElem) loaderElem.remove();
}

// Transforme un texte de programme en HTML structuré
function formatProgram(text) {
  const sections = text.split(/\n─{3,}\n/);
  let html = '<div class="program">';
  sections.forEach(section => {
    const lines = section.split('\n').map(l => l.trim()).filter(l => l);
    if (!lines.length) return;
    html += '<div class="prog-section">';
    let inList = false;
    lines.forEach(line => {
      if (/^[0-9]+\.\s/.test(line)) {
        if (inList) { html += '</ul>'; inList = false; }
        html += `<h3 class="prog-step">${line}</h3>`;
      }
      else if (/^[•\-\–]\s/.test(line)) {
        if (!inList) {
          html += '<ul class="prog-list">';
          inList = true;
        }
        html += `<li>${line.replace(/^[•\-\–]\s*/, '')}</li>`;
      }
      else {
        if (inList) { html += '</ul>'; inList = false; }
        html += `<p class="prog-text">${line}</p>`;
      }
    });
    if (inList) html += '</ul>';
    html += '</div>';
  });
  html += '</div>';
  return html;
}

// Ajoute une bulle dans le chat
function addBubble(text, who) {
  if (intro && intro.style.display !== 'none') explodeIntro();
  const b = document.createElement('div');
  b.className = `bubble ${who}`;
  // si c’est l’assistant et qu’on détecte un programme, on injecte HTML
  if (who === 'assistant' && (/^[0-9]|\n─{3,}|\n[•\-\–]\s/.test(text))) {
    b.innerHTML = formatProgram(text);
  } else {
    b.textContent = text;
  }
  chat.appendChild(b);
  chat.scrollTop = chat.scrollHeight;
}

async function ask() {
  const q = promptEl.value.trim();
  if (!q) return;
  promptEl.value = '';
  sendBtn.disabled = true;
  pumpMuscle();
  addBubble(q, 'user');
  showRepLoader();

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
    hideRepLoader();
    if (!res.ok) {
      addBubble(`⚠️ HTTP ${res.status} : ${text}`, 'assistant');
    } else {
      addBubble(text, 'assistant');
    }
  } catch {
    hideRepLoader();
    addBubble('⚠️ Connexion échouée', 'assistant');
  } finally {
    sendBtn.disabled = false;
    promptEl.focus();
  }
}

sendBtn.addEventListener('click', ask);
promptEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    ask();
  }
});
