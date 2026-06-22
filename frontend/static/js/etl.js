let etlPollInterval = null;

async function ejecutarETL() {
  const btn = document.getElementById('btn-run-etl');
  const progress = document.getElementById('etl-progress');
  const resultado = document.getElementById('etl-resultado');

  btn.disabled = true;
  progress.classList.add('active');
  resultado.classList.remove('active');

  try {
    const res = await authFetch('/api/etl/run/', { method: 'POST' });
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      mostrarResultado(data);
      cargarHistorial();
      cargarEstadisticasReales();
    } else if (res.status === 404) {
      mostrarMensajeNoDataset();
    } else {
      mostrarErrorDetallado(data, res.status);
    }
  } catch(e) {
    mostrarErrorConexion(e.message);
  } finally {
    btn.disabled = false;
    progress.classList.remove('active');
  }
}

async function subirDataset() {
  const input = document.getElementById('archivo-dataset');
  if (!input.files.length) { alert('Selecciona un archivo primero.'); return; }

  const formData = new FormData();
  formData.append('archivo', input.files[0]);

  const progress = document.getElementById('etl-progress');
  progress.classList.add('active');

  try {
    const res = await authFetch('/api/etl/upload/', {
      method: 'POST',
      body: formData
    });

    const data = await res.json().catch(() => ({}));

    if (res.status === 202) {
      mostrarAceptado(data);
      iniciarPollingEstado();
    } else if (res.ok) {
      mostrarResultado(data);
      cargarHistorial();
      cargarEstadisticasReales();
    } else {
      mostrarErrorDetallado(data, res.status);
    }
  } catch (e) {
    mostrarErrorConexion(e.message);
  } finally {
    progress.classList.remove('active');
  }
}

function iniciarPollingEstado() {
  if (etlPollInterval) clearInterval(etlPollInterval);

  const resultado = document.getElementById('etl-resultado');
  resultado.classList.add('active');

  const badge = document.getElementById('etl-status-badge');
  badge.className = 'etl-status-badge etl-status--proceso';
  badge.textContent = 'Procesando...';

  document.getElementById('etl-metricas').innerHTML = `
    <div style="grid-column: 1 / -1;">
      <div style="background:rgba(16,229,204,0.05); border:1px solid rgba(16,229,204,0.15); border-radius:12px; padding:1.25rem; color:#1a2635;">
        <div style="font-weight:700; margin-bottom:0.4rem; color:#10e5cc;">
          <div class="spinner-border spinner-border-sm me-1" role="status"></div>
          Archivo recibido. Procesando en segundo plano...
        </div>
        <div id="etl-status-msg" style="font-size:0.85rem; color:#8899aa;">Iniciando...</div>
      </div>
    </div>
  `;

  etlPollInterval = setInterval(async () => {
    try {
      const res = await authFetch('/api/etl/status/');
      if (!res) return;
      const data = await res.json();

      const msgEl = document.getElementById('etl-status-msg');
      if (msgEl) {
        const detalle = data.detalle ? ` - ${data.detalle}` : '';
        msgEl.textContent = `[${data.fase || '...'}] ${data.mensaje || ''}${detalle}`;
      }

      if (!data.activo) {
        clearInterval(etlPollInterval);
        etlPollInterval = null;
        await cargarResultadoFinal();
        cargarHistorial();
        cargarEstadisticasReales();
      }
    } catch(e) {
      console.error('Polling error:', e);
    }
  }, 1500);
}

async function cargarResultadoFinal() {
  try {
    const res = await authFetch('/api/etl/historial/');
    if (!res) return;
    const items = await res.json();
    if (items && items.length > 0) {
      mostrarResultado(items[0]);
    }
  } catch(e) {
    console.error('Error cargando resultado final:', e);
  }
}

function mostrarAceptado(data) {
  const resultado = document.getElementById('etl-resultado');
  resultado.classList.add('active');

  const badge = document.getElementById('etl-status-badge');
  badge.className = 'etl-status-badge etl-status--proceso';
  badge.textContent = 'En cola';

  document.getElementById('etl-metricas').innerHTML = `
    <div style="grid-column: 1 / -1;">
      <div style="background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.15); border-radius:12px; padding:1.25rem; color:#1a2635;">
        <div style="font-weight:700; margin-bottom:0.4rem; color:#059669;">
          <i class="bi bi-check-circle-fill me-1"></i>Archivo recibido correctamente
        </div>
        <div style="font-size:0.85rem; color:#8899aa;">${data.message || 'Procesando en segundo plano...'}</div>
      </div>
    </div>
  `;
}

