const Store = (() => {
  const DEFAULT_DOCUMENTS = [
    { id: 'DOC-1001', name: 'Vendor_Invoice_ACME.pdf', category: 'Invoice', division: 'Finance', vendor: 'ACME Corp', date: '2026-03-28', status: 'Approved', amount: '$4,250.00' },
    { id: 'DOC-1002', name: 'Q1_Tax_Report.pdf', category: 'Tax', division: 'Accounting', vendor: 'Internal', date: '2026-03-27', status: 'Verified', amount: '$12,800.00' },
    { id: 'DOC-1003', name: 'Software_License_Agreement.pdf', category: 'Contract', division: 'Legal', vendor: 'TechSoft Inc', date: '2026-03-25', status: 'Pending Review', amount: '$1,500.00' }
  ];

  const DEFAULT_LOGS = [
    { date: '2026-03-28', time: '14:32', user: 'Admin User', activity: 'Save Document', document: 'Vendor_Invoice_ACME.pdf', division: 'Finance', status: 'Success' },
    { date: '2026-03-27', time: '09:15', user: 'Admin User', activity: 'OCR Scan', document: 'Q1_Tax_Report.pdf', division: 'Accounting', status: 'Completed' }
  ];

  const init = () => {
    if (!localStorage.getItem('smartdocs_documents')) {
      localStorage.setItem('smartdocs_documents', JSON.stringify(DEFAULT_DOCUMENTS));
    }
    if (!localStorage.getItem('smartdocs_logs')) {
      localStorage.setItem('smartdocs_logs', JSON.stringify(DEFAULT_LOGS));
    }
    if (!localStorage.getItem('smartdocs_stats')) {
      localStorage.setItem('smartdocs_stats', JSON.stringify({
        totalDocs: 128,
        todayDocs: 4,
        monthlyExpense: 48500,
        ocrAccuracy: '99.2%',
        storageUsed: '42.8 GB / 100 GB'
      }));
    }
  };

  const getDocuments = () => JSON.parse(localStorage.getItem('smartdocs_documents')) || [];
  const getLogs = () => JSON.parse(localStorage.getItem('smartdocs_logs')) || [];
  const getStats = () => JSON.parse(localStorage.getItem('smartdocs_stats')) || {};

  const addDocument = (docData) => {
    const docs = getDocuments();
    docs.unshift(docData);
    localStorage.setItem('smartdocs_documents', JSON.stringify(docs));

    addLog({
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().split(' ')[0].substring(0, 5),
      user: 'Admin User',
      activity: 'Save Document',
      document: docData.name,
      division: docData.division || 'General',
      status: 'Success'
    });

    const stats = getStats();
    stats.totalDocs = (parseInt(stats.totalDocs) || 0) + 1;
    stats.todayDocs = (parseInt(stats.todayDocs) || 0) + 1;
    localStorage.setItem('smartdocs_stats', JSON.stringify(stats));
  };

  const addLog = (logItem) => {
    const logs = getLogs();
    logs.unshift(logItem);
    localStorage.setItem('smartdocs_logs', JSON.stringify(logs));
  };

  init();

  return { getDocuments, getLogs, getStats, addDocument, addLog };
})();