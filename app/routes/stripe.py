from __future__ import annotations

import os
from datetime import datetime, timezone

import stripe
from flask import Blueprint, current_app, jsonify, request

from app import db
from app.models import HireRequest, Invoice
from app.utils.invoice_pdf import generate_receipt as generate_receipt_pdf
from app.utils.notify import send_invoice_email


stripe_bp = Blueprint('stripe', __name__)


def _configure_stripe():
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', '')


def _create_receipt_if_missing(hr):
    existing = Invoice.query.filter_by(hire_request_id=hr.id, invoice_type='receipt').first()
    if existing:
        return existing

    inv = Invoice.query.filter_by(hire_request_id=hr.id, invoice_type='invoice').first()
    inv_num = inv.invoice_number if inv else f'INV-{datetime.now(timezone.utc).strftime("%Y%m")}-{hr.id:04d}'
    rec_num = f'REC-{datetime.now(timezone.utc).strftime("%Y%m")}-{hr.id:04d}'
    rel_path = os.path.join('invoices', f'{rec_num}.pdf')
    abs_path = os.path.join('uploads', rel_path)

    generate_receipt_pdf(hr, inv_num, rec_num, abs_path)
    rec = Invoice(
        hire_request_id=hr.id,
        invoice_number=rec_num,
        invoice_type='receipt',
        pdf_path=rel_path,
        sent_at=datetime.now(timezone.utc) if not hr.invoice_opt_out else None,
    )
    db.session.add(rec)
    db.session.commit()

    if not hr.invoice_opt_out:
        try:
            send_invoice_email(hr, rec, abs_path)
        except Exception:
            current_app.logger.exception('Failed to email Stripe receipt')

    return rec


def _handle_checkout_completed(session):
    hire_request_id = session.get('client_reference_id') or session.get('metadata', {}).get('hire_request_id')
    if not hire_request_id:
        current_app.logger.warning('Stripe checkout.session.completed missing hire_request_id metadata')
        return

    hr = HireRequest.query.get(int(hire_request_id))
    if not hr:
        current_app.logger.warning('Stripe checkout.session.completed references missing hire request %s', hire_request_id)
        return

    hr.payment_status = 'confirmed'
    hr.stripe_checkout_session_id = session.get('id')
    if session.get('payment_intent'):
        hr.stripe_payment_intent_id = session.get('payment_intent')
    db.session.commit()

    _create_receipt_if_missing(hr)

    try:
        from app.utils.whatsapp import alert_payment_received
        amount_paid = (session.get('amount_total') or 0) / 100.0
        amount_remaining = max((hr.total_amount or 0) - amount_paid, 0)
        alert_payment_received(hr, amount_paid=amount_paid, amount_remaining=amount_remaining)
    except Exception:
        current_app.logger.exception('Failed to send WhatsApp payment alert for Stripe payment')


def _handle_payment_failed(intent):
    hire_request_id = intent.get('metadata', {}).get('hire_request_id')
    if not hire_request_id:
        return

    hr = HireRequest.query.get(int(hire_request_id))
    if not hr:
        return

    hr.payment_status = 'failed'
    hr.stripe_payment_intent_id = intent.get('id')
    db.session.commit()


@stripe_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    _configure_stripe()

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', '')
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')

    if not endpoint_secret:
        current_app.logger.error('Stripe webhook rejected because STRIPE_WEBHOOK_SECRET is not configured.')
        return jsonify({'error': 'webhook misconfigured'}), 503

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        current_app.logger.warning('Stripe webhook signature/body validation failed: %s', e)
        return jsonify({'error': str(e)}), 400

    event_type = event.get('type')
    data_object = event.get('data', {}).get('object', {})

    try:
        if event_type == 'checkout.session.completed':
            _handle_checkout_completed(data_object)
        elif event_type == 'payment_intent.payment_failed':
            _handle_payment_failed(data_object)
    except Exception:
        current_app.logger.exception('Stripe webhook handling failed for %s', event_type)
        return jsonify({'status': 'error'}), 500

    return jsonify({'status': 'success'})
