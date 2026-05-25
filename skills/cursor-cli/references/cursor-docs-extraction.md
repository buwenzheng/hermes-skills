# Cursor Docs Extraction Notes

## Problem

Cursor's website uses Next.js with heavy SSR. Page content is embedded as **double-escaped JSON** inside `<script>` tags, making standard HTML parsing ineffective.

## What Doesn't Work

- `grep` / text extraction on raw HTML → finds nothing useful
- Browser navigation → times out
- Standard curl + strip tags → only gets navigation/footer text
- `re.findall(r'<p>(.*?)</p>', html)` → zero matches (content not in HTML tags)

## What Works

Cursor embeds content in `self.__next_f.push([1,"..."])` script blocks. The actual prose lives in a specific byte range (~80000-95000 of the response).

```python
import subprocess, re

result = subprocess.run(['curl', '-sL', '--max-time', '20', url], capture_output=True, text=True)
html = result.stdout

# Content is double-escaped. Key fields to extract:
# 1. baseId values → section headers
base_ids = re.findall(r'baseId\\":\\"([^"\\]+)\\"', html)

# 2. code blocks → command examples
codes = re.findall(r'\\"code\\":\\"([^"\\]{10,})\\"', html)

# 3. children text → paragraph content
children = re.findall(r'\\"children\\":\\"([^"\\]{20,})\\"', html)
```

## Decoding

```python
decoded = text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
```

## Alternative: Node.js

Node handles the escaping better:

```javascript
const fs = require('fs');
const html = fs.readFileSync('/tmp/cursor.html', 'utf8');
const chunk = html.slice(80000, 95000);
const matches = chunk.match(/"baseId":"([^"\\]+)"/g) || [];
```

## Quick Fetch Script

```python
import subprocess, re, os

base_url = "https://cursor.com/docs/cli"
docs = ["overview", "installation", "using", "shell-mode", ...]

for doc in docs:
    url = f"{base_url}/{doc}"
    result = subprocess.run(['curl', '-sL', '--max-time', '20', url], capture_output=True, text=True)
    html = result.stdout
    
    blocks = []
    base_ids = re.findall(r'baseId\\":\\"([^"\\]+)\\"', html)
    for bid in base_ids:
        decoded = bid.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        blocks.append(f"## {decoded.replace('-', ' ').title()}")
    
    codes = re.findall(r'\\"code\\":\\"([^"\\]{10,})\\"', html)
    for code in codes:
        decoded = code.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        if '#' in decoded or 'curl' in decoded or 'agent' in decoded:
            blocks.append(f"```bash\n{decoded}\n```")
    
    with open(f"~/.hermes/tmp/cursor-cli-docs/{doc}.md", 'w') as f:
        f.write('\n\n'.join(blocks))
```

## Key Positions in Response

| Range | Content |
|-------|---------|
| 0-50000 | Navigation, scripts, stylesheets |
| 80000-95000 | Main prose content (titles, paragraphs, code) |
| 95000-end | Footer, related links, scripts |

## Gotcha

The Chinese version (`cursor.com/cn/docs/cli/...`) returns much less content than English (`cursor.com/docs/cli/...`). Always use English path for extraction.