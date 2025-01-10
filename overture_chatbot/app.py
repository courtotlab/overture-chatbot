"""
   Copyright 2025 Ontario Institute for Cancer Research

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

"""Chainlit GUI for chatbot"""

import chainlit as cl
from query_graphql import query_total_chain

@cl.on_chat_start
async def on_chat_start():
    """Chainlit hook that executes on start of chat"""
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
    """Chainlit hook that executes after every message"""
    answer = await cl.make_async(invoke_query_total_chain)({"query": message.content})
    await cl.Message(
        content=answer,
    ).send()
