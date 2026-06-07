// RAG landing page — calls /api/query and renders an answer card with images,
// source chunks, related artifacts, and follow-up suggestions.

const askForm    = document.getElementById('askForm');
const askInput   = document.getElementById('askInput');
const answerSec  = document.getElementById('answerSection');
const answerLoader = document.getElementById('answerLoader');
const answerWrap = document.getElementById('answerWrap');
const answerCard = document.getElementById('answerCard');
const sourcesBlock = document.getElementById('sourcesBlock');
const sourcesGrid  = document.getElementById('sourcesGrid');
const relatedBlock = document.getElementById('relatedBlock');
const relatedGrid  = document.getElementById('relatedGrid');
const followupsBlock = document.getElementById('followupsBlock');
const followupsRow = document.getElementById('followupsRow');
const historySec  = document.getElementById('historySection');
const historyList = document.getElementById('historyList');
const suggestionsBox = document.getElementById('suggestions');
const detailModal = document.getElementById('detailModal');
const detailBody  = document.getElementById('detailBody');
const imageModal  = document.getElementById('image-modal');
const modalImg    = document.getElementById('modal-img');

const HISTORY_KEY = 'rag_history_v1';
let HISTORY = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');

const MUSEUM_NAMES = {};

function escapeHtml(s) {
  return (s || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

async function getJson(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return r.json();
}

function bcDate(yMin, yMax) {
  if (yMin == null) return '';
  const fmt = y => y < 0 ? `${-y} ق.م` : `${y} م`;
  if (yMin === yMax) return fmt(yMin);
  return `${fmt(yMin)} – ${fmt(yMax)}`;
}

function renderSuggestions(items) {
  suggestionsBox.innerHTML = items.map(s =>
    `<button class="suggestion-pill" data-q="${escapeHtml(s.q)}">
       <span style="margin-left:6px">${s.icon || '✦'}</span>${escapeHtml(s.q)}
     </button>`).join('');
  suggestionsBox.querySelectorAll('.suggestion-pill').forEach(b => {
    b.addEventListener('click', () => askQuery(b.dataset.q));
  });
}

function renderHistory() {
  if (!HISTORY.length) { historySec.hidden = true; return; }
  historySec.hidden = false;
  historyList.innerHTML = HISTORY.slice(0, 8).map(q =>
    `<div class="history-item">${escapeHtml(q)}</div>`).join('');
  historyList.querySelectorAll('.history-item').forEach((el, i) =>
    el.addEventListener('click', () => askQuery(HISTORY[i])));
}

function pushHistory(q) {
  HISTORY = [q, ...HISTORY.filter(x => x !== q)].slice(0, 30);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(HISTORY));
  renderHistory();
}

function buildAnswerCard(res) {
  const a = res.primary_artifact;
  if (!a) {
    const lowConf = res.low_confidence;
    return `<div class="answer-card no-image${lowConf ? ' no-match' : ''}">
      <div class="ac-body">
        ${lowConf ? '<div class="no-match-icon">📭</div>' : ''}
        <div class="ac-answer">
          <span class="answer-mode-tag ${lowConf ? 'no-match-tag' : res.mode}">${
            lowConf ? '🔍 خارج نطاق القاعدة'
            : (res.mode === 'generative' ? '✨ مولّدة' : '⚡ مباشر')
          }</span>
          ${escapeHtml(res.answer)}
        </div>
      </div>
    </div>`;
  }
  const isMuseum = a.kind === 'museum' || a.kind === 'hall';
  const images = a.images || [];
  const primary = images[0];
  const otherImgs = images.slice(1, 5);

  // Pull museum + hall info for non-museum artifacts
  let museumLine = '';
  if (a.current_location?.museum_ar || a.current_location?.museum_en) {
    const m = a.current_location.museum_ar || a.current_location.museum_en;
    const c = a.current_location.city_ar || a.current_location.city_en;
    museumLine = c ? `${m} — ${c}` : m;
  }
  const hall = a.current_location?.hall_ar || a.current_location?.hall_en || '';
  const period = a.period?.ar || a.period?.en || '';
  const yrange = bcDate(a.period?.year_min, a.period?.year_max);
  const dynasty = a.dynasty?.ar || a.dynasty?.en || '';
  const materials = (a.material || []).join('، ');

  // Image side
  let imageSide = '';
  if (primary) {
    imageSide = `
      <div class="ac-image" id="acHeroImg" style="background-image:url('/images/${escapeHtml(primary.filename)}')">
        ${otherImgs.length ? `<div class="ac-image-thumbs">
          ${[primary, ...otherImgs].map((img, i) => `
            <img src="/images/${escapeHtml(img.filename)}"
                 data-src="/images/${escapeHtml(img.filename)}"
                 class="${i === 0 ? 'active' : ''}">
          `).join('')}
        </div>` : ''}
      </div>`;
  }

  return `
    <div class="answer-card${primary ? '' : ' no-image'}">
      ${imageSide}
      <div class="ac-body">
        <div class="ac-title-row">
          <h2>${escapeHtml(a.names.ar || a.names.en)}</h2>
          ${a.names.en && a.names.ar !== a.names.en ? `<span class="ac-name-en">${escapeHtml(a.names.en)}</span>` : ''}
        </div>
        <div class="ac-answer">
          <span class="answer-mode-tag ${res.mode}">${res.mode === 'generative' ? '✨ مولّدة بنموذج' : '⚡ استرجاع مباشر'}</span>
          ${escapeHtml(res.answer)}
        </div>
        <div class="ac-meta">
          ${museumLine ? `<div class="meta-item"><span class="label">المتحف</span><span class="value">${escapeHtml(museumLine)}</span></div>` : ''}
          ${hall ? `<div class="meta-item"><span class="label">القاعة</span><span class="value">${escapeHtml(hall)}</span></div>` : ''}
          ${period ? `<div class="meta-item"><span class="label">العصر</span><span class="value">${escapeHtml(period)}${yrange ? ' (' + escapeHtml(yrange) + ')' : ''}</span></div>` : ''}
          ${dynasty ? `<div class="meta-item"><span class="label">الأسرة</span><span class="value">${escapeHtml(dynasty)}</span></div>` : ''}
          ${materials ? `<div class="meta-item"><span class="label">المادة</span><span class="value">${escapeHtml(materials)}</span></div>` : ''}
          ${a.opened ? `<div class="meta-item"><span class="label">افتُتح</span><span class="value">${escapeHtml(a.opened)}</span></div>` : ''}
        </div>
        <div class="ac-actions">
          <button onclick="openDetail('${escapeHtml(a.id)}')">عرض التفاصيل الكاملة</button>
          ${(a.sources || []).map(s => `<a href="${escapeHtml(s.url)}" target="_blank">${escapeHtml(s.type)}</a>`).join('')}
        </div>
      </div>
    </div>`;
}

function buildSourceCard(s) {
  const img = s.primary_image
    ? `<div class="src-thumb" style="background-image:url('/images/${escapeHtml(s.primary_image)}')"></div>`
    : `<div class="src-thumb" style="background:linear-gradient(135deg,#2c2737,#1f1d28);display:flex;align-items:center;justify-content:center;color:var(--gold);font-size:24px">𓂀</div>`;
  return `
    <div class="source-card" data-id="${escapeHtml(s.artifact_id)}">
      ${img}
      <div class="src-body">
        <h4 class="src-name">${escapeHtml(s.name_ar || s.name_en || s.artifact_id)}</h4>
        <div class="src-text">${escapeHtml(s.text)}</div>
        <div class="src-score">${escapeHtml(s.museum_ar || s.museum_id || '')} · score ${s.score}</div>
      </div>
    </div>`;
}

function buildRelatedCard(r) {
  if (!r) return '';
  return `
    <div class="related-card" data-id="${escapeHtml(r.id)}">
      <div class="rel-thumb" style="background-image:url('/images/${escapeHtml(r.primary_image || '')}')"></div>
      <div class="rel-name">${escapeHtml(r.name_ar || r.name_en || r.id)}</div>
    </div>`;
}

function suggestFollowups(res) {
  const suggestions = [];
  const a = res.primary_artifact;
  if (!a) return suggestions;
  const name = a.names?.ar || a.names?.en;
  if (a.kind === 'museum') {
    suggestions.push({ q: `ما القاعات الرئيسية في ${name}؟` });
    suggestions.push({ q: `أين يقع ${name}؟` });
  } else if (a.kind === 'hall') {
    suggestions.push({ q: `ما القطع المعروضة في ${name}؟` });
  } else {
    if (!res.answer.includes('عام')) suggestions.push({ q: `متى صُنعت ${name}؟` });
    if (!res.answer.includes('متحف')) suggestions.push({ q: `أين توجد ${name} حاليًا؟` });
    if (!res.answer.includes('مادة') && a.material?.length) suggestions.push({ q: `من أي مادة صُنعت ${name}؟` });
    if (a.discovery?.year) suggestions.push({ q: `من اكتشف ${name}؟` });
  }
  return suggestions.slice(0, 4);
}

async function askQuery(q) {
  if (!q || !q.trim()) return;
  q = q.trim();
  askInput.value = q;
  pushHistory(q);

  // Show loader, hide previous
  document.getElementById('hero').scrollIntoView({ behavior: 'smooth' });
  answerSec.hidden = false;
  answerWrap.hidden = true;
  answerLoader.hidden = false;

  const modeInput = document.querySelector('input[name="mode"]:checked');
  const mode = modeInput ? modeInput.value : 'extractive';

  let res;
  try {
    res = await getJson('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q, k: 6, mode, lang: 'ar' }),
    });
  } catch (err) {
    answerLoader.hidden = true;
    answerWrap.hidden = false;
    answerCard.innerHTML = `<div class="answer-card no-image"><div class="ac-body">
      <div class="ac-answer" style="color:#ff9090">حدث خطأ: ${escapeHtml(err.message)}</div></div></div>`;
    sourcesBlock.hidden = true;
    relatedBlock.hidden = true;
    return;
  }

  answerLoader.hidden = true;
  answerWrap.hidden = false;

  // Hero card
  answerCard.innerHTML = buildAnswerCard(res);

  // Image thumbs interactivity
  const heroImg = document.getElementById('acHeroImg');
  if (heroImg) {
    heroImg.addEventListener('click', e => {
      if (e.target.tagName === 'IMG') return;
      const url = heroImg.style.backgroundImage.replace(/^url\(["']?(.+?)["']?\)$/, '$1');
      modalImg.src = url; imageModal.classList.add('show');
    });
    heroImg.querySelectorAll('.ac-image-thumbs img').forEach(t => {
      t.addEventListener('click', e => {
        e.stopPropagation();
        heroImg.style.backgroundImage = `url('${t.dataset.src}')`;
        heroImg.querySelectorAll('.ac-image-thumbs img').forEach(o => o.classList.remove('active'));
        t.classList.add('active');
      });
    });
  }

  // Sources
  if (res.sources?.length) {
    sourcesBlock.hidden = false;
    sourcesGrid.innerHTML = res.sources.map(buildSourceCard).join('');
    sourcesGrid.querySelectorAll('.source-card').forEach(card => {
      card.addEventListener('click', () => openDetail(card.dataset.id));
    });
  } else {
    sourcesBlock.hidden = true;
  }

  // Related
  if (res.related?.length) {
    relatedBlock.hidden = false;
    relatedGrid.innerHTML = res.related.map(buildRelatedCard).join('');
    relatedGrid.querySelectorAll('.related-card').forEach(card => {
      card.addEventListener('click', () => openDetail(card.dataset.id));
    });
  } else {
    relatedBlock.hidden = true;
  }

  // Follow-ups
  const followups = suggestFollowups(res);
  if (followups.length) {
    followupsBlock.hidden = false;
    followupsRow.innerHTML = followups.map(f =>
      `<button class="followup-pill">${escapeHtml(f.q)}</button>`).join('');
    followupsRow.querySelectorAll('.followup-pill').forEach((b, i) =>
      b.addEventListener('click', () => askQuery(followups[i].q)));
  } else {
    followupsBlock.hidden = true;
  }

  // Smooth scroll to answer
  setTimeout(() => answerSec.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
}

async function openDetail(id) {
  let rec;
  try {
    rec = await getJson(`/api/artifacts/${encodeURIComponent(id)}`);
  } catch {
    alert('Detail not available for ' + id);
    return;
  }
  const imgs = (rec.images || []).map(i =>
    `<img src="/images/${escapeHtml(i.filename)}" alt="${escapeHtml(i.caption_en || '')}"
          title="${escapeHtml(i.credit || '')} — ${escapeHtml(i.license || '')}"
          onclick="zoomImage(this.src)">`).join('');
  const qa = (rec.qa_pairs_ar || []).map(p =>
    `<div class="qa"><b>س:</b> ${escapeHtml(p.q)}<br><b>ج:</b> ${escapeHtml(p.a)}</div>`).join('');
  const related = (rec.related_ids || []).map(rid =>
    `<span class="chip" data-id="${escapeHtml(rid)}">${escapeHtml(rid)}</span>`).join('');

  detailBody.innerHTML = `
    <h2>${escapeHtml(rec.names?.ar || rec.names?.en || rec.id)}</h2>
    <div class="name-en">${escapeHtml(rec.names?.en || '')}</div>
    ${imgs ? `<div class="gallery">${imgs}</div>` : ''}
    ${rec.current_location?.museum_ar || rec.current_location?.museum_en
      ? `<div class="field"><b>المتحف:</b> ${escapeHtml(rec.current_location.museum_ar || rec.current_location.museum_en || '')}</div>` : ''}
    ${rec.current_location?.hall_ar
      ? `<div class="field"><b>القاعة:</b> ${escapeHtml(rec.current_location.hall_ar)}</div>` : ''}
    ${rec.period?.ar || rec.period?.en
      ? `<div class="field"><b>العصر:</b> ${escapeHtml(rec.period.ar || rec.period.en)}</div>` : ''}
    ${rec.dynasty?.ar || rec.dynasty?.en
      ? `<div class="field"><b>الأسرة:</b> ${escapeHtml(rec.dynasty.ar || rec.dynasty.en)}</div>` : ''}
    ${rec.material?.length ? `<div class="field"><b>المادة:</b> ${escapeHtml(rec.material.join('، '))}</div>` : ''}
    ${rec.sources?.length ? `<div class="field"><b>المصدر:</b> ${rec.sources.map(s => `<a href="${escapeHtml(s.url)}" target="_blank" style="color:var(--gold)">${escapeHtml(s.type)}</a>`).join(' · ')}</div>` : ''}
    <div class="desc">${escapeHtml(rec.description?.ar || rec.description?.en || '')}</div>
    ${qa ? '<h3>أسئلة عن هذه القطعة</h3>' + qa : ''}
    ${related ? '<h3>قطع ذات صلة</h3><div class="related-chips">' + related + '</div>' : ''}
  `;
  detailModal.hidden = false;
  detailModal.querySelectorAll('.related-chips .chip').forEach(c => {
    c.addEventListener('click', () => openDetail(c.dataset.id));
  });
  detailModal.scrollTop = 0;
}
function closeDetail() { detailModal.hidden = true; }
function zoomImage(src) { modalImg.src = src; imageModal.classList.add('show'); }

window.openDetail = openDetail;
window.closeDetail = closeDetail;
window.zoomImage = zoomImage;

// ─── init ─────────────────────────────────────────────────────────────
askForm.addEventListener('submit', e => {
  e.preventDefault();
  askQuery(askInput.value);
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (imageModal.classList.contains('show')) imageModal.classList.remove('show');
    else if (!detailModal.hidden) closeDetail();
  }
});

(async () => {
  try {
    const sug = await getJson('/api/suggestions');
    renderSuggestions(sug);
  } catch (e) { console.warn('no suggestions', e); }
  try {
    const ms = await getJson('/api/museums');
    ms.forEach(m => MUSEUM_NAMES[m.id] = m.names.ar);
  } catch (e) { /* ignore */ }
  renderHistory();
})();
