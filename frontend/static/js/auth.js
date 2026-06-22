/* auth.js — Gestion de tokens JWT y proteccion de rutas */

const API = '/api';

function getToken() { return localStorage.getItem('access'); }
function getRefresh() { return localStorage.getItem('refresh'); }

async function authFetch(url, options = {}) {
  options.headers = options.headers || {};
  options.headers['Authorization'] = `Bearer ${getToken()}`;

  if (!(options.body instanceof FormData)) {
    options.headers['Content-Type'] = options.headers['Content-Type'] || 'application/json';
  }

  let res = await fetch(url, options);

  if (res.status === 401) {
    const refreshRes = await fetch(`${API}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: getRefresh() })
    });
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      localStorage.setItem('access', data.access);
      options.headers['Authorization'] = `Bearer ${data.access}`;
      res = await fetch(url, options);
    } else {
      cerrarSesion();
      return null;
    }
  }
  return res;
}

function cerrarSesion() {
  localStorage.clear();
  window.location.href = '/login/';
}

(function protegerRuta() {
  const rutasPublicas = ['/login/'];
  if (!rutasPublicas.includes(window.location.pathname) && !getToken()) {
    window.location.href = '/login/';
  }

  const nombres = localStorage.getItem('nombres') || localStorage.getItem('username') || '—';
  const rolDisplay = localStorage.getItem('rol_display') || localStorage.getItem('rol') || '';

  const el = document.getElementById('usuario-nombre');
  if (el) el.innerHTML = `${nombres}<br><span style="font-size:0.7rem;color:#6b7280;">${rolDisplay}</span>`;

  const elRol = document.getElementById('usuario-rol');
  if (elRol) elRol.textContent = rolDisplay;

  const avatar = document.getElementById('user-avatar-inicial');
  if (avatar) avatar.textContent = (username && username !== '—') ? username.charAt(0).toUpperCase() : 'U';
})();

function mostrarToast(mensaje, tipo = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const colors = { success: '#059669', error: '#dc2626', info: '#0bb8a4', warning: '#ea580c' };
  const bg = colors[tipo] || colors.info;
  const icon = { success: 'bi-check-circle-fill', error: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill', warning: 'bi-exclamation-circle-fill' };
  const toast = document.createElement('div');
  toast.className = 'toast align-items-center border-0 show';
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body" style="font-size:0.85rem;">
        <i class="bi ${icon[tipo] || icon.info} me-2"></i>${mensaje}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  toast.style.background = bg;
  toast.style.color = 'white';
  toast.style.borderRadius = '10px';
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 4000);
}

async function descargarArchivo(url, filename) {
  try {
    mostrarToast('Generando archivo...', 'info');
    const res = await authFetch(url);
    if (!res || !res.ok) {
      let msg = 'Error al descargar el archivo';
      try {
        const err = await res.json();
        if (err.error) msg = err.error;
      } catch(e) {}
      mostrarToast(msg, 'error');
      return;
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
    mostrarToast(`Descarga completada: ${filename}`, 'success');
  } catch (e) {
    console.error("Error descargando archivo:", e);
    mostrarToast('Error al descargar el archivo: ' + e.message, 'error');
  }
}
