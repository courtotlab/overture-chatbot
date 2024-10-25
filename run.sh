#!/bin/sh
python3 initialize_db/main.py
chainlit run overture_chatbot/app.py --host=0.0.0.0 --port=5000 --headless
