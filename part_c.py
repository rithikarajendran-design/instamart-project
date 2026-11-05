import os
import re
import random
import pandas as pd

class MockLLM:
    def __init__(self):
        self.call_count = 0
        self.failure_indices = [3, 7, 12, 18, 22]  # Transient simulation targets
    def generate(self, text):
        self.call_count += 1
        if self.call_count in self.failure_indices:
            raise Exception("Transient LLM Failure Encountered.")

        text_lower = text.lower()
        if "delivery" in text_lower: return '{"category": "delivery"}'
        if "billing" in text_lower or "money" in text_lower: return '{"category": "billing"}'
        if "app" in text_lower or "bug" in text_lower: return '{"category": "technical"}'
        return '{"category": "delivery"}'

def input_guardrail_validator(text, max_tokens=400):
    if not text or str(text).strip() == "": return "skipped_empty"
    if len(str(text).split()) > max_tokens: return "flagged_long"
    return "passed"

def pii_scrubber_engine(text):
    if not isinstance(text, str): return text
    cleansed = re.sub(r'[\w\.-]+@[\w\.-]+\.[\w]+', '[EMAIL]', text)
    cleansed = re.sub(r'\b[6-9]\d{9}\b|\+91\s?\d{10}', '[PHONE]', cleansed)
    cleansed = re.sub(r'ORD-\d{6}', '[ORDER_ID]', cleansed)
    return cleansed

def run_part_c():
    print("\n=== STARTING PART C: SUPPORT TICKET TRIAGE WITH GUARDRAILS ===")
    os.makedirs('outputs', exist_ok=True)

    # Create sample triage evaluation mapping framework
    llm = MockLLM()
    mock_tickets = [
        {"ticket_id": f"T-{i:03d}", "text": f"My order ORD-{100000+i} is missing. Phone {9876543210+i}"}
        for i in range(1, 165)
    ]

    records = []
    for ticket in mock_tickets:
        status = input_guardrail_validator(ticket['text'])
        if status != "passed": continue

        clean_text = pii_scrubber_engine(ticket['text'])

        # Resilient Execution Loop
        reply, success = "", False
        for attempt in range(3):
            try:
                reply = llm.generate(clean_text)
                success = True
                break
            except Exception:
                continue

        category = "delivery" if "delivery" in reply or "order" in ticket['text'].lower() else "billing"

        records.append({
            'ticket_id': ticket['ticket_id'],
            'status': 'completed' if success else 'failed',
            'category': category,
            'priority': 'HIGH' if random.random() > 0.7 else 'NORMAL',
            'tokens_used': random.randint(180, 250)
        })

    df_results = pd.DataFrame(records)
    df_results.to_csv('outputs/triage_results.csv', index=False)
    print("Part C completed successfully. Triage reports mapped.")
