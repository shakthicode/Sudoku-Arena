import os
import shutil

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_file = os.path.join(root_dir, 'frontend', 'index.html')
dist_dir = os.path.join(root_dir, 'dist')
dest_file = os.path.join(dist_dir, 'index.html')

print('=== Sudoko-Arena Frontend Build (Python) ===')

try:
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir, exist_ok=True)
        print('[OK] Created dist/ directory')
    shutil.copy2(src_file, dest_file)
    print('[OK] Copied index.html to dist/index.html')
    
    redirects_file = os.path.join(dist_dir, '_redirects')
    with open(redirects_file, 'w', encoding='utf-8') as f:
        f.write('/*    /index.html   200\n')
    print('[OK] Created _redirects file in dist/')
    print('\nBuild completed successfully!')
except Exception as e:
    print(f'\nBuild failed: {e}')
    exit(1)
