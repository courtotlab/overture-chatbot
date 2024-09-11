import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="Welcome to the Overture Chatbot!").send()
    langchain_chain = pass
    cl.user_session.set("runnable", langchain_chain)