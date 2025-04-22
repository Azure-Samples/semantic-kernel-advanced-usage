# Custom selection strategy - speaker_selection_strategy

A custom implementation of `selection_strategy` for selecting next agent in `AgentGroupChat` by leveraging an improved logic covering more complex scenarios.

## Rationale

By default, the `selection_strategy` can be a simple round-robin approach or KernelFunction-based selection, based on agents names only. This variant is designed to improve the selection logic by considering the following:

- Limit history of the last selected agent to a certain number of turns (e.g. 3).
- Consider agents descriptions for better matching and configurability.
- Optionally, also include available `tools` in the selection process.
- Set LLM temperature to 0.0 to limit randomness in the selection process.
- Use `structured_output` to return the selected agent and the reason for selection - best for explanation purposes.
- Integrate OpenTelemetry custom attributes for better observability (see ⬆️)

## Usage

1. Ensure you filled `.env` file with the correct values from `.env.sample`.
2. Run `pip install -r requirements.txt` to install the required packages.
3. Experiment with the `selection_strategy` in `playground.ipynb` notebook.

## Further work

Check `advanced_orchestration_dapr` for more advanced orchestration strategies.
