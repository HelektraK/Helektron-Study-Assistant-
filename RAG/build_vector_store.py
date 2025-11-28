import os
import json
import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --------------------------------------------
# Correct project paths
# --------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Uploaded document text is stored here by your FastAPI app
DOC_DIR = os.path.join(BASE_DIR, "..", "upload", "docs")

# Vector store output directory
VS_DIR = os.path.join(BASE_DIR, "..", "upload", "vs")

os.makedirs(VS_DIR, exist_ok=True)


# --------------------------------------------
# Load documents from upload/docs/
# --------------------------------------------
def load_documents():
    docs = []
    if not os.path.exists(DOC_DIR):
        print(f"Missing directory {DOC_DIR}. No documents found.")
        return docs

    for filename in os.listdir(DOC_DIR):
        path = os.path.join(DOC_DIR, filename)
        if not os.path.isfile(path):
            continue

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
                if text:
                    docs.append(Document(page_content=text, metadata={"source": filename}))
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    return docs


# --------------------------------------------
# Build vector store
# --------------------------------------------
def build_vector_store():
    print(f"Building vector store from {DOC_DIR}...")

    docs = load_documents()

    if not docs:
        print("No documents found in upload/docs/. Upload files in the web app first.")
        return

    print(f"Loaded {len(docs)} raw documents.")

    # -------------------------------
    # Chunk documents
    # -------------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, # ~750 tokens
        chunk_overlap=200, # contextual overlap
        length_function=len
    )

    split_docs = []
    for doc in docs:
        chunks = splitter.split_text(doc.page_content)
        for chunk in chunks:
            split_docs.append(
                Document(
                    page_content=chunk,
                    metadata=doc.metadata  # keep source info
                )
            )

    print(f"Created {len(split_docs)} total chunks.")

    # -------------------------------
    # Generate embeddings
    # -------------------------------
    embeddings = HuggingFaceEmbeddings()

    print("Generating embeddings...")
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    # -------------------------------
    # Save FAISS index + metadata
    # -------------------------------
    print("Saving FAISS index and metadata...")

    faiss.write_index(vectorstore.index, os.path.join(VS_DIR, "vs.faiss"))

    with open(os.path.join(VS_DIR, "docs.json"), "w") as f:
        json.dump([d.dict() for d in split_docs], f, indent=2)

    print("\n🎉 Vector store built successfully!")
    print(f"Saved to: {VS_DIR}")


if __name__ == "__main__":
    build_vector_store()
