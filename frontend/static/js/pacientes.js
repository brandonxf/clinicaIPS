/* pacientes.js — Listado de pacientes con filtros y paginación */

let paginaActual = 1;
let totalPaginas = 1;
let todosLosPacientes = [];
let debounceTimer = null;
let userRol = window.USER_ROL || '';
console.log('USER_ROL:', userRol);

const puedePredecir = userRol === 'administrador' || userRol === 'analista';
const puedeEditar = userRol === 'administrador';
console.log('puedePredecir:', puedePredecir, '| puedeEditar:', puedeEditar);

async function cargarPacientes(pagina = 1) {
  paginaActual = pagina;
  const riesgo  = document.getElementById('filtro-riesgo').value;
  const sexo    = document.getElementById('filtro-sexo').value;
  const critico = document.getElementById('filtro-critico').checked;
  const busqueda = document.getElementById('busqueda').value;

  let url = `/api/pacientes/?page=${pagina}`;
  if (riesgo)  url += `&riesgo=${riesgo}`;
  if (sexo)    url += `&sexo=${sexo}`;
  if (critico) url += `&critico=true`;
  if (busqueda) url += `&search=${encodeURIComponent(busqueda)}`;

  const tbody = document.getElementById('pacientes-tbody');
  tbody.innerHTML = `<tr><td colspan="12" class="text-center py-4">
    <div class="spinner-border spinner-border-sm me-2"></div>Cargando...
  </td></tr>`;

  try {
    const res = await authFetch(url);
    if (!res) return;
    const data = await res.json();

    const resultados = data.results ?? data;
    const total = data.count ?? resultados.length;
    totalPaginas = data.next || data.previous ? Math.ceil(total / 50) : 1;

    todosLosPacientes = resultados;
    renderTabla(resultados);
    document.getElementById('badge-total').textContent = total;
    document.getElementById('pagination-info').textContent =
      `Mostrando ${resultados.length} de ${total} pacientes`;
    renderPaginacion();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="12" class="text-center text-danger py-4">
      Error al cargar datos: ${e.message}
    </td></tr>`;
  }
}

function renderTabla(pacientes) {
  const tbody = document.getElementById('pacientes-tbody');
  if (!pacientes.length) {
    tbody.innerHTML = '<tr><td colspan="12" class="text-center text-muted py-5">Sin pacientes encontrados</td></tr>';
    return;
  }

  const puedePred = puedePredecir;
  const puedeEdit = puedeEditar;
  tbody.innerHTML = pacientes.map(p => {
    const sexoIcono = p.sexo === 'Masculino' ? '♂' : p.sexo === 'Femenino' ? '♀' : p.sexo === 'M' ? '♂' : p.sexo === 'F' ? '♀' : '—';
    const badgeRiesgo = p.riesgo_enfermedad || 'bajo';
    const btnPredict = puedePred
      ? `<button class="btn btn-sm btn-outline-info" style="border-radius:8px;font-size:0.72rem;padding:0.25rem 0.5rem;white-space:nowrap;"
                 onclick="predecirRiesgo(${p.id_paciente})" title="Predecir riesgo">
           <i class="bi bi-robot"></i> Predecir
         </button>`
      : '<span class="text-muted" style="font-size:0.75rem;">—</span>';
    const btnEdit = puedeEdit
      ? `<button class="btn btn-sm btn-outline-warning" style="border-radius:8px;font-size:0.72rem;padding:0.25rem 0.5rem;white-space:nowrap;"
                 onclick="editarPaciente(${p.id})" title="Editar paciente">
           <i class="bi bi-pencil"></i>
         </button>`
      : '';
    return `<tr class="${p.es_critico ? 'critico-row' : ''}">
      <td class="patient-id">${p.id_paciente}</td>
      <td class="patient-name">${p.nombres} ${p.apellidos}</td>
      <td>${p.edad ?? '—'}</td>
      <td>${sexoIcono}</td>
      <td>${p.imc ? p.imc.toFixed(1) : '—'}
          ${p.clasificacion_imc ? `<span class="imc-sub">${p.clasificacion_imc.replace('_',' ')}</span>` : ''}</td>
      <td class="${p.glucosa > 126 ? 'glucose-high' : ''}">${p.glucosa ?? '—'}</td>
      <td class="${p.presion_sistolica > 140 ? 'pressure-high' : ''}">${p.presion_sistolica ?? '—'}</td>
      <td style="max-width:180px;">${p.diagnostico_preliminar || '—'}</td>
      <td><span class="risk-badge risk-${badgeRiesgo}">${badgeRiesgo}</span></td>
      <td>${p.es_critico
        ? '<i class="bi bi-exclamation-triangle-fill critico-icon" title="Paciente crítico"></i>'
        : '<i class="bi bi-check-circle-fill stable-icon"></i>'}</td>
      <td>${btnPredict}</td>
      <td>${btnEdit}</td>
    </tr>`;
  }).join('');
}

function filtrarLocal() {
  // Debounce: espera 500ms después de dejar de escribir antes de buscar
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    cargarPacientes(1);
  }, 500);
}

function renderPaginacion() {
  const ctrl = document.getElementById('pagination-controls');
  if (totalPaginas <= 1) { ctrl.innerHTML = ''; return; }

  let html = `
    <button class="btn btn-sm btn-outline-secondary" onclick="cargarPacientes(${paginaActual-1})"
            ${paginaActual === 1 ? 'disabled' : ''}>
      <i class="bi bi-chevron-left"></i>
    </button>`;
  for (let i = Math.max(1, paginaActual-2); i <= Math.min(totalPaginas, paginaActual+2); i++) {
    html += `<button class="btn btn-sm ${i === paginaActual ? 'btn-primary' : 'btn-outline-secondary'}"
               onclick="cargarPacientes(${i})">${i}</button>`;
  }
  html += `
    <button class="btn btn-sm btn-outline-secondary" onclick="cargarPacientes(${paginaActual+1})"
            ${paginaActual === totalPaginas ? 'disabled' : ''}>
      <i class="bi bi-chevron-right"></i>
    </button>`;
  ctrl.innerHTML = html;
}

let pacienteEditandoId = null;

const EDIT_FIELDS = [
  { key: 'nombres', label: 'Nombres', type: 'text' },
  { key: 'apellidos', label: 'Apellidos', type: 'text' },
  { key: 'edad', label: 'Edad', type: 'number', step: '1' },
  { key: 'sexo', label: 'Sexo', type: 'select', options: ['Masculino', 'Femenino', 'Otro'] },
  { key: 'peso', label: 'Peso (kg)', type: 'number', step: '0.1' },
  { key: 'altura', label: 'Altura (m)', type: 'number', step: '0.01' },
  { key: 'presion_sistolica', label: 'Presión Sistólica (mmHg)', type: 'number', step: '0.1' },
  { key: 'presion_diastolica', label: 'Presión Diastólica (mmHg)', type: 'number', step: '0.1' },
  { key: 'frecuencia_cardiaca', label: 'Frecuencia Cardíaca (lpm)', type: 'number', step: '0.1' },
  { key: 'glucosa', label: 'Glucosa (mg/dL)', type: 'number', step: '0.1' },
  { key: 'colesterol', label: 'Colesterol (mg/dL)', type: 'number', step: '0.1' },
  { key: 'saturacion_oxigeno', label: 'Saturación O₂ (%)', type: 'number', step: '0.1' },
  { key: 'temperatura', label: 'Temperatura (°C)', type: 'number', step: '0.1' },
  { key: 'diagnostico_preliminar', label: 'Diagnóstico', type: 'text' },
  { key: 'actividad_fisica', label: 'Actividad Física', type: 'select', options: ['sedentario', 'baja', 'media', 'alta'] },
  { key: 'fumador', label: 'Fumador', type: 'checkbox' },
  { key: 'consumo_alcohol', label: 'Consumo Alcohol', type: 'checkbox' },
  { key: 'antecedentes_familiares', label: 'Antecedentes Familiares', type: 'checkbox' },
];

function editarPaciente(pk) {
  pacienteEditandoId = pk;
  const body = document.getElementById('editar-body');
  body.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm"></div><p class="mt-2 mb-0 text-muted">Cargando datos...</p></div>';
  const modal = new bootstrap.Modal(document.getElementById('modalEditar'));
  modal.show();

  const paciente = todosLosPacientes.find(p => p.id === pk);
  if (!paciente) return;

  const formFields = EDIT_FIELDS.map(f => {
    const val = paciente[f.key] ?? '';
    if (f.type === 'select') {
      const opts = f.options.map(o =>
        `<option value="${o}" ${val === o ? 'selected' : ''}>${o.charAt(0).toUpperCase() + o.slice(1)}</option>`
      ).join('');
      return `<div class="col-md-4">
        <label class="form-label" style="font-size:0.78rem;font-weight:600;">${f.label}</label>
        <select class="form-select form-select-sm" name="${f.key}">${opts}</select>
      </div>`;
    }
    if (f.type === 'checkbox') {
      return `<div class="col-md-4 d-flex align-items-center pt-4">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" name="${f.key}" id="chk_${f.key}" ${val ? 'checked' : ''}>
          <label class="form-check-label" style="font-size:0.8rem;" for="chk_${f.key}">${f.label}</label>
        </div>
      </div>`;
    }
    return `<div class="col-md-4">
      <label class="form-label" style="font-size:0.78rem;font-weight:600;">${f.label}</label>
      <input type="${f.type}" class="form-control form-control-sm" name="${f.key}" value="${val}"
             ${f.step ? `step="${f.step}"` : ''}>
    </div>`;
  }).join('');

  body.innerHTML = formFields;
}

async function guardarEdicion(e) {
  e.preventDefault();
  const form = document.getElementById('formEditar');
  const data = {};
  const formData = new FormData(form);
  for (const [key, val] of formData.entries()) {
    const field = EDIT_FIELDS.find(f => f.key === key);
    if (!field) continue;
    if (field.type === 'checkbox') {
      data[key] = true;
    } else if (field.type === 'number') {
      data[key] = val === '' ? null : (field.step === '1' ? parseInt(val) : parseFloat(val));
    } else {
      data[key] = val;
    }
  }
  for (const f of EDIT_FIELDS) {
    if (f.type === 'checkbox' && !formData.has(f.key)) {
      data[f.key] = false;
    }
  }

  try {
    const res = await authFetch(`/api/pacientes/${pacienteEditandoId}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res) throw new Error('No autorizado');
    const result = await res.json();
    if (result.error) throw new Error(result.error);
    bootstrap.Modal.getInstance(document.getElementById('modalEditar')).hide();
    cargarPacientes(paginaActual);
  } catch (err) {
    alert('Error al guardar: ' + err.message);
  }
}

