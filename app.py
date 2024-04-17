from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import requests
import openai
import re
from datetime import datetime, timedelta
import copy

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')

openai.api_key = ''

questions_and_facts = {
    "question": [],
    "documents": [],
    "factsByDay": {},
    "status": "processing" 
}


def fetch_and_extract_text(urls):
    extracted_texts = {}
    for url in urls:
        if not url or not (url.startswith('http://') or url.startswith('https://')):
            print(f"Skipping invalid URL: '{url}'")
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            extracted_texts[url] = response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch or extract text from {url}: {e}")
            extracted_texts[url] = ""  # Consider how you want to handle failures
    return extracted_texts

def find_contradictions(new_fact, existing_facts):
    contradictions = {'existing_facts': [],
                    'status': 'keep'}
    for existing_fact in existing_facts:
        prompt = f"Does the statement: '{new_fact}' contradict the existing fact: '{existing_fact}'?"

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
            {"role": "system", "content": prompt}],
        n=1,
        stop=None,
        temperature=0.4
        )
        
        if response.choices:
            content = response.choices[0].message.content
            if "yes" in content.lower():
                contradictions['existing_facts'].append(existing_fact)
    
    return contradictions


@app.route('/submit_question_and_documents', methods = ['POST'])
def submit_question_and_documents():
    
    data = request.get_json()
    question = data.get('question', '')
    document_urls = data.get('documents', [])
    
    document_texts = fetch_and_extract_text(document_urls)
    all_suggestions = {}
    
    for url, document_text in document_texts.items():
        date_match = re.search(r'\d{4}\d{2}\d{2}', url)
        
        if date_match:
            document_date = date_match.group(0)
        else:
            document_date = "2024-01-02"  # Default date
            
        document_date_obj = datetime.strptime(document_date, "%Y%m%d")
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
            {"role": "system", "content": """
            You are a smart assistant tasked with summarizing key decisions and important facts from a series of call logs.\n
            Summarize each new point or insight or decision made in the call log.\n
            Start each point by the team has.\n 
            Generate at least three points.\n
            """
            },
                {"role": "user", "content": f"{document_text}"},
                {"role": "system", "content": f"Based on the above, {question}"}
    ],
            n=1,
            stop=None,
            temperature=0.4
        )
        
        extracted_facts = response.choices[0].message.content.strip().split('\n')
        
        current_timestamp = datetime.now().isoformat()
        formatted_date = document_date_obj.strftime("%Y-%m-%d")
        questions_and_facts['documents'].append(url)
        if formatted_date in all_suggestions:
            pass
        else:
            all_suggestions[formatted_date] = []

        existing_facts = [fact['text'] for facts_list in questions_and_facts["factsByDay"].values() for fact in facts_list]

        for fact_text in extracted_facts:
            if fact_text.strip():
                contradictions = find_contradictions(fact_text, existing_facts)
                fact_detail = {"text": fact_text, "timestamp": current_timestamp, "question": question, "documents":[url], "contradictions":contradictions}
                
                questions_and_facts["factsByDay"].setdefault(formatted_date, []).append(fact_detail)            
                
                all_suggestions[formatted_date].append(fact_detail)
    
    questions_and_facts['question'].append(question)
    questions_and_facts["status"] = "done"
    
    return jsonify({'suggestions': all_suggestions})


@app.route('/submit_and_retrieve', methods=['POST'])
def submit_and_retrieve():
    
    questions_and_facts_2 = {
    "question": "",
    "factsByDay": {},
    "status": "processing" 
    }
    
    data = request.get_json()
    question = data.get('question', '')
    document_urls = data.get('documents', [])
    
    questions_and_facts_2['question'] = question
    
    document_texts = fetch_and_extract_text(document_urls)
    
    for url, document_text in document_texts.items():
        
        date_match = re.search(r'\d{4}\d{2}\d{2}', url)
        if date_match:
            document_date = date_match.group(0)
        else:
            document_date = "2024-01-02"  # Default date
            
        document_date_obj = datetime.strptime(document_date, "%Y%m%d")
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
            {"role": "system", "content": """
            You are a smart assistant tasked with summarizing key decisions and important facts from a series of call logs.\n
            Summarize each new point or insight or decision made in the call log.\n
            Start each point by the team has.\n 
            Generate at least three points.\n
            
            
            
            """},
                {"role": "user", "content": f"{document_text}"},
                {"role": "system", "content": f"Based on the above, {question}"}
    ],
            n=1,
            stop=None,
            temperature=0.4
        )
        
        extracted_facts = response.choices[0].message.content.strip().split('\n')
        
        current_timestamp = datetime.now().isoformat()
        formatted_date = document_date_obj.strftime("%Y-%m-%d")

        for fact_text in extracted_facts:
            if fact_text.strip():

                questions_and_facts_2["factsByDay"].setdefault(formatted_date, []).append(fact_text)
        
    questions_and_facts_2["status"] = "done"
    
    return jsonify(questions_and_facts_2)

