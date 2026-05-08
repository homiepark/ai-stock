// Inline boot script to apply the user's saved theme before paint.
// Avoids the dark-light flash on first load.

export function ThemeBoot() {
  const code = `
    try {
      const saved = localStorage.getItem('theme');
      const root = document.documentElement;
      if (saved === 'light') { root.classList.remove('dark'); root.classList.add('light'); }
      else { root.classList.add('dark'); root.classList.remove('light'); }
    } catch (e) {}
  `;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
