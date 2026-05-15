window.onload = () => {

    console.log('Sistema iniciado')

    loadClientes()
    loadOrdenes()
    loadTecnicos()
    cargarTecnicosSelect()
}

// ═══════════════════════════════════════════
//  ESTADO GLOBAL
// ═══════════════════════════════════════════
let editingId=null,currentMode='anio',editingCli=null,currentModalId=null;
let pendingImages=[],ramCount=0,discoCount=0,fallaCount=0,presCount=0;
let ordersPage=1,histPage=1;
const PAGE_LIMIT=50;
const CACHE_MS=30000;
const apiCache=new Map();
const MESES=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

// ═══════════════════════════════════════════
//  UTILS
// ═══════════════════════════════════════════
const gv=id=>{const e=document.getElementById(id);return e?e.value.trim():'';}
const sv=(id,v)=>{const e=document.getElementById(id);if(e){e.value=v||'';}}
function toast(msg,type=''){const t=document.createElement('div');t.className='toast '+(type||'');t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),3200);}
async function fetchJson(url,useCache=true){
  const now=Date.now(),hit=apiCache.get(url);
  if(useCache&&hit&&now-hit.ts<CACHE_MS)return hit.data;
  const data=await fetch(url).then(r=>r.json());
  if(useCache)apiCache.set(url,{ts:now,data});
  return data;
}
function clearApiCache(){apiCache.clear();}
function loadingHtml(){return '<div class="loading"><i class="ti ti-loader-2"></i> Cargando...</div>';}
function renderPager(id,page,pages,fn){
  const el=document.getElementById(id);if(!el)return;
  if(pages<=1){el.innerHTML='';return;}
  el.innerHTML=`
    <button class="btn btn-sm" ${page<=1?'disabled':''} onclick="${fn}(${page-1})"><i class="ti ti-chevron-left"></i></button>
    <span>Página ${page} de ${pages}</span>
    <button class="btn btn-sm" ${page>=pages?'disabled':''} onclick="${fn}(${page+1})"><i class="ti ti-chevron-right"></i></button>`;
}
function showPage(p){
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.getElementById('page-'+p).classList.add('active');
  document.getElementById('tab-'+p).classList.add('active');
  if(p==='dashboard') { loadDashboardPending(); }
  if(p==='ordenes')   { cargarTecnicosSelect(); loadOrdenes(); }
  if(p==='clientes')  loadClientes();
  if(p==='historial') initHistorial();
  if(p==='nueva'&&!editingId) { fetchNextNum(); cargarTecnicosSelect(); }
  if(p==='configuracion') { cargarConfiguracion(); loadTecnicos(); }
}
function fetchNextNum(){
  fetch('/api/ordenes?page=1&limit=1')
    .then(r=>r.json())
    .then(data=>{
      const lastId = (data.items && data.items[0]) ? data.items[0].id : 0;
      const next = String(lastId + 1).padStart(4, '0');
      document.getElementById('orden-num-prev').textContent = 'Próximo: OT-' + next;
    })
    .catch(()=>{});
}
function showStep(n){
  document.querySelectorAll('.step-panel').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.stab').forEach(x=>x.classList.remove('active'));
  document.getElementById('step'+n).classList.add('active');
  document.getElementById('stab'+n).classList.add('active');
}

// ═══════════════════════════════════════════
//  THEME TOGGLE
// ═══════════════════════════════════════════
function toggleTheme() {
  const isDark = document.body.classList.toggle('dark-theme');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  document.getElementById('theme-toggle').innerHTML = isDark ? '<i class="ti ti-sun"></i>' : '<i class="ti ti-moon"></i>';
}
// Init Theme
if(localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark-theme');
  document.getElementById('theme-toggle').innerHTML = '<i class="ti ti-sun"></i>';
}

// ═══════════════════════════════════════════
//  RADIOS
// ═══════════════════════════════════════════
const RADIO_3=[{val:'ok',lbl:'✓ OK',cls:'ro-ok'},{val:'falla',lbl:'✗ Falla',cls:'ro-falla'},{val:'na',lbl:'N/A',cls:'ro-na'}];
const RADIO_SI=[{val:'si',lbl:'✓ Sí',cls:'ro-ok'},{val:'no',lbl:'✗ No',cls:'ro-falla'},{val:'na',lbl:'N/A',cls:'ro-na'}];
const RADIO_BIOS=[{val:'si_actualizado',lbl:'✓ Sí, actualizado',cls:'ro-ok'},{val:'no_necesario',lbl:'No es necesario',cls:'ro-na'},{val:'pendiente',lbl:'Pendiente',cls:'ro-falla'}];
function buildRadios(id,opts){
  const c=document.getElementById(id);if(!c)return;
  c.innerHTML=opts.map(o=>`<label class="radio-opt" id="rl-${id}-${o.val}"><input type="radio" name="${id}" value="${o.val}" onchange="styleRadio('${id}')">${o.lbl}</label>`).join('');
}
function styleRadio(name){
  document.querySelectorAll(`[name="${name}"]`).forEach(r=>{
    const l=r.parentElement; l.classList.remove('ro-ok','ro-falla','ro-na');
    if(r.checked){if(r.value==='ok'||r.value==='si'||r.value==='si_actualizado')l.classList.add('ro-ok');else if(r.value==='falla'||r.value==='no'||r.value==='pendiente')l.classList.add('ro-falla');else l.classList.add('ro-na');}
  });
}
function getRadio(name){const r=document.querySelector(`[name="${name}"]:checked`);return r?r.value:'na';}
function setRadio(name,val){const r=document.querySelector(`[name="${name}"][value="${val}"]`);if(r){r.checked=true;styleRadio(name);}}
function initAllRadios(){
  ['r-carcasa','r-pantalla','r-teclado-vis','r-puertos','r-bisagras'].forEach(id=>buildRadios(id,RADIO_3));
  buildRadios('r-cargador-inc',RADIO_SI);
  ['r-enc-bat','r-enc-car','r-carga-so','r-teclado-fn','r-audio','r-display','r-touchpad','r-wifi','r-usb','r-camara'].forEach(id=>buildRadios(id,RADIO_3));
  buildRadios('r-bios-estado',RADIO_BIOS);
}

// ═══════════════════════════════════════════
//  DYNAMIC RAM
// ═══════════════════════════════════════════
function addRam(data={}){
  ramCount++;const n=ramCount;
  const tr=document.createElement('tr');tr.id='ram-row-'+n;
  tr.innerHTML=`<td style="text-align:center;font-weight:600;color:var(--blue)">${n}</td>
    <td><input placeholder="8 GB" data-f="capacidad" value="${data.capacidad||''}"></td>
    <td><select data-f="tipo_ram"><option value="">—</option>${['DDR3','DDR4','DDR5','LPDDR4','LPDDR5'].map(x=>`<option${data.tipo_ram===x?' selected':''}>${x}</option>`).join('')}</select></td>
    <td><input placeholder="3200 MHz" data-f="velocidad" value="${data.velocidad||''}"></td>
    <td><input placeholder="S/N módulo" data-f="serie" value="${data.serie||''}" style="min-width:90px"></td>
    <td><input placeholder="2" data-f="pases" value="${data.pases||''}" style="width:45px"></td>
    <td><input placeholder="45 min" data-f="duracion_test" value="${data.duracion_test||''}"></td>
    <td><select data-f="resultado"><option value="">—</option><option${data.resultado==='PASS'?' selected':''} style="color:var(--green)">PASS</option><option${data.resultado==='FAIL'?' selected':''} style="color:var(--red)">FAIL</option><option${data.resultado==='No testeado'?' selected':''}>No testeado</option></select></td>
    <td><button class="btn btn-xs btn-danger" onclick="removeRow('ram-row-${n}')"><i class="ti ti-trash"></i></button></td>`;
  document.getElementById('ram-tbody').appendChild(tr);
}
function getRamData(){return Array.from(document.querySelectorAll('#ram-tbody tr')).map(tr=>{const g=f=>tr.querySelector(`[data-f="${f}"]`)?.value||'';return{capacidad:g('capacidad'),tipo_ram:g('tipo_ram'),velocidad:g('velocidad'),serie:g('serie'),pases:g('pases'),duracion_test:g('duracion_test'),resultado:g('resultado')};});}