@app.route('/submit_question', methods=['GET'])
def submit_question_page():
    return render_template('submit_question.html')

@app.route('/get_question_and_facts', methods=['GET'])
def get_question_and_facts():
    return jsonify(questions_and_facts), 200


@app.route('/view_facts', methods=['GET'])
def view_facts_page():
    
    filtered_questions_and_facts = copy.deepcopy(questions_and_facts)
    current_time = datetime.now()
    question = questions_and_facts.get("question")
    min_date = datetime.max
    unique_questions = list(set(questions_and_facts["question"]))
    
    for date, facts in filtered_questions_and_facts["factsByDay"].items():
        for fact in facts:
            if 'timestamp' in fact:
                fact_date = datetime.strptime(fact['timestamp'].split("T")[0], "%Y-%m-%d")
                if fact_date < min_date:
                    min_date = fact_date
                hours_diff = (current_time - fact_date).total_seconds() / 3600
                fact['hours_diff'] = hours_diff
    
    if filtered_questions_and_facts["factsByDay"]:
    
        all_dates = list(questions_and_facts["factsByDay"].keys())
        start_date = min(all_dates)  # Find the earliest date
    else:
        start_date = min_date.strftime('%Y-%m-%d')
    
    return render_template('view_facts.html',unique_questions=unique_questions, start_date=start_date, questions_and_facts=filtered_questions_and_facts, current_time=current_time)

@app.route('/record_suggestion', methods=['POST'])
def record_suggestion():
    data = request.get_json()
    suggestion = data.get('suggestion')
    action = data.get('action')
    date_key = data.get('date')
    
    if action == "accept":
        for fact in questions_and_facts["factsByDay"].get(date_key):
            if fact["text"] == suggestion['text']:
                
                fact["action"] = "accepted" 

    elif action == "reject":
        for fact in questions_and_facts["factsByDay"].get(date_key):
            if fact["text"] == suggestion['text']:                
                fact['action'] = "rejected"
        
    return jsonify({"status": "success"})

from flask import request, jsonify

@app.route('/record_contradiction', methods=['POST'])
def record_contradiction():
    data = request.get_json()
    suggestion_id = data.get('identifier')
    action = data.get('action')
    parts = suggestion_id.split('-')
    date_key = '-'.join(parts[0:3])
    index = int(parts[-1])
    
    suggestion = questions_and_facts["factsByDay"][date_key][index]
    
    if action == "keep":
        if 'contradictions' in suggestion:
            suggestion['contradictions']['status'] = 'keep'
    elif action == "remove":
        
        if 'contradictions' in suggestion:
            suggestion['contradictions']['status'] = 'remove'
    
    return jsonify({"status": "success"})


@app.route('/bulk_record_suggestion', methods=['POST'])
def bulk_record_suggestion():
    data = request.get_json()
    suggestions = data.get('suggestions', {})
    action = data.get('action', '')
    
    for date_key, suggestions_list in suggestions.items():
        for suggestion in suggestions_list:
            suggestion_text = suggestion.get('text')

            if action == "accept":
                
                if date_key in questions_and_facts["factsByDay"]:
                    for fact in questions_and_facts["factsByDay"][date_key]:
                        if fact['text'] == suggestion_text:
                            fact['action'] = 'accepted'
                            
            elif action == "reject":
                
                if date_key in questions_and_facts["factsByDay"]:
                    for fact in questions_and_facts["factsByDay"][date_key]:
                        if fact['text'] == suggestion_text:
                            fact['action'] = 'rejected'

    return jsonify({"status": "success"})

@app.route('/reset_questions_and_facts', methods=['POST'])
def reset_questions_and_facts():
    global questions_and_facts
    questions_and_facts = {
        'question': [],
        'documents': [],
        'factsByDay': {},
        'status': 'processing'
    }

    return jsonify({'status': 'success'})

@app.route("/")
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(port=8000, debug=True)

