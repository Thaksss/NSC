import os
import re

for file in os.listdir('templates'):
    if file.endswith('.html') and file != 'admin_reports.html':
        filepath = os.path.join('templates', file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% if session.get('role') == 'admin' %}" not in content:
            pattern = r'(\s*\{%\s*if session\.get\(\'username\'\)\s*%\}\s*<a href=\"/logout\")'
            
            replacement = '''
            {% if session.get('role') == 'admin' %}
                <a href="/admin/reports" class="btn-highlight" style="background-color: #f39c12; margin-right: 10px;">ระบบจัดการ (Admin)</a>
            {% endif %}\\1'''
            
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {file}')
