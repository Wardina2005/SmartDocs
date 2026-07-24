document.addEventListener('DOMContentLoaded', () => {
  const throughputElem = document.getElementById('reportThroughputChart');
  if (!throughputElem) return;

  new Chart(throughputElem, {
    type: 'bar',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      datasets: [{ label: 'Processed Docs', data: [45, 60, 75, 50, 80, 20], backgroundColor: '#16A34A' }]
    }
  });

  const accuracyElem = document.getElementById('reportAccuracyChart');
  if (accuracyElem) {
    new Chart(accuracyElem, {
      type: 'pie',
      data: {
        labels: ['High (>98%)', 'Medium (90-97%)', 'Low (<90%)'],
        datasets: [{ data: [85, 12, 3], backgroundColor: ['#16A34A', '#F59E0B', '#EF4444'] }]
      }
    });
  }
});