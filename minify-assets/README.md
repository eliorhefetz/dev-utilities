# minify-assets

Minify CSS and JavaScript assets using a single PowerShell script.

## Features

- Minify CSS files into `.min.css`
- Minify JavaScript files into `.min.js`
- Support running CSS only, JS only, or both
- In `all` mode, validate both CSS and JS before running
- Stop execution if required folders or source files are missing

## Expected structure

```text
project/
  css/
    style.css
  js/
    app.js
  minify-assets.ps1
  run-minify.bat
```

## Usage

Run both CSS and JS:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\minify-assets.ps1 all
```

Run CSS only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\minify-assets.ps1 css
```

Run JS only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\minify-assets.ps1 js
```

Run with a custom root path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\minify-assets.ps1 all -Root "C:\path\to\project"
```

## Batch runner

You can also run:

```bat
run-minify.bat
```

This executes the script in `all` mode from the script directory.

## Output

The script creates minified files next to the originals:

- `style.css` → `style.min.css`
- `app.js` → `app.min.js`

## Notes

- Source files ending with `.min.css` or `.min.js` are skipped
- In `all` mode, the script does not process anything unless both CSS and JS are valid and ready
- The script expects `cleancss` and `terser` to be available in your environment
