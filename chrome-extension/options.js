const D = typeof ASG_DEFAULTS !== "undefined" ? ASG_DEFAULTS : {};

const DEFAULT_SUFFIX =
  D.suffixTemplate ||
  "\n\n---\nBefore you answer: for each major factual claim, add a short tag (confidence: High | Medium | Low). After your answer, add Self-assessment with calibration and caveats.";

const DEFAULT_SELF_GRADE =
  D.selfGradeTemplate ||
  "Review your previous assistant message. Give confidence 0–100, caveats, and hallucination check. Be concise.";

const DEFAULT_MEDIA =
  D.mediaCheckTemplate ||
  "\n\n---\nState whether you actually processed the user’s attachment; if not, do not describe its contents.";

const suffixEl = document.getElementById("suffix");
const selfGradeEl = document.getElementById("selfGrade");
const mediaEl = document.getElementById("mediaCheck");
const saveBtn = document.getElementById("save");
const resetBtn = document.getElementById("reset");
const statusEl = document.getElementById("status");

const STORAGE_KEYS = {
  suffixTemplate: DEFAULT_SUFFIX,
  selfGradeTemplate: DEFAULT_SELF_GRADE,
  mediaCheckTemplate: DEFAULT_MEDIA,
};

function loadIntoForm() {
  chrome.storage.sync.get(STORAGE_KEYS, (items) => {
    suffixEl.value = items.suffixTemplate || DEFAULT_SUFFIX;
    selfGradeEl.value = items.selfGradeTemplate || DEFAULT_SELF_GRADE;
    mediaEl.value = items.mediaCheckTemplate || DEFAULT_MEDIA;
  });
}

loadIntoForm();

saveBtn.addEventListener("click", () => {
  chrome.storage.sync.set(
    {
      suffixTemplate: suffixEl.value || DEFAULT_SUFFIX,
      selfGradeTemplate: selfGradeEl.value || DEFAULT_SELF_GRADE,
      mediaCheckTemplate: mediaEl.value || DEFAULT_MEDIA,
    },
    () => {
      statusEl.textContent = "Saved.";
      statusEl.style.color = "#16a34a";
      setTimeout(() => {
        statusEl.textContent = "";
      }, 2500);
    }
  );
});

resetBtn.addEventListener("click", () => {
  suffixEl.value = DEFAULT_SUFFIX;
  selfGradeEl.value = DEFAULT_SELF_GRADE;
  mediaEl.value = DEFAULT_MEDIA;
  chrome.storage.sync.set(
    {
      suffixTemplate: DEFAULT_SUFFIX,
      selfGradeTemplate: DEFAULT_SELF_GRADE,
      mediaCheckTemplate: DEFAULT_MEDIA,
    },
    () => {
      statusEl.textContent = "Reset to defaults and saved.";
      statusEl.style.color = "#16a34a";
      setTimeout(() => {
        statusEl.textContent = "";
      }, 2500);
    }
  );
});
