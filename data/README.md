# data/

**Scaffold for upcoming implementation. No dataset has been committed yet.**

This directory will hold EcomSafeBench, the planned benchmark of commercial-jailbreak and benign shopping conversations.

**Plan:**
1. **Pilot first:** about 150 conversations (50 commercial jailbreaks, 40 multi-turn escalations, 60 benign) across all five product domains: electronics, pharmaceuticals, fashion, financial products, and groceries.
2. **Full benchmark later:** the planned design is 3,900 annotated conversations (1,300 commercial jailbreaks, 1,100 multi-turn escalations, 1,500 benign/control).

**Planned structure:** each conversation carries two levels of labels, validated against the annotation schema (to be added):
- **Conversation level:** domain, benign/control status, attack type, and escalation pattern.
- **Turn level:** intent labels (PV/CD/FF/RB/CR).

**Do not commit:**
- copyrighted source papers or other third-party documents;
- sensitive, personal, or unreviewed generated artifacts;
- large raw model outputs.
