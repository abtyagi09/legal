"""
MCP (Model Context Protocol) integration for SQLite database access
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class SQLiteMCPClient:
    """Client for interacting with SQLite database via MCP"""
    
    def __init__(self, db_path: str = "legal_cases.db"):
        self.db_path = db_path
        self.session: Optional[ClientSession] = None
        self._exit_stack = None
        
    async def connect(self):
        """Connect to SQLite MCP server"""
        try:
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-sqlite", self.db_path]
            )
            
            # Create context manager for stdio client
            self._exit_stack = asyncio.create_task(self._run_client(server_params))
            logger.info(f"Connected to SQLite MCP server for database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite MCP server: {e}")
            raise
    
    async def _run_client(self, server_params: StdioServerParameters):
        """Run the MCP client"""
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                # Keep connection alive
                while True:
                    await asyncio.sleep(1)
    
    async def query(self, sql: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute SQL query via MCP"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        
        try:
            # Use MCP's query tool
            result = await self.session.call_tool(
                "query",
                arguments={"sql": sql, "params": params or []}
            )
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_cases(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all cases, optionally filtered by status"""
        if status:
            sql = "SELECT * FROM cases WHERE status = ?"
            result = await self.query(sql, (status,))
        else:
            sql = "SELECT * FROM cases"
            result = await self.query(sql)
        
        return result.get("data", [])
    
    async def get_case_by_number(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Get case by case number"""
        sql = "SELECT * FROM cases WHERE case_number = ?"
        result = await self.query(sql, (case_number,))
        data = result.get("data", [])
        return data[0] if data else None
    
    async def search_cases(self, query: str) -> List[Dict[str, Any]]:
        """Search cases by title or client name"""
        sql = """
        SELECT * FROM cases 
        WHERE title LIKE ? OR client LIKE ?
        ORDER BY filed_date DESC
        """
        search_term = f"%{query}%"
        result = await self.query(sql, (search_term, search_term))
        return result.get("data", [])
    
    async def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new case"""
        sql = """
        INSERT INTO cases (id, case_number, title, type, status, filed_date, 
                          attorney_id, client, next_hearing, estimated_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            case_data["id"],
            case_data["case_number"],
            case_data["title"],
            case_data["type"],
            case_data.get("status", "New"),
            case_data["filed_date"],
            case_data["attorney_id"],
            case_data["client"],
            case_data.get("next_hearing"),
            case_data.get("estimated_value")
        )
        result = await self.query(sql, params)
        return result
    
    async def update_case_status(self, case_number: str, status: str) -> Dict[str, Any]:
        """Update case status"""
        sql = "UPDATE cases SET status = ? WHERE case_number = ?"
        result = await self.query(sql, (status, case_number))
        return result
    
    async def get_attorneys(self, specialty: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all attorneys, optionally filtered by specialty"""
        if specialty:
            sql = "SELECT * FROM attorneys WHERE specialty LIKE ?"
            result = await self.query(sql, (f"%{specialty}%",))
        else:
            sql = "SELECT * FROM attorneys"
            result = await self.query(sql)
        
        return result.get("data", [])
    
    async def get_attorney_by_id(self, attorney_id: str) -> Optional[Dict[str, Any]]:
        """Get attorney by ID"""
        sql = "SELECT * FROM attorneys WHERE id = ?"
        result = await self.query(sql, (attorney_id,))
        data = result.get("data", [])
        return data[0] if data else None
    
    async def get_invoices(self, client_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get invoices, optionally filtered by client"""
        if client_name:
            sql = """
            SELECT i.*, 
                   GROUP_CONCAT(ii.description || ': $' || ii.amount, ', ') as items
            FROM invoices i
            LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
            WHERE i.client_name LIKE ?
            GROUP BY i.id
            """
            result = await self.query(sql, (f"%{client_name}%",))
        else:
            sql = """
            SELECT i.*, 
                   GROUP_CONCAT(ii.description || ': $' || ii.amount, ', ') as items
            FROM invoices i
            LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
            GROUP BY i.id
            """
            result = await self.query(sql)
        
        return result.get("data", [])
    
    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """Get invoice by invoice number with items"""
        sql = """
        SELECT i.*, 
               json_group_array(
                   json_object('description', ii.description, 'amount', ii.amount)
               ) as items
        FROM invoices i
        LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
        WHERE i.invoice_number = ?
        GROUP BY i.id
        """
        result = await self.query(sql, (invoice_number,))
        data = result.get("data", [])
        return data[0] if data else None
    
    async def get_legal_rates(self) -> List[Dict[str, Any]]:
        """Get all legal service rates"""
        sql = "SELECT * FROM legal_rates ORDER BY rate DESC"
        result = await self.query(sql)
        return result.get("data", [])
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self._exit_stack:
            self._exit_stack.cancel()
            self._exit_stack = None
        self.session = None
        logger.info("Disconnected from SQLite MCP server")

# Global MCP client instance
_mcp_client: Optional[SQLiteMCPClient] = None

async def get_mcp_client() -> SQLiteMCPClient:
    """Get or create global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = SQLiteMCPClient()
        await _mcp_client.connect()
    return _mcp_client
