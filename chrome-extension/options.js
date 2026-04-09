const DEFAULT_SUFFIX =
  "\n\n---\nBefore you answer: for each major factual claim, add a short tag in parentheses: (confidence: High | Medium | Low). After your answer, add a section titled \"Self-assessment\" with: (1) an overall confidence score from 0–100 for how well-supported your answer is, (2) up to three specific caveats or unknowns, and (3) anything a user should verify independently.";

const suffixEl = document.getElementById("suffix");
const saveBtn = document.getElementById("save");
const statusEl = document.getElementById("status");

chrome.storage.sync.get({ suffixTemplate: DEFAULT_SUFFIX }, (items) => {
  suffixEl.value = items.suffixTemplate || DEFAULT_SUFFIX;
});

saveBtn.addEventListener("click", () => {
  const v = suffixEl.value || DEFAULT_SUFFIX;
  chrome.storage.sync.set({ suffixTemplate: v }, () => {
    statusEl.textContent = "Saved.";
    setTimeout(() => {
      statusEl.textContent = "";
    }, 2000);
  });
});
