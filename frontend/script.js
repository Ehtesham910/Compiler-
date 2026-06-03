async function compileAndRun() {
  const source = document.getElementById("sourceCode").value;
  const runBtn = document.getElementById("runBtn");

  const outputBox = document.getElementById("outputBox");
  const errorBox = document.getElementById("errorBox");
  outputBox.textContent = "";
  errorBox.textContent = "";

  // Disable button and show loading
  runBtn.disabled = true;
  runBtn.textContent = "Compiling...";

  try {
    const res = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: source, run: true }),
    });
    const data = await res.json();

    if (data.ok) {
      outputBox.textContent = data.output || "";
    } else {
      errorBox.textContent = data.error || "Compilation/Execution failed";
    }
  } catch (err) {
    errorBox.textContent = "Request failed: " + err;
  } finally {
    // Re-enable button
    runBtn.disabled = false;
    runBtn.textContent = "Compile & Run";
  }
}

document.getElementById("runBtn").addEventListener("click", compileAndRun);

// Mark 1: Syntax Guide Toggle
function toggleSyntaxGuide() {
  const guide = document.getElementById("syntax-guide");
  guide.classList.toggle("hidden");
}

document.getElementById("syntax-toggle").addEventListener("click", toggleSyntaxGuide);
document.getElementById("syntax-close").addEventListener("click", toggleSyntaxGuide);

