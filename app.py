import streamlit as st
import requests

# Garage details for dropdown selection with manual ID mapping
garageDBDetails = [{"id": 1, "name": "11motors_data", "dbURL": ""},
    {"id": 2, "name": "ezdrive_data", "dbURL": ""},
    {"id": 3, "name": "flag_data", "dbURL": ""},
    {"id": 4, "name": "admin_all", "dbURL": ""},
]

# FastAPI backend endpoint
API_URL = "http://127.0.0.1:8000/ask_question"

# Streamlit UI
def main():
    st.set_page_config(page_title="RAMP GPT", layout="centered")
    st.title("🔍 RAMP GPT")
    st.subheader("Enter your question below to get instant answers!")

    # Add a dropdown for selecting the role scope (admin_user, ezdrive_user, flag_user)
    scope = st.selectbox("👤 Select your Role Scope", ["admin_user", "ezdrive_user", "flag_user","11motors_user"])

    # Add a dropdown for selecting the user role (admin, owner, customer)
    user_role = st.selectbox("👤 Select your role", ["admin", "owner", "customer"]).lower()

    # Determine which garages (databases) should be available based on the selected role scope
    if scope == "admin_user":
        garage_names = ["admin_all", "11motors_data", "ezdrive_data", "flag_data"]  # Admin sees all
    elif scope == "ezdrive_user":
        garage_names = ["ezdrive_data"]  # Only ezdrive_data for ezdrive users
    elif scope == "flag_user":
        garage_names = ["flag_data"]  # Only flag_data for flag users
    elif scope == "11motors_user":
        garage_names = ["11motors_data"]  # Only 11motors_data for 11motors users

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
    user_id = st.text_input("🔢 Enter your User ID")

    if st.button("🚀 Submit Query"):
        if not user_query or not user_id:
            st.error("❌ Please enter a valid question and User ID.")
            return
        
        if not selected_garage:
            st.error("❌ Please select a garage before submitting.")
            return

        # ✅ Add selected_garage, selected_garage_id, user_role, and scope in the payload
        payload = {
            "question": user_query,
            "role": user_role,  # The original user role (admin, owner, customer)
            "scope": scope,  # New role scope (admin_user, ezdrive_user, flag_user)
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
