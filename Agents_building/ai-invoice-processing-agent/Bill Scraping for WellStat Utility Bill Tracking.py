import os, sys, base64, json, csv, re, time, traceback
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: pip install google-generativeai")
    sys.exit(1)


# CONFIGURATION

GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
MODEL_NAME      = "gemini-3.1-flash-lite-preview"
PDF_MIME_TYPE   = "application/pdf"
OUTPUT_CSV      = "wellstat_output.csv"
RETRY_ATTEMPTS  = 3
RETRY_DELAY_SEC = 5


CSV_COLUMNS = [
    "account_number",
    "bill_id",
    "start_date",
    "end_date",
    "total_demand",
    "total_consumption",
    "total_consumption_on_peak",
    "total_consumption_int_peak",
    "total_consumption_off_peak",
    "total_supply",
    "total_cost",
    "total_on_peak_cost",
    "total_off_peak_cost",
    "outstanding_balance",
    "new_charges",
    "total_bill_amount",
    "meter_read_type",
    "supplier",
    "submeter_number",
    "submeter_consumption",
    "submeter_demand",
    "confidence_score",
]


EXTRACTION_PROMPT = """
You are an expert utility bill data extraction engine for WellStat.
Return ONLY a JSON array — no markdown, no explanation.

A single PDF may contain MULTIPLE utility types (electric, water, gas,
wastewater, stormwater). Extract one JSON object per utility.

Each object must have EXACTLY these keys:

{
  "utility_type"               : "electric"|"water"|"gas"|"wastewater"|"stormwater",
  "account_number"             : "STRING — always quoted, e.g. '5504 0891 875'",
  "bill_id"                    : "STRING — quoted invoice/statement/bill number, or null",
  "start_date"                 : "YYYY-MM-DD or null",
  "end_date"                   : "YYYY-MM-DD or null",
  "total_demand"               : number|null,
  "total_consumption"          : number|null,
  "total_consumption_on_peak"  : number|null,
  "total_consumption_int_peak" : number|null,
  "total_consumption_off_peak" : number|null,
  "total_supply"               : number|null,
  "total_cost"                 : number|null,
  "total_on_peak_cost"         : number|null,
  "total_off_peak_cost"        : number|null,
  "outstanding_balance"        : number|null,
  "new_charges"                : number|null,
  "total_bill_amount"          : number|null,
  "meter_read_type"            : "Actual"|"Estimated"|null,
  "supplier"                   : "string",
  "submeter_number"            : "string|null",
  "submeter_consumption"       : "string|null",
  "submeter_demand"            : "string|null"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT RULES — read every rule carefully
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GENERAL
1. Always return a JSON array [ {...} ] even for one utility.
2. null (not 0, not "") for any field not present on the bill.
3. Dates → YYYY-MM-DD. If not found, null.
4. Numbers → plain float/int (no $, no commas, no units).
5. Do NOT guess or invent values.

BILLING PERIOD — shared across all utilities on one PDF
6. All utility rows from the same PDF share the same billing period.
   If a stormwater or wastewater section has no own dates, copy the
   start_date and end_date from the electric or water section.

BILL ID — must be a JSON string
7. bill_id MUST be a quoted string, never a bare integer.
   Correct:  "bill_id": "210005780064"
   WRONG:    "bill_id": 210005780064
   Look for: "Invoice Number", "Invoice ID", "Invoice #",
             "Statement Number", "Bill Number", "Reference Number".
   Return null ONLY if none of these labels exist anywhere on the bill.

OUTSTANDING BALANCE — CRITICAL
8. outstanding_balance = the ORIGINAL prior-period balance BEFORE
   any payments are applied.
   Labels: "Previous Balance", "Previous Amount Due", "Prior Balance",
   "Balance Forward", "Past Due Amount", "Amount from Previous Bill".

   PAYMENT LOGIC — follow this exactly:
   a) Find the "Previous Balance" (or equivalent) amount — call it P.
   b) Find "Payments Received" (or equivalent) — call it R.
   c) If R >= P  →  outstanding_balance = 0.0   (balance was fully paid)
   d) If R < P   →  outstanding_balance = P - R  (partial payment)
   e) If P = 0   →  outstanding_balance = 0.0

   EXAMPLES:
   • Previous Balance $29,743.81 / Payment $29,743.81 → 0.0  (fully paid)
   • Previous Balance $15,672.71 / Payment $0.00      → 15672.71 (unpaid)
   • Previous Amount Due $6,289.61 / Payment $6,289.61→ 0.0  (fully paid)
   NEVER return the gross prior balance when it was fully paid.

DEMAND (electric)
9. total_demand = the ON-PEAK billed demand in kW (the billing demand,
   not the off-peak or maximum 12-month demand).
   If the bill shows "Total On Peak kW billed" use that value.
   Do NOT use off-peak kW or the rolling 12-month maximum demand.

CONSUMPTION TIERS (electric)
10. total_consumption    → grand total kWh. Use "Total for Billing"
    column when available; do NOT use raw meter-read column if different.
11. total_consumption_on_peak  → kWh labeled "On-Peak", "Peak", "HLH".
12. total_consumption_int_peak → kWh labeled "Int-Peak", "Intermediate",
    "Intermediate Peak", "Shoulder", "LLH-Int". null if not present.
13. total_consumption_off_peak → kWh labeled "Off-Peak", "Off Peak", "LLH".
14. Water/gas: native unit (gallons, CF, CCF) in total_consumption;
    set on_peak / int_peak / off_peak to null.

COSTS — PER-UTILITY ISOLATION (CRITICAL — most common extraction error)
15. total_cost = the service charge for THIS utility row ONLY.
    You MUST read the individual utility section on the bill and sum only
    the line items that belong to it. NEVER copy the combined bill total.

    For ELECTRIC:
      total_cost = the total electric delivery charge for this billing period
      (sum all delivery/distribution line items; EXCLUDE supply if billed
      separately by a third-party supplier).
      Labels to sum: "Distribution Services", "Customer Charge",
      "Demand Charge", "Energy Charge", "ECA", "Capacity Charge",
      "Taxes", "Franchise Fee", "Environmental Surcharge", etc.
      The section will end with a subtotal labeled "Total Electric Delivery
      Charges", "Total:", or similar — use that subtotal directly.

    For WATER: total_cost = water section subtotal only.
      Labels: "Water Charges", "Service Charge", "Commodity Charge",
      "Water Non-Residential Service Charge", section "Total:".

    For WASTEWATER: total_cost = wastewater section subtotal only.
      Labels: "Sewer Charges", "Wastewater Non-Residential Service Charge",
      section "Total:".

    For STORMWATER: total_cost = stormwater fee only.
      Labels: "Stormwater Fee", "Stormwater Charges".

    For GAS: total_cost = gas section subtotal only.

    EXAMPLE (multi-utility bill with Electric $12,152.38, Water $251.31,
    Wastewater $129.76, Stormwater $217.80):
      Electric row  → total_cost = 12152.38
      Water row     → total_cost = 251.31
      Wastewater row→ total_cost = 129.76
      Stormwater row→ total_cost = 217.80
    WRONG: copying $12,533.45 (combined current charges) into every row.

    FLAT-RATE ELECTRIC BILLS (no separate delivery/supply split):
    If the electric bill does NOT break out delivery vs. supply separately
    (i.e., one utility covers both), set total_cost = the grand total
    electric charge for the period (e.g., "Total Current Charges" on a
    TEP or similar single-supplier bill).

16. new_charges = current-period charges for THIS utility row ONLY.
    Apply the same per-utility isolation as rule 15.

    DECISION TREE — follow in order:
    a) If the utility's own section has a labeled "Current Charges" or
       "Current Service Charges" subtotal, use that value.
    b) If no such per-utility label exists in the section, set
       new_charges = total_cost for that same row (the section subtotal
       you already found under rule 15).
    c) NEVER use the bill-summary "Current Charges" or "Current Service
       Charges" line that covers ALL utilities combined.

    WHY THIS MATTERS — some bills (e.g. WSSC) show only one combined
    "Current Charges" in the summary header. Each utility section only
    prints its own "Total:" subtotal. In that case use the "Total:" as
    both total_cost AND new_charges. Do NOT pull the combined summary
    figure into individual utility rows.

    EXAMPLE (multi-utility bill):
      Electric section Total: $12,152.38
        → total_cost = 12152.38  AND  new_charges = 12152.38
      Water section Total: $251.31
        → total_cost = 251.31    AND  new_charges = 251.31
      Wastewater section Total: $129.76
        → total_cost = 129.76   AND  new_charges = 129.76
      Stormwater section Total: $217.80
        → total_cost = 217.80   AND  new_charges = 217.80
    WRONG: putting the combined summary total into any individual row.

17. total_bill_amount = the grand total the customer owes now
    (the final "Total Due" / "Amount Due" / "New Account Balance").
    This IS the whole-bill total and IS shared across all rows from
    the same PDF. This is the only field that is shared across utility rows.

ON-PEAK / OFF-PEAK COSTS (electric) — CRITICAL, do not skip
18. total_on_peak_cost = the dollar charge for on-peak energy consumption.
    Look for line items labeled:
      "On-Peak Energy", "ECA On-Peak", "Peak Energy Charge",
      "HLH Energy", "On-Peak kWh charge".
    Sum all such line items if more than one appears.
    Set null ONLY if the bill has NO on-peak energy cost line item at all
    (e.g., flat-rate bills with a single energy charge and no TOU split).

    EXAMPLES:
    • CSU bill: "ECA On-Peak: 18,828 kWh x $0.0464 = $873.62"
      → total_on_peak_cost = 873.62
    • Pepco bill: "On-Peak Energy: 35,912 kWh x $0.027785 = $997.81"
      → total_on_peak_cost = 997.81
    • TEP bill: single "Winter - kWh" charge with no TOU split
      → total_on_peak_cost = null

19. total_off_peak_cost = the dollar charge for off-peak energy consumption.
    Look for line items labeled:
      "Off-Peak Energy", "ECA Off-Peak", "Off-Peak kWh charge",
      "LLH Energy", "Off Peak Energy Charge".
    Sum all such line items if more than one appears.
    Set null ONLY if the bill has NO off-peak energy cost line item at all.

    EXAMPLES:
    • CSU bill: "ECA Off-Peak: 94,440 kWh x $0.0232 = $2,191.01"
      → total_off_peak_cost = 2191.01
    • Pepco bill: "Off-Peak Energy: 55,486 kWh x $0.027785 = $1,541.68"
      → total_off_peak_cost = 1541.68
    • TEP bill: single energy charge with no TOU split
      → total_off_peak_cost = null

METER READ TYPE — infer when not labelled
20. Set "Actual" if explicit meter readings (numbers) are listed,
    even if the bill does not print the word "Actual" or "Act.".
    Set "Estimated" only if the bill prints "Est." or "Estimated".
    null only if no meter reading data at all.

SUPPLIER
21. If both a commodity supplier AND a delivery utility appear,
    format as: "SupplierName | DeliveryUtilityName"
    Example: "ENGIE Resources | Pepco"
    Single company → just that name.

SUBMETERS — suppress zero-consumption meters
22. Populate submeter_* only when the bill explicitly lists submeters.
    If multiple submeters are listed, comma-separate.
    EXCLUDE any submeter whose consumption is 0 (inactive meter).
    Example: meter P shows 0 gallons, meter S shows 237,000 gallons
    → only include meter S.

Respond ONLY with the JSON array. No markdown fences.
"""

