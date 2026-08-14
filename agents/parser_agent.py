import fitz  # PyMuPDF
import docx
import io

def extract_text(file):

    if not file:
        return ""

    try:
        filename = file.name.lower()
        file.seek(0)

        # ================= PDF =================
        if filename.endswith(".pdf"):

            file_bytes = file.read()

            if not file_bytes:
                return ""

            doc = fitz.open(stream=file_bytes, filetype="pdf")

            text = ""
            for page in doc:
                text += page.get_text()

            return text.strip()

        # ================= DOCX =================
        elif filename.endswith(".docx"):

            document = docx.Document(io.BytesIO(file.read()))

            text = "\n".join(p.text for p in document.paragraphs)

            return text.strip()

        # ================= TXT =================
        elif filename.endswith(".txt"):

            return file.read().decode("utf-8", errors="ignore")

        return ""

    except Exception as e:
        print("EXTRACTION ERROR:", e)
        return ""