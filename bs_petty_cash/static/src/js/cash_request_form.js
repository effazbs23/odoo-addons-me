function initCashRequestForm() {
    if (!document.getElementById("cash_request_form")) return;

    // ── Vessel / Company AJAX ────────────────────────────────────────────────
    var companySelect = document.querySelector('select[name="company_id"]');
    var vesselSelect = document.querySelector('select[name="vessel_id"]');

    function updateVessels(companyId) {
        if (!vesselSelect) return;
        if (!companyId) {
            vesselSelect.innerHTML = '<option value="">Select Cost Center</option>';
            return;
        }
        fetch("/get_vessels_by_company", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {company_id: companyId},
            }),
        })
            .then(function (r) {
                return r.json();
            })
            .then(function (data) {
                if (!data.result) return;
                var prev = vesselSelect.value;
                vesselSelect.innerHTML = '<option value="">Select Cost Center</option>';
                data.result.vessels.forEach(function (v) {
                    vesselSelect.add(new Option(v.name, v.id));
                });
                if (
                    prev &&
                    data.result.vessels.some(function (v) {
                        return v.id == prev;
                    })
                ) {
                    vesselSelect.value = prev;
                }
            })
            .catch(function (e) {
                console.error("Error fetching vessels:", e);
            });
    }

    var debounceTimer;
    function debounce(fn, delay) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fn, delay || 300);
    }

    if (companySelect) {
        if (companySelect.value) updateVessels(companySelect.value);
        companySelect.addEventListener("change", function () {
            debounce(function () {
                updateVessels(companySelect.value);
            });
        });
    }

    // ── Currency symbol ──────────────────────────────────────────────────────
    var currencySelect = document.getElementById("currency_select");
    var currencySymbol = document.getElementById("currency_symbol");

    function updateCurrencySymbol() {
        if (!currencySelect || !currencySymbol) return;
        var opt = currencySelect.options[currencySelect.selectedIndex];
        currencySymbol.textContent = opt ? opt.getAttribute("data-symbol") || "" : "";
    }

    if (currencySelect) {
        updateCurrencySymbol();
        currencySelect.addEventListener("change", updateCurrencySymbol);
    }

    // ── Purpose lines ────────────────────────────────────────────────────────
    var tbody = document.getElementById("purpose_lines_body");
    var addLineBtn = document.getElementById("add_line_btn");
    var totalSpan = document.getElementById("lines_total");

    if (!tbody || !addLineBtn || !totalSpan) {
        console.warn("Cash request form elements not found");
        return;
    }

    function recalcTotal() {
        var total = 0;
        tbody.querySelectorAll(".line-amount").forEach(function (inp) {
            var v = parseFloat(inp.value);
            if (!isNaN(v)) total += v;
        });
        totalSpan.textContent = total.toFixed(2);
    }

    function updateRemoveButtons() {
        var rows = tbody.querySelectorAll(".purpose-line-row");
        rows.forEach(function (row) {
            var btn = row.querySelector(".remove-line-btn");
            if (btn) btn.disabled = rows.length === 1;
        });
    }

    function wireRow(row) {
        var amountInput = row.querySelector(".line-amount");
        var removeBtn = row.querySelector(".remove-line-btn");
        if (amountInput) amountInput.addEventListener("input", recalcTotal);
        if (removeBtn) {
            removeBtn.addEventListener("click", function () {
                row.remove();
                recalcTotal();
                updateRemoveButtons();
            });
        }
    }

    function addLine() {
        var row = document.createElement("tr");
        row.className = "purpose-line-row";
        row.innerHTML =
            '<td><input type="text" class="form-control form-control-sm line-purpose"' +
            ' name="line_purpose[]" required placeholder="Purpose description"/></td>' +
            '<td><input type="number" class="form-control form-control-sm line-amount text-end"' +
            ' name="line_amount[]" step="1" min="1" required placeholder="0.00"/></td>' +
            '<td><input type="file" class="form-control form-control-sm line-attachment"' +
            ' name="line_attachment[]"' +
            ' accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip"/></td>' +
            '<td class="text-center"><button type="button" class="btn btn-danger btn-sm remove-line-btn" title="Remove">' +
            '<i class="fa fa-trash"></i></button></td>';
        tbody.appendChild(row);
        wireRow(row);
        updateRemoveButtons();
        row.querySelector(".line-purpose").focus();
    }

    // Wire existing first row
    tbody.querySelectorAll(".purpose-line-row").forEach(wireRow);

    addLineBtn.addEventListener("click", addLine);

    updateRemoveButtons();
    recalcTotal();
}

// Run immediately if DOM is ready, otherwise wait for it
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCashRequestForm);
} else {
    initCashRequestForm();
}
