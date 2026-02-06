"""
Integration Actions for Legal Document Agent
Provides external API calls, notifications, and invoice generation
"""

import logging
import json
from typing import Dict, Optional, Any
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class IntegrationActions:
    """Integration actions for external services"""
    
    def __init__(self):
        """Initialize integration actions"""
        self.session = None
        
    async def initialize(self):
        """Initialize async HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def call_external_api(
        self, 
        url: str, 
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Call an external API
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, PUT, DELETE)
            headers: Optional HTTP headers
            data: Optional request body data
            params: Optional query parameters
            
        Returns:
            API response as dictionary
        """
        try:
            logger.info(f"Calling external API: {method} {url}")
            
            await self.initialize()
            
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                status = response.status
                
                # Try to parse JSON response
                try:
                    result = await response.json()
                except:
                    result = {"text": await response.text()}
                
                logger.info(f"API response status: {status}")
                
                return {
                    "success": 200 <= status < 300,
                    "status_code": status,
                    "data": result
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"API call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
        except Exception as e:
            logger.error(f"Unexpected error calling API: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def send_email_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        cc: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email notification (placeholder - integrate with your email service)
        
        Args:
            recipient: Email address
            subject: Email subject
            body: Email body (HTML supported)
            cc: Optional CC recipients
            
        Returns:
            Result dictionary
        """
        try:
            logger.info(f"Sending email notification to: {recipient}")
            
            # TODO: Integrate with your email service (SendGrid, Azure Communication Services, etc.)
            # Example for Azure Communication Services:
            # from azure.communication.email import EmailClient
            # email_client = EmailClient.from_connection_string(connection_string)
            # message = {
            #     "senderAddress": "sender@yourdomain.com",
            #     "recipients": {"to": [{"address": recipient}]},
            #     "content": {"subject": subject, "html": body}
            # }
            # poller = await email_client.begin_send(message)
            # result = await poller.result()
            
            # Placeholder implementation
            notification_data = {
                "recipient": recipient,
                "subject": subject,
                "body": body[:100] + "...",  # Preview
                "cc": cc,
                "sent_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Email notification prepared: {notification_data}")
            
            return {
                "success": True,
                "message": "Email notification queued successfully",
                "data": notification_data
            }
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_teams_notification(
        self,
        webhook_url: str,
        title: str,
        message: str,
        color: str = "0078D4"
    ) -> Dict[str, Any]:
        """
        Send notification to Microsoft Teams channel
        
        Args:
            webhook_url: Teams incoming webhook URL
            title: Notification title
            message: Notification message
            color: Theme color (hex)
            
        Returns:
            Result dictionary
        """
        try:
            logger.info(f"Sending Teams notification: {title}")
            
            # Teams adaptive card format
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": color,
                "title": title,
                "sections": [{
                    "activityTitle": "Legal Document Agent",
                    "activitySubtitle": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "text": message,
                    "markdown": True
                }]
            }
            
            result = await self.call_external_api(
                url=webhook_url,
                method="POST",
                headers={"Content-Type": "application/json"},
                data=card
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_case(
        self,
        title: str,
        case_type: str,
        client_name: str,
        attorney_id: str,
        description: Optional[str] = None,
        priority: str = "medium",
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Create a new legal case
        
        Args:
            title: Case title
            case_type: Type of case (e.g., "Contract Dispute", "Personal Injury")
            client_name: Client name
            attorney_id: Assigned attorney ID
            description: Case description
            priority: Case priority (low, medium, high)
            api_base_url: Base URL for the legal API
            
        Returns:
            Created case data dictionary
        """
        try:
            logger.info(f"Creating case: {title}")
            
            case_data = {
                "title": title,
                "case_type": case_type,
                "client_name": client_name,
                "attorney_id": attorney_id,
                "priority": priority,
                "status": "open"
            }
            
            if description:
                case_data["description"] = description
            
            result = await self.call_external_api(
                url=f"{api_base_url}/cases",
                method="POST",
                headers={"Content-Type": "application/json"},
                data=case_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create case: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_case(
        self,
        case_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        priority: Optional[str] = None,
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Update an existing legal case
        
        Args:
            case_id: Case ID to update
            status: New status (open, in_progress, closed)
            notes: Additional notes
            priority: New priority (low, medium, high)
            api_base_url: Base URL for the legal API
            
        Returns:
            Updated case data dictionary
        """
        try:
            logger.info(f"Updating case: {case_id}")
            
            update_data = {}
            if status:
                update_data["status"] = status
            if notes:
                update_data["notes"] = notes
            if priority:
                update_data["priority"] = priority
            
            result = await self.call_external_api(
                url=f"{api_base_url}/cases/{case_id}",
                method="PUT",
                headers={"Content-Type": "application/json"},
                data=update_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update case: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_case(
        self,
        case_id: str,
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Get case details
        
        Args:
            case_id: Case ID to retrieve
            api_base_url: Base URL for the legal API
            
        Returns:
            Case data dictionary
        """
        try:
            logger.info(f"Getting case: {case_id}")
            
            result = await self.call_external_api(
                url=f"{api_base_url}/cases/{case_id}",
                method="GET"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get case: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_cases(
        self,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        attorney_id: Optional[str] = None,
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Search for cases with filters
        
        Args:
            status: Filter by status
            case_type: Filter by case type
            attorney_id: Filter by attorney ID
            api_base_url: Base URL for the legal API
            
        Returns:
            List of matching cases
        """
        try:
            logger.info("Searching cases")
            
            params = {}
            if status:
                params["status"] = status
            if case_type:
                params["case_type"] = case_type
            if attorney_id:
                params["attorney_id"] = attorney_id
            
            result = await self.call_external_api(
                url=f"{api_base_url}/cases",
                method="GET",
                params=params
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search cases: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_invoice(
        self,
        client_name: str,
        client_email: str,
        invoice_number: Optional[str] = None,
        items: Optional[list] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an invoice document
        
        Args:
            client_name: Client name
            client_email: Client email
            invoice_number: Invoice number (auto-generated if not provided)
            items: List of invoice items [{"description": "", "amount": 0.0, "quantity": 1}]
            due_date: Due date (ISO format)
            notes: Additional notes
            
        Returns:
            Invoice data dictionary
        """
        try:
            logger.info(f"Generating invoice for: {client_name}")
            
            # Generate invoice number if not provided
            if not invoice_number:
                invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Default items if none provided
            if not items:
                items = []
            
            # Calculate totals
            subtotal = sum(item.get("amount", 0) * item.get("quantity", 1) for item in items)
            tax_rate = 0.0  # Customize based on your jurisdiction
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount
            
            # Create invoice data structure
            invoice_data = {
                "invoice_number": invoice_number,
                "date_issued": datetime.utcnow().isoformat(),
                "due_date": due_date or (datetime.utcnow().isoformat()),
                "client": {
                    "name": client_name,
                    "email": client_email
                },
                "items": items,
                "subtotal": subtotal,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total": total,
                "currency": "USD",
                "notes": notes or "",
                "status": "draft"
            }
            
            # Generate HTML invoice
            invoice_html = self._generate_invoice_html(invoice_data)
            invoice_data["html"] = invoice_html
            
            logger.info(f"Invoice generated: {invoice_number}, Total: ${total:.2f}")
            
            # TODO: Save to database or storage
            # TODO: Send via email using send_email_notification
            
            return {
                "success": True,
                "message": f"Invoice {invoice_number} generated successfully",
                "data": invoice_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate invoice: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_legal_case(
        self,
        title: str,
        case_type: str,
        client_name: str,
        attorney_id: str,
        estimated_value: Optional[float] = None,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Create a new legal case
        
        Args:
            title: Case title
            case_type: Type of case (e.g., "Contract Dispute", "Intellectual Property")
            client_name: Client name
            attorney_id: Attorney ID to assign
            estimated_value: Estimated case value in USD
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with case details
        """
        try:
            logger.info(f"Creating new legal case: {title}")
            
            case_data = {
                "title": title,
                "type": case_type,
                "client": client_name,
                "attorney_id": attorney_id
            }
            
            if estimated_value is not None:
                case_data["estimated_value"] = estimated_value
            
            result = await self.call_external_api(
                url=f"{api_url}/cases",
                method="POST",
                headers={"Content-Type": "application/json"},
                data=case_data
            )
            
            if result.get("success"):
                case = result.get("data", {}).get("case", {})
                return {
                    "success": True,
                    "message": f"Case created successfully: {case.get('case_number', 'N/A')}",
                    "data": case
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to create legal case: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_case_status(
        self,
        case_id: str,
        status: Optional[str] = None,
        next_hearing: Optional[str] = None,
        estimated_value: Optional[float] = None,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Update a legal case status
        
        Args:
            case_id: Case ID to update
            status: New status (e.g., "Active", "Settlement Negotiation", "Closed")
            next_hearing: Next hearing date in ISO format (YYYY-MM-DD)
            estimated_value: Updated estimated value
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with updated case details
        """
        try:
            logger.info(f"Updating case: {case_id}")
            
            update_data = {}
            if status:
                update_data["status"] = status
            if next_hearing:
                update_data["next_hearing"] = next_hearing
            if estimated_value is not None:
                update_data["estimated_value"] = estimated_value
            
            if not update_data:
                return {
                    "success": False,
                    "error": "No updates provided"
                }
            
            result = await self.call_external_api(
                url=f"{api_url}/cases/{case_id}",
                method="PUT",
                headers={"Content-Type": "application/json"},
                data=update_data
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Case updated successfully",
                    "data": result.get("data", {}).get("case", {})
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to update case: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_cases(
        self,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        attorney_id: Optional[str] = None,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Search for legal cases
        
        Args:
            status: Filter by status (e.g., "Active", "Closed")
            case_type: Filter by case type (e.g., "Contract Dispute")
            attorney_id: Filter by attorney ID
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with matching cases
        """
        try:
            logger.info(f"Searching cases with filters: status={status}, type={case_type}, attorney={attorney_id}")
            
            params = {}
            if status:
                params["status"] = status
            if case_type:
                params["case_type"] = case_type
            if attorney_id:
                params["attorney_id"] = attorney_id
            
            result = await self.call_external_api(
                url=f"{api_url}/cases",
                method="GET",
                params=params
            )
            
            if result.get("success"):
                cases_data = result.get("data", {})
                return {
                    "success": True,
                    "message": f"Found {cases_data.get('count', 0)} cases",
                    "data": cases_data
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to search cases: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_case_details(
        self,
        case_id: str,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific case
        
        Args:
            case_id: Case ID
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with case details
        """
        try:
            logger.info(f"Getting details for case: {case_id}")
            
            result = await self.call_external_api(
                url=f"{api_url}/cases/{case_id}",
                method="GET"
            )
            
            return result
                
        except Exception as e:
            logger.error(f"Failed to get case details: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_attorney_info(
        self,
        attorney_id: Optional[str] = None,
        specialty: Optional[str] = None,
        available_only: bool = False,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Get attorney information
        
        Args:
            attorney_id: Specific attorney ID (if None, returns all)
            specialty: Filter by specialty
            available_only: Only return available attorneys
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with attorney information
        """
        try:
            if attorney_id:
                logger.info(f"Getting info for attorney: {attorney_id}")
                result = await self.call_external_api(
                    url=f"{api_url}/attorneys/{attorney_id}",
                    method="GET"
                )
            else:
                logger.info(f"Searching attorneys: specialty={specialty}, available_only={available_only}")
                params = {}
                if specialty:
                    params["specialty"] = specialty
                if available_only:
                    params["available_only"] = "true"
                
                result = await self.call_external_api(
                    url=f"{api_url}/attorneys",
                    method="GET",
                    params=params
                )
            
            return result
                
        except Exception as e:
            logger.error(f"Failed to get attorney info: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_legal_rates(
        self,
        service_type: Optional[str] = None,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Get legal service rates
        
        Args:
            service_type: Filter by service type (e.g., "Contract Review")
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with rate information
        """
        try:
            logger.info(f"Getting legal rates: service_type={service_type}")
            
            params = {}
            if service_type:
                params["service_type"] = service_type
            
            result = await self.call_external_api(
                url=f"{api_url}/legal-rates",
                method="GET",
                params=params
            )
            
            return result
                
        except Exception as e:
            logger.error(f"Failed to get legal rates: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def calculate_legal_estimate(
        self,
        service: str,
        hours: float,
        api_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Calculate cost estimate for legal services
        
        Args:
            service: Service type (e.g., "Contract Review")
            hours: Estimated hours
            api_url: Base URL of the legal API
            
        Returns:
            Result dictionary with cost calculation
        """
        try:
            logger.info(f"Calculating estimate: {service} for {hours} hours")
            
            result = await self.call_external_api(
                url=f"{api_url}/calculate-estimate",
                method="GET",
                params={"service": service, "hours": str(hours)}
            )
            
            if result.get("success"):
                estimate = result.get("data", {})
                return {
                    "success": True,
                    "message": f"Total estimate: ${estimate.get('total', 0):.2f}",
                    "data": estimate
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to calculate estimate: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_invoices(
        self,
        query: str,
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Search for invoices by name, client, or invoice number
        
        Args:
            query: Search query (invoice name, client name, or invoice number)
            api_base_url: Base URL for the legal API
            
        Returns:
            Search results with matching invoices
        """
        try:
            logger.info(f"Searching invoices: {query}")
            
            result = await self.call_external_api(
                url=f"{api_base_url}/invoices/search/{query}",
                method="GET"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search invoices: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_invoice(
        self,
        invoice_id: str,
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Get a specific invoice by ID
        
        Args:
            invoice_id: Invoice ID to retrieve
            api_base_url: Base URL for the legal API
            
        Returns:
            Invoice data dictionary
        """
        try:
            logger.info(f"Getting invoice: {invoice_id}")
            
            result = await self.call_external_api(
                url=f"{api_base_url}/invoices/{invoice_id}",
                method="GET"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get invoice: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_client_invoices(
        self,
        client_name: str,
        api_base_url: str = "https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io"
    ) -> Dict[str, Any]:
        """
        Get all invoices for a specific client
        
        Args:
            client_name: Client name
            api_base_url: Base URL for the legal API
            
        Returns:
            Client invoices with totals
        """
        try:
            logger.info(f"Getting invoices for client: {client_name}")
            
            result = await self.call_external_api(
                url=f"{api_base_url}/invoices/client/{client_name}",
                method="GET"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get client invoices: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_invoice_html(self, invoice_data: Dict[str, Any]) -> str:
        """Generate HTML representation of invoice"""
        items_html = ""
        for item in invoice_data["items"]:
            desc = item.get("description", "")
            qty = item.get("quantity", 1)
            amount = item.get("amount", 0)
            line_total = qty * amount
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{desc}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{qty}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${amount:.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${line_total:.2f}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice {invoice_data['invoice_number']}</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #333; margin: 0;">INVOICE</h1>
                <p style="color: #666; font-size: 18px;">#{invoice_data['invoice_number']}</p>
            </div>
            
            <div style="margin-bottom: 30px;">
                <div style="display: inline-block; width: 48%;">
                    <h3 style="color: #333;">Bill To:</h3>
                    <p style="margin: 5px 0;">
                        <strong>{invoice_data['client']['name']}</strong><br>
                        {invoice_data['client']['email']}
                    </p>
                </div>
                <div style="display: inline-block; width: 48%; text-align: right; vertical-align: top;">
                    <p style="margin: 5px 0;">
                        <strong>Date Issued:</strong> {invoice_data['date_issued'][:10]}<br>
                        <strong>Due Date:</strong> {invoice_data['due_date'][:10]}<br>
                        <strong>Status:</strong> {invoice_data['status'].upper()}
                    </p>
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Quantity</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid #ddd;">Rate</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid #ddd;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            
            <div style="text-align: right; margin-bottom: 30px;">
                <p style="margin: 5px 0;"><strong>Subtotal:</strong> ${invoice_data['subtotal']:.2f}</p>
                <p style="margin: 5px 0;"><strong>Tax ({invoice_data['tax_rate']*100:.1f}%):</strong> ${invoice_data['tax_amount']:.2f}</p>
                <p style="margin: 10px 0; font-size: 20px; color: #0078D4;">
                    <strong>Total: ${invoice_data['total']:.2f} {invoice_data['currency']}</strong>
                </p>
            </div>
            
            {f'<div style="border-top: 1px solid #ddd; padding-top: 20px;"><p><strong>Notes:</strong><br>{invoice_data["notes"]}</p></div>' if invoice_data['notes'] else ''}
            
            <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                <p>Thank you for your business!</p>
            </div>
        </body>
        </html>
        """
        
        return html


# Tool definitions for OpenAI function calling
INTEGRATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_external_api",
            "description": "Call an external REST API to fetch or send data. Use this when you need to integrate with external services or retrieve information from APIs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the API endpoint"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP method to use"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional request body data"
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional query parameters",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_notification",
            "description": "Send an email notification to a recipient. Use this when you need to notify someone about important updates, documents, or events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (HTML supported)"
                    },
                    "cc": {
                        "type": "string",
                        "description": "Optional CC recipients (comma-separated)"
                    }
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_teams_notification",
            "description": "Send a notification to a Microsoft Teams channel via webhook. Use this for team notifications about document updates or important events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "webhook_url": {
                        "type": "string",
                        "description": "Microsoft Teams incoming webhook URL"
                    },
                    "title": {
                        "type": "string",
                        "description": "Notification title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Notification message content (Markdown supported)"
                    },
                    "color": {
                        "type": "string",
                        "description": "Theme color in hex format (e.g., '0078D4' for blue)"
                    }
                },
                "required": ["webhook_url", "title", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_invoice",
            "description": "Generate a professional invoice document for legal services. Use this when you need to bill a client or create an invoice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {
                        "type": "string",
                        "description": "Client's full name or company name"
                    },
                    "client_email": {
                        "type": "string",
                        "description": "Client's email address"
                    },
                    "invoice_number": {
                        "type": "string",
                        "description": "Invoice number (auto-generated if not provided)"
                    },
                    "items": {
                        "type": "array",
                        "description": "List of invoice line items",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "amount": {"type": "number"},
                                "quantity": {"type": "number"}
                            },
                            "required": ["description", "amount"]
                        }
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Payment due date in ISO format (YYYY-MM-DD)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes or payment terms"
                    }
                },
                "required": ["client_name", "client_email", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_legal_case",
            "description": "Create a new legal case in the system. Use this when a client wants to open a new case or matter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Case title (e.g., 'ABC Corp v. XYZ Inc.')"
                    },
                    "case_type": {
                        "type": "string",
                        "description": "Type of case (e.g., 'Contract Dispute', 'Intellectual Property', 'Employment Dispute')"
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client or company name"
                    },
                    "attorney_id": {
                        "type": "string",
                        "description": "Attorney ID to assign to this case (e.g., 'att-001')"
                    },
                    "estimated_value": {
                        "type": "number",
                        "description": "Estimated case value in USD"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["title", "case_type", "client_name", "attorney_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_case_status",
            "description": "Update the status of an existing legal case. Use this to change case status, update hearing dates, or modify case value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Case ID (e.g., 'case-001')"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status (e.g., 'Active', 'Settlement Negotiation', 'Discovery', 'Closed')"
                    },
                    "next_hearing": {
                        "type": "string",
                        "description": "Next hearing date in ISO format (YYYY-MM-DD)"
                    },
                    "estimated_value": {
                        "type": "number",
                        "description": "Updated estimated case value in USD"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_cases",
            "description": "Search for legal CASE RECORDS in the external legal management system (NOT documents). Use this ONLY to find case records by status, type, or attorney - NOT for searching document content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status (e.g., 'Active', 'Closed')"
                    },
                    "case_type": {
                        "type": "string",
                        "description": "Filter by case type (e.g., 'Contract Dispute', 'Intellectual Property')"
                    },
                    "attorney_id": {
                        "type": "string",
                        "description": "Filter by attorney ID (e.g., 'att-001')"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_case_details",
            "description": "Get detailed information about a specific legal case including attorney details and case history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Case ID (e.g., 'case-001')"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attorney_info",
            "description": "Get information about attorneys. Can search for specific attorney, filter by specialty, or find available attorneys.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attorney_id": {
                        "type": "string",
                        "description": "Specific attorney ID (e.g., 'att-001'). Leave empty to search all attorneys."
                    },
                    "specialty": {
                        "type": "string",
                        "description": "Filter by specialty (e.g., 'Corporate Law', 'Intellectual Property', 'Contract Law')"
                    },
                    "available_only": {
                        "type": "boolean",
                        "description": "Only return available attorneys"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_rates",
            "description": "Get hourly rates for legal services. Use this to find pricing for specific services or view all available services and rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_type": {
                        "type": "string",
                        "description": "Filter by service type (e.g., 'Contract Review', 'Legal Consultation', 'Document Drafting')"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_legal_estimate",
            "description": "Calculate the total cost estimate for legal services based on service type and estimated hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service type (e.g., 'Contract Review', 'Legal Consultation')"
                    },
                    "hours": {
                        "type": "number",
                        "description": "Estimated hours needed"
                    },
                    "api_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["service", "hours"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_invoices",
            "description": "Search for INVOICE RECORDS in the external billing system by name, client name, or invoice number. Use this when user asks to find, show, or view invoice RECORDS from the system - NOT for analyzing invoice documents uploaded to the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - can be invoice name, client name, or invoice number (e.g., 'TechSolutions', 'INV-2026-001', 'Professional Services')"
                    },
                    "api_base_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoice",
            "description": "Get a specific invoice by its ID. Use this when you have an invoice ID and need the full details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "description": "Invoice ID (e.g., 'inv-001', 'inv-002')"
                    },
                    "api_base_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["invoice_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_invoices",
            "description": "Get all invoices for a specific client, including totals and outstanding balances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {
                        "type": "string",
                        "description": "Client name (e.g., 'TechSolutions Consulting', 'ABC Corporation')"
                    },
                    "api_base_url": {
                        "type": "string",
                        "description": "Base URL of the legal API (default: https://ca-mock-legal-api.wittymoss-05f49619.eastus2.azurecontainerapps.io)"
                    }
                },
                "required": ["client_name"]
            }
        }
    }
]


