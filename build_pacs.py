import urllib2
from BeautifulSoup import BeautifulSoup as BS
import re
import yaml

PACS_REGEX = re.compile(r"[0-9]{2}\.[0-9]{2}\.[a-zA-Z\-\+][a-zA-Z\-]")
PACS_REGEX_WEAK = re.compile(r"[0-9]{2}\.([0-9]{2}\.[a-zA-Z\-\+][a-zA-Z\-])?")

def open_http(url):
    """Tries to open an http url. Raises an error if the request fails."""
    # Can form POST requests and add headers here
    req = urllib2.Request(url)
    # Make request (request, data - do not use, timeout in seconds)
    result = urllib2.urlopen(req, None, 10)
    return result

def pacs_get_level(code):
    if code[1] == '0': return 1
    if len(code) == 3: return 2
    assert len(code) == 8
    if code[6] in ('+','-'): return 3
    if code[6].isupper(): return 4
    return 5

def get_node(key):
    # The key should be the PACS code
    return nodes.setdefault(key, {'code': key, 'level': pacs_get_level(key), 'cross_references': [], 'cross_referenced': [], 'cross_parents': [], 'children': [], 'cross_children': [], 'year_s': '2010'})

try:
    f = open('pacs.yml')
except:
    nodes = {}
else:
    nodes = yaml.load(f.read())
    f.close()

urls = [("http://www.aip.org/pacs/pacs2010/individuals/pacs2010_regular_edition/reg%d0.htm" % i,'main') for i in range(0,10)]
urls = urls[0:]

for url in urls:
    res = ''.join(open_http(url[0]).readlines())
    soup = BS(res)
    rows = soup.findAll('tr')
    cur_node = None
    for r in rows:
        try:
            html_cells = r.findAll('td')
            if len(html_cells) != 2: continue
            cells = map(lambda x: str(''.join(x.findAll(text=True))), html_cells)
            if "... ... ..." in cells[0]:
                pacs_match = re.search(PACS_REGEX, cells[1]) 
                assert pacs_match
                get_node(pacs_match.group(0))['cross_parents'].append(cur_node['code'])
                cur_node['cross_children'].append(pacs_match.group(0))
                continue
            else:
                out = {}
                code = re.search(PACS_REGEX_WEAK, cells[0]).group(0)
                out = get_node(code)
                out['source'] = url[1]
                name = cells[1].rstrip()
                description = ''
                #If first italics characters is ( or [, then assume this is a comment
                try:
                    comment_candidate_split = html_cells[1].findAll('i')[-1].findAll(text = True)
                    if comment_candidate_split[0][0] in ('(','['):
                        n = len(comment_candidate_split)
                        description = str(''.join(comment_candidate_split))
                        name = str(''.join(html_cells[1].findAll(text = True)[0:-1 * n])).rstrip()
                except IndexError: pass
                assert name
                out['name'] = name
                out['description'] = description
                for x in re.findall(PACS_REGEX, cells[1]):
                    y = get_node(x)
                    y['cross_referenced'].append(code)
                    out['cross_references'].append(x)
                out['parent'] = None
                while cur_node:
                    if out['level'] > cur_node['level']:
                        assert out['level'] == cur_node['level'] + 1
                        out['parent'] = cur_node['code']
                        cur_node['children'].append(code)
                        break
                    else:
                        cur_node = nodes[cur_node['parent']]
                cur_node = out
        except:
            print "ERROR: %s" % r

f = open('pacs.yml','w')
f.write(yaml.dump(nodes))
f.close()