# KEY MAP — normalise any suffixed Gemini keys

_KEY_MAP = {
    "total_demand_kw":                "total_demand",
    "total_consumption_kwh":          "total_consumption",
    "total_consumption_on_peak_kwh":  "total_consumption_on_peak",
    "total_consumption_int_peak_kwh": "total_consumption_int_peak",
    "total_consumption_off_peak_kwh": "total_consumption_off_peak",
    "total_supply_kwh":               "total_supply",
    "total_cost_usd":                 "total_cost",
    "total_on_peak_cost_usd":         "total_on_peak_cost",
    "total_off_peak_cost_usd":        "total_off_peak_cost",
    "outstanding_balance_usd":        "outstanding_balance",
    "new_charges_usd":                "new_charges",
    "total_bill_amount_usd":          "total_bill_amount",
}


# READING PDF

def step1_read_pdf(pdf_path: str) -> bytes:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    size_kb = path.stat().st_size / 1024
    print(f"    [STEP 1] READ     → {path.name}  ({size_kb:.1f} KB)")
    return path.read_bytes()


# ENCODING THE PDF INTO BASE64

def step2_encode_base64(pdf_bytes: bytes) -> str:
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    print(f"    [STEP 2] ENCODE   → {len(b64):,} chars")
    return b64


def step3_call_gemini(b64: str, model) -> str:
    print(f"    [STEP 3] SEND     → Gemini ({MODEL_NAME})")
    parts = [{"inline_data": {"mime_type": PDF_MIME_TYPE, "data": b64}},
             EXTRACTION_PROMPT]
    last_err = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = model.generate_content(parts)
            text = resp.text.strip()
            print(f"    [STEP 3] RECEIVE  → {len(text):,} chars  (attempt {attempt})")
            return text
        except Exception as exc:
            last_err = exc
            print(f"    [STEP 3] ERROR attempt {attempt}: {exc}")
            if attempt < RETRY_ATTEMPTS:
                print(f"    [STEP 3] Retry in {RETRY_DELAY_SEC}s …")
                time.sleep(RETRY_DELAY_SEC)
    raise RuntimeError(f"Gemini failed after {RETRY_ATTEMPTS} attempts: {last_err}")


