# Badozinator

A simple knowledge management system using a Retrieval-Augmented Generation (RAG) approach with the Mistral API and a Streamlit application.

I want to build a Knowledge management system based on a RAG architecture.
It should be in the form of a streamlit app.
What is already done:
- query functions and processing of confluence pages in utils/query_confluence
- mistral embedings & mistral llm functions for the rag are in utils/embeddings?py

In term of use cases i'd like the following:
- The user should be able to load files both Manually AND from confluence
- The corresponding document should be processed and saved so that the user could choose to reuse them later without having to reload and reprocess them
- After interacting with the document interface, the user should be able to access a chat app.
- The RAG provides an anwser based on the provided context as much as possible 
- If context is insufficient to answer, it should still give the best answer as possible but notifying the user that context provided was not enough
- At the end of each answer, the RAG should also provide the list of sources it used to provide its answer so that the user can double check or dig deeper if necessary