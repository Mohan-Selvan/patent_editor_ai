
// A Utility function to provide information to the user in a toast format.
export function showToast(message: string, type: "success" | "error" | "info" = "info") {
  // Create container if it doesn't exist
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "fixed bottom-4 right-4 flex flex-col gap-2 z-50";
    document.body.appendChild(container);
  }

  // Create toast element
  const toast = document.createElement("div");
  toast.className = `px-4 py-2 rounded shadow-lg text-white text-sm opacity-0 translate-y-2 transition-all duration-300
    bg-gray-800 border-l-4
    ${type === "success" ? "border-green-500" : type === "error" ? "border-red-500" : "border-blue-500"}`;
  toast.innerText = message;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.remove("opacity-0", "translate-y-2");
    toast.classList.add("opacity-100", "translate-y-0");
  });

  // Auto-remove after 3s
  setTimeout(() => {
    toast.classList.remove("opacity-100", "translate-y-0");
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}