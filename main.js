/* main.js — Final unified version (budget integrated, DB-driven) */

const ui = (function(){
  const API_BASE = "http://127.0.0.1:5000";

  // ---- Helpers ----
  function getUser(){ return JSON.parse(localStorage.getItem('fa_user') || 'null'); }
  function setUser(u){ localStorage.setItem('fa_user', JSON.stringify(u)); }
  function clearUser(){ localStorage.removeItem('fa_user'); localStorage.removeItem('fa_user_name'); }

  function showToast(msg, type='info', timeout=3000){
    const container = document.getElementById('toastContainer');
    if(!container){ console.log(type.toUpperCase(), msg); return; }
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    container.appendChild(el);
    // animate
    setTimeout(()=> el.classList.add('show'), 20);
    setTimeout(()=> { el.classList.remove('show'); setTimeout(()=> el.remove(), 300); }, timeout);
  }

  function apiJson(res){ return res.json().catch(()=>({status:'error', message:'Invalid JSON'})); }
  function formatNumber(n){ return Number(n).toLocaleString('en-IN'); }
  function formatDate(d){ return d ? d.slice(0,10) : ''; }

  // ---- AUTH ----
  async function login(){
    const email = document.getElementById('loginEmail')?.value?.trim();
    const pw = document.getElementById('loginPassword')?.value?.trim();
    if(!email || !pw){ showToast('Enter email & password','error'); return; }

    try{
      const res = await fetch(`${API_BASE}/login`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, password: pw})
      });
      const data = await apiJson(res);
      if(res.ok && data.status === 'success'){
        setUser(data.user);
        localStorage.setItem('fa_user_name', data.user.name || data.user.email);
        showToast('Login successful','success');
        setTimeout(()=> window.location.href = 'dashboard.html', 600);
      } else showToast(data.message || 'Login failed','error');
    } catch(e){
      console.error(e); showToast('Server not reachable','error');
    }
  }

  async function signup(){
    const name = document.getElementById('signupName')?.value?.trim();
    const email = document.getElementById('signupEmail')?.value?.trim();
    const pw = document.getElementById('signupPassword')?.value?.trim();
    const pw2 = document.getElementById('signupPassword2')?.value?.trim();
    if(!name || !email || !pw){ showToast('Complete all fields','error'); return; }
    if(pw !== pw2){ showToast('Passwords do not match','error'); return; }

    try{
      const res = await fetch(`${API_BASE}/signup`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name,email,password:pw})
      });
      const data = await apiJson(res);
      if(res.ok && data.status === 'success'){
        showToast('Account created — please login','success');
        setTimeout(()=> { window.location.href = 'index.html'; }, 900);
      } else showToast(data.message || 'Signup failed','error');
    } catch(e){ console.error(e); showToast('Server not reachable','error'); }
  }

  function logout(){
    clearUser();
    showToast('Logged out','info');
    setTimeout(()=> window.location.href = 'index.html', 350);
  }

  async function resetPassword(){
    const email = document.getElementById('resetEmail')?.value?.trim();
    if(!email){ showToast('Enter registered email','error'); return; }
    showToast('Password reset link (demo) — implement email flow later','info', 3500);
  }

  // ---- TRANSACTIONS ----
  async function fetchTransactions(){
    const user = getUser(); if(!user) return [];
    try{
      const res = await fetch(`${API_BASE}/transactions?user_id=${user.id}`);
      if(!res.ok){ showToast('Failed to fetch transactions','error'); return []; }
      const data = await apiJson(res); return data.transactions || [];
    } catch(e){ console.error(e); showToast('Server not reachable','error'); return []; }
  }

  async function addTransaction(){
    const user = getUser(); if(!user){ showToast('Please login','error'); window.location.href='index.html'; return; }
    const category = document.getElementById('txnCategory')?.value?.trim() || document.getElementById('quickCat')?.value?.trim();
    const amount = Number(document.getElementById('txnAmount')?.value || document.getElementById('quickAmt')?.value);
    const type = document.getElementById('txnType')?.value || document.getElementById('quickType')?.value || 'expense';
    const date = new Date().toISOString().slice(0,10);
    if(!category || !amount){ showToast('Enter category & amount','error'); return; }

    try{
      const res = await fetch(`${API_BASE}/transactions`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ user_id: user.id, category, amount, type, date })
      });
      const data = await apiJson(res);
      if(res.ok){
        showToast('Transaction added','success');
        await renderTxns();
        await updateDashboard();
        // If budget page present, refresh budget display (DB-driven)
        if(window.location.pathname.split('/').pop().includes('budget')) await fetchAndRenderBudget();
      }
      else showToast(data.message || 'Add failed','error');
    } catch(e){ console.error(e); showToast('Server not reachable','error'); }
  }

  async function renderTxns(){
    const list = document.getElementById('txnList'); if(!list) return;
    list.innerHTML = '<div class="muted">Loading...</div>';
    const txns = await fetchTransactions();
    if(!txns.length){ list.innerHTML = '<div class="muted">No transactions yet</div>'; return; }
    list.innerHTML = '';
    txns.slice(0,200).forEach(t=>{
      const div = document.createElement('div'); div.className='txn-item';
      const dateText = formatDate(t.date || t.created_at || '');
      const amt = Number(t.amount || 0);
      div.innerHTML = `<div><strong>${t.category || '—'}</strong><div class="muted">${dateText}</div></div><div><span style="color:${t.type==='income' ? '#6ee7b7' : '#ff8a8a'}">₹${formatNumber(amt)}</span></div>`;
      list.appendChild(div);
    });
  }

  // ---- GOALS ----
  async function fetchGoals(){
    const user = getUser(); if(!user) return [];
    try{
      const res = await fetch(`${API_BASE}/goals?user_id=${user.id}`);
      if(!res.ok){ showToast('Failed to fetch goals','error'); return []; }
      const data = await apiJson(res); return data.goals || [];
    } catch(e){ console.error(e); showToast('Server not reachable','error'); return []; }
  }

  async function addGoal(){
    const user = getUser(); if(!user){ showToast('Please login','error'); window.location.href='index.html'; return; }
    const name = document.getElementById('goalName')?.value?.trim();
    const target = Number(document.getElementById('goalAmount')?.value);
    const date = document.getElementById('goalDate')?.value;
    if(!name || !target || !date){ showToast('Complete goal form','error'); return; }
    try{
      const res = await fetch(`${API_BASE}/goals`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ user_id: user.id, name, target, saved:0, date })
      });
      const data = await apiJson(res);
      if(res.ok){ showToast('Goal added','success'); await renderGoals(); await updateDashboard(); }
      else showToast(data.message || 'Add goal failed','error');
    } catch(e){ console.error(e); showToast('Server not reachable','error'); }
  }

  async function renderGoals(){
    const container = document.getElementById('goalList'); if(!container) return;
    container.innerHTML = '<div class="muted">Loading...</div>';
    const goals = await fetchGoals();
    if(!goals.length){ container.innerHTML = '<div class="muted">No goals yet</div>'; return; }
    container.innerHTML = '';
    goals.forEach(g=>{
      const saved = Number(g.saved || 0);
      const target = Number(g.target || 0);
      const prog = Math.min(100, Math.round((saved/Math.max(target,1))*100));
      const dateText = formatDate(g.date || '');
      const div = document.createElement('div'); div.className='goal-card';
      div.innerHTML = `<div style="display:flex;justify-content:space-between"><strong>${g.name || g.goal_name}</strong><span class="muted">${dateText}</span></div>
        <div style="margin-top:8px">Target: ₹${formatNumber(target)} • Saved: ₹${formatNumber(saved)}</div>
        <div style="margin-top:8px;background:rgba(255,255,255,0.02);height:10px;border-radius:8px;overflow:hidden">
          <div style="width:${prog}%;height:10px;background:linear-gradient(90deg,#00C6FF,#00FFA3)"></div>
        </div>`;
      container.appendChild(div);
    });
  }

  // ---- PREDICTIONS ----
  async function renderPredictionPage(){
    const user = getUser(); if(!user){ showToast('Please login','error'); return; }
    const el = document.getElementById('nextPred');
    const ctx = document.getElementById('predChart');
    try{
      const res = await fetch(`${API_BASE}/predictions?user_id=${user.id}`);
      const data = await apiJson(res);
      if(res.ok && data.status === 'success'){
        el && (el.textContent = `₹${formatNumber(data.next_pred || 0)}`);
        if(ctx && window.Chart){
          if(window.predChartInst) window.predChartInst.destroy();
          window.predChartInst = new Chart(ctx, {
            type:'bar',
            data:{ labels: data.labels.length? data.labels : ['Next Month'], datasets:[
              { label:'Actual', data: data.actual.length? data.actual : [], backgroundColor:'rgba(255,110,110,0.6)' },
              { label:'Predicted', data: data.predicted.length? data.predicted : [], backgroundColor:'rgba(0,198,255,0.6)' }
            ]},
            options:{ responsive:true, plugins:{legend:{labels:{color:'#fff'}}}, scales:{x:{ticks:{color:'#A8B3CF'}}, y:{ticks:{color:'#A8B3CF'}}} }
          });
        }
      } else showToast(data.message || 'Prediction fetch failed','error');
    } catch(e){ console.error(e); showToast('Server not reachable','error'); }
  }

  // ---- BUDGET (DB-driven via /add_budget and /get_budget) ----

  // POST new budget for current month
  async function addBudget(){
    // amount input only (budget.html uses #budgetAmount)
    const user = getUser();
    if(!user){ showToast('Please login','error'); window.location.href='index.html'; return; }
    const amount = Number(document.getElementById('budgetAmount')?.value);
    if(!amount || amount <= 0){ showToast('Enter a valid budget amount','error'); return; }

    try{
      const res = await fetch(`${API_BASE}/add_budget`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ user_id: user.id, amount })
      });
      const data = await apiJson(res);
      if(res.ok && data.status === 'success'){
        showToast('Budget saved for current month','success');
        document.getElementById('budgetAmount').value = '';
        await fetchAndRenderBudget();
      } else {
        showToast(data.message || 'Failed to save budget','error');
      }
    } catch(e){
      console.error(e); showToast('Server not reachable','error');
    }
  }

  // Fetch budget info (current + previous up to 3 months) from backend and render UI
  async function fetchAndRenderBudget(){
    const user = getUser();
    if(!user) return;

    const summaryEl = document.getElementById('budgetSummary');
    const prevEl = document.getElementById('prevBudgetList');

    if(summaryEl) summaryEl.innerHTML = '<div class="muted">Loading...</div>';
    if(prevEl) prevEl.innerHTML = '';

    try{
      const res = await fetch(`${API_BASE}/get_budget?user_id=${user.id}`);
      const data = await apiJson(res);
      if(!res.ok || data.status !== 'success'){
        if(summaryEl) summaryEl.innerHTML = '<div class="muted">Failed to load budget</div>';
        showToast(data.message || 'Failed to fetch budget','error');
        return;
      }

      // Current
      const cur = data.current || { month_year:'', amount:0, spent:0, remaining:0, remaining_days:0, note:'' };
      if(summaryEl){
        if(cur.amount && cur.amount > 0){
          const color = cur.spent > cur.amount ? '#ff7b7b' : (cur.remaining < (cur.amount*0.2) ? '#facc15' : '#22c55e');
          summaryEl.innerHTML = `
            <div style="background:rgba(255,255,255,0.03);padding:14px;border-radius:10px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <h3 style="margin:0">₹${formatNumber(cur.amount)}</h3>
                  <div class="muted">Budget — ${cur.month_year}</div>
                </div>
                <div style="text-align:right">
                  <div style="font-weight:700;color:${color}">Remaining ₹${formatNumber(cur.remaining)}</div>
                  <div class="muted">${cur.remaining_days} days left</div>
                </div>
              </div>
              <div style="margin-top:10px;color:#fff">${cur.note}</div>
              <div style="margin-top:10px" class="muted">Spent: ₹${formatNumber(cur.spent)}</div>
            </div>`;
        } else {
          summaryEl.innerHTML = `<div class="muted">No budget set for this month</div>`;
        }
      }

      // Previous months
      const prev = data.previous || [];
      if(prevEl){
        if(!prev.length) prevEl.innerHTML = '<div class="muted">No previous budget records found</div>';
        else {
          prevEl.innerHTML = '';
          prev.forEach(m=>{
            const item = document.createElement('div');
            item.className = 'txn-item';
            item.innerHTML = `<div><strong>${m.month_year}</strong><div class="muted">Budget: ₹${formatNumber(m.amount)}</div></div>
                              <div style="text-align:right">Spent: ₹${formatNumber(m.spent)}</div>`;
            prevEl.appendChild(item);
          });
        }
      }

    } catch(e){
      console.error(e);
      if(summaryEl) summaryEl.innerHTML = '<div class="muted">Error loading budget</div>';
      showToast('Server not reachable','error');
    }
  }

  // ---- DASHBOARD ----
  // ---- DASHBOARD ----
