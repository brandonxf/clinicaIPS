/* pacientes.js — Listado de pacientes con filtros y paginación */

let paginaActual = 1;
let totalPaginas = 1;
let todosLosPacientes = [];
let debounceTimer = null;

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
  tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4">
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
    tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-4">
      Error al cargar datos: ${e.message}
    </td></tr>`;
  }
}

function renderTabla(pacientes) {
  const tbody = document.getElementById('pacientes-tbody');
  if (!pacientes.length) {
    tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-5">Sin pacientes encontrados</td></tr>';
    return;
  }

  tbody.innerHTML = pacientes.map(p => {
    const sexoIcono = p.sexo === 'Masculino' ? '♂' : p.sexo === 'Femenino' ? '♀' : p.sexo === 'M' ? '♂' : p.sexo === 'F' ? '♀' : '—';
    const badgeRiesgo = p.riesgo_enfermedad || 'bajo';
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

document.addEventListener('DOMContentLoaded', () => cargarPacientes(1));
