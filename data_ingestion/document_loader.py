import os


def load_txt_documents(folder_path):
    texts = []
    if not os.path.isdir(folder_path):
        print(f"[WARN] News folder not found: {folder_path}")
        return texts
    for file in sorted(os.listdir(folder_path)):
        if file.endswith(".txt"):
            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                texts.append(content)
    return texts


def chunk_text(text, max_length=300):
    sentences = text.split(". ")
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) < max_length:
            current += sentence + ". "
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence + ". "
    if current.strip():
        chunks.append(current.strip())
    return chunks