function handleFileSelect(input) {
  const zone = document.getElementById('upload-zone');
  const displayName = document.getElementById('file-name-display');
  if (input.files.length) {
    zone.classList.add('has-file');
    displayName.textContent = input.files[0].name;
  } else {
    zone.classList.remove('has-file');
  }
}

function mostrarErrorDetallado(data, statusCode) {
  if (etlPollInterval) { clearInterval(etlPollInterval); etlPollInterval = null; }

  const resultado = document.getElementById('etl-resultado');
  resultado.classList.add('active');

  const badge = document.getElementById('etl-status-badge');
  badge.className = 'etl-status-badge etl-status--error';
  badge.textContent = 'Error';

  const detalle = data.detalle || data.message || data.error || 'Error desconocido';
  const tipo = data.tipo || 'Error';

  document.getElementById('etl-metricas').innerHTML = `
    <div style="grid-column: 1 / -1;">
      <div style="background:rgba(255,95,109,0.05); border:1px solid rgba(255,95,109,0.15); border-radius:12px; padding:1.25rem; color:#1a2635;">
        <div style="font-weight:700; margin-bottom:0.4rem; color:#ff375f;">
          <i class="bi bi-exclamation-triangle-fill me-1"></i>Error al subir archivo (${statusCode})
        </div>
        <div style="font-size:0.85rem; color:#8899aa;">${tipo}: ${detalle}</div>
      </div>
    </div>
  `;
  document.getElementById('etl-log').textContent = 'Sin log disponible';
}

function mostrarErrorConexion(mensaje) {
  if (etlPollInterval) { clearInterval(etlPollInterval); etlPollInterval = null; }

  const resultado = document.getElementById('etl-resultado');
  resultado.classList.add('active');

  const badge = document.getElementById('etl-status-badge');
  badge.className = 'etl-status-badge etl-status--error';
  badge.textContent = 'Error de conexion';

  document.getElementById('etl-metricas').innerHTML = `
    <div style="grid-column: 1 / -1;">
      <div style="background:rgba(249,115,22,0.05); border:1px solid rgba(249,115,22,0.15); border-radius:12px; padding:1.25rem; color:#1a2635;">
        <div style="font-weight:700; margin-bottom:0.4rem; color:#ea580c;">
          <i class="bi bi-wifi-off me-1"></i>Error de conexion
        </div>
        <div style="font-size:0.85rem; color:#8899aa;">${mensaje}</div>
      </div>
    </div>
  `;
  document.getElementById('etl-log').textContent = 'Sin log disponible';
}

function mostrarMensajeNoDataset() {
  const resultado = document.getElementById('etl-resultado');
  resultado.classList.add('active');
  const badge = document.getElementById('etl-status-badge');
  badge.className = 'etl-status-badge etl-status--pendiente';
  badge.textContent = 'Sin Dataset';
  document.getElementById('etl-metricas').innerHTML = `
    <div style="grid-column: 1 / -1;">
      <div style="background:rgba(16,229,204,0.05); border:1px solid rgba(16,229,204,0.15); border-radius:12px; padding:1.25rem; color:#1a2635;">
        <div style="font-weight:700; margin-bottom:0.4rem; color:#0bb8a4;">
          <i class="bi bi-cloud-arrow-up me-1"></i>Sube un dataset primero
        </div>
        <div style="font-size:0.85rem; color:#8899aa;">
          Usa el panel "Subir Dataset" de la derecha para cargar un archivo CSV o Excel.
          El ETL se ejecutará automáticamente al subirlo.
        </div>
      </div>
    </div>
  `;
  document.getElementById('etl-log').textContent = '';
}

