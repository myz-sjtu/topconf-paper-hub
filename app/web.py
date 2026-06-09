from fastapi.responses import HTMLResponse


def index_page() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TopConf Paper Hub</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d9dee7;
      --text: #17202f;
      --muted: #637083;
      --accent: #0f766e;
      --accent-soft: #d8f3ee;
      --network: #0f766e;
      --architecture: #a44b12;
      --ai: #3356b8;
      --shadow: 0 10px 28px rgba(31, 41, 55, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    button,
    input {
      font: inherit;
    }

    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
    }

    aside {
      background: #eef2f5;
      border-right: 1px solid var(--line);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-width: 0;
    }

    main {
      padding: 18px;
      min-width: 0;
    }

    .brand {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    h1 {
      font-size: 21px;
      line-height: 1.15;
      margin: 0;
      font-weight: 760;
    }

    h2 {
      font-size: 16px;
      margin: 0;
      font-weight: 720;
    }

    .count {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .toolbar,
    .filters {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }

    .toolbar {
      justify-content: space-between;
      margin-bottom: 14px;
    }

    .segmented {
      display: inline-grid;
      grid-auto-flow: column;
      grid-auto-columns: max-content;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--panel);
      min-height: 38px;
    }

    .segmented button {
      border: 0;
      border-right: 1px solid var(--line);
      background: transparent;
      color: var(--muted);
      padding: 8px 12px;
      cursor: pointer;
      min-width: 72px;
    }

    .segmented button:last-child { border-right: 0; }
    .segmented button.active {
      background: var(--accent-soft);
      color: #074b45;
      font-weight: 700;
    }

    .search {
      width: min(360px, 100%);
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 12px;
      background: var(--panel);
      color: var(--text);
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }

    .panel-head {
      min-height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
    }

    .domain-list,
    .conference-list,
    .paper-list {
      display: grid;
    }

    .domain-list {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }

    .domain-card {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 10px;
      cursor: pointer;
      min-width: 0;
      text-align: left;
    }

    .domain-card.active {
      border-color: var(--accent);
      box-shadow: inset 0 0 0 1px var(--accent);
    }

    .domain-name {
      display: block;
      font-weight: 750;
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .domain-total {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
    }

    .conference-list {
      gap: 8px;
      max-height: calc(100vh - 260px);
      overflow: auto;
      padding-right: 2px;
    }

    .conference-row {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 10px;
      display: grid;
      gap: 5px;
      text-align: left;
      cursor: pointer;
      min-width: 0;
    }

    .conference-row.active {
      border-color: var(--accent);
      box-shadow: inset 0 0 0 1px var(--accent);
    }

    .conf-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      min-width: 0;
    }

    .acronym {
      font-weight: 780;
      overflow-wrap: anywhere;
    }

    .full-name {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 24px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 0 9px;
      color: var(--muted);
      background: #fafbfc;
      font-size: 12px;
      white-space: nowrap;
    }

    .badge.network { color: var(--network); border-color: rgba(15, 118, 110, 0.32); }
    .badge.architecture { color: var(--architecture); border-color: rgba(164, 75, 18, 0.32); }
    .badge.ai { color: var(--ai); border-color: rgba(51, 86, 184, 0.32); }

    .paper-list {
      gap: 10px;
    }

    .paper-card {
      border-bottom: 1px solid var(--line);
      padding: 14px;
      display: grid;
      gap: 9px;
      min-width: 0;
    }

    .paper-card:last-child { border-bottom: 0; }

    .paper-title {
      color: var(--text);
      font-size: 16px;
      font-weight: 760;
      line-height: 1.3;
      text-decoration: none;
      overflow-wrap: anywhere;
    }

    .paper-title:hover { color: var(--accent); }

    .meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      color: var(--muted);
      font-size: 13px;
    }

    .authors {
      color: #3b4656;
      font-size: 13px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }

    .abstract {
      color: #465468;
      font-size: 13px;
      line-height: 1.5;
      overflow-wrap: anywhere;
      max-width: 1100px;
    }

    .abstract-label {
      display: block;
      color: #2f3b4c;
      font-size: 12px;
      font-weight: 740;
      margin-bottom: 3px;
    }

    .abstract.missing {
      color: var(--muted);
      font-style: italic;
    }

    .tags {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    .sources {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    .tag,
    .source-link {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      background: #f0f3f7;
      color: #405064;
      padding: 3px 8px;
      font-size: 12px;
    }

    .source-link {
      color: #2f5f89;
      text-decoration: none;
    }

    .source-link:hover {
      background: #e4eef8;
    }

    .empty {
      padding: 28px 16px;
      color: var(--muted);
      text-align: center;
      line-height: 1.45;
    }

    .loading {
      color: var(--muted);
      padding: 14px;
    }

    @media (max-width: 900px) {
      .shell {
        grid-template-columns: 1fr;
      }

      aside {
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }

      .conference-list {
        max-height: 360px;
      }

      .toolbar {
        align-items: stretch;
      }

      .search {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>TopConf Paper Hub</h1>
        <span class="count" id="conferenceCount">0 conferences</span>
      </div>

      <div class="domain-list" id="domainList"></div>

      <section class="panel">
        <div class="panel-head">
          <h2>Conferences</h2>
          <span class="count" id="visibleConferenceCount">0 shown</span>
        </div>
        <div class="conference-list" id="conferenceList">
          <div class="loading">Loading...</div>
        </div>
      </section>
    </aside>

    <main>
      <div class="toolbar">
        <div class="filters">
          <div class="segmented" id="yearControls"></div>
        </div>
        <input
          class="search"
          id="searchInput"
          placeholder="Search collected essays"
          aria-label="Search collected essays"
        >
      </div>

      <section class="panel">
        <div class="panel-head">
          <h2 id="paperHeading">Collected Essays</h2>
          <span class="count" id="paperCount">0 essays</span>
        </div>
        <div class="paper-list" id="paperList">
          <div class="loading">Loading...</div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      conferences: [],
      papers: [],
      domain: "all",
      conference: "all",
      year: "all",
      query: ""
    };

    const domainLabels = {
      all: "All",
      network: "Network",
      architecture: "Architecture",
      ai: "AI"
    };

    const els = {
      conferenceCount: document.getElementById("conferenceCount"),
      visibleConferenceCount: document.getElementById("visibleConferenceCount"),
      domainList: document.getElementById("domainList"),
      conferenceList: document.getElementById("conferenceList"),
      yearControls: document.getElementById("yearControls"),
      searchInput: document.getElementById("searchInput"),
      paperHeading: document.getElementById("paperHeading"),
      paperCount: document.getElementById("paperCount"),
      paperList: document.getElementById("paperList")
    };

    function domainClass(domain) {
      return ["network", "architecture", "ai"].includes(domain) ? domain : "";
    }

    function visibleConferences() {
      return state.conferences.filter((item) => state.domain === "all" || item.domain === state.domain);
    }

    function visiblePapers() {
      const query = state.query.trim().toLowerCase();
      return state.papers.filter((paper) => {
        const domainOk = state.domain === "all" || paper.domain === state.domain;
        const conferenceOk = state.conference === "all" || paper.conference === state.conference;
        const yearOk = state.year === "all" || String(paper.year) === String(state.year);
        const queryOk = !query || [
          paper.title,
          paper.abstract || "",
          paper.authors.join(" "),
          paper.conference,
          paper.domain
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);
        return domainOk && conferenceOk && yearOk && queryOk;
      });
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderDomains() {
      const counts = state.conferences.reduce((acc, item) => {
        acc[item.domain] = (acc[item.domain] || 0) + 1;
        acc.all += 1;
        return acc;
      }, { all: 0, network: 0, architecture: 0, ai: 0 });

      els.domainList.innerHTML = ["all", "network", "architecture", "ai"].map((domain) => `
        <button class="domain-card ${state.domain === domain ? "active" : ""}" data-domain="${domain}">
          <span class="domain-name">${domainLabels[domain]}</span>
          <span class="domain-total">${counts[domain] || 0}</span>
        </button>
      `).join("");

      els.domainList.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => {
          state.domain = button.dataset.domain;
          state.conference = "all";
          render();
        });
      });
    }

    function renderConferences() {
      const items = visibleConferences();
      els.conferenceCount.textContent = `${state.conferences.length} conferences`;
      els.visibleConferenceCount.textContent = `${items.length} shown`;

      if (!items.length) {
        els.conferenceList.innerHTML = `<div class="empty">No conferences.</div>`;
        return;
      }

      els.conferenceList.innerHTML = [
        `<button class="conference-row ${state.conference === "all" ? "active" : ""}" data-conf="all">
          <div class="conf-top">
            <span class="acronym">All Conferences</span>
            <span class="badge">all</span>
          </div>
        </button>`,
        ...items.map((item) => `
          <button
            class="conference-row ${state.conference === item.acronym ? "active" : ""}"
            data-conf="${item.acronym}"
          >
            <div class="conf-top">
              <span class="acronym">${item.acronym}</span>
              <span class="badge ${domainClass(item.domain)}">${domainLabels[item.domain]}</span>
            </div>
            <div class="full-name">${item.full_name}</div>
          </button>
        `)
      ].join("");

      els.conferenceList.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => {
          state.conference = button.dataset.conf;
          render();
        });
      });
    }

    function renderYears() {
      const years = Array.from(new Set(state.papers.map((paper) => paper.year))).sort((a, b) => b - a);
      const values = ["all", ...years];
      els.yearControls.innerHTML = values.map((year) => `
        <button class="${String(state.year) === String(year) ? "active" : ""}" data-year="${year}">
          ${year === "all" ? "All Years" : year}
        </button>
      `).join("");

      els.yearControls.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => {
          state.year = button.dataset.year;
          render();
        });
      });
    }

    function renderPapers() {
      const items = visiblePapers();
      const headingParts = [];
      if (state.domain !== "all") headingParts.push(domainLabels[state.domain]);
      if (state.conference !== "all") headingParts.push(state.conference);
      if (state.year !== "all") headingParts.push(state.year);
      els.paperHeading.textContent = headingParts.length ? headingParts.join(" / ") : "Collected Essays";
      els.paperCount.textContent = `${items.length} essays`;

      if (!items.length) {
        els.paperList.innerHTML = `<div class="empty">No collected essays match this view.</div>`;
        return;
      }

      els.paperList.innerHTML = items.map((paper) => {
        const url = paper.paper_url || paper.pdf_url || `/api/v1/papers/${paper.id}`;
        const tags = paper.tags.length
          ? paper.tags.map((tag) => `<span class="tag">${escapeHtml(tag.label)}</span>`).join("")
          : `<span class="tag">${escapeHtml(domainLabels[paper.domain])}</span>`;
        const authors = paper.authors.slice(0, 8).map(escapeHtml).join(", ");
        const abstract = paper.abstract ? escapeHtml(paper.abstract) : "";
        const sources = paper.source_records
          .filter((source) => source.source_url)
          .map((source) => `
            <a class="source-link" href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">
              ${escapeHtml(source.source_type)}
            </a>
          `)
          .join("");
        return `
          <article class="paper-card">
            <a class="paper-title" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">
              ${escapeHtml(paper.title)}
            </a>
            <div class="abstract ${abstract ? "" : "missing"}">
              <span class="abstract-label">Abstract</span>
              ${abstract || "No abstract collected yet."}
            </div>
            <div class="meta">
              <span class="badge ${domainClass(paper.domain)}">${domainLabels[paper.domain]}</span>
              <span>${escapeHtml(paper.conference)}</span>
              <span>${escapeHtml(paper.year)}</span>
              ${paper.doi ? `<span>DOI ${escapeHtml(paper.doi)}</span>` : ""}
            </div>
            ${authors ? `<div class="authors">${authors}${paper.authors.length > 8 ? ", ..." : ""}</div>` : ""}
            <div class="tags">${tags}</div>
            ${sources ? `<div class="sources">${sources}</div>` : ""}
          </article>
        `;
      }).join("");
    }

    function render() {
      renderDomains();
      renderConferences();
      renderYears();
      renderPapers();
    }

    async function load() {
      const [conferenceResponse, paperResponse] = await Promise.all([
        fetch("/api/v1/conferences"),
        fetch("/api/v1/papers?limit=50000")
      ]);
      state.conferences = await conferenceResponse.json();
      const paperPayload = await paperResponse.json();
      state.papers = paperPayload.items || [];
      render();
    }

    els.searchInput.addEventListener("input", (event) => {
      state.query = event.target.value;
      renderPapers();
    });

    load().catch((error) => {
      els.conferenceList.innerHTML = `<div class="empty">Could not load conferences.</div>`;
      els.paperList.innerHTML = `<div class="empty">Could not load essays.</div>`;
      console.error(error);
    });
  </script>
</body>
</html>
        """
    )
