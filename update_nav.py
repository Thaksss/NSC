import os

target = """            {% if session.get('username') %}
                <a href="/logout\""""

replacement = """            {% if session.get('role') == 'admin' %}
                <a href="/admin/reports" class="btn-highlight" style="background-color: #f39c12; margin-right: 10px;">ระบบจัดการ (Admin)</a>
            {% endif %}
            {% if session.get('username') %}
                <a href="/logout\""""

for file in os.listdir('templates'):
    if file.endswith('.html') and file != 'admin_reports.html':
        filepath = os.path.join('templates', file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% if session.get('role') == 'admin' %}" not in content and target in content:
            new_content = content.replace(target, replacement)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file}")