def _force_str(v):
    """Force a value to string if it is not None/null."""
    if v is None: return None
    s = str(v).strip()
    return None if s.lower() == "null" else s

def step4_parse_json(raw: str, pdf_name: str) -> list[dict]:
    
    cleaned = re.sub(r"^```[a-zA-Z]*[\s]*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"[\s]*```\s*$", "", cleaned).strip()

    if not cleaned:
        print("    [STEP 4] PARSE    → empty response from Gemini")
        return []

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        print(f"    [STEP 4] PARSE    → JSON ERROR: {exc}")
        print(f"    [STEP 4] Raw (first 500): {cleaned[:500]}")
        return []

    if isinstance(parsed, dict):
        parsed = [parsed]

    normalised = []
    for rec in parsed:
        norm: dict = {}
        for k, v in rec.items():
            norm[_KEY_MAP.get(k, k)] = v

        # bill_id and account_number to string
        for fld in ("bill_id", "account_number"):
            norm[fld] = _force_str(norm.get(fld))

        normalised.append(norm)

    _fill_missing_dates(normalised)

    print(f"    [STEP 4] PARSE    → {len(normalised)} record(s)")
    for r in normalised:
        print(f"             {r.get('utility_type','?')}  "
              f"acct={r.get('account_number','?')}  "
              f"bill_id={r.get('bill_id','?')}  "
              f"dates={r.get('start_date','?')}→{r.get('end_date','?')}")
    return normalised


def _fill_missing_dates(records: list[dict]):
    """If any record is missing start/end dates, copy from a sibling that has them."""
    sd = next((r["start_date"] for r in records if r.get("start_date")), None)
    ed = next((r["end_date"]   for r in records if r.get("end_date")),   None)
    for r in records:
        if not r.get("start_date") and sd:
            r["start_date"] = sd
        if not r.get("end_date") and ed:
            r["end_date"] = ed

# CONFIDENCE SCORING

_ALWAYS_REQUIRED = [
    "account_number", "bill_id", "start_date", "end_date",
    "total_bill_amount", "outstanding_balance",
    "new_charges", "total_cost", "meter_read_type", "supplier",
]
_ELEC_REQUIRED = ["total_demand", "total_consumption"]
_ELEC_OPTIONAL = [
    "total_consumption_on_peak", "total_consumption_int_peak",
    "total_consumption_off_peak", "total_on_peak_cost", "total_off_peak_cost",
]
_WATER_GAS_REQUIRED = ["total_consumption"]


def _is_null(v) -> bool:
    return v is None or str(v).strip().lower() in ("", "null", "none")

def _is_zero(v) -> bool:
    try:    return float(v) == 0.0
    except: return False


def step5_confidence(record: dict) -> tuple[float, str]:
    """
    Deductions:
      −10  missing always-required field (with utility-aware exemptions)
      − 8  missing utility-required field
      − 5  missing int-peak tier when on+off both present (TOU electric only)
      − 3  suspicious zero in total_cost or total_bill_amount
      − 2  missing optional TOU field (TOU electric only — skipped for flat-rate)
      − 5  dates missing or invalid

    Exemptions applied without penalty:
      • stormwater: bill_id and meter_read_type are legitimately absent
        (acreage-based fee; no invoice number, no meter)
      • flat-rate electric (no TOU tiers): optional TOU consumption/cost
        fields and the int-peak tier check are skipped — null is correct
    """
    score, notes = 100.0, []
    u = (record.get("utility_type") or "").lower()

    _stormwater_exempt = {"bill_id", "meter_read_type"}

    for f in _ALWAYS_REQUIRED:
        if u == "stormwater" and f in _stormwater_exempt:
            notes.append(f"exempt:{f}")
            continue
        v = record.get(f)
        if _is_null(v):
            score -= 10; notes.append(f"missing:{f}")
        elif _is_zero(v) and f in ("total_cost", "total_bill_amount"):
            score -= 3;  notes.append(f"zero:{f}")

    if u == "electric":
        for f in _ELEC_REQUIRED:
            v = record.get(f)
            if _is_null(v):
                score -= 8; notes.append(f"missing:{f}")
            elif _is_zero(v):
                score -= 3; notes.append(f"zero:{f}")

        is_tou = not _is_null(record.get("total_consumption_on_peak"))

        if is_tou:
            has_off = not _is_null(record.get("total_consumption_off_peak"))
            has_int = not _is_null(record.get("total_consumption_int_peak"))
            if has_off and not has_int:
                score -= 5; notes.append("missing_int_peak_tier")
            for f in _ELEC_OPTIONAL:
                if _is_null(record.get(f)):
                    score -= 2; notes.append(f"absent:{f}")
        else:
            notes.append("flat_rate:tou_fields_not_applicable")

    elif u in ("water", "wastewater", "gas"):
        for f in _WATER_GAS_REQUIRED:
            if _is_null(record.get(f)):
                score -= 8; notes.append(f"missing:{f}")

    # Date sanity with None guard
    sd_str = record.get("start_date") or ""
    ed_str = record.get("end_date")   or ""
    if not sd_str or not ed_str:
        score -= 5; notes.append("missing_date")
    else:
        try:
            sd = datetime.strptime(sd_str, "%Y-%m-%d")
            ed = datetime.strptime(ed_str, "%Y-%m-%d")
            if ed <= sd:
                score -= 5; notes.append("end_not_after_start")
        except ValueError:
            score -= 5; notes.append("bad_date_format")

    score    = round(max(0.0, min(100.0, score)), 1)
    note_str = "; ".join(notes) if notes else "OK"
    print(f"    [STEP 5] SCORE    → {score}/100  ({note_str})")
    return score, note_str

# BUILDING CSV ROW

def step6_build_row(record: dict) -> dict:
    score, _ = step5_confidence(record)
    row = {col: None for col in CSV_COLUMNS}
    row["confidence_score"] = score
    for k, v in record.items():
        if k in row:
            row[k] = v
    return row


def process_pdf(pdf_path: str, model) -> list[dict]:
    name = Path(pdf_path).name
    print(f"\n{'═'*66}")
    print(f"  PDF: {name}")
    print(f"{'═'*66}")
    try:
        pdf_bytes = step1_read_pdf(pdf_path)
        b64       = step2_encode_base64(pdf_bytes)
        raw       = step3_call_gemini(b64, model)
        records   = step4_parse_json(raw, name)
        rows      = [step6_build_row(r) for r in records]
        print(f"\n   {len(rows)} row(s) from {name}")
        return rows
    except Exception as exc:
        print(f"\n   FAILED {name}: {exc}")
        traceback.print_exc()
        return []


def _write_csv(rows: list[dict], output_csv: str, write_header: bool):
    path = Path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerows(rows)
        f.flush(); os.fsync(f.fileno())
    print(f"    [STEP 6] WRITE    → {len(rows)} row(s) → {output_csv}")


def run(pdf_paths: list[str], output_csv: str = OUTPUT_CSV):
    if GEMINI_API_KEY in ("", "YOUR_API_KEY_HERE"):
        print("ERROR: Set GEMINI_API_KEY env var."); sys.exit(1)

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME,
                                  generation_config={"temperature": 0})

    out = Path(output_csv)
    if out.exists():
        out.unlink()
        print(f"  Cleared previous: {output_csv}")

    all_rows, first = [], True
    for p in pdf_paths:
        rows = process_pdf(p, model)
        if not rows:
            print(f"  No rows from {Path(p).name}"); continue
        _write_csv(rows, output_csv, write_header=first)
        first = False
        all_rows.extend(rows)

    print(f"\n{'─'*66}")
    if all_rows:
        print(f"   {len(all_rows)} total row(s) → {output_csv}")
    else:
        print("  ⚠️  No rows extracted. Check [STEP 4] logs.")
    print(f"{'─'*66}\n")
    return all_rows


# ENTRY POINT

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdfs = sys.argv[1:]
    else:
        d = Path("./bills")
        d.mkdir(exist_ok=True)
        pdfs = sorted(str(p) for p in d.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs in {d.resolve()}")
            print("Usage: python exp2_fixed.py file1.pdf file2.pdf ...")
            sys.exit(1)

    print(f"\nWellStat Bill Scraper v6")
    print(f"PDFs to process: {len(pdfs)}")
    for p in pdfs: print(f"  • {p}")
    run(pdfs, OUTPUT_CSV)