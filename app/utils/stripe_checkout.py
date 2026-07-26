"""Helpers for creating Stripe Checkout sessions."""
from __future__ import annotations

from flask import current_app, url_for
import stripe


def stripe_is_configured() -> bool:
    return bool(current_app.config.get('STRIPE_SECRET_KEY'))


def _charge_amount(hr) -> float:
    tip = float(hr.tip_amount or 0)
    if hr.payment_schedule in ('deposit', 'installments') and hr.deposit_amount:
        return float(hr.deposit_amount) + tip
    return float(hr.total_amount or 0) + tip


def checkout_amount_cents(hr) -> int:
    return int(round(_charge_amount(hr) * 100))


def success_url() -> str:
    configured = current_app.config.get('STRIPE_SUCCESS_URL')
    if configured:
        return configured
    return url_for('public.hire_success_page', _external=True)


def cancel_url() -> str:
    configured = current_app.config.get('STRIPE_CANCEL_URL')
    if configured:
        return configured
    return url_for('public.hire', _external=True)


def _configured_currency() -> str:
    return current_app.config.get('STRIPE_CURRENCY', 'usd')


def create_checkout_session(hr):
    if not stripe_is_configured():
        raise RuntimeError('Stripe is not configured. Add STRIPE_SECRET_KEY before using Stripe checkout.')

    amount_cents = checkout_amount_cents(hr)
    if amount_cents <= 0:
        raise ValueError('Stripe payments require a positive amount. Add a total amount or deposit amount before paying.')

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    payment_label = 'Deposit' if hr.payment_schedule in ('deposit', 'installments') and hr.deposit_amount else 'Project Payment'
    metadata = {
        'hire_request_id': str(hr.id),
        'client_email': hr.client_email or '',
        'project_title': hr.project_title or '',
        'payment_method': hr.payment_method or '',
        'payment_schedule': hr.payment_schedule or '',
    }

    return stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        client_reference_id=str(hr.id),
        customer_email=hr.client_email or None,
        metadata=metadata,
        payment_intent_data={
            'metadata': metadata,
            'description': f'{payment_label}: {hr.project_title}',
        },
        line_items=[{
            'price_data': {
                'currency': _configured_currency(),
                'product_data': {
                    'name': f'{payment_label} | {hr.project_title}',
                    'description': (hr.project_description or '')[:240],
                },
                'unit_amount': amount_cents,
            },
            'quantity': 1,
        }],
        success_url=success_url() + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=cancel_url(),
    )


def create_store_checkout_session(product: dict):
    if not stripe_is_configured():
        raise RuntimeError('Stripe is not configured. Add STRIPE_SECRET_KEY before using Stripe checkout.')

    amount_cents = int(product.get('price_cents', 0))
    if amount_cents <= 0:
        raise ValueError('Store products require a positive Stripe amount.')

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    metadata = {
        'product_slug': product['slug'],
        'product_title': product['title'],
        'purchase_type': 'store_print',
    }

    return stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        metadata=metadata,
        payment_intent_data={
            'metadata': metadata,
            'description': product['title'],
        },
        line_items=[{
            'price_data': {
                'currency': _configured_currency(),
                'product_data': {
                    'name': product['title'],
                    'description': product.get('description', '')[:240],
                },
                'unit_amount': amount_cents,
            },
            'quantity': 1,
        }],
        success_url=url_for('public.store_success_page', slug=product['slug'], _external=True) + '&session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('public.store', _external=True),
    )
