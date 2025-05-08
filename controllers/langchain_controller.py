import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from dotenv import load_dotenv
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()
router = APIRouter()

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=700,
    api_key=os.getenv("OPENAI_API_KEY"),
)

embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
)

@router.post("/pdf-query")
async def query_pdf_with_langchain(
    file: UploadFile = File(...),
    query: str = Form(...)
):
    try:
        # Save uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Load and split PDF
        loader = PyMuPDFLoader(tmp_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)

        # In-memory Chroma vectorstore
        vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)

        # Setup RetrievalQA
        retriever = vectorstore.as_retriever()
        qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        # Run query
        result = qa.run(query)
        return {"query": query, "response": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
