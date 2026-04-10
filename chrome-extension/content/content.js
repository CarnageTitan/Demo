(function () {
  const ROOT_ID = "ai-selfgrade-root";
  const PANEL_ID = "ai-selfgrade-panel";

  function getDefaults() {
    const D = typeof ASG_DEFAULTS !== "undefined" ? ASG_DEFAULTS : {};
    return {
      suffixTemplate:
        D.suffixTemplate ||
        "\n\n---\n(Caliber) Ask for calibrated confidence and a short Self-assessment after your answer.",
      selfGradeTemplate:
        D.selfGradeTemplate ||
        "(Caliber) Review your previous assistant message: confidence 0–100, caveats, hallucination check.",
      mediaCheckTemplate:
        D.mediaCheckTemplate ||
        "\n\n---\n(Caliber) State whether you actually processed the user’s attachment; if not, do not describe its contents.",
    };
  }

  const HOST_HINTS = {
    "chatgpt.com": { composer: ["#prompt-textarea", "textarea[data-id]", "textarea[placeholder]"] },
    "chat.openai.com": { composer: ["#prompt-textarea", "textarea[data-id]", "textarea[placeholder]"] },
    "claude.ai": { composer: ["div[contenteditable='true'][data-testid]", "div[contenteditable='true']", "textarea"] },
    "gemini.google.com": { composer: ["rich-textarea .ql-editor", "div[contenteditable='true']", "textarea"] },
    "perplexity.ai": { composer: ["textarea[placeholder]", "textarea"] },
    "www.perplexity.ai": { composer: ["textarea[placeholder]", "textarea"] },
  };

  function getHostKey() {
    const h = location.hostname.replace(/^www\./, "");
    if (HOST_HINTS[location.hostname]) return location.hostname;
    if (HOST_HINTS[h]) return h;
    return location.hostname;
  }

  function queryVisible(selectors) {
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.offsetParent !== null) return el;
    }
    return null;
  }

  function findComposer() {
    const hints = HOST_HINTS[getHostKey()]?.composer || [];
    const fromHints = queryVisible(hints);
    if (fromHints) return fromComposerCandidate(fromHints);

    const textareas = Array.from(document.querySelectorAll("textarea:not([readonly])"));
    const visibleTa = textareas.find((t) => t.offsetParent !== null && !t.disabled);
    if (visibleTa) return { el: visibleTa, kind: "textarea" };

    const editables = Array.from(
      document.querySelectorAll("div[contenteditable='true'], [contenteditable='true']")
    );
    const ce = editables.find(
      (d) => d.offsetParent !== null && !d.closest("#" + PANEL_ID) && !d.closest("#" + ROOT_ID)
    );
    if (ce) return { el: ce, kind: "contenteditable" };

    return null;
  }

  function fromComposerCandidate(el) {
    if (el.matches("textarea")) return { el, kind: "textarea" };
    if (el.matches("[contenteditable='true']")) return { el, kind: "contenteditable" };
    const innerTa = el.querySelector("textarea:not([readonly])");
    if (innerTa) return { el: innerTa, kind: "textarea" };
    const innerCe = el.querySelector("[contenteditable='true']");
    if (innerCe) return { el: innerCe, kind: "contenteditable" };
    return { el, kind: "textarea" };
  }

  function setComposerValue(composer, text) {
    const { el, kind } = composer;
    if (kind === "textarea") {
      const start = el.selectionStart ?? el.value.length;
      const end = el.selectionEnd ?? el.value.length;
      const v = el.value;
      el.value = v.slice(0, start) + text + v.slice(end);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      try {
        el.focus();
        const pos = start + text.length;
        el.setSelectionRange(pos, pos);
      } catch (_) {}
      return;
    }
    el.focus();
    const sel = window.getSelection();
    if (sel && sel.rangeCount) {
      const range = sel.getRangeAt(0);
      range.deleteContents();
      range.insertNode(document.createTextNode(text));
      range.collapse(false);
      sel.removeAllRanges();
      sel.addRange(range);
    } else {
      el.appendChild(document.createTextNode(text));
    }
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
  }

  function textFromElement(el) {
    if (!el) return "";
    return (el.innerText || el.textContent || "").trim();
  }

  function findAssistantMessages() {
    const candidates = [];

    document.querySelectorAll('[data-message-author-role="assistant"]').forEach((node) => {
      const t = textFromElement(node);
      if (t.length > 20) candidates.push({ el: node, text: t });
    });

    document
      .querySelectorAll(
        '[data-role="assistant"], [data-testid*="assistant"], [data-testid="conversation-turn-assistant"]'
      )
      .forEach((node) => {
        const t = textFromElement(node);
        if (t.length > 20) candidates.push({ el: node, text: t });
      });

    if (candidates.length === 0) {
      document.querySelectorAll("article, [class*='message'], [class*='Message']").forEach((node) => {
        const cls = (node.className && String(node.className).toLowerCase()) || "";
        if (cls.includes("assistant") || cls.includes("model")) {
          const t = textFromElement(node);
          if (t.length > 40) candidates.push({ el: node, text: t });
        }
      });
    }

    const seen = new Set();
    const uniq = [];
    for (const c of candidates) {
      const key = c.text.slice(0, 120);
      if (seen.has(key)) continue;
      seen.add(key);
      uniq.push(c);
    }
    return uniq;
  }

  function getLastAssistantExcerpt(maxLen) {
    const msgs = findAssistantMessages();
    if (!msgs.length) return "";
    let t = msgs[msgs.length - 1].text;
    if (t.length > maxLen) t = t.slice(0, maxLen) + "\n… [truncated]";
    return t;
  }

  function loadSettings() {
    const def = getDefaults();
    return new Promise((resolve) => {
      chrome.storage.sync.get(
        {
          suffixTemplate: def.suffixTemplate,
          selfGradeTemplate: def.selfGradeTemplate,
          mediaCheckTemplate: def.mediaCheckTemplate,
        },
        (items) => {
          resolve({
            suffixTemplate: items.suffixTemplate || def.suffixTemplate,
            selfGradeTemplate: items.selfGradeTemplate || def.selfGradeTemplate,
            mediaCheckTemplate: items.mediaCheckTemplate || def.mediaCheckTemplate,
          });
        }
      );
    });
  }

  function ensureRoot() {
    if (document.getElementById(ROOT_ID)) return;
    const root = document.createElement("div");
    root.id = ROOT_ID;
    document.documentElement.appendChild(root);

    const panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.innerHTML = `
      <div class="asg-header" id="asg-drag">
        <span class="asg-title">Caliber prompts</span>
        <button type="button" class="asg-toggle" id="asg-collapse" aria-expanded="true">Hide</button>
      </div>
      <div class="asg-body">
        <p class="asg-note">Caliber only adds text to your composer—it cannot see your files. Prompts ask the chat model to state what it accessed and flag weak or invented details.</p>
        <div class="asg-actions">
          <button type="button" class="asg-btn asg-btn-primary" id="asg-insert-suffix">Caliber: epistemic + confidence block</button>
          <button type="button" class="asg-btn" id="asg-media-check">Caliber: media / file check</button>
          <button type="button" class="asg-btn" id="asg-self-grade">Caliber: reply audit</button>
        </div>
        <p class="asg-label">Last detected assistant excerpt</p>
        <pre class="asg-preview" id="asg-preview">—</pre>
        <p class="asg-status" id="asg-status"></p>
        <a class="asg-link" id="asg-options" href="#">Extension options</a>
      </div>
    `;
    root.appendChild(panel);

    const header = panel.querySelector("#asg-drag");
    const collapseBtn = panel.querySelector("#asg-collapse");
    collapseBtn.addEventListener("click", () => {
      const collapsed = panel.classList.toggle("asg-collapsed");
      collapseBtn.textContent = collapsed ? "Show" : "Hide";
      collapseBtn.setAttribute("aria-expanded", String(!collapsed));
    });

    let drag = null;
    header.addEventListener("mousedown", (e) => {
      if (e.target.closest("button")) return;
      drag = { x: e.clientX, y: e.clientY, left: panel.offsetLeft, top: panel.offsetTop };
      panel.style.left = panel.offsetLeft + "px";
      panel.style.top = panel.offsetTop + "px";
      panel.style.right = "auto";
      panel.style.bottom = "auto";
      e.preventDefault();
    });
    window.addEventListener("mousemove", (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.x;
      const dy = e.clientY - drag.y;
      panel.style.left = Math.max(8, drag.left + dx) + "px";
      panel.style.top = Math.max(8, drag.top + dy) + "px";
    });
    window.addEventListener("mouseup", () => {
      drag = null;
    });

    panel.querySelector("#asg-options").addEventListener("click", (e) => {
      e.preventDefault();
      if (chrome.runtime?.openOptionsPage) chrome.runtime.openOptionsPage();
    });

    panel.querySelector("#asg-insert-suffix").addEventListener("click", async () => {
      const status = panel.querySelector("#asg-status");
      status.textContent = "";
      status.classList.remove("asg-err");
      const { suffixTemplate } = await loadSettings();
      const composer = findComposer();
      if (!composer) {
        status.textContent = "Could not find the chat input. Click the input box and try again.";
        status.classList.add("asg-err");
        return;
      }
      setComposerValue(composer, suffixTemplate);
      status.textContent = "Appended. Send your message when ready.";
    });

    panel.querySelector("#asg-media-check").addEventListener("click", async () => {
      const status = panel.querySelector("#asg-status");
      status.textContent = "";
      status.classList.remove("asg-err");
      const { mediaCheckTemplate } = await loadSettings();
      const composer = findComposer();
      if (!composer) {
        status.textContent = "Could not find the chat input.";
        status.classList.add("asg-err");
        return;
      }
      setComposerValue(composer, mediaCheckTemplate);
      status.textContent = "Media check appended. Send as part of your next message.";
    });

    panel.querySelector("#asg-self-grade").addEventListener("click", async () => {
      const status = panel.querySelector("#asg-status");
      status.textContent = "";
      status.classList.remove("asg-err");
      const { selfGradeTemplate } = await loadSettings();
      const excerpt = getLastAssistantExcerpt(6000);
      const composer = findComposer();
      if (!composer) {
        status.textContent = "Could not find the chat input.";
        status.classList.add("asg-err");
        return;
      }
      let block = selfGradeTemplate;
      if (excerpt) {
        block = selfGradeTemplate + "\n\n---\nExcerpt of your last reply (may be truncated):\n" + excerpt;
      } else {
        block =
          selfGradeTemplate +
          "\n\n(I could not detect your last reply in the page DOM; still audit your previous message in this thread.)";
      }
      setComposerValue(composer, "\n\n" + block);
      status.textContent = "Caliber audit prompt inserted. Send it as your next message.";
    });

    function refreshPreview() {
      const ex = getLastAssistantExcerpt(800);
      const pre = panel.querySelector("#asg-preview");
      pre.textContent = ex || "— none detected; Caliber’s audit prompt still asks the model to review its prior reply.";
    }
    refreshPreview();
    const obs = new MutationObserver(() => refreshPreview());
    obs.observe(document.body, { childList: true, subtree: true, characterData: true });

    loadSettings().then(() => refreshPreview());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureRoot);
  } else {
    ensureRoot();
  }
})();
