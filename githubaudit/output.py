import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import logging
import re


def generate_html(metadata, data):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template/layout.html')
    output = template.render(metadata=metadata, repos=data)

    current_date = datetime.now().strftime("%Y-%m-%d")
    unix_timestamp = int(datetime.now().timestamp())
    target = metadata.get('target', 'output')
    
    # sanitize the target name for use in filename
    safe_target = re.sub(r'[^\w\-_\.]', '_', target)
    
    filename = f'{safe_target}_{current_date}_{unix_timestamp}.html'
    
    with open(filename, 'w') as f:
        f.write(output)
    logging.info(f"HTML output saved to {filename}")


def generate_json(data):
    issues_data = {}
    for repo in data:
        if repo['issues']:
            issues_data[repo['name']] = repo['issues']
    
    print(json.dumps(issues_data, indent=2))
    #print(json.dumps(data, indent=2))