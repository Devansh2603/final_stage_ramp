import streamlit as st
import requests

# Garage details for dropdown selection with manual ID mapping
garageDBDetails = [
    {"id": 1, "name": "11motors_data", "dbURL": "", "user_ids": [2, 4]},
    {"id": 3, "name": "flag_data", "dbURL": "", "user_ids": [1, 3]}
]

# FastAPI backend endpoint
API_URL = "http://127.0.0.1:8000/ask_question"

# Streamlit UI
def main():
    st.set_page_config(page_title="RAMP GPT", layout="centered")
    st.title("🔍 RAMP GPT")
    st.subheader("Enter your question below to get instant answers!")

    garage_names = [garage["name"] for garage in garageDBDetails]
    selected_garage = st.selectbox("🏠 Select a Garage", garage_names, index=None, placeholder="No options to select.")

    # Manually assign garage ID based on selection
    selected_garage_id = next((garage["id"] for garage in garageDBDetails if garage["name"] == selected_garage), None)

    if selected_garage:
        # ✅ Send selected garage + ID to backend
        response = requests.post("http://localhost:8000/set_garage/", json={
            "garage_name": selected_garage,
            "garage_id": selected_garage_id  # Added garage ID here
        })

        if response.status_code == 200:
            st.success(f"Garage set to {selected_garage}")
        else:
            st.error("Failed to set garage")

        # ✅ Fetch the selected garage for confirmation
        db_response = requests.get("http://localhost:8000/get_garage/")
        if db_response.status_code == 200:
            st.write(f"🔍 Connected to Garage: {db_response.json().get('garage_name', 'Unknown')}")
        else:
            st.error("Failed to fetch selected garage")

    # User input for query
    user_query = st.text_area("💬 Ask a question:")
    user_role = st.selectbox("👤 Select your role", ["admin", "owner", "customer"]).lower()
    user_id = st.text_input("🔢 Enter your User ID")

    if st.button("🚀 Submit Query"):
        if not user_query or not user_id:
            st.error("❌ Please enter a valid question and User ID.")
            return
        
        if not selected_garage:
            st.error("❌ Please select a garage before submitting.")
            return

        # ✅ Add selected_garage and selected_garage_id in the payload
        payload = {
            "question": user_query,
            "role": user_role,
            "user_id": user_id,
            "selected_garage": selected_garage,
            "selected_garage_id": selected_garage_id
            
        }

        # Send request to FastAPI backend
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                st.success("✅ Query executed successfully!")
                st.write("### 📝 SQL Query:")
                st.code(data.get("query_result", {}).get("raw_answer", "N/A"), language="sql")
                st.write("### 🤖 AI Response:")
                st.write(data.get("query_result", {}).get("human_readable", "No response generated."))
                st.write(f"⏱ Execution Time: {data.get('execution_time', 'N/A')} sec")
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Server Error: {str(e)}")

if __name__ == "__main__":
    main()
