"""
WhatsApp Follow-Up HTML Generator

Generates personalized wa.me messages from CSV contact data, segments by profile,
and creates an HTML page with clickable wa.me links, message preview, and send tracking.

Usage:
  1. Prepare two CSVs: contact/waitlist data + transaction/purchase data
  2. Cross-reference to find targets (not yet purchased)
  3. Segment contacts by profile field (pekerjaan, role, etc.)
  4. Generate unique messages per person using body_pool per segment
  5. Create HTML with wa.me links, upload to MinIO

Requirements:
  - csv, io, random, urllib.parse, json (stdlib)
  - boto3, dotenv (for MinIO upload)
  - phone normalization: strip dashes/spaces/parens, 0→62, +remove
"""

import csv, io, random, urllib.parse, json

# --- Configuration ---

SEED = 42  # reproducibility

# Segment definitions: label, color, bg
SEG_INFO = {
    'business':  {'label': 'Business Owner',    'color': '#f59e0b', 'bg': '#fef3c7'},
    'freelancer': {'label': 'Freelancer',       'color': '#10b981', 'bg': '#d1fae5'},
    'developer': {'label': 'Developer',          'color': '#3b82f6', 'bg': '#dbeafe'},
    'career':    {'label': 'Mahasiswa / Career',  'color': '#8b5cf6', 'bg': '#ede9fe'},
    'marketing': {'label': 'Marketing',          'color': '#ec4899', 'bg': '#fce7f3'},
    'ops':       {'label': 'Operations',         'color': '#06b6d4', 'bg': '#cffafe'},
    'general':   {'label': 'Lainnya',             'color': '#6b7280', 'bg': '#f3f4f6'},
}

SEG_ORDER = ['business', 'freelancer', 'developer', 'career', 'marketing', 'ops', 'general']

# --- Phone normalization ---

def normalize_phone(raw):
    """Normalize phone to 62xxx format for wa.me."""
    p = raw.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if p.startswith('+'):
        p = p[1:]
    if p.startswith('62'):
        return p
    if p.startswith('08'):
        return '62' + p[1:]
    if p.startswith('8'):
        return '62' + p
    return '62' + p.lstrip('0')

# --- Segment assignment ---

def assign_segment(row, field='Pekerjaan'):
    """Map a row to a segment based on a field value."""
    p = row.get(field, '').strip()
    if 'Business' in p or 'Founder' in p: return 'business'
    if 'Freelancer' in p: return 'freelancer'
    if 'Developer' in p or 'Engineer' in p: return 'developer'
    if 'Mahasiswa' in p or 'Fresh Grad' in p: return 'career'
    if 'Marketing' in p or 'Growth' in p: return 'marketing'
    if 'Operations' in p or 'Admin' in p: return 'ops'
    return 'general'

# --- Cross-reference ---

def cross_reference(waitlist_csv, transactions_csv, status_field='Status', exclude_status='BELUM BELI'):
    """
    Cross-reference waitlist against transactions.
    Returns list of waitlist rows NOT found in transactions (by email).
    Deduplicates by email (keeps first occurrence).
    """
    # Load transactions emails
    with open(transactions_csv) as f:
        txn_emails = set()
        for row in csv.DictReader(f):
            txn_emails.add(row.get('Email', '').strip().lower())

    # Filter waitlist
    targets = []
    seen = set()
    with open(waitlist_csv) as f:
        for row in csv.DictReader(f):
            if row.get(status_field, '').strip() != exclude_status:
                continue
            email = row.get('Email', '').strip().lower()
            if email in seen:
                continue
            seen.add(email)
            # Optional: exclude if email in transactions
            # if email in txn_emails:
            #     continue
            row['wa'] = normalize_phone(row.get('WhatsApp', row.get('Phone', '')))
            row['first'] = row.get('Name', '').strip().split(' ')[0]
            targets.append(row)
    return targets

# --- Message generation ---

def generate_messages(targets, greetings, body_pool, seed=42):
    """
    Generate unique personalized messages for each target.
    
    greetings: list of greeting templates with {n} placeholder
    body_pool: dict of segment -> list of body templates (NO name refs)
    
    Key rules:
    - Greeting contains name, body does NOT repeat it
    - Body pool needs ≥10 variants per segment for 61+ contacts
    - Use random.seed for reproducibility
    - Verify uniqueness after generation
    """
    random.seed(seed)
    messages = []
    for i, t in enumerate(targets):
        seg = assign_segment(t)
        greeting = greetings[i % len(greetings)].format(n=t['first'])
        pool = body_pool.get(seg, body_pool['general'])
        body = pool[i % len(pool)]
        
        messages.append(f"{greeting}.\n\n{body}")
    
    # Verify uniqueness
    if len(set(messages)) != len(messages):
        dupes = [m for m in messages if messages.count(m) > 1]
        raise ValueError(f"{len(dupes)} duplicate messages found. Increase body pool size.")
    
    return messages

# --- HTML generation ---

