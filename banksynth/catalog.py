"""Curated banking field catalog, not a statistical ranking or regulatory standard."""
from dataclasses import dataclass

# Field = generator specification. Ranges are illustrative test-data assumptions.
DEFINITIONS = {
"customers": """
customer_id=id
 display_name=name
 age=int:18:85
 annual_income=money:12000:500000
 credit_score=int:300:850
 segment=enum:Retail;Affluent;Private
 market=market
 currency=currency
 date_of_birth=birthdate
 email=email
 phone_number=phone
 nationality=country
 residence_country=country
 city=enum:Test Central;Test North;Test West
 postal_code=token:POST
 employment_status=enum:Employed;Self-employed;Retired;Student
 occupation=enum:Engineer;Teacher;Analyst;Nurse;Designer
 employer_name=company
 monthly_income=monthly_income
 customer_since=pastdate
 preferred_language=enum:English;Mandarin;Malay;Tamil
 marital_status=enum:Single;Married;Divorced
 dependants=int:0:5
 relationship_manager_id=token:RM
 risk_rating=enum:Low;Medium;High
""",
"accounts": """
account_id=id
 customer_id=fk:customers
 account_type=enum:Current;Savings
 currency=currency
 opened_at=pastdate
 opening_balance=money:100:100000
 closing_balance=money:100:100000
 account_status=enum:Active;Dormant;Restricted
 account_number=token:ACCOUNT
 product_code=enum:CUR-STD;SAV-PLUS;SAV-BASIC
 branch_id=fk:branches
 available_balance=available_balance
 hold_amount=money:0:100
 overdraft_limit=money:0:5000
 interest_rate=decimal:0:5
 accrued_interest=money:0:200
 monthly_fee=money:0:25
 statement_frequency=enum:Monthly;Quarterly
 statement_delivery=enum:Electronic;Paper
 last_activity_date=last_activity
 joint_account=bool
 account_purpose=enum:Daily spending;Savings;Salary
 minimum_balance=money:0:500
 debit_blocked=bool
 credit_blocked=bool
""",
"transactions": """
transaction_id=id
 account_id=fk:accounts
 timestamp=timestamp
 direction=enum:Debit;Credit
 amount=money:0.01:10000
 currency=currency
 category=enum:Groceries;Dining;Shopping;Transport;Utilities;Transfer
 channel=enum:Mobile;Card;Online;ATM;Branch
 balance_after=money:0:100000
 is_fraud=bool
 anomaly_reason=anomaly_reason
 transaction_status=enum:Posted
 merchant_name=company
 merchant_category_code=enum:5411;5812;5999;4111;4900
 merchant_country=country
 reference_number=token:REF
 description=enum:Synthetic retail payment;Synthetic transfer;Synthetic bill payment
 counterparty_name=name
 counterparty_account=token:COUNTERPARTY
 device_id=token:DEVICE
 ip_address=ip
 transaction_fee=money:0:15
 settlement_date=settlement_date
 value_date=value_date
 authentication_method=enum:Biometric;OTP;PIN;Password
""",
"loans": """
loan_id=id
 customer_id=fk:customers
 principal=money:1000:1000000
 currency=currency
 term_months=int:12:120
 apr_percent=decimal:3:24
 monthly_payment=money:10:50000
 status=enum:Performing;Default
 loan_type=enum:Personal;Auto;Education
 origination_date=pastdate
 maturity_date=loan_maturity
 outstanding_principal=outstanding
 amount_repaid=repaid
 collateral_type=enum:Unsecured;Vehicle;Deposit
 collateral_value=money:0:500000
 debt_to_income_ratio=decimal:0:1
 loan_to_value_ratio=decimal:0:1
 payment_frequency=enum:Monthly
 days_past_due=days_past_due
 next_payment_date=futuredate
 interest_type=enum:Fixed;Floating
 purpose=enum:Education;Vehicle purchase;Home improvement
 origination_fee=money:0:1000
 repayment_account_reference=token:REPAY
 application_reference=token:APPLICATION
""",
"cards": """
card_id=id
 account_id=fk:accounts
 card_reference=token:CARD
 cardholder_name=name
 card_type=enum:Debit;Credit;Prepaid
 network=enum:Visa;Mastercard;Amex
 card_status=enum:Active;Frozen;Expired
 issue_date=pastdate
 expiry_date=futuredate
 credit_limit=money:1000:50000
 current_balance=money:0:1000
 available_credit=available_credit
 minimum_payment=money:0:50
 payment_due_date=futuredate
 billing_cycle_day=int:1:28
 contactless_enabled=bool
 online_payments_enabled=bool
 international_enabled=bool
 cash_advance_limit=money:0:1000
 cash_advance_apr=decimal:10:35
 purchase_apr=decimal:5:30
 annual_fee=money:0:500
 reward_points=int:0:100000
 last_four_digits=lastfour
 replacement_count=int:0:4
""",
"payments": """
payment_id=id
 account_id=fk:accounts
 payment_reference=token:PAYMENT
 payment_type=enum:Domestic;International;Bill payment
 payment_rail=enum:FAST;ACH;RTGS;SWIFT
 amount=money:1:100000
 currency=currency
 payment_status=enum:Pending;Completed;Rejected
 initiated_at=timestamp
 execution_date=futuredate
 beneficiary_name=name
 beneficiary_account=token:BEN-ACCOUNT
 beneficiary_bank_name=company
 beneficiary_bank_code=token:BANK
 beneficiary_country=country
 purpose_code=enum:SALA;SUPP;OTHR
 remittance_information=enum:Synthetic invoice settlement;Synthetic salary;Synthetic transfer
 charge_bearer=enum:SHA;OUR;BEN
 fee_amount=money:0:50
 exchange_rate=decimal:0.5:2
 instructed_amount=instructed_amount
 priority=enum:Normal;Urgent
 recurring=bool
 recurrence_frequency=enum:None;Weekly;Monthly
 approval_status=enum:Pending;Approved;Declined
""",
"beneficiaries": """
beneficiary_id=id
 customer_id=fk:customers
 beneficiary_name=name
 nickname=enum:Test household;Test supplier;Test savings
 beneficiary_type=enum:Individual;Business
 account_reference=token:BEN-ACCOUNT
 bank_name=company
 bank_identifier=token:BANK-ID
 bank_country=country
 bank_city=enum:Test Central;Test North;Test West
 bank_address=address
 beneficiary_address=address
 beneficiary_country=country
 currency=currency
 created_date=pastdate
 verification_status=enum:Pending;Verified;Rejected
 verification_method=enum:Micro-deposit;Document;Bank confirmation
 trusted_beneficiary=bool
 transfer_limit=money:100:100000
 daily_limit=money:100:200000
 relationship=enum:Self;Family;Supplier;Other
 last_used_date=pastdate
 payment_count=int:0:1000
 favorite=bool
 enabled=bool
""",
"deposits": """
deposit_id=id
 account_id=fk:accounts
 deposit_type=enum:Term;Fixed;Notice
 principal=money:1000:1000000
 currency=currency
 interest_rate=decimal:0.1:6
 term_months=int:1:60
 start_date=pastdate
 maturity_date=deposit_maturity
 maturity_amount=deposit_maturity_amount
 interest_amount=deposit_interest
 interest_frequency=enum:At maturity
 day_count_basis=enum:30/360
 auto_renewal=bool
 renewal_instruction=enum:Principal only;Principal and interest;Do not renew
 funding_reference=token:FUNDING
 payout_reference=token:PAYOUT
 early_withdrawal_allowed=bool
 early_withdrawal_penalty_rate=decimal:0:2
 minimum_placement=money:100:1000
 deposit_status=enum:Active;Matured;Closed
 product_code=enum:TD-01;FD-06;FD-12
 campaign_code=token:CAMPAIGN
 accrued_interest=money:0:100
 withholding_tax_rate=decimal:0:30
""",
"investments": """
investment_id=id
 customer_id=fk:customers
 security_id=fk:securities
 portfolio_name=enum:Test growth;Test income;Test balanced
 asset_class=enum:Equity;Bond;Fund;Cash
 quantity=decimal:1:10000
 unit_cost=money:1:1000
 market_price=money:1:1000
 cost_basis=cost_basis
 market_value=market_value
 unrealized_gain=unrealized_gain
 currency=currency
 purchase_date=pastdate
 valuation_date=asof
 investment_objective=enum:Growth;Income;Preservation
 risk_profile=enum:Conservative;Balanced;Aggressive
 management_fee_rate=decimal:0:2
 custody_fee_rate=decimal:0:1
 dividend_income=money:0:10000
 coupon_income=money:0:10000
 investment_status=enum:Open;Closed
 advisor_reference=token:ADVISOR
 suitability_status=enum:Suitable;Review required
 reinvest_distributions=bool
 settlement_reference=token:SETTLEMENT
""",
"securities": """
security_id=id
 security_name=company
 instrument_reference=token:INSTRUMENT
 ticker=token:TICKER
 asset_class=enum:Equity;Bond;Fund;Cash
 exchange=enum:TEST-SGX;TEST-LSE;TEST-NYSE
 currency=currency
 issuer_name=company
 issuer_country=country
 industry_sector=enum:Financials;Technology;Healthcare;Industrials
 instrument_type=enum:Common stock;Government bond;ETF
 issue_date=pastdate
 maturity_date=futuredate
 coupon_rate=decimal:0:8
 coupon_frequency=enum:Annual;Semiannual;Quarterly;None
 face_value=money:100:1000
 price=money:1:1000
 price_date=asof
 lot_size=int:1:100
 credit_rating=enum:AAA;AA;A;BBB;BB;Unrated
 risk_level=enum:Low;Medium;High
 tradable=bool
 country_of_risk=country
 listing_status=enum:Listed;Suspended;Delisted
 settlement_cycle=enum:T+1;T+2
""",
"fx_trades": """
fx_trade_id=id
 account_id=fk:accounts
 trade_reference=token:FX
 trade_date=pastdate
 value_date=futuredate
 currency_pair=fx_pair
 buy_currency=currency
 sell_currency=other_currency
 buy_amount=money:100:100000
 sell_amount=fx_sell_amount
 exchange_rate=decimal:0.5:2
 spot_rate=decimal:0.5:2
 forward_points=decimal:-0.05:0.05
 trade_type=enum:Spot;Forward;Swap
 direction=enum:Buy;Sell
 trade_status=enum:Booked;Settled;Cancelled
 counterparty_name=company
 counterparty_reference=token:COUNTERPARTY
 dealer_reference=token:DEALER
 trading_channel=enum:Online;Voice;Branch
 settlement_instruction=token:SSI
 confirmation_reference=token:CONFIRM
 commission=money:0:100
 margin_percent=decimal:0:10
 purpose=enum:Hedging;Travel;Trade settlement
""",
"mortgages": """
mortgage_id=id
 customer_id=fk:customers
 property_reference=token:PROPERTY
 property_type=enum:Apartment;House;Condominium
 property_address=address
 property_value=money:200000:3000000
 principal=money:50000:200000
 outstanding_balance=outstanding
 currency=currency
 interest_rate=decimal:1:8
 rate_type=enum:Fixed;Floating;Hybrid
 term_months=int:120:360
 monthly_payment=mortgage_payment
 origination_date=pastdate
 maturity_date=loan_maturity
 loan_to_value_ratio=mortgage_ltv
 occupancy=enum:Owner occupied;Investment;Second home
 repayment_type=enum:Principal and interest
 valuation_date=asof
 insurance_required=bool
 escrow_balance=money:0:10000
 payment_day=int:1:28
 days_past_due=int:0:180
 mortgage_status=enum:Performing;Delinquent;Closed
 lien_position=int:1:2
""",
"businesses": """
business_id=id
 customer_id=fk:customers
 legal_name=company
 trading_name=company
 registration_reference=token:REG
 incorporation_date=pastdate
 incorporation_country=country
 legal_structure=enum:Limited company;Partnership;Sole proprietor
 industry_code=enum:TEST-RET;TEST-TEC;TEST-MFG
 industry_description=enum:Retail;Technology;Manufacturing
 annual_turnover=money:100000:10000000
 employee_count=int:1:5000
 business_size=enum:Micro;Small;Medium;Large
 registered_address=address
 operating_address=address
 contact_email=email
 contact_phone=phone
 website=website
 tax_reference=token:TAX
 ownership_type=enum:Private;Public;State owned
 beneficial_owner_count=int:1:10
 listing_status=enum:Listed;Unlisted
 financial_year_end=enum:12-31;03-31;06-30;09-30
 banking_relationship_years=int:0:30
 business_status=enum:Active;Inactive;Dissolved
""",
"trade_finance": """
trade_id=id
 business_id=fk:businesses
 instrument_type=enum:Letter of credit;Guarantee;Documentary collection
 instrument_reference=token:TRADE
 currency=currency
 face_amount=money:10000:1000000
 issue_date=pastdate
 expiry_date=futuredate
 applicant_name=company
 beneficiary_name=company
 issuing_bank=company
 advising_bank=company
 confirming_bank=company
 shipment_country=country
 destination_country=country
 goods_description=enum:Synthetic electronics;Synthetic textiles;Synthetic equipment
 incoterm=enum:FOB;CIF;DAP;EXW
 latest_shipment_date=futuredate
 tenor_days=int:30:180
 available_amount=trade_available
 utilized_amount=trade_utilized
 margin_percent=decimal:0:30
 commission_rate=decimal:0:3
 document_status=enum:Pending;Received;Discrepant;Accepted
 instrument_status=enum:Issued;Amended;Expired;Closed
""",
"kyc": """
kyc_id=id
 customer_id=fk:customers
 review_reference=token:KYC
 verification_status=enum:Pending;Verified;Needs review
 verification_date=pastdate
 next_review_date=futuredate
 document_type=enum:Test passport;Test national ID;Test permit
 document_reference=token:DOC
 document_issue_date=pastdate
 document_expiry_date=futuredate
 issuing_country=country
 address_verified=bool
 identity_verified=bool
 source_of_funds=enum:Salary;Business income;Savings;Inheritance
 source_of_wealth=enum:Employment;Business;Investment;Inheritance
 expected_monthly_volume=money:100:100000
 expected_transaction_count=int:1:500
 politically_exposed=bool
 sanctions_screening_result=enum:Clear;Potential match;Review required
 adverse_media_result=enum:Clear;Potential match
 risk_score=int:0:100
 risk_rating=enum:Low;Medium;High
 enhanced_due_diligence=bool
 reviewer_reference=token:REVIEWER
 onboarding_channel=enum:Branch;Mobile;Online;Partner
""",
"aml_alerts": """
alert_id=id
 transaction_id=fk:transactions
 alert_reference=token:AML
 created_at=timestamp
 rule_code=enum:TEST-HIGH-VALUE;TEST-VELOCITY;TEST-CROSS-BORDER
 rule_name=enum:Illustrative monitoring rule
 alert_type=enum:Transaction monitoring;Behavior review
 severity=enum:Low;Medium;High;Critical
 risk_score=int:0:100
 alert_status=enum:Open;In review;Closed;Escalated
 assigned_analyst=token:ANALYST
 case_reference=token:CASE
 detection_channel=enum:Batch;Real-time
 transaction_count=int:1:100
 aggregate_amount=money:1000:1000000
 currency=currency
 monitoring_window_days=int:1:90
 threshold_amount=money:1000:100000
 reason_code=enum:TEST-THRESHOLD;TEST-PATTERN;TEST-COUNTRY
 disposition=enum:Unresolved;False positive;Further review
 escalation_required=bool
 investigation_note=enum:Synthetic alert for workflow testing only
 model_version=enum:test-v1;test-v2
 review_due_date=futuredate
 is_test_alert=constant:true
""",
"digital_sessions": """
session_id=id
 customer_id=fk:customers
 login_at=timestamp
 logout_at=logout
 duration_seconds=int:10:7200
 channel=enum:Mobile;Web
 device_id=token:DEVICE
 device_type=enum:Phone;Tablet;Desktop
 operating_system=enum:Test iOS;Test Android;Test Windows;Test Linux
 browser=enum:Test Chrome;Test Safari;Test Firefox
 app_version=enum:1.0.0;1.1.0;2.0.0
 ip_address=ip
 country=country
 city=enum:Test Central;Test North;Test West
 authentication_method=enum:Password;Biometric;Passkey
 multi_factor_used=bool
 login_result=enum:Success;Failed;Locked
 failed_attempts=int:0:5
 pages_viewed=int:1:50
 actions_count=int:0:30
 payment_initiated=bool
 password_changed=bool
 new_device=bool
 session_risk_score=int:0:100
 connection_type=enum:WiFi;Mobile;Wired
""",
"branches": """
branch_id=id
 branch_code=token:BRANCH
 branch_name=company
 branch_type=enum:Retail;Corporate;Digital service center
 address=address
 city=enum:Test Central;Test North;Test West
 country=country
 postal_code=token:POST
 region=enum:North;South;East;West;Central
 phone=phone
 email=email
 opening_date=pastdate
 branch_status=enum:Open;Temporarily closed
 manager_reference=token:MANAGER
 staff_count=int:2:100
 atm_count=int:0:10
 counter_count=int:1:20
 accessible_entrance=bool
 weekend_service=bool
 cash_service=bool
 advisory_service=bool
 safe_deposit_service=bool
 opening_hour=enum:08:00;09:00;10:00
 closing_hour=enum:16:00;17:00;18:00
 timezone=enum:Asia/Singapore;Europe/London;America/New_York;Europe/Berlin
""",
"complaints": """
complaint_id=id
 customer_id=fk:customers
 case_reference=token:COMPLAINT
 received_date=pastdate
 channel=enum:Phone;Email;Branch;Online
 category=enum:Service;Fees;Payments;Access;Product
 subcategory=enum:Delay;Incorrect charge;Availability;Communication
 product_area=enum:Accounts;Cards;Loans;Payments
 subject=enum:Synthetic service case;Synthetic fee query;Synthetic access issue
 description=enum:Fictional complaint for case-management testing
 priority=enum:Low;Normal;High
 complaint_status=enum:Open;In progress;Resolved
 assigned_team=enum:Service;Operations;Product
 assigned_agent=token:AGENT
 response_due_date=futuredate
 resolution_code=enum:Pending;Explanation;Refund;Correction
 compensation_amount=money:0:1000
 currency=currency
 customer_satisfaction_score=int:1:5
 escalated=bool
 regulatory_referral=bool
 contact_preference=enum:Email;Phone;Letter
 follow_up_required=bool
 attachment_count=int:0:10
 response_time_hours=int:1:240
""",
"consents": """
consent_id=id
 customer_id=fk:customers
 consent_reference=token:CONSENT
 consent_type=enum:Marketing;Analytics;Open banking;Data sharing
 purpose=enum:Synthetic consent workflow testing
 consent_status=enum:Granted;Withdrawn;Expired
 captured_date=pastdate
 expiry_date=futuredate
 capture_channel=enum:Mobile;Web;Branch;Phone
 policy_version=enum:test-1.0;test-2.0
 policy_language=enum:English;Mandarin;Malay;Tamil
 email_marketing=bool
 sms_marketing=bool
 phone_marketing=bool
 push_notifications=bool
 third_party_sharing=bool
 profiling_allowed=bool
 analytics_allowed=bool
 data_scope=enum:Profile;Accounts;Transactions;All selected
 recipient_reference=token:RECIPIENT
 retention_days=int:30:730
 proof_reference=token:PROOF
 ip_address=ip
 device_reference=token:DEVICE
 renewal_required=bool
""",
}

