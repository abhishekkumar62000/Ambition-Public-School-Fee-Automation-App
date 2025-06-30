 import logging 
logging.basicConfig(level=logging.DEBUG)

import streamlit as st
import pandas as pd 
import yagmail # type: ignore
import plotly.express as px
from datetime import datetime 
import io 
import requests 
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os
import seaborn as sns
import matplotlib.pyplot as plt

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fee Warning Automation",
    layout="centered",
    page_icon=":school:"
)

# Enhanced Custom CSS for a more interactive and modern UI
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(120deg, #e3f0ff 0%, #f9f9f9 100%);
    }
    .main {
        background-color: #ffffffee;
        border-radius: 22px;
        box-shadow: 0 6px 32px rgba(44, 62, 80, 0.13);
        padding: 2.7rem 2.2rem 2.2rem 2.2rem;
        margin-top: 1.7rem;
        animation: fadeIn 1.2s;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2E86C1 60%, #117A65 100%);
        color: white;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.13em;
        padding: 0.7em 2.2em;
        border: none;
        transition: 0.2s;
        box-shadow: 0 2px 8px #2e86c13a;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #117A65 60%, #2E86C1 100%);
        color: #fff;
        transform: scale(1.06);
        box-shadow: 0 4px 16px #117a653a;
    }
    .stFileUploader {
        background: #eaf6fb;
        border-radius: 12px;
        padding: 1.2em;
        border: 2.5px dashed #2E86C1;
        margin-bottom: 1em;
    }
    .stAlert {
        border-radius: 12px;
    }
    .stDataFrame, .stTable {
        background: #f8fbff;
        border-radius: 10px;
        box-shadow: 0 2px 8px #2e86c11a;
    }
    .stMetric {
        background: #eaf6fb;
        border-radius: 12px;
        padding: 0.7em 0.5em;
        margin: 0.3em;
        box-shadow: 0 2px 8px #2e86c11a;
    }
    .stExpanderHeader {
        font-size: 1.1em;
        color: #2E86C1;
        font-weight: bold;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(30px);}
        to { opacity: 1; transform: translateY(0);}
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Animated, interactive header with subtle hover and animation
st.markdown(
    """
    <div class="main">
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: -10px;">
            <img src="https://img.icons8.com/color/96/000000/school-building.png" width="60" style="margin-right: 18px; animation: bounce 1.5s infinite alternate;">
            <div>
                <h1 style="margin-bottom: 0; color: #2E86C1; font-family: 'Segoe UI', sans-serif; letter-spacing: 1px;">
                    Ambition Public School
                </h1>
                <span style="font-size: 1.2em; color: #117A65; font-weight: bold;">
                    📧 Fee Warning & AI Automation Dashboard
                </span>
            </div>
            <img src="https://img.icons8.com/color/96/000000/artificial-intelligence.png" width="60" style="margin-left: 18px; animation: pulse 2s infinite;">
        </div>
        <hr style="margin-top: 10px; margin-bottom: 0;">
    </div>
    <style>
    @keyframes bounce {
        0% { transform: translateY(0);}
        100% { transform: translateY(-10px);}
    }
    @keyframes pulse {
        0% { filter: brightness(1);}
        50% { filter: brightness(1.3);}
        100% { filter: brightness(1);}
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Interactive info box with icon and animation
st.info(
    "✨ **Upload the student fee data Excel file and send smart, personalized reminders to parents.**<br>"
    "💡 _Tip: You can preview the data, filter, and customize your message before sending!_",
    icon="ℹ️"
)

# Path to QR code image
QR_IMAGE_PATH = os.path.join(os.getcwd(), "QR Pay.png")

# ---------- STEP 1: Upload Excel ----------
uploaded_file = st.file_uploader("📂 **Upload Excel File**", type=["xlsx"])
if uploaded_file:
    with st.spinner("Processing your data..."):
        df = pd.read_excel(uploaded_file)
        st.success("File uploaded and data loaded successfully!")

    df.columns = df.columns.str.strip()
    st.write("Columns found:", list(df.columns))

    # Accept both possible column names
    dues_col = None
    if "Total Payment Dues" in df.columns:
        dues_col = "Total Payment Dues"
    elif "Total Payment Dues (₹)" in df.columns:
        dues_col = "Total Payment Dues (₹)"

    if "Email" not in df.columns or dues_col is None:
        st.error("Excel must contain 'Email' and 'Total Payment Dues' columns.")
    else:
        # Generate personalized payment links (dummy example)
        PAYMENT_BASE_URL = "https://pay.ambitionschool.com/pay?student_id="
        if "Student ID" in df.columns:
            df["Payment Link"] = df["Student ID"].apply(lambda sid: f"{PAYMENT_BASE_URL}{sid}")
        else:
            df["Payment Link"] = df["Student Name"].apply(lambda name: f"{PAYMENT_BASE_URL}{name.replace(' ', '').lower()}")

        # Optionally, generate QR codes for each payment link (requires qrcode library)
        import qrcode
        import base64

        def generate_qr_code_base64(link):
            qr = qrcode.make(link)
            buf = io.BytesIO()
            qr.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            base64_img = base64.b64encode(img_bytes).decode()
            return f"data:image/png;base64,{base64_img}"

        df["Payment QR"] = df["Payment Link"].apply(generate_qr_code_base64)

        # ---------- 3. 🔍 Smart Filters & Search ----------
        st.header("🔍 Smart Filters & Search")

        filtered_df = df.copy()

        # Filter by Class
        if "Class" in df.columns:
            class_options = sorted(df["Class"].dropna().unique())
            selected_classes = st.multiselect("Filter by Class", class_options, default=class_options)
            filtered_df = filtered_df[filtered_df["Class"].isin(selected_classes)]

        # Filter by Due Amount Range
        min_due = int(df[dues_col].min())
        max_due = int(df[dues_col].max())
        due_range = st.slider("Filter by Due Amount Range (₹)", min_due, max_due, (min_due, max_due))
        filtered_df = filtered_df[(filtered_df[dues_col] >= due_range[0]) & (filtered_df[dues_col] <= due_range[1])]

        # Filter by City/Address
        city_col = None
        for col in ["City", "Address"]:
            if col in df.columns:
                city_col = col
                break
        city_query = st.text_input(f"Search by {city_col if city_col else 'City/Address'} (optional)").strip()
        if city_col and city_query:
            filtered_df = filtered_df[filtered_df[city_col].str.contains(city_query, case=False, na=False)]

        # Only show students with dues > 0
        due_df = filtered_df[filtered_df[dues_col] > 0].copy()

        # ---------- 1. 📊 Class-wise Fee Summary Dashboard ----------
        st.header("📊 Class-wise Fee Summary Dashboard")

        # Bar chart: Class vs Total Pending Fees
        if "Class" in filtered_df.columns:
            class_dues = filtered_df.groupby("Class")[dues_col].sum().reset_index()
            fig_class_dues = px.bar(
                class_dues,
                x="Class",
                y=dues_col,
                title="Class vs Total Pending Fees",
                labels={dues_col: "Total Pending Fees (₹)"}
            )
            st.plotly_chart(fig_class_dues, use_container_width=True)

            # Find worst performing class (max dues)
            worst_class_row = class_dues.loc[class_dues[dues_col].idxmax()]
            st.info(f"🔴 **Worst Performing Class:** {worst_class_row['Class']} (₹{worst_class_row[dues_col]:,.0f} pending)")

            # Pie chart: Class-wise distribution of defaulters
            defaulters_per_class = due_df.groupby("Class")["Student Name"].count().reset_index()
            defaulters_per_class = defaulters_per_class.rename(columns={"Student Name": "Defaulter Count"})
            fig_defaulters_pie = px.pie(
                defaulters_per_class,
                names="Class",
                values="Defaulter Count",
                title="Class-wise Distribution of Defaulters"
            )
            st.plotly_chart(fig_defaulters_pie, use_container_width=True)

        # ---------- 3. 🛠️ Edit Dues Manually Inside the App (Excel-Free Mode) ----------
        st.header("🛠️ Edit Dues Manually (Excel-Free Mode)")

        # Show editable table for all students (filtered_df)
        if "Student Name" in filtered_df.columns and dues_col:
            st.markdown("You can edit the dues directly below. Changes are saved in real time (session only).")
            edited_df = st.data_editor(
                filtered_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    dues_col: st.column_config.NumberColumn(
                        "Total Payment Dues",
                        min_value=0,
                        step=1,
                        format="₹{:.0f}"
                    )
                },
                key="editable_dues"
            )
            # Update the filtered_df and due_df with the edited values
            filtered_df = edited_df
            due_df = filtered_df[filtered_df[dues_col] > 0].copy()
        else:
            st.warning("Cannot enable editing: 'Student Name' or dues column missing.")

        # ---------- 1. 📊 Real-Time Dashboard Analytics ----------
        st.header("📊 Real-Time Dashboard Analytics")

        col1, col2, col3 = st.columns(3)
        col1.metric("🔢 Total Students", len(filtered_df))
        col2.metric("💰 Total Fee Pending (₹)", f"₹{filtered_df[dues_col].sum():,.0f}")
        col3.metric("🧑‍🎓 Number of Defaulters", len(due_df))

        # 📚 Class-wise Dues (Bar Chart)
        if "Class" in filtered_df.columns:
            class_dues = filtered_df.groupby("Class")[dues_col].sum().reset_index()
            fig_class = px.bar(class_dues, x="Class", y=dues_col, title="Class-wise Dues (₹)", labels={dues_col: "Total Dues (₹)"})
            st.plotly_chart(fig_class, use_container_width=True)

        # 📍 City-wise Dues (Pie Chart)
        if "City" in filtered_df.columns:
            city_dues = filtered_df.groupby("City")[dues_col].sum().reset_index()
            fig_city = px.pie(city_dues, names="City", values=dues_col, title="City-wise Dues (₹)")
            st.plotly_chart(fig_city, use_container_width=True)

        st.success(f"{len(due_df)} students have pending dues.")
        st.dataframe(due_df)

        # --- Student Profile Drilldown ---
        st.subheader("🧑‍🎓 Student Profile Drilldown")
        student_names = due_df["Student Name"].unique()
        selected_student = st.selectbox("Select a student to view profile", student_names)
        if selected_student:
            profile = due_df[due_df["Student Name"] == selected_student].iloc[0]
            st.markdown(f"### Profile: {profile['Student Name']}")
            st.write(f"**Class:** {profile['Class']}")
            st.write(f"**Parent Email:** {profile['Email']}")
            if 'Phone' in profile:
                st.write(f"**Parent Phone:** {profile['Phone']}")
            st.write(f"**Total Payment Dues:** ₹{profile[dues_col]:,.0f}")
            if "Past Delay Count" in profile:
                st.write(f"**Past Delay Count:** {profile['Past Delay Count']}")
            if "Payment Link" in profile:
                st.markdown(f"**Payment Link:** [Pay Now]({profile['Payment Link']})")
            if "Payment QR" in profile:
                st.markdown("**Scan to Pay:**")
                st.image(profile["Payment QR"])
            # Payment history & dues trend (if you have monthly columns)
            payment_cols = [col for col in due_df.columns if "Month" in col or "Paid" in col]
            if payment_cols:
                st.write("**Payment History:**")
                st.write(profile[payment_cols])
                st.line_chart(profile[payment_cols])
            # Communication log (from email_log)
            if "email_log" in st.session_state:
                comm_log = pd.DataFrame(st.session_state.email_log)
                if "Student Name" in comm_log.columns:
                    comm_log = comm_log[comm_log["Student Name"] == selected_student]
                    if not comm_log.empty:
                        st.write("**Communication Log:**")
                        st.dataframe(comm_log)
                    else:
                        st.info("No communication log found for this student.")
                else:
                    st.info("No communication log found for this student.")

        # ---------- STEP 2: Email Credentials ----------
        st.header("🔐 Email Configuration")
        sender_email = st.text_input("Enter your Gmail address", value="ambitionschool.notice@gmail.com", help="Use a Gmail address with App Password enabled.")
        sender_password = st.text_input("Enter your Gmail app password", type="password", help="Generate an App Password from your Google Account Security settings.")

        # ---------- 5. 📧 Dynamic Email Personalization with Templates ----------
        st.header("📧 Email Template Selection & Preview")

        # Define templates
        def get_email_templates():
            return {
                "Standard Reminder": (
                    "Urgent: Fee Due Reminder for {student_name}",
                    """Dear Parent/Guardian,

This is a reminder that the school fee for your child, **{student_name}**, studying in Class **{student_class}**, is still unpaid.

🧾 **Outstanding Amount**: ₹{due_amount}

Please clear the dues at the earliest to avoid a **daily penalty**. Timely payment ensures your child continues to receive academic support.

If you've already paid, kindly ignore this message.

Warm regards,  
**Ambition Public School**
"""
                ),
                "Junior Student Friendly": (
                    "Fee Reminder for {student_name} (Junior Section)",
                    """Dear Parent,

We hope your little one, **{student_name}** (Class **{student_class}**), is enjoying their learning journey with us!

Our records show a pending fee of **₹{due_amount}**. Kindly clear the dues soon to ensure uninterrupted participation in school activities.

Thank you for your prompt attention.

Best wishes,  
**Ambition Public School**
"""
                ),
                "Senior Section Strict": (
                    "Final Notice: Fee Due for {student_name} (Senior Section)",
                    """Dear Parent/Guardian,

This is a final reminder regarding the outstanding fee for **{student_name}** (Class **{student_class}**).

🧾 **Amount Due**: ₹{due_amount}

Immediate payment is required to avoid further action. Please disregard this notice if payment has already been made.

Sincerely,  
**Ambition Public School**
"""
                ),
            }

        templates = get_email_templates()
        template_names = list(templates.keys())
        selected_template = st.selectbox("Choose Email Template", template_names)

        # Optionally, auto-select template based on class (junior/senior)
        junior_classes = ["Nursery", "KG", "Prep", "1", "2", "3", "4", "5"]
        senior_classes = ["9", "10", "11", "12"]

        # Preview for the first student in due_df
        preview_row = None
        if not due_df.empty:
            preview_row = due_df.iloc[0]
            # Auto-select template if enabled
            if str(preview_row["Class"]) in junior_classes:
                auto_template = "Junior Student Friendly"
            elif str(preview_row["Class"]) in senior_classes:
                auto_template = "Senior Section Strict"
            else:
                auto_template = "Standard Reminder"
            # If admin wants auto, uncomment below:
            # selected_template = auto_template

            subject_template, body_template = templates[selected_template]
            preview_subject = subject_template.format(
                student_name=preview_row["Student Name"],
                student_class=preview_row["Class"],
                due_amount=preview_row[dues_col]
            )
            preview_body = body_template.format(
                student_name=preview_row["Student Name"],
                student_class=preview_row["Class"],
                due_amount=preview_row[dues_col]
            )
            st.subheader("📄 Email Preview")
            st.markdown(f"**Subject:** {preview_subject}")
            st.markdown(preview_body)

        # ---------- 2. 📥 Sent Email Log with Download Option ----------
        if "email_log" not in st.session_state:
            st.session_state.email_log = []

        # ---------- 4. 📱 SMS Alert System Integration ----------
        st.header("📱 SMS Alert System (Fast2SMS)")

        send_sms = st.checkbox("Also send SMS alerts to parents' mobile numbers (India only)")
        sms_message_template = st.text_area(
            "SMS Message Template (use {student_name}, {student_class}, {due_amount})",
            value="Dear Parent, Fee due for {student_name} (Class {student_class}): ₹{due_amount}. Please pay soon. - Ambition School"
        )

        # Optionally, let user select the phone column
        phone_col = None
        for col in ["Phone", "Mobile", "Parent Phone", "Parent Mobile"]:
            if col in df.columns:
                phone_col = col
                break
        if send_sms and not phone_col:
            st.warning("No phone number column found in your Excel. Please ensure a column named 'Phone', 'Mobile', 'Parent Phone', or 'Parent Mobile' exists.")

        # Add your Fast2SMS API key here (for demo, use env variable or config in production)
        FAST2SMS_API_KEY = "RF2uxDjgks3PndJLweQTA4chSoEZCiazGN0tmblHfWyM6V8BOUA9wu6baJPNUvjLc4BXy5KS8de1ihxl"

        def send_sms_via_fast2sms(phone, message):
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {
                "authorization": FAST2SMS_API_KEY
            }
            payload = {
                "route": "q",
                "message": message,
                "language": "english",
                "flash": 0,
                "numbers": phone
            }
            try:
                response = requests.post(url, headers=headers, data=payload)
                # Debug: print response for troubleshooting
                print("Fast2SMS response:", response.status_code, response.text)
                if response.status_code == 200 and response.json().get("return"):
                    return "Success", ""
                else:
                    return "Failed", response.text
            except Exception as e:
                return "Failed", str(e)

        if st.button("🚀 Send Warning Emails"):
            if not sender_email or not sender_password:
                st.error("Please enter your email and password.")
            else:
                try:
                    yag = yagmail.SMTP(user=sender_email, password=sender_password)
                    with st.spinner("Sending emails and SMS..."):
                        success_count = 0
                        sms_success_count = 0
                        email_log = []
                        for _, row in due_df.iterrows():
                            # Auto-select template based on class
                            if str(row["Class"]) in junior_classes:
                                template_key = "Junior Student Friendly"
                            elif str(row["Class"]) in senior_classes:
                                template_key = "Senior Section Strict"
                            else:
                                template_key = selected_template
                            subject_template, body_template = templates[template_key]
                            subject = subject_template.format(
                                student_name=row["Student Name"],
                                student_class=row["Class"],
                                due_amount=row[dues_col]
                            )
                            payment_link = row.get("Payment Link", "")
                            body = body_template.format(
                                student_name=row["Student Name"],
                                student_class=row["Class"],
                                due_amount=row[dues_col]
                            )
                            if payment_link:
                                body += f"\n\n[Click here to pay now]({payment_link})"
                            status = "Success"
                            error_msg = ""
                            sms_status = ""
                            sms_error = ""
                            try:
                                yag.send(
                                    to=row["Email"],
                                    subject=subject,
                                    contents=[body, QR_IMAGE_PATH]  # Optionally, add QR code image here
                                )
                                success_count += 1
                            except Exception as e:
                                status = "Failed"
                                error_msg = str(e)
                                st.error(f"Failed to send email to {row['Email']} – {e}")

                            # Send SMS if enabled and phone column exists
                            if send_sms and phone_col and pd.notna(row[phone_col]):
                                # Clean phone number: remove spaces, +, -, country code, etc.
                                phone_str = str(row[phone_col])
                                phone_digits = ''.join(filter(str.isdigit, phone_str))
                                # Remove country code if present (assume Indian numbers)
                                if phone_digits.startswith('91') and len(phone_digits) > 10:
                                    phone_digits = phone_digits[-10:]
                                # Now check if it's a valid 10-digit number
                                if len(phone_digits) == 10:
                                    sms_message = sms_message_template.format(
                                        student_name=row["Student Name"],
                                        student_class=row["Class"],
                                        due_amount=row[dues_col]
                                    )
                                    sms_status, sms_error = send_sms_via_fast2sms(phone_digits, sms_message)
                                    if sms_status == "Success":
                                        sms_success_count += 1
                                    else:
                                        st.error(f"Failed to send SMS to {phone_digits} – {sms_error}")
                                else:
                                    st.error(f"Invalid phone number format: {row[phone_col]}")

                            email_log.append({
                                "Date-Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Status": status,
                                "Student Name": row["Student Name"],
                                "Parent Email": row["Email"],
                                "Parent Phone": row[phone_col] if phone_col and pd.notna(row[phone_col]) else "",
                                "SMS Status": sms_status,
                                "SMS Error": sms_error,
                                "Error": error_msg
                            })
                        st.session_state.email_log = email_log
                    st.success(f"✅ Emails sent successfully to {success_count} parents.")
                    if send_sms and phone_col:
                        st.success(f"✅ SMS sent successfully to {sms_success_count} parents.")
                except Exception as e:
                    st.error(f"❌ Failed to connect to email server: {e}")

        # Show Email Log Table & Download Option
        if st.session_state.get("email_log"):
            st.header("📥 Sent Email/SMS Log")
            log_df = pd.DataFrame(st.session_state.email_log)
            display_cols = ["Date-Time", "Status", "Student Name", "Parent Email"]
            if "Parent Phone" in log_df.columns:
                display_cols.append("Parent Phone")
            st.dataframe(log_df[display_cols])

            # Download option
            csv = log_df.to_csv(index=False)
            st.download_button(
                "📥 Download Log as CSV",
                csv,
                "email_sms_log.csv",
                "text/csv",
                key="download-csv"
            )

        # ---------- Predictive Analytics: Advanced Fee Defaulter Predictor ----------
        st.header("🤖 Predictive Analytics: Fee Defaulter Risk (Advanced)")

        required_ai_cols = ["Past Delay Count", "Class", dues_col]
        ai_ready = all(col in df.columns for col in required_ai_cols)
        if not ai_ready:
            st.warning("To use the predictor, your Excel must have columns: Past Delay Count, Class, and Total Payment Dues.")
        else:
            # Prepare features
            ai_df = df.copy()
            # Encode class as number
            le = LabelEncoder()
            ai_df["Class_encoded"] = le.fit_transform(ai_df["Class"].astype(str))
            # Feature engineering: you can add more features here
            features = ["Past Delay Count", "Class_encoded", dues_col]
            if "City" in ai_df.columns:
                le_city = LabelEncoder()
                ai_df["City_encoded"] = le_city.fit_transform(ai_df["City"].astype(str))
                features.append("City_encoded")
            X = ai_df[features]
            # If Defaulter column exists, use it; else, simulate
            if "Defaulter" in ai_df.columns:
                y = ai_df["Defaulter"]
            else:
                y = ((ai_df["Past Delay Count"] > 0) & (ai_df[dues_col] > 0)).astype(int)
            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            # Advanced ML model: RandomForest (can be replaced with XGBoost, etc.)
            clf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42)
            clf.fit(X_train, y_train)
            # Predict risk for all students
            ai_df["Defaulter_Risk_Score"] = clf.predict_proba(X)[:,1]
            ai_df["High_Risk"] = ai_df["Defaulter_Risk_Score"] > 0.5

            # --- Interactive Filtering/Sorting ---
            st.subheader("🎯 Filter & Sort by Defaulter Risk Score")
            min_risk, max_risk = float(ai_df["Defaulter_Risk_Score"].min()), float(ai_df["Defaulter_Risk_Score"].max())
            risk_range = st.slider("Select risk score range", 0.0, 1.0, (0.5, 1.0), step=0.01)
            filtered_risk_df = ai_df[(ai_df["Defaulter_Risk_Score"] >= risk_range[0]) & (ai_df["Defaulter_Risk_Score"] <= risk_range[1])]
            sort_by = st.selectbox("Sort by", ["Defaulter_Risk_Score", dues_col, "Past Delay Count"], index=0)
            filtered_risk_df = filtered_risk_df.sort_values(sort_by, ascending=False)

            st.write(f"Showing {len(filtered_risk_df)} students with risk score in selected range.")
            st.dataframe(filtered_risk_df[["Student Name", "Class", dues_col, "Past Delay Count", "Defaulter_Risk_Score", "High_Risk"]])

            # Show top 10 high-risk students
            st.subheader("🚨 Top 10 High-Risk Students Likely to Default Next Month")
            st.write("These students have a high predicted risk of fee delay next month. Consider calling their parents proactively.")
            st.dataframe(filtered_risk_df[["Student Name", "Class", dues_col, "Past Delay Count", "Defaulter_Risk_Score"]].head(10))

            # Recommendations
            if not filtered_risk_df.empty:
                st.info(f"Recommendation: Call the parents of these {min(10, len(filtered_risk_df))} students for early fee reminders.")

            # Visualize risk distribution
            st.subheader("📊 Risk Score Distribution")
            fig_risk = px.histogram(ai_df, x="Defaulter_Risk_Score", nbins=20, title="Distribution of Defaulter Risk Scores")
            st.plotly_chart(fig_risk, use_container_width=True)

        # ---------- EDA: Exploratory Data Analysis ----------
        st.header("📈 Exploratory Data Analysis (EDA)")

        if st.checkbox("Show Data Overview"):
            st.subheader("Data Overview")
            st.write(df.describe(include='all'))

        if st.checkbox("Show Missing Values"):
            st.subheader("Missing Values")
            st.write(df.isnull().sum())

        if st.checkbox("Show Sample Data"):
            st.subheader("Sample Data")
            st.write(df.head(10))

        # Interactive: Select column for distribution plot
        st.subheader("📊 Column Distribution")
        eda_col = st.selectbox("Select column to visualize distribution", df.select_dtypes(include=['number', 'object']).columns)
        if eda_col:
            if pd.api.types.is_numeric_dtype(df[eda_col]):
                st.bar_chart(df[eda_col].value_counts().sort_index())
            else:
                st.bar_chart(df[eda_col].value_counts())

        # Correlation heatmap for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1 and st.checkbox("Show Correlation Heatmap"):
            st.subheader("Correlation Heatmap")
            fig, ax = plt.subplots()
            sns.heatmap(df[numeric_cols].corr(), annot=True, cmap="Blues", ax=ax)
            st.pyplot(fig)

        # Pie chart for categorical columns
        cat_cols = df.select_dtypes(include=['object']).columns
        cat_col = st.selectbox("Select categorical column for pie chart", cat_cols)
        if cat_col:
            st.subheader(f"Pie Chart: {cat_col}")
            pie_data = df[cat_col].value_counts()
            fig_pie = px.pie(values=pie_data.values, names=pie_data.index, title=f"Distribution of {cat_col}")
            st.plotly_chart(fig_pie, use_container_width=True)

        # Scatter plot for two numeric columns
        if len(numeric_cols) >= 2:
            st.subheader("Scatter Plot")
            x_col = st.selectbox("X-axis", numeric_cols, key="scatter_x")
            y_col = st.selectbox("Y-axis", numeric_cols, key="scatter_y")
            if x_col and y_col:
                fig_scatter = px.scatter(df, x=x_col, y=y_col, color="Class" if "Class" in df.columns else None,
                                     title=f"{x_col} vs {y_col}")
                st.plotly_chart(fig_scatter, use_container_width=True)

        # ---------- Feature Engineering Example ----------
        st.header("🛠️ Feature Engineering")
        if st.button("Add Features"):
            df['Is_High_Due'] = df[dues_col] > df[dues_col].mean()
            st.write("Added 'Is_High_Due' column (True if dues above average).")
            st.write(df[['Student Name', dues_col, 'Is_High_Due']].head())

# Place this function ONCE, before use
def send_sms_via_fast2sms(phone, message):
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": FAST2SMS_API_KEY
    }
    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": phone
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        # Debug: print response for troubleshooting
        print("Fast2SMS response:", response.status_code, response.text)
        if response.status_code == 200 and response.json().get("return"):
            return "Success", ""
        else:
            return "Failed", response.text
    except Exception as e:
        return "Failed", str(e)


# ------------------- New Student Admission Data Collection -------------------
with st.expander("📝 New Student Admission Data Collection (Click to Expand/Collapse)", expanded=False):
    if "admission_list" not in st.session_state:
        st.session_state.admission_list = []

    with st.form("admission_form"):
        st.write("Fill the form below to register a new student for admission:")
        admission_student_name = st.text_input("Student Name")
        admission_father_name = st.text_input("Father's Name")
        admission_mother_name = st.text_input("Mother's Name")
        admission_address = st.text_area("Address")
        admission_class = st.text_input("Class")
        admission_parent_number = st.text_input("Parent's Mobile Number")
        admission_reg_fee = st.number_input("Registration Fee Payment (₹)", min_value=0, step=1)
        admission_submitted = st.form_submit_button("Submit Admission")
        if (
            admission_submitted
            and admission_student_name
            and admission_father_name
            and admission_mother_name
            and admission_address
            and admission_class
            and admission_parent_number
            and admission_reg_fee > 0
        ):
            st.session_state.admission_list.append({
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Student Name": admission_student_name,
                "Father's Name": admission_father_name,
                "Mother's Name": admission_mother_name,
                "Address": admission_address,
                "Class": admission_class,
                "Parent's Mobile Number": admission_parent_number,
                "Registration Fee Payment (₹)": admission_reg_fee
            })
            st.success("Admission data submitted successfully!")

    # Show admission dashboard (admin view)
    if st.session_state.admission_list:
        st.subheader("📋 New Admission Dashboard")
        admission_df = pd.DataFrame(st.session_state.admission_list)
        st.dataframe(admission_df)
        csv_admission = admission_df.to_csv(index=False)
        st.download_button(
            "Download Admission Data as CSV",
            csv_admission,
            "new_admissions.csv",
            "text/csv",
            key="download-admission-csv"
        )
        if __name__ == '__main__':
    main()  # or your main function name
