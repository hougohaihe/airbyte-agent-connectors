# Airbyte Agent Connectors

A fork of [airbytehq/airbyte-agent-connectors](https://github.com/airbytehq/airbyte-agent-connectors) that provides AI-powered data integration connectors.

> **Personal Fork**: This is my personal learning fork to explore AI-powered data connectors and experiment with custom integrations.

## Overview

This project extends Airbyte's connector framework with agent-based capabilities, enabling intelligent data synchronization and transformation through AI-powered workflows.

## Features

- 🤖 AI-powered data connectors
- 🔌 Compatible with Airbyte ecosystem
- 🛠️ Custom connector development framework
- 📊 Intelligent data mapping and transformation
- 🔄 Automated sync scheduling

## Project Structure

```
airbyte-agent-connectors/
├── .claude-plugin/          # Claude AI plugin configuration
├── .github/                 # GitHub Actions workflows and utilities
│   ├── actions/            # Reusable GitHub Actions
│   └── workflows/          # CI/CD pipelines
├── connectors/             # Individual connector implementations
├── skills/                 # AI agent skills and capabilities
└── LICENSE                 # Apache 2.0 License
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Docker (for running connectors in containers)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/airbyte-agent-connectors.git
cd airbyte-agent-connectors

# Install dependencies
pip install -r requirements.txt
```

### Development

```bash
# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with verbose output and stop on first failure (useful during active development)
pytest -v -x
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **Generate Skills**: Automatically generates AI agent skills from connector definitions
- **Publish**: Publishes connectors and updates to the marketplace
- **Slack Notifications**: Sends build status updates to configured Slack channels

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on [Airbyte](https://airbyte.com/) open-source data integration platform
- Powered by Claude AI for intelligent connector capabilities

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Personal Notes

> These are my own notes as I work through this codebase.

- The `skills/` directory is where most of the interesting AI logic lives — good starting point for exploration
- `pytest -v -x` is my preferred way to run tests locally; stops fast on failures instead of churning through everything
