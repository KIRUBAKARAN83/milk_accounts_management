(function () {
  "use strict";

  function downloadPdf(file) {
    var url = URL.createObjectURL(file);
    var link = document.createElement("a");
    link.href = url;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 30000);
  }

  async function shareBill(button) {
    var message = button.getAttribute("data-message") || "Milk bill";
    var filename = button.getAttribute("data-filename") || "milk-bill.pdf";
    var response = await fetch(button.getAttribute("data-url"), {
      credentials: "same-origin"
    });
    if (!response.ok || !(response.headers.get("content-type") || "").includes("application/pdf")) {
      throw new Error("The bill PDF could not be generated.");
    }

    var file = new File([await response.blob()], filename, { type: "application/pdf" });
    if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ title: message, text: message, files: [file] });
      return;
    }

    downloadPdf(file);
    window.open("https://wa.me/?text=" + encodeURIComponent(message), "_blank", "noopener");
    window.alert("The bill PDF was downloaded. Attach it to the WhatsApp message to send it.");
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-bill-share]");
    if (!button) return;
    button.disabled = true;
    shareBill(button).catch(function (error) {
      if (error.name !== "AbortError") {
        window.alert(error.message || "Could not share the bill.");
      }
    }).finally(function () {
      button.disabled = false;
    });
  });
})();
