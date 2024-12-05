# Overture Chatbot (Development Branch)
This project aims to allow unstructured queries on an Overture data set using a chat interface. Data is currently derived from the [VirusSeq data set](https://virusseq-dataportal.ca/explorer) but ultimately aims to integrate with any Overture project.

## Status
In development

## Installation
1. Save the project to your local drive.
2. Assuming you have (Docker)[https://www.docker.com/] installed, you can navigate to the project directory and run `docker compose up` to create the containers.

It may take a significant amount of time (~25 minutes) to initially set up as the large language model files need to be downloaded and the vector database needs to be initialized the first time. It takes significantly less time to get up and going the second time.

## Usage
Once the logs say “chainlit-1 … Your app is available at http://0.0.0.0:5000’, you should be able to access the GUI on localhost:5000 or http://0.0.0.0:5000.

## Known Limitations
- There is limited support for non-NVIDIA GPUs (e.g. Apple's Metal), in part due to [macOS virtualization layer](https://chariotsolutions.com/blog/post/apple-silicon-gpus-docker-and-ollama-pick-two/); it should still run but the inference will be slower

## Roadmap
- Improve accuracy using (llama.cpp's grammar)[https://github.com/ggerganov/llama.cpp/blob/master/grammars/README.md]
- Date related searches
- Update testing suite to incorporate virtualization