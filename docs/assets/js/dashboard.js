(() => {
  "use strict";

  const root = document.querySelector("[data-q25-dashboard]");
  if (!root) return;

  const bind = (name, value) => {
    if (value === undefined || value === null) return;
    root.querySelectorAll(`[data-bind="${name}"]`).forEach((node) => {
      node.textContent = value;
    });
  };

  const state = (name, value) => {
    root.querySelectorAll(`[data-bind="${name}"]`).forEach((node) => {
      node.dataset.state = value;
    });
  };

  const ratioText = (metric) => {
    if (!metric || metric.total === undefined || metric.count === undefined) return "—";
    return `${metric.count}/${metric.total}`;
  };

  const pct = (rate) => {
    if (rate === null || rate === undefined || Number.isNaN(Number(rate))) return 0;
    return Math.max(0, Math.min(100, Number(rate) * 100));
  };

  const setBar = (name, metric) => {
    const node = root.querySelector(`[data-bar="${name}"]`);
    if (node) node.style.width = `${pct(metric && metric.rate)}%`;
  };

  const fmt = (value, digits = 3) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
    return Number(value).toFixed(digits);
  };

  const shortCampaign = (value) => {
    if (!value) return "—";
    return String(value).replace(/^frontier_/, "");
  };

  const decisionClass = (decision) => {
    const text = String(decision || "").toUpperCase();
    if (text.includes("FAIL") || text.includes("FALSIFIED") || text.includes("KILL")) return "bad";
    if (text.includes("PASS") || text.includes("CONTINUE")) return "good";
    return "warn";
  };

  const renderTriage = (rows) => {
    const body = root.querySelector('[data-bind="triage-body"]');
    if (!body) return;
    body.innerHTML = "";
    if (!Array.isArray(rows) || rows.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 7;
      td.textContent = "No rankable family rows in the latest evidence packet.";
      tr.appendChild(td);
      body.appendChild(tr);
      return;
    }

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const support = row.control_supported === true ? "PASS" : row.control_supported === false ? "FAIL" : "—";
      const cells = [
        row.campaign_rank,
        row.family || "—",
        fmt(row.best_robust_sharpe),
        fmt(row.floor_margin),
        fmt(row.central_control_margin),
        support,
        row.decision_code || "—",
      ];
      cells.forEach((value, index) => {
        const td = document.createElement("td");
        td.textContent = String(value);
        if (index === 5) td.className = support === "PASS" ? "q25-support-pass" : support === "FAIL" ? "q25-support-fail" : "";
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  };

  fetch("data/methodology_health.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      const latest = data.latest_evidence || {};
      const loop = data.learning_loop || {};
      const campaign = loop.latest_campaign || {};
      const depth = loop.evidence_depth || {};
      const validation = loop.validation_feedback || {};
      const queue = loop.measurement_queue || {};
      const leader = data.development_leader || {};
      const next = queue.next_campaign || null;

      bind("latest-campaign", shortCampaign(latest.campaign));
      bind("latest-decision", latest.decision ? `${latest.decision} · ${latest.kind || "evidence"}` : latest.kind || "—");
      bind("falsification-ratio", ratioText(campaign.falsification_coverage));
      bind("causal-ratio", ratioText(campaign.causal_support));
      bind("economic-ratio", ratioText(campaign.economic_survival));
      bind("promotion-ratio", ratioText(campaign.promotion_ready));
      bind("matrix-lag", depth.measured_campaigns_since_full_matrix ?? "—");
      bind("matrix-lag-detail", depth.latest_full_matrix_campaign ? `campaigns since ${shortCampaign(depth.latest_full_matrix_campaign)} full matrix` : "no full matrix packet found");
      setBar("falsification", campaign.falsification_coverage);
      setBar("causal", campaign.causal_support);
      setBar("economic", campaign.economic_survival);
      setBar("promotion", campaign.promotion_ready);

      bind("evidence-tier", `evidence: ${latest.kind || "unknown"}`);
      state("evidence-tier", latest.kind === "summary_only" ? "warn" : "good");

      bind("validation-state", `validation: ${validation.state || "none"}`);
      state("validation-state", decisionClass(validation.forward_gate_decision || validation.state));

      bind("queue-state", `queue: ${queue.count || 0} frozen campaign${queue.count === 1 ? "" : "s"}`);
      state("queue-state", queue.count > 0 ? "warn" : "good");

      bind("leader-id", leader.id || "No declared development leader");
      bind("leader-dev-sr", fmt(leader.robust_development_sharpe));
      bind("leader-forward-sr", fmt(validation.forward_sharpe_12));
      bind("leader-forward-decision", validation.forward_gate_decision || "not observed");
      if (validation.guidance_superseded_by_newer_validation) {
        bind("leader-note", "Newer frozen validation supersedes the older development instruction. This seam is no longer active and should not be rescued by retuning the spent fold.");
      } else if (leader.id) {
        bind("leader-note", leader.note || "Development evidence only; validation status remains separate.");
      }

      if (next) {
        bind("queue-campaign", shortCampaign(next.campaign));
        bind("queue-candidates", next.candidate_count ?? "—");
        bind("queue-families", next.family_count ?? "—");
        bind("queue-measured", "not committed");
        bind("queue-note", next.classification_note || "Frozen preregistration is ahead of committed measurement evidence.");
      } else {
        bind("queue-campaign", "Queue clear");
        bind("queue-candidates", "0");
        bind("queue-families", "0");
        bind("queue-measured", "current");
        bind("queue-note", "No preregistered campaign is ahead of the committed evidence frontier.");
      }

      renderTriage(latest.family_triage || []);
      root.dataset.dashboardState = "ready";
    })
    .catch((error) => {
      root.dataset.dashboardState = "error";
      bind("latest-decision", "Generated health JSON could not be loaded; use Methodology Health / repository evidence.");
      const body = root.querySelector('[data-bind="triage-body"]');
      if (body) body.innerHTML = `<tr><td colspan="7">Dashboard data unavailable (${String(error.message || error)}).</td></tr>`;
    });
})();
