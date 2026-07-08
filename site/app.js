async function loadSummary() {
  const res = await fetch("./data/demo-summary.json");
  if (!res.ok) throw new Error("Failed to load demo summary");
  return res.json();
}

function renderSummary(data) {
  const overall = document.getElementById("overall-verdict");
  overall.textContent = data.overall_verdict;
  overall.className = `verdict ${data.overall_verdict}`;

  document.getElementById("run-meta").textContent =
    `Run ${data.run_id} · scenario ${data.scenario_id} · seed ${data.seed}`;

  const visitsEl = document.getElementById("visits");
  visitsEl.innerHTML = "";
  for (const visit of data.visit_results) {
    const card = document.createElement("article");
    card.className = "visit-card";
    const findings = visit.findings
      .map((f) => `<li><strong>${f.rule_id}</strong> — ${f.message}</li>`)
      .join("");
    card.innerHTML = `
      <div class="visit-head">
        <span class="visit-id">${visit.visit_id}</span>
        <span class="badge ${visit.verdict}">${visit.verdict}</span>
      </div>
      <p class="meta">${visit.visit_date} · ${visit.station_state} · ${visit.port} · ${visit.vehicle}</p>
      ${findings ? `<ul class="findings">${findings}</ul>` : ""}
    `;
    visitsEl.appendChild(card);
  }

  const assumptionsEl = document.getElementById("assumptions");
  assumptionsEl.innerHTML = data.assumptions.map((a) => `<li>${a}</li>`).join("");
}

document.getElementById("run-demo").addEventListener("click", async () => {
  const btn = document.getElementById("run-demo");
  btn.disabled = true;
  btn.textContent = "Loading receipt…";
  try {
    renderSummary(await loadSummary());
    btn.textContent = "Demo loaded";
  } catch (err) {
    btn.textContent = "Load failed";
    console.error(err);
  }
});

loadSummary()
  .then(renderSummary)
  .catch((err) => console.error("Initial load failed", err));
