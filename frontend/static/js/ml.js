/* ml.js — Entrenamiento, métricas, predicción */

let confusionChart = null;
let metricasChart = null;

function getEl(id) {
  return document.getElementById(id);
}

function safeSetHTML(el, html) {
  if (!el) return false;
  el.innerHTML = html;
  return true;
}

async function entrenarModelo() {
  const selectAlgoritmo = getEl('select-algoritmo');
  const btn = getEl('btn-entrenar');
  const progress = getEl('train-progress');

  if (!selectAlgoritmo || !btn || !progress) return;

  const algoritmo = selectAlgoritmo.value;

  btn.disabled = true;
  progress.classList.add('active');

  try {
    const res = await authFetch('/api/ml/entrenar/', {
      method: 'POST',
      body: JSON.stringify({ algoritmo })
    });
    if (!res) return;

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      const result = data.result || data || {};
      const metrics = result.metricas || result.metrics || {};
      const matrix = result.matrix || null;

      const unifiedMetricas = {
        accuracy: metrics.accuracy ?? 0,
        precision: metrics.precision ?? 0,
        recall: metrics.recall ?? 0,
        f1_score: metrics.f1_score ?? 0,
        confusion_matrix: metrics.confusion_matrix ?? null,
        clases: metrics.clases ?? null,
        matrix: matrix
      };

      mostrarMetricas(unifiedMetricas, data.modelo, matrix);
      await cargarModelos();
    } else {
      alert('Error: ' + (data.error || 'No se pudo entrenar el modelo'));
    }
  } catch (e) {
    alert('Error de conexión: ' + (e?.message || String(e)));
  } finally {
    btn.disabled = false;
    progress.classList.remove('active');
  }
}

function mostrarMetricas(metricas, modelo, matrix) {
  const panel = getEl('metricas-panel');
  if (!panel || !metricas || !modelo) return;

  const acc = ((metricas?.accuracy ?? 0) * 100).toFixed(1);
  const prec = ((metricas?.precision ?? 0) * 100).toFixed(1);
  const rec = ((metricas?.recall ?? 0) * 100).toFixed(1);
  const f1 = ((metricas?.f1_score ?? 0) * 100).toFixed(1);

  safeSetHTML(panel, `
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
      <div class="ml-metric-card">
        <div class="label">Accuracy</div>
        <div class="value" style="color:#10e5cc;">${acc}%</div>
        <div class="bar"><div class="bar-fill" style="width:${acc}%; background:linear-gradient(90deg,#10e5cc,#0bb8a4);"></div></div>
      </div>
      <div class="ml-metric-card">
        <div class="label">Precision</div>
        <div class="value" style="color:#10b981;">${prec}%</div>
        <div class="bar"><div class="bar-fill" style="width:${prec}%; background:linear-gradient(90deg,#10b981,#34d399);"></div></div>
      </div>
      <div class="ml-metric-card">
        <div class="label">Recall</div>
        <div class="value" style="color:#f97316;">${rec}%</div>
        <div class="bar"><div class="bar-fill" style="width:${rec}%; background:linear-gradient(90deg,#f97316,#fb923c);"></div></div>
      </div>
      <div class="ml-metric-card">
        <div class="label">F1-Score</div>
        <div class="value" style="color:#8b5cf6;">${f1}%</div>
        <div class="bar"><div class="bar-fill" style="width:${f1}%; background:linear-gradient(90deg,#8b5cf6,#a78bfa);"></div></div>
      </div>
    </div>
    <div class="ml-metric-card" style="text-align:center; padding:0.75rem;">
      <div class="model-name">Modelo: <strong style="color:#080e1c;">${modelo.nombre}</strong></div>
    </div>
  `);

  const confusionSection = getEl('confusion-section');
  if (confusionSection) confusionSection.style.removeProperty('display');

  const chartMetricas = getEl('chart-metricas');
  if (chartMetricas) {
    if (metricasChart) { metricasChart.destroy(); metricasChart = null; }

    metricasChart = new Chart(chartMetricas, {
      type: 'bar',
      data: {
        labels: ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
        datasets: [{
          label: 'Valor (%)',
          data: [acc, prec, rec, f1],
          backgroundColor: ['rgba(16,229,204,0.6)', 'rgba(16,185,129,0.6)', 'rgba(249,115,22,0.6)', 'rgba(139,92,246,0.6)'],
          borderColor: ['#10e5cc', '#10b981', '#f97316', '#8b5cf6'],
          borderWidth: 2,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { callback: v => v + '%', color: '#8899aa', font: { size: 11 } },
            grid: { color: '#f0f0f0' }
          },
          x: {
            ticks: { color: '#8899aa', font: { size: 11 } },
            grid: { display: false }
          }
        }
      }
    });
  }

  if (matrix && typeof matrix === 'object' && !metricas.confusion_matrix) {
    const clases = Object.keys(matrix);
    const cm = clases.map(k => matrix[k]);
    renderMatrizConfusion(cm, clases);
  } else {
    renderMatrizConfusion(metricas.confusion_matrix, metricas.clases);
  }
}


