# EVAL_QUESTIONS.md - Evaluation Questions for Codex

## Feature A: RAG with Citations

### Basic Queries
1. "What is the maximum wind speed allowed for crane operations?"
   - Expected: Reference to wind speed threshold from safety manual
   - Citations: Should cite specific document and section

2. "What are the rain-related work restrictions?"
   - Expected: Information about rainfall thresholds
   - Citations: Should cite precipitation rules

3. "Can we work in fog conditions?"
   - Expected: Visibility requirements
   - Citations: Should cite visibility/fog protocols

### Complex Queries
4. "What safety equipment is required for roof work during bad weather?"
   - Expected: Equipment list + weather considerations
   - Citations: Multiple sources

5. "Compare the wind restrictions for different types of operations"
   - Expected: Comparative analysis
   - Citations: Multiple rules

## Feature B: Durable Memory

### User Memory Tests
1. Tell the bot: "I manage Site Alpha in Boston"
   - Check: USER_MEMORY.md should contain this fact

2. Ask about: "What sites do I manage?"
   - Expected: Should recall Site Alpha from memory

3. Tell the bot: "I prefer morning safety briefings"
   - Check: USER_MEMORY.md should store preference

### Company Memory Tests
1. Report: "Site Alpha has a recurring roof leak issue"
   - Check: COMPANY_MEMORY.md should contain this

2. Ask: "Are there any known issues at Site Alpha?"
   - Expected: Should mention roof leak from memory

3. New manager asks: "Check Site Alpha for today"
   - Expected: Should warn about roof leak even though new user

## Feature C: Weather + Safety Decision (Optional)

### Weather Integration Tests
1. "Check Site Alpha for today" (Boston location)
   - Expected: 
     - Retrieve safety rules
     - Check Boston weather
     - Compare rules vs reality
     - Make recommendation

2. "Can we do crane work in Miami today?"
   - Expected: Weather check + rule comparison

3. "What are the weather violations for this week?"
   - Expected: Multi-day forecast analysis

### Decision Quality
4. Query during bad weather: "Check Chicago for outdoor work"
   - Current conditions: High winds or heavy rain
   - Expected: Recommendation to postpone work
   - Memory: Should log safety pause

5. Query during good weather: "Check San Diego for roof work"
   - Current conditions: Clear, calm
   - Expected: Approval to proceed

## Edge Cases

### No Documents
- Ask question with no documents ingested
- Expected: Graceful handling, no hallucination

### Unknown Location
- Check weather for non-existent location
- Expected: Graceful error handling

### Duplicate Memory
- Tell bot same fact twice
- Expected: Store only once (no duplicates)

### Ambiguous Queries
- "Is it safe to work?"
- Expected: Ask for clarification (site location, operation type)

## Integration Tests

### Full Workflow
1. Ingest safety manual
2. Set user location preference
3. Report site issue
4. Check site safety
5. Verify memory updates

Expected flow:
- Rules retrieved with citations
- Weather checked automatically
- Site issues recalled from memory
- Safety decision made
- Memory updated with safety pause

## Performance Expectations

- Document ingestion: < 5 seconds per PDF
- Query response: < 3 seconds
- Safety check (with weather): < 5 seconds
- Memory write: < 1 second