function mostrarResultado(data) {
  const sec = document.getElementById('etl-resultado');
  sec.classList.add('active');

  const badge = document.getElementById('etl-status-badge');
  if (data.estado === 'completado') {
    badge.className = 'etl-status-badge etl-status--completado';
    badge.textContent = 'Completado';
  } else {
    badge.className = 'etl-status-badge etl-status--error';
    badge.textContent = 'Error';
  }

  document.getElementById('etl-metricas').innerHTML = `
    <div class="etl-metric-item">
      <div class="value">${data.registros_entrada ?? 0}</div>
      <div class="label">Registros Entrada</div>
    </div>
    <div class="etl-metric-item etl-metric-item--limpios">
      <div class="value">${data.registros_limpios ?? 0}</div>
      <div class="label">Registros Limpios</div>
    </div>
    <div class="etl-metric-item etl-metric-item--duplicados">
      <div class="value">${data.duplicados_eliminados ?? 0}</div>
      <div class="label">Duplicados</div>
    </div>
    <div class="etl-metric-item etl-metric-item--tiempo">
      <div class="value">${data.tiempo_ejecucion_seg ?? 0}s</div>
      <div class="label">Tiempo</div>
    </div>
  `;

  document.getElementById('etl-log').textContent = data.log_detalle || 'Sin log disponible';
}

async function cargarEstadisticasReales() {
  try {
    const res = await authFetch('/api/etl/stats/');
    if (!res || !res.ok) return;
    const stats = await res.json();

    animateValue('stat-total-ejec', stats.total_ejecuciones || 0);
    animateValue('stat-total-limpios', stats.total_limpios || 0);
    animateValue('stat-total-duplicados', stats.total_duplicados || 0);
    document.getElementById('stat-promedio-tiempo').textContent =
      (stats.promedio_tiempo || 0) + 's';
  } catch(e) {
    console.error('Error cargando stats ETL:', e);
  }
}

async function cargarHistorial() {
  try {
    const res = await authFetch('/api/etl/historial/');
    if (!res) return;
    const data = await res.json();

    const tbody = document.getElementById('historial-tbody');

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="7">
        <div class="empty-state">
          <i class="bi bi-inbox"></i>
          Sin registros ETL
        </div>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(r => `
      <tr>
        <td style="font-size:0.82rem;">${formatFecha(r.fecha_ejecucion)}</td>
        <td style="font-size:0.82rem;">${r.usuario_nombre || '---'}</td>
        <td><span style="background:rgba(136,153,170,0.12); color:#5a6577; padding:0.25rem 0.6rem; border-radius:6px; font-size:0.75rem; font-weight:600;">${r.registros_entrada}</span></td>
        <td><span style="background:rgba(16,185,129,0.1); color:#059669; padding:0.25rem 0.6rem; border-radius:6px; font-size:0.75rem; font-weight:600;">${r.registros_limpios}</span></td>
        <td><span style="background:rgba(249,115,22,0.1); color:#ea580c; padding:0.25rem 0.6rem; border-radius:6px; font-size:0.75rem; font-weight:600;">${r.duplicados_eliminados}</span></td>
        <td style="font-size:0.82rem; color:#8899aa;">${r.tiempo_ejecucion_seg}s</td>
        <td><span class="etl-status-badge ${badgeEstado(r.estado)}">${r.estado}</span></td>
      </tr>
    `).join('');
  } catch(e) {
    console.error('Error historial:', e);
  }
}

function animateValue(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  const diff = target - start;
  if (diff === 0) return;
  const duration = 600;
  const startTime = performance.now();

  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + diff * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function formatFecha(f) {
  return f ? new Date(f).toLocaleString('es-CO', { dateStyle:'short', timeStyle:'short' }) : '---';
}

function badgeEstado(e) {
  const map = {
    completado: 'etl-status--completado',
    error: 'etl-status--error',
    en_proceso: 'etl-status--proceso',
    pendiente: 'etl-status--pendiente'
  };
  return map[e] || 'etl-status--pendiente';
}

async function resetData() {
  if (!confirm('Esto eliminara todos los pacientes, historial ETL y KPIs. Continuar?')) return;

  const btn = document.getElementById('btn-reset-data');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>Restableciendo...';

  try {
    const res = await authFetch('/api/etl/reset/', { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      alert(data.message || 'Datos restablecidos correctamente');
      cargarHistorial();
      cargarEstadisticasReales();
    } else {
      alert('Error: ' + (data.error || 'Error desconocido'));
    }
  } catch(e) {
    alert('Error de conexion: ' + e.message);
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="bi bi-trash3"></i>Restablecer Datos';
}

document.addEventListener('DOMContentLoaded', () => {
  cargarEstadisticasReales();
  cargarHistorial();
});
