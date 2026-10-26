# data/

EcomSafeBench data is not stored in this folder. The canonical workflow for generating it is [`../data_generation/`](../data_generation/).

## Where EcomSafeBench lives

- **Generation and validation code:** `../data_generation/` (`ecomsafe_datagen`).
- **Current pilots:** these are synthetic and come from `ecomsafe_datagen`. Full generated pilot outputs are **not** committed. Run reports for `pilot_150` (headline) and `pilot_v5` (comparison), plus a 24-record sample, are in `../data_generation/examples/`.
- **Full benchmark:** the full 3,900-conversation EcomSafeBench (1,300 commercial jailbreaks, 1,100 multi-turn escalations, 1,500 benign/control) is still planned. The pilots so far are single-turn only.

## Labels

- **Record format:** each generated record is a `Conversation` (`data_generation/ecomsafe_datagen/schema.py`).
- **Request intent labels** for shopper messages: PV, CD, FF, RB and BENIGN.
- **Response labels** (`ResponseLabel`): CR (Compliant Refusal), COMPLIED, PARTIAL and HELPED. They are response-side labels, assigned only after target-model responses are collected.

## Do not commit

- copyrighted papers or other third-party documents without a compatible licence;
- API keys, `.env` files, or LLM caches;
- bulk raw model outputs or unreviewed generated artifacts.
