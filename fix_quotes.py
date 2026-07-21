import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the syntax error: '...status = 'pending'...' -> "...status = 'pending'..."
content = content.replace("conn.execute('SELECT * FROM pollution_reports WHERE status = 'approved'').fetchall()", 
                          "conn.execute(\"SELECT * FROM pollution_reports WHERE status = 'approved'\").fetchall()")

content = content.replace("conn.execute('SELECT * FROM cleared_reports WHERE status = 'pending'').fetchall()",
                          "conn.execute(\"SELECT * FROM cleared_reports WHERE status = 'pending'\").fetchall()")

content = content.replace("conn.execute('SELECT * FROM pollution_reports WHERE status = 'pending'').fetchall()",
                          "conn.execute(\"SELECT * FROM pollution_reports WHERE status = 'pending'\").fetchall()")

content = content.replace("WHERE c.status = 'pending'", "WHERE c.status = ''pending''") # Wait, this is inside ''' ''', so 'pending' is fine.
content = content.replace("WHERE c.status = ''pending''", "WHERE c.status = 'pending'")

content = content.replace("conn.execute('SELECT * FROM pollution_reports WHERE status = 'pending' ORDER BY created_at DESC').fetchall()",
                          "conn.execute(\"SELECT * FROM pollution_reports WHERE status = 'pending' ORDER BY created_at DESC\").fetchall()")

content = content.replace("conn.execute('SELECT * FROM cleared_reports WHERE status = 'pending' ORDER BY created_at DESC').fetchall()",
                          "conn.execute(\"SELECT * FROM cleared_reports WHERE status = 'pending' ORDER BY created_at DESC\").fetchall()")

content = content.replace("conn.execute('UPDATE pollution_reports SET status = 'approved' WHERE id = ?', (report_id,))",
                          "conn.execute(\"UPDATE pollution_reports SET status = 'approved' WHERE id = ?\", (report_id,))")

content = content.replace("conn.execute('UPDATE pollution_reports SET status = 'rejected' WHERE id = ?', (report_id,))",
                          "conn.execute(\"UPDATE pollution_reports SET status = 'rejected' WHERE id = ?\", (report_id,))")

content = content.replace("conn.execute('UPDATE cleared_reports SET status = 'approved' WHERE id = ?', (clear_id,))",
                          "conn.execute(\"UPDATE cleared_reports SET status = 'approved' WHERE id = ?\", (clear_id,))")

content = content.replace("conn.execute('UPDATE pollution_reports SET status = 'cleared' WHERE id = ?', (clear_report['report_id'],))",
                          "conn.execute(\"UPDATE pollution_reports SET status = 'cleared' WHERE id = ?\", (clear_report['report_id'],))")

content = content.replace("conn.execute('UPDATE cleared_reports SET status = 'rejected' WHERE id = ?', (clear_id,))",
                          "conn.execute(\"UPDATE cleared_reports SET status = 'rejected' WHERE id = ?\", (clear_id,))")


with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
