document.getElementById("opts").addEventListener("click", (e) => {
  e.preventDefault();
  if (chrome.runtime?.openOptionsPage) {
    chrome.runtime.openOptionsPage();
  }
});
