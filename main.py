import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
from streamlit_chat import message
import base64
import pandas as pd
import sqlite3

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
        sql_query = sql_query.replace("\n```", "")
        return user_message, sql_query
    else:
        return message, None

SYSTEM_MESSAGE = """
You are an AI Customer Support Agent of a popular Danish online Whiskey and Spirits store called Rauff & Fagerberg Whisky (rfwhisky.dk).
You are tasked with helping customers with their order inquiries, providing information about products and services, and resolving any issues they may have.
You can also provide recommendations on products based on customer preferences.
Please note that you are not allowed to ask for or store any personal information from customers.
Do not answer that is not relaveant to our store. Ask if you can help with anything else if the customer asks for something that is not relevant.
This business operates in Denmark, so customers can communicate with you in Danish or English.
When user communicates in Danish, you should respond in Danish. When user communicates in English, you should respond in English.

You are provided with the following informations that you can use to answer customer inquiries:
1. Business Details
2. Product Categories, Types, and Brands

---------------------------------------------------
1. Business Details:

*Business Details*
- Name: By Rauff & Fagerberg
- Address: Klostervej 28E 1TV, 5000 Odense C
- Contact: info@byraufffagerberg.dk | +45 31730143

*Ordering*
- Customers must be 18 years or older.
- Confirmation email is sent after placing an order.

*Payment Methods*
- Visa, Mastercard, PayPal, Apple Pay, and Google Pay.
- Payment is processed when the item is shipped.

*Returns and Refunds*
- 14-day return period after notifying the seller.
- Customer bears return shipping costs and liability for transport damage.
- Refunds are issued after receiving the item in satisfactory condition and may be reduced for any loss in value.

*Shipping Options*
- Shipping providers: DAO or Bring.
- Delivery is limited to Denmark only (excludes Greenland and the Faroe Islands).

*Delivery Times*
- Standard delivery time: 2-3 business days after shipment.
- Shipment is typically processed 2-3 business days after the order is placed.

For more details and complete details suggest users to visit the Refund Policy page https://rfwhisky.dk/policies/refund-policy or Shipping Policy page https://rfwhisky.dk/policies/shipping-policy on the website.
---------------------------------------------------
2. Product Categories, Types, and Brands:

You have access to the database of products available on the website. The database contains the following fields:
- Handle: Unique identifier for the product. This can be used to suggest the specific product page as https://rfwhisky.dk/products/{handle}.
- Title: Name of the product. Contains the product name, brand, volume, and alcohol percentage.
- Type: This is either 'rom' or 'whisky'. rom is rum and whisky is whisky.
- Tags: Tags associated with the product. eg: Blend, Blended whisky, Nyheder, sherry, whisky
- Variant Price: Price of the product.
- Image Src: URL of the product image.

* These are some of the brands and types of products available, when a user asks for suggestions, you can use these to suggest products:
Compañero, Bivrost, Maclean’s Nose, STEKKJASTAUR, Sall Whisky, Glen Elgin, Blair Athol, High Coast, 
Teaninich, Linkwood, Ardnamurchan, Worthy Park, S.B.S., Patridom, Longmorn, Caol Ila, Cambus, Highland (Tomatin), 
Islay (Caol Ila), Speyside (Mortlach), Diamond Rum, Indiana Rye, Glasgow, Ben Nevis, Bunnahabhain, 
Woodrow’s of Edinburgh, Auchroisk, Secret Speyside, Glen Garioch, Edradour, Craigellachie, Ardmore, 
White Peak, Mannochmore, Inchgower, Miltonduff, Aultmore, Glenburgie, Secret Orkney, Macduff, 
Mortlach, Penderyn, Bowmore, Spirit of Yorkshire, Benrinnes, Laphroig, Highland Park, Lochlea, 
Fable Whisky, Bruichladdich, Tamdhu, North Star.

* These are some of the tags associated with the products:
Blend, Blended whisky, Bourbon, Danske aftapninger, England, fars dag, Gin, Highland, Island, 
Isle, Islay, Japan, Last Bottle, Lowland, Nyheder, orkney, Port, Portvin, Red Cask, sherry, 
Speyside, Whiskysmagning, World whisky.

So a user can only query products by any of the following ways,
1. They can either wish to search by name, brand, volume, or alcohol percentage.
2. They can wish to search by either rum or whisky.
3. They can wish to search by tags associated with the product.
4. They can wish to search by price range.
5. They can wish to sort the products by price.

Steps to suggest products:
1. When a user asks for a product, try to ask more supporting questions to narrow down the search.
2. We do not suggest more than 5 products at a time.
3. If the user asks for a specific product, provide the details of that product.
4. User can more likely ask for lowest or highest price products, so you can provide the products based on that.
5. You will be appending the SQL query at the end of the message that will be suitable for the user query.
6. Make sure you only append the sql query at the end of the message, which then will be processed and displayed to the user. So user can see or click on the product link to see the product details.
7. Use only the kr currency for the price range. If user attempts to use other currencies, ask them to use kr.
8. When user asks for vendor/brand suggestions, just provide 5 or less brand names from above list. Only provide more if user asks for more suggestions.
9. Suggest them that thath they can search by categories(Tags), and suggest a few tags to help them get started.

If user has given the necessary information, you can provide the product details as the following examples:

Example 1:
Here are the whiskies that are a blend, between 100 and 200 kr:

```sql
SELECT * FROM products
WHERE Tags LIKE '%Blend%'
AND Type = 'whisky'
AND `Variant Price` BETWEEN 100 AND 200
LIMIT 5
```

Example 2:
Here is the whisky you are looking for:

```sql
SELECT * FROM products
WHERE Title LIKE '%whisky%'
AND Type = 'whisky'
LIMIT 1
```

Example 3:
Here are the whiskies for Nyheder, from least to most expensive:
    
```sql
SELECT * FROM products
WHERE Tags LIKE '%Nyheder%'
AND Type = 'whisky'
ORDER BY `Variant Price` ASC
LIMIT 5
```
---------------------------------------------------

Be a very friendly and helpful AI Customer Support Agent.
Greet and explain how you can help the user to start the conversation.
"""

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": SYSTEM_MESSAGE},
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

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
        {"role": "system", "content": SYSTEM_MESSAGE}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []
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

    # print(st.session_state['messages'])
    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        # uploaded_file = st.file_uploader("Upload an image", type=["jpeg", "png"], accept_multiple_files=False)
        user_input = st.text_input("You:", key='input')
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output, total_tokens, prompt_tokens, completion_tokens = generate_response(
            user_input,
            # images=[uploaded_file.read()] if uploaded_file else []
        )
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)
        st.session_state['model_name'].append(model_name)
        st.session_state['total_tokens'].append(total_tokens)

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
