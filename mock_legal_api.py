"""
Mock Legal API Server
A sample legal services API for testing integration actions

Run with: uvicorn mock_legal_api:app --port 3001 --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

app = FastAPI(
    title="Mock Legal Services API",
    description="Sample API for testing legal document agent integrations",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data
ATTORNEYS = [
    {
        "id": "att-001",
        "name": "Sarah Johnson",
        "specialty": "Corporate Law",
        "hourly_rate": 500,
        "years_experience": 15,
        "bar_number": "CA123456",
        "email": "sarah.johnson@lawfirm.com",
        "phone": "+1-555-0101",
        "available": True
    },
    {
        "id": "att-002",
        "name": "Michael Chen",
        "specialty": "Intellectual Property",
        "hourly_rate": 450,
        "years_experience": 12,
        "bar_number": "CA123457",
        "email": "michael.chen@lawfirm.com",
        "phone": "+1-555-0102",
        "available": True
    },
    {
        "id": "att-003",
        "name": "Emily Rodriguez",
        "specialty": "Contract Law",
        "hourly_rate": 400,
        "years_experience": 8,
        "bar_number": "CA123458",
        "email": "emily.rodriguez@lawfirm.com",
        "phone": "+1-555-0103",
        "available": False
    }
]

LEGAL_RATES = [
    {
        "id": "rate-001",
        "service": "Contract Review",
        "rate": 350,
        "unit": "hour",
        "description": "Review and analysis of legal contracts",
        "typical_duration": "2-4 hours"
    },
    {
        "id": "rate-002",
        "service": "Legal Consultation",
        "rate": 300,
        "unit": "hour",
        "description": "Initial consultation and legal advice",
        "typical_duration": "1-2 hours"
    },
    {
        "id": "rate-003",
        "service": "Document Drafting",
        "rate": 400,
        "unit": "hour",
        "description": "Drafting legal documents and agreements",
        "typical_duration": "3-5 hours"
    },
    {
        "id": "rate-004",
        "service": "Court Representation",
        "rate": 600,
        "unit": "hour",
        "description": "Legal representation in court proceedings",
        "typical_duration": "varies"
    },
    {
        "id": "rate-005",
        "service": "Legal Research",
        "rate": 250,
        "unit": "hour",
        "description": "Research on legal precedents and case law",
        "typical_duration": "2-6 hours"
    }
]

CASES = [
    {
        "id": "case-001",
        "case_number": "2026-CV-12345",
        "title": "ABC Corp v. XYZ Inc.",
        "type": "Contract Dispute",
        "status": "Active",
        "filed_date": "2026-01-15",
        "attorney_id": "att-001",
        "client": "ABC Corporation",
        "next_hearing": "2026-03-20",
        "estimated_value": 500000
    },
    {
        "id": "case-002",
        "case_number": "2026-CV-12346",
        "title": "Smith v. Johnson LLC",
        "type": "Employment Dispute",
        "status": "Settlement Negotiation",
        "filed_date": "2025-11-10",
        "attorney_id": "att-002",
        "client": "John Smith",
        "next_hearing": None,
        "estimated_value": 150000
    },
    {
        "id": "case-003",
        "case_number": "2026-IP-00789",
        "title": "TechStart Inc. v. Competitor Co.",
        "type": "Intellectual Property",
        "status": "Discovery",
        "filed_date": "2026-02-01",
        "attorney_id": "att-002",
        "client": "TechStart Inc.",
        "next_hearing": "2026-04-15",
        "estimated_value": 1000000
    }
]

CLIENTS = [
    {
        "id": "client-001",
        "name": "ABC Corporation",
        "type": "Business",
        "email": "legal@abccorp.com",
        "phone": "+1-555-1001",
        "address": "123 Business Ave, San Francisco, CA 94102",
        "active_cases": 2,
        "total_billed": 125000
    },
    {
        "id": "client-002",
        "name": "John Smith",
        "type": "Individual",
        "email": "john.smith@email.com",
        "phone": "+1-555-1002",
        "address": "456 Residential St, San Francisco, CA 94103",
        "active_cases": 1,
        "total_billed": 15000
    }
]

INVOICES = [
    {
        "id": "inv-001",
        "invoice_number": "INV-2026-001",
        "invoice_name": "Professional Services Invoice from TechSolutions Consulting",
        "client_name": "TechSolutions Consulting",
        "client_email": "billing@techsolutions.com",
        "issue_date": "2026-01-15",
        "due_date": "2026-02-14",
        "status": "paid",
        "items": [
            {
                "description": "Contract Review - Technology Agreement",
                "quantity": 8,
                "rate": 350,
                "amount": 2800
            },
            {
                "description": "Legal Consultation - Corporate Structure",
                "quantity": 3,
                "rate": 300,
                "amount": 900
            },
            {
                "description": "Document Drafting - NDA Templates",
                "quantity": 5,
                "rate": 400,
                "amount": 2000
            }
        ],
        "subtotal": 5700,
        "tax": 0,
        "total": 5700,
        "paid_amount": 5700,
        "balance": 0,
        "notes": "Thank you for your business. Payment received via wire transfer.",
        "attorney_id": "att-001",
        "case_id": None
    },
    {
        "id": "inv-002",
        "invoice_number": "INV-2026-002",
        "invoice_name": "Legal Services - ABC Corporation Q1 2026",
        "client_name": "ABC Corporation",
        "client_email": "legal@abccorp.com",
        "issue_date": "2026-02-01",
        "due_date": "2026-03-03",
        "status": "outstanding",
        "items": [
            {
                "description": "Corporate Law Services - Contract Dispute Case",
                "quantity": 20,
                "rate": 500,
                "amount": 10000
            },
            {
                "description": "Court Representation - Preliminary Hearing",
                "quantity": 6,
                "rate": 600,
                "amount": 3600
            }
        ],
        "subtotal": 13600,
        "tax": 0,
        "total": 13600,
        "paid_amount": 0,
        "balance": 13600,
        "notes": "Payment due within 30 days. Wire transfer details included.",
        "attorney_id": "att-001",
        "case_id": "case-001"
    },
    {
        "id": "inv-003",
        "invoice_number": "INV-2026-003",
        "invoice_name": "IP Consultation - TechStart Inc.",
        "client_name": "TechStart Inc.",
        "client_email": "legal@techstart.com",
        "issue_date": "2026-02-05",
        "due_date": "2026-03-07",
        "status": "outstanding",
        "items": [
            {
                "description": "Legal Consultation - Patent Strategy",
                "quantity": 4,
                "rate": 450,
                "amount": 1800
            },
            {
                "description": "Legal Research - Prior Art Search",
                "quantity": 10,
                "rate": 250,
                "amount": 2500
            }
        ],
        "subtotal": 4300,
        "tax": 0,
        "total": 4300,
        "paid_amount": 0,
        "balance": 4300,
        "notes": "Initial consultation for IP portfolio development.",
        "attorney_id": "att-002",
        "case_id": "case-003"
    }
]

# Models
class CaseCreate(BaseModel):
    title: str
    type: str
    client: str
    attorney_id: str
    estimated_value: Optional[float] = None

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    next_hearing: Optional[str] = None
    estimated_value: Optional[float] = None

# Endpoints
@app.get("/")
def root():
    """API information"""
    return {
        "name": "Mock Legal Services API",
        "version": "1.0.0",
        "endpoints": {
            "attorneys": "/attorneys",
            "rates": "/legal-rates",
            "cases": "/cases",
            "clients": "/clients",
            "invoices": "/invoices"
        }
    }

@app.get("/attorneys")
def get_attorneys(
    specialty: Optional[str] = None,
    available_only: bool = False
):
    """Get list of attorneys"""
    attorneys = ATTORNEYS.copy()
    
    if specialty:
        attorneys = [a for a in attorneys if specialty.lower() in a["specialty"].lower()]
    
    if available_only:
        attorneys = [a for a in attorneys if a["available"]]
    
    return {
        "count": len(attorneys),
        "attorneys": attorneys
    }

@app.get("/attorneys/{attorney_id}")
def get_attorney(attorney_id: str):
    """Get attorney by ID"""
    attorney = next((a for a in ATTORNEYS if a["id"] == attorney_id), None)
    
    if not attorney:
        raise HTTPException(status_code=404, detail="Attorney not found")
    
    # Get attorney's cases
    attorney_cases = [c for c in CASES if c["attorney_id"] == attorney_id]
    
    return {
        **attorney,
        "active_cases": len([c for c in attorney_cases if c["status"] == "Active"]),
        "total_cases": len(attorney_cases)
    }

@app.get("/legal-rates")
def get_legal_rates(service_type: Optional[str] = None):
    """Get legal service rates"""
    rates = LEGAL_RATES.copy()
    
    if service_type:
        rates = [r for r in rates if service_type.lower() in r["service"].lower()]
    
    return {
        "count": len(rates),
        "rates": rates,
        "currency": "USD"
    }

@app.get("/legal-rates/{rate_id}")
def get_rate(rate_id: str):
    """Get specific rate by ID"""
    rate = next((r for r in LEGAL_RATES if r["id"] == rate_id), None)
    
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    
    return rate

@app.get("/cases")
def get_cases(
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    attorney_id: Optional[str] = None
):
    """Get list of cases"""
    cases = CASES.copy()
    
    if status:
        cases = [c for c in cases if c["status"].lower() == status.lower()]
    
    if case_type:
        cases = [c for c in cases if case_type.lower() in c["type"].lower()]
    
    if attorney_id:
        cases = [c for c in cases if c["attorney_id"] == attorney_id]
    
    return {
        "count": len(cases),
        "cases": cases
    }

@app.get("/cases/{case_id}")
def get_case(case_id: str):
    """Get case details"""
    case = next((c for c in CASES if c["id"] == case_id), None)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Add attorney details
    attorney = next((a for a in ATTORNEYS if a["id"] == case["attorney_id"]), None)
    
    return {
        **case,
        "attorney": attorney
    }

@app.post("/cases")
def create_case(case_data: CaseCreate):
    """Create a new case"""
    new_case = {
        "id": f"case-{uuid.uuid4().hex[:6]}",
        "case_number": f"2026-CV-{len(CASES) + 10000}",
        "title": case_data.title,
        "type": case_data.type,
        "status": "New",
        "filed_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "attorney_id": case_data.attorney_id,
        "client": case_data.client,
        "next_hearing": None,
        "estimated_value": case_data.estimated_value
    }
    
    CASES.append(new_case)
    
    return {
        "message": "Case created successfully",
        "case": new_case
    }

@app.put("/cases/{case_id}")
def update_case(case_id: str, updates: CaseUpdate):
    """Update case status"""
    case = next((c for c in CASES if c["id"] == case_id), None)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if updates.status:
        case["status"] = updates.status
    if updates.next_hearing:
        case["next_hearing"] = updates.next_hearing
    if updates.estimated_value is not None:
        case["estimated_value"] = updates.estimated_value
    
    return {
        "message": "Case updated successfully",
        "case": case
    }

@app.get("/clients")
def get_clients(client_type: Optional[str] = None):
    """Get list of clients"""
    clients = CLIENTS.copy()
    
    if client_type:
        clients = [c for c in clients if c["type"].lower() == client_type.lower()]
    
    return {
        "count": len(clients),
        "clients": clients
    }

@app.get("/clients/{client_id}")
def get_client(client_id: str):
    """Get client details"""
    client = next((c for c in CLIENTS if c["id"] == client_id), None)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client's cases
    client_cases = [c for c in CASES if c["client"] == client["name"]]
    
    return {
        **client,
        "cases": client_cases
    }

@app.get("/case-summary")
def get_case_summary():
    """Get summary statistics"""
    return {
        "total_cases": len(CASES),
        "active_cases": len([c for c in CASES if c["status"] == "Active"]),
        "cases_by_status": {
            "Active": len([c for c in CASES if c["status"] == "Active"]),
            "Settlement Negotiation": len([c for c in CASES if c["status"] == "Settlement Negotiation"]),
            "Discovery": len([c for c in CASES if c["status"] == "Discovery"])
        },
        "total_estimated_value": sum(c.get("estimated_value", 0) for c in CASES),
        "total_attorneys": len(ATTORNEYS),
        "available_attorneys": len([a for a in ATTORNEYS if a["available"]])
    }

@app.get("/calculate-estimate")
def calculate_estimate(
    service: str = Query(..., description="Service type"),
    hours: float = Query(..., description="Estimated hours")
):
    """Calculate cost estimate for legal services"""
    rate = next((r for r in LEGAL_RATES if r["service"].lower() == service.lower()), None)
    
    if not rate:
        raise HTTPException(status_code=404, detail="Service not found")
    
    subtotal = rate["rate"] * hours
    tax = subtotal * 0.0  # No tax for services
    total = subtotal + tax
    
    return {
        "service": rate["service"],
        "hourly_rate": rate["rate"],
        "hours": hours,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "currency": "USD"
    }

@app.get("/invoices")
def get_invoices(
    status: Optional[str] = Query(None, description="Filter by status (paid, outstanding, overdue)"),
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    attorney_id: Optional[str] = Query(None, description="Filter by attorney ID")
):
    """Get all invoices with optional filters"""
    filtered = INVOICES.copy()
    
    if status:
        filtered = [inv for inv in filtered if inv["status"].lower() == status.lower()]
    
    if client_name:
        filtered = [inv for inv in filtered if client_name.lower() in inv["client_name"].lower()]
    
    if attorney_id:
        filtered = [inv for inv in filtered if inv.get("attorney_id") == attorney_id]
    
    return {
        "count": len(filtered),
        "invoices": filtered
    }

@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str):
    """Get a specific invoice by ID"""
    invoice = next((inv for inv in INVOICES if inv["id"] == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
    return invoice

@app.get("/invoices/search/{query}")
def search_invoices(query: str):
    """Search invoices by name, client, or invoice number"""
    query_lower = query.lower()
    results = [
        inv for inv in INVOICES
        if query_lower in inv["invoice_name"].lower()
        or query_lower in inv["client_name"].lower()
        or query_lower in inv["invoice_number"].lower()
    ]
    
    return {
        "query": query,
        "count": len(results),
        "invoices": results
    }

@app.get("/invoices/client/{client_name}")
def get_client_invoices(client_name: str):
    """Get all invoices for a specific client"""
    client_invoices = [
        inv for inv in INVOICES
        if client_name.lower() in inv["client_name"].lower()
    ]
    
    total_billed = sum(inv["total"] for inv in client_invoices)
    total_paid = sum(inv["paid_amount"] for inv in client_invoices)
    balance = sum(inv["balance"] for inv in client_invoices)
    
    return {
        "client_name": client_name,
        "invoice_count": len(client_invoices),
        "total_billed": total_billed,
        "total_paid": total_paid,
        "outstanding_balance": balance,
        "invoices": client_invoices
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🏛️  Mock Legal Services API Starting...")
    print("="*60)
    print(f"\n📍 API will be available at: http://localhost:3001")
    print(f"📚 Interactive docs at: http://localhost:3001/docs")
    print(f"\n🔗 Test endpoints:")
    print(f"   • Attorneys: http://localhost:3001/attorneys")
    print(f"   • Legal Rates: http://localhost:3001/legal-rates")
    print(f"   • Cases: http://localhost:3001/cases")
    print(f"   • Invoices: http://localhost:3001/invoices")
    print(f"   • Summary: http://localhost:3001/case-summary")
    print(f"\n💡 Use with your agent:")
    print(f'   "Call the API at http://localhost:3001/legal-rates"')
    print(f'   "Get attorney info from http://localhost:3001/attorneys/att-001"')
    print(f'   "Show me the invoice from TechSolutions Consulting"')
    print(f'   "Fetch case summary from http://localhost:3001/case-summary"\n')
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=3001)