// ═══════════════════════════════════════════
//  DYNAMIC DISCOS
// ═══════════════════════════════════════════
function addDisco(data={}){
  discoCount++;const n=discoCount;
  const tr=document.createElement('tr');tr.id='disco-row-'+n;
  tr.innerHTML=`<td style="text-align:center;font-weight:600;color:var(--blue)">${n}</td>
    <td><input placeholder="Samsung" data-f="marca" value="${data.marca||''}"></td>
    <td><select data-f="tipo"><option value="">—</option>${['HDD','SSD SATA','NVMe M.2','eMMC','SSD M.2 SATA'].map(x=>`<option${data.tipo===x?' selected':''}>${x}</option>`).join('')}</select></td>
    <td><input placeholder="512 GB" data-f="capacidad" value="${data.capacidad||''}"></td>
    <td><input placeholder="S/N disco" data-f="serie" value="${data.serie||''}" style="min-width:90px"></td>
    <td><select data-f="smart"><option value="">—</option><option${data.smart==='Good'?' selected':''} style="color:var(--green)">Good</option><option${data.smart==='Warning'?' selected':''} style="color:var(--amber)">Warning</option><option${data.smart==='Bad'?' selected':''} style="color:var(--red)">Bad</option><option${data.smart==='No aplica'?' selected':''}>No aplica</option></select></td>
    <td><input placeholder="2500 h" data-f="horas" value="${data.horas||''}" style="width:65px"></td>
    <td><input placeholder="0" data-f="apagados" type="number" value="${data.apagados||''}" style="width:52px"></td>
    <td><input placeholder="0" data-f="sectores" type="number" value="${data.sectores||''}" style="width:52px"></td>
    <td><select data-f="rendimiento"><option value="">—</option>${['Normal','Degradado','Bajo'].map(x=>`<option${data.rendimiento===x?' selected':''}>${x}</option>`).join('')}</select></td>
    <td><input placeholder="550 MB/s" data-f="lectura_max" value="${data.lectura_max||''}" style="width:80px"></td>
    <td><input placeholder="350 MB/s" data-f="lectura_media" value="${data.lectura_media||''}" style="width:80px"></td>
    <td><input placeholder="100 MB/s" data-f="lectura_baja" value="${data.lectura_baja||''}" style="width:80px"></td>
    <td><button class="btn btn-xs btn-danger" onclick="removeRow('disco-row-${n}')"><i class="ti ti-trash"></i></button></td>`;
  document.getElementById('disco-tbody').appendChild(tr);
}
function getDiscoData(){return Array.from(document.querySelectorAll('#disco-tbody tr')).map(tr=>{const g=f=>tr.querySelector(`[data-f="${f}"]`)?.value||'';return{marca:g('marca'),tipo:g('tipo'),capacidad:g('capacidad'),serie:g('serie'),smart:g('smart'),horas:g('horas'),apagados:g('apagados'),sectores:g('sectores'),rendimiento:g('rendimiento'),lectura_max:g('lectura_max'),lectura_media:g('lectura_media'),lectura_baja:g('lectura_baja')};});}

// ═══════════════════════════════════════════
//  DYNAMIC FALLAS
// ═══════════════════════════════════════════
function addFalla(data={}){
  fallaCount++;const n=fallaCount;
  const tr=document.createElement('tr');tr.id='falla-row-'+n;
  tr.innerHTML=`<td style="text-align:center;font-weight:600;color:var(--red)">${n}</td>
    <td><input placeholder="Describa la falla..." data-f="falla" value="${data.falla||''}" style="min-width:160px"></td>
    <td><input placeholder="Componente afectado" data-f="componente" value="${data.componente||''}" style="min-width:130px"></td>
    <td><select data-f="severidad"><option value="">—</option><option${data.severidad==='Alta'?' selected':''} style="color:var(--red)">Alta</option><option${data.severidad==='Media'?' selected':''} style="color:var(--amber)">Media</option><option${data.severidad==='Grave'?' selected':''} style="color:#7A0000">Grave</option></select></td>
    <td><select data-f="prioridad"><option value="">—</option>${['Inmediata','Próxima','Preventiva','Resuelta'].map(x=>`<option${data.prioridad===x?' selected':''}>${x}</option>`).join('')}</select></td>
    <td><button class="btn btn-xs btn-danger" onclick="removeRow('falla-row-${n}')"><i class="ti ti-trash"></i></button></td>`;
  document.getElementById('fallas-tbody').appendChild(tr);
}
function getFallasData(){return Array.from(document.querySelectorAll('#fallas-tbody tr')).map(tr=>{const g=f=>tr.querySelector(`[data-f="${f}"]`)?.value||'';return{falla:g('falla'),componente:g('componente'),severidad:g('severidad'),prioridad:g('prioridad')};});}

// ═══════════════════════════════════════════
//  DYNAMIC PRESUPUESTO
// ═══════════════════════════════════════════
function addPresItem(data={}){
  presCount++;const n=presCount;
  const moneda=gv('f-presupuesto-moneda')||'USD';
  const tr=document.createElement('tr');tr.id='pres-row-'+n;
  tr.innerHTML=`<td style="text-align:center;font-weight:600;color:var(--blue)">${n}</td>
    <td><input placeholder="Descripción del ítem..." data-f="descripcion" value="${data.descripcion||''}" style="min-width:200px"></td>
    <td><select data-f="tipo"><option value="">—</option>${['Componente','Servicio','Periférico','Repuesto','Otro'].map(x=>`<option${data.tipo===x?' selected':''}>${x}</option>`).join('')}</select></td>
    <td><div style="display:flex;align-items:center;gap:3px"><span style="font-size:11px;color:var(--text2)">${moneda}</span><input type="number" step="0.01" min="0" placeholder="0.00" data-f="precio" value="${data.precio||''}" style="width:80px" oninput="calcTotal()"></div></td>
    <td><button class="btn btn-xs btn-danger" onclick="removeRow('pres-row-${n}');calcTotal()"><i class="ti ti-trash"></i></button></td>`;
  document.getElementById('pres-tbody').appendChild(tr);
}
function getPresData(){return Array.from(document.querySelectorAll('#pres-tbody tr')).map(tr=>{const g=f=>tr.querySelector(`[data-f="${f}"]`)?.value||'';return{descripcion:g('descripcion'),tipo:g('tipo'),precio:parseFloat(g('precio'))||0};});}
function calcTotal(){
  const items=getPresData();
  const total=items.reduce((s,i)=>s+(parseFloat(i.precio)||0),0);
  const moneda=gv('f-presupuesto-moneda')||'USD';
  document.getElementById('pres-total').textContent=moneda+' '+total.toFixed(2);
}

function removeRow(id){const r=document.getElementById(id);if(r)r.remove();calcTotal();}

// ═══════════════════════════════════════════
//  IMAGE QUEUE
// ═══════════════════════════════════════════
function queueImages(input,seccion){
  Array.from(input.files).forEach(file=>{
    const idx=pendingImages.length;
    pendingImages.push({file,seccion,descripcion:''});
    const reader=new FileReader();
    reader.onload=e=>{
      const prev=document.getElementById('previews-'+seccion);
      const thumb=document.createElement('div');thumb.className='img-thumb';thumb.id='pimg-'+idx;
      thumb.innerHTML=`<img src="${e.target.result}"><button class="del-img" onclick="removePending(${idx})">✕</button><div class="img-label">${file.name}</div>`;
      prev.appendChild(thumb);
    };
    reader.readAsDataURL(file);
  });
  input.value='';
}
function removePending(idx){pendingImages[idx]=null;document.getElementById('pimg-'+idx)?.remove();}
async function uploadPendingImages(ordenId){
  for(const img of pendingImages.filter(Boolean)){
    const fd=new FormData();fd.append('file',img.file);fd.append('seccion',img.seccion);fd.append('descripcion',img.descripcion);
    await fetch(`/api/upload/${ordenId}`,{method:'POST',body:fd});
  }
}

