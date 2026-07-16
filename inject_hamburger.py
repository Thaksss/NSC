import os
import re

css_injection = """
    <style>
        /* Mobile Navbar */
        .hamburger {
            display: none;
            flex-direction: column;
            gap: 4px;
            cursor: pointer;
            z-index: 2000;
        }
        .hamburger span {
            display: block;
            width: 25px;
            height: 3px;
            background-color: #333;
            transition: all 0.3s;
        }
        @media (max-width: 768px) {
            .hamburger {
                display: flex;
            }
            .nav-links {
                position: fixed;
                top: 0;
                right: -250px;
                width: 250px;
                height: 100vh;
                background-color: #ffffff;
                flex-direction: column;
                padding-top: 70px;
                padding-left: 20px;
                box-shadow: -2px 0 10px rgba(0,0,0,0.1);
                transition: right 0.3s ease;
                z-index: 1500;
                align-items: flex-start;
                gap: 15px;
            }
            .nav-links.active {
                right: 0;
            }
            /* Hamburger animation */
            .hamburger.active span:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
            .hamburger.active span:nth-child(2) { opacity: 0; }
            .hamburger.active span:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }
        }
    </style>
"""

js_injection = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (!document.querySelector('.hamburger')) {
                const nav = document.querySelector('.navbar');
                const navLinks = document.querySelector('.nav-links');
                if (nav && navLinks) {
                    const hamburger = document.createElement('div');
                    hamburger.className = 'hamburger';
                    hamburger.innerHTML = '<span></span><span></span><span></span>';
                    nav.insertBefore(hamburger, navLinks);
                    
                    hamburger.addEventListener('click', function() {
                        hamburger.classList.toggle('active');
                        navLinks.classList.toggle('active');
                    });
                }
            }
        });
    </script>
"""

for file in os.listdir('templates'):
    if file.endswith('.html'):
        filepath = os.path.join('templates', file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '.hamburger {' not in content:
            content = content.replace('</head>', css_injection + '\n</head>')
            
        if "hamburger.classList.toggle('active');" not in content:
            content = content.replace('</body>', js_injection + '\n</body>')
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
