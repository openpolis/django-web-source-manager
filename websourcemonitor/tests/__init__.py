# get some big strings from files, once for every tests
import websourcemonitor

with open(f'{websourcemonitor.__path__[0]}/tests/resources/source_original.html', 'r') as src_f:
    html_content = src_f.read().encode('utf-8')
with open(f'{websourcemonitor.__path__[0]}/tests/resources/source_parsed_content.txt', 'r') as src_f:
    parsed_content = src_f.read().strip()