async function updateDashboard(){
  const user = getUser();
  if(!user) { window.location.href='index.html'; return; }

  // user name
  const userNameEl = document.getElementById('userName');
  if(userNameEl) userNameEl.textContent = (localStorage.getItem('fa_user_name') || user.name || 'User');

  // fetch transactions & compute totals
  const txns = await fetchTransactions();
  const income = txns.filter(t=>t.type==='income').reduce((s,n)=>s+Number(n.amount||0),0);
  const expense = txns.filter(t=>t.type==='expense').reduce((s,n)=>s+Number(n.amount||0),0);
  const saving = income - expense;

  if(document.getElementById('incomeCard')) document.getElementById('incomeCard').textContent = `₹${formatNumber(income)}`;
  if(document.getElementById('expenseCard')) document.getElementById('expenseCard').textContent = `₹${formatNumber(expense)}`;
  if(document.getElementById('saveCard')) document.getElementById('saveCard').textContent = `₹${formatNumber(saving)}`;

  // ---- NEW: fetch goals and update Active Goals counter ----
  try {
    const goals = await fetchGoals(); // uses existing fetchGoals() in your file
    const activeCount = Array.isArray(goals) ? goals.filter(g => {
      // treat 'in_progress' (or anything not 'completed') as active.
      // adjust condition if you use different status values.
      const status = (g.status || '').toLowerCase();
      return status !== 'completed' && status !== 'done' && status !== 'closed';
    }).length : 0;

    const activeGoalsEl = document.getElementById('activeGoals');
    if(activeGoalsEl) activeGoalsEl.textContent = activeCount;

  } catch(err) {
    console.error('Error fetching goals for dashboard:', err);
    // keep existing display if error
  }

  // ---- refresh budget display if present ----
  if(document.getElementById('budgetSummary') || document.getElementById('prevBudgetList')){
    await fetchAndRenderBudget();
  }
}

  // ---- DASHBOARD MODAL & CHART ----
  async function setupDashboardUI(){
    const modal = document.getElementById('quickModal');
    const addBtn = document.getElementById('quickAddBtn');
    const closeBtn = document.getElementById('quickClose');
    const saveBtn = document.getElementById('quickSave');
    const chartCanvas = document.getElementById('expenseChart');

    if (!addBtn || !modal) return;
    modal.style.display = "none";

    addBtn.addEventListener('click', () => modal.style.display = "flex");
    closeBtn.addEventListener('click', () => modal.style.display = "none");

    saveBtn.addEventListener('click', async () => {
      modal.style.display = "none";
      await addTransaction();
      await renderExpenseChart();
      await updateDashboard();
    });

    async function renderExpenseChart(){
      const user = getUser(); if(!user) return;
      try {
        const res = await fetch(`${API_BASE}/predictions?user_id=${user.id}`);
        const data = await res.json();
        const ctx = chartCanvas.getContext('2d');
        if(window.expChart) window.expChart.destroy();

        window.expChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: data.labels.length ? data.labels : ['No Data'],
            datasets: [
              { label: 'Actual', data: data.actual || [0], backgroundColor: 'rgba(255,110,110,0.6)' },
              { label: 'Predicted', data: data.predicted || [0], backgroundColor: 'rgba(0,198,255,0.6)' }
            ]
          },
          options: {
            plugins: { legend: { labels: { color: '#fff' } } },
            scales: { x: { ticks: { color: '#A8B3CF' } }, y: { ticks: { color: '#A8B3CF' } } }
          }
        });
      } catch (err) {
        console.error('Chart error:', err);
      }
    }

    await renderExpenseChart();
  }

  // ---- INIT ----
  async function pageInit(){
    const path = window.location.pathname.split('/').pop();
    if(path.includes('dashboard')){
      await updateDashboard();
      await setupDashboardUI();
    }
    if(path.includes('transactions')) await renderTxns();
    if(path.includes('goals')) await renderGoals();
    if(path.includes('prediction')) await renderPredictionPage();
    if(path.includes('budget')) await fetchAndRenderBudget(); // budget page load
  }

  // expose public API (keeps original names)
  return {
    login, signup, logout, resetPassword,
    addTransaction, renderTxns, addGoal, renderGoals,
    renderPredictionPage, updateDashboard, pageInit,
    addBudget, fetchAndRenderBudget
  };
})();

window.addEventListener('load', ()=>{ try{ ui.pageInit(); }catch(e){ console.error(e); } });
