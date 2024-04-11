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