// Render existing images in edit previews
function renderEditImages(containerId,imgs,isEdit=false){
  const cont=document.getElementById(containerId);if(!cont)return;
  imgs.forEach(img=>{
    const thumb=document.createElement('div');thumb.className='img-thumb';thumb.id='eimg-'+img.id;
    thumb.innerHTML=`<img src="/imagenes/${img.ruta}"><button class="del-img" onclick="deleteEditImage(${img.id},'eimg-${img.id}')">✕</button><div class="img-label">${img.descripcion||img.seccion}</div>`;
    cont.appendChild(thumb);
  });
}
async function deleteEditImage(imgId,thumbId){
  await fetch(`/api/imagenes/${imgId}`,{method:'DELETE'});
  document.getElementById(thumbId)?.remove();
}

// ═══════════════════════════════════════════
//  CLIENTES
// ═══════════════════════════════════════════
let currentPage = 1;
const perPage = 20;

async function loadClientes(page = 1){
  const q=document.getElementById('search-cli')?.value||'';
  currentPage = page;
  const res=await fetch(`/api/clientes?q=${encodeURIComponent(q)}&page=${page}&per_page=${perPage}`).then(r=>r.json());
  const list=res.data||[];
  const total=res.total||0;
  const pages=res.pages||1;
  const cont=document.getElementById('lista-clientes');
  if(!list.length){cont.innerHTML='<div class="empty"><i class="ti ti-users"></i><p>No hay clientes registrados</p></div>';return;}
  let html=list.map(c=>`
    <div class="order-row">
      <div class="avatar">${(c.nombres[0]||'?').toUpperCase()}</div>
      <div class="order-info">
        <div class="order-device">${c.nombres} ${c.apellidos}</div>
        <div class="order-client">CI: ${c.dni}${c.tel?' · '+c.tel:''}${c.email?' · '+c.email:''}</div>
      </div>
      <div class="order-actions">
        <button class="btn btn-sm" onclick="editarCliente(${c.id})"><i class="ti ti-edit"></i></button>
        <button class="btn btn-sm btn-danger" onclick="eliminarCliente(${c.id})"><i class="ti ti-trash"></i></button>
      </div>
    </div>`).join('');
  html+=`<div style="display:flex;justify-content:space-between;align-items:center;margin-top:15px;padding-top:15px;border-top:1px solid #eee"><div style="color:#666;font-size:13px">Mostrando ${list.length} de ${total} clientes</div><div style="display:flex;gap:8px"><button class="btn btn-sm" ${page<=1?'disabled':''} onclick="loadClientes(${page-1})" ${page<=1?'style="opacity:0.5;cursor:not-allowed"':''}><i class="ti ti-chevron-left"></i> Anterior</button><span style="display:flex;align-items:center;font-size:13px;color:#666">Página ${page} de ${pages}</span><button class="btn btn-sm" ${page>=pages?'disabled':''} onclick="loadClientes(${page+1})" ${page>=pages?'style="opacity:0.5;cursor:not-allowed"':''}>Siguiente <i class="ti ti-chevron-right"></i></button></div></div>`;
  cont.innerHTML=html;
}
async function guardarCliente(){
  const dni=gv('c-dni'),nombres=gv('c-nombres'),apellidos=gv('c-apellidos');
  if(!dni||!nombres||!apellidos){toast('Cédula, nombres y apellidos son obligatorios','error');return;}
  const data={dni,nombres,apellidos,tel:gv('c-tel'),email:gv('c-email'),ciudad:gv('c-ciudad'),dir:gv('c-dir')};
  const r=await fetch(editingCli?`/api/clientes/${editingCli}`:'/api/clientes',{method:editingCli?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  if(r.ok){clearApiCache();toast('Cliente guardado','success');limpiarCli();loadClientes(1);}
  else{const e=await r.json();toast(e.error||'Error','error');}
}
async function editarCliente(id){
  const res=await fetch('/api/clientes').then(r=>r.json());
  const list=res.data||[];
  const c=list.find(x=>x.id===id);if(!c)return;
  editingCli=id;
  sv('c-dni',c.dni);sv('c-nombres',c.nombres);sv('c-apellidos',c.apellidos);
  sv('c-tel',c.tel);sv('c-email',c.email);sv('c-ciudad',c.ciudad);sv('c-dir',c.dir);
  document.getElementById('cli-form-title').textContent='Editando: '+c.nombres+' '+c.apellidos;
  window.scrollTo(0,0);
}
async function eliminarCliente(id){
  if(!confirm('¿Eliminar este cliente?'))return;
  await fetch(`/api/clientes/${id}`,{method:'DELETE'});clearApiCache();toast('Cliente eliminado');loadClientes(currentPage);
}
function limpiarCli(){
  ['c-dni','c-nombres','c-apellidos','c-tel','c-email','c-ciudad','c-dir'].forEach(id=>sv(id,''));
  editingCli=null;document.getElementById('cli-form-title').textContent='Registrar nuevo cliente';
}


// ═══════════════════════════════════════════
//  TECNICOS - GESTIÓN
// ═══════════════════════════════════════════
let editingTec = null;
let tecnicosPage = 1;
const tecPerPage = 20;

async function loadTecnicos(page = 1) {
  const q = document.getElementById('search-tec')?.value || '';
  tecnicosPage = page;
  try {
    const res = await fetch(`/api/tecnicos`);
    let list = await res.json();

    // Filtrar manualmente si hay búsqueda
    if (q) {
      list = list.filter(t =>
        (t.dni && t.dni.includes(q)) ||
        (t.nombres && t.nombres.toLowerCase().includes(q.toLowerCase())) ||
        (t.apellidos && t.apellidos.toLowerCase().includes(q.toLowerCase()))
      );
    }

    const cont = document.getElementById('lista-tecnicos');
    if (!list.length) {
      cont.innerHTML = '<div class="empty"><i class="ti ti-user-x"></i><p>No hay técnicos registrados</p></div>';
      return;
    }

    let html = list.map(t => `
      <div class="order-row">
        <div class="avatar">${(t.nombres[0]||'?').toUpperCase()}</div>
        <div style="flex:1">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:500;font-size:13px">${t.nombres} ${t.apellidos}</div>
              <div style="font-size:11px;color:var(--text2)">CI: ${t.dni||'N/A'}${t.especialidad ? ' · '+t.especialidad : ''}${t.telefono ? ' · '+t.telefono : ''}</div>
            </div>
            <span class="badge ${t.activo==1?'bg-green':'bg-red'}">${t.activo==1?'Activo':'Inactivo'}</span>
          </div>
        </div>
        <div style="display:flex;gap:4px">
          <button class="btn btn-sm" onclick="editarTecnico(${t.id})"><i class="ti ti-edit"></i></button>
          <button class="btn btn-sm btn-danger" onclick="eliminarTecnico(${t.id})"><i class="ti ti-trash"></i></button>
        </div>
      </div>`).join('');

    cont.innerHTML = html;
  } catch (e) {
    console.error('Error cargando técnicos:', e);
  }
}

async function guardarTecnico() {
  const dni = gv('tec-dni');
  const nombres = gv('tec-nombres');
  const apellidos = gv('tec-apellidos');

  if (!nombres || !apellidos) {
    toast('Nombres y apellidos son obligatorios', 'error');
    return;
  }

  const data = {
    id: editingTec ? editingTec : null,
    dni: dni,
    nombres: nombres,
    apellidos: apellidos,
    especialidad: gv('tec-especialidad'),
    telefono: gv('tec-tel'),
    email: gv('tec-email'),
    activo: parseInt(gv('tec-activo'))
  };

  try {
    const res = await fetch('/api/tecnicos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });

    if (res.ok) {
      clearApiCache();
      toast('Técnico guardado correctamente', 'success');
      limpiarTec();
      loadTecnicos(1);
      cargarTecnicosSelect();
    } else {
      const e = await res.json();
      toast(e.error || 'Error al guardar', 'error');
    }
  } catch (e) {
    toast('Error de conexión: ' + e.message, 'error');
  }
}

async function editarTecnico(id) {
  try {
    const res = await fetch(`/api/tecnicos/${id}`);
    const t = await res.json();

    if (!t || t.error) return;

    editingTec = id;
    sv('tec-id', t.id);
    sv('tec-dni', t.dni || '');
    sv('tec-nombres', t.nombres);
    sv('tec-apellidos', t.apellidos);
    sv('tec-especialidad', t.especialidad || '');
    sv('tec-tel', t.telefono || '');
    sv('tec-email', t.email || '');
    sv('tec-activo', t.activo != null ? t.activo : 1);

    document.getElementById('tec-form-title').textContent = 'Editando: ' + t.nombres + ' ' + t.apellidos;
    window.scrollTo(0, 0);
  } catch (e) {
    console.error('Error cargando técnico:', e);
  }
}

async function eliminarTecnico(id) {
  if (!confirm('¿Eliminar este técnico?')) return;
  try {
    await fetch(`/api/tecnicos/${id}`, {method: 'DELETE'});
    clearApiCache();
    toast('Técnico eliminado correctamente');
    loadTecnicos(tecnicosPage);
    cargarTecnicosSelect();
  } catch (e) {
    toast('Error al eliminar: ' + e.message, 'error');
  }
}

function limpiarTec() {
  ['tec-id','tec-dni','tec-nombres','tec-apellidos','tec-especialidad','tec-tel','tec-email'].forEach(id=>sv(id,''));
  sv('tec-activo', '1');
  editingTec = null;
  document.getElementById('tec-form-title').textContent = 'Gestión de Técnicos';
}

async function cargarTecnicosSelect() {
  try {
    const res = await fetch('/api/tecnicos?activo=true');
    const tecnicos = await res.json();

    // Llenar el select del formulario de nueva orden (usa nombre completo)
    const selectForm = document.getElementById('f-tecnico');
    if (selectForm) {
      selectForm.innerHTML = '<option value="">-- Seleccionar técnico --</option>';
      tecnicos.forEach(t => {
        const nombreCompleto = `${t.nombres} ${t.apellidos}`;
        selectForm.innerHTML += `<option value="${nombreCompleto}">${nombreCompleto}${t.especialidad ? ' ('+t.especialidad+')' : ''}</option>`;
      });
    }

    // Llenar el select de filtro en la página de órdenes (usa nombre completo para coincidir con BD)
    const selectFilter = document.getElementById('filter-tec-ord');
    if (selectFilter) {
      const selectedValue = selectFilter.value;
      selectFilter.innerHTML = '<option value="">Todos los técnicos</option>';
      tecnicos.forEach(t => {
        const nombreCompleto = `${t.nombres} ${t.apellidos}`;
        selectFilter.innerHTML += `<option value="${nombreCompleto}">${nombreCompleto}</option>`;
      });
      if (selectedValue && tecnicos.some(t => `${t.nombres} ${t.apellidos}` === selectedValue)) {
        selectFilter.value = selectedValue;
      }
    }
  } catch (e) {
    console.error('Error cargando select de técnicos:', e);
  }
}

// ═══════════════════════════════════════════
//  BÚSQUEDA CLIENTE EN FORMULARIO
// ═══════════════════════════════════════════
async function buscarCli(){
  const q=document.getElementById('buscar-cli').value.trim();
  const cont=document.getElementById('cli-results');
  if(!q){cont.innerHTML='';return;}
  const res=await fetch(`/api/clientes?q=${encodeURIComponent(q)}`).then(r=>r.json());
  const list=res.data||[];
  if(!list.length){cont.innerHTML='<div style="font-size:11px;color:var(--text2);padding:4px 0">No encontrado. Ingrese los datos manualmente abajo.</div>';return;}
  cont.innerHTML=list.slice(0,5).map(c=>`
    <div class="cli-result" onclick="selCli(${c.id})">
      <div class="avatar">${(c.nombres[0]||'?').toUpperCase()}</div>
      <div><div style="font-weight:500;font-size:12px">${c.nombres} ${c.apellidos}</div>
      <div style="font-size:11px;color:var(--text2)">CI: ${c.dni}${c.tel?' · '+c.tel:''}</div></div>
    </div>`).join('');
}
async function selCli(id){
  const res=await fetch('/api/clientes').then(r=>r.json());
  const list=res.data||[];
  const c=list.find(x=>x.id===id);if(!c)return;
  sv('f-cli-dni',c.dni);sv('f-cli-nombres',c.nombres);sv('f-cli-apellidos',c.apellidos);
  sv('f-cli-tel',c.tel);sv('f-cli-email',c.email);sv('f-cli-ciudad',c.ciudad);sv('f-cli-dir',c.dir);
  document.getElementById('cli-results').innerHTML='';document.getElementById('buscar-cli').value='';
  const bar=document.getElementById('cli-sel-bar');bar.style.display='flex';
  document.getElementById('cli-sel-txt').textContent=c.nombres+' '+c.apellidos+' — CI: '+c.dni;
}
function clearCliSearch(){document.getElementById('buscar-cli').value='';document.getElementById('cli-results').innerHTML='';}
function clearCliSel(){
  ['f-cli-dni','f-cli-nombres','f-cli-apellidos','f-cli-tel','f-cli-email','f-cli-ciudad','f-cli-dir'].forEach(id=>sv(id,''));
  document.getElementById('cli-sel-bar').style.display='none';
}

// ═══════════════════════════════════════════
//  GUARDAR ORDEN
// ═══════════════════════════════════════════
async function guardarOrden(){
  const nombres=gv('f-cli-nombres'),tipo=gv('f-tipo'),modelo=gv('f-modelo'),falla=gv('f-falla');
  if(!nombres){toast('Ingrese el nombre del cliente (Paso 1)','error');showStep(0);return;}
  if(!tipo){toast('Seleccione el tipo de equipo (Paso 2)','error');showStep(1);return;}
  if(!modelo){toast('Ingrese el modelo del equipo (Paso 2)','error');showStep(1);return;}
  if(!falla){toast('Describa la falla reportada (Paso 2)','error');showStep(1);return;}

  const payload={
    cliente:{dni:gv('f-cli-dni'),nombres,apellidos:gv('f-cli-apellidos'),tel:gv('f-cli-tel'),email:gv('f-cli-email'),ciudad:gv('f-cli-ciudad'),dir:gv('f-cli-dir')},
    fecha_rec:gv('f-fecha-rec'),fecha_ent:gv('f-fecha-ent'),tecnico:gv('f-tecnico'),
    prioridad:gv('f-prioridad'),estado:gv('f-estado'),precio:gv('f-precio')||null,
    equipo:{tipo,marca:gv('f-marca'),modelo,serie:gv('f-serie'),so:gv('f-so'),condicion:gv('f-condicion'),accesorios:gv('f-accesorios'),falla,
            procesador:gv('f-procesador'),tarjeta_video:gv('f-tarjeta-video'),tarjeta_pcie:gv('f-tarjeta-pcie'),
            ram_total:gv('f-ram-total'),almacenamiento_total:gv('f-almacenamiento-total'),version_bios:gv('f-version-bios')},
    visual:{carcasa:getRadio('r-carcasa'),pantalla:getRadio('r-pantalla'),teclado_vis:getRadio('r-teclado-vis'),
            puertos:getRadio('r-puertos'),bisagras:getRadio('r-bisagras'),cargador_inc:getRadio('r-cargador-inc'),
            cargador_est:gv('f-cargador-est'),voltaje:gv('f-voltaje'),obs:gv('f-obs-visual')},
    funcional:{enc_bat:getRadio('r-enc-bat'),enc_car:getRadio('r-enc-car'),carga_so:getRadio('r-carga-so'),
               teclado:getRadio('r-teclado-fn'),audio:getRadio('r-audio'),display:getRadio('r-display'),
               touchpad:getRadio('r-touchpad'),wifi:getRadio('r-wifi'),usb:getRadio('r-usb'),camara:getRadio('r-camara'),obs:gv('f-obs-func')},
    bateria:{tool:gv('f-bat-tool'),disenio:gv('f-bat-dis'),actual:gv('f-bat-act'),salud:gv('f-bat-salud'),duracion:gv('f-bat-dur'),estado:gv('f-bat-estado'),serie:gv('f-bat-serie'),obs:gv('f-obs-bat')},
    ram:getRamData(),discos:getDiscoData(),
    termica:{cpu_rep:gv('f-cpu-rep'),cpu_carga:gv('f-cpu-carga'),gpu_rep:gv('f-gpu-rep'),gpu_carga:gv('f-gpu-carga'),disco:gv('f-temp-disco'),ventilacion:gv('f-vent'),obs:gv('f-obs-termica')},
    diagnostico:{estado_general:gv('f-estado-general'),servicio:gv('f-servicio'),diagnostico:gv('f-diagnostico'),
                 trabajos:gv('f-trabajos'),repuestos:gv('f-repuestos'),obs:gv('f-obs-final'),bios_estado:getRadio('r-bios-estado')},
    diag_fabricante:{software:gv('f-diag-fab-software'),resultado:gv('f-diag-fab-resultado'),obs:gv('f-diag-fab-obs')},
    fallas:getFallasData(),
    presupuesto:{moneda:gv('f-presupuesto-moneda')||'USD',notas:gv('f-presupuesto-notas')},
    presupuesto_items:getPresData(),
  };
  const method=editingId?'PUT':'POST';
  const url=editingId?`/api/ordenes/${editingId}`:'/api/ordenes';
  const res=await fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(!res.ok){const e=await res.json();toast(e.error||'Error al guardar','error');return;}
  const data=await res.json();
  const oid=editingId||data.id;
  if(pendingImages.filter(Boolean).length>0){toast('Subiendo imágenes...');await uploadPendingImages(oid);}
  clearApiCache();
  toast(editingId?'Orden actualizada':'Orden guardada exitosamente','success');
  limpiarForm();showPage('ordenes');
}

function limpiarForm(){
  const IDS=['f-cli-dni','f-cli-nombres','f-cli-apellidos','f-cli-tel','f-cli-email','f-cli-ciudad','f-cli-dir',
    'f-fecha-rec','f-fecha-ent','f-tecnico','f-precio','f-tipo','f-marca','f-modelo','f-serie','f-so',
    'f-condicion','f-accesorios','f-falla','f-procesador','f-tarjeta-video','f-tarjeta-pcie',
    'f-ram-total','f-almacenamiento-total','f-version-bios',
    'f-cargador-est','f-voltaje','f-obs-visual','f-obs-func',
    'f-bat-tool','f-bat-dis','f-bat-act','f-bat-salud','f-bat-dur','f-bat-estado','f-bat-serie','f-obs-bat',
    'f-ram-tool','f-cpu-rep','f-cpu-carga','f-gpu-rep','f-gpu-carga','f-temp-disco','f-vent','f-obs-termica',
    'f-estado-general','f-servicio','f-diagnostico','f-trabajos','f-repuestos','f-obs-final',
    'f-diag-fab-software','f-diag-fab-resultado','f-diag-fab-obs',
    'f-presupuesto-moneda','f-presupuesto-notas','f-prioridad','f-estado'];
  IDS.forEach(id=>{const e=document.getElementById(id);if(e){if(e.tagName==='SELECT')e.selectedIndex=0;else e.value='';}});
  document.getElementById('f-fecha-rec').value=new Date().toISOString().split('T')[0];
  document.getElementById('ram-tbody').innerHTML='';
  document.getElementById('disco-tbody').innerHTML='';
  document.getElementById('fallas-tbody').innerHTML='';
  document.getElementById('pres-tbody').innerHTML='';
  document.getElementById('previews-equipo').innerHTML='';
  document.getElementById('previews-visual').innerHTML='';
  document.getElementById('pres-total').textContent='0.00';
  document.getElementById('form-lbl').textContent='Nueva orden de trabajo';
  document.getElementById('buscar-cli').value='';
  document.getElementById('cli-results').innerHTML='';
  document.getElementById('cli-sel-bar').style.display='none';
  initAllRadios();
  pendingImages=[];ramCount=0;discoCount=0;fallaCount=0;presCount=0;editingId=null;
  showStep(0);fetchNextNum();
}

// ═══════════════════════════════════════════
//  DASHBOARD
// ═══════════════════════════════════════════
async function loadDashboard(){
  const cont=document.getElementById('dashboard-pending');
  cont.innerHTML=loadingHtml();
  const [stats,pending]=await Promise.all([fetchJson('/api/stats'),fetchJson('/api/ordenes/pendientes?limit=7')]);
  document.getElementById('stats-grid').innerHTML=`
    <div class="stat-card s-total"><div class="stat-num">${stats.total}</div><div class="stat-lbl">Total órdenes</div></div>
    <div class="stat-card s-revision"><div class="stat-num">${stats.revision}</div><div class="stat-lbl">En revisión</div></div>
    <div class="stat-card s-espera"><div class="stat-num">${stats.espera}</div><div class="stat-lbl">Esp. repuesto</div></div>
    <div class="stat-card s-listo"><div class="stat-num">${stats.listo}</div><div class="stat-lbl">Listos</div></div>
    <div class="stat-card s-entregado"><div class="stat-num">${stats.entregado}</div><div class="stat-lbl">Entregados</div></div>`;
  const pend=pending.items||[];
  if(!pend.length){cont.innerHTML='<div class="empty"><i class="ti ti-check"></i><p>No hay equipos pendientes</p></div>';return;}
  const hidden=Math.max((pending.total||0)-pend.length,0);
  cont.innerHTML=pend.map(o=>orderRow(o,false)).join('')+
    (hidden?`<div class="more-pending"><button class="btn btn-sm btn-primary" onclick="showPendingOrders()">+ ${hidden} equipos más</button></div>`:'');
}

function showPendingOrders(){
  const est=document.getElementById('filter-est');
  if(est)est.value='pendientes';
  showPage('ordenes');
}

// ═══════════════════════════════════════════
//  ÓRDENES
// ═══════════════════════════════════════════
function statusBadge(s){const m={revision:'En revisión',espera:'Esp. repuesto',listo:'Listo',entregado:'Entregado',cancelado:'Cancelado'};return`<span class="badge badge-${s}">${m[s]||s}</span>`;}
function prioSpan(p){const c=p==='Urgente'?'prio-urgente':p==='Alta'?'prio-alta':'prio-normal';return`<span class="${c}" style="font-size:10px;min-width:48px;text-align:center">${p}</span>`;}
function orderRow(o,showActions=true){
  const device=[o.tipo,o.marca,o.modelo].filter(Boolean).join(' ');
  const client=[(o.nombres||'')+(o.apellidos?' '+o.apellidos:''),o.dni?'CI:'+o.dni:''].filter(Boolean).join(' · ');
  const acts=showActions?`<div class="order-actions" onclick="event.stopPropagation()">
    <button class="btn btn-sm" title="PDF Cliente" onclick="descargarPDF(${o.id},'cliente')"><i class="ti ti-file-text"></i></button>
    <button class="btn btn-sm" title="PDF Técnico" onclick="descargarPDF(${o.id},'tecnico')"><i class="ti ti-file-analytics"></i></button>
    <button class="btn btn-sm btn-danger" title="Eliminar" onclick="eliminarOrden(${o.id})"><i class="ti ti-trash"></i></button>
  </div>`:'';
  return`<div class="order-row" onclick="openModal(${o.id})">
    <div class="order-num">${o.num}</div>
    <div class="order-info"><div class="order-device">${device||'—'}</div><div class="order-client">${client||'Sin cliente'}</div></div>
    ${statusBadge(o.estado)} ${prioSpan(o.prioridad||'Normal')}
    <div style="font-size:10px;color:var(--text2);min-width:74px;text-align:right">${o.fecha_rec||'—'}</div>
    ${acts}</div>`;
}
async function loadOrdenes(page=1){
  ordersPage=page;
  const q=gv('search-ord'),est=document.getElementById('filter-est').value;
  const tecnicoId=document.getElementById('filter-tec-ord')?.value||'';
  const cont=document.getElementById('orders-list');
  cont.innerHTML=loadingHtml();
  let url=`/api/ordenes?q=${encodeURIComponent(q)}&estado=${est}&page=${ordersPage}&limit=${PAGE_LIMIT}`;
  if(tecnicoId)url+=`&tecnico_id=${tecnicoId}`;
  const data=await fetchJson(url);
  const list=data.items||[];
  const count=document.getElementById('orders-count');
  if(count)count.textContent=`${data.total||0} resultado${(data.total||0)!==1?'s':''}`;
  renderPager('orders-pager',data.page||1,data.pages||1,'loadOrdenes');
  if(!list.length){cont.innerHTML='<div class="empty"><i class="ti ti-search"></i><p>No se encontraron órdenes</p></div>';return;}
  cont.innerHTML=list.map(o=>orderRow(o)).join('');
}
async function eliminarOrden(id){
  if(!confirm('¿Eliminar esta orden de trabajo?'))return;
  await fetch(`/api/ordenes/${id}`,{method:'DELETE'});
  clearApiCache();
  toast('Orden eliminada');loadOrdenes();loadDashboard();closeModalDirect();
}
function descargarPDF(id,tipo){window.open(`/api/pdf/${id}/${tipo}`,'_blank');}

// ═══════════════════════════════════════════
//  MODAL
// ═══════════════════════════════════════════
async function openModal(id){
  currentModalId=id;
  const o=await fetch(`/api/ordenes/${id}`).then(r=>r.json());
  const eq=o.equipo||{},dg=o.diagnostico||{},df=o.diag_fabricante||{};
  const pp=o.presupuesto||{},items=o.presupuesto_items||[];
  document.getElementById('modal-title').textContent=o.num+' — '+(eq.marca||'')+' '+(eq.modelo||'');
  const moneda=pp.moneda||'USD';
  const total=items.reduce((s,i)=>s+(parseFloat(i.precio)||0),0);
  document.getElementById('modal-body').innerHTML=`
    <div style="margin-bottom:9px">${statusBadge(o.estado)} ${prioSpan(o.prioridad||'Normal')}</div>
    <div class="dg">
      <div class="di"><label>Cliente</label><p>${o.nombres||'—'} ${o.apellidos||''}</p></div>
      <div class="di"><label>Cédula / DNI</label><p>${o.dni||'—'}</p></div>
      <div class="di"><label>Teléfono</label><p>${o.tel||'—'}</p></div>
      <div class="di"><label>Correo</label><p>${o.email||'—'}</p></div>
      <div class="di"><label>Equipo</label><p>${eq.tipo||''} ${eq.marca||''} ${eq.modelo||''}</p></div>
      <div class="di"><label>Procesador</label><p>${eq.procesador||'—'}</p></div>
      <div class="di"><label>Técnico</label><p>${o.tecnico||'—'}</p></div>
      <div class="di"><label>Total presupuesto</label><p>${items.length?moneda+' '+total.toFixed(2):(o.precio?'$ '+parseFloat(o.precio).toFixed(2):'—')}</p></div>
      <div class="di"><label>Recepción</label><p>${o.fecha_rec||'—'}</p></div>
      <div class="di"><label>Entrega est.</label><p>${o.fecha_ent||'—'}</p></div>
    </div>
    ${eq.falla?`<div style="margin-top:7px"><label style="font-size:10px;color:var(--text2)">Falla reportada</label><p style="font-size:11px">${eq.falla}</p></div>`:''}
    ${dg.estado_general?`<div style="margin-top:5px"><label style="font-size:10px;color:var(--text2)">Estado del equipo</label><p style="font-size:11px;font-weight:500">${dg.estado_general}</p></div>`:''}
    ${df.resultado?`<div style="margin-top:5px"><label style="font-size:10px;color:var(--text2)">Diagnóstico fabricante</label><p style="font-size:11px">${df.resultado}${df.software?' — '+df.software:''}</p></div>`:''}
    <div style="margin-top:11px;display:flex;align-items:center;gap:7px;flex-wrap:wrap">
      <label style="margin:0;font-size:11px;white-space:nowrap">Cambiar estado:</label>
      <select id="modal-estado" style="width:185px" onchange="cambiarEstado(${id},this.value)">
        <option value="revision" ${o.estado==='revision'?'selected':''}>En revisión</option>
        <option value="espera"   ${o.estado==='espera'?'selected':''}>Esperando repuesto</option>
        <option value="listo"    ${o.estado==='listo'?'selected':''}>Listo para entregar</option>
        <option value="entregado"${o.estado==='entregado'?'selected':''}>Entregado</option>
        <option value="cancelado"${o.estado==='cancelado'?'selected':''}>Cancelado</option>
      </select>
    </div>`;
  renderModalImages(o.imagenes||[]);
  document.getElementById('modal-img-section').style.display='block';
  // CORRECCIÓN: usar `id` (parámetro original correcto) en lugar de `o.id`
  // o.id puede estar corrompido si equipo.id ≠ ordenes.id tras un PUT/replace
  document.getElementById('modal-actions').innerHTML=`
    <button class="btn btn-primary btn-sm" onclick="descargarPDF(${id},'cliente')"><i class="ti ti-file-text"></i> PDF Cliente</button>
    <button class="btn btn-sm" style="background:#2B5D8A;color:#fff;border-color:#2B5D8A" onclick="descargarPDF(${id},'tecnico')"><i class="ti ti-file-analytics"></i> PDF Técnico</button>
    <button class="btn btn-sm" style="background:#17a2b8;color:#fff;border-color:#17a2b8" onclick="imprimirTicket(${id})"><i class="ti ti-ticket"></i> Imprimir Ticket</button>
    <button class="btn btn-sm" onclick="editarOrden(${id})"><i class="ti ti-edit"></i> Editar</button>
    <button class="btn btn-danger btn-sm" onclick="eliminarOrden(${id})"><i class="ti ti-trash"></i> Eliminar</button>`;
  document.getElementById('modal-overlay').classList.add('open');
}
function renderModalImages(imgs){
  const cont=document.getElementById('modal-img-previews');
  if(!imgs.length){cont.innerHTML='<div style="font-size:11px;color:var(--text2)">Sin imágenes adjuntas</div>';return;}
  cont.innerHTML=imgs.map(img=>`
    <div class="img-thumb">
      <img src="/imagenes/${img.ruta}" alt="">
      <button class="del-img" onclick="deleteModalImage(${img.id})">✕</button>
      <div class="img-label">${img.seccion}: ${img.descripcion||''}</div>
    </div>`).join('');
}
async function uploadModalImages(input){
  if(!currentModalId)return;
  const seccion=gv('modal-img-seccion'),desc=gv('modal-img-desc');
  for(const file of input.files){
    const fd=new FormData();fd.append('file',file);fd.append('seccion',seccion);fd.append('descripcion',desc);
    await fetch(`/api/upload/${currentModalId}`,{method:'POST',body:fd});
  }
  input.value='';
  const o=await fetch(`/api/ordenes/${currentModalId}`).then(r=>r.json());
  renderModalImages(o.imagenes||[]);toast('Imágenes subidas','success');
}
async function deleteModalImage(imgId){
  if(!confirm('¿Eliminar esta imagen?'))return;
  await fetch(`/api/imagenes/${imgId}`,{method:'DELETE'});
  const o=await fetch(`/api/ordenes/${currentModalId}`).then(r=>r.json());
  renderModalImages(o.imagenes||[]);
}
async function cambiarEstado(id,val){
  await fetch(`/api/ordenes/${id}/estado`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({estado:val})});
  clearApiCache();
  toast('Estado actualizado','success');loadOrdenes();loadDashboard();
}
function closeModal(e){if(e.target.id==='modal-overlay')closeModalDirect();}
function closeModalDirect(){document.getElementById('modal-overlay').classList.remove('open');}

// ═══════════════════════════════════════════
//  EDITAR ORDEN — carga datos + imágenes
// ═══════════════════════════════════════════
async function editarOrden(id){
  closeModalDirect();
  const o=await fetch(`/api/ordenes/${id}`).then(r=>r.json());
  const eq=o.equipo||{},v=o.visual||{},f=o.funcional||{},b=o.bateria||{};
  const t=o.termica||{},dg=o.diagnostico||{},df=o.diag_fabricante||{};
  const pp=o.presupuesto||{};
  editingId=id;

  // Cliente & orden
  sv('f-cli-dni',o.dni);sv('f-cli-nombres',o.nombres);sv('f-cli-apellidos',o.apellidos);
  sv('f-cli-tel',o.tel);sv('f-cli-email',o.email);sv('f-cli-ciudad',o.ciudad);sv('f-cli-dir',o.dir);
  sv('f-fecha-rec',o.fecha_rec);sv('f-fecha-ent',o.fecha_ent);sv('f-tecnico',o.tecnico);
  sv('f-prioridad',o.prioridad);sv('f-estado',o.estado);sv('f-precio',o.precio);
  // Equipo
  sv('f-tipo',eq.tipo);sv('f-marca',eq.marca);sv('f-modelo',eq.modelo);sv('f-serie',eq.serie);
  sv('f-so',eq.so);sv('f-condicion',eq.condicion);sv('f-accesorios',eq.accesorios);sv('f-falla',eq.falla);
  sv('f-procesador',eq.procesador);sv('f-tarjeta-video',eq.tarjeta_video);sv('f-tarjeta-pcie',eq.tarjeta_pcie);
  sv('f-ram-total',eq.ram_total);sv('f-almacenamiento-total',eq.almacenamiento_total);sv('f-version-bios',eq.version_bios);
  // Visual
  sv('f-cargador-est',v.cargador_est);sv('f-voltaje',v.voltaje);sv('f-obs-visual',v.obs);
  // Funcional
  sv('f-obs-func',f.obs);
  // Batería
  sv('f-bat-tool',b.tool);sv('f-bat-dis',b.disenio);sv('f-bat-act',b.actual);
  sv('f-bat-salud',b.salud);sv('f-bat-dur',b.duracion);sv('f-bat-estado',b.estado);sv('f-bat-serie',b.serie);sv('f-obs-bat',b.obs);
  // Térmica
  sv('f-cpu-rep',t.cpu_rep);sv('f-cpu-carga',t.cpu_carga);sv('f-gpu-rep',t.gpu_rep);
  sv('f-gpu-carga',t.gpu_carga);sv('f-temp-disco',t.disco);sv('f-vent',t.ventilacion);sv('f-obs-termica',t.obs);
  // Diagnóstico
  sv('f-estado-general',dg.estado_general);sv('f-servicio',dg.servicio);sv('f-diagnostico',dg.diagnostico);
  sv('f-trabajos',dg.trabajos);sv('f-repuestos',dg.repuestos);sv('f-obs-final',dg.obs);
  // Diag fabricante
  sv('f-diag-fab-software',df.software);sv('f-diag-fab-resultado',df.resultado);sv('f-diag-fab-obs',df.obs);
  // Presupuesto
  sv('f-presupuesto-moneda',pp.moneda||'USD');sv('f-presupuesto-notas',pp.notas);

  // RAM
  document.getElementById('ram-tbody').innerHTML='';ramCount=0;
  (o.ram||[]).forEach(r=>addRam(r));
  // Discos
  document.getElementById('disco-tbody').innerHTML='';discoCount=0;
  (o.discos||[]).forEach(d=>addDisco(d));
  // Fallas
  document.getElementById('fallas-tbody').innerHTML='';fallaCount=0;
  (o.fallas||[]).forEach(f2=>addFalla(f2));
  // Presupuesto items
  document.getElementById('pres-tbody').innerHTML='';presCount=0;
  (o.presupuesto_items||[]).forEach(pi=>addPresItem(pi));
  calcTotal();

  // Radios
  initAllRadios();
  setTimeout(()=>{
    setRadio('r-carcasa',v.carcasa||'na');setRadio('r-pantalla',v.pantalla||'na');
    setRadio('r-teclado-vis',v.teclado_vis||'na');setRadio('r-puertos',v.puertos||'na');
    setRadio('r-bisagras',v.bisagras||'na');setRadio('r-cargador-inc',v.cargador_inc||'na');
    setRadio('r-enc-bat',f.enc_bat||'na');setRadio('r-enc-car',f.enc_car||'na');
    setRadio('r-carga-so',f.carga_so||'na');setRadio('r-teclado-fn',f.teclado||'na');
    setRadio('r-audio',f.audio||'na');setRadio('r-display',f.display||'na');
    setRadio('r-touchpad',f.touchpad||'na');setRadio('r-wifi',f.wifi||'na');
    setRadio('r-usb',f.usb||'na');setRadio('r-camara',f.camara||'na');
    setRadio('r-bios-estado',dg.bios_estado||'na');
  },60);

  // Imágenes existentes en las pestañas correspondientes
  document.getElementById('previews-equipo').innerHTML='';
  document.getElementById('previews-visual').innerHTML='';
  const imgs=o.imagenes||[];
  renderEditImages('previews-equipo', imgs.filter(i=>i.seccion==='equipo'));
  renderEditImages('previews-visual',  imgs.filter(i=>i.seccion==='visual'));

  document.getElementById('form-lbl').textContent='Editando '+o.num;
  document.getElementById('cli-sel-bar').style.display='flex';
  document.getElementById('cli-sel-txt').textContent=(o.nombres||'')+' '+(o.apellidos||'')+' — CI: '+(o.dni||'');
  showPage('nueva');showStep(0);
}

// ═══════════════════════════════════════════
//  HISTORIAL
// ═══════════════════════════════════════════
async function initHistorial(){
  const anios=await fetchJson('/api/anios');
  const sel=document.getElementById('sel-anio');
  const cur=sel.value;sel.innerHTML='';
  if(!anios.length){const op=document.createElement('option');op.textContent=new Date().getFullYear();sel.appendChild(op);}
  else anios.forEach(y=>{const op=document.createElement('option');op.value=y;op.textContent=y;sel.appendChild(op);});
  if(cur&&anios.includes(cur))sel.value=cur;
  if(!document.getElementById('sel-dia').value)document.getElementById('sel-dia').value=new Date().toISOString().split('T')[0];
  document.getElementById('sel-mes').value=new Date().getMonth()+1;
  loadHistorial();
}
function setMode(m){
  currentMode=m;
  ['anio','mes','dia'].forEach(x=>document.getElementById('mode-'+x).classList.toggle('active',x===m));
  document.getElementById('fg-mes').style.display=m==='mes'||m==='dia'?'flex':'none';
  document.getElementById('fg-dia').style.display=m==='dia'?'flex':'none';
  loadHistorial();
}
async function loadHistorial(page=1){
  histPage=page;
  const anio=document.getElementById('sel-anio').value,mes=document.getElementById('sel-mes').value;
  const dia=document.getElementById('sel-dia').value,est=document.getElementById('h-estado').value,q=gv('h-search');
  let url=`/api/ordenes?estado=${est}&q=${encodeURIComponent(q)}&page=${histPage}&limit=${PAGE_LIMIT}`;
  if(currentMode==='dia') url+=`&dia=${dia}`;
  else if(currentMode==='mes') url+=`&anio=${anio}&mes=${mes}`;
  else url+=`&anio=${anio}`;
  const cont=document.getElementById('hist-list');
  cont.innerHTML=loadingHtml();
  const data=await fetchJson(url);
  const list=data.items||[];
  let lbl='';
  if(currentMode==='anio') lbl='Año '+anio;
  else if(currentMode==='mes') lbl=MESES[parseInt(mes)-1]+' '+anio;
  else if(dia){const[y,m,d]=dia.split('-');lbl=d+' de '+MESES[parseInt(m)-1]+' de '+y;}
  const total=data.total||0;
  document.getElementById('period-lbl').innerHTML=`<i class="ti ti-calendar-event"></i> ${lbl} <span>— ${total} orden${total!==1?'es':''}</span>`;
  const hc=document.getElementById('hist-count');if(hc)hc.textContent=`${total} resultado${total!==1?'s':''}`;
  renderPager('hist-pager',data.page||1,data.pages||1,'loadHistorial');
  const counts=data.counts||{};
  const st={total,revision:counts.revision||0,espera:counts.espera||0,listo:counts.listo||0,entregado:counts.entregado||0,cancelado:counts.cancelado||0};
  document.getElementById('hist-stats').innerHTML=`
    <div class="stat-card s-total"><div class="stat-num">${st.total}</div><div class="stat-lbl">Total</div></div>
    <div class="stat-card s-revision"><div class="stat-num">${st.revision}</div><div class="stat-lbl">En revisión</div></div>
    <div class="stat-card s-espera"><div class="stat-num">${st.espera}</div><div class="stat-lbl">Esp. repuesto</div></div>
    <div class="stat-card s-listo"><div class="stat-num">${st.listo}</div><div class="stat-lbl">Listos</div></div>
    <div class="stat-card s-entregado"><div class="stat-num">${st.entregado}</div><div class="stat-lbl">Entregados</div></div>
    <div class="stat-card s-cancelado"><div class="stat-num">${st.cancelado}</div><div class="stat-lbl">Cancelados</div></div>`;
  if(!list.length){cont.innerHTML='<div class="empty"><i class="ti ti-calendar-x"></i><p>No hay órdenes en este período</p></div>';return;}
  cont.innerHTML=list.map(o=>orderRow(o)).join('');
}


// --- FUNCIONES DE CONFIGURACIÓN Y TICKET ---

async function cargarConfiguracion() {
  try {
    const res = await fetch('/api/configuracion');
    const data = await res.json();
    if (data && data.nombre_taller) {
      document.getElementById('conf-nombre').value = data.nombre_taller;
      document.getElementById('conf-direccion').value = data.direccion || '';
      document.getElementById('conf-telefono').value = data.telefono || '';
      document.getElementById('conf-tipo').value = data.tipo_documento || 'RUT';
      document.getElementById('conf-num').value = data.numero_documento || '';
    }
  } catch (e) { console.error('Error cargando config:', e); }
}


async function cargarConfig() {
    const form = document.getElementById('form-config');
    if (!form) return; // Si el formulario no existe, salir

    try {
        const res = await fetch('/api/configuracion');
        const data = await res.json();

        if (data && data.nombre_taller) {
            document.getElementById('conf-nombre').value = data.nombre_taller;
            document.getElementById('conf-direccion').value = data.direccion || '';
            document.getElementById('conf-telefono').value = data.telefono || '';
            document.getElementById('conf-tipo').value = data.tipo_documento || 'RUT';
            document.getElementById('conf-num').value = data.numero_documento || '';
        }
    } catch (error) {
        console.error('Error cargando configuración:', error);
    }
}

// 2. Modifica tu función de cambio de pestaña existente
// Busca tu función actual (ej: cambiarTab) y agrégale este bloque:
function cambiarTab(nombreTab) {
    // ... (tu código existente que oculta todas las pestañas y muestra la activa) ...

    // --- AGREGA ESTO AL FINAL DE TU FUNCIÓN ---
    if (nombreTab === 'configuracion') {
        cargarConfiguracion();
    }
}

// 3. Si no tienes una función centralizada, agrega este "EventListener" al final del archivo:
document.addEventListener('DOMContentLoaded', () => {
    // Buscar todos los botones/enlaces del menú que tengan onclick con 'configuracion'
    // Esta es una forma genérica de interceptar el clic si no quieres tocar tu función principal
    const enlacesMenu = document.querySelectorAll('[onclick*="configuracion"]');

    enlacesMenu.forEach(enlace => {
        enlace.addEventListener('click', () => {
            // Pequeño retraso para asegurar que el DOM se actualizó
            setTimeout(() => {
                cargarConfiguracion();
            }, 100);
        });
    });

    // ... (el resto de tu código inicial) ...
});

async function guardarConfig(e) {
  e.preventDefault();
  const datos = {
    nombre: document.getElementById('conf-nombre').value,
    direccion: document.getElementById('conf-direccion').value,
    telefono: document.getElementById('conf-telefono').value,
    tipo_doc: document.getElementById('conf-tipo').value,
    num_doc: document.getElementById('conf-num').value
  };

  try {
    const res = await fetch('/api/configuracion', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(datos)
    });
    if (res.ok) {
      toast('✅ Configuración guardada correctamente', 'success');
      cargarConfig();
    } else {
      toast('❌ Error al guardar configuración', 'error');
    }
  } catch (e) {
    toast('Error de conexión: ' + e.message, 'error');
  }
}

async function imprimirTicket(idOrden) {
    // 1. Si no se pasa el ID, intentar obtenerlo del modal actual
    if (!idOrden && currentModalId) {
        idOrden = currentModalId;
    }

    // 2. Validación final
    if (!idOrden) {
        toast('⚠️ Error: No se pudo identificar la orden. Por favor, cierra y vuelve a abrir el detalle de la orden.', 'error');
        return;
    }

    try {
        // 3. Llamada a la API con el ID correcto
        const res = await fetch(`/api/orden/${idOrden}/ticket`);

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || 'Orden no encontrada');
        }

        const data = await res.json();
        const t = data.taller;
        const o = data.orden;

        // 4. Validar que existan datos del taller
        if (!t || !t.nombre_taller) {
            toast('⚠️ Primero debes configurar los datos de tu taller en la pestaña "Configuración".', 'error');
            return;
        }

        // 5. Generar contenido HTML del ticket
        const contenido = `
            <div style="width:75mm; font-family:'Courier New', monospace; text-align:center; margin: 0 auto; padding: 5px;">
                <h3 style="margin:5px 0; text-transform:uppercase; font-size:14px;">${t.nombre_taller}</h3>
                <p style="margin:2px 0; font-size:12px;">${t.direccion || ''}</p>
                <p style="margin:2px 0; font-size:12px;">Tel: ${t.telefono || ''}</p>
                <p style="margin:2px 0; font-size:12px;"><b>${t.tipo_documento}: ${t.numero_documento || ''}</b></p>
                <br>
                <div style="border-bottom:1px dashed #000;"></div>
                <p style="text-align:left; margin:5px 0;"><b>ORDEN N°:</b> ${String(o.id).padStart(6,'0')}</p>
                <p style="text-align:left; margin:5px 0;"><b>FECHA:</b> ${o.fecha} ${o.hora ? '(' + o.hora + ')' : ''}</p>
                <p style="text-align:left; margin:5px 0;"><b>CLIENTE:</b> ${o.cliente}</p>
                <p style="text-align:left; margin:5px 0;"><b>TEL:</b> ${o.telefono_cliente}</p>
                <div style="border-bottom:1px dashed #000;"></div>
                <p style="text-align:left; margin:5px 0;"><b>EQUIPO:</b> ${o.equipo}</p>
                <p style="text-align:left; margin:5px 0;"><b>SERIE:</b> ${o.serie}</p>
                <div style="border-bottom:1px dashed #000;"></div>
                <p style="text-align:left; margin:5px 0;"><b>FALLA REPORTADA:</b></p>
                <p style="text-align:left; font-size:11px; white-space:pre-wrap;">${o.falla}</p>
                <br>
                <p style="font-size:12px;">¡Gracias por su confianza!</p>
                <p style="font-size:10px;">Conserve este ticket para el retiro.</p>
            </div>
        `;

        // 6. Abrir ventana de impresión
        const win = window.open('', '', 'width=400,height=600');
        win.document.write(`
            <html><head><title>Ticket Orden ${o.id}</title>
            <style>
                body { margin: 0; padding: 10px; font-family: 'Courier New', monospace; }
                @media print { button { display: none; } body { padding: 0; } }
            </style>
            </head><body>${contenido}
            <div style="text-align:center; margin-top:20px;">
                <button onclick="window.print()" style="padding:10px 20px; font-size:16px; cursor:pointer;">🖨️ IMPRIMIR AHORA</button>
            </div></body></html>
        `);
        win.document.close();

    } catch (error) {
        console.error('Error al generar ticket:', error);
        toast('❌ Error al generar el ticket: ' + error.message, 'error');
    }
}


// ═══════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════
document.getElementById('f-fecha-rec').value=new Date().toISOString().split('T')[0];
initAllRadios();
loadDashboard();