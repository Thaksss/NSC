import os
import glob
import re

css_block = """
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
                display: flex !important;
                position: fixed;
                top: 0;
                right: -250px;
                width: 250px;
                height: 100vh;
                background-color: #ffffff;
                flex-direction: column !important;
                padding-top: 70px;
                padding-left: 20px;
                padding-right: 20px;
                box-shadow: -2px 0 10px rgba(0,0,0,0.1);
                transition: right 0.3s ease;
                z-index: 1500;
                align-items: flex-start !important;
                gap: 15px !important;
                overflow-y: auto;
            }
            .nav-links.active {
                right: 0;
            }
            .nav-links a {
                color: #333 !important;
                text-shadow: none !important;
                margin-left: 0 !important;
                width: 100%;
                text-align: left;
                padding: 5px 0;
            }
            .nav-links .btn-highlight,
            .nav-links .btn-logout {
                color: #ffffff !important;
                text-align: center;
                width: 100%;
                padding: 10px 15px;
                border-radius: 20px;
            }
            .nav-links form {
                margin-left: 0 !important;
                width: 100%;
            }
            .nav-links form button {
                width: 100% !important;
                margin-left: 0 !important;
                margin-top: 5px;
            }
            /* Hamburger animation */
            .hamburger.active span:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
            .hamburger.active span:nth-child(2) { opacity: 0; }
            .hamburger.active span:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }
        }
    </style>
"""

for file in glob.glob('templates/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = re.compile(r'\s*<style>\s*/\*\s*Mobile Navbar\s*\*/.*?</style>', re.DOTALL)
    
    if pattern.search(content):
        content = pattern.sub(css_block, content)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated', file)
    else:
        print('Not found in', file)