function renderMatrizConfusion(cm, clases) {
  if (!cm || !clases) return;

  const canvas = getEl('chart-confusion');
  if (!canvas || !canvas.parentElement) return;

  if (confusionChart) { confusionChart.destroy(); confusionChart = null; }

  let html = '<table class="ml-table" style="font-size:0.82rem;">';
  html += '<thead><tr><th style="background:#080e1c; color:#fff; font-size:0.7rem;">Real \\ Pred</th>';
  clases.forEach(c => (html += `<th style="background:#080e1c; color:#fff; font-size:0.7rem;">${c}</th>`));
  html += '</tr></thead><tbody>';

  cm.forEach((row, i) => {
    html += `<tr><td style="background:#162136; color:#fff; font-weight:700; font-size:0.78rem;">${clases[i]}</td>`;
    row.forEach((v, j) => {
      const isDiag = i === j;
      const bg = isDiag ? 'rgba(16,229,204,0.15)' : (v > 0 ? 'rgba(255,95,109,0.08)' : '');
      const color = isDiag ? '#0bb8a4' : (v > 0 ? '#ff375f' : '#8899aa');
      html += `<td style="background:${bg}; color:${color}; font-weight:${isDiag || v > 0 ? '700' : '400'}; text-align:center; font-family:'Space Grotesk',monospace;">${v}</td>`;
    });
    html += '</tr>';
  });

  html += '</tbody></table>';
  canvas.parentElement.innerHTML = '<h6 style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:700; color:#8899aa; margin-bottom:0.75rem;">Matriz de Confusión</h6>' + html;
}

async function predecirPaciente() {
  const inputId = getEl('input-paciente-id');
  const div = getEl('prediccion-resultado');

  if (!inputId || !div) return;

  const id = inputId.value;
  if (!id) { alert('Ingresa el ID del paciente.'); return; }

  div.classList.add('active');
  div.innerHTML = '<div style="display:flex; align-items:center; gap:0.5rem; color:#8899aa; font-size:0.85rem;"><div class="spinner-border spinner-border-sm" style="color:#10e5cc;"></div>Prediciendo...</div>';

  try {
    const res = await authFetch('/api/ml/predecir/', {
      method: 'POST',
      body: JSON.stringify({ paciente_id: parseInt(id) })
    });

    if (!res) return;
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      const colorMap = {
        bajo: { bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)', text: '#059669', bar: '#10b981' },
        medio: { bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.2)', text: '#ea580c', bar: '#f97316' },
        alto: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)', text: '#dc2626', bar: '#ef4444' },
        critico: { bg: 'rgba(255,95,109,0.1)', border: 'rgba(255,95,109,0.25)', text: '#ff375f', bar: '#ff5f6d' }
      };
      const c = colorMap[data.riesgo_predicho] || colorMap.bajo;
      const pct = (data.probabilidad * 100).toFixed(1);
      const p = data.paciente || {};
      const nombreCompleto = [p.nombres, p.apellidos].filter(Boolean).join(' ') || '—';

      const distHtml = Object.entries(data.distribucion_clases || {})
        .map(([k, v]) => {
          const dc = colorMap[k] || colorMap.bajo;
          return `
            <div style="margin-bottom:0.5rem;">
              <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:3px;">
                <span style="color:#1a2635; text-transform:capitalize;">${k}</span>
                <span style="font-weight:700; color:#080e1c; font-family:'Space Grotesk',sans-serif;">${(v * 100).toFixed(1)}%</span>
              </div>
              <div style="height:4px; border-radius:4px; background:#e5e7eb; overflow:hidden;">
                <div style="height:100%; width:${(v * 100).toFixed(1)}%; background:${dc.bar}; border-radius:4px; transition:width 0.6s ease;"></div>
              </div>
            </div>`;
        }).join('');

      div.innerHTML = `
        <div style="background:${c.bg}; border:1px solid ${c.border}; border-radius:12px; padding:1.25rem;">
          <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
            <div style="width:48px; height:48px; border-radius:12px; background:${c.bg}; display:flex; align-items:center; justify-content:center;">
              <i class="bi bi-heart-pulse-fill" style="font-size:1.4rem; color:${c.text};"></i>
            </div>
            <div>
              <div style="font-size:0.75rem; color:#8899aa; text-transform:uppercase; letter-spacing:0.05em; font-weight:700;">Riesgo Predicho</div>
              <div style="font-size:1.3rem; font-weight:700; color:${c.text}; text-transform:capitalize; font-family:'Space Grotesk',sans-serif;">${data.riesgo_predicho}</div>
            </div>
            <div style="margin-left:auto; text-align:right;">
              <div style="font-size:1.5rem; font-weight:700; color:#080e1c; font-family:'Space Grotesk',sans-serif;">${pct}%</div>
              <div style="font-size:0.7rem; color:#8899aa;">Probabilidad</div>
            </div>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; padding:0.75rem; background:rgba(255,255,255,0.6); border-radius:10px; margin-bottom:1rem;">
            <div><span style="font-size:0.65rem; text-transform:uppercase; color:#8899aa; font-weight:700;">Paciente</span><div style="font-weight:600; color:#080e1c;">${nombreCompleto}</div></div>
            <div><span style="font-size:0.65rem; text-transform:uppercase; color:#8899aa; font-weight:700;">Edad / Sexo</span><div style="font-weight:600; color:#080e1c;">${p.edad ?? '—'} años / ${p.sexo === 'Masculino' ? '♂' : p.sexo === 'Femenino' ? '♀' : p.sexo || '—'}</div></div>
            <div><span style="font-size:0.65rem; text-transform:uppercase; color:#8899aa; font-weight:700;">IMC</span><div style="font-weight:600; color:#080e1c;">${p.imc ? p.imc.toFixed(1) : '—'}</div></div>
            <div><span style="font-size:0.65rem; text-transform:uppercase; color:#8899aa; font-weight:700;">Glucosa</span><div style="font-weight:600; color:${p.glucosa > 126 ? '#dc2626' : '#080e1c'};">${p.glucosa ?? '—'}</div></div>
            <div><span style="font-size:0.65rem; text-transform:uppercase; color:#8899aa; font-weight:700;">P. Sistólica</span><div style="font-weight:600; color:${p.presion_sistolica > 140 ? '#dc2626' : '#080e1c'};">${p.presion_sistolica ?? '—'}</div></div>
            <div><span style="font-size:0.65rem; text-transform:uppercase; color:#8899aa; font-weight:700;">Diagnóstico</span><div style="font-weight:600; color:#080e1c;">${p.diagnostico_preliminar || '—'}</div></div>
          </div>
          <div style="height:6px; border-radius:6px; background:#e5e7eb; overflow:hidden; margin-bottom:1rem;">
            <div style="height:100%; width:${pct}%; background:${c.bar}; border-radius:6px; transition:width 0.8s ease;"></div>
          </div>
          <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:700; color:#8899aa; margin-bottom:0.75rem;">Distribución por Clases</div>
          ${distHtml}
        </div>`;
    } else {
      div.innerHTML = `<div style="background:rgba(255,95,109,0.05); border:1px solid rgba(255,95,109,0.15); border-radius:12px; padding:1rem; color:#ff375f; font-size:0.85rem;">
        <i class="bi bi-exclamation-triangle-fill me-1"></i>${data.error || 'No se pudo predecir'}
      </div>`;
    }
  } catch (e) {
    div.innerHTML = `<div style="background:rgba(255,95,109,0.05); border:1px solid rgba(255,95,109,0.15); border-radius:12px; padding:1rem; color:#ff375f; font-size:0.85rem;">
      <i class="bi bi-exclamation-triangle-fill me-1"></i>Error: ${(e?.message || String(e))}
    </div>`;
  }
}

