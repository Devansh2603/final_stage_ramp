from sqlalchemy import (
    Column, Integer, String, DECIMAL, ForeignKey, Text, Date, DateTime, Enum
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Customer Vehicle Info Table
class CustomerVehicleInfo(Base):
    __tablename__ = "customer_vehicle_info"

    customer_id = Column(Integer, primary_key=True)
    customer_name = Column(String(255), nullable=False)
    customer_mobile = Column(String(255), nullable=False)
    customer_vehicle_number = Column(String(255), unique=True, nullable=False)
    update_date = Column(DateTime, nullable=True)
    technician = Column(String(255), nullable=True)
    nbr_of_coupons = Column(Integer, nullable=True)
    vehicle_type = Column(String(255), nullable=False)
    location_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_address = Column(Text, nullable=True)
    emp_name = Column(String(255), nullable=True)
    chasis_no = Column(String(255), nullable=True)
    engine_no = Column(String(255), nullable=True)
    manufactured_year = Column(Integer, nullable=True)
    person_id = Column(Integer, nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    pincode = Column(Integer, nullable=True)

    # Relationships
    service_summaries = relationship("VehicleServiceSummary", back_populates="vehicle")


# Job Card Details Table
class JobCardDetails(Base):
    __tablename__ = "job_card_details"

    job_card_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer_vehicle_info.customer_id"), nullable=False)
    vehicle_svc_id = Column(Integer, nullable=False)
    problem_desc = Column(Text, nullable=True)
    complaint_status = Column(String(255), nullable=True)
    workshop_finding = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=True)


# Vehicle Service Details Table
class VehicleServiceDetails(Base):
    __tablename__ = "vehicle_service_details"

    vehicle_svc_details_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer_vehicle_info.customer_id"), nullable=False)
    vehicle_svc_id = Column(Integer, nullable=False)
    service_type_cd = Column(String(255), nullable=False)
    service_desc = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=True)
    service_date = Column(Date, nullable=True)
    discount_amount = Column(DECIMAL(10, 2), nullable=True)
    discount_type = Column(String(50), nullable=True)  # "%" or "Amount"
    amount_value = Column(DECIMAL(10, 2), nullable=True)

    # Relationships
    service_summary = relationship("VehicleServiceSummary", back_populates="service_details")


# Vehicle Service Summary Table
class VehicleServiceSummary(Base):
    __tablename__ = "vehicle_service_summary"

    vehicle_svc_summary_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer_vehicle_info.customer_id"), nullable=False)
    vehicle_svc_id = Column(Integer, ForeignKey("vehicle_service_details.vehicle_svc_details_id"), nullable=False)
    service_date = Column(Date, nullable=True)
    service_amt = Column(DECIMAL(10, 2), nullable=True)
    service_tax = Column(DECIMAL(10, 2), nullable=True)
    service_net_amt = Column(DECIMAL(10, 2), nullable=True)  # service_amt + service_tax
    parts_amt = Column(DECIMAL(10, 2), nullable=True)
    vat_tax = Column(DECIMAL(10, 2), nullable=True)
    parts_net_amt = Column(DECIMAL(10, 2), nullable=True)  # parts_amt + vat_tax
    salvage_amount = Column(DECIMAL(10, 2), nullable=True)
    salvage_tax_amt = Column(DECIMAL(10, 2), nullable=True)
    salvage_net_amt = Column(DECIMAL(10, 2), nullable=True)
    total_amt = Column(DECIMAL(10, 2), nullable=True)  # service_net_amt + parts_net_amt
    total_paid = Column(DECIMAL(10, 2), nullable=True)
    invoice_id = Column(Integer, nullable=True)
    invoice_create_date = Column(Date, nullable=True)
    discount_amount = Column(DECIMAL(10, 2), nullable=True)
    disc_type = Column(String(50), nullable=True)  # "%" or "Amount"
    service_status = Column(Enum("A", "R", "B", "D"), nullable=True)  # Arrived, Ready, Blocked, Done
    technician = Column(String(255), nullable=True)
    supervisor_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    kilometer_driven = Column(Integer, nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_mobile = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)

    # Relationships
    vehicle = relationship("CustomerVehicleInfo", back_populates="service_summaries")
    service_details = relationship("VehicleServiceDetails", back_populates="service_summary")