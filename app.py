import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GOOGLE_CREDENTIALS"], scope)
client = gspread.authorize(creds)
sheet = client.open("hello").sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("Quest International School")
st.subheader("Om Nagar, Maruthi Nagar, Langar Houz, Hyderabad, Telangana 500008")

# Section to Add a Student
st.header("Add Student")
with st.form("add_student_form"):
    admission_number = st.number_input("Admission Number", min_value=1, format="%d")
    student_name = st.text_input("Student Name")
    mobile_number = st.text_input("Parent Mobile Number")
    class_name = st.selectbox("Class", ["Nur", "PPI", "PPII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"])
    total_fee = st.number_input("Total Fee", min_value=0, format="%d")
    
    submit_button = st.form_submit_button("Add Student")
    
    if submit_button:
        if 'Admission number' in df.columns and admission_number in df['Admission number'].values:
            st.error(f"Student with Admission Number {admission_number} already exists!")
        elif not student_name or not mobile_number or not class_name or total_fee == 0:
            st.error("Please fill in all the required details before submitting the form.")    
        else:
            new_student = {
                "Admission number": admission_number,
                "Student Name": student_name,
                "Parent Mobile Number": mobile_number,
                "Class": class_name,
                "Total Fee": int(total_fee),
                "Paid Amount": 0,
                "Remaining Balance": int(total_fee),
                "Payment History": "",
                "Receipt Number": "",
                "Payment Date": ""
            }
            new_student_df = pd.DataFrame([new_student])
            df = pd.concat([df, new_student_df], ignore_index=True)
            sheet.append_row([admission_number, student_name, mobile_number, class_name, int(total_fee), 0, int(total_fee), "", "", ""])  
            st.success("Student added successfully!")

# Section to Add Payments
st.header("Add Payment for a Student")
existing_admission_numbers = df['Admission number'].tolist()

selected_admission_number = st.selectbox("Select Student by Admission Number", existing_admission_numbers)

if selected_admission_number:
    # Automatically fetch and display student name
    student_row = df[df['Admission number'] == selected_admission_number].iloc[0]
    student_name = student_row['Student Name']
    st.write(f"Student Name: {student_name}")
    st.write(f"Total Fee: {student_row['Total Fee']}")
    st.write(f"Paid Amount: {student_row['Paid Amount']}")
    st.write(f"Remaining Balance: {student_row['Remaining Balance']}")
    
    # Payment Type
    payment_type = st.selectbox("Select Payment Type", ["Term-wise", "Month-wise", "Custom-wise"])
    
    if payment_type == "Term-wise":
        term_options = st.multiselect("Select Term(s)", ["I Term", "II Term", "III Term"])
        amount = st.number_input(f"Enter Payment Amount for Term(s)", min_value=0, format="%d")
        payment_type_detail = f"Term-wise: {', '.join(term_options)}" if term_options else "Term-wise"

    elif payment_type == "Month-wise":
        month_options = st.multiselect("Select Month(s)", [f"{str(i).zfill(2)}-month" for i in range(1, 11)])
        amount = st.number_input(f"Enter Payment Amount for Month(s)", min_value=0, format="%d")
        payment_type_detail = f"Month-wise: {', '.join(month_options)}" if month_options else "Month-wise"

    elif payment_type == "Custom-wise":
        amount = st.number_input("Enter Custom Payment Amount", min_value=0, format="%d")
        payment_type_detail = "Custom-wise"

    add_payment_button = st.button("Add Payment")

    if add_payment_button:
        paid_amount = student_row['Paid Amount'] if pd.notna(student_row['Paid Amount']) else 0
        amount = int(amount)
        remaining_balance = int(student_row['Total Fee']) - (paid_amount + amount)

        if remaining_balance < 0:
            st.error("Paid amount exceeds the total fee! Please enter a valid amount.")
        else:
            # Generate receipt number (combining date, month, and admission number)
            payment_date = datetime.now()
            day = payment_date.strftime("%d")
            month = payment_date.strftime("%m")
            last_two_digits_admission = str(selected_admission_number)[-2:]

            # Receipt number: Day + Month + Last 2 digits of Admission Number (ensuring 5 digits)
            receipt_number = f"{day}{month}{last_two_digits_admission}".zfill(5)

            # Prepare the payment history
            payment_history = student_row['Payment History']
            new_payment = f"{payment_type_detail}, Amount: {amount}, Receipt: {receipt_number}"
            updated_payment_history = payment_history + "\n" + f"{payment_date.strftime('%Y-%m-%d')}: {new_payment}" if payment_history else f"{payment_date.strftime('%Y-%m-%d')}: {new_payment}"

            # Update the DataFrame
            df.loc[df['Admission number'] == selected_admission_number, 
                   ['Paid Amount', 'Remaining Balance', 'Payment History', 'Receipt Number', 'Payment Date']] = [
                paid_amount + amount, remaining_balance, updated_payment_history, receipt_number, payment_date.strftime('%Y-%m-%d')
            ]
            
            # Update Google Sheets
            row_index = df[df['Admission number'] == selected_admission_number].index[0] + 2
            sheet.update(f"F{row_index}", [[int(paid_amount + amount)]])
            sheet.update(f"G{row_index}", [[int(remaining_balance)]])
            sheet.update(f"H{row_index}", [[payment_type_detail]])
            sheet.update(f"I{row_index}", [[updated_payment_history]])
            sheet.update(f"J{row_index}", [[receipt_number]])
            sheet.update(f"K{row_index}", [[payment_date.strftime('%Y-%m-%d')]])

            st.success(f"Payment added successfully! Remaining balance: {remaining_balance}")

            # Display Receipt
            st.markdown(f"""
                <div style="text-align: center; font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;">
                    <img src='https://example.com/logo.png' style='width: 100px; height: 100px;' alt='School Logo'/>
                    <h1 style="color: #4CAF50;">Quest International School</h1>
                    <h3 style="color: #555;">Om Nagar, Maruthi Nagar, Langar Houz, Hyderabad, Telangana 500008</h3>
                    <hr style="border: 1px solid #ddd; margin: 20px 0;">
                    <h2 style="color: #333;">Payment Receipt</h2>
                    <table style="width: 100%; max-width: 600px; margin: 0 auto; border-collapse: collapse; font-size: 16px;">
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Admission Number:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{selected_admission_number}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Student Name:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{student_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Class:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{student_row['Class']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Parent Mobile Number:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{student_row['Parent Mobile Number']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Date:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{payment_date.strftime('%Y-%m-%d')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Amount Paid:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{amount}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Remaining Balance:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{remaining_balance}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Receipt Number:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{receipt_number}</td>
                        </tr>
                    </table>
                    <hr style="border: 1px solid #ddd; margin: 20px 0;">
                    <p style="font-size: 14px; color: #777;">Thank you for your payment!</p>
                </div>
            """, unsafe_allow_html=True)
