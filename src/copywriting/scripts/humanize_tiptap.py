"""Programmatic humanizer for Tiptap JSON content (LearnHouse activities).

Recursively walks Tiptap doc structure and applies humanizer rules to all
text nodes. Designed for bulk content pipelines - not for interactive editing.

Usage:
    python humanize_tiptap.py input.json output.json

Or as a library:
    from humanize_tiptap import humanize_tiptap
    with open('activity.json') as f:
        content = json.load(f)
    humanized = humanize_tiptap(content)
"""

import json, re, sys


def humanize_text(text):
    """Apply humanizer rules to a single text string."""
    if not text:
        return text
    text = text.replace('—', '. ').replace('–', ', ').replace(' -- ', '. ')
    text = re.sub(r'\\. \\.', '. ', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\\. ,', ',', text)
    text = re.sub(r', \\.', '.', text)
    ai_words = [
        (r'\badditionally\b', 'selain itu'), (r'\bcrucial\b', 'penting'),
        (r'\bdelve\b', 'masuk ke'), (r'\bfostering?\b', 'ngembangin'),
        (r'\bshowcasing\b', 'nunjukin'), (r'\bunderscore[s]?\b', 'nunjukin'),
        (r'\bvital\b', 'penting'), (r'\bpivotal\b', 'kunci'),
        (r'\blandscape\b', 'dunia'), (r'\btapestry\b', 'gabungan'),
        (r'\btestament\b', 'bukti'), (r'\bvibrant\b', 'ramai'),
        (r'\benhancing?\b', 'nigihin'), (r'\bgarner\w*\b', 'dapetin'),
        (r'\binterplay\b', 'interaksi'), (r'\bintricate\w*\b', 'kompleks'),
        (r'\bvaluable\b', 'berharga'), (r'\bcomprehensive\b', 'lengkap'),
        (r'\bremarkable\b', 'luar biasa'), (r'\bseamless\w*\b', 'mulus'),
        (r'\bleverage\w*\b', 'manfaatin'), (r'\butilize\w*\b', 'pake'),
        (r'\btransformative\b', 'ngubah'), (r'\binnovative\b', 'baru'),
        (r'\bstreamline\w*\b', 'permudah'), (r'\brobust\b', 'kuat'),
        (r'\bempower\w*\b', 'kasih kekuatan'), (r'\bsignificantly\b', 'banyak'),
        (r'\bsubsequently\b', 'setelah itu'), (r'\bencompassing\b', 'mencakup'),
        (r'\bemphasizing\b', 'tekanin'), (r'\bhighlights?(?!ed)', 'nunjukin'),
        (r'\brepresent[s]?\b', 'jadi'),
    ]
    for p, r in ai_words:
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    for o, n in [('Terdapat','Ada'),('terdapat','ada'),('Hal tersebut','itu'),
        ('Dalam rangka','buat'),('Saat ini sedang berlangsung','lagi jalan sekarang'),
        ('Melalui platform ini','di sini'),('Berdasarkan data yang kami miliki','dari data kita'),
        ('Penting untuk dicatat bahwa',''),('Penting untuk diketahui bahwa',''),
        ('In order to ','To '),('Due to the fact that ','Karena '),
        ('At this point in time','sekarang'),('It is important to note that ',''),
        ('The system has the ability to ','Baca '),('The real question is','Pertanyaannya'),
        ('at its core','pada dasarnya'),('in reality','sebenarnya'),
        ('what really matters','yang penting'),('fundamentally','pada dasarnya'),
        ("Let's dive in",''),("let's explore",''),("Let's break this down",''),
        ("Here's what you need to know",''),('without further ado',''),
        ('The future looks bright',''),('Exciting times lie ahead',''),
        ('In conclusion',''),
        # Indonesian educational content patterns (discovered Jul 2026)
        # These English jargon terms feel irrelevant in Indonesian course content
        (' Expected: ',' Hasilnya: '),('Expected output: ','Output-nya: '),
        (' Expected:\n',' Hasilnya:\n'),
        ('Use case','Contoh penerapan'),('use case','contoh'),
        ('Best practice','Tips'),('best practice','tips'),
        ('Best Practice','Tips'),('Best Practices','Tips'),
        ]:
        text = text.replace(o, n)
    # Regex patterns for "adalah" copula — replace with "itu" or restructure
    # Only match "adalah" as standalone word (not part of longer word)
    text = re.sub(r'\badalah\b', 'itu', text)
    # Normalize whitespace after replacements
    return re.sub(r'  +', ' ', text).strip()


def humanize_node(node):
    """Recursively humanize all text nodes in a Tiptap JSON structure."""
    if not node:
        return node
    node = dict(node)
    if 'content' not in node or not isinstance(node['content'], list):
        return node
    if node.get('type') in ('paragraph', 'heading', 'listItem', 'codeBlock', 'blockquote'):
        nc = []
        for c in node['content']:
            if not isinstance(c, dict):
                nc.append(c)
                continue
            c = dict(c)
            if c.get('type') == 'text' and 'text' in c:
                c['text'] = humanize_text(c['text'])
            elif 'content' in c:
                c = humanize_node(c)
            nc.append(c)
        node['content'] = nc
    else:
        node['content'] = [humanize_node(c) if isinstance(c, dict) and 'content' in c else c for c in node['content']]
    return node


def humanize_tiptap(tiptap_doc):
    """Humanize a full Tiptap document. Returns new doc dict."""
    return humanize_node(tiptap_doc)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python humanize_tiptap.py input.json output.json")
        sys.exit(1)
    with open(sys.argv[1], 'r') as f:
        doc = json.load(f)
    humanized = humanize_tiptap(doc)
    with open(sys.argv[2], 'w') as f:
        json.dump(humanized, f, ensure_ascii=False, indent=2)
    blocks = len(humanized.get('content', []))
    print(f"Humanized {blocks} blocks -> {sys.argv[2]}")
