

# class RagBasedChatLLM:
#     def __init__(self, llm, vector_store) -> None:
#         self.llm = llm
#         self.qa_chain = PebbloRetrievalQA.from_chain_type(
#                             llm=llm,
#                             retriever=vector_store.as_retriever(),
#                             return_source_documents=True,
#                             app_name="MyAPP",
#                             owner="Lindenbaum",
#                             description="qa_chain")

#     def get_llm_query_result(self, query) -> str:
#         response = self.qa_chain.invoke(query)
#         print(response["result"])
#         for doc in response["source_documents"]:
#             print(doc.metadata, doc.page_content[:200])
#         return "result"