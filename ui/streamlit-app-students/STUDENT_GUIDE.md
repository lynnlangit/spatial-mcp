# Student MCP Chat App - Quick Start Guide

Welcome to the **Student MCP Chat App**! This app is designed for the bioinformatics study group with **built-in safety guardrails** to prevent accidental costs.

## 🎓 What Makes This App Special?

This is **not** the full production app. It has safety features:

✅ **Token Limits**: Max 50,000 tokens per session (~$1.50 max cost)  
✅ **Request Limits**: Max 50 requests per session  
✅ **Usage Tracking**: See your usage in real-time  
✅ **Auto-Warnings**: Alerts at 80% usage  
✅ **Easy Reset**: Clear conversation to reset limits  

**Your instructor's app has NO limits** - this lets them test freely while you learn safely.

---

## 🚀 Quick Start (5 Minutes)

### Option 1: Use the Deployed App (Recommended)

Your instructor will provide:
```
Student App URL: https://streamlit-mcp-chat-students-XXXXX.run.app
```

Just click and start using! No setup needed.

### Option 2: Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp/ui/streamlit-app-students

# 2. Copy environment file
cp .env.example .env

# 3. Add API keys (instructor will provide)
# Edit .env and paste the keys

# 4. Install dependencies
python3 -m pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
```

---

## 📊 Understanding the Safety Limits

### Session Limits

| Limit | Value | Why? |
|-------|-------|------|
| **Tokens per request** | 4,096 | Prevents single huge queries |
| **Tokens per session** | 50,000 | ~$1.50 max cost per session |
| **Requests per session** | 50 | Prevents runaway loops |

### What Happens When You Hit a Limit?

You'll see a friendly message:
```
🛑 Session Token Limit Reached
Great job exploring! You've used 50,000 tokens this session.

To continue:
- Click "Clear conversation" in sidebar
- Or refresh the page

