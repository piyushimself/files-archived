# Document & Creative Library

This repository contains original PDF/DOCX resources, existing HTML projects, and an automated HTML reading-edition pipeline.

## PDF and DOCX reading editions

The repository includes an automated workflow that converts every root-level PDF and DOCX into a responsive, searchable HTML reading page.

- **Generated library:** [Open the HTML reading archive](html/index.html)
- **Original documents:** remain unchanged in the repository root.
- **Conversion script:** [tools/convert_documents.py](tools/convert_documents.py)
- **Automation:** [Convert PDF and DOCX documents to HTML](.github/workflows/convert-documents.yml)

The workflow runs when PDF/DOCX files or the conversion script change, and can also be started manually from the GitHub Actions tab. It uses text extraction first and OCR as a fallback for image-only PDFs. Always compare extracted text with the original, especially for scanned pages, complex tables, columns, and unusual layouts.

## Existing HTML projects

The other standalone HTML projects remain in the repository root.
