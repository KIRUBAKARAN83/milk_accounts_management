(function () {
  "use strict";

  var DB_PREFIX = "milk-accounts-offline-";
  var DATA_URL = "/accounts/offline/data/";
  var SYNC_URL = "/accounts/offline/sync/";
  var db = null;
  var csrfToken = "";
  var syncing = false;
  var editing = null;

  function requestResult(request) {
    return new Promise(function (resolve, reject) {
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  function openDatabase(userId) {
    return new Promise(function (resolve, reject) {
      var request = indexedDB.open(DB_PREFIX + userId, 1);
      request.onupgradeneeded = function () {
        var database = request.result;
        ["customers", "entries", "payments", "queue", "meta"].forEach(function (name) {
          if (!database.objectStoreNames.contains(name)) {
            database.createObjectStore(name, { keyPath: name === "queue" ? "mutation_id" : name === "meta" ? "key" : "id" });
          }
        });
      };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  function store(name, mode) {
    return db.transaction(name, mode || "readonly").objectStore(name);
  }

  function all(name) {
    return requestResult(store(name).getAll());
  }

  async function getRecord(name, id) {
    var key = String(id).indexOf("local-") === 0 ? String(id) : Number(id);
    return requestResult(store(name).get(key));
  }

  function getMeta(key) {
    return requestResult(store("meta").get(key)).then(function (value) {
      return value ? value.value : null;
    });
  }

  function setMeta(key, value) {
    return requestResult(store("meta", "readwrite").put({ key: key, value: value }));
  }

  function putRecord(name, value) {
    return requestResult(store(name, "readwrite").put(value));
  }

  function deleteRecord(name, key) {
    return requestResult(store(name, "readwrite").delete(key));
  }

  function showNotice(message, type) {
    var notice = document.getElementById("notice");
    notice.textContent = message || "";
    notice.className = "notice" + (type ? " " + type : "");
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  function asNumber(value) {
    var parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function currency(value) {
    return "₹ " + asNumber(value).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function localDate() {
    var date = new Date();
    date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
    return date.toISOString().slice(0, 10);
  }

  function statusText() {
    var status = document.getElementById("connectionStatus");
    status.textContent = navigator.onLine ? "Online" : "Offline — changes stay on this device";
  }

  async function render() {
    if (!db) return;
    var customers = await all("customers");
    var entries = await all("entries");
    var payments = await all("payments");
    var queue = await all("queue");
    var list = document.getElementById("customerList");

    document.getElementById("customerCount").textContent = customers.length;
    document.getElementById("entryCount").textContent = entries.length;
    document.getElementById("paymentCount").textContent = payments.length;
    document.getElementById("queueCount").textContent = queue.length;
    document.getElementById("discardButton").hidden = queue.length === 0;
    document.getElementById("emptyState").hidden = customers.length > 0;

    list.innerHTML = customers.map(function (customer) {
      var customerEntries = entries.filter(function (entry) {
        return String(entry.customer_id) === String(customer.id);
      }).sort(function (a, b) { return b.date.localeCompare(a.date); });
      var customerPayments = payments.filter(function (payment) {
        return String(payment.customer_id) === String(customer.id);
      }).sort(function (a, b) { return b.paid_on.localeCompare(a.paid_on); });
      var hasRecords = customerEntries.length > 0 || customerPayments.length > 0;
      var entryRows = customerEntries.map(function (entry) {
        return '<li><span>' + escapeHtml(entry.date) + ' · ' + escapeHtml(entry.quantity_ml) +
          ' ml</span><span class="row-actions"><button class="button secondary small" data-action="edit-entry" data-id="' +
          escapeHtml(entry.id) + '">Edit</button><button class="button danger small" data-action="delete-entry" data-id="' +
          escapeHtml(entry.id) + '">Delete</button></span></li>';
      }).join("");
      var paymentRows = customerPayments.map(function (payment) {
        return '<li><span>' + escapeHtml(payment.paid_on) + ' · ' + currency(payment.amount) +
          (payment.note ? ' · ' + escapeHtml(payment.note) : '') +
          '</span><span class="row-actions"><button class="button secondary small" data-action="edit-payment" data-id="' +
          escapeHtml(payment.id) + '">Edit</button><button class="button danger small" data-action="delete-payment" data-id="' +
          escapeHtml(payment.id) + '">Delete</button></span></li>';
      }).join("");

      return '<article class="customer-card"><div class="customer-header"><div><h3>' +
        escapeHtml(customer.name || "Unnamed customer") + '</h3><div class="balance">Balance: ' +
        currency(customer.balance_amount) + ' · ' + customerEntries.length + ' milk entries · ' +
        customerPayments.length + ' payments</div></div><div class="record-actions">' +
        '<button class="button secondary" data-action="edit-customer" data-id="' + escapeHtml(customer.id) + '">Edit customer</button>' +
        '<button class="button green" data-action="add-entry" data-id="' + escapeHtml(customer.id) + '">Add milk</button>' +
        '<button class="button secondary" data-action="add-payment" data-id="' + escapeHtml(customer.id) + '">Add payment</button>' +
        '<button class="button secondary" data-action="share-bill" data-id="' + escapeHtml(customer.id) + '">Share bill PDF</button>' +
        '<button class="button danger" data-action="delete-customer" data-id="' + escapeHtml(customer.id) + '"' +
        (hasRecords ? ' disabled title="Customer with entries or payments cannot be deleted offline"' : '') + '>Delete</button>' +
        '</div></div><div class="record-grid"><section class="record-section"><h4>Milk entries</h4><ul>' +
        (entryRows || '<li class="muted">No milk entries</li>') +
        '</ul></section><section class="record-section"><h4>Payments</h4><ul>' +
        (paymentRows || '<li class="muted">No payments</li>') +
        '</ul></section></div></article>';
    }).join("");
  }

  async function acceptSnapshot(snapshot, replace) {
    var storedUser = localStorage.getItem("milkAccountsOfflineUser");
    if (storedUser && String(snapshot.user_id) !== storedUser && db) {
      var pending = await all("queue");
      if (pending.length) {
        throw new Error("Offline changes are waiting for another account. Sign in as that account to sync them before switching users.");
      }
      db.close();
      db = null;
    }

    if (!db) {
      db = await openDatabase(snapshot.user_id);
      localStorage.setItem("milkAccountsOfflineUser", String(snapshot.user_id));
    }
    csrfToken = snapshot.csrf_token || csrfToken;

    if (replace) {
      var tx = db.transaction(["customers", "entries", "payments", "meta"], "readwrite");
      ["customers", "entries", "payments"].forEach(function (name) {
        var objectStore = tx.objectStore(name);
        objectStore.clear();
        snapshot[name].forEach(function (record) { objectStore.put(record); });
      });
      var versions = { customers: {}, entries: {}, payments: {} };
      snapshot.customers.forEach(function (item) { versions.customers[String(item.id)] = item.updated_at; });
      snapshot.entries.forEach(function (item) { versions.entries[String(item.id)] = item.updated_at; });
      snapshot.payments.forEach(function (item) { versions.payments[String(item.id)] = item.updated_at; });
      tx.objectStore("meta").put({ key: "versions", value: versions });
      tx.objectStore("meta").put({ key: "pricePerLitre", value: snapshot.price_per_litre });
      await new Promise(function (resolve, reject) {
        tx.oncomplete = resolve;
        tx.onerror = function () { reject(tx.error); };
        tx.onabort = function () { reject(tx.error); };
      });
    }
    await render();
  }

  async function fetchSnapshot() {
    var response = await fetch(DATA_URL, {
      credentials: "same-origin",
      headers: { "Accept": "application/json" }
    });
    if (!response.ok || !(response.headers.get("content-type") || "").includes("application/json")) {
      throw new Error("Could not load your account data. Connect to the internet and sign in again to sync.");
    }
    return response.json();
  }

  async function initializeOnline() {
    var knownUser = localStorage.getItem("milkAccountsOfflineUser");
    if (!db && knownUser) db = await openDatabase(knownUser);
    var snapshot = await fetchSnapshot();
    var pending = db ? await all("queue") : [];
    await acceptSnapshot(snapshot, pending.length === 0);
    if (pending.length) {
      await syncQueue(snapshot);
    }
  }

  async function syncQueue(snapshot) {
    if (syncing || !navigator.onLine || !db) return;
    syncing = true;
    var button = document.getElementById("syncButton");
    button.disabled = true;
    try {
      snapshot = snapshot || await fetchSnapshot();
      await acceptSnapshot(snapshot, false);
      var queue = (await all("queue")).sort(function (a, b) {
        return a.created_at.localeCompare(b.created_at);
      });
      var idMap = (await getMeta("idMap")) || {};
      var versions = (await getMeta("versions")) || { customers: {}, entries: {}, payments: {} };

      for (var i = 0; i < queue.length; i += 1) {
        var mutation = queue[i];
        var data = Object.assign({}, mutation.data);
        ["id", "customer_id"].forEach(function (key) {
          if (data[key] != null && idMap[String(data[key])]) {
            data[key] = idMap[String(data[key])];
          }
        });

        var versionGroup = mutation.action.indexOf("customer.") === 0 ? "customers" :
          mutation.action.indexOf("entry.") === 0 ? "entries" :
          mutation.action.indexOf("payment.") === 0 ? "payments" : null;
        if (versionGroup && data.id != null &&
            (mutation.action.endsWith(".update") || mutation.action.endsWith(".delete"))) {
          data.expected_updated_at = versions[versionGroup][String(data.id)];
        }

        var response = await fetch(SYNC_URL, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
            "Accept": "application/json"
          },
          body: JSON.stringify({
            mutation_id: mutation.mutation_id,
            action: mutation.action,
            data: data
          })
        });
        var result = await response.json();
        if (!response.ok) {
          throw new Error(result.error || "A queued change could not be synchronized.");
        }

        if (result.local_id) idMap[result.local_id] = result.id;
        if (result.versions) {
          Object.keys(result.versions).forEach(function (group) {
            Object.assign(versions[group], result.versions[group]);
          });
        }
        await setMeta("idMap", idMap);
        await setMeta("versions", versions);
        await deleteRecord("queue", mutation.mutation_id);
      }

      var remaining = await all("queue");
      if (!remaining.length) {
        var latest = await fetchSnapshot();
        await acceptSnapshot(latest, true);
        showNotice("All offline changes were synchronized.", "success");
      }
    } catch (error) {
      showNotice(error.message || "Sync failed. Your queued changes remain saved on this device.", "error");
    } finally {
      syncing = false;
      button.disabled = false;
      await render();
    }
  }

  async function applyLocally(action, data) {
    var now = new Date().toISOString();
    if (action === "customer.create") {
      await putRecord("customers", { id: data.local_id, name: data.name, balance_amount: data.balance_amount, updated_at: null });
      return;
    }
    if (action === "customer.update") {
      var customer = await getRecord("customers", data.id);
      customer.name = data.name;
      customer.balance_amount = data.balance_amount;
      customer.updated_at = now;
      await putRecord("customers", customer);
      return;
    }
    if (action === "customer.delete") {
      await deleteRecord("customers", data.id);
      return;
    }
    if (action === "entry.create") {
      await putRecord("entries", {
        id: data.local_id, customer_id: data.customer_id, date: data.date,
        quantity_ml: data.quantity_ml, updated_at: null
      });
      return;
    }
    if (action === "entry.update") {
      var entry = await getRecord("entries", data.id);
      entry.customer_id = data.customer_id;
      entry.date = data.date;
      entry.quantity_ml = data.quantity_ml;
      entry.updated_at = now;
      await putRecord("entries", entry);
      return;
    }
    if (action === "entry.delete") {
      await deleteRecord("entries", data.id);
      return;
    }
    if (action === "payment.create") {
      await putRecord("payments", {
        id: data.local_id, customer_id: data.customer_id, amount: data.amount,
        paid_on: data.paid_on, note: data.note, updated_at: null
      });
      var paymentCustomer = await getRecord("customers", data.customer_id);
      paymentCustomer.balance_amount = (asNumber(paymentCustomer.balance_amount) - asNumber(data.amount)).toFixed(2);
      await putRecord("customers", paymentCustomer);
      return;
    }
    if (action === "payment.update") {
      var payment = await getRecord("payments", data.id);
      var oldAmount = asNumber(payment.amount);
      payment.amount = data.amount;
      payment.paid_on = data.paid_on;
      payment.note = data.note;
      payment.updated_at = now;
      await putRecord("payments", payment);
      var editedCustomer = await getRecord("customers", payment.customer_id);
      editedCustomer.balance_amount = (asNumber(editedCustomer.balance_amount) + oldAmount - asNumber(data.amount)).toFixed(2);
      await putRecord("customers", editedCustomer);
      return;
    }
    if (action === "payment.delete") {
      var deletedPayment = await getRecord("payments", data.id);
      var paymentOwner = await getRecord("customers", deletedPayment.customer_id);
      paymentOwner.balance_amount = (asNumber(paymentOwner.balance_amount) + asNumber(deletedPayment.amount)).toFixed(2);
      await putRecord("customers", paymentOwner);
      await deleteRecord("payments", data.id);
    }
  }

  async function enqueue(action, data) {
    if (!db) throw new Error("No saved account data is available. Connect and open the workspace first.");
    var mutation = {
      mutation_id: crypto.randomUUID(),
      action: action,
      data: data,
      created_at: new Date().toISOString()
    };
    await requestResult(store("queue", "readwrite").put(mutation));
    await applyLocally(action, data);
    await render();
    showNotice(navigator.onLine ? "Change saved on this device. Syncing…" : "Change saved on this device and queued for sync.");
    if (navigator.onLine) await syncQueue();
  }

  async function openForm(kind, record) {
    if (!db) {
      showNotice("No saved account data is available yet. Connect and open this workspace first.", "error");
      return;
    }
    editing = { kind: kind, record: record || null };
    var fields = document.getElementById("formFields");
    var title = document.getElementById("formTitle");
    var current = record || {};
    var customers = await all("customers");
    var selectedCustomer = customers.find(function (customer) {
      return String(customer.id) === String(current.customer_id);
    });
    var customerSelect = record
      ? '<div class="readonly-customer"><span class="muted">Customer</span><strong>' +
        escapeHtml(selectedCustomer ? selectedCustomer.name : "Unavailable customer") +
        '</strong><input type="hidden" name="customer_id" value="' + escapeHtml(current.customer_id) + '"></div>'
      : '<label>Customer<select name="customer_id" required>' +
        customers.map(function (customer) {
          return '<option value="' + escapeHtml(customer.id) + '"' +
            (String(customer.id) === String(current.customer_id) ? " selected" : "") + '>' +
            escapeHtml(customer.name) + '</option>';
        }).join("") + '</select></label>';

    if (kind === "customer") {
      title.textContent = record ? "Edit customer" : "Add customer";
      fields.innerHTML =
        '<label>Customer name<input name="name" maxlength="200" required value="' +
        escapeHtml(current.name || "") + '"></label>' +
        '<label>Balance amount<input name="balance_amount" type="number" step="0.01" value="' +
        escapeHtml(current.balance_amount == null ? "0" : current.balance_amount) + '" required></label>';
    } else if (kind === "entry") {
      title.textContent = record ? "Edit milk entry" : "Add milk entry";
      fields.innerHTML = customerSelect +
        '<label>Date<input name="date" type="date" required value="' + escapeHtml(current.date || localDate()) + '"></label>' +
        '<label>Quantity (ml)<input name="quantity_ml" type="number" min="0" step="1" required value="' +
        escapeHtml(current.quantity_ml == null ? "" : current.quantity_ml) + '"></label>';
    } else {
      title.textContent = record ? "Edit payment" : "Add payment";
      fields.innerHTML = customerSelect +
        '<label>Amount (₹)<input name="amount" type="number" min="0.01" step="0.01" required value="' +
        escapeHtml(current.amount == null ? "" : current.amount) + '"></label>' +
        '<label>Payment date<input name="paid_on" type="date" required value="' + escapeHtml(current.paid_on || localDate()) + '"></label>' +
        '<label>Note<input name="note" maxlength="255" value="' + escapeHtml(current.note || "") + '"></label>';
    }
    document.getElementById("formError").hidden = true;
    document.getElementById("recordDialog").showModal();
  }

  async function saveForm(event) {
    event.preventDefault();
    var form = event.currentTarget;
    var values = new FormData(form);
    var record = editing.record;
    var data;
    var action;
    if (editing.kind === "customer") {
      data = { name: String(values.get("name")).trim(), balance_amount: values.get("balance_amount") };
      action = record ? "customer.update" : "customer.create";
      if (record) data.id = record.id;
      else data.local_id = "local-" + crypto.randomUUID();
    } else if (editing.kind === "entry") {
      data = {
        customer_id: values.get("customer_id"),
        date: values.get("date"),
        quantity_ml: values.get("quantity_ml")
      };
      action = record ? "entry.update" : "entry.create";
      if (record) data.id = record.id;
      else data.local_id = "local-" + crypto.randomUUID();
    } else {
      data = {
        customer_id: values.get("customer_id"),
        amount: values.get("amount"),
        paid_on: values.get("paid_on"),
        note: values.get("note")
      };
      action = record ? "payment.update" : "payment.create";
      if (record) data.id = record.id;
      else data.local_id = "local-" + crypto.randomUUID();
      if (record) data.customer_id = record.customer_id;
      if (!record && asNumber(data.amount) <= 0) {
        showFormError("Payment amount must be greater than zero.");
        return;
      }
      if (record && asNumber(data.amount) <= 0) {
        showFormError("Payment amount must be greater than zero.");
        return;
      }
    }
    try {
      await enqueue(action, data);
      document.getElementById("recordDialog").close();
    } catch (error) {
      showFormError(error.message);
    }
  }

  function showFormError(message) {
    var error = document.getElementById("formError");
    error.textContent = message;
    error.hidden = false;
  }

  async function deleteItem(kind, id) {
    var stores = kind === "customer" ? "customers" : kind === "entry" ? "entries" : "payments";
    var record = await getRecord(stores, id);
    if (!record) return;
    if (!window.confirm("Delete this " + kind + "? This change will sync when online.")) return;
    await enqueue(kind + ".delete", { id: id });
  }

  function base64ToBytes(base64) {
    var raw = atob(base64);
    var result = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i += 1) result[i] = raw.charCodeAt(i);
    return result;
  }

  function makePdf(canvases) {
    var encoder = new TextEncoder();
    var parts = [];
    var length = 0;
    var offsets = [0];
    function append(bytes) {
      parts.push(bytes);
      length += bytes.length;
    }
    function text(value) { return encoder.encode(value); }
    append(text("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"));

    var pageCount = canvases.length;
    var objectCount = 2 + pageCount * 3;
    offsets[1] = length;
    append(text("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"));
    offsets[2] = length;
    var kids = canvases.map(function (_, index) { return (3 + index * 3) + " 0 R"; }).join(" ");
    append(text("2 0 obj\n<< /Type /Pages /Kids [" + kids + "] /Count " + pageCount + " >>\nendobj\n"));

    canvases.forEach(function (canvas, index) {
      var pageObj = 3 + index * 3;
      var contentObj = pageObj + 1;
      var imageObj = pageObj + 2;
      var imageBytes = base64ToBytes(canvas.toDataURL("image/jpeg", 0.9).split(",")[1]);
      var draw = text("q\n595 0 0 842 0 0 cm\n/Im0 Do\nQ\n");

      offsets[pageObj] = length;
      append(text(pageObj + " 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] " +
        "/Resources << /XObject << /Im0 " + imageObj + " 0 R >> >> /Contents " + contentObj + " 0 R >>\nendobj\n"));

      offsets[contentObj] = length;
      append(text(contentObj + " 0 obj\n<< /Length " + draw.length + " >>\nstream\n"));
      append(draw);
      append(text("endstream\nendobj\n"));

      offsets[imageObj] = length;
      append(text(imageObj + " 0 obj\n<< /Type /XObject /Subtype /Image /Width " + canvas.width +
        " /Height " + canvas.height + " /ColorSpace /DeviceRGB /BitsPerComponent 8 " +
        "/Filter /DCTDecode /Length " + imageBytes.length + " >>\nstream\n"));
      append(imageBytes);
      append(text("\nendstream\nendobj\n"));
    });

    var xrefOffset = length;
    var xref = "xref\n0 " + (objectCount + 1) + "\n0000000000 65535 f \n";
    for (var objectIndex = 1; objectIndex <= objectCount; objectIndex += 1) {
      xref += String(offsets[objectIndex]).padStart(10, "0") + " 00000 n \n";
    }
    append(text(xref + "trailer\n<< /Size " + (objectCount + 1) +
      " /Root 1 0 R >>\nstartxref\n" + xrefOffset + "\n%%EOF"));
    return new Blob(parts, { type: "application/pdf" });
  }

  async function offlineBill(customer) {
    var entries = (await all("entries")).filter(function (entry) {
      return String(entry.customer_id) === String(customer.id);
    }).sort(function (a, b) { return a.date.localeCompare(b.date); });
    var price = asNumber(await getMeta("pricePerLitre")) || 50;
    var canvases = [];
    var pageSize = 30;
    var pageTotal = Math.max(1, Math.ceil(entries.length / pageSize));

    for (var page = 0; page < pageTotal; page += 1) {
      var canvas = document.createElement("canvas");
      canvas.width = 1190;
      canvas.height = 1684;
      var context = canvas.getContext("2d");
      context.scale(2, 2);
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, 595, 842);
      context.fillStyle = "#1e3c72";
      context.font = "bold 22px Arial";
      context.fillText("Milk Billing Invoice", 38, 48);
      context.fillStyle = "#233044";
      context.font = "bold 15px Arial";
      context.fillText(String(customer.name || "Customer"), 38, 80);
      context.font = "12px Arial";
      context.fillText("Generated " + new Date().toLocaleDateString(), 38, 102);
      var totalMl = entries.reduce(function (sum, entry) { return sum + asNumber(entry.quantity_ml); }, 0);
      var totalAmount = totalMl / 1000 * price;
      context.fillText("Milk total: " + (totalMl / 1000).toFixed(2) + " L     Amount: INR " + totalAmount.toFixed(2), 38, 128);
      context.fillText("Previous balance: INR " + asNumber(customer.balance_amount).toFixed(2), 38, 148);
      context.font = "bold 10px Arial";
      context.fillStyle = "#1e3c72";
      context.fillText("Date", 38, 183);
      context.fillText("Quantity (ml)", 185, 183);
      context.fillText("Litres", 355, 183);
      context.fillText("Amount (INR)", 450, 183);
      context.strokeStyle = "#aab5c4";
      context.beginPath();
      context.moveTo(38, 190);
      context.lineTo(557, 190);
      context.stroke();
      context.font = "10px Arial";
      context.fillStyle = "#233044";
      var currentRows = entries.slice(page * pageSize, (page + 1) * pageSize);
      currentRows.forEach(function (entry, rowIndex) {
        var y = 211 + rowIndex * 19;
        var quantity = asNumber(entry.quantity_ml);
        context.fillText(entry.date, 38, y);
        context.fillText(String(quantity), 185, y);
        context.fillText((quantity / 1000).toFixed(3), 355, y);
        context.fillText("INR " + (quantity / 1000 * price).toFixed(2), 450, y);
      });
      context.fillStyle = "#64748b";
      context.fillText("Page " + (page + 1) + " of " + pageTotal, 500, 815);
      canvases.push(canvas);
    }
    return makePdf(canvases);
  }

  function saveFile(blob, filename) {
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 30000);
  }

  async function sendPdf(blob, filename, customerName) {
    var file = new File([blob], filename, { type: "application/pdf" });
    if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({
        title: "Milk bill - " + customerName,
        text: "Milk bill for " + customerName,
        files: [file]
      });
      return;
    }
    saveFile(blob, filename);
    var message = "Milk bill for " + customerName + " is attached.";
    window.open("https://wa.me/?text=" + encodeURIComponent(message), "_blank", "noopener");
    showNotice("The PDF was downloaded. Attach it to the WhatsApp message to send it.", "success");
  }

  async function shareBill(customerId) {
    var customer = await getRecord("customers", customerId);
    if (!customer) return;
    var idMap = (await getMeta("idMap")) || {};
    var serverId = idMap[String(customer.id)] || customer.id;
    var filename = "milk-bill-" + String(customer.name || "customer").trim().replace(/[^a-z0-9]+/gi, "-").toLowerCase() + ".pdf";
    try {
      if (navigator.onLine && Number.isInteger(Number(serverId))) {
        var response = await fetch("/accounts/customers/" + serverId + "/bill-pdf/", {
          credentials: "same-origin"
        });
        if (!response.ok || !(response.headers.get("content-type") || "").includes("application/pdf")) {
          throw new Error("Unable to download the server bill.");
        }
        await sendPdf(await response.blob(), filename, customer.name || "customer");
      } else {
        await sendPdf(await offlineBill(customer), filename, customer.name || "customer");
      }
    } catch (error) {
      if (error.name === "AbortError") return;
      showNotice(error.message || "Could not share the bill.", "error");
    }
  }

  async function clearDeviceData() {
    if (!db || !window.confirm("Clear all saved customer data and queued changes from this device? This cannot be undone.")) return;
    var name = db.name;
    db.close();
    db = null;
    await new Promise(function (resolve, reject) {
      var request = indexedDB.deleteDatabase(name);
      request.onsuccess = resolve;
      request.onerror = function () { reject(request.error); };
      request.onblocked = function () { reject(new Error("Close other app tabs before clearing saved data.")); };
    });
    localStorage.removeItem("milkAccountsOfflineUser");
    document.getElementById("customerList").innerHTML = "";
    document.getElementById("emptyState").hidden = false;
    document.getElementById("customerCount").textContent = "0";
    document.getElementById("entryCount").textContent = "0";
    document.getElementById("paymentCount").textContent = "0";
    document.getElementById("queueCount").textContent = "0";
    showNotice("Offline data was cleared from this device.", "success");
  }

  async function discardQueuedChanges() {
    if (!db || !window.confirm("Discard every unsynchronized change on this device and reload the latest server data? This cannot be undone.")) return;
    await requestResult(store("queue", "readwrite").clear());
    var snapshot = await fetchSnapshot();
    await acceptSnapshot(snapshot, true);
    showNotice("Queued changes were discarded. Latest server data was downloaded.", "success");
  }

  document.getElementById("addCustomer").addEventListener("click", function () { openForm("customer"); });
  document.getElementById("syncButton").addEventListener("click", function () { syncQueue(); });
  document.getElementById("discardButton").addEventListener("click", function () {
    discardQueuedChanges().catch(function (error) { showNotice(error.message || "Could not discard queued changes.", "error"); });
  });
  document.getElementById("clearButton").addEventListener("click", function () {
    clearDeviceData().catch(function (error) { showNotice(error.message || "Could not clear offline data.", "error"); });
  });
  document.getElementById("closeDialog").addEventListener("click", function () { document.getElementById("recordDialog").close(); });
  document.getElementById("cancelForm").addEventListener("click", function () { document.getElementById("recordDialog").close(); });
  document.getElementById("recordForm").addEventListener("submit", saveForm);

  document.getElementById("customerList").addEventListener("click", async function (event) {
    var button = event.target.closest("[data-action]");
    if (!button || button.disabled) return;
    var id = button.getAttribute("data-id");
    var action = button.getAttribute("data-action");
    try {
      if (action === "edit-customer") await openForm("customer", await getRecord("customers", id));
      else if (action === "add-entry") await openForm("entry", { customer_id: id });
      else if (action === "add-payment") await openForm("payment", { customer_id: id });
      else if (action === "edit-entry") await openForm("entry", await getRecord("entries", id));
      else if (action === "edit-payment") await openForm("payment", await getRecord("payments", id));
      else if (action === "delete-customer") await deleteItem("customer", id);
      else if (action === "delete-entry") await deleteItem("entry", id);
      else if (action === "delete-payment") await deleteItem("payment", id);
      else if (action === "share-bill") await shareBill(id);
    } catch (error) {
      showNotice(error.message || "The requested action failed.", "error");
    }
  });

  window.addEventListener("online", function () {
    statusText();
    initializeOnline().catch(function (error) {
      showNotice(error.message || "Could not reconnect to your account.", "error");
    });
  });
  window.addEventListener("offline", statusText);

  async function start() {
    statusText();
    if (navigator.onLine) {
      try {
        await initializeOnline();
        return;
      } catch (error) {
        showNotice(error.message || "Could not load account data.", "error");
      }
    }
    var userId = localStorage.getItem("milkAccountsOfflineUser");
    if (userId) {
      try {
        db = await openDatabase(userId);
        await render();
        if (!(await all("customers")).length) {
          showNotice("No saved offline data is available. Connect and open this workspace to download it.", "error");
        }
      } catch (error) {
        showNotice("Could not read the saved offline data on this device.", "error");
      }
    } else {
      showNotice("No offline data is saved yet. Connect, sign in, and open this workspace once to download it.", "error");
    }
  }

  start();
})();
