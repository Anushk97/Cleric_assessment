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

def migrate_facts_to_dict(questions_and_facts):
    for date_key, facts in questions_and_facts["factsByDay"].items():
        migrated_facts = []
        for fact in facts:
            if isinstance(fact, str):
                migrated_facts.append({"text": fact, "timestamp": None, "action": "existing"})
            else:
                migrated_facts.append(fact)
        questions_and_facts["factsByDay"][date_key] = migrated_facts

#migrate_facts_to_dict(questions_and_facts)

def fetch_and_extract_text(urls):
    extracted_texts = {}
    for url in urls:
        if not url or not (url.startswith('http://') or url.startswith('https://')):
            print(f"Skipping invalid URL: '{url}'")
        try:
            response = requests.get(url)
            response.raise_for_status()
            extracted_texts[url] = response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch or extract text from {url}: {e}")
            extracted_texts[url] = "" 
    return extracted_texts

def find_contradictions(new_fact, existing_facts):
    #print('new fact', new_fact)
    #print('existing fact', existing_facts)
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
        
        #print('response', response)
        
        if response.choices:
            content = response.choices[0].message.content
            if "yes" in content.lower():
                contradictions['existing_facts'].append(existing_fact)
        
        # if "yes" in response.choices[0].text.lower():
        #     contradictions.append(existing_fact)

    print('contradictions', contradictions)
    return contradictions


