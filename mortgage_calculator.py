import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
import numpy as np
from io import StringIO

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

if image_file is not None:
    if st.button("Convert Image to CSV"):
        try:
             
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

            # xlnet.pdf is an example file; we support pdf, doc, and image formats. For images and pdf files, we provide OCR capabilities.
            file_object = client.files.create(file=image_file, purpose="file-extract")
            
            # Retrieve the result
            # file_content = client.files.retrieve_content(file_id=file_object.id)
            # Note: The previous retrieve_content API is marked as deprecated in the latest version. You can use the following line instead.
            # If you are using an older version, you can use retrieve_content.
            file_content = client.files.content(file_id=file_object.id).text
            
            # Include it in the request
            messages = [
                {
                    "role": "system",
                    "content": "You are Kimi, an AI assistant provided by Moonshot AI. You are particularly skilled in Chinese and English conversations. You provide users with safe, helpful, and accurate answers. You will refuse to answer any questions involving terrorism, racism, pornography, or violence. Moonshot AI is a proper noun and should not be translated into other languages.",
                },
                {
                    "role": "system",
                    "content": file_content,
                },
                #{"role": "user", "content": f"Give a brief introduction of what {image_file.name} is about. If it is financial, and possible to convert it to CSV format, provide the csv. Otherwise, provide FALSE for the CSV output. Ensure output is in a string array format [description, csv], where the delimiter between description and csv is ', \"'"},
                {"role": "user", "content": f"If the data in {image_file.name} is financial, convert it to CSV format. Otherwise, provide FALSE for the CSV output. "},
            ]
            
            # Then call chat-completion to get Kimi's response            
            completion = client.chat.completions.create(
            model="kimi-k2-turbo-preview",
            messages=messages,
            temperature=0.6,
            )

            st.write(completion.choices[0].message.content)
            # filter = completion.choices[0].message.content.replace('TRUE\n```csv\n', '')
            # filter = 'Date' + completion.choices[0].message.content.split("Date",1)[1]
            filter = completion.choices[0].message.content.split("Balance",1)[1]
            st.write(filter)

            
            # csv_string = """2003-10-08,Previous balance,,,0.55,0.55
            #     2003-10-14,Payroll Deposit - HOTEL,,,694.81,695.36
            #     2003-10-14,Web Bill Payment - MASTERCARD,9685,200.00,,495.36"""

            csv_string = "" + filter + ""

            # 2. Convert to DataFrame with explicit column names
            # header=None ensures the first row (2021-10-10) is read as data, not a header.
            # names=[...] applies your custom labels to the columns.
            csv_data = StringIO(csv_string)
            df = pd.read_csv(
                csv_data, 
                header=None, 
                names=['Date', 'Description', 'Ref.', 'withdrawals', 'Deposits', 'Balance'],
                skipinitialspace=True
            )

            # 3. Pre-process (Same as before)
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

            # 4. Streamlit Plotting
            st.title("Balance Over Time")
            st.write("Data Frame with Manual Headers:", df)
            st.line_chart(df['Balance'])

        except Exception as e:
            st.error(f"Error processing image: {e}")



 
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
