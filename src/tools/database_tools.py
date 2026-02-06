"""
Database tools using SQLite directly for legal agent
"""
import logging
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "legal_cases.db")

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

class DatabaseTools:
    """Tools for accessing SQLite database directly"""
    
    @staticmethod
    async def search_cases_db(status: Optional[str] = None, case_type: Optional[str] = None, attorney_id: Optional[str] = None) -> Dict[str, Any]:
        """Search cases in database by status, type, or attorney"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build dynamic query based on provided filters
            query = "SELECT * FROM cases WHERE 1=1"
            params = []
            
            if status:
                query += " AND status LIKE ?"
                params.append(f"%{status}%")
            
            if case_type:
                query += " AND case_type LIKE ?"
                params.append(f"%{case_type}%")
            
            if attorney_id:
                query += " AND attorney_id = ?"
                params.append(attorney_id)
            
            query += " ORDER BY filed_date DESC"
            
            cursor.execute(query, tuple(params))
            cases = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "data": cases,
                "message": f"Found {len(cases)} case(s)"
            }
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_case_details_db(case_number: str) -> Dict[str, Any]:
        """Get case details from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cases WHERE case_number = ?", (case_number,))
            case = cursor.fetchone()
            
            if not case:
                conn.close()
                return {
                    "success": False,
                    "error": f"Case {case_number} not found"
                }
            
            case_dict = dict(case)
            
            # Get attorney details
            cursor.execute("SELECT * FROM attorneys WHERE id = ?", (case_dict.get("attorney_id"),))
            attorney = cursor.fetchone()
            if attorney:
                case_dict["attorney"] = dict(attorney)
            
            conn.close()
            
            return {
                "success": True,
                "data": case_dict,
                "message": f"Retrieved case {case_number}"
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def create_legal_case_db(
        title: str,
        case_type: str,
        client_name: str,
        attorney_id: str,
        estimated_value: Optional[float] = None,
        api_url: Optional[str] = None  # For compatibility with tool signature
    ) -> Dict[str, Any]:
        """Create a new case in database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Generate case ID and number
            case_id = f"case-{uuid.uuid4().hex[:6]}"
            
            # Get current year and next case number
            current_year = datetime.now().year
            cursor.execute("SELECT case_number FROM cases WHERE case_number LIKE ?", (f"{current_year}-%",))
            case_numbers = [row[0] for row in cursor.fetchall()]
            next_num = len(case_numbers) + 1
            case_number = f"{current_year}-CV-{next_num:05d}"
            
            case_data = {
                "id": case_id,
                "case_number": case_number,
                "title": title,
                "type": case_type,
                "status": "New",
                "filed_date": datetime.now().strftime("%Y-%m-%d"),
                "attorney_id": attorney_id,
                "client": client_name,
                "next_hearing": None,
                "estimated_value": estimated_value
            }
            
            cursor.execute("""
                INSERT INTO cases (id, case_number, title, type, status, filed_date, 
                                  attorney_id, client, next_hearing, estimated_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_data["id"], case_data["case_number"], case_data["title"],
                case_data["type"], case_data["status"], case_data["filed_date"],
                case_data["attorney_id"], case_data["client"], 
                case_data["next_hearing"], case_data["estimated_value"]
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "data": case_data,
                "message": f"Case created successfully: {case_number}"
            }
                
        except Exception as e:
            logger.error(f"Case creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def update_case_status_db(case_number: str, status: str) -> Dict[str, Any]:
        """Update case status in database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify case exists
            cursor.execute("SELECT * FROM cases WHERE case_number = ?", (case_number,))
            case = cursor.fetchone()
            
            if not case:
                conn.close()
                return {
                    "success": False,
                    "error": f"Case {case_number} not found"
                }
            
            cursor.execute("UPDATE cases SET status = ? WHERE case_number = ?", (status, case_number))
            conn.commit()
            
            # Get updated case
            cursor.execute("SELECT * FROM cases WHERE case_number = ?", (case_number,))
            updated_case = dict(cursor.fetchone())
            conn.close()
            
            return {
                "success": True,
                "data": updated_case,
                "message": f"Case {case_number} status updated to {status}"
            }
                
        except Exception as e:
            logger.error(f"Status update failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_attorney_info_db(attorney_id: str) -> Dict[str, Any]:
        """Get attorney information from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM attorneys WHERE id = ?", (attorney_id,))
            attorney = cursor.fetchone()
            conn.close()
            
            if not attorney:
                return {
                    "success": False,
                    "error": f"Attorney {attorney_id} not found"
                }
            
            return {
                "success": True,
                "data": dict(attorney),
                "message": f"Retrieved attorney information"
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def search_invoices_db(query: str) -> Dict[str, Any]:
        """Search invoices in database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT i.*, GROUP_CONCAT(ii.description || ': $' || ii.amount, ', ') as items
                FROM invoices i
                LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
                WHERE i.client_name LIKE ? OR i.invoice_number LIKE ?
                GROUP BY i.id
            """, (search_term, search_term))
            
            invoices = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "data": invoices,
                "message": f"Found {len(invoices)} invoice(s)"
            }
        except Exception as e:
            logger.error(f"Invoice search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_invoice_db(invoice_number: str) -> Dict[str, Any]:
        """Get invoice details from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,))
            invoice = cursor.fetchone()
            
            if not invoice:
                conn.close()
                return {
                    "success": False,
                    "error": f"Invoice {invoice_number} not found"
                }
            
            invoice_dict = dict(invoice)
            
            # Get invoice items
            cursor.execute("""
                SELECT description, amount FROM invoice_items 
                WHERE invoice_id = ?
            """, (invoice_dict["id"],))
            
            items = [dict(row) for row in cursor.fetchall()]
            invoice_dict["items"] = items
            
            conn.close()
            
            return {
                "success": True,
                "data": invoice_dict,
                "message": f"Retrieved invoice {invoice_number}"
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_legal_rates_db() -> Dict[str, Any]:
        """Get legal service rates from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM legal_rates ORDER BY rate DESC")
            rates = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "data": {"rates": rates},
                "message": "Retrieved legal service rates"
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Export database tools
db_tools = DatabaseTools()
