19/01/2026
Feedback on the basic_graph : 
1. Trying to build deterministic workflow then you did good but if you are trying to build an agent- No use of LLM : its bad??
2. Used langgraph for the correct reason - Nice 
3. Separating analysis from response - good 
4. word in feedback_lower : this is very wrong because if I give "not bad" which is grammatically a positive meaning but your response will be its negative..
5. Confidence score becomes unreliable 

Overall : Good work but improvements could be done

1-5 experimenting the langgraph - OK

Multi_agent_graph : 
1. Role seperation is good
2. Router is bad but that's good -> checking state and not text - good
3. MAX steps guard is good (prod level)
4. Router agent is useless - not wrong but not worth, you can do that with langGraph
5. Planner agent output is unstructured and cannot be considered
6. Executor has no restrictions - it literally executes anything

--- Take note of these things when doing the next one, will give feedback for the rest later. 
