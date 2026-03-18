"""Envoi d'emails via SMTP Gmail."""

import logging
import smtplib
from email.mime.text import MIMEText

from scripts import config

logger = logging.getLogger(__name__)


def envoyer_email(destinataire: str, objet: str, corps: str) -> bool:
    """Envoie un email via Gmail SMTP.

    Retourne True si l'envoi a réussi, False sinon.
    Nécessite GMAIL_ADDRESS et GMAIL_APP_PASSWORD dans le .env.
    """
    address = config.GMAIL_ADDRESS
    password = config.GMAIL_APP_PASSWORD

    if not address or not password:
        logger.error(
            "Configuration Gmail manquante. "
            "Définissez GMAIL_ADDRESS et GMAIL_APP_PASSWORD dans le .env."
        )
        return False

    msg = MIMEText(corps, "plain", "utf-8")
    msg["From"] = address
    msg["To"] = destinataire
    msg["Subject"] = objet

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(address, password)
            server.send_message(msg)
        logger.info("Email envoyé à %s : %s", destinataire, objet)
        return True
    except Exception:
        logger.exception("Échec de l'envoi de l'email à %s", destinataire)
        return False