@app.route('/submit_question_and_documents', methods = ['POST'])
def submit_question_and_documents():
    #print(request.form)
    #question = request.form.get('question', '')
    #document_urls = request.form.get('documents', '').split(',')  # Assuming URLs are comma-separated
    
    data = request.get_json()  # Use get_json() to parse the JSON body
    question = data.get('question', '')
    document_urls = data.get('documents', [])
    
    #print("Document URLs:", document_urls)
    
    document_texts = fetch_and_extract_text(document_urls)
    
    #questions_and_facts["factsByDay"] = {}
    all_suggestions = {}
    
    for url, document_text in document_texts.items():
        # Process each document's text with the OpenAI API to extract facts
        date_match = re.search(r'\d{4}\d{2}\d{2}', url)
        # print('date match', date_match)
        
        if date_match:
            document_date = date_match.group(0)
        else:
            document_date = "2024-01-02"  # Default date
            
        document_date_obj = datetime.strptime(document_date, "%Y%m%d")
        # print('doc date', document_date_obj)
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",  # or the latest available model
            messages=[
            {"role": "system", "content": "You are a smart assistant tasked with summarizing key decisions and important facts from a series of call logs. summarize each new point or insight or decision made in the call log. start each point by the team has. generate at least three points."},
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
        # print('formatted date', formatted_date)
        questions_and_facts['documents'].append(url)
        if formatted_date in all_suggestions:
            pass
        else:
            all_suggestions[formatted_date] = []

        existing_facts = [fact['text'] for facts_list in questions_and_facts["factsByDay"].values() for fact in facts_list]

        for fact_text in extracted_facts:
            contradictions = find_contradictions(fact_text, existing_facts)
            #fact_detail = {"text": fact_text, "timestamp": current_timestamp, "action": "existing", "date": formatted_date}
            fact_detail = {"text": fact_text, "timestamp": current_timestamp, "question": question, "documents":[url], "contradictions":contradictions} #versioning by timestamp 
            # print('fact detail', fact_detail)
            questions_and_facts["factsByDay"].setdefault(formatted_date, []).append(fact_detail)            
            # all_suggestions[formatted_date].append({"text": fact_text, "timestamp": current_timestamp})
            all_suggestions[formatted_date].append(fact_detail)
            #all_suggestions.append(fact_detail)
    
    questions_and_facts['question'].append(question)
    questions_and_facts["status"] = "done"
    # print('P1', questions_and_facts)
    
    #print('SUGGESTION', all_suggestions)
    #print('questions and facts', questions_and_facts)
    #return jsonify({"suggestions": suggestions_with_dates})
    
    #return jsonify({"suggestions": questions_and_facts["factsByDay"][formatted_date]})
    return jsonify({'suggestions': all_suggestions})


@app.route('/submit_and_retrieve', methods=['POST'])
def submit_and_retrieve():
    
    questions_and_facts_2 = {
    "question": "",
    "factsByDay": {},
    "status": "processing" 
    }
    
    data = request.get_json()  # Use get_json() to parse the JSON body
    question = data.get('question', '')
    document_urls = data.get('documents', [])
    
    questions_and_facts_2['question'] = question
    
    document_texts = fetch_and_extract_text(document_urls)
    
    for url, document_text in document_texts.items():
        # Process each document's text with the OpenAI API to extract facts
        date_match = re.search(r'\d{4}\d{2}\d{2}', url)
        # print('date match', date_match)
        
        if date_match:
            document_date = date_match.group(0)
        else:
            document_date = "2024-01-02"  # Default date
            
        document_date_obj = datetime.strptime(document_date, "%Y%m%d")
        # print('doc date', document_date_obj)
        
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",  # or the latest available model
            messages=[
            {"role": "system", "content": "You are a smart assistant tasked with summarizing key decisions and important facts from a series of call logs. summarize each new point or insight or decision made in the call log. start each point by the team has. generate at least three points."},
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
        # print('formatted date', formatted_date)

        # existing_facts = [fact['text'] for facts_list in questions_and_facts_2["factsByDay"].values() for fact in facts_list]

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
    # Create a new dictionary to hold only non-rejected facts
    filtered_questions_and_facts = copy.deepcopy(questions_and_facts)
    # print('FLAG2', questions_and_facts)
    current_time = datetime.now()
    question = questions_and_facts.get("question")
    min_date = datetime.max
    unique_questions = list(set(questions_and_facts["question"]))
    
    for date, facts in filtered_questions_and_facts["factsByDay"].items():
        # Filter out facts where the action is 'rejected'
        # facts[:] = [fact for fact in facts if isinstance(fact, dict) and fact.get("action") != "rejected"]
        for fact in facts:
            if 'timestamp' in fact:
                fact_date = datetime.strptime(fact['timestamp'].split("T")[0], "%Y-%m-%d")
                if fact_date < min_date:
                    min_date = fact_date
                hours_diff = (current_time - fact_date).total_seconds() / 3600
                fact['hours_diff'] = hours_diff
    #start_date = min_date.strftime('%Y-%m-%d')
    
    if filtered_questions_and_facts["factsByDay"]:
        # Assuming the keys are already in 'YYYY-MM-DD' format
        all_dates = list(questions_and_facts["factsByDay"].keys())
        start_date = min(all_dates)  # Find the earliest date
    else:
        start_date = min_date.strftime('%Y-%m-%d')
    
    #print('start date', start_date)
    #print('filtered facts', filtered_questions_and_facts)
    # Pass the filtered facts to the template instead of the original questions_and_facts["factsByDay"]
    return render_template('view_facts.html',unique_questions=unique_questions, start_date=start_date, questions_and_facts=filtered_questions_and_facts, current_time=current_time)

@app.route('/record_suggestion', methods=['POST'])
def record_suggestion():
    data = request.get_json()
    # print('data in RS', data)
    suggestion = data.get('suggestion')
    # print('suggestion:', suggestion)
    action = data.get('action')
    # print('action in RS::', action)
    date_key = data.get('date')
    #date_key = '2024-01-02'
    #print('date_key', date_key)
    
    # print('FLAG4', questions_and_facts)

    #current_timestamp = datetime.now().isoformat()
    # print('FLAG1')
    if action == "accept":
        # print('FLAG3')
        for fact in questions_and_facts["factsByDay"].get(date_key):
            # print('FACT', fact['text'])
            if fact["text"] == suggestion['text']:
                
                #print("YASSSS")
                fact["action"] = "accepted"  # Update the action to 'added'

    elif action == "reject":        
        #print("NOOOO")
        for fact in questions_and_facts["factsByDay"].get(date_key):
            if fact["text"] == suggestion['text']:                
                fact['action'] = "rejected"
        
    # print("Q&F", questions_and_facts)
    return jsonify({"status": "success"})

from flask import request, jsonify

@app.route('/record_contradiction', methods=['POST'])
def record_contradiction():
    data = request.get_json()
    suggestion_id = data.get('identifier')  # Identifier for the suggestion containing the contradiction
    action = data.get('action')  # 'keep' or 'remove'
    #print('ACTION', action)
    # Split the identifier to extract date and index
    parts = suggestion_id.split('-')
    date_key = '-'.join(parts[0:3])
    index = int(parts[-1])

    # Find the suggestion based on date and index
    suggestion = questions_and_facts["factsByDay"][date_key][index]
    #print('suggestion---', suggestion)
    
    if action == "keep":
        # Mark the fact's contradiction status as 'keep'
        if 'contradictions' in suggestion:
            suggestion['contradictions']['status'] = 'keep'
    elif action == "remove":
        # Mark the fact's contradiction status as 'remove'
        if 'contradictions' in suggestion:
            suggestion['contradictions']['status'] = 'remove'
    
    #print('Q&F', questions_and_facts)
    #print('suggestion---*', suggestion)
    return jsonify({"status": "success"})


@app.route('/bulk_record_suggestion', methods=['POST'])
def bulk_record_suggestion():
    data = request.get_json()
    suggestions = data.get('suggestions', {})  # Expecting a dictionary with dates as keys
    action = data.get('action', '')  # 'accept' or 'reject'

    # Loop through the dictionary of suggestions
    for date_key, suggestions_list in suggestions.items():
        for suggestion in suggestions_list:
            suggestion_text = suggestion.get('text')

            if action == "accept":
                # Logic to mark the suggestion as accepted
                if date_key in questions_and_facts["factsByDay"]:
                    for fact in questions_and_facts["factsByDay"][date_key]:
                        if fact['text'] == suggestion_text:
                            fact['action'] = 'accepted'  # Mark as accepted

            elif action == "reject":
                # Logic to mark the suggestion as rejected
                if date_key in questions_and_facts["factsByDay"]:
                    for fact in questions_and_facts["factsByDay"][date_key]:
                        if fact['text'] == suggestion_text:
                            fact['action'] = 'rejected'  # Mark as rejected

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

