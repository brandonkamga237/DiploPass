  // ── DATA ──────────────────────────────────────────────────────────────
  const ROLE_COLORS = {
    'Directeur': 'role-directeur',
    'Chef de service': 'role-chef-service',
    'Chef de bureau': 'role-chef-bureau',
    'Représentant filière': 'role-representant',
    'Admin Système': 'role-admin'
  };
  const AVATAR_COLORS = ['#25669e','#2da06e','#e8a020','#e07a20','#9a3a9a','#3a9aa0'];

  let users = [
    {id:1, nom:'NDJAKOMO ESSIANE', prenom:'Salomé', email:'directeur@enset.cm', role:'Directeur', filiere:'—', actif:true, created:'10/01/2026'},
    {id:2, nom:'MBARGA', prenom:'Paul', email:'css@enset.cm', role:'Chef de service', filiere:'Scolarité', actif:true, created:'12/01/2026'},
    {id:3, nom:'FOTSO', prenom:'Élise', email:'cb.info@enset.cm', role:'Chef de bureau', filiere:'Génie Informatique', actif:true, created:'15/01/2026'},
    {id:4, nom:'KAMGA', prenom:'David', email:'rf.info@enset.cm', role:'Représentant filière', filiere:'Génie Informatique', actif:true, created:'15/01/2026'},
    {id:5, nom:'NGONO', prenom:'Marie', email:'rf.elec@enset.cm', role:'Représentant filière', filiere:'Génie Électrique', actif:false, created:'20/01/2026'},
    {id:6, nom:'AWONO', prenom:'Cédric', email:'cb.civil@enset.cm', role:'Chef de bureau', filiere:'Génie Civil', actif:true, created:'22/01/2026'},
  ];
  let importHistory = [
    {file:'finissants_ginfo.json', date:'15/01/2026', count:312, status:'ok'},
    {file:'finissants_gelec.json', date:'15/01/2026', count:198, status:'ok'},
  ];
  let currentFilter = 'tous';
  let confirmCallback = null;
  let nextId = 7;

  // ── SIDEBAR TOGGLE ────────────────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const topbar  = document.getElementById('topbar');
  const mainEl  = document.getElementById('main');
  const overlay = document.getElementById('sidebarOverlay');

  document.getElementById('sidebarToggle').addEventListener('click', () => {
    const isMobile = window.innerWidth < 992;
    if (isMobile) {
      sidebar.classList.toggle('mobile-open');
      overlay.classList.toggle('show');
    } else {
      sidebar.classList.toggle('collapsed');
      topbar.classList.toggle('sidebar-collapsed');
      mainEl.classList.toggle('sidebar-collapsed');
    }
  });
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('show');
  });

  // ── SECTIONS ──────────────────────────────────────────────────────────
  function showSection(name) {
    ['overview','comptes','import'].forEach(s => {
      document.getElementById('section-'+s).style.display = (s === name) ? '' : 'none';
    });
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => l.classList.remove('active'));
    if (name === 'comptes') renderUsers();
    if (name === 'import') renderImportHistory();
  }

  // ── AVATAR ────────────────────────────────────────────────────────────
  function initials(u) {
    return (u.nom[0]||'')+(u.prenom[0]||'');
  }
  function avatarColor(u) {
    return AVATAR_COLORS[u.id % AVATAR_COLORS.length];
  }

  // ── RENDER USERS TABLE ────────────────────────────────────────────────
  function renderUsers(filter) {
    if (filter !== undefined) currentFilter = filter;
    const search = (document.getElementById('searchInput')?.value||'').toLowerCase();
    let list = users.filter(u => {
      const matchRole = (currentFilter === 'tous') || u.role === currentFilter;
      const matchSearch = !search || (u.nom+' '+u.prenom+' '+u.email).toLowerCase().includes(search);
      return matchRole && matchSearch;
    });

    const tbody = document.getElementById('users-table-body');
    const empty = document.getElementById('empty-state');
    if (!list.length) { tbody.innerHTML=''; empty.style.display=''; return; }
    empty.style.display='none';

    tbody.innerHTML = list.map(u => `
      <tr id="row-${u.id}">
        <td>
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="avatar-sm" style="background:${avatarColor(u)}">${initials(u)}</div>
            <div>
              <div style="font-weight:600;font-size:.85rem;">${u.nom} ${u.prenom}</div>
              <div style="font-size:.74rem;color:var(--gris-dark);">${u.email}</div>
            </div>
          </div>
        </td>
        <td><span class="badge-role ${ROLE_COLORS[u.role]||''}">${u.role}</span></td>
        <td style="font-size:.82rem;color:var(--gris-dark);">${u.filiere}</td>
        <td><span class="badge-status ${u.actif ? 'badge-actif' : 'badge-inactif'}">${u.actif ? 'Actif' : 'Inactif'}</span></td>
        <td>
          <div class="action-btns">
            <button class="btn-icon-sm edit" title="Modifier" onclick="editUser(${u.id})"><i class="bi bi-pencil-fill"></i></button>
            <button class="btn-icon-sm deactivate" title="${u.actif ? 'Désactiver' : 'Activer'}" onclick="toggleUser(${u.id})"><i class="bi bi-${u.actif ? 'pause-fill' : 'play-fill'}"></i></button>
            <button class="btn-icon-sm delete" title="Supprimer" onclick="confirmDelete(${u.id})"><i class="bi bi-trash3-fill"></i></button>
          </div>
        </td>
      </tr>
    `).join('');

    updateStats();
  }

  function filterUsers() { renderUsers(); }

  document.getElementById('filter-tabs').addEventListener('click', e => {
    const btn = e.target.closest('.filter-tab');
    if (!btn) return;
    document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderUsers(btn.dataset.role);
  });

  // ── STATS ─────────────────────────────────────────────────────────────
  function updateStats() {
    document.getElementById('stat-actif').textContent = users.filter(u=>u.actif).length;
    document.getElementById('stat-inactif').textContent = users.filter(u=>!u.actif).length;
  }

  // ── RECENT ACCOUNTS ───────────────────────────────────────────────────
  function renderRecentAccounts() {
    const recent = [...users].reverse().slice(0,4);
    document.getElementById('recent-accounts-body').innerHTML = recent.map(u => `
      <tr>
        <td>
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="avatar-sm" style="background:${avatarColor(u)}">${initials(u)}</div>
            <div>
              <div style="font-weight:600;font-size:.85rem;">${u.nom} ${u.prenom}</div>
              <div style="font-size:.74rem;color:var(--gris-dark);">${u.email}</div>
            </div>
          </div>
        </td>
        <td><span class="badge-role ${ROLE_COLORS[u.role]||''}">${u.role}</span></td>
        <td style="font-size:.82rem;color:var(--gris-dark);">${u.created}</td>
        <td><span class="badge-status ${u.actif ? 'badge-actif' : 'badge-inactif'}">${u.actif ? 'Actif' : 'Inactif'}</span></td>
        <td></td>
      </tr>
    `).join('');
  }

  // ── CREATE ACCOUNT ────────────────────────────────────────────────────
  const createModalEl = document.getElementById('createModal');
  const createModal = new bootstrap.Modal(createModalEl);

  function openCreateModal() { createModal.show(); }

  function toggleFiliereField() {
    const role = document.getElementById('f-role').value;
    document.getElementById('filiere-field').style.display =
      (role === 'Chef de bureau' || role === 'Représentant filière') ? '' : 'none';
  }

  function togglePwd() {
    const inp = document.getElementById('f-password');
    const eye = document.getElementById('pwd-eye');
    if (inp.type === 'password') { inp.type='text'; eye.className='bi bi-eye-slash'; }
    else { inp.type='password'; eye.className='bi bi-eye'; }
  }

  function createAccount() {
    const nom = document.getElementById('f-nom').value.trim().toUpperCase();
    const prenom = document.getElementById('f-prenom').value.trim();
    const email = document.getElementById('f-email').value.trim();
    const role = document.getElementById('f-role').value;
    const filiere = document.getElementById('f-filiere')?.value || '—';
    const pwd = document.getElementById('f-password').value;

    if (!nom || !prenom || !email || !role || !pwd) {
      showToast('Veuillez remplir tous les champs obligatoires.', 'error'); return;
    }
    if (users.find(u=>u.email===email)) {
      showToast('Cette adresse email est déjà utilisée.', 'error'); return;
    }

    const today = new Date().toLocaleDateString('fr-FR');
    users.push({id:nextId++, nom, prenom, email, role, filiere: filiere||'—', actif:true, created:today});
    createModal.hide();
    // reset
    ['f-nom','f-prenom','f-email','f-password'].forEach(id => document.getElementById(id).value='');
    document.getElementById('f-role').value='';
    document.getElementById('filiere-field').style.display='none';

    updateStats();
    renderRecentAccounts();
    showToast(`Compte de ${prenom} ${nom} créé avec succès.`, 'success');
  }

  // ── TOGGLE USER ───────────────────────────────────────────────────────
  function toggleUser(id) {
    const u = users.find(x=>x.id===id);
    if (!u) return;
    if (u.actif) {
      openConfirm(
        'warning',
        'bi bi-pause-fill',
        `Désactiver ${u.prenom} ${u.nom} ?`,
        'L\'utilisateur ne pourra plus se connecter au système.',
        'Désactiver',
        () => { u.actif = false; renderUsers(); renderRecentAccounts(); showToast(`Compte de ${u.prenom} ${u.nom} désactivé.`, 'warning'); }
      );
    } else {
      u.actif = true;
      renderUsers(); renderRecentAccounts();
      showToast(`Compte de ${u.prenom} ${u.nom} réactivé.`, 'success');
    }
  }

  // ── DELETE USER ───────────────────────────────────────────────────────
  function confirmDelete(id) {
    const u = users.find(x=>x.id===id);
    if (!u) return;
    openConfirm(
      'danger',
      'bi bi-trash3-fill',
      `Supprimer le compte de ${u.prenom} ${u.nom} ?`,
      'Cette action est irréversible. Le compte sera définitivement supprimé.',
      'Supprimer',
      () => {
        users = users.filter(x=>x.id!==id);
        renderUsers(); renderRecentAccounts();
        showToast(`Compte supprimé.`, 'success');
      }
    );
  }

  function editUser(id) {
    showToast('Fonctionnalité de modification à venir.', 'warning');
  }

  // ── CONFIRM OVERLAY ───────────────────────────────────────────────────
  function openConfirm(type, icon, title, msg, btnLabel, cb) {
    const el = document.getElementById('confirmOverlay');
    const iconEl = document.getElementById('confirm-icon-el');
    const iconI = document.getElementById('confirm-icon-i');
    const btn = document.getElementById('confirm-action-btn');
    iconEl.className = `confirm-icon ${type}`;
    iconI.className = `bi ${icon}`;
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-msg').textContent = msg;
    btn.textContent = btnLabel;
    btn.className = type === 'danger' ? 'btn-danger-custom px-4 py-2' : 'btn-primary-custom px-4 py-2';
    confirmCallback = cb;
    el.classList.add('show');
  }
  function closeConfirm() { document.getElementById('confirmOverlay').classList.remove('show'); confirmCallback=null; }
  document.getElementById('confirm-action-btn').addEventListener('click', () => {
    if (confirmCallback) { confirmCallback(); closeConfirm(); }
  });

  // ── IMPORT ────────────────────────────────────────────────────────────
  const dropZone = document.getElementById('dropZone');
  let importedData = null;

  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  });
  dropZone.addEventListener('click', () => document.getElementById('fileInput').click());

  function handleFileSelect(input) { if (input.files[0]) processFile(input.files[0]); }

  function processFile(file) {
    if (!file.name.endsWith('.json')) { showToast('Format invalide. Veuillez sélectionner un fichier .json', 'error'); return; }
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const data = JSON.parse(e.target.result);
        if (!Array.isArray(data)) throw new Error('Le fichier doit contenir un tableau JSON.');
        importedData = data;
        dropZone.classList.add('has-file');
        document.getElementById('file-name').textContent = file.name;
        document.getElementById('file-info').textContent = `${data.length} entrées · ${(file.size/1024).toFixed(1)} Ko`;
        renderJsonSummary(data);
        document.getElementById('file-preview').style.display = '';
      } catch(err) { showToast('Fichier JSON invalide : '+err.message, 'error'); }
    };
    reader.readAsText(file);
  }

  function renderJsonSummary(data) {
    const filieres = {};
    data.forEach(e => { const f = e.filiere||'Inconnue'; filieres[f]=(filieres[f]||0)+1; });
    const rows = Object.entries(filieres).map(([f,c]) => `
      <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--gris-bg);font-size:.83rem;">
        <span style="color:var(--dark);">${f}</span>
        <span style="font-weight:600;color:var(--blue);">${c} étudiants</span>
      </div>
    `).join('');
    document.getElementById('json-summary').innerHTML = `
      <div style="background:#f8f9fb;border-radius:10px;padding:14px;">
        <div style="font-size:.75rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--gris-dark);margin-bottom:8px;">Aperçu par filière</div>
        ${rows}
        <div style="display:flex;justify-content:space-between;padding:8px 0 0;font-size:.85rem;font-weight:700;">
          <span>Total</span><span style="color:var(--green);">${data.length} étudiants</span>
        </div>
      </div>`;
  }

  function clearFile() {
    importedData = null;
    document.getElementById('fileInput').value='';
    document.getElementById('file-preview').style.display='none';
    dropZone.classList.remove('has-file');
  }

  function launchImport() {
    if (!importedData) return;
    const today = new Date().toLocaleDateString('fr-FR');
    importHistory.unshift({file: document.getElementById('file-name').textContent, date:today, count:importedData.length, status:'ok'});
    document.getElementById('stat-etudiants').textContent = (1240 + importedData.length).toLocaleString('fr-FR');
    clearFile();
    renderImportHistory();
    showToast(`${importedData ? importedData.length : 0} étudiants importés avec succès.`, 'success');
    importedData = null;
  }

  function renderImportHistory() {
    const el = document.getElementById('import-history');
    if (!importHistory.length) { el.innerHTML='<p style="font-size:.82rem;color:var(--gris-dark);">Aucun import effectué.</p>'; return; }
    el.innerHTML = importHistory.map(h => `
      <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--gris-bg);">
        <div style="width:36px;height:36px;background:#e6f5ef;border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--green);font-size:1rem;flex-shrink:0;">
          <i class="bi bi-file-earmark-check-fill"></i>
        </div>
        <div style="flex:1;">
          <div style="font-size:.84rem;font-weight:600;color:var(--dark);">${h.file}</div>
          <div style="font-size:.73rem;color:var(--gris-dark);">${h.count} entrées · ${h.date}</div>
        </div>
        <span class="badge-status badge-actif">OK</span>
      </div>
    `).join('');
  }

  // ── TOAST ─────────────────────────────────────────────────────────────
  function showToast(msg, type='success') {
    const icons = {success:'check-circle-fill', error:'x-circle-fill', warning:'exclamation-triangle-fill'};
    const colors = {success:'var(--green)', error:'var(--red)', warning:'var(--yellow)'};
    const t = document.createElement('div');
    t.className = `toast-custom ${type !== 'success' ? type : ''}`;
    t.style.borderLeftColor = colors[type]||colors.success;
    t.innerHTML = `<i class="bi bi-${icons[type]||icons.success}" style="color:${colors[type]};font-size:1.1rem;flex-shrink:0;"></i><span>${msg}</span>`;
    document.getElementById('toastContainer').appendChild(t);
    setTimeout(() => { t.style.opacity='0'; t.style.transition='opacity .3s'; setTimeout(()=>t.remove(),300); }, 3500);
  }

  // ── INIT ──────────────────────────────────────────────────────────────
  updateStats();
  renderRecentAccounts();