Cost estimate: $1.50
```

**No money is wasted** - limits stop you before costs grow.

---

## Study Group Workflow

### **Week 1: Guided Exploration**

The deployed app connects to **3 real MCP servers** on GCP Cloud Run with PatientOne sample data:
- **spatialtools** — spatial transcriptomics analysis
- **multiomics** — multi-omics integration and pathway enrichment
- **fgbio** — genomic QC and FASTQ validation

**Start with:**
1. Run **"Warm Up Servers"** to wake up Cloud Run instances
2. Try each of the 6 built-in example prompts
3. Observe what tools get called and what data is returned

**Best for:**
- Getting comfortable with the UI
- Understanding MCP servers and tool calling
- Seeing real bioinformatics results

### **Week 2+: Independent Analysis**

Once comfortable with the built-in prompts:
- Write your own prompts referencing PatientOne GCS data
- Try different gene lists for pathway enrichment
- Explore spatial patterns with different marker genes
- Combine multiple steps in a single prompt

**Safety limits protect you:**
- 50,000 tokens per session (~$1.50 max)
- 50 requests per session
- Clear conversation to reset and continue

---

## 📈 Monitoring Your Usage

### Sidebar Dashboard

```
🎓 Student Mode
┌─────────────────────────┐
│ Tokens Used             │
│ 12,450 / 50,000        │
│ [████████░░░░░] 25%     │
│                         │
│ Requests                │
│ 8 / 50                  │
│ [████░░░░░░░░] 16%     │
│                         │
│ 💰 Est. cost: $0.11    │
│ ⏱️ Session: 15m 32s     │
└─────────────────────────┘
```

### After Each Query

```
📊 Session: 8/50 requests, 12,450/50,000 tokens
```

### Warnings

At 80% usage:
```
⚠️ Token Usage Warning: 40,000 / 50,000 tokens used (10,000 remaining)
```

---

## 💡 Best Practices

### 1. **Start with Mock Mode**

Week 1-2, use mock mode to:
- Practice writing good prompts
- Learn what each server does
- Experiment freely (it's free!)

### 2. **Switch to Real Mode Gradually**

Week 3+, use real mode for:
- Homework requiring actual analysis
- Custom tool testing
- Real data exploration

### 3. **Monitor Your Usage**

Keep an eye on the sidebar:
- If tokens spike → your query might be too broad
- If requests stack up → you might have a loop

### 4. **Reset When Needed**

Hit a limit? No problem:
- Click "Clear conversation" (sidebar)
- Or refresh the page
- Start fresh!

### 5. **Ask Focused Questions**

Good prompts are:
- ✅ Specific: "Calculate spatial autocorrelation for CD4"
- ✅ Clear: "Run HAllA on proteomics vs metabolomics"

Bad prompts are:
- ❌ Vague: "Analyze everything"
- ❌ Open-ended: "What can you tell me?"

---

## 🆘 Troubleshooting

### "Session Request Limit Reached"

**Cause**: You made 50 queries in this session

**Solution**:
1. Click "Clear conversation" in sidebar
2. Or refresh the page
3. Your usage resets

### "Session Token Limit Reached"

**Cause**: You used 50,000 tokens (~$1.50)

**Solution**:
1. Great job exploring!
2. Clear conversation or refresh
3. Continue learning

### "API Key Missing"

**Cause**: Environment variable not set

**Solution**:
1. Check .env file has the key
2. Restart the app
3. Contact instructor if still broken

### "Too slow / not responding"

**Most likely cause**: Cloud Run cold start. The MCP servers sleep when idle (`min-instances=0`) and take 10-30 seconds to wake up on first request.

**Solutions**:
- Run **"Warm Up Servers"** example prompt first to wake all servers
- Wait 30-60 seconds for the first query to complete
- Subsequent queries will be fast (servers stay warm for ~15 minutes)

---

## Built-in Example Prompts

The app has **6 pre-built example prompts** in the sidebar dropdown. These use PatientOne (PAT001-OVC-2025) sample data stored in GCS.

### Getting Started

1. Select **"Warm Up Servers"** first — this wakes up the Cloud Run servers (they sleep when idle)
2. Then try any of the analysis prompts

### Available Prompts

| Prompt | What It Does |
|--------|-------------|
| **Warm Up Servers** | Lists all available tools from connected servers |
| **Spatial Analysis** | Runs Moran's I spatial autocorrelation on Visium gene expression data for CD3D, CD8A, EPCAM, MKI67 |
| **Multi-omics Integration** | Loads and aligns RNA, protein, and phosphoproteomics data across 15 samples |
| **Genomic QC** | Validates a FASTQ file and reports quality scores, read length, GC content |
| **Pathway Enrichment** | Runs GO biological process enrichment for genes TP53, BRCA1, MYC, KRAS |
| **PatientOne Mini Workflow** | Two-step analysis: FASTQ quality check, then spatial autocorrelation |

### Writing Your Own Prompts

Good prompts are **specific and directive**:

```
Use the spatial_autocorrelation tool with
expression_file=gs://sample-inputs-patientone/patient-data/PAT001-OVC-2025/spatial/visium_gene_expression.csv
and coordinates_file=gs://sample-inputs-patientone/patient-data/PAT001-OVC-2025/spatial/visium_spatial_coordinates.csv
to calculate spatial autocorrelation for genes CD3D, CD8A
```

Avoid vague prompts:
- "Analyze everything" (too broad)
- "What can you tell me?" (too open-ended)
- "Run my data" (no file paths specified)

---

## Homework Tips

### Managing Your Token Budget

Each session gives you 50,000 tokens (~30-40 queries):
- Built-in example prompts use ~1,000-3,000 tokens each
- Monitor usage in the sidebar as you go
- Clear conversation to reset and continue

**Study group total cost: ~$30-60 for entire 6-week program**

---

## 🔒 What's Different from Instructor's App?

| Feature | Student App | Instructor App |
|---------|------------|----------------|
| **Token Limits** | ✅ 50K per session | ❌ Unlimited |
| **Request Limits** | ✅ 50 per session | ❌ Unlimited |
| **Authentication** | ✅ None (public) | ℹ️ Optional SSO |
| **Usage Tracking** | ✅ Visible sidebar | ℹ️ Optional |
| **Warnings** | ✅ At 80% usage | ❌ None |
| **Cost Protection** | ✅ Auto-stops | ❌ None |
| **MCP Servers** | ✅ Same servers | ✅ Same servers |
| **Providers** | ✅ Gemini only (Flash/Pro) | ✅ Claude + Gemini |

**You share the same MCP infrastructure** - only the safety limits differ!

---

## 💬 Getting Help

### During Study Group

1. **Ask in Slack/Discord** - Other students might have same question
2. **Pair with a buddy** - Two heads better than one
3. **Check README.md** - Technical details there

### Common Questions

**Q: Can I increase my limits?**
A: No - limits are for your protection. Reset conversation instead.

**Q: What if I need more tokens for homework?**
A: Most assignments fit easily. If not, split into multiple sessions.

**Q: Why mock mode first?**
A: Free practice! Learn without spending tokens.

**Q: Can I use instructor's app?**
A: Ask your instructor - they might grant access for specific projects.

---

## Success Metrics

Track your progress:

**Week 1-2:**
- Ran all 6 built-in example prompts
- Understand what each MCP server does
- Written your own prompts with specific file paths

**Week 3-4:**
- Explored different gene lists and analysis parameters
- Combined multiple tools in a single prompt
- Stayed within token limits

**Week 5-6:**
- Built a custom MCP tool
- Integrated into a workflow
- Helped another student

---

## Ready to Start?

1. Open the student app URL provided by your instructor
2. Check sidebar shows "Student Mode" with token/request counters
3. Select **"Warm Up Servers"** from the Example Prompts dropdown and click Send
4. Try each built-in prompt: Spatial Analysis, Multi-omics, Genomic QC, Pathway Enrichment
5. Watch your usage counters in the sidebar

**Remember**: Limits are your friend - they let you explore freely without worry!
