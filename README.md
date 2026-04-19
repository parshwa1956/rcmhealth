# Kaldi RCM App Starter Package

This starter package gives you a modular Streamlit structure for your Revenue Integrity & Denials Prevention Platform.

## Included modules
- Executive View
- Overview
- Claims
- Recoverable Amount
- Prior Auth
- Denial Reasons
- Next Best Action
- Payer Recovery Priorities
- Appeals Workqueue
- Service Lines
- Export Center

## Run
```bash
pip install -r requirements.txt
streamlit run app_health.py
```

## Notes
- The app tries to import `parser_v5_skeleton.py` first.
- If that parser is missing or returns incomplete data, the built-in fallback parser still creates usable claim and service-line output for dashboard testing.
- This starter is designed to be extended, not treated as a finished production parser.
