import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

st.title("Mortgage Repayments Calculator")

st.write("### Input Data")
col1, col2 = st.columns(2)
home_value = col1.number_input("Home Value", min_value=0, value=500000)
deposit = col1.number_input("Deposit", min_value=0, value=100000)
interest_rate = col2.number_input("Interest Rate (in %)", min_value=0.0, value=5.5)
loan_term = col2.number_input("Loan Term (in years)", min_value=1, value=30)

# Image Ingestion Section
import requests
import io

st.write("### Ingest Image and Convert to CSV via Kimi K2")
image_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

from openai import OpenAI
 
client = OpenAI(
    api_key="sk-WSH31D2FSxhTXUaNTDQIqSVfOyOuh7adtBnwOhYUKDrzBbc1", # Replace MOONSHOT_API_KEY with the API Key you obtained from the Kimi Open Platform
    base_url="https://api.moonshot.ai/v1",
)
 
completion = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "system", "content": "You are Kimi, an AI assistant provided by Moonshot AI. You are proficient in Chinese and English conversations. You provide users with safe, helpful, and accurate answers. You will reject any requests involving terrorism, racism, or explicit content. Moonshot AI is a proper noun and should not be translated."},
        {"role": "user", "content": "Hello, my name is Li Lei. What is 1+1?"}
    ],
    temperature = 0.6,
)
 
# We receive a response from the Kimi large language model via the API (role=assistant)
st.write(completion.choices[0].message.content)

#  if image_file is not None:
#     api_key = st.secrets.get("kimi_k2_api_key", None)
#     if not api_key:
#         api_key = st.text_input("Enter your Kimi K2 API Key", type="password")
#     if api_key:
#         if st.button("Convert Image to CSV"):
#             try:
#                 # Prepare the image for upload
#                 files = {"file": (image_file.name, image_file, image_file.type)}
#                 headers = {"Authorization": f"Bearer {api_key}"}
#                 # Replace the URL below with the actual Kimi K2 endpoint
#                 response = requests.post(
#                     "https://api.kimi.com/v1/k2/convert-image-to-csv",
#                     files=files,
#                     headers=headers,
#                 )
#                 if response.status_code == 200:
#                     csv_content = response.content.decode("utf-8")
#                     df_csv = pd.read_csv(io.StringIO(csv_content))
#                     st.write("#### CSV Data Preview")
#                     st.dataframe(df_csv)
#                 else:
#                     st.error(f"Kimi K2 API Error: {response.status_code} - {response.text}")
#             except Exception as e:
#                 st.error(f"Error processing image: {e}")
#     else:
#         st.info("Please provide your Kimi K2 API key.")
 
# Calculate the repayments.
loan_amount = home_value - deposit
monthly_interest_rate = (interest_rate / 100) / 12
number_of_payments = loan_term * 12
monthly_payment = (
    loan_amount
    * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments)
    / ((1 + monthly_interest_rate) ** number_of_payments - 1)
)

# Display the repayments.
total_payments = monthly_payment * number_of_payments
total_interest = total_payments - loan_amount

st.write("### Repayments")
col1, col2, col3 = st.columns(3)
col1.metric(label="Monthly Repayments", value=f"${monthly_payment:,.2f}")
col2.metric(label="Total Repayments", value=f"${total_payments:,.0f}")
col3.metric(label="Total Interest", value=f"${total_interest:,.0f}")


# Create a data-frame with the payment schedule.
schedule = []
remaining_balance = loan_amount

for i in range(1, number_of_payments + 1):
    interest_payment = remaining_balance * monthly_interest_rate
    principal_payment = monthly_payment - interest_payment
    remaining_balance -= principal_payment
    year = math.ceil(i / 12)  # Calculate the year into the loan
    schedule.append(
        [
            i,
            monthly_payment,
            principal_payment,
            interest_payment,
            remaining_balance,
            year,
        ]
    )

df = pd.DataFrame(
    schedule,
    columns=["Month", "Payment", "Principal", "Interest", "Remaining Balance", "Year"],
)

# Display the data-frame as a chart.
st.write("### Payment Schedule")
payments_df = df[["Year", "Remaining Balance"]].groupby("Year").min()
st.line_chart(payments_df)