LABELS = {"customers": "Customer profiles", "accounts": "Accounts & balances", "transactions": "Transactions", "loans": "Lending", "cards": "Cards", "payments": "Payments", "beneficiaries": "Beneficiaries", "deposits": "Term deposits", "investments": "Investment holdings", "securities": "Security master", "fx_trades": "Foreign exchange", "mortgages": "Mortgages", "businesses": "Business banking", "trade_finance": "Trade finance", "kyc": "KYC & onboarding", "aml_alerts": "AML monitoring", "digital_sessions": "Digital banking", "branches": "Branch network", "complaints": "Service & complaints", "consents": "Consent & preferences"}

# These links are mandatory whenever a table is selected. Other FK fields only
# bring their parent table into the output when the user selects that field.
OWNERS = {"accounts": ["customer_id"], "transactions": ["account_id"], "loans": ["customer_id"], "cards": ["account_id"], "payments": ["account_id"], "beneficiaries": ["customer_id"], "deposits": ["account_id"], "investments": ["customer_id", "security_id"], "fx_trades": ["account_id"], "mortgages": ["customer_id"], "businesses": ["customer_id"], "trade_finance": ["business_id"], "kyc": ["customer_id"], "aml_alerts": ["transaction_id"], "digital_sessions": ["customer_id"], "complaints": ["customer_id"], "consents": ["customer_id"]}
DERIVED = {"birthdate": "date", "monthly_income": "decimal", "available_balance": "decimal", "last_activity": "date", "anomaly_reason": "text", "settlement_date": "date", "value_date": "date", "loan_maturity": "date", "outstanding": "decimal", "repaid": "decimal", "days_past_due": "integer", "available_credit": "decimal", "instructed_amount": "decimal", "deposit_maturity": "date", "deposit_maturity_amount": "decimal", "deposit_interest": "decimal", "cost_basis": "decimal", "market_value": "decimal", "unrealized_gain": "decimal", "fx_pair": "text", "other_currency": "text", "fx_sell_amount": "decimal", "mortgage_payment": "decimal", "mortgage_ltv": "decimal", "trade_available": "decimal", "trade_utilized": "decimal", "logout": "datetime"}

