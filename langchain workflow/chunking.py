from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def get_pdf_document_chunks(chunk_size=1024, chunk_overlap=50):
    loader = DirectoryLoader(path='./docs' ,glob="*.pdf", loader_cls=UnstructuredPDFLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)

    print(f"总共分割为 {len(chunks)} 个文档块")
    return chunks