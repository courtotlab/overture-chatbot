import chainlit as cl
from query_graphql import query_total_chain

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Welcome to the Overture Chatbot!").send()
    langchain_chain = query_total_chain()
    cl.user_session.set("runnable", langchain_chain)

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")

    msg = cl.Message(content="")

    for chunk in await cl.make_async(runnable.stream)(
        {"query": message.content},
    ):
        await msg.stream_token(chunk)

    await msg.send()
