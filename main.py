from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sql_agent import SessionLocal
from workflow_engine import workflow
import logging
from models import CustomerVehicleInfo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends

import time  # ✅ Import time module

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True  # ✅ Ensures logs are displayed in the terminal
)


app = FastAPI()

# ✅ Garage Mapping for Manual Garage ID Handling
GARAGE_DETAILS = {
    1: "11motors_data",
    3: "flag_data"
}

# ✅ Request & Response Models
class QueryRequest(BaseModel):
    question: str
    role: str
    user_id: str
    selected_garage: str
    selected_garage_id: int  # ✅ Added selected_garage_id

class QueryResponse(BaseModel):
    query_result: dict
    sql_error: bool
    execution_time: float  # ✅ Include execution time

# ✅ Get All Garage IDs for Owners
def get_user_vehicles(session, user_id):
    return [v.customer_id for v in session.query(CustomerVehicleInfo.customer_id).filter(CustomerVehicleInfo.customer_id == user_id).all()]

selected_garage = None
selected_garage_id = None  # ✅ Added global garage ID

class GarageSelection(BaseModel):
    garage_name: str
    garage_id: int  # ✅ Added garage ID
    
@app.get("/")
def read_root():
    return {"message": "API is running successfully!"}


@app.post("/set_garage/")
def set_garage(garage: GarageSelection):
    """Set the selected garage name dynamically."""
    global selected_garage, selected_garage_id
    selected_garage = garage.garage_name
    selected_garage_id = garage.garage_id  # ✅ Store garage ID globally
    logging.debug(f"✅ Garage set successfully: {selected_garage} with ID {selected_garage_id}")
    
    return {"message": f"Garage set to {selected_garage} with ID {selected_garage_id}"}
    

@app.get("/get_garage/")
def get_garage():
    """Get the currently selected garage."""
    if not selected_garage:
        logging.error("❌ No garage selected yet.")
        raise HTTPException(status_code=400, detail="No garage selected yet.")
    logging.debug(f"✅ Retrieved Garage Info: {selected_garage} with ID {selected_garage_id}")
    return {"selected_garage": selected_garage, "garage_id": selected_garage_id}  # ✅ Return garage ID too

def get_database_url():
    if not selected_garage or not selected_garage_id:
        raise HTTPException(status_code=400, detail="No garage selected")

    if selected_garage_id not in GARAGE_DETAILS:
        raise HTTPException(status_code=403, detail="Invalid garage ID")

    return f"mysql+pymysql://root:devanshjoshi@localhost/{GARAGE_DETAILS[selected_garage_id]}"

def get_session():
    """Returns a database session based on the selected garage."""
    
    database_url = get_database_url()
    logging.debug(f"✅ Database URL: {database_url}")
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_db():
    """FastAPI dependency to provide a database session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()

@app.post("/ask_question", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    """Process user query with role-based access control."""
    logging.debug(f"📥 Incoming request: {request}")
    start_time = time.time()  # ✅ Start Timer

    user_role = request.role.lower()  # ✅ Ensure role comparison is case-insensitive
    user_id = request.user_id

    # ✅ Verify selected garage ID
    if request.selected_garage_id not in GARAGE_DETAILS:
        raise HTTPException(status_code=400, detail="Invalid garage ID provided.")

    try:
        # ✅ Get Garage IDs for the user (Owners only)
        garage_ids = get_user_vehicles(db, user_id) if user_role == "owner" else []
        garage_condition = f"cv.customer_id IN ({', '.join(map(str, garage_ids))})" if garage_ids else ""

        # ✅ Initial Query State
        state = {
            "question": request.question,
            "sql_query": "",
            "query_result": {"raw_answer": "No data", "human_readable": "No response generated."},
            "sql_error": False,
            "garage_ids": garage_ids  # ✅ Always pass a list
        }
        config = {"configurable": {"session": db, "role": user_role}}  # ✅ Pass role to workflow

        logging.debug(f"Received query: {request.question} from user {request.user_id} with role {request.role}")

        # ✅ Compile and invoke workflow
        try:
               app_workflow = workflow.compile()
               result = app_workflow.invoke(input=state, config=config)
               logging.debug(f"✅ Final Result: {result}")
        except Exception as e:
            logging.error(f"❌ Workflow Execution Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Workflow execution failed")


        execution_time = round(time.time() - start_time, 3)

        return QueryResponse(
            query_result=result.get("query_result", {}),
            sql_error=result["sql_error"],
            execution_time=execution_time  # ✅ Include execution time in response
        )

    except Exception as e:
        logging.error(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
    

