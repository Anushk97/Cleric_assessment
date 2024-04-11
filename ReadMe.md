# Cleric AI Engineer Assignment

## Frontend Design

**Framework**: I chose Flask for its simplicity and Python integration, making it ideal for rapid development and prototyping.

**User Interface**: HTML, CSS, and JavaScript were used to build a user-friendly and responsive interface. AJAX was implemented for dynamic content updates without full page reloads, enhancing user interaction.

## Backend Design

**Data Storage**: The application uses nested dictionaries and lists to store questions, facts, and contradictions in memory, providing fast access and manipulation during runtime. For future, I plan to integrate persistent storage for long-term data retention.

**Natural Language Processing (NLP)**: OpenAI's GPT models are utilized for summarizing documents and extracting facts, leveraging advanced NLP techniques for high-quality outputs.

**Contradiction Handling**: I built a custom algorithm to identify and manage contradictions within the extracted facts, allowing for a more nuanced understanding of the document content.

## Deployment

**Google Cloud**: The application is deployed on Google Cloud, leveraging its scalable infrastructure to accommodate varying loads and data availability.

**Containerization**: Docker is used for containerizing the application, simplifying deployment and ensuring consistency across different environments.

## Notes and Assumptions

- Suggestion box: Closing without selecting any suggestion will auto reject all suggestions.

- The URL checker attempts to create a URL object from the input string and checks if the protocol is either http or https. It returns true for valid URLs and false for invalid ones.

- Once a contradiction is removed, it will not show on the facts page.

## Test cases

- https://llm-bot-pficsoahpa-uc.a.run.app/static/call_log_20240314_104111.txt

- https://llm-bot-pficsoahpa-uc.a.run.app/static/call_log_20240315_104111.txt

- https://llm-bot-pficsoahpa-uc.a.run.app/static/call_log_20240317_104111.txt

