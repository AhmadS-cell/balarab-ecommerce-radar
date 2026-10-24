from pathlib import Path
import re,json
root=Path(__file__).parent
for f in (root/'docs').rglob('*.html'):
 text=f.read_text(encoding='utf-8')
 assert re.search(r'<meta\s+name=[\"\x27]robots[\"\x27]\s+content=[\"\x27][^\"\x27]*noindex',text,re.I),f
 assert not re.search(r'__[A-Z_]+__',text),f
page=(root/'docs/index.html').read_text(encoding='utf-8')
rows=json.loads(re.search(r'const REELS = (\[.*?\]);\n',page,re.S).group(1))
assert len(rows)==len({x['id'] for x in rows})
assert len(re.findall('class="recommended-card"',page))>=5
print('PASS: all HTML has noindex; library IDs and five recommendations checked.')