@dataclass(frozen=True)
class Field:
    table: str
    name: str
    rule: str

    @property
    def id(self):
        return f"{self.table}.{self.name}"

    @property
    def label(self):
        return self.name.replace("_", " ").capitalize().replace(" id", " ID").replace("Ip ", "IP ").replace("Apr ", "APR ")

    @property
    def dtype(self):
        kind = self.rule.split(":")[0]
        return DERIVED.get(kind, {"int": "integer", "money": "decimal", "decimal": "decimal", "bool": "boolean", "constant": "boolean", "pastdate": "date", "futuredate": "date", "asof": "date", "timestamp": "datetime"}.get(kind, "text"))

    @property
    def description(self):
        kind, _, args = self.rule.partition(":")
        if kind == "id":
            return "Unique fictional primary key; automatically included for this table."
        if kind == "fk":
            return f"Join key to {LABELS[args]}; a matching parent record is included."
        if kind == "enum":
            return "Illustrative values: " + args.replace(";", ", ") + "."
        if kind in ("money", "int", "decimal"):
            return f"Synthetic {self.label.lower()}. Illustrative range: {args.replace(':', ' to ')}."
        if kind in DERIVED:
            return f"{self.label} calculated from related values in this synthetic dataset."
        if kind in ("name", "company", "address", "phone", "email", "website", "token", "lastfour", "ip"):
            return f"Fictional {self.label.lower()}; test-only values, not a real identity or payment credential."
        return f"Synthetic {self.label.lower()} for {LABELS[self.table].lower()}; illustrative test data."

