import json,base64,sys,glob,os
# decode every saved Drive download into /home/claude/midia/raw/<title>
for f in glob.glob('/root/.claude/projects/-home-claude-eusoujuliano-posts/6e6f525e-bbd3-5dd6-ad69-c9a3232cd075/tool-results/mcp-Google_Drive-download_file_content-*.txt'):
    try: d=json.load(open(f))
    except Exception as e: continue
    out='/home/claude/midia/raw/'+d['title']
    if d['title']=='1.png': continue
    if not os.path.exists(out):
        open(out,'wb').write(base64.b64decode(d['content'])); print('saved',d['title'])
