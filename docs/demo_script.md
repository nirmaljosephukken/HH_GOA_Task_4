# Demo video script (about 4 minutes)

**Before you record**
1. Open the TigerGraph Savanna console and check the workspace is running (resume it if it is asleep).
2. In the project folder, activate the venv and start the console: `python -m streamlit run ui/app.py`.
3. Open http://localhost:8501 full screen. Keep a second tab on Savanna (GraphStudio) for the last shot.
4. Do one warm-up run (any case) so TigerGraph and Gemini are awake. If a live run feels slow on camera, switch **LLM investigator** off: the decision is identical and a run takes about 10 seconds.

---

**[0:00 to 0:25] The problem** (Case Portfolio page)
> "Fraud teams get thousands of alerts and the risk score is wrong in both directions. In this bank's own history, all 900 alerts raised by the score alone were false alarms. SentinelGraph is an agent that works an alert like a careful analyst: it gathers evidence from a graph, says what it doesn't know, asks for the evidence that would settle it, and recommends an action someone can defend under policy."

Show the portfolio: 20 cases, 10 legitimate, 9 fraud, 1 uncertain, 6 SARs.

**[0:25 to 0:50] Architecture** (README diagram or blog)
> "TigerGraph Savanna holds three layers: the transaction graph with a latent-cardholder vertex, the case memory of 5,565 closed cases plus every case the agent opens, and the policy knowledge, all with native vector embeddings. The agent calls 16 installed GSQL queries through the official TigerGraph MCP server. A deterministic policy engine makes the decisions. The LLM only probes and writes, and its text is checked."

**[0:50 to 2:00] Live run: HHG-019** (Investigate page)
Pick HHG-019 in the alert box. Point at the empty "Ready to investigate" screen.
> "This is the alert as it arrives: a $99.92 online payment the bank model scored 0.90."

Click **Run investigation**. While steps stream in:
> "Every line is a graph query through MCP, about a tenth of a second each."

When it finishes, point at the green **Live run** bar and the **Compared with the previous run** strip.
> "This was run just now and written back into the graph. The outcome matches the previous run: same evidence, same decision. Only the wording changes."

Walk the four cards at the top:
> "What happened, what the agent found, how certain it is, and what happens next: block and reissue the card, with a team lead approving."

Scroll to **Evidence sufficiency**:
> "Two independent lines of evidence agree and the probability is past 85%, so policy section 6 says stop. That's why the agent didn't ask the customer."

Scroll to the **Investigation graph**:
> "On its own card this looks like an ordinary new-device purchase. The graph shows the same rare device on four other cards within days, all scored as likely fraud by our case-memory model. That model has an AUC of 0.91 against 0.87 for the bank's score."

Back at the **Next best action** panel, click **Approve** on BLOCK_CARD.
> "Auto actions ran already. Blocking waits for a human, and the approval is written into the case's audit trail in TigerGraph."

**[2:00 to 2:40] Asking for evidence: HHG-003** (Case Portfolio → HHG-003)
Open HHG-003 from the portfolio (it opens as a **Saved investigation**).
> "A customer says they never made a $49 purchase. The graph says the card uses that region all the time. The agent asked the customer to confirm, and the Decision evolution shows the probability move from 17% to 63%. The evidence still conflicts, so it blocks the card to protect the customer but hands the final call to an analyst. It's honest about doubt instead of faking confidence."

Point at **Why the agent handed over?**.

**[2:40 to 3:20] Finding what nobody reported** (Alert Queue → Proactive tab, then a custom alert)
> "The agent also scans the graph on its own: device rings, just-under-$500 bursts, and connected components."

Open **Custom alert**, enter transaction **3475414**, trigger **analyst_request**, and run it.
> "Four purchases in half an hour, each just under $500. The graph finds the same pattern on 11 other cards. It isn't one of the documented patterns, so the agent labels it undocumented, files a SAR and escalates."

**[3:20 to 3:40] Knowledge and memory** (Policies page)
Type "when may the agent block a card without approval?"
> "The policy is stored as vectors in TigerGraph. GraphRAG pulls the clause the agent cites: blocking always needs L1 or L2."

**[3:40 to 4:00] Close** (Savanna tab)
Show the `FraudCase` vertices with their FC_TXN, FC_CARD and FC_EVENT edges.
> "Every case is written back into TigerGraph, so the next investigation finds it by graph adjacency and by vector similarity. The code, the 20 answer files and full traces are in the repo."