FIELDS = tuple(Field(table, *line.strip().split("=", 1)) for table, definition in DEFINITIONS.items() for line in definition.strip().splitlines())
BY_ID = {f.id: f for f in FIELDS}
PRIMARY_KEYS = {table: next(f.name for f in FIELDS if f.table == table and f.rule == "id") for table in DEFINITIONS}
DEFAULT_FIELDS = ("customers.display_name", "customers.age", "customers.annual_income", "customers.credit_score", "accounts.account_type", "accounts.currency", "accounts.opening_balance", "accounts.closing_balance", "transactions.timestamp", "transactions.direction", "transactions.amount", "transactions.balance_after")


def resolve_fields(selected):
    """Resolve selected fields plus PK/FK closure, in stable catalog order."""
    if not selected:
        raise ValueError("Select at least one field to generate.")
    if len(selected) != len(set(selected)) or any(x not in BY_ID for x in selected):
        raise ValueError("Selection contains unknown or duplicate fields.")
    chosen = set(selected)
    while True:
        before = len(chosen)
        for field_id in list(chosen):
            f = BY_ID[field_id]
            chosen.add(f"{f.table}.{PRIMARY_KEYS[f.table]}")
            chosen.update(f"{f.table}.{name}" for name in OWNERS.get(f.table, []))
            if f.rule.startswith("fk:"):
                parent = f.rule[3:]
                chosen.add(f"{parent}.{PRIMARY_KEYS[parent]}")
        if len(chosen) == before:
            break
    return tuple(f.id for f in FIELDS if f.id in chosen)


def catalog_records():
    return [{"Field ID": f.id, "Field": f.label, "Domain": LABELS[f.table], "Type": f.dtype, "Description": f.description} for f in FIELDS]

assert len(FIELDS) == len(BY_ID) == 500
assert all(sum(f.table == table for f in FIELDS) == 25 for table in DEFINITIONS)
