import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
from streamlit_chat import message
import base64
import pandas as pd
import sqlite3
from prompt import SUGGESTIONS_AGENT_SYSTEM_PROMPT, SYSTEM_PROMPT

# Load CSV file into DataFrame
df = pd.read_csv('data.csv')

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('data.db')

# Convert DataFrame to SQL table
df.to_sql('products', conn, if_exists='replace', index=False)

load_dotenv()

# Setting page title and header
st.set_page_config(page_title="Rauff & Fagerberg Whisky", page_icon=":robot_face:")
st.markdown("<h2 style='text-align: center;'>Rauff & Fagerberg Whisky - AI Assitant</h1>", unsafe_allow_html=True)
message("Velkommen til butikken! Hvordan kan jeg hjælpe dig i dag?\n\nWelcome to RFwhisky! How can i help you today?", key=str('-1'), allow_html=True)

# Create OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_sql_query_from_message(message: str) -> tuple[str, str]:
    if "```sql" in message:
        user_message = message.split("```sql")[0].strip()
        sql_query = message.split("```sql")[1].strip()
        sql_query = sql_query.split("```")[0].strip()
        return user_message, sql_query
    else:
        return message, None

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
if 'suggestions' not in st.session_state:
    st.session_state['suggestions'] = []
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0
if 'full_name' not in st.session_state:
    st.session_state['full_name'] = ""
if 'email' not in st.session_state:
    st.session_state['email'] = ""
if 'agreed' not in st.session_state:
    st.session_state['agreed'] = False

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("Sidebar")
model_name = st.sidebar.radio("Choose a model:", ("GPT-4o", "GPT-4o-Mini", "GPT-4-Turbo", "GPT-3.5", "O1-Preview"))
counter_placeholder = st.sidebar.empty()
counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# Map model names to OpenAI model IDs
if model_name == "GPT-4o":
    model = "gpt-4o"
elif model_name == "GPT-4o-Mini":
    model = "gpt-4o-mini"
elif model_name == "GPT-3.5":
    model = "gpt-3.5-turbo"
elif model_name == "GPT-4-Turbo":
    model = "gpt-4-turbo"
elif model_name == "O1-Preview":
    model = "o1-preview"

# reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    st.session_state['suggestions'] = []
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []
    st.session_state['full_name'] = ""
    st.session_state['email'] = ""
    st.session_state['agreed'] = False
    counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")


# generate a response
def generate_response(prompt, images: list[bytes] = None):
    if images:
        base64_image = base64.b64encode(images[0]).decode('utf-8')
        content = [
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                },
            },
        ]
        st.session_state['messages'].append({"role": "user", "content": content})
    else:
        st.session_state['messages'].append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model=model,
        messages=st.session_state['messages']
    )
    response = completion.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": response})
    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

# generate suggestions
def generate_suggestions(agent_prompt, user_prompt):
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {"role": "system", "content": SUGGESTIONS_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"""
User's Query:
{user_prompt}

AI Agent's Response:
{agent_prompt}

Next Possible Queriees from User:
""",
            },
        ],
    )
    response = completion.choices[0].message.content
    suggestions =  [
        line[2:] for line in response.split("\n") if line.strip()
    ]
    return suggestions

