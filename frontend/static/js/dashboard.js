/* dashboard.js — KPIs, graficas Chart.js */

const COLORES_RIESGO = {
  bajo:    '#059669',
  medio:   '#d97706',
  alto:    '#ea580c',
  critico: '#dc2626',
};

async function cargarDashboard() {
  try {
    const res = await authFetch('/api/dashboard/kpis/');
    if (!res || !res.ok) return;
    const data = await res.json();

    const k = data.kpis;
    setText('kpi-total',       k.total_pacientes ?? '—');
    setText('kpi-criticos',    `${k.pacientes_criticos ?? '—'} (${k.pct_criticos ?? 0}%)`);
    setText('kpi-hipertensos', `${k.pacientes_hipertensos ?? '—'} (${k.pct_hipertensos ?? 0}%)`);
    setText('kpi-diabeticos',  `${k.pacientes_diabeticos ?? '—'} (${k.pct_diabeticos ?? 0}%)`);
    setText('kpi-fumadores',   k.pacientes_fumadores ?? '—');
    setText('pct-fumadores',   `${k.pct_fumadores ?? 0}% del total`);

    const avg = k.promedios || {};
    setText('kpi-imc',    avg.avg_imc     ? avg.avg_imc.toFixed(1) : '—');
    setText('kpi-glucosa', avg.avg_glucosa ? avg.avg_glucosa.toFixed(1) + ' mg/dL' : '—');

    const etl = data.ultimo_etl;
    document.getElementById('etl-status').innerHTML = etl?.fecha
      ? `<div class="d-flex gap-3 flex-wrap">
           <div><div class="kpi-sub">Ultima ejecucion</div>
                <div class="fw-semibold">${formatFecha(etl.fecha)}</div></div>
           <div><div class="kpi-sub">Registros</div>
                <div class="fw-semibold">${etl.registros}</div></div>
           <div><div class="kpi-sub">Estado</div>
                <span class="badge ${badgeEstado(etl.estado)}">${etl.estado}</span></div>
         </div>`
      : '<span class="kpi-sub">Sin ejecuciones registradas</span>';

    const ml = data?.modelo_activo;
    document.getElementById('ml-status').innerHTML = ml?.nombre
      ? `<div class="d-flex gap-3 flex-wrap">
           <div><div class="kpi-sub">Modelo</div>
                <div class="fw-semibold">${ml.nombre}</div></div>
           <div><div class="kpi-sub">Accuracy</div>
                <div class="fw-semibold" style="color:var(--emerald);">${ml.accuracy != null ? (ml.accuracy*100).toFixed(1)+'%' : '—'}</div></div>
         </div>`
      : '<span class="kpi-sub">No hay modelos entrenados</span>';

    renderGraficaRiesgo(data.graficas.distribucion_riesgo);
    renderGraficaEdad(data.graficas.segmentacion_edad);
    renderGraficaIMC(data.graficas.distribucion_imc);
    renderGraficaDiagnosticos(data.graficas.top_diagnosticos);
    renderUltimasConsultas(data.ultimas_consultas || []);

  } catch(e) {
    console.error('Error cargando dashboard:', e);
  }
}

function renderUltimasConsultas(consultas) {
  const tbody = document.getElementById('ultimas-consultas-body');
  if (!tbody) return;
  if (!consultas.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted small py-3">Sin consultas registradas</td></tr>';
    return;
  }
  const riesgoBadge = { bajo:'bg-success', medio:'bg-warning text-dark', alto:'bg-orange', critico:'bg-danger' };
  tbody.innerHTML = consultas.map(c => {
    const nombre = [c.nombres, c.apellidos].filter(Boolean).join(' ') || '—';
    const sexo = c.sexo === 'Masculino' ? 'M' : c.sexo === 'Femenino' ? 'F' : c.sexo || '—';
    const badge = riesgoBadge[c.riesgo_enfermedad] || 'bg-secondary';
    const fecha = c.fecha_consulta ? new Date(c.fecha_consulta).toLocaleDateString('es-CO') : '—';
    return `<tr>
      <td class="fw-medium">${nombre}</td>
      <td>${c.edad ?? '—'}</td>
      <td>${sexo}</td>
      <td>${c.diagnostico_preliminar || '—'}</td>
      <td><span class="badge ${badge}">${c.riesgo_enfermedad || '—'}</span></td>
      <td class="text-muted small">${fecha}</td>
    </tr>`;
  }).join('');
}

function renderGraficaRiesgo(data) {
  if (!data || !Object.keys(data).length) return;
  const labels = Object.keys(data);
  const values = Object.values(data);
  new Chart(document.getElementById('chart-riesgo'), {
    type: 'doughnut',
    data: {
      labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
      datasets: [{ data: values, backgroundColor: labels.map(l => COLORES_RIESGO[l] || '#94a3b8'),
                   borderWidth: 2, borderColor: '#fff' }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#64748b', font: { size: 11 } } }
      }
    }
  });
}

function renderGraficaEdad(data) {
  if (!data?.length) return;
  new Chart(document.getElementById('chart-edad'), {
    type: 'bar',
    data: {
      labels: data.map(d => d.rango_edad),
      datasets: [{ label: 'Pacientes', data: data.map(d => d.total),
                   backgroundColor: 'rgba(37,99,235,0.6)', borderColor: '#2563eb',
                   borderWidth: 1, borderRadius: 6 }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } },
        x: { grid: { display: false }, ticks: { color: '#64748b' } }
      }
    }
  });
}

function renderGraficaIMC(data) {
  if (!data || !Object.keys(data).length) return;
  const labels = { bajo_peso:'Bajo Peso', normal:'Normal', sobrepeso:'Sobrepeso', obesidad:'Obesidad' };
  const colors = { bajo_peso:'#0891b2', normal:'#059669', sobrepeso:'#d97706', obesidad:'#dc2626' };
  const keys = Object.keys(data);
  new Chart(document.getElementById('chart-imc'), {
    type: 'pie',
    data: {
      labels: keys.map(k => labels[k] || k),
      datasets: [{ data: Object.values(data),
                   backgroundColor: keys.map(k => colors[k] || '#94a3b8'),
                   borderWidth: 2, borderColor: '#fff' }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#64748b', font: { size: 11 } } }
      }
    }
  });
}

function renderGraficaDiagnosticos(data) {
  if (!data?.length) return;
  new Chart(document.getElementById('chart-diagnosticos'), {
    type: 'bar',
    data: {
      labels: data.map(d => d.diagnostico_preliminar || 'Sin diagnostico'),
      datasets: [{ label: 'Casos', data: data.map(d => d.total),
                   backgroundColor: 'rgba(124,58,237,0.5)', borderColor: '#7c3aed',
                   borderWidth: 1, borderRadius: 4 }]
    },
    options: {
      indexAxis: 'y', responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } },
        y: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 10 } } }
      }
    }
  });
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function formatFecha(f) {
  return f ? new Date(f).toLocaleString('es-CO', { dateStyle:'medium', timeStyle:'short' }) : '—';
}
function badgeEstado(e) {
  return { completado:'bg-success', error:'bg-danger', en_proceso:'bg-warning text-dark',
           pendiente:'bg-secondary' }[e] || 'bg-secondary';
}

document.addEventListener('DOMContentLoaded', cargarDashboard);
