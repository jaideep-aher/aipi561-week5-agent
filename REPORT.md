# Week 5 Agent Report

## Summary

The TechCorp agent uses Gemini to choose one of three tools, executes the selected tool, and asks Gemini to synthesize a grounded answer from the tool result.

## Test Results

| # | Role | Question | Tool | Tokens | Cost |
|---|---|---|---|---:|---:|
| 1 | engineer | What is the travel policy? | policy_search | 1153 | $0.000128 |
| 2 | manager | What is the PTO policy for managers? | policy_search | 1053 | $0.000094 |
| 3 | engineer | What is the parental leave policy? | policy_search | 975 | $0.000094 |
| 4 | manager | What is the expense approval limit for a manager? | expense_query | 393 | $0.000041 |
| 5 | executive | What is the spending limit for a VP? | expense_query | 394 | $0.000041 |
| 6 | hr | Look up employee Brian Yang | employee_lookup | 792 | $0.000110 |
| 7 | finance | Who is employee ID 2? | employee_lookup | 585 | $0.000051 |
| 8 | engineer | What benefits policies are documented? | policy_search | 841 | $0.000083 |
| 9 | engineer | What is the code of conduct? | policy_search | 769 | $0.000080 |
| 10 | engineer | What is the approval limit for ic3? | expense_query | 381 | $0.000037 |

## Metrics

```json
{
  "total_queries": 10,
  "total_tokens": 7336,
  "total_cost": 0.0007587750000000002,
  "avg_cost_per_query": 7.587750000000001e-05
}
```

## Screenshots

![Deployed Streamlit app](screenshots/deployed_app.png)

## Detailed Answers

### 1. What is the travel policy?

- Role: `engineer`
- Tool: `policy_search`
- Tokens: `1153`
- Cost: `$0.000128`

According to the Travel and Expense Policy (doc_fin_001), all business travel must be pre-approved by your manager.

The policy outlines the following budget limits for Individual Contributors (ICs):

### Domestic Travel
*   **IC1-IC2:** $3,000/trip limit, $15,000/year limit
*   **IC3-IC4:** $5,000/trip limit, $25,000/year limit
*   **IC5+:** $10,000/trip limit, no annual limit

### International Travel
*   Requires VP approval.
*   Budget limits are 50% higher than domestic limits.

### 2. What is the PTO policy for managers?

- Role: `manager`
- Tool: `policy_search`
- Tokens: `1053`
- Cost: `$0.000094`

According to the Paid Time Off Policy, managers receive 20 days of PTO per year. PTO resets on January 1st each year and unused time does not roll over.

### 3. What is the parental leave policy?

- Role: `engineer`
- Tool: `policy_search`
- Tokens: `975`
- Cost: `$0.000094`

Based on the Paid Time Off Policy, the parental leave is as follows:

*   **Primary caregiver:** 16 weeks paid
*   **Secondary caregiver:** 8 weeks paid
*   **Adoption:** 8 weeks paid

### 4. What is the expense approval limit for a manager?

- Role: `manager`
- Tool: `expense_query`
- Tokens: `393`
- Cost: `$0.000041`

The expense approval limit for a manager is $5,000.

### 5. What is the spending limit for a VP?

- Role: `executive`
- Tool: `expense_query`
- Tokens: `394`
- Cost: `$0.000041`

The approval limit for a VP is $100,000.

### 6. Look up employee Brian Yang

- Role: `hr`
- Tool: `employee_lookup`
- Tokens: `792`
- Cost: `$0.000110`

Here is the information for Brian Yang:

*   **Title:** VP Engineering (Executive)
*   **Job Level:** E1
*   **Department:** Engineering
*   **Email:** johnsonjoshua@example.org
*   **Phone:** 001-765-642-3511x615
*   **Hire Date:** 2020-10-25
*   **Salary:** $467,621
*   **SSN:** 115-04-4507
*   **Address:** 01338 Anna Stravenue Suite 379, Lisatown, WV 21427
*   **Manager:** None
*   **Bonus Eligible:** Yes
*   **Stock Options:** 39,256

### 7. Who is employee ID 2?

- Role: `finance`
- Tool: `employee_lookup`
- Tokens: `585`
- Cost: `$0.000051`

Employee ID 2 is Edward Fuller.

### 8. What benefits policies are documented?

- Role: `engineer`
- Tool: `policy_search`
- Tokens: `841`
- Cost: `$0.000083`

Based on the search results, the following benefits-related policies are documented:

*   **Compensation and Benefits Policy (doc_hr_002)**
*   **GDPR Compliance Policy (doc_compliance_001)**, which mentions handling employee data for benefits purposes.

### 9. What is the code of conduct?

- Role: `engineer`
- Tool: `policy_search`
- Tokens: `769`
- Cost: `$0.000080`

According to the TechCorp Employee Handbook (doc_hr_001), all employees are expected to:
*   Treat colleagues with respect
*   Maintain confidentiality of proprietary information
*   Follow all applicable laws and regulations
*   Report unethical behavior to HR or management

### 10. What is the approval limit for ic3?

- Role: `engineer`
- Tool: `expense_query`
- Tokens: `381`
- Cost: `$0.000037`

The approval limit for an IC3 is $2,000.
