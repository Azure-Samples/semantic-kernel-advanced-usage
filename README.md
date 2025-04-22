# Semantic Kernel Advanced Usage

## Overview

This repository contains advanced usage examples for [Semantic Kernel](https://github.com/microsoft/semantic-kernel) framework. The examples are designed to demonstrate various features and capabilities of the framework, including:

- **Advanced orchestration**
- **Dapr hosting**
- **Process framework**
- **Tracing and telemetry**
- **Copilot Studio integration**
- **Copilot Agent with Semantic Kernel and MS Graph APIs**

> [!NOTE]
> We're in the process of updating the examples to use the latest version of Semantic Kernel, which introduced some breaking changes.
> Please double check `requirements.txt` files for the tested version of Semantic Kernel in that specific example.

## Scenarios

> [!NOTE]
> Each scenario is self-contained and will run independently.

- [`advanced_orchestration_dapr`](/templates/advanced_orchestration_dapr/README.md): Demonstrates advanced orchestration techniques and Dapr hosting via Actors.
- [`authentication_context`](/templates/authentication_context/README.md): Demonstrates how to persist "hidden" information in the conversation to maintain context, like the user being authenticated.
- [`copilot_studio_skill`](/templates/copilot_studio_skill/README.md): Demonstrates how to use Semantic Kernel to create a skill for Microsoft Copilot Studio.
- [`natural_language_to_SQL`](/templates/natural_language_to_SQL/README.md): Demonstrates a natural language query to SQL using a state machine architecture supported by the Semantic Kernel Process Framework.
- [`copilot_studio`](/templates/copilot_studio/README.md): Demonstrates how to use Microsoft Copilot Agents as they were first-party agents in Semantic Kernel.
- [`copilot-agent-ms-graph`](/templates/copilot-agent-ms-graph/README.md): Demonstrates how to deploy a Semantic Kernel-powered Agent to Copilot that uses Microsoft MS Graph APIs.
- [`speaker_selection_strategy`](/templates/speaker_selection_strategy/README.md): Demonstrates how to use a custom speaker election strategy in a multi-agent scenario.

## Contributing

> [!TIP]
> Thanks to EMEA AI Global Black Belts for all the efforts!

This project welcomes contributions and suggestions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.
