// NativeFrames UI helpers.
// Streamlit reruns the Python script for most interactions, so this JS
// intentionally stays small and handles only presentation enhancements.

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("img").forEach((img) => {
    if ((img.alt || "").toLowerCase().includes("nativeframes")) {
      img.loading = "eager";
    }
  });
});