async function predecirRiesgo(pacienteId) {
  const body = document.getElementById('prediccion-body');
  const modal = new bootstrap.Modal(document.getElementById('modalPrediccion'));
  body.innerHTML = `<div class="text-center py-4">
    <div class="spinner-border spinner-border-sm"></div>
    <p class="mt-2 mb-0 text-muted" style="font-size:0.85rem;">Ejecutando predicción...</p>
  </div>`;
  modal.show();

  try {
    const res = await authFetch('/api/ml/predecir/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paciente_id: pacienteId })
    });
    if (!res) throw new Error('No autorizado');
    const data = await res.json();

    if (data.error) {
      body.innerHTML = `<div class="text-center py-4 text-danger">
        <i class="bi bi-exclamation-triangle-fill" style="font-size:2rem;"></i>
        <p class="mt-2 mb-0">${data.error}</p>
      </div>`;
      return;
    }

    const riesgo = data.riesgo_predicho || 'desconocido';
    const prob = data.probabilidad ? (data.probabilidad * 100).toFixed(1) : '—';
    const clases = data.distribucion_clases || {};
    const paci = data.paciente || {};

    const bars = Object.entries(clases).map(([k, v]) => {
      const pct = (v * 100).toFixed(1);
      const color = k === 'bajo' ? '#059669' : k === 'medio' ? '#ea580c' : k === 'alto' ? '#dc2626' : '#ff375f';
      return `<div class="d-flex align-items-center mb-2">
        <span style="width:60px;font-size:0.78rem;font-weight:600;text-transform:capitalize;">${k}</span>
        <div class="progress flex-grow-1" style="height:8px;border-radius:6px;background:#f0f0f0;">
          <div class="progress-bar" style="width:${pct}%;background:${color};border-radius:6px;"></div>
        </div>
        <span style="width:50px;text-align:right;font-size:0.78rem;font-weight:600;color:${color};">${pct}%</span>
      </div>`;
    }).join('');

    body.innerHTML = `
      <div class="text-center mb-3">
        <strong style="font-size:1rem;">${paci.nombres || ''} ${paci.apellidos || ''}</strong>
        <span class="d-block text-muted" style="font-size:0.8rem;">ID: ${data.paciente_id || pacienteId}</span>
      </div>
      <div class="text-center mb-3">
        <span class="risk-badge risk-${riesgo}" style="font-size:1rem;padding:0.5rem 1.5rem;">
          Riesgo: ${riesgo}
        </span>
        <div class="mt-2" style="font-size:0.85rem;color:#5a6577;">
          Probabilidad: <strong>${prob}%</strong>
        </div>
      </div>
      <hr style="opacity:0.3;">
      <div style="font-size:0.82rem;font-weight:600;color:#1a2635;margin-bottom:0.5rem;">Distribución por clase</div>
      ${bars}
    `;
  } catch (e) {
    body.innerHTML = `<div class="text-center py-4 text-danger">
      <i class="bi bi-exclamation-triangle-fill" style="font-size:2rem;"></i>
      <p class="mt-2 mb-0">Error: ${e.message}</p>
    </div>`;
  }
}

function getFilterParams() {
  const riesgo  = document.getElementById('filtro-riesgo').value;
  const sexo    = document.getElementById('filtro-sexo').value;
  const critico = document.getElementById('filtro-critico').checked;
  const busqueda = document.getElementById('busqueda').value;
  const params = new URLSearchParams();
  if (riesgo)  params.set('riesgo', riesgo);
  if (sexo)    params.set('sexo', sexo);
  if (critico) params.set('critico', 'true');
  if (busqueda) params.set('search', busqueda);
  return params.toString();
}

function descargarConFiltros(baseUrl, filename) {
  const qs = getFilterParams();
  const url = qs ? `${baseUrl}?${qs}` : baseUrl;
  descargarArchivo(url, filename);
}

document.addEventListener('DOMContentLoaded', () => cargarPacientes(1));
