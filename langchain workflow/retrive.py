from get_embeddings import vector_store 
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

llm = ChatTongyi(
    model="qwen3-8b",
    max_retries=3,
    streaming=True,
    api_key=None)

retriever = vector_store.as_retriever()

prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个农业领域的专家，请根据知识库提供的上下文回答用户的问题。如果信息不足，请说明你无法回答。"),
            ("human", "知识库上下文: {context}\n问题: {question}")
        ]
    )

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

query = "玉米大斑病（Exserohilum turcicum感染）权威综述"
response = rag_chain.invoke(query)

print(response)

    