// Récupération / initialisation de l'historique
let history = JSON.parse(localStorage.getItem('spotter_history') || '{}');
function saveHistory() {
  localStorage.setItem('spotter_history', JSON.stringify(history));
}

const intro    = document.getElementById('intro');
const chat     = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn  = document.getElementById('send');
const wrapper  = document.getElementById('wrapper');
let loaderElem, repInterval;

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
  requestAnimationFrame(() =>
    chars.forEach(s => {
      const dx  = (Math.random() - 0.5) * 200;
      const dy  = (Math.random() - 0.5) * 200;
      const rot = (Math.random() - 0.5) * 720;
      s.style.transform = `translate(${dx}px,${dy}px) rotate(${rot}deg)`;
      s.style.opacity   = '0';
    })
  );
  setTimeout(() => intro.style.display = 'none', 800);
}

function pumpMuscle() {
  wrapper.classList.add('pump');
  wrapper.addEventListener('animationend',
    () => wrapper.classList.remove('pump'),
    { once: true }
  );
}

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

function addBubble(text, who) {
  if (intro && intro.style.display !== 'none') explodeIntro();
  const b = document.createElement('div');
  b.className = `bubble ${who}`;
  b.textContent = text;
  chat.appendChild(b);
  chat.scrollTop = chat.scrollHeight;
}

async function ask() {
  const q = promptEl.value.trim();
  if (!q) return;

  // Préparation du contexte mémoire
  const memText = Object.entries(history)
    .map(([exo, wt]) => `- ${exo} : ${wt} kg`)
    .join('\n') || 'Aucune donnée historique.';

  // Easter-eggs
  if (q.toLowerCase() === 'qui est ton créateur ?') {
    promptEl.value = '';
    addBubble(
      '🤖 Mon créateur, c’est Hugo, développeur web passionné et coach musculation amateur !',
      'assistant'
    );
    return;
  }
  if (q.toLowerCase() === 'quel est mon métier ?') {
    promptEl.value = '';
    addBubble(
      '💼 Toi, c’est Hugo – développeur web qui code des apps et soulève de la fonte !',
      'assistant'
    );
    return;
  }

  promptEl.value = '';
  sendBtn.disabled = true;
  pumpMuscle();
  addBubble(q, 'user');
  showRepLoader();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_input: q,
        memory: memText
      })
    });
    const data = await res.json();
    hideRepLoader();

    const ai = res.ok && data.assistant_response
      ? data.assistant_response
      : `⚠️ ${data.error || res.status}`;

    addBubble(ai, 'assistant');

    // Mise à jour de l'historique si l'IA renvoie un JSON contenant "weights"
    try {
      const parsed = JSON.parse(ai);
      const weights = parsed.weights;
      if (weights && typeof weights === 'object') {
        Object.assign(history, weights);
        saveHistory();
      }
    } catch {}

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
