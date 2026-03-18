from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from .database import Base


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OTP(Base):
    __tablename__ = "otps"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Token(Base):
    __tablename__ = "tokens"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    mobile = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    camera = Column(Integer, default=0)
    sms = Column(Integer, default=0)
    storage = Column(Integer, default=0)
    location = Column(Integer, default=0)
    completed = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BureauScore(Base):
    __tablename__ = "bureau_scores"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=True, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    score = Column(Integer, nullable=False)
    approved = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    permission_id = Column(Integer, ForeignKey("kosam_uat.permissions.id"), nullable=True, index=True)
    full_name = Column(String, nullable=False)
    pan = Column(String, nullable=False, unique=True, index=True)
    date_of_birth = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    employment_type = Column(String, nullable=False)
    loan_purpose = Column(String, nullable=False)
    user_mobile = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Lender(Base):
    __tablename__ = "lenders"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    lender_name = Column(String, nullable=False)
    roi_min = Column(Integer, nullable=False)
    roi_max = Column(Integer, nullable=False)
    processing_fee_min = Column(Integer, nullable=False)
    processing_fee_max = Column(Integer, nullable=False)
    loan_amount_min = Column(Integer, nullable=False)
    loan_amount_max = Column(Integer, nullable=False)
    tenure_min = Column(Integer, nullable=False)
    tenure_max = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LenderAssignment(Base):
    __tablename__ = "lender_assignments"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    user_mobile = Column(String, nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=True, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    lender_id = Column(Integer, ForeignKey("kosam_uat.lenders.id"), nullable=True, index=True)
    name = Column(String, nullable=True)
    lender_name = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    website = Column(String, nullable=True)
    roi_min = Column(Float, nullable=True)
    roi_max = Column(Float, nullable=True)
    processing_fee_min = Column(Integer, nullable=True)
    processing_fee_max = Column(Integer, nullable=True)
    loan_amount_min = Column(Integer, nullable=True)
    loan_amount_max = Column(Integer, nullable=True)
    tenure_min = Column(Integer, nullable=True)
    tenure_max = Column(Integer, nullable=True)
    tenure_min_months = Column(Integer, nullable=True)
    tenure_max_months = Column(Integer, nullable=True)
    recommended = Column(Boolean, default=False)
    reason = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=False, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    address_type = Column(String, nullable=True)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Reference(Base):
    __tablename__ = "references"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=False, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=True)
    mobile = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EmploymentDetail(Base):
    __tablename__ = "employment_details"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=False, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    employer_name = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    monthly_income = Column(Float, nullable=True)
    employment_type = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    office_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Selfie(Base):
    __tablename__ = "selfies"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=False, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    selfie_url = Column(String, nullable=True)
    verified = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=False, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    account_type = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    account_number_masked = Column(String, nullable=True)
    upi_id = Column(String, nullable=True)
    status = Column(String, nullable=True, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Approval(Base):
    """Loan approval / loan offer table - approved loan terms for a customer."""
    __tablename__ = "approvals"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=False, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    lender_name = Column(String, nullable=True)
    loan_amount = Column(Integer, nullable=True)
    tenure_months = Column(Integer, nullable=True)
    roi_min = Column(Float, nullable=True)
    roi_max = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    processing_fee = Column(Integer, nullable=True)
    emi = Column(Float, nullable=True)
    status = Column(String, nullable=True, default="approved")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserJourneyStatus(Base):
    __tablename__ = "user_journey_status"
    __table_args__ = {"schema": "kosam_uat"}

    id = Column(Integer, primary_key=True, index=True)
    user_mobile = Column(String, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("kosam_uat.profiles.id"), nullable=True, index=True)
    current_step = Column(String, nullable=False)
    permissions_completed = Column(Integer, default=0)
    profile_completed = Column(Integer, default=0)
    bureau_completed = Column(Integer, default=0)
    lender_assignment_completed = Column(Integer, default=0)
    banking_completed = Column(Integer, default=0)
    loan_offer_completed = Column(Integer, default=0)
    loan_detail_completed = Column(Integer, default=0)
    kyc_completed = Column(Integer, default=0)
    selfie_completed = Column(Integer, default=0)
    address_completed = Column(Integer, default=0)
    reference_completed = Column(Integer, default=0)
    account_completed = Column(Integer, default=0)
    employment_completed = Column(Integer, default=0)
    emandate_completed = Column(Integer, default=0)
    e_sign_completed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
