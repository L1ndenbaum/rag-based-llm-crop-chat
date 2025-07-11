from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
from chunking import get_pdf_document_chunks
from pymilvus import connections
import sys

try:
    connections.connect(host="localhost")
    print("Milvus connected")
except Exception as error:
    print(error)
    sys.exit(-1)

chunks = get_pdf_document_chunks()
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Milvus.from_documents(
    documents=chunks,
    embedding=embedding,
    connection_args={
        "host": "localhost",
        "port": 19530
    },
    collection_name="crop_docs"
)
