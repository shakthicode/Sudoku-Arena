const fs = require('fs');
const path = require('path');

const rootDir = path.join(__dirname, '..');
const srcFile = path.join(rootDir, 'frontend', 'index.html');
const distDir = path.join(rootDir, 'dist');
const destFile = path.join(distDir, 'index.html');

console.log('=== Sudoku-Arena Frontend Build ===');

try {
  // Create dist directory if it doesn't exist
  if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
    console.log('📁 Created dist/ directory');
  }

  // Copy index.html to dist/index.html
  fs.copyFileSync(srcFile, destFile);
  console.log('📄 Copied index.html to dist/index.html');

  // Create Netlify _redirects file to prevent 404s on refresh for SPA routing
  const redirectsContent = '/*    /index.html   200\n';
  fs.writeFileSync(path.join(distDir, '_redirects'), redirectsContent);
  console.log('📄 Created _redirects file in dist/');

  console.log('\n✅ Build completed successfully!');
} catch (err) {
  console.error('\n❌ Build failed:', err);
  process.exit(1);
}
