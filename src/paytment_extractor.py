"""
Core payment extraction logic with comprehensive logging.
"""
import imaplib
import email
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from email.header import decode_header
from typing import List, Dict, Optional, Tuple
from src.logger import get_logger

logger = get_logger(__name__)

class PaymentExtractor:
    """Extract payments from Gmail using IMAP."""
    
    def __init__(self, gmail_username: str, gmail_password: str, days_back: int = 15):
        self.gmail_username = gmail_username
        self.gmail_password = gmail_password
        self.days_back = days_back
        
        # Payment services configuration
        self.services = {
            'wise': 'noreply@wise.com',
            'paypal': 'service@paypal.com', 
            'remitly': 'no-reply@remitly.com',
            'billcom': 'bill.com'
        }
        
        logger.info(f"PaymentExtractor initialized for {gmail_username}, looking back {days_back} days")
    
    def extract_all_payments(self) -> List[Dict]:
        """Extract payments from all configured services."""
        logger.info("Starting payment extraction from all services")
        all_payments = []
        
        # Connect to Gmail
        logger.info("Connecting to Gmail IMAP server")
        mail = self._connect_to_gmail()
        
        try:
            for service_name, email_pattern in self.services.items():
                logger.info(f"Processing {service_name} service")
                payments = self._extract_service_payments(mail, service_name, email_pattern)
                all_payments.extend(payments)
                logger.info(f"Found {len(payments)} payments from {service_name}")
        
        except Exception as e:
            logger.error(f"Error during payment extraction: {str(e)}", exc_info=True)
            raise
        
        finally:
            logger.info("Closing Gmail connection")
            mail.close()
            mail.logout()
        
        logger.info(f"Total payments extracted: {len(all_payments)}")
        return all_payments
    
    def _connect_to_gmail(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP server."""
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.gmail_username, self.gmail_password)
            mail.select("inbox")
            logger.info("Gmail connection established successfully")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {str(e)}")
            raise
    
    def _extract_service_payments(self, mail: imaplib.IMAP4_SSL, service_name: str, email_pattern: str) -> List[Dict]:
        """Extract payments from a specific service."""
        logger.debug(f"Searching for emails from {email_pattern}")
        
        # Build search query
        since_date = (datetime.now() - timedelta(days=self.days_back)).strftime("%d-%b-%Y")
        query = f'FROM "{email_pattern}" SINCE "{since_date}"'
        
        try:
            status, messages = mail.search(None, query)
            if status != "OK" or not messages[0]:
                logger.debug(f"No messages found for {service_name}")
                return []
            
            message_ids = messages[0].split()
            logger.debug(f"Found {len(message_ids)} messages for {service_name}")
            
            payments = []
            for msg_id in reversed(message_ids):  # Process newest first
                payment = self._extract_payment_from_message(mail, msg_id, service_name)
                if payment:
                    payments.append(payment)
            
            return payments
            
        except Exception as e:
            logger.error(f"Error extracting payments from {service_name}: {str(e)}")
            return []
    
    def _extract_payment_from_message(self, mail: imaplib.IMAP4_SSL, msg_id: bytes, service_name: str) -> Optional[Dict]:
        """Extract payment data from a single message."""
        try:
            # Get message content
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                logger.debug(f"Failed to fetch message {msg_id}")
                return None
            
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extract email components
            subject = self._decode_header_safe(email_message.get("Subject", ""))
            date_str = email_message.get("Date", "")
            body = self._get_email_body(email_message)
            
            full_text = f"{subject} {body}"
            
            # Check if it's a payment email
            if not self._is_payment_email(full_text):
                logger.debug(f"Message {msg_id} not identified as payment email")
                return None
            
            # Extract payment details
            amount, currency = self._extract_amount(full_text)
            if not amount:
                logger.debug(f"Could not extract amount from message {msg_id}")
                return None
            
            sender = self._extract_sender(full_text)
            
            payment = {
                'service': service_name.title(),
                'sender': sender,
                'amount': amount,
                'currency': currency,
                'date': date_str,
                'days_ago': self._calculate_days_ago(date_str),
                'subject': subject
            }
            
            logger.debug(f"Extracted payment: {sender} - {amount} {currency} via {service_name}")
            return payment
            
        except Exception as e:
            logger.debug(f"Error processing message {msg_id}: {str(e)}")
            return None
    
    def _is_payment_email(self, text: str) -> bool:
        """Check if email is payment-related."""
        payment_keywords = [
            'payment', 'paid', 'sent you', 'received', 'invoice',
            'transfer', 'money', 'got paid', 'wants to pay'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in payment_keywords)
    
    def _extract_amount(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract amount and currency from text."""
        patterns = [
            r'[\$₱€£¥]([0-9,]+\.?[0-9]*)',  # Symbol first
            r'([0-9,]+\.?[0-9]*)\s*(USD|PHP|EUR|GBP|CAD)',  # Amount then currency code
            r'(USD|PHP|EUR|GBP|CAD)\s*([0-9,]+\.?[0-9]*)',  # Currency code then amount
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                for group in groups:
                    if re.match(r'^[0-9,]+\.?[0-9]*$', group):
                        amount = group.replace(',', '')
                        currency = 'USD'  # Default currency
                        # Look for currency in other groups
                        for g in groups:
                            if g != group and len(g) <= 3 and g.isalpha():
                                currency = g.upper()
                                break
                        return amount, currency
        
        return None, None
    
    def _extract_sender(self, text: str) -> str:
        """Extract sender name from text."""
        patterns = [
            r'from\s+([A-Za-z0-9\s\.\,\-\_&]+?)(?:\s+(?:sent|paid|has|is|wants|received))',
            r'([A-Za-z0-9\s\.\,\-\_&]+?)\s+(?:sent you|paid you|has sent|wants to pay)',
            r'You got paid by\s+([A-Za-z0-9\s\.\,\-\_&]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sender = match.group(1).strip()
                sender = re.sub(r'\s+', ' ', sender)  # Normalize whitespace
                sender = sender.strip('.,- ')  # Remove trailing punctuation
                if len(sender) >= 3:
                    return sender
        
        return "Unknown Sender"
    
    def _decode_header_safe(self, header: str) -> str:
        """Safely decode email header."""
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            result = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    result += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    result += str(part)
            return result
        except Exception as e:
            logger.debug(f"Header decode error: {str(e)}")
            return str(header)
    
    def _get_email_body(self, email_message) -> str:
        """Extract text body from email message."""
        body = ""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except Exception:
                            continue
            else:
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception:
                    body = str(email_message.get_payload())
        except Exception as e:
            logger.debug(f"Email body extraction error: {str(e)}")
        
        return body
    
    def _calculate_days_ago(self, date_str: str) -> str:
        """Calculate human-readable time difference."""
        try:
            email_date = parsedate_to_datetime(date_str)
            days = (datetime.now(email_date.tzinfo) - email_date).days
            if days == 0:
                return "Today"
            elif days == 1:
                return "Yesterday"
            else:
                return f"{days} days ago"
        except Exception:
            return "Unknown"