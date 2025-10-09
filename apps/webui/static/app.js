document.addEventListener("DOMContentLoaded", () => {
  const sourceLabel = document.getElementById("active-source");
  const audit = document.getElementById("audit-log");

  const log = (msg) => {
    const timestamp = new Date().toISOString();
    audit.textContent = `[${timestamp}] ${msg}\n` + audit.textContent;
  };

  const fetchJson = async (url, options = {}) => {
    const resp = await fetch(url, options);
    let payload = null;
    try {
      payload = await resp.json();
    } catch (err) {
      log(`Non-JSON response from ${url}`);
    }
    if (!resp.ok) {
      const error = payload && payload.error ? payload.error : resp.statusText;
      throw new Error(error || "Request failed");
    }
    return payload;
  };

  const refreshSource = async () => {
    try {
      const data = await fetchJson("/sources");
      sourceLabel.textContent = `Source: ${data.source} (slug ${data.slug})`;
      log("Source info refreshed.");
    } catch (err) {
      sourceLabel.textContent = "Source lookup failed.";
      log(`Source refresh failed: ${err.message}`);
    }
  };

  document.getElementById("refresh-threads")?.addEventListener("click", () => {
    window.location.reload();
  });

  document.getElementById("create-thread-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      title: form.title.value,
      client_slug: form.client_slug.value,
      source: form.source.value,
    };
    try {
      const data = await fetchJson("/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      log(`Thread created: ${data.thread?.id || "?"}`);
      window.location.reload();
    } catch (err) {
      log(`Create thread failed: ${err.message}`);
    }
  });

  document.querySelectorAll(".thread-item .archive-thread").forEach((button) => {
    button.addEventListener("click", async (event) => {
      const li = event.currentTarget.closest(".thread-item");
      const threadId = li?.dataset.threadId;
      const archive = event.currentTarget.dataset.archive === "true";
      if (!threadId) return;
      try {
        await fetchJson(`/threads/${threadId}/archive`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ archive }),
        });
        log(`${archive ? "Archived" : "Restored"} thread ${threadId}`);
        window.location.reload();
      } catch (err) {
        log(`Archive failed: ${err.message}`);
      }
    });
  });

  document.querySelectorAll(".thread-item .message-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const li = form.closest(".thread-item");
      const threadId = li?.dataset.threadId;
      const prompt = form.prompt.value.trim();
      if (!threadId || !prompt) return;
      try {
        await fetchJson(`/threads/${threadId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt }),
        });
        log(`Message appended to ${threadId}`);
        window.location.reload();
      } catch (err) {
        log(`Message failed: ${err.message}`);
      }
    });
  });

  document.getElementById("search-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const q = form.q.value;
    const resultsList = document.getElementById("search-results");
    resultsList.textContent = "Searching…";
    try {
      const data = await fetchJson(`/search?q=${encodeURIComponent(q)}`);
      resultsList.textContent = "";
      if (!data.matches || !data.matches.length) {
        resultsList.textContent = "No matches.";
        return;
      }
      data.matches.forEach((match) => {
        const li = document.createElement("li");
        li.textContent = `${match.title || match.id} — ${match.snippet || ""}`;
        resultsList.appendChild(li);
      });
      log(`Search returned ${data.matches.length} matches.`);
    } catch (err) {
      resultsList.textContent = "Search failed.";
      log(`Search failed: ${err.message}`);
    }
  });

  document.getElementById("set-source-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      path: form.path.value,
      force: form.force.checked,
    };
    try {
      const data = await fetchJson("/set-source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      log(`Set source: ${data.status}`);
      await refreshSource();
    } catch (err) {
      log(`Set source failed: ${err.message}`);
    }
  });

  document.getElementById("ingest-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      path: form.path.value,
      client_slug: form.client_slug.value,
      dest: form.dest.value,
    };
    try {
      const data = await fetchJson("/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      log(`Ingest queued: ${data.job_id || "n/a"}`);
      window.location.reload();
    } catch (err) {
      log(`Ingest failed: ${err.message}`);
    }
  });

  document.getElementById("hotswap-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = { client_slug: form.client_slug.value };
    try {
      await fetchJson("/hotswap", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      log("Hotswap completed.");
      await refreshSource();
      window.location.reload();
    } catch (err) {
      log(`Hotswap failed: ${err.message}`);
    }
  });

  document.getElementById("preset-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = { preset: form.preset.value };
    try {
      const data = await fetchJson("/preset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      log(data.message || "Preset applied.");
    } catch (err) {
      log(`Preset failed: ${err.message}`);
    }
  });

  document.querySelectorAll(".load-thread").forEach((button) => {
    button.addEventListener("click", (event) => {
      const li = event.currentTarget.closest(".thread-item");
      if (li) {
        li.classList.toggle("expanded");
      }
    });
  });

  refreshSource();
});
