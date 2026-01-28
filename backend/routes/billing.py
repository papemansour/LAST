"""
Billing Routes - Secretary payment management for teachers
This file is prepared for future refactoring of server.py
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(tags=["Billing"])

# Note: These routes are currently defined in server.py
# This file documents the billing endpoints for future extraction

"""
Billing Endpoints:

Teacher Payments:
- GET /secretary/teacher-payments - Get all teacher payments
- POST /secretary/teacher-payments - Create teacher payment (with bonus/deductions)
- DELETE /secretary/teacher-payments/{payment_id} - Delete payment
- POST /secretary/send-payment-email - Send payment email to teacher

Student Receipts:
- GET /secretary/student-receipts - Get all student receipts
- POST /secretary/student-receipts - Create student receipt
- DELETE /secretary/student-receipts/{receipt_id} - Delete receipt

Billing Stats:
- GET /secretary/billing-stats - Get billing statistics
- POST /secretary/reset-billing-stats - Reset billing stats

Schema for Teacher Payment:
{
    "id": str,
    "teacher_id": str,
    "teacher_name": str,
    "email": str,
    "amount": float,
    "currency": "EUR" | "FCFA",
    "period": str,
    "description": str,
    "status": "paid" | "pending",
    "bonus": float,         # NEW: Bonus amount
    "deductions": int,      # NEW: Number of missed classes
    "created_at": datetime
}

Deduction Calculation:
- 1 deduction = 5 EUR or 2000 FCFA
- Final amount = base_amount + bonus - (deductions * deduction_value)
"""
