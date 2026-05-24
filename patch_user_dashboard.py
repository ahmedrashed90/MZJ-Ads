from pathlib import Path
p=Path('/mnt/data/work_userdash/assets/js/app.js')
s=p.read_text()
# Insert helpers after campaignPublishProgress
needle="function campaignPublishProgress(campaign){\n  const stages = campaign.publishStages || {};\n  return (stages.prep ? 35 : 0) + (stages.approval ? 30 : 0) + (stages.publish ? 35 : 0);\n}\n"
insert=needle+r'''
function currentUserMatchesTask(task){
  const user = getCurrentUser();
  const keys = [user.uid, user.id, user.email, user.name].map(normalizeText).filter(Boolean);
  const taskKeys = [task.assignedToUid, task.assignedToId, task.assignedToEmail, task.assignedToName].map(normalizeText).filter(Boolean);
  return keys.some(key => taskKeys.includes(key));
}
function getVisibleTasksForCurrentUser(){
  const current = getCurrentUser();
  if(isCurrentUserAdmin()) return campaigns.flatMap(campaign => tasksForCampaign(campaign));
  return campaigns.flatMap(campaign => tasksForCampaign(campaign)).filter(task => currentUserMatchesTask(task));
}
function findTaskById(taskId, campaignId = ''){
  const saved = campaignTasks.find(task => task.id === taskId);
  if(saved) return saved;
  const campaignList = campaignId ? campaigns.filter(item => item.id === campaignId) : campaigns;
  for(const campaign of campaignList){
    const found = fallbackTasksFromCampaign(campaign).find(task => task.id === taskId);
    if(found) return found;
  }
  return null;
}
function campaignForTask(task){
  return campaigns.find(item => item.id === task?.campaignId || item.docId === task?.campaignId) || {};
}
function stepButtonClass(step){ return step.done ? 'step-btn done' : 'step-btn'; }
function stepButtonTitle(step){ return step.adminOnly ? 'اعتماد الأدمن فقط' : 'تنفيذ المرحلة'; }
async function updateTaskOnFirebase(taskId, patch){
  if(!mainDb || !taskId || taskId.startsWith('fallback-')){
    showToast('التاسك غير محفوظ على Firebase بعد. احفظ الحملة مرة أخرى.');
    return;
  }
  try{
    await safeCollection(window.MZJ_CAMPAIGN_TASKS_COLLECTION).doc(taskId).update({ ...patch, updatedAt: serverTime() });
    showToast('تم تحديث التاسك.');
  }catch(error){
    console.error('Task update error', error, patch);
    showToast('تعذر تحديث التاسك على Firebase.');
  }
}
function buildTaskDetailHtml(task){
  const campaign = campaignForTask(task);
  const admin = isCurrentUserAdmin();
  const steps = Array.isArray(task.steps) && task.steps.length ? task.steps : taskStepTemplate(task.departmentRole || 'other');
  return `<div class="detail-head"><div><h2>${escapeHtml(task.creative || task.product || 'تاسك')}</h2><p>${escapeHtml([campaign.campaignName || campaign.name, campaign.campaignCode || task.campaignCode].filter(Boolean).join(' · '))}</p></div><button type="button" class="mini-btn" id="closeDashboardDetail">إغلاق</button></div>
    <article class="task-detail-panel">
      <div class="task-detail-info">
        <span>المحتوى: <strong>${escapeHtml(task.contentSectionName || '—')}</strong></span>
        <span>نوع التاسك: <strong>${escapeHtml(task.taskType || '—')}</strong></span>
        <span>اليوزر: <strong>${escapeHtml(task.assignedToName || 'غير محدد')}</strong></span>
        <span>القسم: <strong>${escapeHtml(task.assignedDepartmentName || task.departmentRole || '—')}</strong></span>
        <span>النسبة: <strong>${taskProgress(task)}%</strong></span>
      </div>
      <div class="task-receive-row">
        <button type="button" class="mini-btn ${task.received ? 'done' : ''}" data-toggle-received="${escapeHtml(task.id)}">${task.received ? 'تم الاستلام' : 'تأكيد الاستلام'}</button>
      </div>
      <div class="task-step-grid">
        ${steps.map((step, index) => `<button type="button" class="${stepButtonClass(step)}" data-task-step="${escapeHtml(task.id)}" data-step-index="${index}" ${step.adminOnly && !admin ? 'disabled' : ''} title="${stepButtonTitle(step)}"><span>${escapeHtml(step.label)}</span><strong>${Number(step.percent || 0)}%</strong>${step.adminOnly ? '<em>أدمن</em>' : ''}</button>`).join('')}
      </div>
    </article>`;
}
function renderTaskDetail(taskId, campaignId = ''){
  const detail = document.getElementById('dashboardCampaignDetail');
  const task = findTaskById(taskId, campaignId);
  if(!detail || !task) return;
  detail.classList.add('show');
  detail.innerHTML = buildTaskDetailHtml(task);
}
async function toggleTaskStep(taskId, stepIndex){
  const task = findTaskById(taskId);
  if(!task) return;
  const steps = Array.isArray(task.steps) && task.steps.length ? task.steps.map(step => ({...step})) : taskStepTemplate(task.departmentRole || 'other');
  const step = steps[Number(stepIndex)];
  if(!step) return;
  if(step.adminOnly && !isCurrentUserAdmin()){
    showToast('الاعتماد للأدمن فقط.');
    return;
  }
  step.done = !step.done;
  const progress = Math.min(100, Math.round(steps.reduce((sum, item) => sum + (item.done ? Number(item.percent || 0) : 0), 0)));
  await updateTaskOnFirebase(task.id, { steps, progress, status: progress >= 100 ? 'done' : 'in_progress' });
}
async function toggleTaskReceived(taskId){
  const task = findTaskById(taskId);
  if(!task) return;
  await updateTaskOnFirebase(task.id, { received: !task.received, status: !task.received ? 'received' : 'pending' });
}
'''
s=s.replace(needle,insert)
# Replace renderAdminDashboard with version that branches? Insert renderUserDashboard before renderAdminDashboard and modify start
needle2="function renderAdminDashboard(){\n  const count = document.getElementById('dashboardCampaignsCount'); if(count) count.textContent = campaigns.length || '—';\n  const tasksCount = document.getElementById('dashboardTasksCount'); if(tasksCount) tasksCount.textContent = campaignTasks.length || '—';\n  const adminBoard = document.getElementById('adminDashboardBoard');\n  if(!adminBoard) return;\n"
replace2=r'''function renderUserDashboard(){
  const board = document.getElementById('adminDashboardBoard');
  if(!board) return;
  const myTasks = getVisibleTasksForCurrentUser();
  const received = myTasks.filter(task => task.received).length;
  const done = myTasks.filter(task => taskProgress(task) >= 100).length;
  const groups = groupTasksForKanban(myTasks);
  const taskCard = task => `<article class="kanban-task-card user-task-card" data-open-task="${escapeHtml(task.id)}" data-task-campaign="${escapeHtml(task.campaignId || '')}">
    <div class="kanban-task-main"><strong>${escapeHtml(task.creative || task.product || 'تاسك')}</strong><span>${taskProgress(task)}%</span></div>
    <p>${escapeHtml([task.contentSectionName, task.taskType].filter(Boolean).join(' / ') || 'بدون نوع')}</p>
    <div class="kanban-task-meta"><span>${escapeHtml(task.campaignName || task.campaignCode || 'حملة')}</span><span>${task.received ? 'تم الاستلام' : 'لم يتم الاستلام'}</span></div>
  </article>`;
  board.innerHTML = `<section class="user-dashboard-panel">
    <div class="user-dash-head"><div><h2>تاسكاتي</h2><p>التاسكات المسندة لحسابك حسب المحتوى المطلوب.</p></div><div class="user-task-stats"><span>${myTasks.length} تاسك</span><span>${received} مستلم</span><span>${done} مكتمل</span></div></div>
    ${groups.length ? `<div class="task-kanban-board user-task-board">${groups.map(group => `<section class="task-kanban-col"><div class="kanban-col-head"><strong>${group.label}</strong><span>${group.tasks.length}</span></div><div class="kanban-col-list">${group.tasks.map(taskCard).join('')}</div></section>`).join('')}</div>` : '<div class="empty-state">لا توجد تاسكات مسندة لك حالياً.</div>'}
  </section>`;
}
function renderAdminDashboard(){
  const allTasks = campaigns.flatMap(campaign => tasksForCampaign(campaign));
  const count = document.getElementById('dashboardCampaignsCount'); if(count) count.textContent = campaigns.length || '—';
  const tasksCount = document.getElementById('dashboardTasksCount'); if(tasksCount) tasksCount.textContent = allTasks.length || '—';
  const adminBoard = document.getElementById('adminDashboardBoard');
  if(!adminBoard) return;
  if(!isCurrentUserAdmin()) { renderUserDashboard(); return; }
'''
s=s.replace(needle2,replace2)
# Replace renderCampaignDetail taskCard to include data-open-task and button marker
old="""  const taskCard = task => `<article class="kanban-task-card">
    <div class="kanban-task-main"><strong>${escapeHtml(task.creative || task.product || 'تاسك')}</strong><span>${taskProgress(task)}%</span></div>
    <p>${escapeHtml([task.contentSectionName, task.taskType].filter(Boolean).join(' / ') || 'بدون نوع')}</p>
    <div class="kanban-task-meta"><span>${escapeHtml(task.assignedToName || 'غير محدد')}</span><span>${task.received ? 'تم الاستلام' : 'لم يتم الاستلام'}</span></div>
  </article>`;
"""
new="""  const taskCard = task => `<article class="kanban-task-card" data-open-task="${escapeHtml(task.id)}" data-task-campaign="${escapeHtml(campaign.id || task.campaignId || '')}">
    <div class="kanban-task-main"><strong>${escapeHtml(task.creative || task.product || 'تاسك')}</strong><span>${taskProgress(task)}%</span></div>
    <p>${escapeHtml([task.contentSectionName, task.taskType].filter(Boolean).join(' / ') || 'بدون نوع')}</p>
    <div class="kanban-task-meta"><span>${escapeHtml(task.assignedToName || 'غير محدد')}</span><span>${task.received ? 'تم الاستلام' : 'لم يتم الاستلام'}</span></div>
  </article>`;
"""
s=s.replace(old,new)
# add event handling in dashboard click before campaignCard
old_event="""    const campaignCard = event.target.closest('[data-open-campaign]');
    if(campaignCard){ renderCampaignDetail(campaignCard.dataset.openCampaign); return; }
    if(event.target.id === 'closeDashboardDetail'){ document.getElementById('dashboardCampaignDetail')?.classList.remove('show'); }
"""
new_event="""    const receivedBtn = event.target.closest('[data-toggle-received]');
    if(receivedBtn){ await toggleTaskReceived(receivedBtn.dataset.toggleReceived); return; }
    const stepBtn = event.target.closest('[data-task-step]');
    if(stepBtn){ await toggleTaskStep(stepBtn.dataset.taskStep, stepBtn.dataset.stepIndex); return; }
    const taskCard = event.target.closest('[data-open-task]');
    if(taskCard){ renderTaskDetail(taskCard.dataset.openTask, taskCard.dataset.taskCampaign || ''); return; }
    const campaignCard = event.target.closest('[data-open-campaign]');
    if(campaignCard){ renderCampaignDetail(campaignCard.dataset.openCampaign); return; }
    if(event.target.id === 'closeDashboardDetail'){ document.getElementById('dashboardCampaignDetail')?.classList.remove('show'); }
"""
s=s.replace(old_event,new_event)
p.write_text(s)