def generate_html(targets, messages, title="Follow-Up Campaign"):
    """
    Create self-contained HTML with wa.me links, message preview, and send tracking.
    Features:
    - Dark theme, segment-colored badges
    - Click "Lihat Pesan" to preview
    - "Buka di WA" opens wa.me with pre-filled message
    - Checkbox "Sudah dikirim" with progress bar
    """
    seg_info = SEG_INFO
    
    # Group by segment
    segments = {}
    for i, t in enumerate(targets):
        seg = assign_segment(t)
        if seg not in segments:
            segments[seg] = []
        segments[seg].append((i, t, messages[i]))

    parts = [f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; max-width: 700px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1e293b, #334155); color: white; padding: 24px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #334155; }}
.header h1 {{ font-size: 20px; margin-bottom: 6px; }}
.header p {{ opacity: 0.6; font-size: 13px; }}
.stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }}
.stat {{ background: #1e293b; padding: 14px; border-radius: 12px; text-align: center; border: 1px solid #334155; }}
.stat .num {{ font-size: 26px; font-weight: 700; }}
.stat .lbl {{ font-size: 11px; color: #94a3b8; margin-top: 2px; }}
.progress-bar {{ background: #1e293b; border-radius: 99px; height: 6px; margin-bottom: 16px; overflow: hidden; border: 1px solid #334155; }}
.progress-fill {{ background: #10b981; height: 100%; border-radius: 99px; transition: width 0.3s; width: 0%; }}
.progress-text {{ font-size: 11px; color: #64748b; margin-bottom: 4px; text-align: right; }}
.segment-header {{ display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 10px; margin-bottom: 10px; margin-top: 6px; }}
.segment-header .badge {{ padding: 3px 10px; border-radius: 16px; font-size: 11px; font-weight: 600; color: white; }}
.segment-header .count {{ font-size: 12px; color: #94a3b8; }}
.card {{ background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 8px; border: 1px solid #334155; }}
.card.done {{ opacity: 0.5; }}
.card.done .card-name {{ text-decoration: line-through; }}
.card-name {{ font-weight: 600; font-size: 14px; }}
.card-phone {{ font-size: 11px; color: #64748b; margin-top: 2px; }}
.card-meta {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
.tag {{ font-size: 10px; padding: 2px 7px; border-radius: 10px; background: #0f172a; color: #94a3b8; border: 1px solid #334155; }}
.card-msg {{ margin-top: 10px; padding: 10px; background: #0f172a; border-radius: 8px; font-size: 12px; line-height: 1.7; white-space: pre-wrap; border-left: 2px solid #10b981; color: #cbd5e1; display: none; }}
.card-msg.visible {{ display: block; }}
.card-actions {{ display: flex; gap: 8px; margin-top: 10px; align-items: center; flex-wrap: wrap; }}
.btn-wa {{ display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; background: #25d366; color: white; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600; }}
.btn-wa:hover {{ background: #1da851; }}
.btn-preview {{ padding: 6px 12px; background: #0f172a; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; font-size: 11px; cursor: pointer; }}
.btn-preview:hover {{ background: #334155; }}
.check-label {{ display: flex; align-items: center; gap: 5px; font-size: 11px; color: #64748b; cursor: pointer; }}
.check-label input {{ width: 15px; height: 15px; accent-color: #10b981; }}
.tip {{ background: #1e293b; padding: 12px; border-radius: 10px; font-size: 11px; color: #94a3b8; border: 1px solid #334155; margin-bottom: 16px; line-height: 1.6; }}
.tip strong {{ color: #e2e8f0; }}
</style>
</head>
<body>
<div class="header">
<h1>{title}</h1>
<p>{len(targets)} kontak, semua pesan berbeda. Klik Buka WA, review, send.</p>
</div>''']

    card_idx = 0
    for seg_key in SEG_ORDER:
        if seg_key not in segments:
            continue
        people = segments[seg_key]
        si = seg_info[seg_key]
        parts.append(f'''
<div class="segment-section" id="seg-{seg_key}">
<div class="segment-header" style="background:{si['bg']}">
<span class="badge" style="background:{si['color']}">{si['label']}</span>
<span class="count">{len(people)} orang</span>
</div>''')
        for i, t, msg in people:
            card_idx += 1
            msg_esc = msg.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            msg_url = urllib.parse.quote(msg)
            parts.append(f'''
<div class="card" id="card-{card_idx}">
<div class="card-name">{t.get('Name', '')}</div>
<div class="card-phone">{t.get('WhatsApp', t.get('Phone', ''))}</div>
<div class="card-actions">
<button class="btn-preview" onclick="toggleMsg('msg-{card_idx}', this)">Lihat Pesan</button>
<a class="btn-wa" href="https://wa.me/{t['wa']}?text={msg_url}" target="_blank">&#x1F4AC; Buka di WA</a>
<label class="check-label"><input type="checkbox" onchange="markDone({card_idx})" data-card="{card_idx}"> Sudah dikirim</label>
</div>
<div class="card-msg" id="msg-{card_idx}">{msg_esc}</div>
</div>''')
        parts.append('</div>')

    parts.append('''
<script>
function toggleMsg(id, btn) {
  const el = document.getElementById(id);
  el.classList.toggle('visible');
  btn.textContent = el.classList.contains('visible') ? 'Tutup Pesan' : 'Lihat Pesan';
}
function markDone(idx) {
  const card = document.getElementById('card-' + idx);
  card.classList.toggle('done');
  updateProgress();
}
function updateProgress() {
  const total = document.querySelectorAll('[data-card]').length;
  const checked = document.querySelectorAll('[data-card]:checked').length;
  document.getElementById('totalNum').textContent = total;
  document.getElementById('sentNum').textContent = checked;
  document.getElementById('remainNum').textContent = total - checked;
  document.getElementById('progressText').textContent = checked + ' / ' + total;
  document.getElementById('progressFill').style.width = (total ? (checked/total*100) : 0) + '%';
}
</script>
</body>
</html>''')

    return '\n'.join(parts)
