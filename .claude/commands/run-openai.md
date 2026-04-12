Run a snowglobe simulation using the OpenAI pool (GPT-5 Mini / GPT-5 Nano) with PDF report generation.

Steps:
1. Check that OPENROUTER_API_KEY is set (warn if not)
2. Check if TAVILY_API_KEY is set (note if planning agent will be skipped)
3. Run: `snowglobe --pool openai --report`
4. Monitor output and report results when complete
5. Report the PDF path to the user