async function cargarModelos() {
  const tbody = getEl('modelos-tbody');
  if (!tbody) return;

  try {
    const res = await authFetch('/api/ml/modelos/');
    if (!res || !res.ok) return;

    const data = await res.json().catch(() => ([]));

    if (!Array.isArray(data) || !data.length) {
      tbody.innerHTML = `<tr><td colspan="6">
        <div class="empty-state">
          <i class="bi bi-inbox"></i>
          Sin modelos entrenados
        </div>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.filter(m => m && typeof m === 'object').map(m => `
      <tr>
        <td style="font-weight:700; color:#080e1c; font-size:0.82rem;">${m.nombre ?? '—'}</td>
        <td><span class="ml-algo-badge">${String(m.algoritmo ?? '').replace('_', ' ')}</span></td>
        <td style="font-family:'Space Grotesk',sans-serif; font-weight:600;">${m.accuracy != null ? (m.accuracy * 100).toFixed(1) + '%' : '—'}</td>
        <td style="font-family:'Space Grotesk',sans-serif; font-weight:600;">${m.f1_score != null ? (m.f1_score * 100).toFixed(1) + '%' : '—'}</td>
        <td style="font-size:0.82rem; color:#8899aa;">${formatFecha(m.fecha_entrenamiento)}</td>
        <td>${m.activo ? '<span class="ml-status-active">Activo</span>' : '<span class="ml-status-inactive">Inactivo</span>'}</td>
      </tr>
    `).join('');
  } catch (e) {
    console.error(e);
  }
}

function formatFecha(f) {
  return f ? new Date(f).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '—';
}

window.entrenarModelo = entrenarModelo;
window.predecirPaciente = predecirPaciente;
window.cargarModelos = cargarModelos;

document.addEventListener('DOMContentLoaded', () => {
  cargarModelos();
});
