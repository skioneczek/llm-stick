document.addEventListener("DOMContentLoaded", () => {
  const sourceLabel = document.getElementById("active-source");
  const audit = document.getElementById("audit-log");
  const threadsContainer = document.getElementById("threads-container");
  const threadsEmpty = document.getElementById("threads-empty");
  let activeThreadId = null;

  const log = (msg) => {
    const timestamp = new Date().toISOString();
    audit.textContent = `[${timestamp}] ${msg}\n` + audit.textContent;
  };

  function sanitizeFilename(input) {
    const base = (input || "thread").toString().trim() || "thread";
    return base
      .replace(/\s+/g, "_")
      .replace(/[^a-zA-Z0-9._-]/g, "_")
      .slice(0, 120) || "thread";
  }

  async function handleExport(threadId, fileTitle = "thread") {
    if (!threadId) return;
    const printableUrl = `/_print/${threadId}`;
    try {
      const response = await fetch(`/export/pdf/${threadId}`);
      const auditHeader = response.headers.get("X-Action-Audit");
      const contentType = (response.headers.get("Content-Type") || "").toLowerCase();
      if (response.ok && contentType.includes("application/pdf")) {
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = objectUrl;
        anchor.download = `${sanitizeFilename(fileTitle || threadId)}.pdf`;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
        log(auditHeader || `PDF exported: ${threadId}`);
        return;
      }

      let fallback = null;
      try {
        fallback = await response.json();
      } catch (_) {
        fallback = null;
      }

      if (fallback && fallback.fallback === "print-to-pdf") {
        window.open(printableUrl, "_blank", "noopener");
        log(auditHeader || `PDF export fallback → print: ${threadId}`);
      } else {
        log(`PDF export failed: Unexpected response (${response.status}).`);
      }
    } catch (err) {
      window.open(printableUrl, "_blank", "noopener");
      log(`PDF export failed: ${err.message}`);
    }
  }

  function openThread(threadId, options = {}) {
    activeThreadId = threadId || null;
    expandThread(threadId, options);
    if (threadId) {
      const element = document.getElementById(`thr-${threadId}`);
      if (element) {
        try {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (_) {
          element.scrollIntoView();
        }
      }
    }
  }

  function expandThread(threadId, options = {}) {
    const { scroll = true } = options;
    if (!threadId) return;
    const target = document.querySelector(`.thread-item[data-thread-id="${threadId}"]`);
    if (!target) return;
    const willExpand = !target.classList.contains("expanded");
    document.querySelectorAll(".thread-item.expanded").forEach((el) => {
      if (el !== target) {
        el.classList.remove("expanded");
      }
    });
    if (willExpand) {
      target.classList.add("expanded");
      activeThreadId = threadId;
      if (scroll) {
        try {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (_) {
          target.scrollIntoView();
        }
      }
    } else {
      target.classList.remove("expanded");
      activeThreadId = null;
    }
  }

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
      const data = await fetchJson("/api/sources");
      const banner = document.getElementById("sourceBanner") || sourceLabel;
      if (data && data.active_source) {
        banner.textContent = `Source: ${data.active_source}`;
        const srcField = document.getElementById("newThreadSourcePath");
        if (srcField && !srcField.value) {
          srcField.value = data.active_source;
        }
        log("Source info refreshed.");
      } else {
        banner.textContent = "No active source — use Set Source controls.";
        log("Source info missing.");
      }
    } catch (err) {
      const banner = document.getElementById("sourceBanner") || sourceLabel;
      banner.textContent = "Source lookup failed. Need CLI? Use launcher window.";
      log(`Source refresh failed: ${err.message}`);
    }
  };

  const renderThreads = (threads = []) => {
    if (!threadsContainer) return;
    threadsContainer.innerHTML = "";
    if (!threads.length) {
      threadsEmpty?.classList.remove("hidden");
      activeThreadId = null;
      return;
    }
    threadsEmpty?.classList.add("hidden");

    threads.forEach((thread) => {
      if (!thread || typeof thread !== "object") return;
      const li = document.createElement("li");
      li.className = "thread-item";
      li.dataset.threadId = thread.id;
      li.dataset.threadTitle = thread.title || "thread";
      li.id = `thr-${thread.id}`;

      const header = document.createElement("header");
      const title = document.createElement("h3");
      title.textContent = thread.title || "Untitled";
      header.appendChild(title);

      const meta = document.createElement("div");
      meta.className = "meta";
      meta.innerHTML = `
        <span>Client: ${thread.client_slug || "default"}</span>
        <span>Source: ${thread.source_slug || "n/a"}</span>
        ${thread.archived ? '<span class="badge">Archived</span>' : ""}
      `;
      header.appendChild(meta);

      const actions = document.createElement("div");
      actions.className = "actions";
      const archiveLabel = thread.archived ? "Restore this conversation" : "Archive this conversation";
      actions.innerHTML = `
        <button class="open-thread" type="button" aria-label="Open this thread" title="Expand and focus this conversation.">Open thread</button>
        <button class="archive-thread" type="button" data-archive="${thread.archived ? "false" : "true"}" aria-label="${archiveLabel}" title="${archiveLabel}">
          ${thread.archived ? "Restore" : "Archive"}
        </button>
        <button class="print-thread" type="button" data-thread-id="${thread.id}" aria-label="Print large-text view" title="Print (Large Text)">Print</button>
        <button class="export-pdf" type="button" data-thread-id="${thread.id}" aria-label="Export local PDF (fallback to Print to PDF)" title="Export PDF (local; may fall back to browser Print to PDF)">Export PDF</button>
      `;
      header.appendChild(actions);
      li.appendChild(header);

      const article = document.createElement("article");
      article.className = "messages";
      if (Array.isArray(thread.messages) && thread.messages.length) {
        const list = document.createElement("ol");
        thread.messages.forEach((msg) => {
          const item = document.createElement("li");
          const roleClass = (msg.role || "assistant").toString().toLowerCase();
          const messageClasses = ["message", roleClass];
          if (roleClass === "plan") {
            messageClasses.push("plan");
          }
          item.className = messageClasses.join(" ");
          const msgHeader = document.createElement("header");
          const role = document.createElement("span");
          role.className = "role";
          role.textContent = (msg.role || "assistant").toString().toUpperCase();
          const timeEl = document.createElement("time");
          timeEl.dateTime = msg.ts ? new Date(msg.ts * 1000).toISOString() : "";
          timeEl.textContent = msg.ts ? new Date(msg.ts * 1000).toLocaleString() : "";
          msgHeader.appendChild(role);
          msgHeader.appendChild(timeEl);
          item.appendChild(msgHeader);

          const body = document.createElement("pre");
          body.textContent = msg.text || "";
          item.appendChild(body);

          if (Array.isArray(msg.citations) && msg.citations.length) {
            const citeList = document.createElement("ul");
            citeList.className = "citations";
            msg.citations.forEach((cite) => {
              const citeItem = document.createElement("li");
              citeItem.textContent = `${cite.file || ""} — ${cite.date || ""}`;
              citeList.appendChild(citeItem);
            });
            item.appendChild(citeList);
          }

          list.appendChild(item);
        });
        article.appendChild(list);
      } else {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No messages yet.";
        article.appendChild(empty);
      }
      li.appendChild(article);

      const form = document.createElement("form");
      form.className = "message-form";
      form.innerHTML = `
        <textarea name="prompt" rows="3" placeholder="Ask a question…" aria-label="Prompt"></textarea>
        <button type="submit">Send</button>
      `;
      li.appendChild(form);

      threadsContainer.appendChild(li);
    });

    if (activeThreadId) {
      const activeEl = threadsContainer.querySelector(`.thread-item[data-thread-id="${activeThreadId}"]`);
      if (activeEl) {
        activeEl.classList.add("expanded");
      } else {
        activeThreadId = null;
      }
    }

    hydrateThreadActions();
  };

  const hydrateThreadActions = () => {
    document.querySelectorAll(".thread-item .open-thread").forEach((button) => {
      button.addEventListener("click", (event) => {
        const li = event.currentTarget.closest(".thread-item");
        if (!li) return;
        openThread(li.dataset.threadId);
      });
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
          await loadThreads();
        } catch (err) {
          log(`Archive failed: ${err.message}`);
        }
      });
    });

    document.querySelectorAll(".thread-item .print-thread").forEach((button) => {
      button.addEventListener("click", (event) => {
        const threadId = event.currentTarget.dataset.threadId;
        if (!threadId) return;
        window.open(`/_print/${threadId}`, "_blank", "noopener");
        log("Opened printable view.");
      });
    });

    document.querySelectorAll(".thread-item .message-form").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const li = form.closest(".thread-item");
        const threadId = li?.dataset.threadId;
        const textarea = form.querySelector('textarea[name="prompt"]');
        const prompt = textarea?.value.trim();
        if (!threadId) {
          log("Missing thread identifier for message submission.");
          return;
        }
        if (!prompt) {
          log("Prompt cannot be empty.");
          textarea?.focus();
          return;
        }
        try {
          await fetchJson(`/threads/${threadId}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt }),
          });
          log(`Message appended to ${threadId}`);
          form.reset();
          textarea?.focus();
          activeThreadId = threadId;
          await loadThreads();
          openThread(threadId, { scroll: false });
        } catch (err) {
          log(`Message failed: ${err.message}`);
        }
      });
    });

    document.querySelectorAll(".thread-item .export-pdf").forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.preventDefault();
        const li = event.currentTarget.closest(".thread-item");
        const threadId = li?.dataset.threadId;
        const threadTitle = li?.dataset.threadTitle || threadId;
        if (!threadId) return;
        await handleExport(threadId, threadTitle);
      });
    });
  };

  const loadThreads = async () => {
    try {
      const data = await fetchJson("/api/threads");
      renderThreads(data.threads || []);
      log("Threads loaded.");
    } catch (err) {
      log(`Thread load failed: ${err.message}`);
    }
  };

  document.getElementById("refresh-threads")?.addEventListener("click", async () => {
    await loadThreads();
  });


  document.getElementById("create-thread-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      title: form.title.value.trim(),
      client_slug: form.client_slug.value.trim() || null,
      source_slug: form.source.value.trim() || null,
    };
    try {
      const data = await fetchJson("/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      log(`Thread created: ${data.thread?.id || "?"}`);
      form.reset();
      const newThreadId = data.thread?.id;
      if (newThreadId) {
        activeThreadId = newThreadId;
      }
      await loadThreads();
      if (newThreadId) {
        openThread(newThreadId, { scroll: false });
      }
    } catch (err) {
      log(`Create thread failed: ${err.message}`);
    }
  });

  document.getElementById("search-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const q = form.q.value;
    const resultsList = document.getElementById("search-results");
    resultsList.textContent = "Searching…";
    try {
      const data = await fetchJson(`/api/search?q=${encodeURIComponent(q)}`);
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

  refreshSource();
  loadThreads();
});
