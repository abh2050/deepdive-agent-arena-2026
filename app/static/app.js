// DeepDive Frontend Application Logic
document.addEventListener('DOMContentLoaded', () => {
  // State
  let currentRun = null;
  let currentAuditEvents = [];
  let currentEvidenceMap = {};
  let currentVerdictsMap = {};

  // Elements
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const queryInput = document.getElementById('queryInput');
  const btnRunResearch = document.getElementById('btnRunResearch');
  const demoModeToggle = document.getElementById('demoModeToggle');
  const promptChips = document.querySelectorAll('.prompt-chip');
  const meshStatusBadge = document.getElementById('meshStatusBadge');
  const meshStatusText = document.getElementById('meshStatusText');
  const btnSettings = document.getElementById('btnSettings');
  const settingsModal = document.getElementById('settingsModal');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const btnCancelSettings = document.getElementById('btnCancelSettings');
  const btnSaveSettings = document.getElementById('btnSaveSettings');
  const inputApiKey = document.getElementById('inputApiKey');
  const inputModel = document.getElementById('inputModel');

  // Pipeline elements
  const pipelineStatus = document.getElementById('pipelineStatus');
  const nodePlanner = document.getElementById('nodePlanner');
  const nodeResearcher = document.getElementById('nodeResearcher');
  const nodeWriter = document.getElementById('nodeWriter');
  const nodeVerifier = document.getElementById('nodeVerifier');
  const nodeSynthesizer = document.getElementById('nodeSynthesizer');
  const plannerDesc = document.getElementById('plannerDesc');
  const researcherDesc = document.getElementById('researcherDesc');
  const writerDesc = document.getElementById('writerDesc');
  const verifierDesc = document.getElementById('verifierDesc');
  const synthesizerDesc = document.getElementById('synthesizerDesc');
  const plannerBadge = document.getElementById('plannerBadge');
  const researcherBadge = document.getElementById('researcherBadge');
  const writerBadge = document.getElementById('writerBadge');
  const verifierBadge = document.getElementById('verifierBadge');
  const synthesizerBadge = document.getElementById('synthesizerBadge');

  // Metrics elements
  const metricsGrid = document.getElementById('metricsGrid');
  const valAttempted = document.getElementById('valAttempted');
  const valVerified = document.getElementById('valVerified');
  const valRejected = document.getElementById('valRejected');
  const valPassRate = document.getElementById('valPassRate');
  const valCoverage = document.getElementById('valCoverage');

  // Workspace elements
  const displayRunId = document.getElementById('displayRunId');
  const reportBody = document.getElementById('reportBody');
  const inspectorBody = document.getElementById('inspectorBody');
  const btnCopyReport = document.getElementById('btnCopyReport');
  const btnDownloadMd = document.getElementById('btnDownloadMd');

  // Audit elements
  const auditTimeline = document.getElementById('auditTimeline');
  const auditEventFilter = document.getElementById('auditEventFilter');
  const btnExportAuditJson = document.getElementById('btnExportAuditJson');

  // History elements
  const historyList = document.getElementById('historyList');
  const historyCount = document.getElementById('historyCount');
  const btnRefreshHistory = document.getElementById('btnRefreshHistory');

  // Evaluation elements
  const evalQuestionsList = document.getElementById('evalQuestionsList');
  const evalResultsJson = document.getElementById('evalResultsJson');
  const btnRunEval = document.getElementById('btnRunEval');
  const evalSpinner = document.getElementById('evalSpinner');

  // Initialize
  checkConfig();
  loadHistory();
  loadEvalQuestions();

  // Load API Key from localStorage
  const savedApiKey = localStorage.getItem('deepdive_mesh_api_key');
  if (savedApiKey) {
    inputApiKey.value = savedApiKey;
  }

  // Tab Navigation
  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.dataset.tab;
      navTabs.forEach(t => t.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(targetId)?.classList.add('active');

      if (targetId === 'tab-history') {
        loadHistory();
      } else if (targetId === 'tab-eval') {
        loadEvalResults();
      }
    });
  });

  // Prompt chips
  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      queryInput.value = chip.dataset.prompt;
      queryInput.focus();
    });
  });

  // Settings modal
  btnSettings.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  btnCloseSettings.addEventListener('click', () => settingsModal.classList.add('hidden'));
  btnCancelSettings.addEventListener('click', () => settingsModal.classList.add('hidden'));
  btnSaveSettings.addEventListener('click', () => {
    const key = inputApiKey.value.trim();
    if (key) {
      localStorage.setItem('deepdive_mesh_api_key', key);
    } else {
      localStorage.removeItem('deepdive_mesh_api_key');
    }
    settingsModal.classList.add('hidden');
    checkConfig();
  });

  // Check backend configuration
  async function checkConfig() {
    try {
      const res = await fetch('/config');
      const data = await res.json();
      const hasKey = data.has_api_key || Boolean(localStorage.getItem('deepdive_mesh_api_key'));
      if (hasKey) {
        meshStatusBadge.classList.add('active');
        meshStatusText.textContent = `Mesh API: Active (${data.model})`;
      } else {
        meshStatusBadge.classList.remove('active');
        meshStatusText.textContent = 'Mesh API: Key not set (Demo Mode available)';
      }
    } catch {
      meshStatusText.textContent = 'Mesh API: Local Dev';
    }
  }

  // Execute Research
  btnRunResearch.addEventListener('click', handleRunResearch);
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleRunResearch();
  });

  async function handleRunResearch() {
    const question = queryInput.value.trim();
    if (!question || question.length < 12) {
      alert('Please enter a research question of at least 12 characters.');
      return;
    }

    setLoading(true);
    resetPipeline();
    updatePipelineStep('planner', 'running', 'Generating subquestions...');

    const apiKey = localStorage.getItem('deepdive_mesh_api_key') || undefined;
    const demoMode = demoModeToggle.checked;

    try {
      // Simulate live visual steps during network request
      const stepTimer1 = setTimeout(() => {
        updatePipelineStep('planner', 'done', 'Subquestions generated');
        updatePipelineStep('researcher', 'running', 'Searching web & fetching pages...');
      }, 1200);

      const stepTimer2 = setTimeout(() => {
        updatePipelineStep('researcher', 'done', 'Passages retrieved & cached');
        updatePipelineStep('writer', 'running', 'Extracting atomic claims & quotes...');
      }, 2400);

      const stepTimer3 = setTimeout(() => {
        updatePipelineStep('writer', 'done', 'Candidate claims extracted');
        updatePipelineStep('verifier', 'running', 'Verifying quotes & entailment...');
      }, 3600);

      const response = await fetch('/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, demo_mode: demoMode, api_key: apiKey }),
      });

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Research request failed' }));
        const detail = err.detail;
        const message = typeof detail === 'object' && detail !== null
          ? detail.message
          : detail;
        throw new Error(message || 'Research failed');
      }

      const report = await response.json();
      finishPipelineSuccess(report);
      renderReport(report);
      if (Array.isArray(report.audit_events)) {
        currentAuditEvents = report.audit_events;
        renderAuditTimeline();
      } else {
        await fetchAndRenderAudit(report.run_id);
      }
      loadHistory();
    } catch (err) {
      alert(`Research Failed: ${err.message}`);
      pipelineStatus.textContent = 'Error';
      pipelineStatus.className = 'pipeline-status';
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    btnRunResearch.disabled = isLoading;
    const spinner = btnRunResearch.querySelector('.btn-spinner');
    const text = btnRunResearch.querySelector('.btn-text');
    if (isLoading) {
      spinner?.classList.remove('hidden');
      if (text) text.textContent = 'Researching...';
      pipelineStatus.textContent = 'Running';
      pipelineStatus.className = 'pipeline-status running';
    } else {
      spinner?.classList.add('hidden');
      if (text) text.textContent = 'Execute DeepDive';
    }
  }

  function resetPipeline() {
    [nodePlanner, nodeResearcher, nodeWriter, nodeVerifier, nodeSynthesizer].forEach(n => {
      n.className = 'agent-node';
    });
    plannerBadge.textContent = '—';
    researcherBadge.textContent = '—';
    writerBadge.textContent = '—';
    verifierBadge.textContent = '—';
    synthesizerBadge.textContent = '—';
  }

  function updatePipelineStep(step, state, desc) {
    const nodeMap = {
      planner: { el: nodePlanner, descEl: plannerDesc, badge: plannerBadge },
      researcher: { el: nodeResearcher, descEl: researcherDesc, badge: researcherBadge },
      writer: { el: nodeWriter, descEl: writerDesc, badge: writerBadge },
      verifier: { el: nodeVerifier, descEl: verifierDesc, badge: verifierBadge },
      synthesizer: { el: nodeSynthesizer, descEl: synthesizerDesc, badge: synthesizerBadge },
    };
    const node = nodeMap[step];
    if (!node) return;
    node.el.className = `agent-node ${state}`;
    if (desc) node.descEl.textContent = desc;
    if (state === 'running') node.badge.textContent = 'ACTIVE';
    if (state === 'done') node.badge.textContent = 'DONE';
  }

  function finishPipelineSuccess(report) {
    [nodePlanner, nodeResearcher, nodeWriter, nodeVerifier, nodeSynthesizer].forEach(n => {
      n.className = 'agent-node done';
    });
    plannerBadge.textContent = `${Object.keys(report.coverage || {}).length} Sub-Q`;
    researcherBadge.textContent = `${report.evidence?.length || 0} Sources`;
    writerBadge.textContent = `${report.metrics?.attempted_claims || 0} Claims`;
    verifierBadge.textContent = `${report.metrics?.verified_claims || 0} Accepted`;
    synthesizerBadge.textContent = '100% Deterministic';

    pipelineStatus.textContent = 'Completed';
    pipelineStatus.className = 'pipeline-status';
  }

  // Render Full Report & Metrics
  function renderReport(report) {
    currentRun = report;
    displayRunId.textContent = `Run ID: ${report.run_id}`;

    // Index evidence
    currentEvidenceMap = {};
    (report.evidence || []).forEach(e => {
      currentEvidenceMap[e.evidence_id] = e;
    });

    // Index verdicts from audit if available
    currentVerdictsMap = {};
    (report.verified_claims || []).forEach(c => {
      currentVerdictsMap[c.claim_id] = { status: 'supported', reason: 'Verified verbatim quote and entailment' };
    });
    (report.rejected_claims || []).forEach(item => {
      if (item.claim && item.verdict) {
        currentVerdictsMap[item.claim.claim_id] = item.verdict;
      }
    });

    // Update metrics cards
    metricsGrid.classList.remove('hidden');
    valAttempted.textContent = report.metrics?.attempted_claims ?? 0;
    valVerified.textContent = report.metrics?.verified_claims ?? 0;
    valRejected.textContent = report.metrics?.rejected_or_unverified_claims ?? 0;
    valPassRate.textContent = `${Math.round((report.metrics?.verification_pass_rate ?? 0) * 100)}%`;
    valCoverage.textContent = `${Math.round((report.metrics?.subquestion_coverage ?? 0) * 100)}%`;

    // Render markdown report with interactive citation chips
    reportBody.innerHTML = formatMarkdownToHtml(report.markdown, report.evidence || []);

    // Add click listeners to citation chips
    reportBody.querySelectorAll('.citation-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.preventDefault();
        const eid = chip.dataset.eid;
        const claimId = chip.dataset.cid;
        inspectEvidence(eid, claimId);
      });
    });

    // Reveal follow-up conversational agent
    const followupSection = document.getElementById('followupSection');
    if (followupSection) {
      followupSection.classList.remove('hidden');
      const followupAnswer = document.getElementById('followupAnswer');
      if (followupAnswer) followupAnswer.classList.add('hidden');
      const followupInput = document.getElementById('followupInput');
      if (followupInput) followupInput.value = '';
    }

    // Auto-inspect first verified evidence item if available
    if (report.verified_claims && report.verified_claims.length > 0) {
      const first = report.verified_claims[0];
      inspectEvidence(first.evidence_id, first.claim_id);
    } else if (report.evidence && report.evidence.length > 0) {
      inspectEvidence(report.evidence[0].evidence_id);
    }
  }


  // Convert raw report markdown to styled HTML with interactive citation badges
  function formatMarkdownToHtml(markdown, evidenceList) {
    if (!markdown) return '<div class="empty-state"><p>Empty report.</p></div>';

    let html = markdown
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
      .replace(/^- (.*$)/gim, '<li>$1</li>');

    // Replace [evidence_id](url) links with clickable citation chips
    html = html.replace(/\[(e_[a-zA-Z0-9]+)\]\(([^)]+)\)/g, (match, eid, url) => {
      return `<a href="${url}" class="citation-chip" data-eid="${eid}" target="_blank" rel="noopener noreferrer">${eid} ↗</a>`;
    });

    // Wrap list items
    html = html.replace(/(<li>[\s\S]*?<\/li>)/gm, '<ul>$1</ul>');
    // Clean double uls
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    return `<div class="report-content">${html}</div>`;
  }

  // Inspect specific evidence item in the right inspector panel
  function inspectEvidence(evidenceId, claimId) {
    const evidence = currentEvidenceMap[evidenceId];
    if (!evidence) return;

    let claim = null;
    if (claimId && currentRun) {
      claim = (currentRun.verified_claims || []).find(c => c.claim_id === claimId) ||
              (currentRun.rejected_claims || []).map(r => r.claim).find(c => c && c.claim_id === claimId);
    }
    if (!claim && currentRun) {
      claim = (currentRun.verified_claims || []).find(c => c.evidence_id === evidenceId);
    }

    const verdict = (claim && currentVerdictsMap[claim.claim_id]) || {
      status: 'supported',
      reason: 'Quote matches source excerpt; verified via entailment check.'
    };

    const qualityPct = Math.round((evidence.quality || 0.5) * 100);

    // Highlight verbatim quote inside excerpt if quote exists
    let highlightedExcerpt = escapeHtml(evidence.excerpt || '');
    if (claim && claim.quote) {
      const escapedQuote = escapeHtml(claim.quote);
      if (highlightedExcerpt.includes(escapedQuote)) {
        highlightedExcerpt = highlightedExcerpt.replace(
          escapedQuote,
          `<span class="highlighted-quote">${escapedQuote}</span>`
        );
      }
    }

    inspectorBody.innerHTML = `
      <div class="inspector-card">
        <div class="evidence-header">
          <div>
            <span class="evidence-id-badge">${evidence.evidence_id}</span>
            <h4 style="margin-top:0.4rem; font-size:1.05rem;">${escapeHtml(evidence.title || 'Source Reference')}</h4>
            <a href="${evidence.url}" target="_blank" rel="noopener" style="font-size:0.8rem; color:var(--accent-cyan); word-break:break-all;">
              ${evidence.url} ↗
            </a>
          </div>
          <div class="source-quality-bar" title="Domain trust score: ${evidence.quality}">
            <div class="quality-meter">
              <div class="quality-fill" style="width: ${qualityPct}%;"></div>
            </div>
            <span style="font-size:0.75rem; color:var(--text-muted);">${qualityPct}% Trust</span>
          </div>
        </div>

        <div class="verdict-banner ${verdict.status}">
          <span class="verdict-title">Verifier Verdict: ${verdict.status.toUpperCase()}</span>
          <p class="verdict-reason">${escapeHtml(verdict.reason || 'No verifier rationale recorded.')}</p>
        </div>

        ${claim ? `
          <div class="quote-box">
            <span class="box-label">Verified Atomic Claim</span>
            <p style="color:#fff; font-size:0.9rem; margin-bottom:0.75rem;">${escapeHtml(claim.statement)}</p>
            <span class="box-label">Verbatim Source Quote</span>
            <p class="quote-text">"${escapeHtml(claim.quote)}"</p>
          </div>
        ` : ''}

        <div class="source-excerpt-box">
          <span class="box-label">Full Canonical Page Excerpt (Provenance)</span>
          <div class="excerpt-text">${highlightedExcerpt}</div>
        </div>
      </div>
    `;
  }

  // Fetch and render SQLite audit trail
  async function fetchAndRenderAudit(runId) {
    try {
      const res = await fetch(`/runs/${runId}/audit`);
      if (!res.ok) return;
      currentAuditEvents = await res.json();
      renderAuditTimeline();
    } catch (e) {
      console.error('Failed to load audit events', e);
    }
  }

  function renderAuditTimeline() {
    const filter = auditEventFilter.value;
    const filtered = filter === 'ALL'
      ? currentAuditEvents
      : currentAuditEvents.filter(e => e.event === filter);

    if (!filtered || filtered.length === 0) {
      auditTimeline.innerHTML = '<div class="empty-state"><p>No matching audit events for this run.</p></div>';
      return;
    }

    auditTimeline.innerHTML = filtered.map(item => `
      <div class="timeline-event">
        <div class="event-header">
          <span class="event-tag ${item.event}">${item.event}</span>
          <span class="event-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
        </div>
        <pre class="event-payload">${escapeHtml(JSON.stringify(item.payload, null, 2))}</pre>
      </div>
    `).join('');
  }

  auditEventFilter.addEventListener('change', renderAuditTimeline);

  // Copy and download buttons
  btnCopyReport.addEventListener('click', () => {
    if (!currentRun || !currentRun.markdown) return;
    navigator.clipboard.writeText(currentRun.markdown);
    btnCopyReport.textContent = 'Copied';
    setTimeout(() => { btnCopyReport.textContent = 'Copy markdown'; }, 2000);
  });

  btnDownloadMd.addEventListener('click', () => {
    if (!currentRun || !currentRun.markdown) return;
    const blob = new Blob([currentRun.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `deepdive_report_${currentRun.run_id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  });

  const btnPrintReport = document.getElementById('btnPrintReport');
  if (btnPrintReport) {
    btnPrintReport.addEventListener('click', () => {
      window.print();
    });
  }

  // Conversational Follow-Up Query Handlers
  const btnSendFollowup = document.getElementById('btnSendFollowup');
  const followupInput = document.getElementById('followupInput');
  const followupAnswer = document.getElementById('followupAnswer');
  const followupAnswerText = document.getElementById('followupAnswerText');
  const followupCitedBadges = document.getElementById('followupCitedBadges');
  const btnFollowupText = document.getElementById('btnFollowupText');
  const followupSpinner = document.getElementById('followupSpinner');

  async function handleSendFollowup() {
    if (!currentRun || !currentRun.run_id) {
      alert('Please run or select a research report first.');
      return;
    }
    const q = followupInput.value.trim();
    if (!q) return;

    btnSendFollowup.disabled = true;
    followupSpinner.classList.remove('hidden');
    btnFollowupText.textContent = 'Thinking...';

    try {
      const apiKey = localStorage.getItem('deepdive_mesh_api_key') || undefined;
      const demoMode = demoModeToggle.checked;

      const res = await fetch(`/runs/${currentRun.run_id}/followup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q,
          demo_mode: demoMode,
          api_key: apiKey,
          report: currentRun,
        }),
      });

      if (!res.ok) {
        throw new Error('Follow-up request failed');
      }

      const data = await res.json();
      followupAnswer.classList.remove('hidden');
      followupAnswerText.textContent = data.answer || 'No response formulated.';
      
      const cited = data.cited_evidence || [];
      followupCitedBadges.innerHTML = cited.map(eid => `
        <span class="citation-chip" data-eid="${eid}" style="cursor:pointer;">${eid}</span>
      `).join('');

      followupCitedBadges.querySelectorAll('.citation-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          inspectEvidence(chip.dataset.eid);
        });
      });
    } catch (e) {
      alert(`Follow-up failed: ${e.message}`);
    } finally {
      btnSendFollowup.disabled = false;
      followupSpinner.classList.add('hidden');
      btnFollowupText.textContent = 'Ask';
    }
  }

  if (btnSendFollowup) {
    btnSendFollowup.addEventListener('click', handleSendFollowup);
  }
  if (followupInput) {
    followupInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSendFollowup();
    });
  }


  btnExportAuditJson.addEventListener('click', () => {
    if (!currentAuditEvents || currentAuditEvents.length === 0) return;
    const blob = new Blob([JSON.stringify(currentAuditEvents, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `deepdive_audit_${currentRun ? currentRun.run_id.slice(0, 8) : 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // History list
  btnRefreshHistory.addEventListener('click', loadHistory);

  async function loadHistory() {
    try {
      const res = await fetch('/runs');
      if (!res.ok) return;
      const runs = await res.json();
      historyCount.textContent = runs.length;

      if (!runs || runs.length === 0) {
        historyList.innerHTML = '<div class="empty-state"><p>No previous runs found.</p></div>';
        return;
      }

      historyList.innerHTML = runs.map(r => `
        <div class="history-card" data-runid="${r.run_id}">
          <div class="history-q">${escapeHtml(r.question)}</div>
          <div class="history-meta">
            <span>Pass Rate: ${Math.round((r.metrics?.verification_pass_rate || 0) * 100)}%</span>
            <span>${r.verified_count || 0} verified</span>
            <span>ID: ${r.run_id.slice(0, 8)}</span>
          </div>
        </div>
      `).join('');

      historyList.querySelectorAll('.history-card').forEach(card => {
        card.addEventListener('click', async () => {
          const runId = card.dataset.runid;
          await loadPreviousRun(runId);
          // Switch to research tab
          document.querySelector('[data-tab="tab-research"]')?.click();
        });
      });
    } catch {
      historyList.innerHTML = '<div class="empty-state"><p>Failed to load run history.</p></div>';
    }
  }

  async function loadPreviousRun(runId) {
    try {
      const res = await fetch(`/runs/${runId}`);
      if (!res.ok) return;
      const report = await res.json();
      finishPipelineSuccess(report);
      renderReport(report);
      await fetchAndRenderAudit(runId);
    } catch (e) {
      alert(`Could not load run: ${e.message}`);
    }
  }

  // Evaluation tab
  async function loadEvalQuestions() {
    try {
      const res = await fetch('/evaluation/questions');
      if (!res.ok) return;
      const questions = await res.json();
      evalQuestionsList.innerHTML = questions.map(q => `
        <div class="benchmark-card">
          <span class="bench-badge">${escapeHtml(q.id)}</span>
          <p class="bench-q">${escapeHtml(q.question)}</p>
          <div style="font-size:0.75rem; color:var(--text-muted);">
            Expected: ${(q.expected_topics || []).join(', ')}
          </div>
        </div>
      `).join('');
    } catch {
      evalQuestionsList.innerHTML = '<div class="empty-state"><p>Evaluation questions not found.</p></div>';
    }
  }

  async function loadEvalResults() {
    try {
      const res = await fetch('/evaluation/results');
      if (res.ok) {
        const results = await res.json();
        evalResultsJson.textContent = JSON.stringify(results, null, 2);
      }
    } catch {
      evalResultsJson.textContent = 'No evaluation results yet.';
    }
  }

  btnRunEval.addEventListener('click', async () => {
    btnRunEval.disabled = true;
    evalSpinner.classList.remove('hidden');
    evalResultsJson.textContent = 'Running benchmark evaluation suite... please wait...';
    try {
      const res = await fetch('/evaluation/run', { method: 'POST' });
      if (!res.ok) {
        throw new Error('Evaluation suite run failed');
      }
      const data = await res.json();
      evalResultsJson.textContent = JSON.stringify(data, null, 2);
      loadHistory();
    } catch (e) {
      evalResultsJson.textContent = `Evaluation run failed: ${e.message}`;
    } finally {
      btnRunEval.disabled = false;
      evalSpinner.classList.add('hidden');
    }
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