def update_chat_response_state(user_input):
    output, total_tokens, prompt_tokens, completion_tokens = generate_response(
        user_input,
        # images=[uploaded_file.read()] if uploaded_file else []
    )
    st.session_state['past'].append(user_input)
    st.session_state['generated'].append(output)
    st.session_state['model_name'].append(model_name)
    st.session_state['total_tokens'].append(total_tokens)
    suggestions = generate_suggestions(output, user_input)
    st.session_state['suggestions'] = suggestions
    # from https://openai.com/pricing#language-models
    if model_name == "GPT-4o": # Input: US$0.005 / 1K | Output: US$0.015 / 1K
        cost = ((prompt_tokens * 0.005) + (completion_tokens * 0.015)) / 1000
    elif model_name == "GPT-4o-Mini": # Input: US$0.00015 / 1K | Output: US$0.0006 / 1K
        cost = ((prompt_tokens * 0.0005) + (completion_tokens * 0.0015)) / 1000
    elif model_name == "GPT-3.5": # Input: US$0.003 / 1K | Output: US$0.006 / 1K
        cost = ((prompt_tokens * 0.003) + (completion_tokens * 0.006)) / 1000
    elif model_name == "GPT-4-Turbo": # Input: US$0.01 / 1K | Output: US$0.03 / 1K
        cost = ((prompt_tokens * 0.01) + (completion_tokens * 0.03)) / 1000
    elif model_name == "O1-Preview": # Input: US$0.002 / 1K | Output: US$0.006 / 1K
        cost = ((prompt_tokens * 0.002) + (completion_tokens * 0.006)) / 1000
    st.session_state['cost'].append(cost)
    st.session_state['total_cost'] += cost
    return output, suggestions

def user_form_submitted():
    return st.session_state["full_name"] and st.session_state["email"] and st.session_state["agreed"]

if not user_form_submitted():
    with st.form("details_form"):
        st.write("Provide your details")
        full_name_val = st.text_input("Full Name")
        email_val = st.text_input("Email")
        checkbox_val = st.checkbox("I agree to the terms and conditions")

        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["full_name"] = full_name_val
            st.session_state["email"] = email_val
            st.session_state["agreed"] = checkbox_val
            st.write(f"Hello {st.session_state['full_name']}! How can I help you today?")
else:
    message(f"Hello {st.session_state['full_name']}! How can I help you today?", key=str('-2'), allow_html=True)

# container for chat history
response_container = st.container()
# container for text box
container = st.container()
# container for suggestions
suggestions_container = st.container()

if user_form_submitted():
    with container:
        with st.form(key='my_form', clear_on_submit=True):
            # uploaded_file = st.file_uploader("Upload an image", type=["jpeg", "png"], accept_multiple_files=False)
            user_input = st.text_input("You:", key='input')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            update_chat_response_state(user_input)

if st.session_state['suggestions']:
    with suggestions_container:
        for suggestion in st.session_state['suggestions']:
            # click on suggestion to send it to the chat
            st.button(
                label=suggestion,
                on_click=lambda s=suggestion: update_chat_response_state(s),
            )

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            generated_message, sql_query = extract_sql_query_from_message(st.session_state["generated"][i])
            st.write("SQL Query: ", sql_query)
            if sql_query:
                result = pd.read_sql_query(sql_query, conn)
                if not result.empty:
                    message(generated_message, key=str(i), allow_html=True)
                    rows = [st.columns(3) for _ in range((len(result) + 2) // 3)]  # Create rows with 3 columns each
                
                    for index, row in result.iterrows():
                        col = rows[index // 3][index % 3]  # Get the correct column in the correct row
                        with col:
                            st.markdown(f"""
                            <div style="border: 1px solid #ddd; padding: 10px; margin: 10px; border-radius: 5px; text-align: center;">
                                <img src="{row['Image Src']}" alt="{row['Title']}" style="width: 100px; height: 100px;">
                                <h6>{row['Title']}</h6>
                                <p>Price: {row['Variant Price']} kr</p>
                                <a href="https://rfwhisky.dk/products/{row['Handle']}" target="_blank">View Product</a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    generated_message = "Sorry, no matching products found. Would you like to try any other whiskey or rum?"
                    message(generated_message, key=str(i), allow_html=True)
                    st.write("No results found.")
            else:
                message(generated_message, key=str(i), allow_html=True)
            # st.write(
            #     f"Model used: {st.session_state['model_name'][i]}; Number of tokens: {st.session_state['total_tokens'][i]}; Cost: ${st.session_state['cost'][i]:.5f}")
            counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")
