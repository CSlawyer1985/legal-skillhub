import os, json
DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'checklist.json')
def load():
    if os.path.exists(DATA):
        try:
            return json.load(open(DATA, encoding='utf-8'))
        except Exception:
            pass
    return []
if __name__ == '__main__':
    items = load()
    print(u'\u3010%s\u3011' % title)
    if not items:
        print('（暂无内容，可往', DATA, '添加条目）')
    else:
        for i, it in enumerate(items, 1):
            print(' %d. %s' % (i, it))
