# Filetype Validator — simple and straightforward

Tool to check if files in a folder have the **correct extension** according to their **actual content** (magic numbers).  
Optionally, it can **automatically rename** them to the correct extension and generate a **CSV report**.

---

## Quick usage

1. **Set parameters (optional)**  
   In the `params.json` file (same directory as `main.py`), define:
   ```json
   {
     "input": "path/to/folder",
     "report": "report.csv",
     "rename": false     
   }
   ```
   - `input` → path to the folder or file to validate  
   - `rename` → `true` to automatically rename, `false` to only generate the report  
   - `report` → name/path of the output CSV file

2. **Run**  
   - Simply open `main.py` in VS Code and click **Run** — it will use `params.json` by default.  
   - Or run from the terminal:
     ```bash
     python main.py --input /path/to/folder --report output.csv
     ```
     With automatic renaming:
     ```bash
     python main.py --input /path/to/folder --report output.csv --rename
     ```

---

## What the CSV report contains
Columns:
```
path, size_bytes, current_ext, detected_ext, detected_mime, confidence, is_match, action, new_path, error, reason
```
- `is_match` → `true` if the current extension matches the detected type  
- `action` → `rename`, `none` or `error`  
- `new_path` → final path if renamed  
- `error` → details in case of failure

---

## Detected formats (MVP)
- **Images:** jpg/jpeg, png, gif, tiff, webp  
- **Documents/Archives:** pdf, zip, docx/xlsx/pptx, odt/ods/odp, epub, 7z, rar, gz, bz2, xz  
- **Media:** mp3, mp4, wav, avi  
- **Text (heuristic):** html, json, txt  
- **Fallback:** bin (unknown)

---

## Key points
- Works **locally** — nothing is sent to the internet.  
- **Safe by default**: only renames when `--rename` or `"rename": true` in JSON is set.  
- Renaming is safe: avoids overwriting existing files (`_1`, `_2`, etc.).

---

## License
MIT
