document.addEventListener('DOMContentLoaded', () => {
  if (!document.getElementById('monthlyExpenseChart')) return;

  const stats = Store.getStats();
  if (document.getElementById('kpiTotal')) document.getElementById('kpiTotal').innerText = stats.totalDocs;
  if (document.getElementById('kpiToday')) document.getElementById('kpiToday').innerText = stats.todayDocs;

  const docs = Store.getDocuments();
  const tbody = document.getElementById('recentDocsTableBody');
  if (tbody) {
    tbody.innerHTML = docs.slice(0, 5).map(doc => `
      <tr>
        <td><i class="bi bi-file-earmark-pdf text-danger me-2"></i><strong>${doc.name}</strong></td>
        <td>${doc.category || 'General'}</td>
        <td>${doc.division || 'Finance'}</td>
        <td>${doc.vendor || 'N/A'}</td>
        <td>${doc.date}</td>
        <td><span class="badge bg-success-subtle text-success rounded-pill px-3">${doc.status || 'Verified'}</span></td>
        <td><button class="btn btn-sm btn-light rounded-circle"><i class="bi bi-three-dots-vertical"></i></button></td>
      </tr>
    `).join('');
  }

  const ctxLine = document.getElementById('monthlyExpenseChart').getContext('2d');
  new Chart(ctxLine, {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [{
        label: 'Expense ($)',
        data: [12000, 19000, 15000, 22000, 30000, 48500],
        borderColor: '#16A34A',
        backgroundColor: 'rgba(22, 163, 74, 0.1)',
        fill: true,
        tension: 0.3
      }]
    }
  });

  const ctxDoughnut = document.getElementById('expenseDivisionChart').getContext('2d');
  new Chart(ctxDoughnut, {
    type: 'doughnut',
    data: {
      labels: ['Finance', 'Legal', 'Accounting', 'Operations'],
      datasets: [{
        data: [40, 20, 25, 15],
        backgroundColor: ['#16A34A', '#22C55E', '#14532D', '#86EFAC']
      }]
    },
    options: { plugins: { legend: { position: 'bottom' } } }
  });
});