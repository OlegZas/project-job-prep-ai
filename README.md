# Streamlit link : https://olegzas-pro.streamlit.app/

# DataPrep AI

DataPrep AI is a Python web app that helps users prepare for data engineering interviews.

The app lets users upload interview notes, resumes, job descriptions, SQL notes, Kafka notes, or cloud study guides. It reads the documents, splits them into smaller chunks, creates embeddings, searches for the most useful chunks, and sends that context to OpenAI to generate an interview-focused answer.

## Business Use Case

Data engineering candidates often study from many different files and notes. This app helps organize that information in one place. A user can ask questions and get answers based on their own documents.

The target user is someone preparing for a data engineering interview.

## Main Features

* Upload TXT, MD, or PDF files
* Use sample interview notes
* Ask questions about uploaded documents
* Retrieve the most relevant document chunks
* Generate answers using OpenAI
* Show references used for the answer
* Ask live market knowledge questions about data engineering topics

## Tech Stack

* Python
* Streamlit
* OpenAI API
* OpenAI embeddings
* NumPy
* PyPDF
* python-dotenv
* GitHub
* Streamlit Community Cloud


## Example Questions

```text
What is a Kafka consumer group?
What are SQL window functions?
What is BigQuery partitioning?
Based on my notes, what interview topics should I study?
What skills are important for data engineers?
```

## Future Improvements

In the future, I would like to add saved chat history, better document storage, BigQuery logging, Docker, Cloud Run deployment, and interview quiz scoring.
