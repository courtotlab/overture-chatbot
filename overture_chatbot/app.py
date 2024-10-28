"""Chainlit GUI for chatbot"""

import chainlit as cl
from query_graphql import query_total_chain

@cl.on_chat_start
async def on_chat_start():
    """Chainlit hook that excecutes on start of chat"""
    await cl.Message(content="Welcome to the Overture Chatbot!").send()

def invoke_query_total_chain(query):
    """Creates a Langchain chain and invokes

    Parameters
    ----------
    query : dict
        Dictionary with "query" as a key and a custom query message

    Returns
    -------
    str
        Returns the result of the invoked chain
    
    See Also
    --------
    query_graphql.query_total_chain
    """
    chain = query_total_chain()
    result = chain.invoke(query)

    return result

@cl.on_message
async def on_message(message: cl.Message):
    """Chainlit hook that excecutes after every message"""
    answer = await cl.make_async(invoke_query_total_chain)({"query": message.content})
    await cl.Message(
        content=answer,
    ).send()
